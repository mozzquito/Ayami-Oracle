---
pattern: "Learned astrathezero/antigravity-bridge: quota-aware multi-account LLM proxy, not a fit for ayami-oracle — architecture mismatch + agy binary name collision"
date: 2026-08-22
source: learn: astrathezero/antigravity-bridge
concepts: ["learn", "codebase", "llm-proxy", "claude-code-integration", "naming-collision"]
---

# Learned antigravity-bridge

antigravity-bridge is a zero-dependency single-file Python REST gateway that pools multiple Google OAuth profiles and exposes them through both OpenAI- and Anthropic-Messages-compatible endpoints, with quota-aware auto-fallback across profiles as its core value-add. It works by shelling out to a CLI literally named `agy`/`antigravity` (Google's Antigravity IDE CLI) for every request — the "Claude" and "GPT" model names it lists are backends that CLI itself exposes, not direct API integrations.

Not a fit for ayami-oracle: the architecture (HTTP server → subprocess → CLI → SSE) is fundamentally different from Claude Code's native skill/subagent model, and ayami-oracle isn't quota-constrained on Claude access the way this tool is designed to solve. zcode's independent read agreed — worth borrowing the *pattern* (profile rotation, dual-API translation) if ever needed, not the dependency itself.

Concrete risk if ever considered: the project's required CLI binary is named `agy`, which collides with ayami-oracle's own `/agy` skill binary at `~/.local/bin/agy` (see [[oracle_agy_skill]] if that memory exists) — installing it would risk PATH shadowing.
