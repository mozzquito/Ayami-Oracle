---
name: HOOKS-SETUP
description: Reference document.
---

# Claude Code Hooks Setup

Setup instructions for the hooks that show timestamp and branch, and warn when the conversation context gets long.

## What You Get

```
🕐 11:57 | 31 December 2025 | Nat-s-Agents | main
```

The context line below appears only once context reaches `TOKEN_WARN_K` (default 150k); below that the hook is silent:

```
⚠️ CONTEXT 181k (warn 150k) - Mention to มอส that this session is getting long; suggest wrapping up ...
```

## Files Needed

### 1. `.claude/settings.json`

Copy from repo - contains all hook definitions.

### 2. `.claude/scripts/token-check.sh`

Warns when the conversation context gets long. Every turn re-reads the whole context, so cost grows with session length.
- Reads the context size from `transcript_path` in the hook's stdin JSON (no `statusline.json` needed)
- Silent below `TOKEN_WARN_K` (default 150, in k tokens)
- `⚠️` at or above `TOKEN_WARN_K`: suggest wrapping up and a fresh session
- `🚨` at or above `TOKEN_HARD_K` (default 250): louder, and appends to `ψ/inbox/handoff.log` (at most once per hour)
- Thresholds are absolute, not a % of the window. Wired on `UserPromptSubmit` only (the one event whose stdout reaches the model).

### 3. `.claude/scripts/agent-id.sh`

Returns current git branch or agent ID.

### 4. `ψ/active/statusline.json` (legacy, not used by token-check.sh)

`token-check.sh` no longer reads this file (changed 2026-09-21). Only `.claude/scripts/statusline.sh` and `.claude/scripts/tokens.sh` still read it; nothing in this setup writes it, so the context part of `statusline.sh` stays silent.

## Setup Steps

```bash
# 1. Pull latest from origin
cd /home/nat/ghq/github.com/laris-co/nat-s-Agents
git pull origin main

# 2. Make scripts executable
chmod +x .claude/scripts/*.sh
chmod +x .claude/hooks/*.sh

# 3. (no longer needed) token-check.sh does not use ψ/active/statusline.json any more

# 4. Restart Claude Code
# The hooks will now show on each prompt
```

## Hook Triggers

| Hook | When | Shows |
|------|------|-------|
| UserPromptSubmit | Every prompt | Timestamp; context warning once >= 150k |
| PreToolUse:Bash | Before bash | Safety check |
| PreToolUse:Task | Before subagent | Log start |
| PostToolUse:Task | After subagent | Log end |
| SessionStart | Session begin | Agent identity + Handoff |

## Callback Hook (for statusline.json) - legacy

Only needed if you still want `statusline.sh` / `tokens.sh` to show context; `token-check.sh` does not need it.
Add to settings.json under each hook section:

```json
{
  "type": "command",
  "command": "callback"
}
```

This makes Claude Code write current model/context info to statusline.json.

## Troubleshooting

**Hooks not showing?**
- Check scripts are executable
- Verify CLAUDE_PROJECT_DIR is set
- Check jq is installed for token-check.sh

**No context warning?**
- It only appears once context reaches `TOKEN_WARN_K`; to test, start a session with `TOKEN_WARN_K=1`

**Permission errors?**
- Run: `chmod +x .claude/scripts/*.sh .claude/hooks/*.sh`

---
Created: 2025-12-31
Updated: 2026-09-21 (token-check.sh reads transcript_path, absolute thresholds)
