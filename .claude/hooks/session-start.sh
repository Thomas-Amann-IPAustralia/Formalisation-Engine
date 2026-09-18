#!/usr/bin/env bash
# SessionStart hook. Plain stdout from this event is added to Claude's context,
# so keep it short and factual (statements, not instructions).
set -uo pipefail

root="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$root" || exit 0

if [ -f docs/STATUS.md ]; then
  echo "Current project status, from docs/STATUS.md:"
  head -n 40 docs/STATUS.md
  echo
fi

branch="$(git branch --show-current 2>/dev/null || echo unknown)"
changed="$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')"
echo "Git branch: ${branch:-detached}. Uncommitted files: ${changed}."
echo "LLM mode for commands run in this session: ${ENGINE_LLM_MODE:-unset}."
exit 0
