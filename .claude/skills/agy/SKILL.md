---
name: agy
description: Delegate a task to agy — a separate, non-interactive multi-model coding agent CLI (installed at ~/.local/bin/agy, offers Gemini 3.x and Claude Sonnet 4.6 as backends). Use when the user says "agy", "ask agy", "ให้ agy ช่วย", wants a second opinion from a different model/agent, or wants a task run by a sibling AI coding agent instead of (or alongside) Claude. Do NOT trigger for talking to another Oracle/Claude instance (use /hey or /talk-to), for zcode (use /zcode — separate GLM-backed CLI), or for Qwen (auth currently broken — see ψ/memory learnings).
---

# /agy — Delegate to the agy multi-model coding agent

> agy is a separate AI coding CLI installed at `~/.local/bin/agy` (Mach-O binary). It behaves like Claude Code / zcode / Codex — its own agent loop with file read/write and a plan/accept-edits mode split. It's multi-model: `agy models` lists Gemini 3.6/3.5 Flash (high/medium/low effort), Gemini 3.1 Pro, and Claude Sonnet 4.6. Calling it means handing a task to a **different model** (your choice which one), not spawning a Claude subagent.

## When to use

- User explicitly asks for agy / "อีก agent หนึ่ง" / a second opinion
- Wants a specific model (e.g. Gemini) tried on the same problem without leaving this session
- Wants a task run in parallel by a sibling coding agent alongside Claude or zcode

Not a default — this is an explicit user choice. For ordinary parallel work inside this session, the Agent tool is still the default (see the command-reference artifact's delegation table). For Z.ai/GLM specifically, use `/zcode` instead.

## Non-interactive invocation

```bash
agy -p "<prompt>" --mode plan
```

- `-p, --print` (alias `--prompt`) — run one prompt, print the response, exit. Use this from Ayami; without it, `agy` opens an interactive session and a scripted call will hang.
- `--mode plan` — **read-only equivalent**: agy plans/analyzes but does not write files. Default choice for review/analysis tasks.
- `--mode accept-edits` — agy may write files without per-tool confirmation prompts. Only use when the user has explicitly asked for a task that requires edits.
- `--model <name>` — pick a specific backend (`agy models` to list current options — as of 2026-08-08: `gemini-3.6-flash-high/medium/low`, `gemini-3.5-flash-high/medium/low`, `gemini-3.1-pro-high/low`, `claude-sonnet-4-6`). Omit to use agy's default.
- `--add-dir <path>` — add an extra directory to agy's workspace (repeatable).
- `--sandbox` — run with terminal restrictions enabled; stacks with `--mode plan` for an extra-cautious read-only pass.
- `--effort low|medium|high` — reasoning effort, where the model supports it.
- `--dangerously-skip-permissions` — **avoid**. Auto-approves all tool permission requests with no prompting; only relevant if the user explicitly asks for a fully unattended run, and even then confirm with them first.

## Example

```bash
agy -p "Review .claude/hooks/safety-check.sh for bugs and security issues, report findings only" \
  --mode plan
```

```bash
agy -p "Try this same code-review task with Gemini instead of the default model" \
  --mode plan --model gemini-3.6-flash-high
```

## Other useful subcommands

- `agy models` — list available models for `--model`
- `agy agent` / `agy agents` — list configured agents (empty by default on a fresh project)
- `agy changelog` — release notes
- `agy install` — configure environment paths/shell settings (already done on this machine)

## Safety notes — same standard as /zcode

- agy is a real autonomous coding agent. `--mode plan` is the safe default for anything shaped like "review" or "analyze." Only switch to `--mode accept-edits` when the user has actually asked for changes to be made, and confirm before delegating anything that writes files, runs git operations, or touches shared state.
- **Never trust a delegated fix as done just because agy reports success.** The `/zcode` session on 2026-08-08 delegated a hardening fix to a safety-critical hook and it looked complete but had two real regressions (one that fully disabled the primary protection) — caught only by writing and running an explicit test suite against the actual output before committing. Apply the same standard here: for anything beyond a trivial read-only report, write a few concrete test cases and run them against what agy produced before telling the user it's done.
- agy runs as a **separate process** you shell out to — its actions won't show up in this session's tool-call history except as the Bash command that launched it and its final stdout. Summarize what it reported back to the user.

## Status

Verified working 2026-08-08 — `agy -p "reply with exactly one word: pong"` returned `pong`. No login/auth step was needed on this machine.
