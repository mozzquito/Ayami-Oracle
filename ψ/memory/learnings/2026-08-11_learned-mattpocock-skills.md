---
pattern: "Learned mattpocock/skills: promoted-bucket plugin curation, model- vs user-invoked skill split, ask-matt as router-of-flows"
date: 2026-08-11
source: "learn: mattpocock/skills"
concepts: ["learn", "codebase", "claude-code-skills", "skill-design", "plugin-architecture"]
---

# Learned mattpocock/skills

Matt Pocock's public Claude Code / Codex skill set (aihero.dev), release v1.2.0 → v1.2.3.

- **Promoted-bucket model**: only `skills/engineering/` and `skills/productivity/` ship in the Claude Code plugin bundle (`.claude-plugin/plugin.json` lists each path explicitly, not a glob). `misc/`, `in-progress/` (deliberate public beta), and `deprecated/` stay installable one-by-one via `skills.sh` but are excluded from the plugin and from top-level READMEs.
- **Model- vs user-invoked skills**: frontmatter `disable-model-invocation: true` marks a skill as user-only (typed `/command`); its Codex analog is `agents/openai.yaml`'s `policy.allow_implicit_invocation: false` — added in v1.2.0 so every skill works identically across Claude Code and Codex without generated copies.
- **`ask-matt` as router-of-flows**: a single meta-skill that maps every other skill into one flow (grilling → wayfinder/to-spec → implement → triage), plus a decision tree for context-window boundaries (continue → `/clear` → `/handoff` → subagent → `/compact`, in that preference order). v1.2.0 introduced "decision ticket" (wayfinder) as a named term distinct from an implementation ticket — worth reusing that framing whenever guiding someone through an ambiguous decision vs. a scoped build.
