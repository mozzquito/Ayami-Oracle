---
pattern: "before drafting a session retrospective, check whether this exact session ID already has a recent one — a resume can land after an earlier instance of the same session already retro'd, making a full rewrite a duplicate rather than new documentation"
date: 2026-09-13
source: "rrr: ayami-oracle"
concepts: ["rrr", "retrospective", "session-scope", "resume", "compaction", "duplication"]
---

# Check for an existing retro on this session ID before drafting a new one

Companion to `2026-09-13_verify-session-scope-before-retro-not-repo-state.md` (which covers *git
state* misleading a retro) — this one covers a narrower trap: a session resumes after a compaction
boundary, and an *earlier instance of that same session* already ran `/rrr` and wrote a full,
accurate retrospective covering exactly the work sitting in the resumed instance's own conversation
memory. The resumed instance, seeing that work vividly in its own context and no obvious sign it
was already documented, starts drafting a full retro over it — effectively duplicating work that
was already done correctly, and potentially overwriting a more-complete account (the earlier
instance may have had context the resumed one lost to compaction).

**How this surfaced**: a session (`4786dae3`) was asked to close with `/rrr`. `find` for recent
retro files (looking for something unrelated) surfaced `14.46_arra-oracle-tools-and-blast-radius-followup.md`
— already covering, in detail, a tool-install pass and an HTML artifact build that were sitting
fresh in this turn's own conversation memory. Reading its header confirmed it belonged to this same
session ID. It even described a later "closing exchange" (a credential blast-radius discussion) that
wasn't visible in the current context at all — proof a compaction boundary sat between that exchange
and this turn, and that the earlier instance's retro was the only complete record of it.

**How to apply**: before drafting a retrospective, `find $PSI/memory/retrospectives -newer <some
recent reference file>` (or just check the last 2-3 days' worth) and grep each candidate's
`📡 Session:` line for the current `$CLAUDE_SESSION_ID`. If a recent one already exists for this
exact session:
1. Read it — treat it as more authoritative than your own memory for anything before its cutoff,
   since it may cover ground lost to compaction.
2. Scan this session's `.jsonl` for activity strictly *after* that retro's cutoff timestamp.
3. Write a **delta** retro (even if brief — "resumed, nothing new" is a valid full retro) rather
   than a full rewrite. A full rewrite risks losing detail the earlier instance had and you don't.

If the delta turns out to be empty (no real user/assistant activity past the cutoff, just
session-bootstrap noise — hooks, re-read memory files, reminders), that's still worth a short retro
saying exactly that, for the same reason a trivial session still gets a `session-metrics.md` row:
gaps break the pattern-detection value of the record.
