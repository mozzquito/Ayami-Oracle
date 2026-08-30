---
pattern: "Found AutoClaw (Zhipu AI/Z.ai's AutoGLM desktop agent app) installed and actively running on this machine, with exec-without-confirmation enabled and a live plaintext bearer token in its config — zcode + agy both flagged security concerns worth a conscious decision"
date: 2026-08-22
source: "learn: local app inspection (no repo) + https://autoclaw.z.ai/"
concepts: ["learn", "security", "local-machine-audit", "second-opinion", "zcode", "agy", "mcp"]
---

# Learned AutoClaw

AutoClaw is Zhipu AI / Z.ai's consumer desktop AI agent product (AutoGLM), bundle id `com.zhipuai.autoclaw`, v1.17.5. Discovered installed at `/Applications/AutoClaw.app` and **actively running** (from a mounted DMG at `/Volumes/AutoClaw 1.17.5-arm64/`, not the `/Applications` copy) during an unrelated session on 2026-08-22. It's a chat/IM-first competitor to Claude Code: multi-agent orchestration ("Agent Cluster Mode", S1→S5 pipeline), browser automation, IM bot channels (Lark/WeChat/QQ), cron, self-evolving skill generation, its own MCP server, and integrations including 1Password and a legal-mode persona.

Config (`~/.openclaw-autoclaw/openclaw.json`) showed `tools.exec: {security: "full", ask: "off"}` — commands execute without per-action confirmation — and contained a **live plaintext bearer JWT** for the user's account. Consulted zcode and agy (Gemini 3.1 Pro) for a security read on the non-secret parts of the install; both independently flagged the exec-without-confirmation setting and the app's ability to self-generate/load new skills/extensions as the two biggest concerns, given the app's access to sensitive integrations (1Password, identity folder).

This was a "what's running on my machine" audit, not a build/adopt decision — full findings in `ψ/learn/z-ai/autoclaw/`. No action taken; flagged to the user for their own call on whether AutoClaw should keep running with those settings.
