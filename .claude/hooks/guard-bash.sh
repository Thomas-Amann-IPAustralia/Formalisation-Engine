#!/usr/bin/env bash
# PreToolUse hook for Bash. A tripwire, not a security boundary: the real controls are
# the deny rules in settings.json and the live-mode guard inside engine.llm.
# Exit 2 blocks the command and shows the message to Claude.
set -uo pipefail

input="$(cat)"
cmd="$(jq -r '.tool_input.command // empty' <<<"$input" 2>/dev/null)"
[ -z "$cmd" ] && exit 0

block() {
  echo "Blocked by .claude/hooks/guard-bash.sh: $1" >&2
  exit 2
}

if grep -Eq 'ENGINE_ALLOW_LIVE_LLM|ENGINE_LLM_MODE=(live|record)|--llm-mode[= ]+(live|record)' <<<"$cmd"; then
  block "live and record LLM runs are Tom's to start, because they cost money and change recorded fixtures. Use replay mode, or ask Tom to run it."
fi

if grep -Eq '(^|[;&|[:space:](])git[[:space:]]+push([[:space:]]|$)' <<<"$cmd"; then
  block "pushing is Tom's call. Commit locally and say what is ready."
fi

if grep -Eq '(^|[;&|[:space:](])pip3?[[:space:]]+install|-m[[:space:]]+pip[[:space:]]+install' <<<"$cmd"; then
  block "dependencies are managed with uv. Ask Tom first, then use 'uv add <package>'."
fi

if grep -Eq '(^|[;&|[:space:](])rm[[:space:]]+-[A-Za-z]*[rR][A-Za-z]*[[:space:]].*(spec-src|gold|snapshots|tests/fixtures|docs/spec)' <<<"$cmd"; then
  block "recursive delete of a protected directory."
fi

exit 0
