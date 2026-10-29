# Envoy Agent ◈

**Envoy is a virtual operations engineer.** It runs, observes and troubleshoots the systems you
give it access to, on your behalf: it investigates before it changes anything, prefers read-only
checks, states the blast radius of a change before making it, and asks before anything
destructive or production-affecting.

Envoy runs the same agent core across a CLI, a terminal UI, a web dashboard and a messaging
gateway. It keeps memory and skills across sessions, delegates to subagents, runs scheduled jobs,
and drives a real terminal and browser. It is designed to be deployed inside the larger Envoy
platform on **Tanzu Platform for Cloud Foundry**, with its model served by the **Tanzu AI
Service**.

<table>
<tr><td><b>Operations first</b></td><td>Investigate-then-act behaviour, approval prompts for dangerous commands, and a guard that stops the agent from killing its own gateway.</td></tr>
<tr><td><b>Web dashboard</b></td><td>A VMware Clarity–styled console for sessions, chat, configuration, models, tools, skills and scheduled jobs.</td></tr>
<tr><td><b>Learns as it works</b></td><td>Agent-curated memory, skills created from experience and refined in use, and full-text search over past sessions.</td></tr>
<tr><td><b>Scheduled automations</b></td><td>A built-in cron scheduler for health checks, reports and audits that run unattended.</td></tr>
<tr><td><b>Any OpenAI-compatible model</b></td><td>Binds to the Tanzu AI Service out of the box; any other provider or self-hosted endpoint works through <code>envoy model</code>.</td></tr>
</table>

---

## Deploy on Tanzu Platform for Cloud Foundry

Envoy deploys as source with its own buildpack, not as a container. The buildpack stages the
pinned, hash-verified toolchain (Python, uv, Node, ripgrep) and builds the Python environment
from `uv.lock`; the start command binds the AI Service model and serves the dashboard.

```bash
source ./activate                       # node + npm for the frontend build
deploy/cloudfoundry/prepare.sh          # builds the dashboard + TUI, packages the buildpack
cf create-buildpack envoy_buildpack deploy/cloudfoundry/build/envoy_buildpack-0.1.0.zip 99
cf create-service ai-models gpt-5.4 envoy-agent-chat
cf push -f deploy/cloudfoundry/manifest.yml --vars-file deploy/cloudfoundry/vars/techbrese.yml
```

See [deploy/cloudfoundry/README.md](deploy/cloudfoundry/README.md) for dashboard credentials,
model selection, storage and verification.

## Run locally

```bash
source ./activate      # provisions the pinned toolchain for this checkout
envoy setup            # pick a provider and model
envoy                  # chat in the terminal
envoy dashboard        # the web dashboard on http://127.0.0.1:9119
```

Useful commands:

| Command | What it does |
|---|---|
| `envoy model` | Choose a provider and model, or add a custom OpenAI-compatible endpoint |
| `envoy tools` | Enable or disable toolsets |
| `envoy skills` | Browse and manage skills |
| `envoy cron` | Manage scheduled jobs |
| `envoy gateway` | Run the messaging gateway |
| `envoy doctor` | Diagnose the installation |

The `hermes` command still works as an alias of `envoy`. <!-- rebrand:keep -->

## Documentation

Reference documentation lives in [website/docs](website/docs). Configuration is in
`config.yaml` under the Envoy home directory; secrets go in `.env` beside it.

## Development

`AGENTS.md` is the contributor guide. Rebranding is applied by
[scripts/rebrand/rebrand.py](scripts/rebrand/rebrand.py), which rewrites user-visible text only and
can be re-run after merging upstream changes.

## License and attribution

MIT — see [LICENSE](LICENSE).
Envoy Agent is a fork of [Hermes Agent](https://github.com/NousResearch/hermes-agent) by Nous Research, used under the MIT license. <!-- rebrand:keep -->
