---
pattern: "Learned maw-js: distributed multi-agent orchestration CLI (tmux state machine + fleet registry + pluggable transport). Already installed on this machine at v26.5.21, matching latest release — the same tool CLAUDE.md's maw peek/sync/hey commands target."
date: 2026-08-13
source: "learn: Soul-Brews-Studio/maw-js"
concepts: ["learn", "codebase", "maw", "tmux", "multi-agent", "bun", "orchestration"]
---

# Learned maw-js

- **MawEngine** is a real-time tmux state machine (50ms capture loop) driving a **Fleet** registry: Oracles (persistent nodes) + Agents (ephemeral tmux sessions), with local scanning plus HTTP/MQTT federation (HMAC-signed, TOFU key pinning).
- Architecture is fully plugin-based — 95 plugins across core/standard/extra tiers, auto-discovered from `~/.maw/plugins/`. Bun + TypeScript runtime, Elysia server, React 19 + Zustand + xterm.js + Three.js web UI (`maw ui`). CalVer versioning (`v{yy}.{m}.{d}[-alpha.{HHMM}]`).
- Verified already installed and current on this machine (`maw v26.5.21` @ `~/.bun/bin/maw`, matches latest GitHub release tag, `maw health` all green) — no install step was needed when asked to "install" it.
