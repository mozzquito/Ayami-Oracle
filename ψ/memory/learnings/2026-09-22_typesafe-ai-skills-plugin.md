---
pattern: "Learned typesafe-ai/skills: already-installed plugin (v0.5.7, matches HEAD), cleared by zcode+agy as safe, jev-gate screening skipped for missing API key"
date: 2026-09-22
source: "learn: typesafe-ai/skills"
concepts: ["learn", "codebase", "typesafe", "jev", "plugin-security", "zcode", "agy"]
---

# Learned typesafe-ai/skills

- The plugin `typesafe@typesafe-ai` (marketplace `typesafe-ai/skills`) was already installed
  and up to date (v0.5.7 = repo HEAD) before this session — no install action was needed.
- It's pure documentation (one SKILL.md teaching TypeSafe/Jev usage patterns), separate from
  `ψ/lab/jev-gate` (the actual gate script). The plugin has no code path, no hooks, no MCP.
- Paired zcode + agy review (per jev-gate's own "always pair" rule) both cleared it: no
  prompt-injection smell, manifest requests zero elevated privileges.
- jev-gate itself couldn't screen the fetched text — no `TYPESAFE_API_KEY` found on this
  machine. Don't assume the key from [[project_typesafe_jev_trial]] is still live; it needs
  re-checking/re-issuing before jev-gate can actually run again.
