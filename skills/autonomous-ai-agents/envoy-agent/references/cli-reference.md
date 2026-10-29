# Envoy CLI Reference

Live sources when anything looks stale: `envoy --help`, `envoy <command> --help`,
https://github.com/trevorputbrese/envoy-agent/blob/main/website/docs/reference/cli-commands.md

### Global Flags

```
envoy [flags] [command]        (no subcommand = interactive chat)

  --version, -V             Show version
  -z, --oneshot PROMPT      One-shot: print ONLY the final response (for scripts/pipes)
  -m MODEL  --provider P    Model/provider override for this invocation
  -t, --toolsets LIST       Comma-separated toolsets for this invocation
  --resume, -r SESSION      Resume session by ID or title
  --continue, -c [NAME]     Resume by name, or most recent session
  --worktree, -w            Isolated git worktree mode (parallel agents)
  --skills, -s SKILL        Preload skills (comma-separate or repeat)
  --profile, -p NAME        Use a named profile
  --yolo                    Skip dangerous command approval
  --tui / --cli             Force the Ink TUI / classic REPL
  --ignore-rules            Skip AGENTS.md/SOUL.md/memory/skill injection
  --safe-mode               Disable ALL customizations (troubleshooting)
  --pass-session-id         Include session ID in system prompt
```

### Chat

```
envoy chat [flags]
  -q, --query TEXT          Single query, non-interactive
  --image PATH              Attach a local image to a single query
  -Q, --quiet               Suppress banner, spinner, tool previews
  --checkpoints             Enable filesystem checkpoints (/rollback)
  --max-turns N             Cap tool-calling iterations
  --source TAG              Session source tag (default: cli)
```
(plus the global flags above)

### Configuration

```
envoy setup [section]      Wizard (model|tts|terminal|gateway|tools|agent)
envoy model                Interactive model/provider picker
envoy fallback [add|remove|list]  Fallback provider chain
envoy config [show|edit|get|set|unset|path|env-path|check|migrate]
envoy login / logout       OAuth sign-in / clear stored auth
envoy doctor [--fix]       Check dependencies and config
envoy status [--full]      Component summary (--full: every section)
```

### Tools & Skills

```
envoy tools [list|enable NAME|disable NAME]   Per-platform toolsets (curses UI with no args)

envoy skills list|browse|search QUERY|inspect ID
envoy skills install ID    Hub identifier OR a direct https://…/SKILL.md URL
envoy skills config        Enable/disable skills per platform
envoy skills check|update|uninstall|publish PATH
envoy skills tap add REPO  Add a GitHub repo as a skill source
envoy bundles              Skill bundles (one /<name> alias loads several skills)
```

### MCP Servers

```
envoy mcp add NAME (--url or --command) | remove | list | test NAME
envoy mcp catalog | install NAME     Curated catalog install
envoy mcp configure NAME             Toggle tool selection
envoy mcp-serve                      Run Envoy as an MCP server (mcp-serve plugin)
```
Details (transport, tool discovery, catalog): `references/native-mcp.md`.

### Gateway (Messaging Platforms)

```
envoy gateway run|install|start|stop|restart|status|setup
```

20+ platforms: Telegram, Discord, Slack, WhatsApp (Baileys + Business Cloud API), iMessage (Photon — `envoy photon setup`), Signal, Email, SMS, Matrix, Mattermost, Teams, LINE, SimpleX, ntfy, Google Chat, Home Assistant, DingTalk, Feishu, WeCom, Weixin, API Server, Webhooks. Open WebUI connects via the API Server adapter. Most adapters ship under `plugins/platforms/`.
Docs: https://github.com/trevorputbrese/envoy-agent/tree/main/website/docs/user-guide/messaging

### Sessions

```
envoy sessions list|browse|rename ID TITLE|delete ID|export OUT|prune|stats
```

### Cron / Webhooks

```
envoy cron list|create SCHED|edit ID|pause|resume|run ID|remove|status
    Schedules: '30m', 'every 2h', '0 9 * * *', ISO timestamp
envoy webhook subscribe NAME|list|remove NAME|test NAME
```
Webhook payloads/routes: `references/webhooks.md`.

### Profiles

```
envoy profile list|create NAME (--clone|--clone-all|--clone-from)|use|show|delete
envoy profile rename A B | alias NAME | export NAME | import FILE
envoy profile migrate-identity A B   Retry a completed rename's session/routing identity migration
```

### Credentials & Pools

```
envoy auth                 Interactive credential manager
envoy auth add [PROVIDER]  Add OAuth or API-key credential (nous, openai-codex, qwen-oauth, …)
envoy auth list|remove P IDX|reset PROVIDER|status
```
Multiple credentials per provider form a pool that rotates automatically and skips exhausted keys.

### Other

```
envoy desktop / gui        Native desktop app
envoy dashboard            Web admin panel + embedded chat (--stop / --status)
envoy proxy                OpenAI-compatible local proxy backed by an OAuth provider
envoy portal               Quick setup / sign in via Nous Portal
envoy kanban <verb>        Multi-agent work-queue board
envoy project              Named multi-folder workspaces
envoy skin list|use|set    Switch/tweak skins (see references/themes.md)
envoy pets <verb>          Pet mascots (see references/petdex.md)
envoy memory setup|status|off|reset   Memory provider
envoy secrets bitwarden|onepassword   External secret stores
envoy moa                  Mixture-of-Agents slots
envoy hooks / security / backup / import / checkpoints / console
envoy logs [-f] [errors]   View agent/error logs
envoy send                 One-off message through a gateway platform
envoy pairing / plugins / insights / journey / computer-use
envoy acp                  ACP server (IDE integration)
envoy completion bash|zsh|fish
envoy update / uninstall
```

Plugin- and provider-supplied subcommands (e.g. `envoy photon setup`) only appear once their plugin is installed/active. Importing from OpenClaw, Claude Code, Codex CLI or Cursor (`envoy import-agent <agent>`, plus the older `envoy claw migrate|cleanup`) comes from the `agent-importers` plugin; a fresh `envoy setup` that finds one of those agents offers to install it.

### Where to Find Things

| Looking for... | Location |
|---|---|
| Config options | `envoy config edit` · [Configuration docs](https://github.com/trevorputbrese/envoy-agent/blob/main/website/docs/user-guide/configuration.md) |
| Tools / toolsets | `envoy tools list` · [Tools reference](https://github.com/trevorputbrese/envoy-agent/blob/main/website/docs/reference/tools-reference.md) |
| Skills catalog | `envoy skills browse` · [Skills catalog](https://github.com/trevorputbrese/envoy-agent/blob/main/website/docs/reference/skills-catalog.md) |
| Provider setup | `envoy model` · [Providers guide](https://github.com/trevorputbrese/envoy-agent/blob/main/website/docs/integrations/providers.md) |
| Env variables | `envoy config env-path` · [Env vars reference](https://github.com/trevorputbrese/envoy-agent/blob/main/website/docs/reference/environment-variables.md) |
| Gateway logs | `~/.hermes/logs/gateway.log` (or `envoy logs`) |
| Sessions | `envoy sessions browse` (reads state.db) |
