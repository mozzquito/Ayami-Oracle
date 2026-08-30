---
pattern: When porting a SQL condition between two databases that model "the same" business process (e.g. a front-end and a backoffice DB), verify the target schema structurally before assuming an equivalent concept/column exists — some process-state concepts may only exist on one side.
date: 2026-08-27
source: rrr: ayami-oracle
concepts: [sql, cross-database, schema-verification, evisa, oracle, mssql]
---

# Verify cross-DB schema concepts before mapping conditions across databases

Two databases that share master-data naming conventions (e.g. `VDC_MST_*` tables identical on
both Oracle and MSSQL in the eVisa system) do **not** necessarily share process-state concepts.
While porting a DTV visa report query from Oracle `MFAVDC.VDC_APP_APPLICATION`
(`APPROVE_STATUS='N'`) to MSSQL `VDC_PRE_APPLICATION`, the natural instinct was to look for an
equivalent `APPROVE_STATUS`-like column and map it. A column-existence check
(`INFORMATION_SCHEMA.COLUMNS`) showed no such column exists at all — not renamed, genuinely
absent — because the "approve" decision only happens in the Oracle BackOffice; MSSQL is purely a
front-end pre-application system. The two closest-sounding candidates (`PRE_APPLY_STATUS`,
`TRANSFER_STATUS`) both turned out to encode different, unrelated concepts (front-end submission
state and BackOffice-transfer state respectively), confirmed only by grepping a previously
written project schema-summary doc, not by guessing from column names.

**Why this matters**: guessing a plausible-sounding column as an "equivalent" across DB boundaries
risks silently shipping a wrong report (especially dangerous on real government PII data) — a
condition that looks harmless (`PRE_APPLY_STATUS = 'S'`?) could filter on a completely unrelated
axis and no error would ever surface.

**How to apply**: before porting any WHERE-clause condition from one database to a differently
modeled "equivalent" database, run a schema lookup (`INFORMATION_SCHEMA.COLUMNS` /
`ALL_TAB_COLUMNS`) for the target table first, searching for both the exact name and a
`LIKE '%keyword%'` pattern. If nothing matches structurally, check for existing schema-summary
documentation before asking the human to confirm meaning from distinct-value samples — do not
invent a mapping from column-name plausibility alone. This generalizes beyond eVisa: any
multi-database system with a front-end/backoffice split (or similarly split write paths) is a
candidate for this exact trap.

See also [[project_evisa_wayama]] for the concrete finding (MSSQL has no approve-status concept at
all) and the related lesson on cross-DB master-data ID sync not being a safe default assumption.
