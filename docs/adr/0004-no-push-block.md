# 0004. Remove the push block; keep the rest of the Bash guard

- Status: Accepted
- Date: 2026-09-19
- Related: NFR-SEC-01, DP-01

## Context

The starter kit blocked `git push` in three places: a deny rule in `.claude/settings.json`, a rule
in `.claude/hooks/guard-bash.sh`, and a line in `CLAUDE.md`. Tom asked what it was protecting
against and, if it got in the way, to remove it.

**What it protected against.** One thing: Claude pushing work to a shared branch that Tom had not
looked at. On a laptop that is a sensible default, because nothing is lost by waiting — the commit
sits in the local repository until Tom reviews it.

**Why it stopped being sensible.** The work moved to Claude Code on the web, which runs in a
throwaway container that is reclaimed after a period of inactivity. There, "commit locally and say
what is ready" means the commit is destroyed. The block no longer defers the push; it discards the
work. The one protection it offered — a human looks before it lands — is already provided by the
branch itself: Claude pushes to `claude/<name>`, never to `main`, and nothing merges without a
pull request Tom approves.

**It also did not work.** The rule matched the literal string `git push`, so
`git -C <path> push` walked straight past it. It stopped an absent-minded push, not a determined
one. A control that only stops the honest case, while costing the work in the normal case, is not
worth keeping.

## Decision

Remove the push block from the hook and move the deny rule to an allow rule. Keep the other three
rules in `guard-bash.sh`, and narrow one of them.

### What the Bash guard is, and what is left of it

It is a script that runs before every shell command Claude tries to run. It reads the command, and
if the text matches one of its patterns it refuses to run it and tells Claude why. It is a
tripwire against absent-mindedness, not a security boundary: anything that can be phrased
differently can get past it.

What stays, and why each is about protecting something that cannot be undone rather than about
restricting Claude:

| Rule | What it stops | Why it stays |
|---|---|---|
| Live or record LLM run | Claude spending Tom's API budget, and overwriting `tests/fixtures/llm_cache/` | Recorded responses are the ground truth every replay test compares against. A stray record run rewrites them and the whole suite silently starts testing the wrong thing. |
| `pip install` | Installing outside uv | Desyncs `uv.lock`, so CI and the laptop stop matching. Cheap to keep; has never misfired. |
| `rm -rf` of a protected directory | Recursive delete of `spec-src`, `gold`, `snapshots`, `tests/fixtures`, `docs/spec` | `gold/` and `spec-src/` are hand-written by Tom and are not regenerable. |

Removed:

| Rule | Why |
|---|---|
| `git push` | Above. |

Narrowed: the live-LLM rule matched its variable names anywhere in a command, so writing
documentation that merely mentioned them was blocked. It fired twice in one session against
attempts to write `.env.example`. It now matches an assignment or a flag, not a bare mention.

### Not changed: the write gap

`protect-paths.sh` runs on the `Edit`, `Write` and `NotebookEdit` tools only, so in principle a
shell write such as `sed -i docs/spec/...` reaches a protected path unchecked. In practice a Bash
read of `spec-src/` was refused by the permission layer when tried, so something above the hook is
covering at least part of this. Left as it is: the remaining exposure is Claude overwriting a file
that git can restore, and Tom's preference is fewer blocks, not more.

## Consequences

- Claude can push to its own `claude/<name>` branch without a prompt that nobody is present to
  answer. It still does not push to `main`, and still does not open a pull request unasked.
- The guard is now three rules about irreversible damage. If Tom wants the remaining ones gone,
  each is a contiguous block of four lines in `guard-bash.sh`.

## The edits Claude could not make

Claude is blocked from editing `.claude/settings.json` and `.claude/hooks/` by `CLAUDE.md`, by
`protect-paths.sh`, and by a harness-level check on modifying its own permissions or instructions.
The third is not Tom's to configure away from inside a session, and working around it would defeat
its purpose. Claude wrote edits 4 and 5 and then reverted them, because committing a change to its
own instructions is the same check. So all five are Tom's to apply.

**1. `.claude/hooks/guard-bash.sh`** — delete these four lines (the rule and the blank line after
it):

```bash
if grep -Eq '(^|[;&|[:space:](])git[[:space:]]+push([[:space:]]|$)' <<<"$cmd"; then
  block "pushing is Tom's call. Commit locally and say what is ready."
fi

```

**2. `.claude/hooks/guard-bash.sh`** — replace this line:

```bash
if grep -Eq 'ENGINE_ALLOW_LIVE_LLM|ENGINE_LLM_MODE=(live|record)|--llm-mode[= ]+(live|record)' <<<"$cmd"; then
```

with this one, which requires an assignment or a flag rather than a mention:

```bash
if grep -Eq '(^|[;&|(]|[[:space:]])(export[[:space:]]+)?(ENGINE_ALLOW_LIVE_LLM=|ENGINE_LLM_MODE=(live|record))|--llm-mode[= ]+(live|record)' <<<"$cmd"; then
```

**3. `.claude/settings.json`** — move the push entry from `permissions.deny` to
`permissions.allow`. Delete this line from `deny`:

```json
      "Bash(git push *)",
```

and add it to `allow`, after the `git commit` entry:

```json
      "Bash(git commit *)",
      "Bash(git push *)"
```

**4. `CLAUDE.md` line 71** — the Method section still says never push. Replace:

```
  also `@pytest.mark.fast`; spec-auditor checks the diff; commit with IDs first; never push.
```

with:

```
  also `@pytest.mark.fast`; spec-auditor checks the diff; commit with IDs first; push to the
  working branch, never to `main` (ADR-0004).
```

**5. `.claude/skills/implement-req/SKILL.md` step 8** — replace:

```
8. Commit with the IDs first. Do not push.
```

with:

```
8. Commit with the IDs first. Push to the working branch; never to `main` (ADR-0004).
```

Until these are applied the hook keeps refusing pushes, `CLAUDE.md` and the skill still say not to,
and this repository's history will show pushes made with `git -C <path> push`, which the pattern
does not match.
