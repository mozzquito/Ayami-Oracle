---
pattern: "External design review (agy/zcode) is only as good as what it can see — reading the actual codebase during Develop overrode 2 of its own recommendations, and caught a near-miss overwrite of an existing file"
date: 2026-08-31
source: "session: forking mildronize/my-template into mozzquito/my-template"
concepts: ["design-review", "develop-stage", "sqlc", "architecture-tests", "overwrite-risk"]
---

# Design review vs. real code, during actual Develop

While implementing a design (`ψ/lab/my-template/DESIGN.md`) that had already been
reviewed by `/agy` and `/zcode`, reading the real target codebase during Develop
overturned two of that review's own conclusions, and caught a near-miss file overwrite:

1. **A "clean" design decision can be moot once you see the real contract.** The design
   dropped a `seq` column in favor of ULID-only ordering, validated by both reviewers.
   Reading the actual repo showed `seq` was already `required` in two OpenAPI specs,
   rendered in a React component, and asserted by name in several frontend tests —
   removing it would have been a much bigger, contract-breaking change than either
   reviewer could have known, since neither had access to the target repo when reviewing.
   Lesson: an abstract design review is a second opinion on the *idea*, not a substitute
   for checking what the idea actually touches in the real code.

2. **A base repo's own comments can record a decision a reviewer will re-propose blind.**
   Added a DB-level append-only trigger per review advice; the base repo's *existing*
   `todo_events` table had a comment explicitly saying enforcement was
   "application-level only, deliberately." Adding the trigger broke a legitimate test
   fixture (backdating timestamps via raw UPDATE for pagination tests) that the original,
   deliberate choice had made possible. Reverted. Lesson: when a codebase already made a
   choice and left a reason in a comment, that reason often encodes a constraint an
   outside reviewer (or an earlier version of yourself, reasoning abstractly) can't see.

3. **`git status`/`git diff` before committing caught overwriting a real file with a
   worse draft.** The design assumed the base repo had no portable Claude Skill file and
   planned to write one from a scaffold. Mid-implementation, `cp`-ing that scaffold into
   place would have silently clobbered an existing, better `.claude/skills/.../SKILL.md`
   (303 lines) the initial `/learn` exploration had simply missed. Caught only because
   `git status` was checked before committing, per [[feedback_verify_before_asserting]] —
   restored from `git checkout HEAD --` and extended the real file instead.

**How to apply**: when a design has been reviewed abstractly (by another model, or by
yourself in a planning pass) and Develop is about to start against a real, pre-existing
codebase — re-verify the review's load-bearing assumptions against the actual code before
implementing them, especially anything that removes a field, adds a DB constraint, or
assumes a file/pattern doesn't already exist. `git status` after any file-copy or
scaffold-drop operation, always, even when confident about what should be there.
