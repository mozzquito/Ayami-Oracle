---
pattern: When building a reference table/report from partly-inferred data, mark provenance per-cell before shipping — don't let polish imply certainty
date: 2026-08-30
source: rrr: ayami-oracle
concepts: [data-provenance, artifact-design, notebooklm-interview, judgment-call]
---

# Tag inferred data with provenance before shipping tables

When an interview/summarization source (NotebookLM chat, meeting transcript, etc.) doesn't
state a value directly and I fill a gap by inferring from surrounding context (e.g. mapping
"ตามคำขอ (ไม่เร่งด่วน)" onto an Incident row that had no Frequency value in the original data),
that inferred value must carry a visible provenance marker in the final artifact — not just be
formatted identically to confirmed data.

**Why**: In this session, the first published version of an HTML tracking table presented
inferred Incident Frequency/Owner values in the same clean chip/table styling as confirmed
Routine data pulled straight from a Google Sheet. The polish of the table format made the
inferred rows look equally authoritative. I did add an "เติมโดย Ayami" (added by Ayami) tag per
row, which caught the problem — but the instinct to ship a good-looking table came before the
instinct to flag uncertainty, and it was a close call. A user skimming a well-designed table
will trust it; the visual design itself becomes an implicit certainty signal unless deliberately
undercut.

**How to apply**: Before publishing any artifact (table, report, dashboard) that mixes confirmed
source data with inferred/derived values:
1. Decide the provenance marker *before* writing the row, not as an afterthought pass.
2. Use a visually distinct but not alarming marker (a small tag/badge works better than a
   footnote asterisk that's easy to miss).
3. State explicitly in the artifact's footer/caption that inferred rows need team verification —
   don't rely on the marker alone to communicate that.
4. This applies especially to: severity/priority levels, ownership assignments, frequency/SLA
   numbers, and anything a reader might copy into a "source of truth" document (a live shared
   spreadsheet, a policy doc) without re-checking.

Related: [[verify-before-asserting]] — same root instinct (don't let confident presentation
outrun actual certainty), applied here specifically to structured/tabular output where the
format itself is a confidence signal.
