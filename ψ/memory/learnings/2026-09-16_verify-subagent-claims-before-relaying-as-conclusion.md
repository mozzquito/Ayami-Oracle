---
pattern: "When two delegated agents (e.g. zcode vs agy) disagree and one cites specific, checkable evidence (file contents, counts, code snippets), verify at least the decision-critical claims directly before relaying the conclusion to the user — confident, detailed-sounding output is not proof."
date: 2026-09-16
source: "rrr: ayami-oracle /learn Affitor/open-affiliate session"
concepts: ["verification", "subagent-delegation", "mcp-security", "zcode", "agy"]
---

# Verify subagent claims before relaying as conclusion

zcode and agy gave opposing recommendations on whether to install an MCP server
(`openaffiliate-mcp`): zcode checked npm/GitHub metadata only and said "cautious
yes"; agy claimed to have read the actual MCP server source and sample data and
said "pass," citing specific file contents (a YAML entry, a proxy-fetch call, a
verified-count).

Before repeating agy's conclusion to the user as fact, the decision-critical
claims were checked directly against the already-cloned repo: read
`packages/mcp/src/index.ts` to confirm it really is a remote `fetch()` proxy
(not local), counted `verified: true` occurrences in `programs/*.yaml` (49/760,
matching agy's figure), and read `programs/cursor.yaml` to confirm the
`agents.prompt` field exists and reads as a direct instruction to an AI agent.
All three held up — but the check took under a minute and would have caught it
if they hadn't.

**Rule**: A subagent or delegated CLI agent (zcode, agy, grok, or a Task
subagent) that reports specific evidence — code snippets, exact counts, "I
opened X and saw Y" — should have its 1-3 most decision-critical claims spot
verified independently when the answer will be relayed as a recommendation,
especially when two sources disagree. This matters more, not less, when the
report sounds confident and detailed, since detail is not evidence the agent
actually did what it claims. See also [[feedback_verify_before_asserting]].
