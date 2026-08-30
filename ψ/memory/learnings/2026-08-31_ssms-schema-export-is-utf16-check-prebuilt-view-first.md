---
pattern: SSMS-generated schema scripts are UTF-16LE (grep needs iconv first); before drafting a new SQL report query, check your own prior learnings for a pre-built view covering the same domain
date: 2026-08-31
source: rrr: ayami-oracle
concepts: [sql, mssql, oracle, encoding, schema-discovery, evisa, self-knowledge-reuse]
---

# Convert SSMS schema-export scripts before grepping, and check your own past learnings before re-deriving a query

**First finding**: A SQL Server "Generate Scripts" schema dump (`save_schema.sql`, produced by SSMS)
is UTF-16LE encoded. Plain `grep`/`cat` on it returns **no matches at all** for strings that are
definitely present — including a table name the user just typed verbatim — because every character
is separated by a null byte. This looks exactly like "the table doesn't exist," which is the wrong
conclusion. Fix: `iconv -f UTF-16LE -t UTF-8 file.sql | grep ...` (or convert once to a scratch copy
before repeated searching). Treat "grep found nothing in a schema/DDL export" as an encoding-check
prompt, not proof of absence, before reporting a table/column missing.

**Second finding**: Before drafting a SQL query for a report/data-pull task, search your own prior
learnings for the same project/domain for a note about a pre-built view or existing query — not just
at the start of a *new* investigation, but every time, even mid-session when the specific ask shifts
(e.g. from "check a stock table" to "pull an applicant list for an event"). In this session, a lesson
from 6 days earlier in the same project (`2026-08-18_evisa-oracle-backoffice-schema-mapping.md`) had
already documented "search for a pre-built reporting view before hand-joining master tables" for this
exact system — yet the agent re-derived a query from raw base tables on the *other* database (MSSQL
pre-application side) before the user surfaced their own pre-built-view query and the agent switched
tracks. A lesson written but not re-consulted at the moment it applies provides no value over never
having written it.

**Practical hook**: when a task is "pull/report data from system X" and a prior learning file exists
tagged with that system's name, grep `ψ/memory/learnings/` for the system name before writing the
first line of SQL — not only when starting the task, but again if the shape of the request changes
mid-session.
