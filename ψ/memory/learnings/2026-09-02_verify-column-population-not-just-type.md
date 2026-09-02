---
pattern: When checking whether a column is viable for a filter, verify both its data type AND its population rate (COUNT(*) vs COUNT(col)) in the same diagnostic pass — a type-only check can pass cleanly while the column is entirely NULL, producing a misleading 0-row filter result later.
date: 2026-09-02
source: rrr: ayami-oracle
concepts: [sql, schema-verification, evisa, oracle, null-columns, diagnostic-queries]
---

# Verify column population, not just column type

## The pattern

During a live evisa/Wayama Oracle-DB debugging session (DTV payment-count query), a column
(`PAYMENT_DATE` on `MFAVDC.VDC_APP_APPLICATION`) was proactively type-checked before being used in
a filter — confirmed as a proper `TIMESTAMP(6) WITH TIME ZONE`, not a risky `VARCHAR2` — and the
filter was built accordingly. It still returned 0 rows. A follow-up diagnostic
(`GROUP BY IS_PAYMENT` with `MIN`/`MAX`/non-null count) revealed the real cause in one query:
`PAYMENT_DATE` was `NULL` for all 110,251 relevant rows. The column was structurally sound and
completely unused in practice.

## Why this matters

"Verify before filtering" (the lesson from the immediately preceding session, where a table's
database location and a status column's code-vs-name split both caused 0-row surprises) is easy to
apply narrowly — check the one thing that caused the *previous* surprise, and stop there. Here,
type-checking was applied (the previous session's literal lesson) but population-checking was not
(a different, equally necessary check). Both failure modes produce the identical downstream
symptom: a clean, syntactically valid 0-row result that reads as "no matching data" rather than
"this column isn't usable the way you're using it."

## The fix that worked once it surfaced

A single combined diagnostic — `COUNT(*)` vs `COUNT(specific_column)`, or a `GROUP BY` with
`MIN`/`MAX`/non-null-count as used here — answers both the type and the population question in one
round-trip, before a filter is proposed at all, rather than after a misleading empty result forces
a second pass.

## Generalizable rule

- Before proposing a filter on any column whose reliability isn't already established, check not
  just "does this column have the right type" but "is this column actually populated for the rows
  I care about" — in the same diagnostic query, since both checks are cheap and a type-only check
  provides false confidence.
- A 0-row result from a syntactically correct, type-correct filter is not evidence of "no matching
  data" — it's evidence that needs its own diagnosis (population, hidden view filters, wrong
  ID/enum mapping — three distinct root causes seen across two consecutive sessions on this same
  project, all producing the identical 0-row symptom).
- When a "cleaner" data source is discovered mid-investigation (here: a proper transaction table,
  `VDC_APP_APPLICATION_PAYMENT`, surfaced from an unrelated earlier `%STATUS%` column scan), present
  it alongside the already-working solution with an honest tradeoff (performance vs. correctness
  edge cases) rather than silently picking one — let the person with domain context make the call.

See also: [[2026-09-01_verify-schema-location-before-sql-filter]] (companion lesson from the
immediately preceding session on this same project — same root theme, different specific check).
