#!/bin/bash
# Short agent ID for hooks (no colors, just ID)
ROOT="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null)}"

if [[ "$PWD" =~ $ROOT/agents/([0-9]+) ]]; then
  echo "agent/${BASH_REMATCH[1]}"
elif [[ "$PWD" == "$ROOT" ]]; then
  echo "main"
else
  echo "?"
fi
