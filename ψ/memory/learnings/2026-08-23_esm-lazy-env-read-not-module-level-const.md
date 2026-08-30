---
pattern: "In a TypeScript/ESM project using dotenv, never read process.env.X as a module-level constant in a file that gets imported by the entrypoint that calls dotenv.config() — static imports are always hoisted and evaluated before the importing module's own top-level code, so the constant permanently captures an empty/stale value from before .env was loaded. Read env vars lazily, inside functions, in any non-entrypoint module."
date: 2026-08-23
source: "rrr: ayami-oracle — grafana-report-bot Discord delivery deploy"
concepts: ["typescript", "esm", "dotenv", "module-loading-order", "nodejs"]
---

# Learned: ESM static-import hoisting breaks module-level dotenv reads in non-entrypoint files

## What happened

`ψ/lab/grafana-report-bot/src/cli.ts` correctly called `dotenv.config()` (aliased
`loadEnv()`) near the top of its own body, before reading `process.env.GRAFANA_URL`
etc. later in the same file — that pattern worked fine.

But `src/discord.ts`, a separate module imported by `cli.ts` via
`import { hasDiscordWebhook, sendReportFile, ... } from "./discord.js"`, had its own
module-level constant:

```ts
const DISCORD_WEBHOOK_URL = process.env.DISCORD_WEBHOOK_URL ?? "";
```

A live end-to-end test (real `daily` report run against production Grafana/Discord)
silently skipped Discord delivery with `"DISCORD_WEBHOOK_URL not set"`, even though the
`.env` file had a correctly-set, verified-present value.

## Root cause

ES module static imports are hoisted and fully evaluated **before** the importing
module's own top-level statements run — this is spec behavior, not a bug in the
bundler/runtime. `cli.ts`'s import of `discord.js` (line ~33) causes `discord.ts`'s
entire module body — including its `process.env.DISCORD_WEBHOOK_URL` read — to execute
*before* `cli.ts` reaches its own `loadEnv()` call (line ~35), regardless of the
textual order those two lines appear in `cli.ts`. Moving `loadEnv()` earlier in
`cli.ts` would NOT fix this — the import resolution order is fixed by the module
graph, not by statement position in the entrypoint file.

## The fix

Convert the module-level constant to a function that reads `process.env` at call time:

```ts
function webhookUrl(): string {
  return process.env.DISCORD_WEBHOOK_URL ?? "";
}
```

and call `webhookUrl()` inside each exported function instead of referencing a
captured constant. By the time any of those functions is actually *called* (well
after the entrypoint's module graph has fully loaded and `loadEnv()` has run), the
env var is populated correctly.

## How to apply

Any TypeScript/Node project using `dotenv` (or similar) where the entrypoint loads
`.env` in its own body: audit every non-entrypoint module for `const X =
process.env.Y` at module scope. If found, convert to a lazy accessor function. This
is invisible in local dev if you `export DISCORD_WEBHOOK_URL=...` in your shell before
running (shell env vars are already present when the process starts, masking the
bug) — it only surfaces when the value comes *exclusively* from a `.env` file loaded
by `dotenv.config()` at runtime, which is exactly the deployment shape (cron/launchd)
most likely to hit it and least likely to be caught by ad-hoc manual testing.

## Related

Caught via live production testing (a real automated `daily` run), not via typecheck
or unit test — `tsc --noEmit` and `npm run build` both passed clean throughout,
because the bug is a runtime *value* problem, not a type problem. Reinforces
[[feedback_verify_before_asserting]] — this bug would have shipped invisibly if the
delivery step hadn't been verified end-to-end against the real webhook.
