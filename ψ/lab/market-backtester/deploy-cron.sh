#!/bin/bash
# Deploys the cron service AND force-verifies the schedule actually took effect.
#
# Why this exists: `railway up` alone does NOT reliably propagate deploy.cronSchedule
# from railway.json into the service's live scheduler state. The deploy succeeds, the
# deployment's own manifest shows the correct cronSchedule, but the live
# ServiceInstance.cronSchedule silently stays/reverts to null — so the cron just never
# fires again, with no error anywhere. Confirmed real (not a CLI display bug) via direct
# GraphQL query, and confirmed NOT fixed by CLI upgrades or repeated `railway up` cycles.
# See README.md "Known bug (critical)" for the full incident writeup.
#
# Usage: ./deploy-cron.sh

set -euo pipefail
cd "$(dirname "$0")"

ENVIRONMENT_ID="fdb22b45-c55d-4b28-9b81-6786051e4c4a"   # production environment, market-backtester-advise project
SERVICE_ID="910c3b74-ecfe-492b-9cd4-3b67f7309671"        # market-backtester-advise service
# Rebuilt 2026-08-27 — the original "mozzquito's Projects" workspace (and every ID it
# contained) was deleted; these are the new project's IDs after a from-scratch rebuild.
CRON_SCHEDULE="0 * * * *"                                # every 1h = 24x/day (was every 2h; มอส asked for hourly 2026-08-28)

echo "== 1/3: deploying code via railway up =="
cp railway.cron.json railway.json
railway up --service market-backtester-advise

echo ""
echo "== 2/3: force-setting cronSchedule via GraphQL (bypasses the broken railway up path) =="
railway api 'mutation($environmentId: String!, $serviceId: String!, $input: ServiceInstanceUpdateInput!) { serviceInstanceUpdate(environmentId: $environmentId, serviceId: $serviceId, input: $input) }' \
  --var environmentId="$ENVIRONMENT_ID" \
  --var serviceId="$SERVICE_ID" \
  --var "input={\"cronSchedule\":\"$CRON_SCHEDULE\"}"

echo ""
echo "== 3/3: verifying nextCronRunAt is non-null (ground truth — do not trust railway status for this field) =="
RESULT=$(railway api 'query($environmentId: String!, $serviceId: String!) { serviceInstance(environmentId: $environmentId, serviceId: $serviceId) { cronSchedule nextCronRunAt } }' \
  --var environmentId="$ENVIRONMENT_ID" \
  --var serviceId="$SERVICE_ID")

echo "$RESULT"

NEXT_RUN=$(echo "$RESULT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['data']['serviceInstance']['nextCronRunAt'] or '')")

if [ -z "$NEXT_RUN" ]; then
  echo ""
  echo "❌ FAILED: nextCronRunAt is still null after the mutation. The schedule is NOT active."
  echo "   Do not assume this deploy worked — investigate before walking away."
  exit 1
fi

echo ""
echo "✅ Cron schedule confirmed active. Next run: $NEXT_RUN"
