---
pattern: an async relay/bridge tool's reported status is not ground truth — when a human-visible channel contradicts it, go to the underlying data store, not more polling
date: 2026-09-11
source: rrr: ayami-oracle
concepts: [mcp-bridge, verification, async-correlation, trust-but-verify, grokbot]
---

# A relay tool's status field can lie by omission — verify against the real data store when it's contradicted

## What happened

Built a new agent via `grokbot-bridge` (a custom MCP server that relays messages to Grok Bot's
native chat), sent it a test prompt, and polled `grokbot_verify` for the reply. It reported
`status: reply_pending` / `reply: null` for over four minutes of polling. The user then sent a
screenshot showing Grok Bot had replied correctly within about a minute of the message being sent.

Root-caused it by SSHing into the box and querying the actual SQLite transcript directly
(`~/sand-data/agents/<id>/store.db`, table `transcript_entries`). Found the real bug in
`scripts/grokbot-gateway.py`'s `inspect_rows()`: it requires the *prompt row* to carry a non-null
`requestId` before it will even attempt to correlate a reply —

```python
rid = prompt.get("requestId")
for rowid, e in decoded:
    if rowid <= seq or not rid or e.get("requestId") != rid:
        continue
```

— but real `kind=message` transcript rows (both `role=user` and `role=assistant`) never carry a
`requestId` in practice; only `kind=send-message` rows do. Confirmed this against a second,
long-lived agent's real 46-row transcript, not just by reading the code. So `reply_pending` was
not "still waiting" — it was mathematically unable to ever resolve for a normal conversation.

## Why this matters

A first pass of code-reading produced a *plausible* theory (fragile exact-string content
matching) that turned out to be a red herring — the real bug was one field-name assumption away
from that. The theory would have been reported with confidence if the user's screenshot hadn't
forced a re-check. **Code-reading alone produces a hypothesis, not a verified root cause** — this
is the same "verify before asserting" pattern from `feedback_verify_before_asserting.md`, but
applied specifically to *tooling I built or maintain*, not just to external claims.

## How to apply

- When a relay/bridge/async tool reports a "still pending" or "no result yet" status, treat it as
  **unverified**, not as **false** — but don't let it sit unquestioned indefinitely either.
- If any human-visible channel (a screenshot, a live UI, a log a person can read) contradicts the
  tool's reported state, stop polling the tool and go straight to the underlying data source the
  tool is supposed to be reading from. The tool's own abstraction is exactly what's suspect at
  that point.
- When the underlying store is a database you can reach (SSH + read-only SQLite connection here),
  querying it directly is usually faster and far more conclusive than more rounds of polling a
  tool that has already been shown unreliable once.
- A code-read hypothesis for *why* something fails is a starting point, not the deliverable —
  confirm it against real data before reporting it as the cause, especially for your own project's
  code (this repo's `omx-grokbot`), where the temptation to trust your own prior design is highest.
