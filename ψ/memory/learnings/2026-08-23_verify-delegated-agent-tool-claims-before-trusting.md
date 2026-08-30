---
pattern: "When a delegated second-opinion agent (zcode, agy, or any sibling CLI) claims a specific external tool/library/repo exists as grounds to simplify a design, verify independently (WebSearch/WebFetch) before trusting it — especially if the agent flags its own uncertainty mid-answer."
date: 2026-08-23
source: "rrr: ayami-oracle — self-hosted AutoClaw-replacement design session (2026-08-22)"
concepts: ["zcode", "agy", "second-opinion", "verify-before-asserting", "mcp", "design-review"]
---

# Verify a delegated agent's concrete tool/repo claims before trusting them

During a design-review consult (asking zcode + agy to poke holes in a proposed self-hosted
Gmail/Calendar/Drive connector + cron system), zcode's punch list included a claim that several
existing open-source MCP servers already covered the need — one linked repo it even flagged
itself as "no, wrong one" mid-answer. Rather than relay that claim as-is or simply discard the
suggestion, an independent WebSearch + WebFetch pass was run to check what actually exists.

That verification pass surfaced something neither zcode nor agy knew about: Google now hosts
**official remote MCP servers** for Gmail, Calendar, and Drive (`gmailmcp.googleapis.com` etc.),
and Claude Code's own CLI already supports registering exactly this kind of OAuth-gated remote
HTTP MCP server (`claude mcp add --transport http ... --client-id ... --client-secret -s user`).
This collapsed the entire proposed design — no custom OAuth server, no custom MCP server code,
no token storage/refresh logic needed at all, since Claude Code manages the OAuth credentials
internally once a server is registered.

**Why**: A delegated CLI agent's "second opinion" is valuable for spotting gaps and risks, but its
claims about *specific* external resources (a named repo, a named library, "this already exists")
carry the same hallucination risk as any single LLM's knowledge — arguably higher, since the agent
is reasoning without live web access. Trusting an unverified claim either way (accepting it at
face value, or dismissing the whole suggestion because one instance of it looked wrong) forfeits
the chance to find the actually-correct answer, which in this case was a materially better
solution than anything either sibling agent proposed.

**How to apply**: When a zcode/agy/sibling-CLI review names a concrete tool, library, or repo as
a reason to change direction, treat that as a lead worth checking, not a fact to relay or an idea
to write off. Run one WebSearch/WebFetch pass to confirm before it shapes an architecture
decision — the cost is a couple of tool calls; the payoff can be avoiding weeks of building
something that already exists in a better, more authoritative form.
