---
pattern: "Learned video-db/call.md: Electron+tRPC+Drizzle meeting-recorder app; MCP auto-trigger loop maps OpenAI's 32-char tool-name limit back to real MCP tool refs via a Map; AI outputs stored as JSON columns rather than normalized tables"
date: 2026-08-10
source: "learn: video-db/call.md"
concepts: ["learn", "codebase", "electron", "mcp", "trpc", "drizzle", "videodb"]
---

# Learned call.md

- Desktop app (Electron + React 19 + tRPC/Hono + Drizzle/SQLite) that records meetings,
  transcribes dual-channel via VideoDB, and runs live AI copilot features (assists,
  coaching nudges, MCP tool auto-triggering) during the call.
- The MCP agent service (`src/main/services/mcp/mcp-agent.service.ts`) is the most
  interesting piece: it listens to the live transcript, decides when to call a connected
  MCP tool via LLM function-calling, and works around OpenAI's 32-char function-name cap
  by generating short synthetic names and mapping them back to `{serverId, toolName}` in
  a `Map` — a pattern worth reusing anywhere multiple tool sources need flattening into
  one function-calling namespace.
- Installed locally via developer setup (`npm install` + `npm run rebuild` for
  better-sqlite3 native bindings) at `~/ghq/github.com/video-db/call.md`; `npm run dev`
  left for the user to run interactively (needs GUI permission grants + VideoDB API key).
