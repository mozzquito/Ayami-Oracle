---
pattern: "A design doc's claim of having 'verified' or 'confirmed' something against a real source is a claim, not a substitute for checking it yourself; and a 'pending task' pointer (focus file, task list) can go stale between when it was written and when you act on it, especially when other concurrent sessions can complete the same work"
date: 2026-09-05
source: "rrr: ayami-oracle"
concepts: ["verification", "concurrent-sessions", "stale-state", "session-resume"]
---

# Verify doc claims yourself; re-check state before acting on a stale pointer

Resumed a session after a month-long real-world gap. A stale focus file (`ψ/inbox/focus-agent-agy.md`) pointed at an unreviewed diff ("Feature 2 Import & Batch-Process Existing Recordings" in a `call.md` fork). Independently reviewed the diff, including spot-checking the design doc's claim that VideoDB SDK field names (`filePath`, `length`) were "confirmed against the installed package's actual `.d.ts`" — grepped the real `node_modules/videodb/dist/**/*.d.ts` files directly rather than trusting the doc's narrative. They matched, but the check was still worth doing: the doc's confident, specific-sounding claim was not itself evidence.

Mid-review, discovered the diff had already been committed by a **different, concurrent Claude Code session** (same git author/human, different `Claude-Session` URL) — the focus file's "pending" state was stale by the time this session acted on it, not from a human edit but from another agent session completing the work in the real-time gap between when the pointer was written and when it was read.

**Rules**:
1. A verification claim in a doc ("confirmed against X") should be spot-checked against the live source when you're the one relying on it for a decision, not accepted because it reads as specific and confident.
2. Before acting on any "pending task" pointer (a focus file, a task list, a TODO), re-check actual current state (git log, git status, the file itself) immediately beforehand — the pointer can be stale not just from time passing, but from a concurrent session finishing the same work since it was written.
3. After a long idle gap in a resumed session, treat all held context as expired by default and re-derive current state from files rather than extrapolating from what you last observed.
