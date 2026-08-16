---
pattern: Check whether a tool/integration actually supports the plan before offering it as an option to the user — verify capability, then propose, not the reverse
date: 2026-08-11
source: "rrr: ayami-oracle"
concepts: [tool-verification, google-sheets, mcp-limits, security-confirmation]
---

# Check tool capability before proposing a plan, not after

When a task spans multiple integrations (Chrome extension + Google Drive MCP), it's
tempting to propose "I'll just open the sheet and paste it for you" as the first option
because it sounds like the ideal outcome. But that phrasing implicitly promises a
capability that was never verified.

In this session: asked to import an xlsx into an *existing* Google Sheet at a specific
gid. Proposed two options to the user — (1) connect Chrome extension so I paste directly,
(2) create a new sheet for manual copy — before actually checking whether either path
was technically possible. Only after the user picked option 1 did `tabs_context_mcp`
reveal the Chrome extension wasn't connected, and only then did a tool search reveal the
Google Drive MCP has no `values.update`-style API for writing into an existing
spreadsheet (only `create_file`, `read_file_content`, `download_file_content`,
`copy_file` — all whole-file operations, not cell/range writes).

**Why**: In-place edits to a user's existing document depend on tool coverage that isn't
visible from the task description alone. Proposing a plan before confirming the
integration exists risks overpromising, then having to walk it back mid-task — costs
trust even when the fallback still ships something useful.

**How to apply**: Before presenting options that name a specific mechanism ("I'll open
the sheet and paste," "I'll call the API to update it directly"), do a quick capability
check first — `ToolSearch` for the relevant write API, or a lightweight connectivity
check (`tabs_context_mcp`) — *then* phrase the options around what's actually available.
If the check can't be done cheaply before asking, frame the option provisionally
("if X is connected, I can... — let me check") rather than presenting it as a done deal.

Related: this sits alongside [[feedback_verify_before_asserting]] — same root instinct
(verify before asserting), applied here to tool/environment capability rather than to
factual claims about code or data.
