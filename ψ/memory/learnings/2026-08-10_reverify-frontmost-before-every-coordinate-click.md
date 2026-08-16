---
pattern: When a UI-automation technique is risky enough that the safety classifier gates it, re-verify its precondition before every single use for the rest of the session, not just once at approval time
date: 2026-08-10
source: rrr: ayami-oracle
concepts: [macos, accessibility, coordinate-click, system-events, safety-classifier, focus-verification, line]
---

# Re-verify frontmost before every coordinate click, not just the first one

## Context

Building a multi-room LINE chat scraper (`ψ/lab/line-check/check-line-all.sh`). AX's structured `click row N of list` action turned out not to register on LINE for Mac's custom-drawn rows (confirmed empirically: a live 10-room run produced identical content for every room, because the "click" never actually switched conversations). The fix was a raw coordinate-based `click at {x,y}` via System Events — which Claude Code's own auto-mode safety classifier blocked outright on first attempt, requiring explicit user approval to proceed.

## What happened

After getting approval and successfully testing one coordinate click (with `set frontmost to true` immediately before it), a later click in the same session was fired *without* that frontmost check. In the time between commands, the user had switched focus back to their terminal (Ghostty — the very session running this automation). The click landed on Ghostty instead of LINE and visibly changed the user's active terminal tab. Caught immediately via the next screenshot, disclosed plainly, user confirmed no real damage — but the mistake was real and avoidable.

## The core mistake

Getting explicit user approval for a risky technique was treated as a **one-time permission checkpoint** ("I'm now allowed to do this") rather than a **standing risk signal** ("this technique can hit the wrong target if a precondition isn't re-checked every time"). The classifier's block wasn't arbitrary — raw coordinate clicks aren't scoped to a known UI element, so they execute against whatever is actually on screen at that pixel, regardless of which process you *intended* to target. That risk doesn't go away after approval; it's inherent to the technique and must be mitigated on every single invocation.

Compounding factor: this is an async/background-job context where the human can switch windows (e.g., to read the AI's last message, or reply from a different app) between one automated step and the next. Focus state cannot be assumed stable across even a few seconds.

## Rule for next time

- When a UI-automation technique is powerful/risky enough that Claude Code's own classifier gates it, build its precondition check (e.g., "frontmost app name == target app") into a hard guard on *every* subsequent call for the rest of the session — not just the first one after approval.
- Never assume window/focus state persists between commands in an async or background-job context, even seconds apart. Re-query, don't cache.
- Prefer the least-scoped-risk technique that still works: AX-scoped actions (`click row N of list`) fail loudly/safely (wrong element or no-op) when the UI doesn't cooperate; raw coordinate clicks fail *silently and dangerously* (hit whatever's actually there) if the frontmost assumption is stale. Only drop to coordinate-based clicks when the AX-scoped action is confirmed not to work, and wrap every use in the same precondition check.
- A dry-run/detection test does not validate a mutating action. Before running a multi-step automation loop live, smoke-test the single riskiest primitive (e.g., "does this click actually switch state?") in isolation first.
