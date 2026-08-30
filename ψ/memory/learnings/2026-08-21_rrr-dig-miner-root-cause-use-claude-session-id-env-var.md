---
pattern: "/rrr's dig-miner picks the wrong concurrent session's .jsonl" has recurred ≥10 times across sessions (2026-08-17 through 2026-08-21) despite prior fixes — the real fix is to stop deriving session id via `ls -t` entirely and read it straight from `$CLAUDE_SESSION_ID` (or `$CLAUDE_CODE_SESSION_ID`), which Claude Code already sets in the environment
date: 2026-08-21
source: rrr: ayami-oracle
concepts: [rrr, dig-miner, session-id, root-cause, environment-variables, self-evaluation-loop]
---

# The dig-miner "wrong session" bug's real fix: $CLAUDE_SESSION_ID, not smarter ls -t

## Timeline of a bug that kept "getting fixed" without going away

- 2026-08-17: first documented occurrence + fix attempt (`2026-08-17_dig-miner-picks-wrong-concurrent-session.md`)
- 2026-08-19/20: recurred at least 4 more times, each logged in `session-metrics.md`'s friction
  column, escalating language each time ("3rd occurrence", "≥8th all-time", "≥9th all-time,
  escalating past 'write a lesson' into 'the lesson isn't preventing recurrence'")
- 2026-08-20: `/rrr` skill itself patched — main agent computes `LATEST_JSONL` once via `ls -t`
  and passes the **literal path** into the dig-miner subagent's prompt, so the subagent can't
  independently re-run `ls -t` and diverge. Documented as the fix.
- 2026-08-21: recurred again — but this time in a **new failure mode** the 2026-08-20 fix never
  touched: the **main agent's own** `ls -t` call (step 1, before any subagent exists) picked a
  totally unrelated concurrent session (an evisa/MFAVDC SQL-query session). The subagent then
  correctly extracted timestamps — for the wrong file, since it was only ever as good as the
  literal path it was handed.

## Root cause

`ls -t *.jsonl | head -1` sorts by mtime, and with **multiple Claude Code sessions genuinely
active in the same project directory at the same time**, several `.jsonl` files can be touched
within the same second-resolution window. At the point this was diagnosed, four separate
session files (`e0a7ecfc`, `2ef11adc`, `f7d77c60`, `f025f327`) all had mtimes within the same
~3-minute window. `ls -t` has no way to disambiguate "my own session" from "a sibling session
that happens to be more recently touched" — it was never the right tool for this job, no matter
how carefully the derivation logic around it gets patched.

## The actual fix

Claude Code sets the current session's id directly in the environment — no derivation needed:

```bash
echo "$CLAUDE_SESSION_ID"          # e.g. e0a7ecfc-6541-4c72-a451-2bc197ef6914
echo "$CLAUDE_CODE_SESSION_ID"     # same value, alternate var name
```

Verified: this matches the `sessionId` field embedded in every JSON record of the session's own
`.jsonl` file — confirmed by grepping the current session's own jsonl and finding this exact
value. This is deterministic, not a heuristic, and requires no fallback logic.

**Replacement for `/rrr`'s step 1**:

```bash
SESSION_ID="${CLAUDE_SESSION_ID:-$CLAUDE_CODE_SESSION_ID}"
LATEST_JSONL="$PROJECT_BASE/${SESSION_ID}.jsonl"
```

instead of:

```bash
LATEST_JSONL=$(ls -t "$PROJECT_BASE"/*.jsonl 2>/dev/null | head -1)
SESSION_ID=$(basename "$LATEST_JSONL" .jsonl)
```

This closes the bug at the only point it can actually be closed — the main agent's own step 1 —
which every previous fix attempt skipped past because they treated the subagent's derivation as
the bug's location, when the subagent was only ever inheriting whatever the main agent handed it.

## General lesson

When a bug **keeps recurring despite fixes that seemed to address it**, treat that as a signal
the fix targeted a symptom's location, not the actual source — check the *entire* call chain
(main agent → subagent → tool), not just the spot most recently observed to fail. And before
writing derivation/heuristic logic to reconstruct a value the runtime might already expose
directly (current session id, current user, current working context), check `env` first — a
guess-based heuristic (`ls -t`, parsing `pwd`, scraping a log) is a code smell when a
authoritative source might already be one `echo $VAR` away.

## Action needed

The `/rrr` skill definition itself (both `.claude/skills/rrr/` if present locally, and the
global `~/.claude/skills/rrr/SKILL.md`) still uses the `ls -t` derivation as of this writing —
this lesson documents the fix but does not apply it. Editing the global skill affects every
Oracle repo using `/rrr`, so that edit should be confirmed with the human first rather than
applied unilaterally from within a single project's session.
