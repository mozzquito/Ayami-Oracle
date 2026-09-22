---
pattern: A "push it" approval covers the state you were shown, not the branch tip at push time; on a shared branch and a public remote, list `origin..HEAD` right before pushing, and when it holds commits you did not make (or any marked local-only), push only your own commits from a temp branch cut from origin. Also never mutation-test a file that a live process executes: mutate a copy.
date: 2026-09-21
source: rrr: ayami-oracle
concepts: [git, push, public-repo, concurrent-sessions, authorization, mutation-testing, live-script]
---

# Re-list what is about to be pushed; mutate copies, not live files

## Situation (verified this session)
- มอส said "push ได้เลย" while `lab/jev-gate` held 4 known local-only commits. By the time I ran the check, `git log origin/lab/jev-gate..HEAD` showed 7-8 commits: another live session had added `7d40feb7` ("eVisa/Wayama retros ... internal IPs (local only) ... do not push this commit without reviewing it first"). Origin `mozzquito/Ayami-Oracle` is PUBLIC (`gh repo view mozzquito/Ayami-Oracle`; a bare `gh repo view` resolved to a different repo, arra-oracle-v3, so ask gh for the repo explicitly).
- Fix that worked: ask มอส (he picked "only statusline"), `git worktree add -b lab/statusline-v2 .tmp/wt-statusline origin/lab/jev-gate`, `git -C` cherry-pick the 3 own commits, run the tests on that clean branch (209/209), push the new branch, remove the worktree. No force, remote `lab/jev-gate` untouched. Related: [[2026-09-21_commit-from-temp-worktree-in-shared-tree]].
- Separate slip: to mutation-test the new tests I edited `.claude/scripts/statusline-ayami.sh` in place. That file is the live `statusLine` command that every Claude Code session in this repo executes, and the run was pushed to the background by the 120 s tool timeout, so the mutated script stayed in place for several minutes. The tests could not take a script path (`SCRIPT` is hard-coded), which is why I mutated the original.

## Rules
1. Approval is bound to what the user saw. Before any push to a shared/public remote, print `git log --format='%h %an %s' origin/<branch>..HEAD` and `git diff --stat`. Any commit you did not make, any "local only"/"do not push" marker, any sensitive word => stop and either ask or push a temp branch with just your own commits. Never "fix" it with `--force` or by rewriting the shared branch.
2. A repo's visibility is a fact to look up, not to remember: ask for it by name (`gh repo view OWNER/REPO`), because default repo resolution can point at a different remote.
3. Never edit a file in place to mutation-test it if something else executes it (statusline, hooks, cron scripts). Run the suite against a copy through an env override, and if the tool timeout can background your run, the original must never be the one being mutated.

## How to apply
- For scripts with tests, make the script path overridable (`SCRIPT="${STATUSLINE_SCRIPT:-...}"`) so mutation runs use a copy. (Not done yet for `ψ/lab/statusline/test_statusline.sh`.)
- After any temporary mutation, `cmp` the file against a backup before doing anything else, as was done here.
