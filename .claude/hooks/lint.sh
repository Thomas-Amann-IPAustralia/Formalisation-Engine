#!/usr/bin/env bash
# PostToolUse hook for Edit and Write. Formats and lints the edited Python file.
# Only problems ruff cannot fix are shown to Claude (exit 2 on PostToolUse shows
# stderr to Claude; the edit itself has already happened).
set -uo pipefail

input="$(cat)"
file="$(jq -r '.tool_input.file_path // empty' <<<"$input" 2>/dev/null)"
case "$file" in
  *.py) ;;
  *) exit 0 ;;
esac
[ -f "$file" ] || exit 0
command -v uv >/dev/null 2>&1 || exit 0

root="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$root" || exit 0

uv run --quiet ruff format --quiet "$file" >/dev/null 2>&1 || true

out="$(uv run --quiet ruff check --fix --quiet --output-format concise "$file" 2>&1)"
rc=$?
if [ "$rc" -ne 0 ]; then
  {
    echo "ruff found problems it could not fix in ${file#"$root"/}:"
    head -n 20 <<<"$out"
  } >&2
  exit 2
fi
exit 0
