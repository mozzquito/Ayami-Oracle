---
pattern: "Before writing a closing retrospective or committing 'pending backlog', re-run git status even if it was checked minutes/turns ago — in a repo with concurrent Claude Code sessions, new legitimate backlog can appear in the gap, and only artifacts that self-report a closed-out state (STATE: completed, an explicit 'no open blockers' line) are safe to fold into someone else's closing commit"
date: 2026-09-06
source: "rrr: ayami-oracle open-threads-status-and-backlog-sweep"
concepts: ["git-status", "concurrent-sessions", "backlog-sweep", "rrr", "closing-a-session", "re-derive-dont-assume"]
---

# Re-check git status immediately before writing a closing retro, not just "recently"

This repo (`ayami-oracle`) runs multiple Claude Code sessions concurrently across sibling
projects. A session closing out with `rrr` had already committed its own pending backlog
one turn earlier, then re-ran `git status` right before writing the closing retrospective
(mostly as a formality) and found a second, unrelated backlog wave had appeared in the
interim — a different session's completed focus file plus a full retro+learning pair for
a shipped feature suite.

## Why this matters

- The gap between "I last checked" and "I'm about to act" is exactly where another
  concurrent session's finished work lands. Treating a recent check as still valid is the
  same mistake named in an earlier retro the same day
  (`2026-09-05_verify-doc-claims-and-recheck-state-before-acting-on-stale-pointers.md`) —
  it recurred within about 21 hours, meaning the lesson hadn't yet become a reflex.
- Folding another session's pending files into your own closing commit is fine, but only
  after verifying they explicitly self-report done-ness: a `STATE: completed` line in a
  focus file, or an explicit "no open blockers / all shipped and pushed" line in a retro's
  self-audit. A file that merely *looks* finished (no obvious placeholder text) is not the
  same bar — check for the explicit closed-out claim, not just the absence of red flags.

## How to apply

1. Immediately before writing any closing retrospective or "final" commit, re-run
   `git status` even if it was checked very recently in the same conversation.
2. For any unexpected new file discovered this way, open it and look for an explicit
   closed-out signal before committing it as part of your own session's backlog sweep.
3. If a file's state is ambiguous (no explicit completion signal, or looks mid-write),
   leave it uncommitted and mention it rather than guessing.
