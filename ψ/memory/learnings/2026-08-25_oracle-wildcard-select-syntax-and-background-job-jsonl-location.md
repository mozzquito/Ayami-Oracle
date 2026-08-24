---
pattern: Oracle rejects a bare `*` mixed with named columns in SELECT (needs table-qualified `t.*`) — and /rrr's dig-miner must not assume the standard ~/.claude/projects/.../<session-id>.jsonl path for background-job sessions
date: 2026-08-25
source: rrr: ayami-oracle
concepts: [sql, oracle, syntax, evisa, rrr, background-jobs, session-discovery]
---

# Oracle wildcard-with-columns syntax, and where background-job session transcripts actually live

**Finding 1 — Oracle SELECT-list syntax.** Unlike MySQL/Postgres, Oracle does not allow a bare
unqualified `*` to appear in a SELECT list alongside named columns — `SELECT col1, *` throws
`ORA-00936: missing expression`. The wildcard must be table-qualified when combined with named
columns: `SELECT col1, t.*`. This bit me directly this session: while fixing a user's missing-comma
bug (`SELECT col *` → `ORA-00923`), I "corrected" it to `SELECT a.TRAVEL_DOC_NO, *` without
checking this rule, handed back a still-broken query, and the user hit a *new* Oracle error from my
fix. **Rule**: when reconstructing any SELECT list that mixes `*` with named columns for Oracle,
always qualify the wildcard (`d.*`, not bare `*`) — don't just patch the specific error message
that was reported and assume the rest of the statement is valid.

**Finding 2 — a correlated `MAX(id)`-per-parent subquery is a scoping choice, not a neutral
default.** A `WHERE id = (SELECT MAX(id) ... WHERE parent_id = outer.parent_id)` pattern that's
correct for "give me the current/latest state of X" is actively wrong for "does this specific named
record exist anywhere in X's history" — it silently excludes any target row that isn't the newest
one for its parent. Confirmed concretely: a target document (`Document-10.pdf`) existed but was
excluded because two other documents were uploaded to the same application later the same day.
When reusing a working query pattern from earlier in a session for a differently-shaped question,
re-derive whether the same scoping still applies rather than assuming it generalizes.

**Finding 3 — `/rrr`'s dig-miner subagent must not assume the standard session-file path for a
background job.** A normal interactive Claude Code session's transcript lives at
`~/.claude/projects/<encoded-cwd>/<CLAUDE_SESSION_ID>.jsonl`, and `$CLAUDE_SESSION_ID` reliably
matches that filename (per the 2026-08-21/22 dig-miner fixes). But when the session is running as a
**background job** (`CLAUDE_JOB_DIR` env var set, e.g. `~/.claude/jobs/<job-id>/`), that standard
path does not exist at all — the job's transcript instead lives at
`~/.claude/jobs/<job-id>/timeline.jsonl`, in a **different schema**
(`{"at": ISO-UTC-timestamp, "state": "working"|"done", "detail": ..., "text": ...}` — no
`type:"user"`/`message.content` structure, and "at" reflects assistant status-update moments, not
raw user-message send times). Confirmed the timestamps in that file line up correctly with the real
per-turn `UserPromptSubmit hook` timestamps already visible in the conversation transcript.
**Rule**: before spawning the dig-miner subagent, check whether `CLAUDE_JOB_DIR` is set; if so,
either point the subagent at `$CLAUDE_JOB_DIR/timeline.jsonl` with adjusted parsing logic, or skip
the subagent entirely and use the `UserPromptSubmit` hook timestamps already present at the top of
each turn in context — they're equally real and don't require a subagent round-trip that's likely
to fail silently against the wrong path.
