---
pattern: A dramatic diagnostic number (a huge mismatch, a suspiciously clean match) is not automatically confirming evidence for the hypothesis you're testing — weigh it equally as evidence you made a mistake
date: 2026-09-15
source: "rrr: ayami-oracle (evisa/Wayama session)"
concepts: [debugging, overconfidence, verification, sql, hypothesis-testing]
---

# Dramatic diagnostic numbers aren't automatically confirming

## What happened

Two days into documenting a known bug (an Oracle view, `VW_GET_APPLICATION_CCDC`, silently
dropping rows on an `INNER JOIN`), I was reconstructing a *different* report's query from an
output file alone — no source query available. I joined the same view (reasonable-looking
choice: it resolves human-readable names from IDs, which the report needed). Testing it against
one date gave a plausible result. Testing it against a different date gave `COUNT(*) = 123,158`
against a raw table count of `5,973` — a ~20x blowup.

I concluded this was *a second confirmed instance* of the known view-join bug, and wrote that
conclusion into a commit message with specific numbers as evidence. It felt well-supported: a
real bug, a real number, a clean narrative connecting them.

It was wrong. The user later sent the actual source query for that report. It never touched the
view at all — it joined master tables directly. The 123,158 blowup was caused by my own
reconstruction choosing the wrong join target, not by the view having a real cardinality problem
in that context. I had to go back into the previous commit and correct the record in the next one.

## The pattern to avoid

A dramatic number — a huge mismatch, a suspiciously exact match, a percentage that lands right on
a round figure — has emotional weight that outruns its actual evidentiary weight. When a
hypothesis is already active in your head (here: "this view has a known row-drop/duplication
issue"), a big number that's *consistent* with that hypothesis gets processed as confirmation.
But the same number is equally consistent with a much more mundane explanation: your own query,
your own join choice, your own assumption was wrong. Both explanations produce the same observed
number. The number alone doesn't distinguish them.

This is a sharper, more specific case of "don't ship a guessed query with more confidence than
the guess deserves" — that lesson is about the *artifact* (the query) looking too polished. This
one is about the *diagnostic output* (a test result, a count, a comparison) feeling like proof
when it's actually just as likely to be measuring your own mistake.

## What to do instead

- When a test result seems to confirm a hypothesis you already hold, explicitly ask: **what
  would this same number look like if I'm wrong instead of the system being wrong?** If both
  are plausible, the number hasn't actually discriminated between them yet.
- Before writing a diagnostic finding into a permanent record (a commit message, a doc), check
  whether the finding depends on a component *you* chose (a join, a filter, a reconstruction)
  rather than one *confirmed from the actual system* (a real source query, a verified schema
  fact). If it's the former, the finding is conditional on your choice being right — say so.
- Prefer describing findings as "X happened when I did Y" rather than "X is true about the
  system" until the causal component (Y) is independently verified, not just internally
  consistent with your working theory.

## Why this matters beyond this one case

This is a recurring trap for any agent doing empirical debugging under uncertainty: confirmation
bias doesn't just distort which experiments you run, it distorts how much weight you give the
*results* of experiments you already ran. A number that fits the story you're already telling
needs the same scrutiny as one that contradicts it — maybe more, since the contradicting number
would have triggered doubt automatically, while the confirming one won't.
