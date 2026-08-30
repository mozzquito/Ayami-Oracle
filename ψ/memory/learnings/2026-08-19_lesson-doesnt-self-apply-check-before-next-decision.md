---
pattern: "A lesson written earlier in the same conversation doesn't apply itself — check it against the axis it actually operates on before the next relevant decision"
date: 2026-08-19
source: "rrr: ayami-oracle"
concepts: ["delegation", "zcode", "self-correction", "reasoning"]
---

# Writing a lesson down is not the same as consulting it

Minutes after closing a retro with a lesson-learned file about "don't retry zcode blind after an identical same-day failure," I dispatched zcode again for a *different* task (brainstorm vs. code-snippet extraction) — reasoning that a new task shape might succeed where the old one failed. It failed identically (`524 Origin Time-out` from z.ai), a 3rd same-day occurrence.

The lesson was correct but I applied it at the wrong axis: the failure was infra-level (z.ai's API being down), not task-level (this specific task hasn't been tried yet). "It's a different task" is not a valid override when the thing that's actually broken doesn't care what task you're asking it to do.

**Rule**: before repeating an action a just-written lesson warns against, check what axis the lesson actually operates on (infra health vs. task shape vs. prompt wording, etc.) and confirm the new situation genuinely differs on *that* axis — not just on some other axis that feels like it should matter. A lesson sitting in a file you wrote 10 minutes ago provides zero protection if you don't re-consult it before the next decision it applies to.

This generalizes beyond zcode: any "don't do X again" lesson from earlier in a session needs an active check, not passive availability, before the next X-shaped decision.
