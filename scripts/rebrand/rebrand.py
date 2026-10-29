#!/usr/bin/env python3
"""Rebrand Hermes Agent to Envoy Agent in user-visible text.

Only prose changes: Python strings and comments, Markdown, locale YAML, TypeScript copy, shell
messages. Identifiers stay as they are (module names, ``HERMES_*`` environment variables, the
``~/.hermes`` state directory, ``@hermes/*`` workspace packages, protocol headers and storage
keys), so the fork keeps merging cleanly with upstream.

Re-runnable. After an upstream merge, take upstream's side of any conflict in rebranded text and
run ``python scripts/rebrand/rebrand.py --apply`` again; a second run over clean output changes
nothing.

    python scripts/rebrand/rebrand.py            # dry run: per-rule and per-file counts
    python scripts/rebrand/rebrand.py --apply    # rewrite files in place
"""

from __future__ import annotations

import argparse
import collections
import io
import re
import subprocess
import sys
import tokenize
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FORK = "trevorputbrese/envoy-agent"
FORK_URL = f"https://github.com/{FORK}"
FORK_RAW = f"https://raw.githubusercontent.com/{FORK}/main"

# Paths whose bytes are load-bearing or historical rather than copy.
EXCLUDED_PREFIXES = (
    ".github/",
    "contributors/",
    "scripts/rebrand/",
    "tests/compat/",
)
EXCLUDED_NAMES = {
    "LICENSE",
    "uv.lock",
    "package-lock.json",
    "flake.lock",
    "package.json",
}

# Extension -> how freely a bare lowercase "hermes" may change.
#   prose:  every standalone word (Markdown, YAML locales, plain text)
#   python: standalone words inside string and comment tokens
#   code:   only command references ("hermes setup", "`hermes`", "hermes --help")
PROSE_EXTS = {".md", ".mdx", ".txt", ".yaml", ".yml"}
CODE_EXTS = {".ts", ".tsx", ".js", ".mjs", ".cjs", ".sh", ".ps1", ".html"}
PY_EXTS = {".py"}

# Subcommands seen after "hermes " in the tree; bare "hermes" in code files changes only here.
SUBCOMMANDS = (
    "update gateway auth setup plugins model config tools sessions cron doctor pm mcp serve skills "
    "profile kanban chat dashboard curator logs egress peer secrets send debug desktop computer-use "
    "webapp vault meet portal worktree pairing photon status import home proxy hooks fallback "
    "verify memory backup pets import-agent approvals pause lsp migrate checkpoints whatsapp slack "
    "resume root uninstall bundles webhook project journey acp moa prompt-size logout console "
    "codex-runtime completion dump tool launchers login browser connectors security gui skin "
    "session install models trace version help version insights claw honcho env"
).split()


def _docs_url(match: re.Match[str]) -> str:
    """Point a hosted-docs link at the same page in the fork's website/docs tree."""
    path = match.group(1).strip("/").split("#", 1)[0]
    docs = ROOT / "website" / "docs"
    if path:
        for suffix in (".md", ".mdx"):
            if (docs / f"{path}{suffix}").is_file():
                return f"{FORK_URL}/blob/main/website/docs/{path}{suffix}"
        if (docs / path).is_dir():
            return f"{FORK_URL}/tree/main/website/docs/{path}"
    return f"{FORK_URL}/tree/main/website/docs"


# Applied to every eligible span, in order.
URL_RULES: list[tuple[str, re.Pattern[str], object]] = [
    # The model catalog is committed, so the fork serves it; the other feeds under docs/api/,
    # llms*.txt and images are built by the upstream docs deploy and keep their upstream URLs.
    ("catalog-feed", re.compile(r"https?://hermes-agent\.nousresearch\.com/docs/api/model-catalog\.json"),
     f"{FORK_RAW}/website/static/api/model-catalog.json"),
    ("docs-url", re.compile(r"https?://hermes-agent\.nousresearch\.com/docs(?!/api/|/llms|/img/)/?([\w./#-]*)"),
     _docs_url),
    ("install-url", re.compile(r"https?://hermes-agent\.nousresearch\.com/install\.(sh|ps1|cmd)"),
     lambda m: f"{FORK_RAW}/scripts/install.{m.group(1)}"),
    ("site-url", re.compile(r"https?://hermes-agent\.nousresearch\.com(?![\w.-])/?(?![\w/])"), FORK_URL),
    ("raw-repo", re.compile(r"raw\.githubusercontent\.com/NousResearch/hermes-agent", re.IGNORECASE),
     f"raw.githubusercontent.com/{FORK}"),
    ("repo-slug", re.compile(r"(?<![\w.-])NousResearch/hermes-agent(?![\w-])", re.IGNORECASE), FORK),
]

NAME_RULES: list[tuple[str, re.Pattern[str], str]] = [
    ("Hermes Agent", re.compile(r"\bHermes([ -])Agent\b"), r"Envoy\1Agent"),
    ("HERMES AGENT", re.compile(r"\bHERMES([ -])AGENT\b"), r"ENVOY\1AGENT"),
    # "Hermes 3", "Hermes-4-405B" and "Nous Hermes" are Nous's language models, not this agent.
    # ``X-Hermes-Session-Token`` and its siblings are wire protocol, not copy.
    # "Hey Hermes" is the wake word the bundled hotword model (tools/wakewords/hey_hermes.tflite)
    # was trained on; renaming the phrase would advertise one the default engine never hears.
    ("Hermes", re.compile(r"(?<!Nous[ -])(?<![Xx]-)(?<![Hh]ey )(?<!HEY )\bHermes\b(?![- ]?\d)"), "Envoy"),
    # ``HERMES-CONTEXT-COMPRESSION``, ``@@HERMES-KERNEL-``: upper-case sentinels code matches.
    ("HERMES", re.compile(r"(?<![Xx]-)(?<!HEY )\bHERMES\b(?![- ]?\d|-[A-Z])"), "ENVOY"),
    ("Nous-approved", re.compile(r"\bNous-approved\b"), "curated"),
    # The caduceus is Hermes's emblem; Envoy's is the nested diamond.
    ("glyph", re.compile("\u2624"), "\u25c8"),
    # "a Hermes" / "Hermes' own" read wrong once the name starts with a vowel and lacks the s.
    ("an Envoy", re.compile(r"\b([Aa]) (Envoy|ENVOY)\b"), r"\1n \2"),
    # The self-help skill ships as skills/autonomous-ai-agents/envoy-agent, so a skill listing it
    # as related names it that way (the skill linter rejects a dangling related_skills entry).
    ("related skill", re.compile(r"(?m)^([ \t]*related_skills:[^\n]*?)\bhermes-agent\b(?!-)"), r"\1envoy-agent"),
]
# Prose and Python string tokens only: in raw code text the apostrophe after a name can be the
# closing quote of a single-quoted string ('Restart Hermes').
POSSESSIVE = ("Envoy's", re.compile(r"(?<![\w'\"‘`])Envoy'(?=[\s,.)])"), "Envoy's")

# Never a rename: a path, flag or key part (``.hermes``, ``hermes-agent``, ``hermes.yaml``,
# ``source=hermes``, an f-string namespace ``hermes.{name}``), a Nous model name (``hermes 3``), a
# regex (``hermes[-_ ]?[34]``, ``hermes (?:pid=...)``) or a ``hermes pid=<n>`` record git keeps.
# The Docker image's Unix account is ``hermes`` (``s6-setuidgid hermes``, ``docker exec -u hermes``,
# ``find ! -user hermes``, "the `hermes` user"): an account name, never a command. "hey hermes" is
# the wake word (see the "Hermes" rule).
_NOT_ACCOUNT = r"(?<!-user )(?<!-group )(?<!-u )(?<!setuidgid )(?<!USER )(?<!chown )(?<!gosu )(?<![Hh]ey )"
_BARE = _NOT_ACCOUNT + r"(?<![\w./~@:#$%\\/=-])hermes(?![\w-]|\.[A-Za-z{]|:\S|/|\[(?!/)| ?\d| \(\?| [a-z_]+=|`{0,2} user\b)"
LOWER_PROSE = re.compile(_BARE)
LOWER_COMMAND = re.compile(
    _NOT_ACCOUNT + r"(?<![\w./~@:#$%\\/-])hermes(?!`{0,2} user\b)(?=(?: +(?:"
    + "|".join(map(re.escape, SUBCOMMANDS)) + r")\b)| +-{1,2}[a-z]|`)"
)
# Python source embedded in a string literal (subprocess ``-c`` payloads, test fixtures).
_EMBEDDED_CODE = re.compile(r"sys\.argv|\bimport\b(?!-)|\bdef \w|startswith\(|endswith\(|==|\bargv\[|\bexec\(|=\s*\[")


def _lower_envoy(match: re.Match[str]) -> str:
    """``'hermes'`` quoted inside a sentence names an identifier (a profile, toolset, argv[0]),
    and a ``hermes:`` mapping key opening a YAML line (``metadata.hermes`` skill frontmatter, the
    ``slash.hermes`` locale entry, a compose service) is a key code looks up."""
    text, start, end = match.string, match.start(), match.end()
    if start and end < len(text) and text[start - 1] in "'\"" and text[end] == text[start - 1]:
        return match.group(0)
    if text.startswith(":", end) and not text[text.rfind("\n", 0, start) + 1:start].strip(" \t-"):
        return match.group(0)
    return "envoy"


class Tally:
    def __init__(self) -> None:
        self.rules: collections.Counter[str] = collections.Counter()
        self.files: collections.Counter[str] = collections.Counter()


def _sub(rule: str, pattern: re.Pattern[str], repl: object, text: str, tally: Tally, path: str) -> str:
    out, n = pattern.subn(repl, text)  # type: ignore[arg-type]
    if n:
        tally.rules[rule] += n
        tally.files[path] += n
    return out


_BOX_EDGE = re.compile(r"[│║┃](?=[\s\"'`,)\\n]*$)")


def pad_box_lines(original: str, updated: str) -> str:
    """Keep box-drawn banners square: "Envoy" is a column shorter than "Hermes", so a line whose
    right edge moved left gets the difference back as spaces in front of that edge."""
    old_lines, new_lines = original.split("\n"), updated.split("\n")
    if len(old_lines) != len(new_lines):
        return updated
    for i, (old, new) in enumerate(zip(old_lines, new_lines)):
        shrink = len(old) - len(new)
        old_edge, new_edge = _BOX_EDGE.search(old), _BOX_EDGE.search(new)
        if shrink > 0 and old_edge and new_edge and old_edge.start() - new_edge.start() == shrink:
            new_lines[i] = new[:new_edge.start()] + " " * shrink + new[new_edge.start():]
    return "\n".join(new_lines)


def rebrand_span(text: str, lower: re.Pattern[str] | None, tally: Tally, path: str, *,
                 possessive: bool = True) -> str:
    original = text
    for rule, pattern, repl in URL_RULES:
        text = _sub(rule, pattern, repl, text, tally, path)
    for rule, pattern, repl in NAME_RULES + ([POSSESSIVE] if possessive else []):
        text = _sub(rule, pattern, repl, text, tally, path)
    if lower is not None:
        text = _sub("hermes (command)", lower, _lower_envoy, text, tally, path)
    return pad_box_lines(original, text) if text != original else text


_PY_TEXT_TOKENS = {tokenize.STRING, tokenize.COMMENT}
if hasattr(tokenize, "FSTRING_MIDDLE"):
    _PY_TEXT_TOKENS.add(tokenize.FSTRING_MIDDLE)
if hasattr(tokenize, "TSTRING_MIDDLE"):
    _PY_TEXT_TOKENS.add(tokenize.TSTRING_MIDDLE)
_FSTRING_STARTS = {getattr(tokenize, name) for name in ("FSTRING_START", "TSTRING_START") if hasattr(tokenize, name)}


def _is_identifier_literal(token: str) -> bool:
    """A one-word literal (``"hermes"``, ``"hermes."``, ``"hermes@x"``) is an identifier, and a
    literal holding Python source is code; neither is a sentence."""
    body = token.lstrip("rRbBuUfFtT").strip("'\"")
    return not re.search(r"\s", body.strip()) or bool(_EMBEDDED_CODE.search(body))


def rebrand_python(src: str, tally: Tally, path: str) -> str:
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(src).readline))
    except (tokenize.TokenError, SyntaxError, IndentationError):
        return src
    lines = src.splitlines(keepends=True)
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line))
    # A line carrying ``# rebrand:keep`` keeps its text (test data spelling an identifier, such as a
    # bot's default wake word, inside a sentence).
    kept = {i for i, line in enumerate(lines, 1) if KEEP_MARKER in line}
    pieces: list[str] = []
    cursor = 0
    previous = None
    for index, tok in enumerate(tokens):
        opens_fstring, previous = previous is not None and previous.type in _FSTRING_STARTS, tok
        if tok.type not in _PY_TEXT_TOKENS or kept.intersection(range(tok.start[0], tok.end[0] + 1)):
            continue
        start = offsets[tok.start[0] - 1] + tok.start[1]
        end = offsets[tok.end[0] - 1] + tok.end[1]
        original = src[start:end]
        # An f-string fragment ("`hermes ", "hermes {sub}") is part of a sentence or command line;
        # only a whole one-word literal is an identifier. A bare "hermes " opening the f-string
        # (f"hermes {profile_arg}pairing approve ...") starts a command line too; mid-string
        # (f"check_key {key} hermes {key}") it is an argument.
        fragment = tok.type != tokenize.STRING and tok.type != tokenize.COMMENT
        command = opens_fstring and original.endswith(" ")
        bare = original.strip() == "hermes" and not command if fragment else _is_identifier_literal(original)
        lower = None if bare else LOWER_PROSE
        # A fragment running into an interpolation ends at its ``{``: show the rules that brace, so
        # ``f"hermes.{name}"`` reads as the ``hermes.<x>`` namespace it builds, not a sentence's end.
        follows = index + 1 < len(tokens) and tokens[index + 1].string == "{" and fragment
        updated = rebrand_span(original + "{", lower, tally, path)[:-1] if follows else rebrand_span(
            original, lower, tally, path)
        if updated != original:
            pieces.append(src[cursor:start])
            pieces.append(updated)
            cursor = end
    if not pieces:
        return src
    pieces.append(src[cursor:])
    return "".join(pieces)


KEEP_MARKER = "rebrand:keep"


def _keeping_marked_lines(src: str, rewrite) -> str:
    """Rewrite *src* except lines carrying ``rebrand:keep`` (upstream attribution, for one)."""
    if KEEP_MARKER not in src:
        return rewrite(src)
    lines = src.split("\n")
    kept = {i: line for i, line in enumerate(lines) if KEEP_MARKER in line}
    holders = [f"\x00keep{i}\x00" if i in kept else line for i, line in enumerate(lines)]
    out = rewrite("\n".join(holders)).split("\n")
    return "\n".join(kept.get(i, line) for i, line in enumerate(out))


def _eligible(rel: str) -> str | None:
    if rel.startswith(EXCLUDED_PREFIXES) or Path(rel).name in EXCLUDED_NAMES:
        return None
    suffix = Path(rel).suffix.lower()
    if suffix in PY_EXTS:
        return "python"
    if suffix in PROSE_EXTS:
        return "prose"
    if suffix in CODE_EXTS:
        return "code"
    if suffix == ".json" and rel.startswith("locales/"):
        return "prose"
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true", help="rewrite files (default: dry run)")
    parser.add_argument("--top", type=int, default=25, help="files to list in the report")
    parser.add_argument("paths", nargs="*", help="limit to these tracked paths")
    args = parser.parse_args()

    listed = subprocess.run(["git", "ls-files", "-z", *args.paths], cwd=ROOT, capture_output=True, check=True,
                            timeout=120)
    tally = Tally()
    changed = 0
    for rel in listed.stdout.decode().split("\0"):
        kind = _eligible(rel) if rel else None
        if kind is None:
            continue
        path = ROOT / rel
        try:
            with path.open(encoding="utf-8", newline="") as fh:  # keep CRLF files CRLF
                src = fh.read()
        except (UnicodeDecodeError, FileNotFoundError, IsADirectoryError):
            continue
        if kind == "python":
            out = rebrand_python(src, tally, rel)
        else:
            out = _keeping_marked_lines(src, lambda text: rebrand_span(
                text, LOWER_PROSE if kind == "prose" else LOWER_COMMAND, tally, rel, possessive=kind == "prose"))
        if out != src:
            changed += 1
            if args.apply:
                with path.open("w", encoding="utf-8", newline="") as fh:
                    fh.write(out)

    verb = "rewrote" if args.apply else "would rewrite"
    print(f"{verb} {changed} files, {sum(tally.rules.values())} replacements")
    for rule, count in tally.rules.most_common():
        print(f"  {count:7d}  {rule}")
    print("top files:")
    for rel, count in tally.files.most_common(args.top):
        print(f"  {count:7d}  {rel}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
