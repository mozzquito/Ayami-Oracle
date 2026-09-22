---
pattern: gh pr list / gh issue list silently resolves to the wrong remote when a repo has both origin and upstream configured — always check git remote -v before trusting their output for a cleanup/handoff plan
date: 2026-09-22
source: rrr: ayami-oracle
concepts: [gh-cli, git-remotes, verify-before-asserting, forward-skill]
---

# gh defaults to the wrong remote in a multi-remote repo

`ayami-oracle` has `origin` (mozzquito/Ayami-Oracle) and `upstream`
(Soul-Brews-Studio/arra-oracle-v3). Running `gh pr list --state open` and
`gh issue list --state open` during `/forward`'s cleanup-context gathering
returned PRs/issues (#3056, #3060, etc.) belonging entirely to `upstream` —
titles about vec0 extensions and other Oracle awakenings, nothing to do with
this repo's actual work. `gh` picked a remote silently, no warning that it
wasn't `origin`.

Caught only because the titles looked obviously wrong for this project. Had I
not sanity-checked, the handoff plan would have told a future session to go
"clean up" someone else's unrelated PRs in a shared upstream project.

**Rule**: before writing `gh pr list`/`gh issue list` output into any
cleanup checklist, plan, or handoff that a future session will act on without
re-verifying, run `git remote -v` (or `gh repo view`) first to confirm which
remote `gh` is actually targeting. This applies to any repo with more than one
remote configured — forked/upstream setups, not just this one.

See [[project_evisa_ticket_flow]] for another instance of the general
"verify before asserting" pattern in this project.
