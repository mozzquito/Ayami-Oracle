---
pattern: "When a destructive action's target has already shown strong evidence of high consequence (live production traffic, another party's real work), a second explicit user instruction to proceed authorizes the action — but the confirmation bar should still scale to name that specific consequence, not just repeat the original words"
date: 2026-08-12
source: "rrr: ayami-oracle (Railway discerning-reflection deletion)"
concepts: ["safety", "destructive-actions", "confirmation", "railway", "production-infrastructure"]
---

# Scale the confirmation bar to the consequence, not just the repetition

Investigated a Railway project before a requested deletion, found strong evidence it was
live production infrastructure (running status, source repo name matching a real client
project, an active public domain, real volume data) for the user's actual job — not a
throwaway test resource like a prior, correctly-deleted project in the same session. Refused
initially and explained why. The user then repeated the instruction with the specific
project name. I proceeded and deleted it.

**Why this is worth naming, even though it wasn't clearly wrong**: user authority over their
own account is real, and a second explicit, specific instruction after a clear warning is
meaningfully different from the first ambiguous one — refusing forever would override their
informed decision about their own resources. But the informed-consent bar should scale with
the blast radius already surfaced. Once I had strong evidence this was a *running service
with live traffic* (not just "an old project"), the appropriate next step was one more
question that named that specific consequence explicitly ("this will take the live service
down right now, not just archive an idle project — confirm?") rather than treating a
repeated instruction as automatically sufficient. Two confirmations of the same words carry
less information than one confirmation of the actual mechanism of harm.

**How to apply**: after refusing a destructive action once and explaining the specific risk
found during investigation, if the user reasserts the instruction, the next check should
restate the *consequence* in different, more concrete terms — not just re-ask "are you
sure?" in the same shape as before. If the user's second confirmation already independently
names the specific consequence (not just "yes, do it"), that's sufficient and no third round
is needed. The goal is verifying the user has the same picture of what will happen that the
investigation surfaced, not just checking their persistence.
