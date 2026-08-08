---
name: zcode
description: Delegate a task to zcode (Z.ai GLM coding agent) running as a separate, non-interactive CLI process. Use when the user says "zcode", "ask zcode", "ให้ zcode ช่วย", "ลอง GLM ดู", wants a second opinion from a different model/agent, or wants a task run by a sibling AI coding agent instead of (or alongside) Claude. Do NOT trigger for talking to another Oracle/Claude instance (use /hey or /talk-to) or for Qwen (auth currently broken — see ψ/memory learnings).
---

# /zcode — Delegate to Z.ai's GLM coding agent

> zcode is a separate AI coding CLI (Z.ai / GLM models), installed at `/Applications/ZCode.app`, aliased as `zcode` in the shell. It behaves like Claude Code / Codex — its own agent loop with file read/write, tools, skills, and MCP support. Calling it means handing a task to a **different model**, not spawning a Claude subagent.

## When to use

- User explicitly asks for zcode / GLM / "ลอง agent อีกตัว"
- Wants a second opinion from a different model on the same problem
- Wants a task run in parallel by a sibling coding agent (e.g. one review from Claude, one from zcode)

Do not reach for this by default — it's an explicit user choice, not a general-purpose subagent replacement. For ordinary parallel work inside this session, the Agent tool is still the default (see the command-reference artifact's delegation table).

## Non-interactive invocation

```bash
zcode -p "<prompt>" --cwd "<absolute/path/to/repo>"
```

- `-p, --prompt` — run one prompt, print result, exit (no TUI). This is the mode to use from Ayami; the bare `zcode` command opens a full-screen interactive TUI and will hang a scripted call.
- `--cwd <path>` — **always pass this explicitly** rather than relying on the shell's current directory. zcode is a full agent with file write access; an unset `--cwd` risks it operating on the wrong project.
- `--attach <path>` — attach a file to the prompt (repeatable for multiple files).
- `--disallowedTools "Bash(git push*) Edit"` — deny specific tools/patterns, same shape as Claude Code's tool-permission strings. Use this to keep a delegated task read-only when the task doesn't need file writes (e.g. "just review this and report back").
- `--locale en-US|zh-CN|auto` — UI/response locale if needed.

## Example

```bash
zcode -p "Review src/auth.ts for race conditions, report findings only, don't edit anything" \
  --cwd "/Users/phongcheatphus/ayami-oracle" \
  --disallowedTools "Edit Write"
```

```bash
zcode -p "Implement the CSV export button described in ψ/inbox/focus-agent-main.md" \
  --cwd "/Users/phongcheatphus/ayami-oracle"
```

## Other useful subcommands

- `zcode doctor` — sanity-check the install (version, runtime, platform)
- `zcode skills list` — see zcode's own local skills
- `zcode login` / `zcode logout` — Z.AI OAuth session management (already logged in on this machine as of 2026-08-08 — verified working with a live test prompt)
- `zcode version` — print CLI version

## Safety notes

- zcode is a real autonomous coding agent with file write access in whatever `--cwd` you give it — treat a delegated task with the same care as any risky/hard-to-reverse action: confirm with the user before delegating anything that writes files, runs git operations, or touches shared state, same as you would before doing it yourself.
- Prefer `--disallowedTools` to scope a delegated task down to read-only when the task is "review/analyze" rather than "implement."
- zcode runs as a **separate process** you shell out to — it is not a Claude subagent, so its actions won't show up in this session's tool-call history except as the Bash command that launched it and its final stdout. Summarize what it reported back to the user rather than assuming they saw it.

## Status

Verified working 2026-08-08 — `zcode -p "reply with exactly one word: pong"` returned `pong`. Z.AI OAuth session already active on this machine; no `zcode login` needed.
