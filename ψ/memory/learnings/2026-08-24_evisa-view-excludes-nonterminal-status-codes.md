---
pattern: A reporting view's row count matching the sum of only some raw status codes means the view silently excludes the rest — verify combined WHERE filters together, not just individually
date: 2026-08-24
source: rrr: ayami-oracle
concepts: [sql, oracle, mssql, schema-discovery, database-forensics, evisa, reporting-views]
---

# A view's total row count is cheap evidence of which status codes it silently excludes

While building an eVisa (MFA) Oracle BackOffice report query for "paid but not yet approved"
applications, `VW_GET_APPLICATION_CCDC.APPROVE_STATUS` showed only 3 values (`Approved`/
`Cancelled`/`Rejected`, ~3.88M rows, +1 NULL). The raw table `VDC_APP_APPLICATION.APPROVE_STATUS`
had 5 codes: `A`/`C`/`R`/`N`/`I` — and `A+C+R` summed to almost exactly the view's total row count.
`N` (New/unresolved, 47,941 rows) and `I` (Interview, 1,483 rows) never appear in the view at all.

**Rule**: when a pre-built reporting view's total row count equals the sum of only *some* of a raw
table's status/category codes, that's strong, cheap evidence the view intentionally scopes to a
subset (usually terminal states) — no need to read the view's SQL definition to confirm this,
`SUM(view total) ≈ SUM(raw codes subset)` is sufficient. Any question about the excluded
non-terminal states must go to the raw table (with manual joins to master tables for resolved
names — no equivalent all-status view existed here after checking `ALL_VIEWS`), not the
convenient view.

**Second finding, same investigation**: two separate zero-row-query bugs were caught this session,
both from combining two *individually correct, individually verified* WHERE literals that had
never been verified *together*:
1. `VISA_CATEGORY='CY'` + `VISA_TYPE_NAME='Non-Immigrant Visa'` — `CY` pairs exclusively with
   `Courtesy Visa` (confirmed 14,571/14,571 rows), never Non-Immigrant.
2. A specific IMF/WBG purpose ("Media with registration...") + `VISA_TYPE_ID=4` (Non-Immigrant) —
   that purpose is 100% Courtesy Visa (85/85 rows).

**Rule**: before combining two WHERE filters sourced from different turns/contexts, re-verify the
*pair together* with `GROUP BY` — e.g. `SELECT literal_A_col, literal_B_col, COUNT(*) ... GROUP BY
literal_A_col, literal_B_col` — even when each literal was already confirmed correct in isolation.
A value being real doesn't mean it co-occurs with another real value on the same row.

**Third finding**: a report field with no obviously matching column ("Country/Territories of
Passport/TD") turned out to be a second resolved-name column on a master table already in use for
a different field ("Nationality") — `VDC_MST_COUNTRY` has both `COUNTENM` (country/territory name)
and `NATIONENM` (nationality name), joined via two different FK columns (`PASSPORT_HOLDER_CODE` vs
`NATIONALITY_CODE`) on the same application row. Before assuming an unmapped report field needs an
unknown master table, check whether it's a second name-column on a master table already confirmed
for a sibling field.
