---
pattern: when a deliverable has an obvious "good/bad" slot but no agreed threshold exists, render it neutral rather than inventing a plausible-sounding cutoff
date: 2026-08-22
source: rrr: ayami-oracle
concepts: [verify-before-asserting, monitoring, thresholds, honesty, report-design]
---

# Don't invent thresholds — render neutral instead

While building `ψ/lab/grafana-report-bot/`, I added a color-coded risk matrix (CPU/Memory/Storage
per host, red if over the agreed threshold). มอส then asked to add Network and Disk I/O to the same
table. Every other column in that table was red/green — the visual pull to just pick a plausible
number ("say, >100 Mbps is red") and keep the table uniform was real, because a table with two
gray "informational only" columns next to four colored ones looks unfinished.

I didn't invent one. No threshold for Network or Disk I/O had ever been discussed or agreed with
มอส in this whole session — CPU/Memory (>80%) and Storage (≤10% remaining) were explicit, discussed,
confirmed numbers; Network/Disk I/O were not. So those two columns render as plain gray text with
an explicit note ("ยังไม่มีเกณฑ์ที่ตกลงกันไว้" — no agreed threshold yet) instead of a fabricated
red/green split.

**Why**: a threshold implies a decision was made about what counts as a problem. Inventing one
myself would mean silently making that decision for มอส and presenting it as if it had been agreed
— indistinguishable, from the report reader's side, from a real threshold. This is the same failure
shape as [[2026-08-22_verify-fine-grained-data-before-writing-root-cause]] (asserting a specific
claim without the verification/agreement that would actually back it) applied to a different kind
of claim: not "here's what caused this," but "here's the line between fine and not-fine."

**How to apply**: any time a deliverable has a slot that visually wants a judgment call (a
threshold, a severity color, a pass/fail label, a recommended value) and no one has actually
supplied or agreed the boundary, leave it unjudged and say so explicitly — a plain informational
value with a visible "no threshold set" note. It reads as less finished than a fully colored table,
and that's correct: it *is* less finished, honestly, until the person who owns that decision
supplies the number. Don't let visual uniformity across a table (or a deliverable) pressure a
default cutoff into existence.
