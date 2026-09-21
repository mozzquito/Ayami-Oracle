---
pattern: A reconstructed production query built from pure guesswork about business semantics reads exactly as credible as a verified one — hedge visibly or refuse to guess at that level of detail
date: 2026-09-13
source: "rrr: ayami-oracle (evisa/Wayama session)"
concepts: [sql, reverse-engineering, overconfidence, hedging, evisa]
---

# Don't ship a guessed production query as a clean "ready to test" draft

## What happened

In an earlier eVisa/Wayama session, มอส asked how a "Daily Ranking Check Act" staff-performance
report might be reproduced as a live query against Oracle. With zero access to the real report
source, I reconstructed a plausible-looking query and handed it over as a formatted, ready-to-run
SQL block — clearly labeled as a guess in prose, but still fully polished in presentation.

Days later มอส sent the *actual* production SQL*Plus script. Three of my core assumptions were
wrong:
- I guessed `CHECK_AVG_DIFF` measured application-submission-to-check time; it actually measured
  paid→document-checked time, computed via two `PROCESS_STATUS_ID` lookups (5 and 8) into a
  process-log table.
- I guessed `CHECKBY` was a column directly on the application table; it actually came from
  `CREATED_BY` on a joined log-table row.
- I guessed `CLEVEL` was a stored country-risk-level value; it was actually a computed flag
  (`CASE WHEN consular_name LIKE '%Embassy%' THEN 3 ELSE 1 END`) with no risk semantics at all.

None of these were reachable from the information available — no naming convention, prior schema
doc, or business description hinted at any of them. The guess wasn't unreasonable to attempt; the
problem was the *presentation*. A clean, syntactically-complete, ready-to-copy SQL block signals
"this is a solid draft to test," when the actual epistemic status was "this is speculative
fiction about semantics I have no way to verify."

## The pattern to avoid

Formatting quality and correctness confidence are independent axes. A polished code block reads
as trustworthy regardless of how much of its content was invented — the reader (especially a
non-programmer stakeholder) has no formatting cue that distinguishes a verified query from a
guessed one. Hedging in a sentence above or below the block is easy to skim past; the block
itself is what gets copy-pasted and acted on.

## What to do instead

- When reconstructing production logic with **zero access to the real source**, say so as
  plainly as the reasoning constraint deserves — not just "this is a guess" but specifically
  which parts are unverifiable business semantics (date-diff basis, which column is derived vs.
  stored, what a computed flag actually encodes) versus which parts are structurally certain
  (table/column existence already confirmed elsewhere).
- Prefer proposing a **diagnostic query to run first** (e.g., "let's check what columns exist
  and what a few sample rows look like") over a **complete reconstruction** when the target is
  specific business logic rather than general schema shape. Schema shape (table/column names)
  is far more guessable correctly than time-diff semantics or derived-flag logic.
- If a real source might exist and could plausibly be obtained, ask for it before reconstructing
  — reconstructing was faster in the moment but cost more total time once the correction round
  happened.

## Why this matters beyond this one case

This is a recurring failure mode for any agent doing infra/DB reverse-engineering from
incomplete information: the artifact's polish outruns its actual confidence level. The fix isn't
"guess less" (guessing is often the only path forward with no other source) — it's "make the
confidence level of the *presentation* match the confidence level of the *content*."
