---
pattern: when a device's own status API contradicts what a user reports observing, ask what they were actually looking at instead of just reporting the discrepancy as resolved
date: 2026-08-26
source: rrr: ayami-oracle
concepts: [debugging, user-communication, iot, verification]
---

# Ask what the user observed when an API contradicts their report

Boss reported a specific camera couldn't connect to the Megvii box. Querying
the box's own `device_state` API and pulling the camera's RTSP stream
directly both showed it connected and working normally — the opposite of
what Boss described. The discrepancy was reported transparently (not
"you're wrong," but "here's what I see, which differs from what you
reported") — which is the right instinct — but the investigation stopped
there. No question was asked about what Boss was actually looking at when
they saw the failure: the box's own web UI, a specific setup step, an
earlier moment before the check, a completely different symptom being
mentally attributed to "connection."

**Why this matters**: an API-level check and a user's lived observation can
both be true at once if they're looking at different layers (UI state vs.
backend state, a snapshot in time vs. current state, or a different failure
entirely that surfaces similarly). Reporting "it looks fine from here" as
if that settles the question leaves the user's original problem
unaddressed — they may still be seeing the failure through whatever path
they were using, and now have no clear next step.

**Rule**: when your own verification contradicts a user's direct report of
a failure, don't stop at reporting the discrepancy — ask one clarifying
question about what they were looking at (which tool, which screen, when).
This costs one message and either surfaces the real gap (a UI bug your API
check can't see, a timing issue, a different device) or confirms the
problem has genuinely resolved itself, both of which are more useful than
leaving "my check disagrees with you" as the final word.
