---
pattern: Verify git state (git log/status) before claiming a commit/push happened, especially after any interruption near a write step
date: 2026-08-08
source: "rrr: my-first-oracle"
concepts: ["git", "verification", "interruption-handling", "auto-mode-permissions", "askuserquestion"]
---

# Verify git state before claiming "done" — don't reconstruct from intent

## What happened

During Ayami Oracle's awakening session, a `[Request interrupted by user]` landed at almost the exact moment `git commit` was about to run — right after `git add`. Everything that followed (closing/redirecting a GitHub issue, repointing `git remote`, running `git push`) proceeded on the unverified assumption that the commit existed. The end-of-turn summary told the user "committed and pushed" — which was false. The gap was only caught because `/rrr`'s own git-context step (`git log --oneline -10`) ran and showed the old pre-session commit still at HEAD.

## The pattern

1. **Never state a git operation is complete without checking.** `git log -1` / `git status --short` are cheap. Run them before any user-facing claim like "committed", "pushed", "merged" — not just at natural checkpoints, but specifically after any interruption that happened near a planned write operation.
2. **An interruption near a write step is a signal, not noise.** Treat `[Request interrupted by user]` as a cue to re-verify state before continuing the plan, not just resume where you think you left off.
3. **User confirmation via a question tool doesn't transitively authorize the underlying tool call.** In this session the user answered "yes, push it" through AskUserQuestion, but the actual `git remote set-url` + `git push` still hit a separate auto-mode permission classifier and got blocked, requiring an explicit second approval. Two different gates — don't assume one satisfies the other for consequential git/network actions.
4. **AskUserQuestion needs ≥2 concrete, mutually exclusive options — it cannot collect open-ended freetext.** For wizard-style "tell me about yourself" phases, use plain text output and wait for the reply; reserve AskUserQuestion for genuine forks in the road.

## Why this generalizes

Any workflow that chains "ask → act → summarize" across multiple turns is vulnerable to this exact gap when an interruption falls between the "act" and "summarize" steps. The fix isn't "be more careful" — it's a structural habit: verify observable state (git log, file existence, API response) immediately before any claim of completion, every time, regardless of how confident the intent was.
