---
pattern: When reusing another skill/agent's file-destination convention, verify its git-tracking status against .gitignore empirically — don't trust a documented pillar table or a copied convention's correctness
date: 2026-08-27
source: rrr: ayami-oracle
concepts: [git, file-routing, testing, design-review, gitignore]
---

# Verify git-tracking before reusing a destination convention

Building a `/triage` skill that routes `ψ/inbox/` items to their correct home, I copied an
existing agent's (`note-taker`) destination convention — `ψ/memory/logs/{feelings,info}/` — into
the new skill's design without independently checking that folder against `.gitignore`. It
turned out to be gitignored by existing repo convention (ephemeral logs), which broke a plain
`git mv` the first time the script tried to move a tracked file there.

Two independent AI agents (zcode, agy) reviewed the design twice — once at the architecture
gate, once at the edge-case/testing gate — and neither caught it, because the question I asked
them was about classification logic and mechanical failure modes, not "is every destination
path's git-tracking status what the move logic assumes?" A documented pillar table in the
project's CLAUDE.md also claimed a related path (`ψ/inbox/*`) was git-tracked; it wasn't — the
whole folder was untracked in practice.

**Why**: Copying a convention (a folder path, a naming scheme, a destination) from existing
code inherits its *shape* but not its *correctness guarantees* for a new context. A folder that
was gitignored on purpose for one skill's writes (ephemeral notes) becomes a silent bug for a
different skill that assumes git-tracked semantics (move-and-stage) around the same path.
Neither a design-review consult nor a synthetic sandbox test caught it — the sandbox tests
didn't replicate the real repo's `.gitignore` rules, so the failure mode simply didn't exist in
the test environment. It only surfaced via a live dry-run against real data in the actual repo.

**How to apply**: Before writing move/write logic that touches an existing destination
convention (whether copied from another skill, or documented in project config), run
`git check-ignore -v <path>` and `git ls-files <path>` directly against the real repo — don't
infer tracking status from documentation or from another skill's apparent behavior. When
building a sandbox test for file-mutation logic, seed the sandbox's `.gitignore` with the real
repo's actual ignore rules for the paths under test, not a clean/simplified stand-in. And before
calling a new mechanical script "done" even after passing agent review + synthetic tests, run at
least one live dry-run against real data in the target repo — it catches what neither a
second-opinion review nor a test you designed yourself thought to check.
