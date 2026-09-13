---
name: grok
description: Delegate a task to grok (xAI Grok coding agent CLI, custom-built in ψ/incubate/grok-cli) running as a separate, non-interactive process. Use when the user says "grok", "ask grok", "ให้ grok ช่วย", "ลอง Grok ดู", wants a second opinion from a different model/agent, or wants a task run by a sibling AI coding agent instead of (or alongside) Claude. Do NOT trigger for Grok Bot the Cursor-sandbox product (that's mcp__grokbot__* / SSH to box@cursor) or for zcode/agy (separate CLIs).
---

# /grok — Delegate to xAI's Grok API via the custom grok-cli

> `grok` is a small MVP coding agent CLI **built in this repo** (`ψ/incubate/grok-cli`, npm-linked as a real `grok` binary on PATH — no alias caveat like zcode). It has its own agent loop: read/write/edit files, `bash` (git included, no separate git tool), `web_fetch`, and `web_search` (only if a Tavily key is configured). It also remembers past runs per-project via local SQLite+FTS5. It is much thinner than zcode/Claude Code — no hooks/MCP/skills, no `--disallowedTools`.

## When to use

- User explicitly asks for grok / xAI / "ลอง Grok ดู"
- Wants a second opinion from a different model on the same problem
- Wants a task run in parallel by a sibling coding agent (e.g. one review from Claude, one from zcode, one from grok)

Do not reach for this by default — same as zcode/agy, it's an explicit user choice, not a general subagent replacement.

## Prerequisite: is it actually set up?

`grok` needs an xAI API key the user must obtain themselves (this tool never signs up or enters payment info). Check first:

```bash
grok --help  # always works, no key needed
cat ~/.grok-cli/config.json 2>&1  # or: echo $XAI_API_KEY
```

If neither is set, a run fails fast with a clear message pointing to https://console.x.ai — surface that to the user rather than retrying.

## Non-interactive invocation

```bash
grok -p "<prompt>" --cwd "<absolute/path/to/repo>" --yolo
```

- `-p, --prompt` — the task. Required.
- `--cwd <path>` — **always pass this explicitly**, same reasoning as zcode: it's a full agent with file write access, don't let it default to the wrong directory.
- `--yolo` — **required when calling this from Ayami's own Bash tool.** Every `bash` command grok's agent loop wants to run is gated behind a confirmation prompt; when stdin isn't a TTY (which it never is when Ayami shells out), that prompt auto-refuses instead of hanging. `--yolo` skips it. This means delegating to grok is equivalent to pre-approving everything it decides to run in `--cwd` — treat it with the same care as zcode's file-write warning below, confirm with the user before delegating anything that writes files or touches shared state.
- `--max-turns <n>` — cap tool-call round trips (default 25) if a task seems open-ended.
- `--quiet` — suppress the `→ tool call` progress lines on stderr if you only want the final answer.

No `--disallowedTools` equivalent exists yet — you cannot scope a grok delegation to read-only the way you can with zcode. If the task should only review/report, say so explicitly in the prompt and verify the diff afterward rather than relying on a flag to enforce it.

## Example

```bash
grok -p "Add a --version flag that reads the version from package.json" \
  --cwd "/Users/phongcheatphus/ayami-oracle/ψ/incubate/grok-cli" \
  --yolo
```

## Memory (project-scoped, automatic)

Every run's prompt + final answer is saved to `~/.grok-cli/memory.sqlite`, keyed by `--cwd`. A later `grok` call on the *same* `--cwd` automatically gets relevant past runs injected as context — nothing to pass, it just happens. Different projects never see each other's history. Don't rely on this for anything precise (it's keyword search, not semantic) — verify against the actual files rather than trusting a recalled summary.

## Other subcommands

- `grok config set-key <xai-api-key>` — the user's own action, not yours to run with a real key on their behalf unless they've explicitly handed you the key to enter (same secret-hygiene rules as any other API key in this repo).
- `grok config set-search-key <tavily-api-key>` — optional, enables `web_search`.
- `grok config path` — print the config file location.

## Safety notes

- grok is a real autonomous coding agent with file write access in whatever `--cwd` you give it, and `--yolo` (needed for non-interactive use) removes its own per-command bash confirmation on top of that — confirm with the user before delegating anything destructive, exactly as you would before doing it yourself.
- It runs as a **separate process**, not a Claude subagent — its actions won't show up in this session's tool history except as the Bash command that launched it and its stdout. Summarize what it reported rather than assuming the user saw it.
- No `--disallowedTools` yet (see above) — a "review only, don't edit" ask relies on the prompt wording and your own follow-up diff check, not an enforced flag.

## Status

Built 2026-09-10/11 in `ψ/incubate/grok-cli`. Typechecked clean, and every non-model piece (memory recall + cwd isolation, `web_fetch`, bash confirm/decline gating, tool-list gating on `web_search`) verified with direct unit-level calls. **Not yet verified against a real xAI API call** — no `XAI_API_KEY` was available on this machine as of this writing. First real `grok -p "..."` run should be treated as the actual smoke test; report back what happened rather than assuming success.
