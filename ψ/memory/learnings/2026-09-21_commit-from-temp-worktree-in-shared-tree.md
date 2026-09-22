---
pattern: When the working tree is shared with other live sessions and the current branch has diverged from origin, commit only the files you own from a temporary worktree cut from main — never switch branches in the shared tree, and never overwrite a shared "focus" file that belongs to another session.
date: 2026-09-21
source: rrr: ayami-oracle
concepts: [git, worktree, shared-working-tree, concurrent-sessions, commit-hygiene, focus-file]
---

# Commit from a temporary worktree when the tree is shared

## Situation (verified this session)
- Current branch `lab/jev-gate` had local-only commits diverged from origin (handoff: "do NOT git pull+push").
- Working tree had many unrelated uncommitted/untracked files, and `ψ/inbox/focus-agent-main.md` held another live session's state (eVisa n8n cleanup).
- Goal: commit two new files (`RUNBOOK.md`, `BRIEF.html`) without touching any of that.

## Pattern 1 — temporary worktree off main
```bash
git worktree add -b <new-branch> .tmp/wt-x main      # .tmp/ is gitignored
mkdir -p .tmp/wt-x/<dir> && cp <my files> .tmp/wt-x/<dir>/
git -C .tmp/wt-x add <dir> && git -C .tmp/wt-x commit ...
git worktree remove .tmp/wt-x                         # branch persists
```
Why not `git switch`: switching would remove tracked-on-this-branch files from disk (lab/jev-gate files vanish on main) and could collide with another session's uncommitted edits. Why not commit on the diverged branch: the new commit would ride on top of un-reconciled history.
Also: check `git check-ignore .tmp`, scan the two files for key-shaped strings, stage by explicit path (no `git add -A`), don't push.

## Pattern 2 — "overwrite" state files may belong to someone else
Repo rule says overwrite `focus-agent-main.md`, but the file contained a different session's task (README said "lines are other session uncommitted"). Overwriting would destroy that. Read it first; if it is another session's state, append to the activity log only and let the handoff skill own the focus file.

**How to apply**: any time `git status` shows lots of foreign changes or a warning about divergence, assume a shared tree. See also [[project_token_reduction]] for why long sessions get expensive.
