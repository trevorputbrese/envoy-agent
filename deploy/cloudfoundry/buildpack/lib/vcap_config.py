"""Wire Envoy to its Cloud Foundry service bindings, then print shell exports.

Every binding is recognised by what it carries, never by its instance name, so the same app
pushes to any foundation:

- Home: the first bound volume service (any binding with a read-write ``volume_mounts`` entry)
  holds ``envoy-home``; without one the home is ``$HOME/.envoy-home`` on the container disk.
  ``ENVOY_VOLUME_SERVICE`` picks a volume when several are bound. ``--home`` prints only this.
- Model: a binding whose credentials carry ``api_base``, ``api_key``, ``model_name`` and the
  ``chat`` capability (the Tanzu AI Service's ``ai-models``) becomes the named custom provider
  ``tanzu-ai`` in ``config.yaml``; ``ENVOY_CHAT_SERVICE`` picks one of several.
- Dashboard login: a user-provided binding with ``username`` and ``password_hash`` (or
  ``password``), optionally ``secret``; ``ENVOY_DASHBOARD_AUTH_SERVICE`` picks one of several.

Only the keys written here change in config.yaml, so dashboard edits survive restarts on a
volume. Caches, which can be rebuilt, stay on the container disk.
"""

from __future__ import annotations

import json
import os
import shlex
import sys
from pathlib import Path

KEY_ENV = "ENVOY_AI_API_KEY"
# Rebuildable directories under the home that stay off a size-limited volume.
LOCAL_DIRS = ("cache", "image_cache", "audio_cache", "installs")


def _named(bindings: list[dict], env: str, what: str) -> dict | None:
    wanted = os.environ.get(env, "").strip()
    if wanted:
        named = [b for b in bindings if wanted in (b.get("name"), b.get("instance_name"))]
        if not named:
            sys.exit(f"envoy: {env}={wanted} is not a bound {what}")
        return named[0]
    return bindings[0] if bindings else None


def _bindings(vcap: dict):
    for bindings in vcap.values():
        yield from bindings


def volume_dir(vcap: dict) -> Path | None:
    volumes = [b for b in _bindings(vcap)
               if any(m.get("container_dir") and m.get("mode", "rw") == "rw" for m in b.get("volume_mounts") or [])]
    binding = _named(volumes, "ENVOY_VOLUME_SERVICE", "volume service")
    if binding is None:
        return None
    mount = next(m for m in binding["volume_mounts"] if m.get("container_dir") and m.get("mode", "rw") == "rw")
    return Path(mount["container_dir"])


def resolve_home(vcap: dict) -> tuple[Path, bool]:
    """(home, on_volume): an explicit HERMES_HOME wins, then a bound volume, then the disk."""
    if os.environ.get("HERMES_HOME"):
        home = Path(os.environ["HERMES_HOME"])
        volume = volume_dir(vcap)
        return home, volume is not None and volume in home.parents
    volume = volume_dir(vcap)
    if volume is not None:
        return volume / "envoy-home", True
    return Path(os.environ.get("HOME", "/home/vcap/app")) / ".envoy-home", False


def keep_caches_local(home: Path) -> None:
    local = Path(os.environ.get("HOME", "/home/vcap/app")) / ".envoy-local"
    for name in LOCAL_DIRS:
        target, link = local / name, home / name
        target.mkdir(parents=True, exist_ok=True)
        if link.is_symlink():
            link.unlink()
        elif link.exists():
            continue  # a real directory from before: leave its contents alone
        link.symlink_to(target)


def chat_binding(vcap: dict) -> dict | None:
    def is_chat(binding: dict) -> bool:
        creds = binding.get("credentials") or {}
        return bool(creds.get("api_base") and creds.get("api_key") and creds.get("model_name")
                    and "chat" in (creds.get("model_capabilities") or []))
    return _named([b for b in _bindings(vcap) if is_chat(b)], "ENVOY_CHAT_SERVICE", "chat model")


PROVIDER = "tanzu-ai"


def write_model(home: Path, creds: dict, service: str) -> None:
    from ruamel.yaml import YAML

    yaml = YAML()
    path = home / "config.yaml"
    config = (yaml.load(path.read_text(encoding="utf-8")) if path.is_file() else None) or {}
    if "_config_version" not in config:
        # A file without a version reads as one from before migrations existed.
        from hermes_cli.config_defaults import DEFAULT_CONFIG

        config["_config_version"] = DEFAULT_CONFIG["_config_version"]
    providers = config.get("providers")
    if not isinstance(providers, dict):
        providers = {}
    providers[PROVIDER] = {
        "name": f"Tanzu AI Service ({service})",
        "api": creds["api_base"].rstrip("/") + "/v1",
        "key_env": KEY_ENV,
        "transport": "chat_completions",
        "default_model": creds["model_name"],
        # The service's proxy answers HTTP 500 to the "developer" role Envoy gives GPT-5 models.
        "capabilities": {"developer_role": False},
    }
    config["providers"] = providers
    model = config.get("model")
    if not isinstance(model, dict):
        model = {}
    for stale in ("base_url", "api_key", "key_env"):
        model.pop(stale, None)
    model.update({"provider": f"custom:{PROVIDER}", "default": creds["model_name"]})
    config["model"] = model
    # The proxy also rejects function tools combined with any reasoning_effort but "none", and
    # Envoy sends "medium" when nothing is configured.
    agent = config.get("agent")
    if not isinstance(agent, dict):
        agent = {}
    if not agent.get("reasoning_effort"):
        agent["reasoning_effort"] = os.environ.get("ENVOY_REASONING_EFFORT", "none")
    config["agent"] = agent
    # Bounded history for a bounded home; an explicit auto_prune either way is the operator's.
    sessions = config.get("sessions")
    if not isinstance(sessions, dict):
        sessions = {}
    sessions.setdefault("auto_prune", True)
    config["sessions"] = sessions
    with path.open("w", encoding="utf-8") as fh:
        yaml.dump(config, fh)
    path.chmod(0o600)


# Dashboard login from a bound user-provided service, so the secrets never sit in the app's
# environment (where `cf push` prints them in its manifest diff).
DASHBOARD_AUTH_FIELDS = {
    "username": "HERMES_DASHBOARD_BASIC_AUTH_USERNAME",
    "password_hash": "HERMES_DASHBOARD_BASIC_AUTH_PASSWORD_HASH",
    "password": "HERMES_DASHBOARD_BASIC_AUTH_PASSWORD",
    "secret": "HERMES_DASHBOARD_BASIC_AUTH_SECRET",
}


def dashboard_auth(vcap: dict) -> dict[str, str]:
    def is_login(binding: dict) -> bool:
        creds = binding.get("credentials") or {}
        return bool(creds.get("username") and (creds.get("password_hash") or creds.get("password")))
    binding = _named([b for b in vcap.get("user-provided", []) if is_login(b)],
                     "ENVOY_DASHBOARD_AUTH_SERVICE", "dashboard login service")
    creds = (binding or {}).get("credentials") or {}
    return {env: str(creds[field]) for field, env in DASHBOARD_AUTH_FIELDS.items() if creds.get(field)}


def main(argv: list[str]) -> int:
    vcap = json.loads(os.environ.get("VCAP_SERVICES") or "{}")
    home, on_volume = resolve_home(vcap)
    if "--home" in argv:
        print(f"export HERMES_HOME={shlex.quote(str(home))}")
        return 0
    home.mkdir(parents=True, exist_ok=True)
    home.chmod(0o700)
    if on_volume:
        keep_caches_local(home)
    print(f"envoy: home {home} ({'volume' if on_volume else 'container disk, lost on restart'})",
          file=sys.stderr)
    exports: dict[str, str] = {"HERMES_HOME": str(home), **dashboard_auth(vcap)}
    binding = chat_binding(vcap)
    if binding is None:
        print("envoy: no AI Service chat model is bound; configure a provider from the dashboard",
              file=sys.stderr)
    else:
        creds = binding["credentials"]
        write_model(home, creds, binding.get("name") or "ai-models")
        exports[KEY_ENV] = creds["api_key"]
        print(f"envoy: chat model {creds['model_name']} from service {binding.get('name')}", file=sys.stderr)
    app = json.loads(os.environ.get("VCAP_APPLICATION") or "{}")
    uris = app.get("application_uris") or []
    if uris and not os.environ.get("HERMES_DASHBOARD_PUBLIC_URL"):
        exports["HERMES_DASHBOARD_PUBLIC_URL"] = f"https://{uris[0]}"
    for name, value in exports.items():
        print(f"export {name}={shlex.quote(value)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
