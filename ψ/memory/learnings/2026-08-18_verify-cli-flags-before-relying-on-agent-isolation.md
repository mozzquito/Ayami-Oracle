---
pattern: Before relying on a CLI flag to establish agent isolation (working directory, sandbox, permission scope), verify the flag actually does that by checking --help — a similarly-named flag on a sibling tool is not guaranteed to behave the same way.
date: 2026-08-18
source: "rrr: ayami-oracle"
concepts: [delegation, agent-isolation, verification, git-worktree]
---

# Verify CLI flags before relying on them for agent isolation

Set up two isolated git worktrees so zcode and agy could implement the same dashboard feature
in parallel without colliding. Passed `--cwd <worktree-path>` to zcode (correct — zcode has a
real `--cwd` flag) and `--add-dir <worktree-path>` to agy, assuming it was agy's equivalent.
It isn't: agy has no `--cwd` flag at all, and `--add-dir` only *adds* a directory to its
workspace — it doesn't change the primary working directory, which stayed whatever the Bash
tool's ambient cwd happened to be (the main repo, drifted there from earlier commands). agy
edited the live main-repo `dashboard.py` directly instead of its isolated copy.

**Caught before damage**: a routine `git status` check before assuming the worktree plan had
worked revealed the mismatch immediately — the edit was uncommitted, so nothing was lost, and
the content itself turned out correct (just landed in the wrong place). Reverted the main-repo
edit, verified zcode's actually-isolated worktree diff separately, and hand-merged the better
parts of both.

**Generalizable rule**: when an isolation plan depends on a specific CLI flag behaving a
certain way (setting a working directory, sandboxing execution, scoping permissions), verify
that flag's actual behavior — `tool --help | grep -i cwd` or equivalent — *before* delegating,
not after. Two tools built by different teams (here: zcode vs. agy, both CLI coding agents)
using a similar-sounding flag name (`--cwd` vs `--add-dir`) is exactly the kind of assumption
that silently fails, because the mistake produces no error — the delegated agent just runs
successfully in the wrong place.

**Secondary lesson — don't discard misplaced-but-correct work reflexively**: once the mistake
was found, the instinct could have been to throw away agy's output and redo everything cleanly.
Checking whether the *content* was actually wrong (it wasn't) before deciding what to do with
it turned an incident into free input — two independent implementations to compare instead of
one, merged into something better than either alone.

See also: [[2026-08-17_verify-facts-in-delegation-prompts]] (same underlying discipline —
verify assumptions in a delegation prompt/setup before trusting them, not after).
