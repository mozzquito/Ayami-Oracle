---
pattern: "Learned HKUDS/ClawWork: economic AI benchmark, non-invasive Nanobot cost wrapper, file-based JSONL state (no DB)"
date: 2026-08-11
source: "learn: HKUDS/ClawWork"
concepts: ["learn", "codebase", "ai-agent-benchmark", "economic-simulation", "nanobot"]
---

# Learned ClawWork

HKUDS's real-world economic benchmark: Nanobot-based AI agents start with $10, pay for every token they generate, and earn income only by completing GDPVal professional tasks (220 tasks / 44 occupations), scored by a GPT-5.2 LLM judge against per-occupation rubrics.

- **Non-invasive provider wrapping**: `clawmode_integration/` bolts economic tracking onto an existing Nanobot `AgentLoop` by subclassing it and swapping the `LiteLLMProvider` for a cost-capturing variant at `__init__` time — no fork of Nanobot's source needed. Useful pattern for adding cross-cutting concerns (cost, auditing, rate limits) to a third-party agent framework without vendoring it.
- **Quality-gated payment**: income is only credited if the normalized eval score clears 0.6 — a hard floor rather than a smooth payout curve, meaning low-effort work earns literally nothing rather than partial credit.
- **File-based state throughout**: no database — `EconomicTracker` writes per-agent JSONL ledgers, and the React/Vite/FastAPI dashboard reads those files directly (plus a `/ws` WebSocket for live pushes). Keeps the whole system inspectable with plain `jq`/`cat`.
