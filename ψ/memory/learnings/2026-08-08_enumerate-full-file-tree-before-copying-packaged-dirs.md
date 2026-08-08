---
pattern: "When copying a skill/plugin/packaged directory by name, enumerate its full file tree first — don't assume a single entry-point file is the whole package"
date: 2026-08-08
source: "rrr: ayami-oracle"
concepts: ["file-copy", "verification", "generalization-trap"]
---

# Enumerate the full file tree before copying packaged directories

Copied 11 skill directories from `~/.claude/skills/` into a project's `.claude/skills/` using a loop that only grabbed each skill's `SKILL.md`. Two of the eleven (`mailbox`, `team-agents`) also ship a `scripts/` subdirectory that `SKILL.md` references by relative path — a `SKILL.md`-only copy would have silently produced a broken skill (references a script that doesn't exist at the destination).

Caught it with a follow-up `find "$dir" -type f | wc -l` check per skill, run only because of a general verification habit — not because the copy plan accounted for multi-file skills from the start. The assumption ("skills are single-file") had been generalized from an earlier, smaller batch (4 skills, all single-file) without re-verification.

**Rule**: before copying a "package" (skill, plugin, template directory — anything with a manifest/entry-point file that may reference sibling files), run a full-tree enumeration first (`find $src -type f`) and copy the whole tree, not just the file you assume is the whole thing. A small prior sample being uniform is not proof the pattern holds — verify each new batch's actual shape.
