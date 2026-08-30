---
pattern: pre-fetch npx-based MCP server packages before running claude mcp list health-check
date: 2026-08-30
source: rrr: ayami-oracle
concepts: [mcp, npx, claude-code-cli, cold-start, health-check]
---

# Pre-fetch npx MCP packages before health-checking

When adding a new stdio MCP server via `claude mcp add name -- npx -y <pkg>@latest`,
the first `claude mcp list` right after almost always fails with a connection timeout
(observed: 30s timeout) if the npm package has never been downloaded/cached on this
machine before. This looks like a config or server problem but isn't — it's just npm
fetching the package tree (deps, dedup, etc.) on first run, which routinely exceeds the
health-check timeout.

**Fix**: run the package directly once before the health check, e.g.
`npx -y <pkg>@latest --version` (or any no-op invocation), to force npm to
download and cache it. Then `claude mcp add` + `claude mcp list` connects immediately.

**How to apply**: any time you install a new npx-based MCP server for the first time on
a machine, pre-fetch first, health-check second — don't diagnose a timeout as a config
bug until you've ruled out cold-start.

Also noted in the same session: macOS's default shell has no `timeout` command (it's
GNU coreutils, not BSD default) — use the Bash tool's own `timeout` parameter, or
`gtimeout` if coreutils is installed via brew, rather than assuming `timeout <n> <cmd>` works.
