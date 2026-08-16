---
pattern: When proposing a root-cause hypothesis about a system whose actual rendering/source code you've never seen, say explicitly "unverified hypothesis" — don't phrase it as a likely answer just because a nearby schema detail fits
date: 2026-08-16
source: "rrr: ayami-oracle"
concepts: [incident-response, hypothesis, confidence-calibration, database, cross-system]
---

# Flag hypotheses as unverified when you haven't seen the actual source

During a live production incident (a visa applicant's photo not rendering in
two BackOffice pages while a third page showed it fine), the reasonable next
move was to look at the schema already documented for the source database
(MSSQL, E-Application side) for a plausible explanation. Finding a
`CONTENT_TYPE`/`FILE_NAME` column on the attachment table made a "the file
was uploaded as PDF, and the broken pages naively render `<img src=...>`
while the working page has a PDF-capable viewer" theory easy to construct.

The theory was phrased as "เดาเหตุผลที่น่าจะตรงประเด็น" (roughly: "here's
probably the reason") — confident framing — despite the fact that the actual
rendering happens in the BackOffice system, which runs on a *different
database (Oracle) whose schema and source code have never been inspected in
this project at all*. The only evidence was a column name on the upstream
data table; zero evidence from the system that actually does the failing
render.

**Rule**: when a hypothesis about a bug spans a system boundary you have
schema/source visibility into only on one side, name that boundary
explicitly and mark the hypothesis as unverified until data from the actual
failing component confirms it. Confident phrasing ("this is probably why")
is earned by evidence from the system that's actually misbehaving, not by
a plausible-sounding column name on an upstream table. This matters more,
not less, when the user has no way to independently double-check your
reasoning (they're asking *because* they don't have the schema knowledge) —
overconfident framing there gets taken at face value.
