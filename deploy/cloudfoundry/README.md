# Envoy Agent on Tanzu Platform for Cloud Foundry

Envoy deploys as source, staged by its own buildpack (`buildpack/`), not as a container image.
One app instance serves the web dashboard on the routed port; the dashboard's chat runs the
agent's TUI in the same container. The chat model comes from a bound Tanzu AI Service
(`ai-models`) instance.

## What the buildpack does

| Phase | Work |
|---|---|
| `detect` | Matches an Envoy checkout (`envoy` launcher, `hermes_cli/`, `pm/lock.json`). |
| `supply` | Stages the uv pinned by `pm/lock.json` (sha256-checked), bootstraps Python with it, then has pm stage the pinned Python, Node, npm, ripgrep and ffmpeg into the dependency directory. Builds the venv from `uv.lock` with the extras in `ENVOY_BUILDPACK_EXTRAS` (default `web mcp ddgs pty cron`). Writes `.profile.d/00-envoy.sh`, the start script and the `envoy` command. |
| `finalize` | Uses the prebuilt dashboard (`hermes_cli/web_dist`) and TUI (`.envoy-cf/tui`), or builds them with the pinned Node when a push carries neither. Stamps the tree as platform-managed so `envoy update` defers to `cf push`. |
| `release` | `web: exec .envoy-cf/lib/start.sh` |

At start, `lib/vcap_config.py` reads `VCAP_SERVICES` and recognises each binding by what it
carries, never by its instance name, so the app pushes unchanged to any foundation:

| Binding | Recognised by | Used as |
|---|---|---|
| Chat model | credentials with `api_base`, `api_key`, `model_name` and the `chat` capability (`ai-models`) | named custom provider `tanzu-ai` (`model.provider: custom:tanzu-ai`) |
| Dashboard login | a user-provided service with `username` and `password_hash` (or `password`), optional `secret` | the dashboard's `HERMES_DASHBOARD_BASIC_AUTH_*` settings |
| Home volume (optional) | any binding with a read-write `volume_mounts` entry (block-storage, nfs, smb) | `<mount>/envoy-home` as Envoy's home folder |

With several bindings of one kind, `ENVOY_CHAT_SERVICE`, `ENVOY_DASHBOARD_AUTH_SERVICE` or
`ENVOY_VOLUME_SERVICE` names the one to use; an explicit `HERMES_HOME` overrides the volume.
The model's key stays in the process environment (`ENVOY_AI_API_KEY`); `config.yaml` names the
variable, never the value. The dashboard then starts on `0.0.0.0:$PORT` behind its login.

On a volume, the rebuildable directories (`cache`, `image_cache`, `audio_cache`, `installs`)
are links to the container disk, so only state (config, sessions, memory, skills, logs) uses the
volume, and ended sessions are pruned after `sessions.retention_days` (90) unless `config.yaml`
sets `sessions.auto_prune` itself. Envoy's state is a few MB to start, so a 1 GB volume lasts.

Two AI Service proxy limits are configured for you:

- It answers HTTP 500 to the `developer` message role Envoy gives GPT-5 models, so the provider
  declares `capabilities: {developer_role: false}` and Envoy sends `system` instead.
- It rejects function tools combined with any `reasoning_effort` but `none`, so
  `agent.reasoning_effort` defaults to `none` (override with `ENVOY_REASONING_EFFORT`).

The venv and tool store record their staging paths. The profile script links
those paths to the droplet (`/home/vcap/app`, `/home/vcap/deps`) before anything starts, so
nothing is rewritten after staging.

## Deploy

Requires the CF CLI targeted at the space, admin rights for `create-buildpack` (or ask an
operator to install the zip), and the checkout's toolchain (`source ./activate`).

```bash
deploy/cloudfoundry/prepare.sh
cf create-buildpack envoy_buildpack deploy/cloudfoundry/build/envoy_buildpack-0.1.0.zip 99
cf create-service ai-models gpt-5.4 envoy-agent-chat
cf create-user-provided-service envoy-agent-dashboard-auth -p dashboard-auth.json
cf create-service block-storage on-demand-1024 envoy-block-store   # optional persistent home
cf push -f deploy/cloudfoundry/manifest.yml --vars-file deploy/cloudfoundry/vars/techbrese.yml
```

The manifest takes the route and the service list from a vars file per foundation
(`vars/techbrese.yml`; copy `vars/example.yml` for another). The names are yours to choose.

`dashboard-auth.json` holds `username`, `password_hash` and `secret` (a random signing key, e.g.
`openssl rand -base64 32`; sessions survive restarts with it). Keep the file private and delete it
after creating the service. The start script exports these as the dashboard's
`HERMES_DASHBOARD_BASIC_AUTH_*` settings. They live in a service binding rather than `cf set-env`
because `cf push` prints app environment variables in its manifest diff.

Make the password hash with the dashboard's own helper:

```bash
.venv/bin/python -c "import getpass; from plugins.dashboard_auth.basic import hash_password; print(hash_password(getpass.getpass()))"
```

To pick up a buildpack change: `cf update-buildpack envoy_buildpack -p <zip>` then
`cf restage envoy-agent`. Each push reuses the staging cache (uv wheels, pm receipts).

## Operate

```bash
cf app envoy-agent
curl -fsS https://envoy-agent.apps.techbrese.com/api/health
cf ssh envoy-agent -c 'envoy doctor'
cf logs envoy-agent --recent
```

## Limits to know

- **Without a volume, storage is ephemeral.** The home falls back to `~/.envoy-home` on the
  container disk, so memory, sessions and dashboard edits are lost on restart or restage; the
  start log says which one is in use (`envoy: home ... (volume)`).
- **Techbrese block storage does not attach yet.** Binding `envoy-block-store` fails at
  container start with `failed to mount volume ... timed out checking for mount source
  /var/vcap/data/dynamic_disks/... after: 20m0s`: the cell never receives the vSphere disk. That
  is the foundation's block-storage/vSphere setup; the binding stays out of `vars/techbrese.yml`
  until it works.
- **One shared login.** The username/password provider guards the dashboard with a single
  credential. For an internet-facing route, prefer the dashboard's OIDC provider against the
  platform's SSO.
- **Single instance.** Envoy keeps state on local disk; do not scale past one instance.
- **Staging needs the app's memory again.** A push stages in a second 2G container while the old
  instance runs. If the org quota is nearly full (`organization's memory limit exceeded: staging
  requires 2048M memory`), `cf stop envoy-agent` first and accept the brief downtime.
