---
pattern: "Learned Tencent/AI-Infra-Guard: AI red-teaming platform (MCP/agent/skill/jailbreak scanners, SARIF output); best ayami-oracle fit is aig-skill-scan against SKILL.md files for prompt-injection/hidden-backdoor audit, as a Docker-backed on-demand slash command, not a periodic daemon"
date: 2026-08-26
source: "learn: Tencent/AI-Infra-Guard"
concepts: ["learn", "codebase", "security", "mcp", "skill-scan", "prompt-injection", "zcode", "agy"]
---

# Learned Tencent/AI-Infra-Guard

AI-Infra-Guard is Tencent Zhuque Lab's AI red-teaming platform: Go backend (Cobra CLI + WebSocket agent server) + React frontend + Python microservices (agent-scan, mcp-scan, skill-scan, AIG-PromptSecurity). Five scan types: AI-infra CVE fingerprinting, agent black-box scan, MCP server/skill static+dynamic audit (SkillTrustBench T01-T09), multi-turn jailbreak eval, LLM API/relay authenticity check. Outputs SARIF 2.1.0.

For ayami-oracle specifically: the strongest integration is `aig-skill-scan` run against `.claude/skills/*/SKILL.md` and `.agents/skills/*/SKILL.md` — it does an intent-alignment audit (does the SKILL.md description match what the code actually does) and catches embedded prompt injection / hidden backdoors, which is exactly the shape of ayami's skill-based architecture.

zcode and agy (consulted as required second opinions per this repo's SDLC-gate CLAUDE.md rule) **disagreed on MCP-scan scope**: agy said `mcp-scan` does both static source audit and dynamic live-endpoint probing; zcode said it's client-only, probing a *running* MCP server URL, with no static-analysis path — meaning it's not useful against ayami today (no MCP server of its own yet) until something like a planned oracle-v2 MCP server exists. This wasn't independently verified against `mcp-scan/` source — worth checking before building on either claim.

Both agents converged on: run it on-demand via a slash command when adding/editing a skill, not as a periodic/pre-commit job — AI-Infra-Guard needs a 2-container Docker stack up to serve its API, heavier than ayami's other CLI tools, and not worth it for a solo project's low change-rate on prompt files.

Full docs: `ψ/learn/Tencent/AI-Infra-Guard/AI-Infra-Guard.md` (hub) and same-day `2026-08-26/0456_*.md` files (Architecture, Code Snippets, Quick Reference).
