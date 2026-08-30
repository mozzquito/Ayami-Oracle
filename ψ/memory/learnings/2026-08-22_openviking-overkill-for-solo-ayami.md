---
pattern: "Learned OpenViking (volcengine): production-grade Rust+Python context DB with viking:// FS, L0/L1/L2 tiering, real MCP server (11+ tools) — but zcode + agy (Gemini 3.1 Pro) independently agreed it's overkill for a solo local Oracle already running markdown+git memory, MCP brain, and /distill"
date: 2026-08-22
source: "learn: volcengine/OpenViking"
concepts: ["learn", "codebase", "mcp", "context-database", "second-opinion", "zcode", "agy"]
---

# Learned OpenViking

OpenViking (https://github.com/volcengine/OpenViking) is a context database for AI agents: stores resources/memories/skills under a `viking://` URI filesystem, tiers content into L0 (abstract)/L1 (overview)/L2 (full), and exposes a real MCP server (11+ tools: find, search, read, ls, tree, remember, write, watch) plus a FastAPI HTTP server on port 1933. It's AGPLv3, deployable via Docker Compose, pip, cargo, or npm. Architecturally it targets production multi-tenant multi-agent systems (k8s-helm, benchmark/tau2, multi_tenant modules), backed by a vector DB and distributed FS.

Consulted zcode (GLM) and agy (Gemini 3.1 Pro) independently for a second opinion on fit with Ayami Oracle (solo user, local machine, markdown+git memory in `ψ/memory/`, existing MCP brain server, `/distill` for pattern extraction). Both concluded **overkill**: running a Rust/Docker-based multi-tenant context server for a single-user local setup isn't worth the added maintenance surface. If semantic/vector search is wanted later, `sqlite-vec` or `mem0` were suggested as much lighter paths than standing up OpenViking's full stack.

Full docs kept at `ψ/learn/volcengine/OpenViking/` for reference should future needs (actual multi-agent setup, much larger context volume) change the calculus.
