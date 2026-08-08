---
pattern: "Learned arra-oracle-skills-cli: found + installed 4 skills missing from Ayami Oracle's local catalog (philosophy, oracle-cheatsheet, oracle-prism, go)"
date: 2026-08-08
source: "learn: Soul-Brews-Studio/arra-oracle-skills-cli"
concepts: ["learn", "codebase", "oracle-skills", "gap-analysis"]
---

# Learned arra-oracle-skills-cli — 4 missing skills

Compared Ayami Oracle's installed `.claude/skills/` against the official catalog at `Soul-Brews-Studio/arra-oracle-skills-cli` (default branch `alpha`). Found and installed 4 skills that were missing:

- **`/philosophy`** — displays the 5 Principles + Rule 6 (the WHY layer, distinct from `/about-oracle`'s WHAT and `/who-are-you`'s WHO). Has an alignment-check mode (`/philosophy check`).
- **`/oracle-cheatsheet`** — mines the session JSONL for commands + traps, generates a copy-paste cheat sheet to `ψ/writing/cheatsheets/`. Fully inline, no subagents.
- **`/oracle-prism`** — one agent shifts through 5 lenses (Archaeologist, Bug Hunter, Skeptic, Architect, Auditor) sequentially, inline. Presets: `--preset retro/design/incident`. Different from `/adversarial-analysis` (which spawns parallel subagents to actively disprove) and `/rrr` (emotional/learning retrospective).
- **`/go`** — single entry point for skill lifecycle management (list/install/remove/find/profile-switch/update). `disable-model-invocation: true` — must be typed explicitly, never auto-triggered, since it can do destructive removal. Wraps the `arra-oracle-skills` CLI; reads use the local binary, writes always fetch fresh from GitHub to prevent silent downgrades.

Deep-dive docs for each written to `ψ/learn/Soul-Brews-Studio/arra-oracle-skills-cli/2026-08-08/1620_*.md` (gitignored, not committed — per project convention `ψ/learn/` is study material, not tracked).
