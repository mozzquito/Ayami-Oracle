---
pattern: don't assume a behavior verified on one AI CLI (e.g. Claude's auto-skill-detection from keywords) also holds on a sibling CLI (agy/zcode) just because both read the same skill files — verify each behavior per-tool
date: 2026-08-21
source: rrr: ayami-oracle
concepts: [verify-before-asserting, agy, zcode, cross-agent-tooling, skills]
---

# Don't assume shared behavior across sibling agent CLIs just because they share files

Two agents can read the exact same `SKILL.md` file and still trigger differently. Confirmed
2026-08-20/21 in this repo: `agy` and `zcode` both auto-read `.agents/skills/<name>/SKILL.md`
(same frontmatter shape as Claude Code's `.claude/skills/`), and both correctly answer when a
skill is invoked **by explicit name** in the prompt ("ใช้ skill ux-ui-design แล้ว..."). What was
*not* tested: whether either CLI auto-triggers a skill from natural-language keywords alone
(the way Claude Code's own skill-matching works, based on the `description` field), without the
skill name being typed.

While drafting advice for how to phrase future commands, there was a near-miss: about to write
"agy/zcode auto-detect the right skill from keywords, just like I do" — extrapolating from
Claude Code's own behavior to a sibling tool that had never actually been tested for that
specific behavior. Caught before sending; the advice was corrected to explicitly recommend
naming the skill until auto-detection is verified.

**General rule**: file-format compatibility (same `SKILL.md` shape, same `AGENTS.md`/`CLAUDE.md`
auto-read) is not evidence of *matching-behavior* compatibility (auto-trigger heuristics,
model selection defaults, permission flows). Each is a separate claim and needs its own test.
See also [[project_impactwildlife_ssl]]-adjacent pattern and the existing
`feedback_verify_before_asserting` memory — this is the same principle applied specifically to
cross-CLI behavior assumptions, not just fact assumptions.
