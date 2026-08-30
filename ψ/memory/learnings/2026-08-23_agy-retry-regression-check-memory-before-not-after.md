---
pattern: "Check ψ/memory/learnings/ for a sibling agent's (zcode/agy) name BEFORE the first invocation of a session, not after it fails — a documented environment-level failure mode should change behavior on the very next attempt."
date: 2026-08-23
source: "rrr: ayami-oracle"
concepts: ["agy", "zcode", "permission-hook", "memory-recall-timing", "sdlc-workflow"]
---

# Learned: checking memory after a failure is too late — check before acting

## What happened

This session retried an identically-blocked `/agy` call 2 extra times across two separate
user requests (an iPad-battery research task, and a `/zcode /agy` NexusRAG-integration
consult), even though `ψ/memory/learnings/2026-08-22_agy-blocked-by-activity-log-hook-dont-retry-identically.md`
already existed from the day before, documenting this exact hook-permission block and
explicitly instructing: after one identical failure, don't retry the same shape of command.

The memory file was correctly written, correctly named, and directly on-topic. It simply
wasn't consulted before acting — only surfaced during this session's own `/rrr` retro, by
which point the mistake had already happened twice.

## The mistake

Treating "check memory" as something that happens reactively, after a tool fails and *reminds*
you to think of it, rather than proactively, as a pre-flight step before invoking a sibling
agent that has a known history of environment-level (not task-level) failures. A prior
session (2026-08-22, `dbc89990` row in session-metrics.md) shows the *correct* behavior:
"agy's Session Activity hook block — which broke the exact same consult in a prior session —
was fixed on the first retry this time because that prior session's lesson file was recalled
and actually applied." This session regressed from that.

## What to do instead

- Before the *first* invocation of `/agy` or `/zcode` in a session, grep
  `ψ/memory/learnings/` for the agent's name (`grep -l agy ψ/memory/learnings/*.md` or
  equivalent). This is a 2-second check that should be as automatic as checking `.origins`
  before a `/learn` clone.
- Don't wait for a failure to prompt the memory check — by then the retry has often already
  happened once, and the whole point of the earlier lesson was to prevent exactly that retry.
- If a fix genuinely isn't available in memory (root cause still open), the correct move per
  the 2026-08-22 lesson stands: skip the agent after one failed attempt per session, disclose
  the skip, and fall back to the sibling agent or self-review — not repeat the same call
  hoping the environment changed.

## Related

[[agy-blocked-by-activity-log-hook-dont-retry-identically]] — the original 2026-08-22
documentation of this exact hook block and the "don't retry identically" rule this session
violated. This lesson is specifically about *when* to consult memory (before, not after),
which the original lesson didn't address because it was written in the moment of discovery,
not in a moment of regression.
