---
pattern: When railway logs --lines/--since returns empty for a cron-job service, query deploymentInstanceExecutions via GraphQL to find the real execution/deployment ID, then fetch logs scoped to that ID directly
date: 2026-09-08
source: rrr: market-backtester (ayami-oracle)
concepts: [railway, cron-jobs, cli-gaps, graphql-fallback, log-verification]
---

# Railway CLI's `logs --lines`/`--since` can silently return nothing for a cron-job service — use GraphQL execution history instead

## What happened

Asked to verify a specific cron run (scheduled 09:00 UTC hourly `market-backtester-advise`
cron job) actually fired and behaved correctly. Tried the obvious approaches first:

```bash
railway logs --lines 200 --service market-backtester-advise        # empty
railway logs --service market-backtester-advise --since 2h         # empty
railway logs --service market-backtester-advise --since 3h -d      # empty (exit 0)
railway logs --service <explicit-service-id> --since 3h            # empty (exit 0)
```

All four returned exit code 0 with zero log lines, for a service that had definitely
executed and definitely produced console output — `railway status` even showed the
cron job as `● Online` with a valid `next run in N minutes`.

## Root cause / working theory

`railway logs` with `--lines`/`--since` appears to resolve logs against "the most recent
successful deployment" or a similarly deployment-scoped default — for a **cron-job**
service specifically, each scheduled tick does *not* create a new top-level Deployment
record the way `railway up` does; ticks are tracked as separate
`DeploymentInstanceExecution` records under whichever Deployment is currently live. The
CLI's time-range log fetch doesn't appear to traverse execution history the same way its
own `deploy-cron.sh`-style GraphQL verification does — it's the same category of gap this
project already worked around for `cronSchedule` propagation (`railway up` not reliably
setting the live schedule; see `deploy-cron.sh`'s GraphQL mutation + verification step).

## The fix that worked

Query execution history directly via GraphQL, using the same `railway api` mechanism
already established in this project for the cronSchedule verification workaround:

```bash
SERVICE_ID="<service-id>"
ENVIRONMENT_ID="<environment-id>"
railway api "query { deploymentInstanceExecutions(input: {serviceId: \"$SERVICE_ID\", environmentId: \"$ENVIRONMENT_ID\"}, first: 20) { edges { node { id deploymentId status createdAt completedAt updatedAt } } } }"
```

This returns real execution records with real timestamps (`createdAt`/`completedAt`) and,
critically, the `deploymentId` each execution actually ran under — which can differ from
whatever the *current* deployment is if a new deploy landed between two scheduled ticks
(exactly what happened here: the execution in question ran under a deployment 14 minutes
*before* a later same-day deploy). Once the right execution/deployment ID is known:

```bash
railway logs <deployment-id> --lines 200    # positional deployment ID arg — this works
```

returns the actual console output for that specific run.

## Generalizable rule

When a platform CLI's time-range or service-scoped log command returns empty for
something you know executed (a cron tick, a one-off job, a specific scheduled run), don't
conclude the logs don't exist. Query the platform's execution/deployment history API
directly to find the specific execution or deployment ID, then fetch logs scoped to that
exact ID — time-range log queries and per-execution deployment tracking can be genuinely
disconnected features on the same platform, especially for job-style (not always-on)
services. This generalizes beyond Railway: any platform distinguishing "logical service"
from "individual runs of that service" (cron jobs, batch jobs, scheduled functions) is a
candidate for this same CLI gap.

A second, related rule surfaced in the same investigation: before reporting on "the
behavior of a just-shipped change," cross-check the actual deployment timestamp against
the timestamp of the event being investigated. A deploy landing between two scheduled
runs means the run in question may have executed under the *previous* version of the
logic — don't assume a user's framing ("since deploying X") is automatically accurate;
verify which build was actually live at that moment before reporting.
