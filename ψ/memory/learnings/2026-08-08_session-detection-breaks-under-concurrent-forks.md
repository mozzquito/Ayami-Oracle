---
pattern: "ls -t *.jsonl | head -1" session detection silently grabs the wrong transcript when a background/forked job runs concurrently with its parent session
date: 2026-08-08
source: "rrr: ayami-oracle"
concepts: [session-detection, background-jobs, dig-miner, silent-failure]
---

# Session detection breaks under concurrent forks

`/rrr` (and anything else that greps `~/.claude/projects/<encoded-pwd>/*.jsonl` to find "the"
current session) assumes exactly one active session per project directory, found via
"most recently modified file." That assumption fails — silently, with no error — the moment
a background job is forked off a parent session and both are active in the same project
directory at once. `ls -t | head -1` can resolve to either file depending on which one
happened to be touched last, independent of which one you actually want.

## What happened

A background job forked mid-session (`SessionStart:fork`) to handle a specific request. When
that forked session later ran `/rrr`, the dig-miner subagent's `ls -t "$PROJECT_BASE"/*.jsonl
| head -1` picked the *parent* orchestrator's transcript instead of the fork's own — a long
unrelated session with entirely different content and its own separate `/rrr` checkpoints.
The mined "timeline" that came back didn't contain a single message from the actual
conversation being retro'd. There was no error signal; the data just quietly didn't match.

## The fix

Don't rely on recency alone to identify "the" session when a skill might run inside a forked
or background job. Prefer an explicit identifier already available to the running
process (a job/session id passed in context) over inferring it from filesystem mtimes. Where
only mtime-based detection is available, treat its output as a hypothesis to sanity-check
against known conversation content (does the mined text match anything you actually said?)
before trusting it — and fall back to reconstructing from conversation memory, honestly
labeled, rather than silently presenting mismatched data as fact.
