# Shared helpers for the Envoy buildpack phases. Sourced, never executed.

step() { echo "-----> $*"; }
info() { echo "       $*"; }
fail() { echo " !     $*" >&2; exit 1; }

case "$(uname -m)" in
  x86_64|amd64) ENVOY_TARGET=linux-x64 ;;
  aarch64|arm64) ENVOY_TARGET=linux-arm64 ;;
  *) fail "unsupported architecture $(uname -m)" ;;
esac

# pin FIELD PACKAGE LOCK: read a pinned artifact field (url | sha256 | version) from pm/lock.json
# before any Python exists. Same reader as setup-envoy's bootstrap: follow object names and
# braces, not indentation.
pin() {
  awk -F '"' -v package="$2" -v target="$ENVOY_TARGET" -v field="$1" '
    /^[[:space:]]*("[^"]+"[[:space:]]*:[[:space:]]*)?\{[[:space:]]*$/ {
      path[++depth] = $2; next
    }
    /^[[:space:]]*}[[:space:]]*,?[[:space:]]*$/ {
      delete path[depth--]; next
    }
    path[2] == "packages" && path[3] == package && $2 == field &&
      ((field == "version" && depth == 3) ||
       (depth == 5 && path[4] == "artifacts" && path[5] == target)) {
      print $4; exit
    }' "$3"
}

# stage_uv LOCK STORE: download the uv that pm/lock.json pins, check its sha256, unpack it into
# the pm tool store and print the binary path.
stage_uv() {
  local lock="$1" store="$2" version url sha entry tmp archive got
  version="$(pin version uv "$lock")"
  entry="$store/uv-$version-$ENVOY_TARGET"
  if [ ! -x "$entry/uv" ]; then
    url="$(pin url uv "$lock")"; sha="$(pin sha256 uv "$lock")"
    [ -n "$url" ] && [ -n "$sha" ] || fail "pm/lock.json pins no uv for $ENVOY_TARGET"
    tmp="$(mktemp -d)"; archive="$tmp/${url##*/}"
    curl -fsSL --retry 3 -o "$archive" "$url" || fail "could not download $url"
    got="$(sha256sum "$archive" | cut -d' ' -f1)"
    [ "$got" = "$sha" ] || fail "uv sha256 mismatch (got $got, pinned $sha)"
    mkdir -p "$tmp/tree" "$store"
    tar -xzf "$archive" -C "$tmp/tree"
    rm -rf "$entry"
    mv "$tmp/tree"/uv-* "$entry" 2>/dev/null || mv "$tmp/tree" "$entry"
    rm -rf "$tmp"
  fi
  printf '%s\n' "$entry/uv"
}
