---
name: it-report
description: Generate an IT Service Monthly Report (Wayama-style, e.g. for Kittisampan or similar clients) from freeform notes or structured data. Use when the user says "it-report", "ทำรายงาน IT", "สรุปรายงาน IT เดือนนี้", pastes monthly maintenance notes and wants a report, or wants to fill/update the report data for a specific month. Do NOT trigger for the eVisa/Wayama infra project itself (that's unrelated) or generic non-IT report requests.
---

# /it-report — IT Service Monthly Report generator

Tooling lives in `ψ/lab/it-monthly-report/`:
- `schema.yaml` — the data contract (every field the report needs, with comments)
- `template.md.j2` — Jinja2 markdown template (traffic-light health dashboard, SLA, MoM trend, license expiry tracking, critical alerts, scope-of-work check, prioritized recommendations, sign-off box)
- `generate.py` — renders a data file into `.md` (always) and `.docx` (with `--docx`)
- `.venv/` — isolated Python env with pyyaml/jinja2/python-docx already installed
- `data/2026-07-example.yaml` — a filled reference example (recreated from the original Kittisampan July 2026 report, gaps filled in)

This tool exists because the original hand-filled Word template had structural
problems (contradicting ticket totals, blank template rows never cleaned up,
FortiGate section with zero data, no SLA/expiry/trend info, no risk flagging)
identified by /agy and /zcode review — see git history / session context for
the full critique if useful.

## When invoked with freeform notes ($ARGUMENTS)

The user will describe what happened this month in plain language (Thai or
English) — NOT already structured. Your job:

1. Read `ψ/lab/it-monthly-report/schema.yaml` for the full field list and comments.
2. Map the user's notes onto that schema. Fields not mentioned in the notes:
   leave as `null` (or empty list) — do **not** invent data. This is a hard rule:
   a monthly IT report is a compliance/audit artifact, so fabricated uptime %,
   license dates, or ticket counts would be actively harmful, not just wrong.
3. Actively flag things the notes imply but don't state explicitly as
   `critical_alerts` when they're real risks (e.g. "opened SMB 1.0" → flag it,
   "license expires in 5 days" → flag it) — this is the whole point of the
   redesign, don't let it regress into a passive log again.
4. Write the filled file to `ψ/lab/it-monthly-report/data/<YYYY-MM>.yaml`
   (ask the user for year/month if not stated).
5. Run:
   ```bash
   cd ψ/lab/it-monthly-report
   ./.venv/bin/python generate.py data/<YYYY-MM>.yaml --docx
   ```
6. Read back the generated `.md` and show the user anything rendered as
   `⚠️ MISSING` — those are fields your notes didn't cover; ask the user to
   fill the gaps rather than silently leaving them.
7. Compute trend_mom by reading the *previous* month's data file in the same
   `data/` directory if one exists, so uptime/ticket-count deltas populate
   automatically instead of staying null.

## When invoked with a path to structured data (YAML/JSON) or "just render X"

Skip the extraction step — copy/adapt the data into `data/<YYYY-MM>.yaml`
matching `schema.yaml`'s shape, then run `generate.py` as above.

## When invoked to review/compare against a previous report

Diff the new data file against the prior month's and call out in the chat
reply what changed (new alerts, resolved alerts, ticket trend direction) —
this is what `trend_mom` and `recurring_issues` in the schema are for.

## Output

Always report back in chat: the path to the generated `.md`/`.docx`, the
overall health status, and a short list of any `⚠️ MISSING` fields left for
the user to fill in.
