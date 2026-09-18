---
name: wrap-up
description: Rewrite docs/STATUS.md at the end of a session so the next session starts from the current state. Use when Tom says to wrap up or finish.
disable-model-invocation: true
allowed-tools: Bash(git log *) Bash(git status *) Bash(git add *) Bash(git commit *) Bash(python3 scripts/spec_tools.py *)
---

!`git log --oneline -12 2>/dev/null || true`

!`python3 scripts/spec_tools.py coverage --summary 2>/dev/null || true`

Rewrite `docs/STATUS.md` under 30 lines, plain statements of fact, with headings `# Status`
(`Milestone:`, `Updated:` ISO date), `## Done recently`, `## In progress`, `## Next up`,
`## Blocked or failing`, `## Questions for Tom`. Drop stale detail. Show Tom the diff, then commit
as `docs: update status`.
