# IT Service Monthly Report — generator

New template + tool for the Wayama-style IT Service Monthly Report (the one
originally delivered to Kittisampan Concrete as a hand-filled `.docx`).
Built from a combined review by `/agy` (Gemini), `/zcode` (GLM), and Ayami's
own read of the original July 2026 report.

**What the original was missing**, in short: no SLA/uptime numbers, no
license-expiry tracking, no trend vs. last month, a Ticket Summary that
contradicted its own Ticket table, blank template rows nobody cleaned up, a
FortiGate section with zero data, and — the important one — real risks
(SMB 1.0 enabled, M365 expired, 85% of hardware >5 years old) that were
buried in the notes instead of surfaced as things the client needs to decide
on. This tool fixes the *shape* of the report so those things can't hide.

## Dashboard (UI)

A local web dashboard lives in `dashboard/` — form-per-section editing (with
live traffic-light/license-expiry previews) instead of hand-editing YAML,
plus an "AI ช่วยวิเคราะห์" panel that shells out to `zcode`/`agy` (whichever
you already use — no API key needed) to turn freeform notes into structured
data you can review before importing.

```bash
cd dashboard
bun install
bun run server.ts &   # API on :8787 (reads/writes ../data/*.yaml, runs generate.py, calls zcode/agy)
bun run dev            # Vite dev server on :5183, proxies /api to the server above
```

Open http://localhost:5183. Pick or create a month, fill sections from the
sidebar, click "Generate Report" to produce the `.md`/`.docx` via the same
`generate.py` the CLI path uses — both paths write the identical YAML shape,
so you can mix hand-edits, `/it-report`, and the dashboard freely on the same
data file. See `dashboard/` for the source; it's a plain Vite+React+TS app
with a small Bun API server, no build/deploy step required for local use.

## Files

| File | What it is |
|---|---|
| `schema.yaml` | The data contract — every field the report needs, with inline comments |
| `template.md.j2` | Jinja2 markdown template that renders a data file into the report |
| `generate.py` | CLI: data file in → `.md` (always) + `.docx` (with `--docx`) |
| `data/<client>/<YYYY-MM>.yaml` | One data file per client per month — start each month from `schema.yaml` |
| `data/<client>/profile.yaml` | Client-constant info (company name, contact) |
| `data/<client>/history.yaml` | Tickets from months this tool didn't generate (pre-tool history, etc.) — reference only, never rendered into a monthly report |
| `data/kittisampan/2026-07.yaml` | Filled reference example, reconstructed from the original July 2026 report |
| `assets/wayama-logo.png` | Header logo used by the `.docx` renderer (extracted from the original report) |
| `.venv/` | Isolated Python env (not committed — see `.gitignore`) |

## Setup (one-time)

```bash
cd ψ/lab/it-monthly-report
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
```

## Generate a report

```bash
cp schema.yaml data/kittisampan/2026-08.yaml   # start a new month from the blank schema
# ...fill data/kittisampan/2026-08.yaml (see "Filling in data" below)...
./.venv/bin/python generate.py data/kittisampan/2026-08.yaml --docx
# -> data/kittisampan/2026-08.md and data/kittisampan/2026-08.docx
```

## Filling in data — two ways

**1. By hand.** Open the copied YAML and fill in the fields directly. Leave
anything unknown as `null` — the generator renders those as `⚠️ MISSING` in
the report instead of silently dropping them, so gaps stay visible instead of
disappearing (that was the original report's biggest problem).

**2. Let AI fill it from freeform notes.** You don't need to hand-build the
YAML yourself — describe the month in plain language (Thai or English: "ย้าย
Express ไป desktop ใหม่, backup ปกติ, M365 จะหมดอายุอาทิตย์หน้า...") to
Claude/Ayami, zcode, or agy, and ask it to fill `data/<month>.yaml` following
`schema.yaml`. A dedicated skill wraps this: run `/it-report <your notes>` in
this repo and it will read the schema, map your notes onto it, flag anything
that looks like a real risk as a `critical_alerts` entry even if you didn't
call it out as one, leave genuinely unknown fields as `null` rather than
guessing, write the data file, and run the generator for you. See
`.claude/skills/it-report/SKILL.md` for exactly what it does.

Both paths write the same shape of YAML — pick whichever is faster for a
given month. A narrated month is faster to produce; a structured one (e.g.
exported from a monitoring tool) is more precise for numbers like uptime %.

## Design notes

- **License alerts are computed, not hand-typed.** `generate.py` scans every
  `expire` date in `software.*_licenses` and auto-flags anything expired or
  due within 30 days — so a report can't ship with an expired license buried
  in a table nobody re-reads (like the original M365 case).
- **`recommendations` are sorted by priority automatically** (high → low),
  regardless of the order you entered them.
- **`trend_mom`** has no automatic carry-over yet — when generating month N,
  copy the relevant numbers from month N-1's `.yaml` by hand (or have the
  `/it-report` skill do it — it's instructed to read the previous month's
  file when one exists).
- Markdown is the primary/reviewable output; `.docx` is a direct python-docx
  render (not a markdown→docx conversion) styled after the original Wayama
  report — cover page, dotted index, two-tone section banners (dark blue
  `#323E4F` / amber `#FFC000`), Cordia New Thai body + Microsoft Sans Serif
  headings, logo header and a "Page X of Y" footer — while adding the
  sections the original lacked (SLA, critical alerts, trend, scope check).
  (Not cloned: the cover's floating stock-photo strip and contact icons —
  skipped deliberately since they're decorations, not data.)
- Tickets that don't belong to the reported month (pre-tool history etc.) go
  in `data/<client>/history.yaml`, never the monthly file — this is how the
  original report's "summary says 0 but the table lists January tickets"
  contradiction stays fixed. `find_previous_month()` only considers
  `YYYY-MM.yaml` files, so helper files (`profile.yaml`, `history.yaml`)
  never skew trend/changelog detection.
