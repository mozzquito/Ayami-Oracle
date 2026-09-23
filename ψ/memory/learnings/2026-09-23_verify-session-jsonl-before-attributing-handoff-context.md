---
pattern: When multiple Claude Code sessions work in the same repo, verify a session's actual .jsonl before writing its retrospective — injected handoff/system context can belong to a sibling session, not the one you're in
date: 2026-09-23
source: rrr: ayami-oracle
concepts: [multi-session, maw, retrospective, verify-before-asserting, dig-miner]
---

# Verify session .jsonl before attributing handoff context to "this session"

In a repo where multiple Claude Code sessions can be active concurrently (this repo's
MAW multi-agent setup makes this routine, not exotic), a resumed session's system prompt
can carry a `SessionStart:resume` handoff describing work that actually belongs to a
**different**, sibling session — not the one currently running. The handoff/CLAUDE.md
context arrives looking like "this session's history," but it isn't necessarily.

**Why**: On 2026-09-23, session `2823d2fa` (whose real `.jsonl` history was just a single
LAN-IP-scan Q&A from 2026-08-26, nearly a month stale) resumed and received the same
`/rrr`-close command that a sibling session `3f12511d` had just closed with one minute
earlier. The resume hook's handoff text described `3f12511d`'s actual work (MPLS-from-VM
Q&A, PR #6, ai-live-poc) — content that read as plausible "recent work for this session"
given the conversational continuity, but belonged to the other session entirely. Writing
a retro that blended both would have fabricated a timeline.

**How to apply**: Before writing any `/rrr` retrospective — especially after a
`SessionStart:resume` — run the dig-miner (or at minimum grep the session's own
`.jsonl` by its `$CLAUDE_SESSION_ID`) and treat its output as ground truth for "what this
session actually did," even when it conflicts with what the handoff or surrounding
context implies. This is the same "verify before asserting" discipline already recorded
in `feedback_verify_before_asserting.md`, applied specifically to session attribution in
multi-session repos.
