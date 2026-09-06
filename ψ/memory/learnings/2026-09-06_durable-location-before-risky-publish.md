---
pattern: "Save a deliverable's source of truth to a durable location before attempting a step that might fail or be blocked (external publish, permission-gated action) — never let a scratchpad copy be the only copy"
date: 2026-09-06
source: "rrr: ayami-oracle (session 450dbd0e, memory-horizon manual + Artifact block)"
concepts: ["durability", "artifact-publishing", "session-scratchpad", "cron-verification", "browser-extension-reliability"]
---

# Durable location before risky publish

## What happened

A carefully designed HTML page (real color/type tokens, both themes, real content) was built
directly in the session's scratchpad directory, with the `Artifact` publish call as the next
step. The publish was blocked by Claude Code's own safety classifier (the page was dense with
real session IDs and conversation excerpts — a legitimate block, not a bug). Two days later, in a
new session, the user asked where the manual was — the scratchpad directory had already been
cleaned up, so the only copy of the finished design work was gone. It had to be rebuilt from
scratch.

**Rule**: before attempting any step with a real chance of failing or being refused (an external
publish, a permission-gated action, a network call to a service that might reject the content),
put the deliverable's actual source file in a durable, project-owned location first (e.g.
`ψ/incubate/`), and treat the risky step as reading *from* that location — never as the only path
that makes the work durable. If the risky step fails, the work should still exist afterward with
zero extra effort.

## A smaller, related miss in the same session

A user request bundled two independently-checkable asks in one sentence: "set up a cron to update
X every Friday at 12:00." Only one was verified (the automation exists) — the schedule time was
never actually checked (the plist still said 12:40, two days later), because editing the cron
*script's* contents felt like it satisfied the whole request, when the *schedule* lived in a
different file entirely.

**Rule**: when a request bundles multiple factual claims into one instruction, verify each fact
independently before considering the request done — don't let visible progress on one part stand
in as evidence for an untouched adjacent part.

## Also observed (not this session's fix to make, but worth flagging on sight)

The `claude-in-chrome` browser extension failed to connect or reach `localhost` on at least 3
separate occasions across this multi-day span (once due to an active VPN, twice via outright
disconnection). Every single time, the actual unblock was "the user opened the URL in their own
browser." Once a tool has failed this many times in the same environment, default straight to
asking the user to do the browser step themselves rather than re-attempting the automated path
first.
