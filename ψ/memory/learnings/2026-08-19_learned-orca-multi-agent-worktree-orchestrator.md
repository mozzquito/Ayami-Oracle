---
pattern: "Learned stablyai/orca: multi-CLI-agent orchestrator built on real git worktrees + PTY-per-agent + observation-only hooks, not agent control"
date: 2026-08-19
source: "learn: stablyai/orca"
concepts: ["learn", "codebase", "electron", "multi-agent", "git-worktree", "pty"]
---

# Learned stablyai/orca

Orca is an Electron desktop app that runs multiple AI coding-agent CLIs (Claude Code, Codex, OpenCode, Pi, Grok, Cursor, etc.) side by side, each in a real, isolated `git worktree` with its own `node-pty` process.

Key insights:
- **Observe, don't wrap**: Orca injects HTTP hooks + parses terminal OSC codes to track agent status (idle/working/waiting/subagent), but the agent CLI runs as a real, unmodified process — Orca never intercepts or controls its execution. Useful reference pattern for building any "dashboard over N parallel coding agents" tool.
- **4 separate comms channels** for a desktop-app-with-CLI-and-mobile-companion shape: Electron IPC (renderer↔main), Runtime RPC (unix socket / E2EE WebSocket for CLI+mobile+remote clients), Agent Hook HTTP (fail-open, token-auth'd loopback server), Desktop Relay (SSH-based federation between Orca instances).
- **PTY persistence across restarts**: a forked background daemon owns the PTY processes so terminal sessions/scrollback survive Electron renderer reload or app restart — the daemon, not the window, owns process lifetime.

Also: zcode (GLM/z.ai `glm-5-turbo`) hit a persistent `524 Origin Time-out` on this task on two separate attempts (different sessions, same day) — worth checking z.ai status before relying on zcode for anything time-sensitive; agy (Gemini backend) completed the same task without issue both times.
