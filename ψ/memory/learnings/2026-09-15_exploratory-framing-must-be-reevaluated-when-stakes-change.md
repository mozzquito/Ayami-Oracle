---
pattern: "exploratory, skip the ceremony" framing must be re-evaluated the moment a task's real stakes change — don't let it ride on autopilot
date: 2026-09-15
source: "rrr: ayami-oracle"
concepts: [sdlc-gate, zcode-agy-consult, scope-escalation, context-anchoring]
---

# Re-evaluate "exploratory" framing when stakes change mid-session

A session started as a hypothetical feasibility question ("รับงานดูแล SCCM/Exchange ให้ธนาคารไหวไหม")
and was correctly handled as exploratory — short recommendation, one AskUserQuestion, no SDLC
ceremony. Partway through, the user pasted the actual RFP text (real bank, real deadline in 3
days, real contractual/financial stakes). The task had become substantive work — drafting SOW/SLA
structure and clarification questions for a real procurement submission — but the "skip the
ceremony" framing from the opening kept being applied anyway. The parent CLAUDE.md's SDLC-gate +
zcode/agy second-opinion rule was never invoked, even once, despite explicitly covering exactly
this kind of substantive deliverable.

**Why**: The exploratory-vs-substantive read happens once, early, and isn't naturally revisited.
Nothing in the flow prompts a re-check when new information (a pasted document, a stated deadline,
a named counterparty) changes what kind of task this actually is now.

**How to apply**: Treat the arrival of a real external document (RFP, contract, ticket, dataset)
mid-conversation as a trigger to re-ask: "is this still pure investigation, or is it now
substantive work with real stakes?" If the latter, apply the SDLC gate and zcode/agy consult from
that point forward — it's fine that the first half of the session didn't need it, but the second
half should not silently inherit the first half's framing.

**Related**: also apply the same re-check to any earlier draft/artifact produced under the old
framing — a generic SOW written before the real RFP appeared can silently go stale once the real
structure (e.g. MD-based contract mechanics) is known. Reconcile or explicitly flag it as
outdated rather than leaving two divergent documents standing.
