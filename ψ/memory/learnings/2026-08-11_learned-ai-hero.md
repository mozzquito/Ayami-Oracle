---
pattern: "Learned ai-hero-dev/ai-hero: numbered lesson-as-runnable-unit convention, Evalite pairing, hand-rolled agent loop over SDK maxSteps"
date: 2026-08-11
source: "learn: ai-hero-dev/ai-hero"
concepts: ["learn", "codebase", "vercel-ai-sdk", "evals", "agent-loop", "mcp"]
---

# Learned ai-hero-dev/ai-hero

Matt Pocock's (aihero.dev) open-source "AI Hero" course repo — same author as `mattpocock/skills` ([[2026-08-11_learned-mattpocock-skills]]). TypeScript/pnpm monorepo of runnable examples on the Vercel AI SDK, MCP, and Evalite.

- **Lesson unit shape**: every numbered example folder is `main.ts` (self-running via `tsx`, no build step) + `readme.md`/`article.md` + an optional co-located `*.eval.ts` using Evalite. Consistent enough that `internal/run-example.ts` resolves lessons by short alias (`v 01` → `vercel-ai-sdk/01-generate-text`).
- **Deliberately hand-rolled agent loop**: `courses/01-deepsearch-in-typescript/` implements its own `while (!ctx.shouldStop())` loop around a `SystemContext` state object rather than using the AI SDK's built-in `maxSteps` — worth remembering as a teaching/control-flow-transparency choice when the SDK's automatic looping is opaque to newcomers.
- **Gap noticed**: `examples/agents/` is still a stub, and no MCP *client* example exists (only MCP servers) — the repo is mid-build, not a finished reference.
