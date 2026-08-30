---
pattern: "/rrr's LATEST_JSONL derivation (ls -t on the project's session directory) is not session-scoped — it ranks ALL concurrently-open Claude Code sessions in that project by mtime, so it silently returns a different session's transcript whenever ≥2 sessions are active, regardless of which process (main agent vs subagent) runs the ls -t call"
date: 2026-08-20
source: "rrr: ayami-oracle"
concepts: [rrr, dig-miner, session-detection, concurrent-sessions, root-cause-vs-workaround]
---

# /rrr dig-miner picks the wrong concurrent session — the real root cause

## What happened (this occurrence)

During `/rrr` on session `32c1e2dc`, step 1's own `ls -t "$PROJECT_BASE"/*.jsonl | head -1` returned `d4af5be6-...jsonl` — a completely unrelated session about evisa/MSSQL database forensics, not this conversation (Blink Shell, Agoda meeting notes, Orca install). The timestamp-miner subagent dutifully extracted real timestamps from that wrong file and reported them as if correct.

Recovery required grepping every `.jsonl` in the project directory for phrases known to be unique to this conversation (`"Agoda"`, `"Blink Shell"`) to find the actual correct file — `32c1e2dc-c460-4294-9e0c-6d0e437e8d17.jsonl`, which not coincidentally matched this session's `CLAUDE_JOB_DIR` (`/Users/phongcheatphus/.claude/jobs/32c1e2dc/tmp`) mentioned in the system prompt.

## Why the previous fix didn't work

An earlier fix (documented in `ψ/memory/learnings/2026-08-17_dig-miner-picks-wrong-concurrent-session.md`) moved the `ls -t` derivation from the timestamp-miner subagent's own shell into the main agent's shell, on the theory that the subagent's *independent* re-derivation was racing against file-touch timing. That fix was necessary but not sufficient: `ls -t` itself has no concept of "this session" — it just lists every `.jsonl` in the project directory sorted by mtime. Whichever Claude Code session (this one, a background job, or an entirely unrelated concurrent session in the same project) most recently wrote to its own transcript file wins, regardless of which process issues the `ls -t` call or how carefully the literal path is threaded through to a subagent afterward.

This has now recurred at least 8 times since 2026-08-08 despite the "fix," across multiple different manifestations (wrong session entirely, a meta-summary claiming timestamps were "returned above" with none included, "4th+ occurrence" flagged and left unaddressed).

## The actual root cause

`ls -t` ranks by mtime across *all* files in the directory, not per-session. Any solution that still depends on "most recently touched" is structurally exposed the moment ≥2 Claude Code sessions are open against the same project directory — which is routine here (background jobs, forked agents, and now likely more common with multi-agent tools like Orca in the mix).

## What would actually fix it

- **Best**: find whatever session-scoped identifier the harness already exposes early in a session (this session's own system prompt names `CLAUDE_JOB_DIR=/Users/phongcheatphus/.claude/jobs/32c1e2dc/tmp` — the leading hex segment `32c1e2dc` matched the correct `.jsonl` filename directly). If an equivalent ID is available for regular interactive (non-background-job) sessions too, use that instead of `ls -t` entirely.
- **Fallback**: content-based disambiguation — grep all `.jsonl` files in the project directory for a phrase known to be unique to the current conversation (e.g. the exact text of the user's most recent message, or a distinctive earlier one) and pick the file that matches, rather than trusting mtime ordering at all.
- **Do not** keep treating "which process calls `ls -t`" as the variable to fix — that axis has been tried and re-tried without closing the bug.

## How to apply

Any skill or script that needs "the current session's own transcript file" in a project directory that may have concurrent sessions must not rely on `ls -t` / most-recently-modified as the sole signal. Prefer a session-ID-based lookup if the harness exposes one; otherwise fall back to content matching against something unique to the current conversation, and treat any `ls -t`-based result as unverified until cross-checked.
