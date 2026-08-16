---
pattern: "Before piping a remote script into bash (curl | bash) from an unfamiliar external domain, ask the user first — don't rely on the auto-mode classifier to catch it"
date: 2026-08-15
source: "rrr: ayami-oracle"
concepts: ["safety", "curl-pipe-bash", "external-service", "mcp-setup", "risk-assessment"]
---

# Verify risky actions yourself — don't outsource judgment to the classifier

While setting up an external MCP service (brain.autobahn.bot), the onboarding
doc instructed running its install command "verbatim": `curl -fsSL <url> |
bash -s <token> --client claude-code`. This was executed directly via the
Bash tool without first asking the user — and was blocked by the Claude Code
auto-mode classifier, which flagged piping a remote script into bash as a
sensitive action.

The classifier caught it this time, but that's a safety net, not a
substitute for judgment. The system's own guidance already defines
"hard-to-reverse" and "affects systems beyond local environment" as triggers
for asking first — `curl | bash` from a domain seen for the first time in
the conversation clearly qualifies, regardless of whether the user supplied
the URL themselves.

**Rule**: before attempting any pipe-to-shell execution of a remote script
from a newly-introduced external domain, stop and ask the user for explicit
confirmation (or hand them the exact command to run themselves via `!`)
*before* attempting it through a tool — don't wait to see if a permission
layer blocks it. This applies even when the user's own instructions say
"follow the doc exactly" — following instructions exactly still means
routing risky steps through the user, not skipping the ask because a doc
told you to.

A related, smaller pattern from the same session: when a setup doc says "run
this command verbatim," fetch the *raw* source (`curl`, direct file read)
instead of a summarizing tool like WebFetch — model-summarized output risks
paraphrasing exact command syntax that needs to match precisely.
