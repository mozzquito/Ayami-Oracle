#!/bin/bash
# Agent Identity Detection
# Model-agnostic - works for Claude Code, z.ai, Codex, Gemini, etc.

ROOT="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null)}"
export MAW_REPO_ROOT="$ROOT"

# Short session-ID suffix for plain top-level sessions. Without this, every
# concurrent plain session reports AGENT_ID=main and collides on the same
# ψ/inbox/focus-agent-main.md (observed directly, 2026-09-23 — 5+ concurrent
# sessions overwriting each other's focus file and handoff.log entries).
# MAW worker IDs (agents/N) already don't collide, so they're untouched.
SESSION_SHORT="unknown"
if [ ! -t 0 ] && command -v jq >/dev/null 2>&1; then
  HOOK_INPUT=$(cat 2>/dev/null)
  SID=$(printf '%s' "$HOOK_INPUT" | jq -r '.session_id // empty' 2>/dev/null)
  [ -n "$SID" ] && SESSION_SHORT="${SID:0:8}"
fi

# Colors: 1=Yellow 2=Magenta 3=Green 4=Cyan 5=Red Main=Blue
YELLOW='\033[0;33m'
MAGENTA='\033[0;35m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Detect agent from PWD
if [[ "$PWD" =~ $ROOT/agents/([0-9]+)$ ]]; then
  AGENT_ID="${BASH_REMATCH[1]}"
  AGENT_TYPE="worker"
  BRANCH="agents/$AGENT_ID"
  case $AGENT_ID in
    1) COLOR=$YELLOW ;;
    2) COLOR=$MAGENTA ;;
    3) COLOR=$GREEN ;;
    4) COLOR=$CYAN ;;
    5) COLOR=$RED ;;
    *) COLOR=$NC ;;
  esac
elif [[ "$PWD" == "$ROOT" ]]; then
  AGENT_ID="main-${SESSION_SHORT}"
  AGENT_TYPE="orchestrator"
  BRANCH="main"
  COLOR=$BLUE
else
  AGENT_ID="unknown"
  AGENT_TYPE="external"
  BRANCH="?"
  COLOR=$NC
fi

# Output with color
echo -e "${COLOR}${BOLD}┌─────────────────────────────────────────────${NC}"
echo -e "${COLOR}${BOLD}│${NC} 🕐 $(date '+%Y-%m-%d %H:%M')"
echo -e "${COLOR}${BOLD}│${NC}"
echo -e "${COLOR}${BOLD}│${NC} AGENT_ID:   ${COLOR}${BOLD}$AGENT_ID${NC}"
echo -e "${COLOR}${BOLD}│${NC} AGENT_TYPE: $AGENT_TYPE"
echo -e "${COLOR}${BOLD}│${NC} BRANCH:     $BRANCH"
echo -e "${COLOR}${BOLD}│${NC}"
echo -e "${COLOR}${BOLD}│${NC} MAW: maw peek | sync | merge $AGENT_ID"
echo -e "${COLOR}${BOLD}└─────────────────────────────────────────────${NC}"
