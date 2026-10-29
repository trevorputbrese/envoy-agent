"""Point Envoy at the chat model bound from the Tanzu AI Service, then print shell exports.

Reads ``VCAP_SERVICES`` for a binding whose credentials carry ``api_base``, ``api_key`` and
``model_name`` with the ``chat`` capability (the ``ai-models`` offering), writes the ``model``
block of ``$HERMES_HOME/config.yaml`` to a named custom provider (``tanzu-ai``), and prints
``export`` lines for the API key, the dashboard's public URL and its login (from the bound
user-provided service ``envoy-agent-dashboard-auth``). With several chat bindings,
``ENVOY_CHAT_SERVICE`` names the one to use. Everything else in config.yaml is left alone, so
settings changed from the dashboard survive a restart on persistent storage.
"""

from __future__ import annotations

import json
import os
import shlex
import sys
from pathlib import Path

KEY_ENV = "ENVOY_AI_API_KEY"


def chat_bindings(vcap: dict) -> list[dict]:
    found = []
    for bindings in vcap.values():
        for binding in bindings:
            creds = binding.get("credentials") or {}
            caps = creds.get("model_capabilities") or []
            if creds.get("api_base") and creds.get("api_key") and creds.get("model_name") and "chat" in caps:
                found.append(binding)
    return found


def pick(bindings: list[dict]) -> dict | None:
    wanted = os.environ.get("ENVOY_CHAT_SERVICE", "").strip()
    if wanted:
        named = [b for b in bindings if wanted in (b.get("name"), b.get("instance_name"))]
        if not named:
            sys.exit(f"envoy: ENVOY_CHAT_SERVICE={wanted} is not a bound chat model")
        return named[0]
    return bindings[0] if bindings else None


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
    wanted = os.environ.get("ENVOY_DASHBOARD_AUTH_SERVICE", "envoy-agent-dashboard-auth")
    for binding in vcap.get("user-provided", []):
        if wanted in (binding.get("name"), binding.get("instance_name")):
            creds = binding.get("credentials") or {}
            return {env: str(creds[field]) for field, env in DASHBOARD_AUTH_FIELDS.items() if creds.get(field)}
    return {}


def main() -> int:
    home = Path(os.environ["HERMES_HOME"])
    vcap = json.loads(os.environ.get("VCAP_SERVICES") or "{}")
    exports: dict[str, str] = dashboard_auth(vcap)
    binding = pick(chat_bindings(vcap))
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
    sys.exit(main())
