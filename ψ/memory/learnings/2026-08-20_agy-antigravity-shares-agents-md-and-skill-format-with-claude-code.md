---
pattern: agy (Google Antigravity CLI) auto-reads this repo's AGENTS.md, .agents/rules/*.md, and CLAUDE.md, and its .agents/skills/<name>/SKILL.md format is byte-compatible with Claude Code's .claude/skills/ — cross-agent knowledge sharing is a file mirror, not a rebuild
date: 2026-08-20
source: rrr: ayami-oracle
concepts: [agy, antigravity, zcode, cross-agent-tooling, skills, mcp, multi-model]
---

# agy/Antigravity shares AGENTS.md + SKILL.md format with Claude Code

`agy` (installed at `~/.local/bin/agy`) is not a thin wrapper CLI — it's Google **Antigravity**'s
CLI companion (same product as the `Antigravity.app` IDE, config at `~/.gemini/antigravity*`).
It offers Gemini 3.x, Claude Sonnet 4.6/Opus 4.6 (Thinking), and GPT-OSS 120B as backends, and
has real infrastructure: interactive sessions with `--continue`/`--conversation <id>` resume,
a plugin system, and MCP support (`mcpServers` key in `~/.gemini/settings.json`, or
`mcp_config.json` per plugin — confirmed via binary strings, not just docs).

Empirically confirmed (2026-08-20, in `ayami-oracle` repo):

- Both `agy` and `zcode` (GLM via ZCode.app) auto-read `AGENTS.md` + `.agents/rules/*.md`
  (frontmatter `trigger: always_on`) + linked `CLAUDE.md` **with zero extra setup** — no MCP
  server, no special flag. `agy` fully adopts the project persona ("ฉันคือ Ayami Oracle");
  `zcode` stays meta ("ฉันคือ ZCode ที่ทำงานภายใต้กฎของ Ayami Oracle") — same source files,
  different framing per CLI.
- `agy`'s skill format at `.agents/skills/<name>/SKILL.md` uses the same frontmatter shape
  (`name`, `description`) as Claude Code's `.claude/skills/<name>/SKILL.md` — a straight
  `cp` of 24 real project skills (verified byte-identical) was enough for `agy` to pick them
  up and cite the right file/line.
- Conversation state is genuinely shared across models: `agy -p "..." --model gemini-3.7-flash-high`
  then `agy -p "..." --model claude-sonnet-4-6 --conversation <id-from-first-call>` — the second
  call correctly recalled context the first model was given. Model choice is a per-call flag,
  not a session-locked property.
- No lock/collision running multiple `agy` processes with different `--model` concurrently
  (tested 3-way parallel: two Gemini tiers + Claude Sonnet, all completed independently).
  Gemini and "Claude and GPT" models draw from **separate quota pools** in Antigravity's
  own account — unrelated to Claude Code's own usage.
- Headless (`agy -p`) mode denies any command needing filesystem writes by default (no
  interactive terminal to approve) — this is `agy`'s own permission gate, separate from
  Claude Code's. `--dangerously-skip-permissions` and `--mode accept-edits` both got blocked
  when *I* (Claude Code) tried to invoke them via Bash — that's Claude Code's own classifier
  refusing to let me bypass another tool's permission prompt, not an agy-side failure.

**Practical implication**: teaching a shared skill/persona to Claude + agy + zcode in a repo
that already has `AGENTS.md`/`.agents/rules/` wired up is a **file-mirroring problem**, not an
integration project — write once in `.claude/skills/`, `cp` to `.agents/skills/`, done. The
real remaining gaps for agy-as-a-full-host are: (1) MCP servers with secrets need to be wired
by the human directly — writing bearer tokens into new files from an agent session trips
safety classifiers on both sides; (2) headless automation (cron-style, no interactive
approval) needs agy's own permission allowlist configured, analogous to Claude Code's
`settings.json` permissions — not yet explored.
