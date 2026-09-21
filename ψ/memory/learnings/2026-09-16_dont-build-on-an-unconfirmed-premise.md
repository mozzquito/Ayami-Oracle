---
pattern: When a recommendation depends on a premise the user didn't confirm, don't let follow-up questions proceed as if it were settled — re-surface it instead
date: 2026-09-16
source: "rrr: ayami-oracle (evisa/Wayama session)"
concepts: [advisory, unconfirmed-assumption, follow-up-questions]
---

# Don't build on an unconfirmed premise just because the conversation moved on

## What happened

มอส asked whether introducing n8n (workflow automation) would help the eVisa report-automation
work. The honest answer depended on one real variable: whether more report-automation workflows
were actually planned beyond the three just shipped — n8n's operational overhead (a new VM to
maintain) is only worth it at some scale. I asked this once, in the first response, framed as
"depends on whether you're scaling up." มอส didn't answer it — he moved straight to asking about
disk sizing, then OS, then closed the thread. I answered both follow-ups fully, on the implicit
assumption that "yes, scaling up" was true, without re-flagging that the premise itself was still
open.

## The pattern to avoid

Once a user's follow-up questions accept a recommendation's premise implicitly (by asking
"how big" instead of "should we"), it's easy to treat the premise as settled and just answer the
narrower question in front of you. But the user moving on isn't the same as the user confirming —
they may simply be provisioning for a decision they haven't actually made yet, or be answering the
easier question first. The unconfirmed premise doesn't go away; it just stops being visible in the
conversation's surface-level flow.

## What to do instead

- If a recommendation was conditioned on something the user didn't answer, and they proceed to a
  narrower follow-up anyway, either answer the follow-up **and** re-flag the open premise in the
  same reply, or note explicitly that the answer assumes the premise holds.
- Track which of your own open questions went unanswered across a conversation — don't let asking
  once count as "handled" if the answer never actually came.

## Why this matters beyond this one case

This generalizes the "re-surface a deferred item, don't let it silently close" lesson from a prior
session to a tighter case: it's not just about items the user explicitly paused ("พักไว้ก่อน") —
it applies just as much to premises baked into a recommendation that the conversation quietly
moved past without ever confirming.
