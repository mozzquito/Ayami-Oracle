---
pattern: When you fix something you cannot fully verify (the verification path itself is broken), state the fix as provisional in the record — don't let the write-up's confidence exceed what the evidence actually supports.
date: 2026-09-01
source: "rrr: ayami-oracle"
concepts: [verification, infrastructure-ids, commit-messages, epistemic-honesty]
---

# Don't overstate confidence in a correction you couldn't fully verify

On 2026-08-28, found that `market-backtester`'s `deploy-cron.sh` had a `SERVICE_ID` that didn't
match any live Railway service after an account migration. Re-derived a replacement via
`railway status --json`, matched by which service instance carried the live `cronSchedule` —
looked correct, and was committed with a confident explanation. It was wrong: Railway
distinguishes a top-level Service ID (project-scoped) from a ServiceInstance ID
(environment-scoped) for the same logical service — two different values. The GraphQL call this
script depends on wants the former; the value pulled from `serviceInstances[].id` was the latter.
The mistake stood, undetected, for 4 days.

**Why it wasn't caught at the time**: the one direct verification that would have confirmed or
refuted the new value (running the actual GraphQL query against it) was *already broken* by a
separate, known "Not Authorized" auth issue on the new account. So the fix was made, and written
up, using indirect/structural evidence only — a plausible match, not a confirmed one. What
actually surfaced the error on 09-01 was incidental: a build-log URL Railway generated for an
unrelated deploy happened to contain the *other* ID, making the discrepancy visible by accident,
not by any verification step actually catching it.

**The generalizable habit**: when the direct way to verify a fix is unavailable, and you're
relying on indirect/structural evidence (a field happens to match, a pattern looks right), say so
explicitly in whatever record you leave — a commit message, a report to the user, code comments.
"Corrected X to Y" reads as settled; "corrected X to Y based on indirect evidence (Z was
unavailable to confirm directly)" is honest about the actual confidence level and primes a future
reader (including future-you) to double-check rather than build on it as fact. The gap between
"I have a plausible answer" and "I have a verified answer" is exactly the gap that let this
mistake stand for 4 days without anyone — including me — flagging it as still-open.

See also: [[2026-08-22_verify-before-trusting-recurring-pattern]] (if it exists) or the broader
"verify before concluding" theme flagged repeatedly in this project's session-metrics history —
this is a specific instance of that same class of error, one step further: not just concluding
without verifying, but *writing up the conclusion with more certainty than the unverified status
warranted*.
