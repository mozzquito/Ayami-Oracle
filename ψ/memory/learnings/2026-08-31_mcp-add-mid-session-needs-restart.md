---
pattern: claude mcp add mid-session doesn't appear in /mcp until Claude Code restarts — warn the user proactively, don't wait for them to hit the gap
date: 2026-08-31
source: rrr: ayami-oracle
concepts: [mcp, claude-code, session-lifecycle, cloudflare]
---

# `claude mcp add` mid-session needs a restart before `/mcp` sees it

When you run `claude mcp add ...` via Bash *while* an interactive Claude Code
session is already open, the new server is written correctly to config
(`~/.claude.json` for user scope) and shows up immediately if you re-run
`claude mcp list` from a fresh Bash invocation — but the **running session's
own `/mcp` menu was loaded at session start** and does not pick up servers
added after that point. The user will see "mcp ไม่มี <name>" even though the
config is completely correct.

**Fix**: after adding an MCP server mid-session, tell the user immediately —
in the same message that reports success — that they need to fully restart
Claude Code (not just re-run `/mcp`) before the new server appears and can be
authenticated. Don't wait for them to discover the gap and report confusion
back to you.

**Generalizes to**: any Claude Code config surface that's loaded once at
session start (MCP servers, likely also plugin/skill registration) — verify
whether an action taken mid-session is live-reloaded or requires a restart
before promising the user it'll "just work" on their next `/command`.

Verified in this session: added `cloudflare-bindings` and
`cloudflare-containers` via `claude mcp add --transport http ... -s user`,
confirmed present via a separate `claude mcp list` Bash call and in
`~/.claude.json` directly, but the live session's `/mcp` menu didn't list
either until the user was told to restart.
