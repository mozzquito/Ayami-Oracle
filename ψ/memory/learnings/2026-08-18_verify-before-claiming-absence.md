---
pattern: A negative claim ("X was not found") is only as strong as the search that produced it — before publishing an absence as fact, run one targeted search for the exact term, don't extrapolate from unrelated search patterns
date: 2026-08-18
source: rrr: ayami-oracle
concepts: [verify-before-asserting, sql, schema-discovery, evisa]
---

# A "not found" claim is only as strong as the search behind it

While building a published ERD diagram of the eVisa Oracle schema, I wrote "no master table
found" for the `NO_OF_ENTRIES_TYPE`/`NO_OF_ENTRIES_REQUESTED` fields. That was true of every
search actually run — but those searches used patterns like `%VISA_TYPE%`, `%PURPOSE%`,
`%PASSPORT_TYPE%`, `%VISA_SUB%`, `%NATION%` — none of which would ever match a table named
`VDC_MST_NO_OF_ENTRIES_MAPPING`. I had never run a search for `%ENTRIES%` specifically. The table
existed the whole time, and it turned out to have a genuinely interesting composite-key structure
(two columns together resolve to one display row) — a more useful finding than "no relationship,"
found only because the user asked to close the gap, not because the shortfall was caught
independently.

This is the same shape of mistake as `[[feedback_verify_before_asserting]]` in existing memory,
applied to a new context: publishing a negative/absence claim in a diagram or document based on
searches that were never actually targeted at the specific term in question.

**Rule**: before stating "X was not found" or "no Y exists" in anything the user will read as a
finished claim (a diagram, a summary doc, a report), run one search specifically for the exact
term or field name — don't infer absence from searches that happened to be run for other reasons,
even if they're broad. If a dedicated search genuinely can't be run yet (no access, time
pressure), phrase the claim as "no confirmed match yet" rather than "not found" — the weaker
phrasing is honest about what was actually checked.

**How to apply**: when drafting a diagram, summary table, or any artifact with confirmed/
unconfirmed status pills or similar signals, audit each "unconfirmed" or "not found" claim against
the actual search history before publishing — if there's no dedicated search for that specific
term, either run it first or downgrade the claim's phrasing to reflect what was really checked.
