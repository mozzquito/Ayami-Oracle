---
pattern: Before hand-joining master tables for a report, search for a pre-built reporting VIEW with the exact output column names — enterprise systems often already resolve every FK to its display name in a `VW_*` view
date: 2026-08-18
source: rrr: ayami-oracle
concepts: [sql, oracle, mssql, schema-discovery, database-forensics, evisa]
---

# Search for a pre-built reporting view before hand-joining master tables

While mapping the eVisa (MFA) BackOffice Oracle schema (`MFAVDC`) to reproduce a report,
`VW_GET_APPLICATION_CCDC` turned out to already resolve nearly every field needed (Nationality,
Visa Type, Passport Type, Consular Office, PIBICS send-status) — replacing a 6-table manual join
entirely. It was found only after first trying to join `VDC_APP_APPLICATION` to individual master
tables (`VDC_MST_PASSPORT_TYPE`, `VDC_MST_PURPOSE_OF_VISIT`, etc.) by hand.

**Rule**: when a target report/UI shows resolved display names (not raw codes), search
`ALL_TAB_COLUMNS`/`INFORMATION_SCHEMA.COLUMNS` for the *exact output column names* (e.g.
`NATIONALITY_NAME`, `VISA_TYPE_NAME`) across all tables/views in the schema — not just the ID
columns — before assuming a hand-built join is required. Enterprise systems frequently ship
`VW_*` or similarly-named views built exactly for this purpose.

**Second finding, same investigation**: the same underlying status concept
(Approved/Cancelled/Rejected) had two different literal representations in the same database —
the raw table (`VDC_APP_APPLICATION.APPROVE_STATUS`) used single-char codes (`'A'`/`'C'`), while
the reporting view (`VW_GET_APPLICATION_CCDC.APPROVE_STATUS`) used full English words
(`'Approved'`/`'Cancelled'`/`'Rejected'`). A value confirmed correct against one table is not
guaranteed to be the literal value in a related view — always run `GROUP BY <status_col>` to see
actual distinct values before hardcoding a filter literal, especially after switching from a raw
table to a view (or vice versa).

**Third finding**: view names that read as a scoped verb-phrase (here, `VW_SENT_CCDC` — "sent to
PIBICS") are a signal to check before treating them as ground truth for a status query. Cancelled
applications structurally never reach a "sent" step, so filtering that view for
`APPROVE_STATUS='Cancelled'` returned 0 rows even though the broader `VW_GET_APPLICATION_CCDC`
(same schema, no "sent" scoping) had 254K matching rows system-wide. Read the view's name as a
business-logic hint before using it, not just as a table to query.

**Bonus, unrelated to schema**: an unknown data export's timestamp string format is a fast,
reliable way to fingerprint which RDBMS it came from, before touching any schema knowledge at
all. Oracle `TIMESTAMP WITH TIME ZONE` renders as `DD-MON-YY HH.MI.SS.FFFFFFFFF AM/PM
REGION/CITY` (dot-separated time, named IANA timezone region). MSSQL `datetimeoffset` renders as
`YYYY-MM-DD HH:MM:SS.fffffff ±HH:MM` (colon-separated, numeric UTC offset only — SQL Server has
no concept of named timezone regions). This correctly identified a CSV export as Oracle-sourced
before any Oracle access was available, saving a wrong-schema-doc detour.
