---
pattern: "Learned Excalidraw+ MCP: workspace-wide API key exposes 37 tools; create_diagram (semantic nodes/edges, auto layout) + take_screenshot is the reliable draw-and-verify loop"
date: 2026-09-21
source: learn: https://plus.excalidraw.com/docs (docs are index-level only; real detail came from calling the server)
concepts: ["learn", "excalidraw", "mcp", "diagram"]
---

# Learned Excalidraw+ MCP

- Two different servers: public `https://mcp.excalidraw.com/mcp` (no auth, render-only `create_view`, needs an MCP-Apps host to show) vs Excalidraw+ `https://api.excalidraw.com/api/v1/mcp` (Bearer API key, manages workspace/collections/scenes, public beta so tool names/schemas may change).
- The docs site is thin (`/docs`, `/docs/mcp`, `/docs/api` are landing-level). Ground truth: `tools/list`, `read_diagram_format`, and each tool's inputSchema.
- Loop that works: `create_collection_scene` (id is at `metadata.id`, not top-level) -> `create_diagram` (nodes: id/label/kind, edges: from/to/label/kind/startArrowhead) -> `take_screenshot` (returns PNG) -> `edit_scene_content` for tweaks.
- Server guidance: one dominant topology per diagram, backward edges rare, node label lines <30 chars, color edges by outcome (success/failure/info), avoid one big group boundary.
- Server is stateless HTTP/SSE: plain curl/urllib JSON-RPC works without a session id. A key added with `claude mcp add` only loads in tools after a session restart.
- Consult result (zcode + agy on the spec): both flagged the giant group and the double-incoming consult node; adopting both fixes made the layout clean. Both also suggested a Maintain->Requirement loop, declined because it breaks the single-topology rule.
- The key is workspace-scope (admin tools: users, invites, logs). Treat as high-privilege; it was pasted in chat, so revoke/rotate after testing.
