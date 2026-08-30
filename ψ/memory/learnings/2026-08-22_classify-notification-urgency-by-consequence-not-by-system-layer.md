---
pattern: When deciding which events in a notification system are "urgent" vs "informational," classify by the actual downstream consequence of a human missing it — not by which layer of the system the event technically belongs to.
date: 2026-08-22
source: "rrr: ayami-oracle"
concepts: [notification-design, decision-quality, trading-bot, urgency-classification]
---

# Classify notification urgency by consequence, not by system layer

Built a Discord quick-confirm flow for `market-backtester`'s paper-trading signals
(2026-08-17): ENTER signals got an individual message, an @mention, and a ✅/❌ confirm prompt.
EXIT signals (stop-loss/take-profit/strategy-exit) were classified as "informational only, no
action needed" — batched together, no mention. That reasoning held for the *paper* simulation
(nothing needs to happen when a paper position closes), but the whole system exists to inform
*real* trading decisions. Someone holding a real position matching the paper signal needs to
know to sell exactly as urgently as they needed to know to buy — missing a TAKE-PROFIT exit
message meant a real profit opportunity went unacted-on, discovered only when the user reported
a specific missed trade days later.

**Why this is a generalizable trap, not a one-off**: the mistake wasn't a coding bug — the code
did exactly what was designed. It was a design-time classification error made confidently,
because "does this event need urgent human action" was answered from the system's own internal
model (paper position lifecycle) instead of from the actual consequence in the world the system
is meant to affect (real money, real timing). Any notification/alerting system that mirrors or
informs a real-world process has this same trap: an event that looks passive from inside the
system (a state transition completing, a job finishing, a position closing) can still be
time-critical from the perspective of the human who has to act on it in the real world.

**Compounding factor**: a second-opinion consultation (zcode + agy, 2026-08-17) investigating
"why are signals arriving too late" focused entirely on entry-latency and never surfaced the
exit-side gap, because the question asked was scoped to entries. When investigating a class of
problem, explicitly enumerate every event type in scope rather than trusting that fixing the most
obvious instance covers siblings of the same issue.

**Rule going forward**: for any notification urgency classification, ask "what does the human
lose by seeing this a batch-cycle late, vs. never seeing it prominently at all" — not "does the
internal state machine consider this a terminal/passive event."
