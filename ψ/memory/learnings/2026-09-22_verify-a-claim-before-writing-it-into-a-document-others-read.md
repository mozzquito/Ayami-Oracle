---
pattern: "Verify a claim before writing it into a document someone else will read (PR body, handoff) — inference is not verification, even when it sounds obviously right"
date: 2026-09-22
source: "rrr: ayami-oracle (lab/jev-gate cleanup: PR #3 merge, PR #4 open, Grok Bot hook proof)"
concepts: [verify-before-asserting, pr-description, git-merge, overconfidence]
---

# Verify before writing a claim into a document, not just before speaking it

## What happened

Opened PR #4 for `lab/jev-gate` → `main`. Four of its commits were the same patches already merged to `main` via PR #3 (different hashes, since they'd been cherry-picked onto a separate branch). Wrote in the PR description: "should merge as no-ops" — a reasonable-sounding inference, never tested.

GitHub reported a real conflict (`CONFLICTING`/`DIRTY`) in `.claude/settings.json`: both branches had added different hook entries to the same JSON block. Had to resolve it in a disposable git worktree and then go back and correct the already-published PR body.

## Why this matters beyond this session

`[[feedback-verify-before-asserting]]` already covers verifying claims before *stating* them to the user. This is the same failure in a colder, more expensive form: a PR body, a handoff, or a commit message is read later — possibly by someone else, possibly by a future session with no memory of how confident the claim actually was. A spoken guess gets corrected in the same breath if wrong; a written guess sits there looking authoritative until someone checks.

The check here was cheap and available the whole time: `git merge --no-commit --no-ff <other-branch>` in a scratch worktree, or even `git merge-tree`, costs one command and turns "should be a no-op" into a verified fact before it goes in the document.

## Rule

Before writing "X should work / should be a no-op / should merge cleanly" into a PR description, commit message, or handoff — run the check that would prove or disprove it, even if the inference feels obvious. If the check is one command away (a dry-run merge, a `--dry-run` flag, a syntax check), there is no excuse to skip it just because the artifact is "only a description."
