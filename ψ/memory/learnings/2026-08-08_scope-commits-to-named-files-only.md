---
pattern: "When a commit instruction names a specific, narrow file set, stage exactly that set — don't sweep in other pending changes sitting in the working tree, even if produced moments earlier by the same workflow"
date: 2026-08-08
source: "rrr: ayami-oracle"
concepts: ["git", "commit-scope", "user-intent"]
---

# Scope commits to exactly what was named

User said "commit 4 skill เข้าgit ได้เลย" (commit these 4 skills) while 4 other pending files sat in the working tree — 3 `/rrr`-generated memory files and 1 modified metrics file, all produced minutes earlier by the same session. Staged and committed only the 4 named skill files, leaving the memory files untouched.

**Rule**: a commit instruction that names a specific set of files is a boundary, not a suggestion — don't bundle unrelated-but-present pending changes into the same commit just because they exist in the working tree. If it's unclear whether adjacent pending changes should be included, ask rather than assume either direction (over- or under-committing).

Secondary observation: two `/rrr` invocations 4 minutes apart (one after a large multi-part session, one after a single follow-up commit) each produced a full-template retrospective per the skill's own rules. For genuinely tiny follow-up sessions, it may be worth surfacing to the human whether they'd rather fold the update into the prior retro than get a second near-duplicate file — the skill doesn't currently offer that choice, so this is a note for future skill design, not something to route around unilaterally today.
