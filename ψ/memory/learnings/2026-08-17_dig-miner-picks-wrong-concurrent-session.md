---
pattern: "/rrr's dig-miner subagent picks the most-recently-modified .jsonl via `ls -t`, which can be a different concurrent session, not the current one — always sanity-check its snippets before merging into a retro's Timeline"
date: 2026-08-17
source: "rrr: ayami-oracle (drivedb)"
concepts: [rrr, dig-miner, retrospectives, concurrent-sessions]
---

# dig-miner can grab the wrong session's timestamps under concurrency

The `/rrr` skill's dig-miner background subagent detects the current session's
`.jsonl` file with:

```bash
LATEST_JSONL=$(ls -t "$PROJECT_BASE"/*.jsonl 2>/dev/null | head -1)
```

This picks whichever file in the project's `~/.claude/projects/<encoded-pwd>/`
directory was modified most recently — which is usually the current session,
but not always. When another Claude Code session is concurrently active in
the same project directory (a real, common scenario — multiple terminal tabs,
a background agent, another Oracle instance), that other session's activity
can touch its own `.jsonl` file more recently than the current session has
been idle, and `ls -t` picks the wrong one.

**This has now happened twice**: 2026-08-15 (an earlier `/rrr` run, noted in
that day's session-metrics friction column) and again on 2026-08-17, where
dig-miner returned timestamped snippets about an unrelated trading-strategy
conversation instead of the actual drivedb session in progress. Both times it
was caught by eye — the returned content obviously didn't match the current
conversation's subject matter — and fixed by manually re-deriving the correct
session ID (already established earlier in the same conversation, from an
earlier Step 1 "Detect session ID" block) and querying that file directly.

**Why this matters**: a wrong-session Timeline isn't just cosmetically wrong —
it actively misleads anyone reading the retro later about what happened when,
and if not caught, would silently corrupt the retrospective record this whole
system exists to keep accurate.

**Rule going forward**: after dig-miner returns, before merging its output
into the Timeline, spot-check that at least one or two of the returned
snippets plausibly match something discussed in the current conversation. If
they don't, don't merge — re-derive `SESSION_ID`/`LATEST_JSONL` directly
(usually already computed once earlier in the same `/rrr` invocation, in the
"Detect session ID" step) and re-query timestamps from the correct file
yourself rather than trusting the subagent's file-selection logic blindly.

A more durable fix would be for dig-miner to receive the session ID as an
explicit parameter (computed once, by the main agent, before spawning the
subagent) rather than re-deriving it independently via `ls -t` inside the
subagent's own shell — this removes the race entirely instead of just
detecting it after the fact. Worth raising as a root-cause fix if this
recurs a third time, per the parent CLAUDE.md "same friction 3 sessions →
fix root cause" rule.
