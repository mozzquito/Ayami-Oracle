---
pattern: Before drafting a SQL filter against a table whose owning database/schema isn't already confirmed, check ALL_TAB_COLUMNS/INFORMATION_SCHEMA for that table's real location and column names first — an unverified assumption produces a misleading "0 rows" instead of an error.
date: 2026-09-01
source: rrr: ayami-oracle
concepts: [sql, schema-verification, evisa, oracle, mssql, view-filtering, subagent-boundaries]
---

# Verify schema location before drafting a SQL filter, not after a 0-row surprise

## The pattern

During a live evisa/Wayama Oracle-DB debugging session (มอส running real queries, pasting back
real results), three separate 0-row or wrong-answer surprises all traced back to the same root
cause: proposing a filter against a table/column without first confirming where it actually lives
and what it's actually named.

1. **Wrong database assumed**: Proposed a lookup against `VDC_MST_PROCESS_STATUS` assuming MSSQL
   (because the surrounding KB doc discussed it in an MSSQL-adjacent section) — it's actually on
   Oracle (`MFAVDC` schema). Cost a full round-trip before `ALL_TAB_COLUMNS` revealed the real
   location.
2. **Code column vs. name column conflated**: Assumed a status column held human-readable text
   ("Pending for approve") when it actually held a single-letter code (`N`), with the real text
   living in sibling columns (`PROCESS_STATUS_NAME`, `PROCESS_STATUS_FULL_NAME`) that weren't
   queried for.
3. **A view assumed exhaustive was not**: `VW_GET_APPLICATION_CCDC` was documented (from an
   earlier session) as covering "all applications." It silently excluded an entire in-process
   status — 10,932 real rows on the raw table returned 0 through the view. This is the hardest
   variant to catch because it produces a *plausible-looking* empty result, not an error.

## Why this matters

An unverified schema assumption doesn't fail loudly — it produces a clean, syntactically valid
0-row result that reads as "no data exists" rather than "your assumption about the schema is
wrong." That ambiguity is what costs the round-trip: the user has to notice the result is
suspicious, and the agent has to backtrack to question a premise it never flagged as uncertain in
the first place.

## The fix that worked

Once burned twice, switched to proactively supplying `ALL_TAB_COLUMNS` diagnostic queries
*alongside* any newly-proposed filter, rather than waiting for a 0-row result to trigger the
check. This paid off directly later in the same session: a `GROUP BY <status>, <category>` sanity
check against real data preempted a query the user was about to run that would have returned 0
rows for an entirely different reason (a visa-type/category combination that simply doesn't exist
for that specific purpose) — turning a guaranteed dead-end into an immediate, explainable answer.

## Generalizable rule

- Before filtering on a column, confirm (via an actual metadata query, not memory/inference) which
  database/schema the table lives in, and whether the column you're filtering on holds a code or
  a resolved name.
- Before trusting a view/table described elsewhere as "covers everything," run a distribution
  check (`GROUP BY` the relevant dimension) against the raw table it's built from, at least once,
  before relying on the view for a completeness claim.
- When a subagent is told "read-only, don't write files" and it writes a file anyway, treat that
  as a signal to scrutinize the rest of its output harder — in this session the same subagent that
  ignored the write-restriction also independently introduced three unrelated factual errors into
  the file it wasn't supposed to create.

See also: [[project_evisa_wayama]] (companion project memory).
