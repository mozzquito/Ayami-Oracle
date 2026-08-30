---
pattern: "Learned mildronize/my-template: a working reference for human-SSO + AI-API-key dual-identity auth, append-only activity log, and cross-language typed API contracts"
date: 2026-08-31
source: "learn: mildronize/my-template"
concepts: ["learn", "codebase", "auth", "append-only-log", "openapi-codegen", "agent-friendly-scaffold"]
---

# Learned mildronize/my-template

- Dual auth (human SSO session vs. agent API key) resolving to one `identity.User` model, with an explicit mutual-exclusion invariant (Bearer never → owner role, session never → agent role) is a clean, working pattern for separating "who did this — human or AI" at the identity layer, not just at the UI layer.
- The append-only `todo_events` table pattern (single write path, no UPDATE/DELETE, idempotency key, monotonic per-parent sequence number) is a concrete reference implementation worth reusing for any "append-only activity log" requirement — it also solves attribution (actor_id on every row) for free.
- Two separate OpenAPI specs (agent-facing vs. browser-facing), each codegen'd into both Go and TypeScript, is a working way to keep a "typed contract shared by backend and frontend" from drifting — a renamed field breaks both builds instead of silently diverging.
