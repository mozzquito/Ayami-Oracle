---
pattern: "Background subagent/bash outputs are not durable across a session gap; don't poll harness-tracked background work with ScheduleWakeup"
date: 2026-09-13
source: "rrr: /learn stablyai/orca session, resumed after ~3.5-week dormant gap"
concepts: ["learn", "background-agents", "scheduleWakeup", "session-resume", "durability"]
---

# Background work durability and the polling anti-pattern

During a `/learn` run on `stablyai/orca`, the session went dormant for ~3.5 weeks between
kicking off background work and it completing. On resume, three things were true at once:

1. **Haiku subagents that write directly to a file survive** — even though their task
   notification reported "killed"/"stopped" (because the process exited before the
   notification could be delivered), the actual `Write` calls they made to the vault had
   already landed on disk and were intact. Don't trust a "killed" notification as proof of
   lost work — check the filesystem artifact before deciding to redo it.

2. **Backgrounded external CLI delegations (zcode/agy via `Bash run_in_background`) are not
   durable** — their result lives only in the scratchpad output file and/or gets echoed into
   the conversation transcript. If the session ends (or the scratchpad gets cleaned) before
   that output is captured into a durable file, it's gone. In this session, `agy`'s output
   survived only because it happened to print inline before the gap; `zcode`'s did not survive
   at all. **How to apply**: for any user-requested delegation to zcode/agy/grok whose result
   matters, write the result to a durable file (vault, docs dir) as soon as it returns, rather
   than treating "it's in the conversation" as sufficient.

3. **`ScheduleWakeup` should never be used to poll work the harness already tracks**
   (`Bash run_in_background`, `Agent`) — the completion notification fires automatically.
   Scheduling a short-interval wakeup "just to check" on that same tracked work is redundant
   by construction and was explicitly flagged as an anti-pattern in the tool's own guidance.
   **How to apply**: after starting a `run_in_background` Bash call or an async `Agent` call,
   just stop and wait — no wakeup needed unless there's a *separate*, harness-invisible thing
   to wait on (e.g. an external API polling loop).
