# Real Estate AI Video — Cloudflare deployment

Production sketch of the CLI prototype in `../src/`, running as a Cloudflare Worker +
Workflow instead of a local CLI call. Same 4 pipeline steps (enhance → script → voiceover
→ render), same verified API integrations — this layer only adds orchestration, job
tracking (D1), and an HTTP trigger.

Chosen over the original playbook's n8n-on-Railway plan and over an earlier
Container+Queue sketch — see `ψ/memory/retrospectives/` for the reasoning. Short version:
every pipeline step is a plain outbound HTTP call, so it fits Cloudflare Workflows
directly (built-in per-step retry, survives Worker timeouts) with no Container needed.

## What's here

- `src/worker.ts` — `POST /jobs` (creates a D1 job row, triggers the Workflow),
  `GET /jobs/:id` (reads job status)
- `src/workflow.ts` — the 4-step Workflow, reusing `../src/{enhance,script,voiceover,render}.ts`
  unmodified (those files were refactored to take an explicit `cfg` param instead of a
  `process.env`-based singleton, so they work in both the CLI and here)
- `migrations/0001_init.sql` — `jobs` table (status, script, costs, video_url, error)
- `wrangler.jsonc` — Worker + Workflow + D1 binding config

## Status (2026-08-31)

- ✅ `npm run typecheck` passes
- ✅ D1 database `realestate-video-db` created and migrated (remote)
- ✅ **Deployed.** Live at `https://realestate-video.phongcheat-phus.workers.dev`
  (Version ID `7b2ac85d-320c-4189-ad41-9a7c36d9b542`). Smoke-tested (routing, D1 query,
  input validation) — no real job has been run yet, see below.
- ❌ **No API keys configured as Worker secrets yet** — see Setup below. Any real job
  triggered right now will fail immediately on the first step.
- ❌ **Not tested end-to-end.** Photo enhancement swapped from fal.ai to Cloudflare
  Workers AI (`pruna/p-image-upscale`) 2026-08-31 — fal.ai's account was locked pending a
  credit top-up and was never actually verified live either. The swap removes that
  blocker but is itself unverified against a real call yet. Two blockers carry over
  unchanged from the CLI prototype (see `../README.md`): `SPEECHGEN_EMAIL` unset,
  Creatomate trial render_scale capped at 0.25.

## Setup (once the blockers above are cleared)

```bash
npm install
npx wrangler secret put OPENROUTER_API_KEY
npx wrangler secret put CLOUDFLARE_API_TOKEN
npx wrangler secret put CLOUDFLARE_ACCOUNT_ID
npx wrangler secret put SPEECHGEN_API_KEY
npx wrangler secret put SPEECHGEN_EMAIL
npx wrangler secret put CREATOMATE_API_KEY
npm run deploy
```

For local dev against the local D1 replica: `npm run db:migrate:local` then `npm run dev`
(put the same keys in a `.dev.vars` file instead of `wrangler secret put`).

## Known gaps not yet addressed (flag before real traffic)

- **`POST /jobs` has no auth.** Anyone with the URL can trigger a job, which spends real
  money on Workers AI/OpenRouter/SpeechGen/Creatomate credits. Needs at least a shared-secret
  header or a real auth scheme before this is reachable from outside your own testing —
  this is on top of, not instead of, the "payment collection" gap already flagged in the
  CLI prototype's README.
- **An orphaned `pending` row is possible.** If `env.PIPELINE.create()` throws after the
  D1 row is inserted (e.g. hitting a Workflow instance-creation rate limit), that job row
  stays `pending` forever with no Workflow ever tracking it. Fine for low volume; add a
  cleanup/retry path before this handles real customer traffic.
- Job status updates inside `step.do` callbacks are correctly skipped on Workflow replay
  once a step is memoized (per Workflows' rules), but the two un-memoized writes after the
  last step (the final `status='done'` update and the `catch` block's `status='failed'`
  update) could in principle re-run on a rare mid-flight replay. Both are idempotent
  (same values rewritten), so this is safe, not a correctness bug — noted for anyone
  auditing this against strict Workflows best practice later.
