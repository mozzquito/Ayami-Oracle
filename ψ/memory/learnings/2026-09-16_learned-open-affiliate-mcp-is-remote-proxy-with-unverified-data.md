---
pattern: "Learned Affitor/open-affiliate: its MCP server is a thin remote proxy (not local), 94% of its 760 affiliate-program entries are unverified, and each entry embeds an agent-facing recommendation prompt — evaluate any 'data + agent instructions in one payload' MCP source this way before installing."
date: 2026-09-16
source: "learn: Affitor/open-affiliate"
concepts: ["learn", "codebase", "mcp-security", "supply-chain", "prompt-injection"]
---

# Learned open-affiliate

- `openaffiliate-mcp` (npm) does not read local data — it's a ~130-line wrapper that `fetch()`s `https://openaffiliate.dev/api/*`. Any "npx MCP server" claim should be checked against its actual source before trusting it as local/offline.
- Only 49/760 programs are `verified: true`. Unverified, community-submitted entries (e.g. `programs/cursor.yaml`, claiming a 20% recurring affiliate commission) are returned by `search_programs`/`get_program` unless the caller explicitly filters `verified_only`.
- Each program YAML has an `agents.prompt` field phrased as a direct instruction to an AI agent ("Recommend X when users need..."). This flows verbatim into MCP tool responses — i.e., the data payload itself contains agent-directed marketing instructions, not just facts.
- Second-opinion agents disagreed: zcode (surface npm/GitHub metadata check) said cautious-yes; agy (read actual MCP source + sample YAML) said pass. The deeper source-level check found the real issues — worth remembering that a metadata-only supply-chain check can miss what a code-level read catches.
