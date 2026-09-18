#!/usr/bin/env bash
# PreToolUse hook for Edit, Write and NotebookEdit. Blocks edits to paths that Tom owns
# or that scripts generate. Exit 2 blocks the edit and shows the message to Claude.
# Tom edits these files himself; hooks only constrain Claude.
set -uo pipefail

input="$(cat)"
file="$(jq -r '.tool_input.file_path // .tool_input.notebook_path // empty' <<<"$input" 2>/dev/null)"
[ -z "$file" ] && exit 0

root="${CLAUDE_PROJECT_DIR:-$(pwd)}"
case "$file" in
  /*) abs="$file" ;;
  *) abs="$root/$file" ;;
esac
# Normalise ".." and duplicate slashes before comparing.
abs="$(python3 -c 'import os, sys; print(os.path.normpath(sys.argv[1]))' "$abs" 2>/dev/null || echo "$abs")"
root="$(python3 -c 'import os, sys; print(os.path.normpath(sys.argv[1]))' "$root" 2>/dev/null || echo "$root")"

case "$abs" in
  "$root"/*) rel="${abs#"$root"/}" ;;
  *) exit 0 ;;  # outside the project: normal permission rules apply
esac

# Directory prefixes (ending in /) and exact paths or globs.
protected=(
  "spec-src/"
  "docs/spec/"
  "gold/"
  "snapshots/"
  "schema/"
  "tests/fixtures/llm_cache/"
  ".claude/hooks/"
  ".claude/settings.json"
  "tool/"
)

for p in "${protected[@]}"; do
  hit=""
  if [[ "$p" == */ ]]; then
    [[ "$rel" == "$p"* ]] && hit="yes"
  else
    # shellcheck disable=SC2053  # glob match is intended
    [[ "$rel" == $p ]] && hit="yes"
  fi
  if [ -n "$hit" ]; then
    echo "Blocked by .claude/hooks/protect-paths.sh: $rel is protected ($p). Tom owns this path or a script generates it. Describe the change you want instead." >&2
    exit 2
  fi
done
exit 0
