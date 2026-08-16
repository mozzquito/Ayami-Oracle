---
pattern: When a cloud platform's CLI status display and its actual server-side state can silently diverge, verify safety/scheduling-critical fields via the platform's API directly and bake that verification into the deploy script — never trust CLI display alone.
date: 2026-08-15
source: "rrr: ayami-oracle"
concepts: [railway, cron, deployment-verification, silent-failure, dashboard-desync]
---

# Verify platform state via API, not CLI display

Railway's `railway up` did not reliably propagate `deploy.cronSchedule` from `railway.json` to
the live `ServiceInstance.cronSchedule` — and `railway status`'s CLI display kept showing what
looked like the correct schedule even after the live cron had gone dark for 3 days with zero
errors anywhere in the logs. The only reliable ground truth was a direct GraphQL query for
`nextCronRunAt`; a non-null value there was the sole proof the cron was actually live.

**Why this matters beyond Railway**: any platform where a CLI/dashboard is a *cached or
best-effort* view rather than a live read of server state can produce this failure mode — a
config that "looks right" locally and in the tool's own status output, but is silently wrong on
the server. This is worse than an error, because there's no error to notice.

**Generalizable rule**: for anything safety- or schedule-critical (cron, autoscaling policies,
DNS, TLS renewal), don't trust a CLI's status/display command as verification. Find the specific
API/field that reflects live server state, query it directly, and make that query part of the
deploy script itself (fail loudly if it doesn't confirm) rather than a one-time manual check.

**Related pattern caught same session**: a dashboard read `cloud_run.py`'s per-symbol strategy
name via a hardcoded string instead of importing/looking it up dynamically — when production
switched strategies, the dashboard would have silently kept showing signals from the *old*
strategy with no error. Same root shape as the cron bug: two places agreeing on a value by
duplication instead of by import, with no error surface when they drift. When two services must
agree on a config value, always import the shared source of truth — never hardcode a copy.

See also: [[2026-08-15_lookahead-test-resampled-signals]] (if written), full context in the
2026-08-15 21:42 retrospective in `ψ/memory/retrospectives/2026-08/15/`.
