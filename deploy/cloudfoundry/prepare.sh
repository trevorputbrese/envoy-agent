#!/usr/bin/env bash
# Prepare a `cf push` of this checkout: build the dashboard and the TUI it embeds (plain
# JavaScript, so building them here is equivalent to building on the platform) and package the
# Envoy buildpack as deploy/cloudfoundry/build/envoy_buildpack-<version>.zip.
#
# Needs the checkout's toolchain on PATH (`source ./activate` provides node and npm).
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
root="$(cd "$here/../.." && pwd)"
cd "$root"

echo "-----> Installing frontend dependencies"
node scripts/build/node-deps.mjs --source "$root" --workspace ui-tui --workspace web
echo "-----> Building the TUI into .envoy-cf/tui"
# The build refuses an output inside its source tree, so it lands in a scratch dir first.
scratch="$(mktemp -d)"; trap 'rm -rf "$scratch"' EXIT
node scripts/build/tui.mjs --source "$root" --out "$scratch/tui"
rm -rf "$root/.envoy-cf/tui"; mkdir -p "$root/.envoy-cf"; cp -R "$scratch/tui" "$root/.envoy-cf/tui"
echo "-----> Building the dashboard into hermes_cli/web_dist"
(cd web && npm run build)

version="$(cat "$here/buildpack/VERSION")"
mkdir -p "$here/build"
zip="$here/build/envoy_buildpack-$version.zip"
rm -f "$zip"
(cd "$here/buildpack" && zip -qr "$zip" VERSION bin lib)
echo "-----> Buildpack: $zip"
