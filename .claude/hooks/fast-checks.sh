#!/usr/bin/env bash
# Stop hook. When Python files have changed, runs the type check and the fast tests.
# While they fail, exit 2 keeps Claude working and shows it the failures.
#
# Loop safety: blocks at most FE_STOP_HOOK_MAX_BLOCKS times (default 3) per user prompt,
# counted per session and prompt_id, then lets Claude stop and tells you why.
# Claude Code also overrides a Stop hook that keeps blocking without progress.
set -uo pipefail

input="$(cat)"
root="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$root" || exit 0
command -v uv >/dev/null 2>&1 || exit 0

# Question-only turns: nothing to check.
if [ -z "$(git status --porcelain -- '*.py' 2>/dev/null)" ]; then
  exit 0
fi

session="$(jq -r '.session_id // "nosession"' <<<"$input" 2>/dev/null)"
prompt="$(jq -r '.prompt_id // "noprompt"' <<<"$input" 2>/dev/null)"
state_dir="${TMPDIR:-/tmp}/formalisation-engine-hooks"
mkdir -p "$state_dir"
counter_file="$state_dir/stop-${session}-${prompt}"
attempts="$(cat "$counter_file" 2>/dev/null || echo 0)"
max_blocks="${FE_STOP_HOOK_MAX_BLOCKS:-3}"

report=""

out="$(uv run --quiet mypy src 2>&1)"
if [ $? -ne 0 ]; then
  report+="Type check (uv run mypy src):"$'\n'"$(tail -n 15 <<<"$out")"$'\n\n'
fi

out="$(uv run --quiet pytest -m fast -x -q --tb=line --no-header -p no:cacheprovider 2>&1)"
rc=$?
# Exit code 5 means no tests were collected, which is not a failure.
if [ "$rc" -ne 0 ] && [ "$rc" -ne 5 ]; then
  report+="Fast tests (uv run pytest -m fast):"$'\n'"$(tail -n 15 <<<"$out")"$'\n'
fi

if [ -z "$report" ]; then
  rm -f "$counter_file"
  exit 0
fi

if [ "$attempts" -ge "$max_blocks" ]; then
  rm -f "$counter_file"
  jq -nc --arg m "Fast checks were still failing after ${max_blocks} attempts, so Claude has stopped. Run 'uv run pytest -m fast' and 'uv run mypy src' to see why." \
    '{systemMessage: $m}'
  exit 0
fi

echo $((attempts + 1)) >"$counter_file"
{
  echo "Fast checks are failing. Fix them before finishing, or explain why they can't be fixed yet."
  echo
  printf '%s' "$report"
} >&2
exit 2
