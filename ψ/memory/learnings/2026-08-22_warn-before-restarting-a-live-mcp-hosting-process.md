---
pattern: "Restarting/killing a process that hosts a live HTTP MCP endpoint drops every session connected to it — including the host app's own internal self-connections — and this should be flagged up front, not discovered reactively"
date: 2026-08-22
source: "rrr: ayami-oracle"
concepts: ["mcp", "session-management", "autoclaw", "restart", "operational-caution"]
---

# Warn before restarting a live MCP-hosting process

Session-based HTTP MCP transports (the kind `claude mcp add --transport http` registers)
negotiate a session ID with the server on connect. Restarting the server process — even
gracefully — invalidates that session; the client (Claude Code, or any other consumer)
has to reconnect (`/mcp` → reconnect) before tool calls work again. `claude mcp list`
showing "✔ Connected" only checks that the HTTP endpoint answers, not that the negotiated
session is still valid — so it can lie about readiness right after a restart.

This session restarted AutoClaw (a desktop AI-agent app whose embedded gateway hosts
`autoclaw-productivity` on `127.0.0.1:19681/mcp`) to pick up a config change. The restart
broke **two** things, not one: this session's own MCP connection to that endpoint, *and*
AutoClaw's own internal agent's self-connections to its own MCP servers (`Autoclaw
Productivity`, `Autoclaw Github` — visible as "error" in AutoClaw's own MCP Servers page
afterward). Both were the identical stale-session failure mode, just on two different
clients hitting the same restarted server. Neither was flagged in advance — the user
discovered the first via a tool error, and the second via a confusing screenshot that
required log/runtime-json archaeology to explain after the fact.

The knowledge to predict this was already available beforehand (this is standard behavior
for session-based MCP HTTP transports) — the miss was not checking for it, it was not
saying it out loud before taking an action the user explicitly asked for.

**Applies broadly**: any time an agent is asked to restart/kill a process that hosts an
MCP server (or any stateful local service other tools are connected to), state the
expected fallout — "this will drop active sessions against it, reconnect via X after" —
as part of confirming the action, not as a retroactive explanation once something breaks.
