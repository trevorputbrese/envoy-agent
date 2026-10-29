#!/usr/bin/env bash
# Web process: point Envoy at its bound AI Service model, then serve the dashboard on $PORT.
set -euo pipefail

mkdir -p "$HERMES_HOME"
chmod 0700 "$HERMES_HOME"

# The model's key reaches the agent only through this process's environment (config.yaml names
# the variable, never the value).
eval "$("$HERMES_PYTHON" "$(dirname "$0")/vcap_config.py")"

# A routed dashboard is a public bind, which Envoy refuses to serve without an auth provider.
if [ -z "${HERMES_DASHBOARD_BASIC_AUTH_USERNAME:-}" ] || \
   [ -z "${HERMES_DASHBOARD_BASIC_AUTH_PASSWORD:-}${HERMES_DASHBOARD_BASIC_AUTH_PASSWORD_HASH:-}" ]; then
  echo "envoy: bind the user-provided service envoy-agent-dashboard-auth (username plus" \
       "password_hash or password) before starting the dashboard" >&2
  exit 1
fi

exec envoy dashboard --host 0.0.0.0 --port "${PORT:-8080}" --skip-build --no-open
