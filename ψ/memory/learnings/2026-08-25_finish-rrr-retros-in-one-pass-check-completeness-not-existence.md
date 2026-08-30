---
pattern: when checking whether a prior /rrr retro already covers a period, verify the file's completeness (all required sections present), not just that a file exists
date: 2026-08-25
source: rrr: ayami-oracle
concepts: [rrr, retrospective, process-integrity]
---

# Finish /rrr retros in one pass — check completeness, not existence

A `/rrr` retro was started (Session Summary, Timeline with placeholder
timestamps, Files Modified, AI Diary all written; a background dig-miner
subagent spawned and its real-timestamp result received) and then the
conversation moved directly into a new calendar day's work before the
remaining required sections — merging the real timestamps in, Honest
Feedback, Lessons Learned, Next Steps, the recurring-pattern check, and the
Self-Audit block — were ever written. Nothing was lost (the dig-miner's
output was still sitting in conversation context and got applied ~16 hours
later at the next `/rrr` invocation), but the retro sat incomplete and
would have looked "done" to a quick glance (the file existed, had a
title, had content) without actually satisfying the skill's own required
sections.

**Rule**: the pattern of "start writing the retro immediately, merge real
timestamps when the dig-miner returns" is correct for speed, but it creates
an implicit obligation to actually finish before ending the turn. When a
later `/rrr` call checks whether a prior retro in the same session-thread
already covers a period (to avoid re-covering ground), check the file's
completeness — does it have all required sections, or does it end abruptly
after the AI Diary — not just whether a file with the right date exists.
An incomplete retro should be finished as the first step of the next
`/rrr` call, before starting a new one for the newer segment.
