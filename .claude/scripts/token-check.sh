#!/bin/bash
# token-check.sh - Warn when the conversation context gets long, log a handoff at the hard limit
#
# WHY:
#   Every turn re-reads the whole context, so cost ~ turns x context size.
#   Measured 2026-09-21: sessions that ran to 700k-970k tokens spent 87-95% of their
#   cache reads above 200k. Ending a session early is the biggest single saving.
#
# WHAT IT DOES:
#   - Reads the current context size from the session transcript (transcript_path on stdin)
#   - Silent below TOKEN_WARN_K (no per-prompt noise)
#   - >= TOKEN_WARN_K: tells the LLM to suggest `/forward` and a fresh session
#   - >= TOKEN_HARD_K: same, louder, and appends a handoff entry to ψ/inbox/handoff.log
#     (append-only, at most once per hour)
#
# THRESHOLDS (absolute, in k tokens - NOT a % of the window, so a 1M window can't hide it):
#   TOKEN_WARN_K  default 150
#   TOKEN_HARD_K  default 250
#
# HOOK INTEGRATION:
#   - Wire on UserPromptSubmit: only that event's stdout reaches the LLM as context.
#     (Pre/PostToolUse stdout is not shown to the LLM, and would spawn this per tool call.)
#   - Needs jq. Exits 0 silently on anything unexpected - a monitor must never block work.
#
# HISTORY:
#   - 2026-01-14: original, read ψ/active/statusline.json (% of 80% of window)
#   - 2026-09-21: statusline.json is no longer written (global statusline.sh was replaced
#     2026-08-15), so the old version was a silent no-op. Now reads the transcript.

WARN_K="${TOKEN_WARN_K:-150}"
HARD_K="${TOKEN_HARD_K:-250}"

ROOT="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null)}"

command -v jq >/dev/null 2>&1 || exit 0

# Hook payload arrives as JSON on stdin; don't block if run from a terminal
[ -t 0 ] && exit 0
INPUT=$(cat)
TRANSCRIPT=$(printf '%s' "$INPUT" | jq -r '.transcript_path // empty' 2>/dev/null)
[ -n "$TRANSCRIPT" ] && [ -f "$TRANSCRIPT" ] || exit 0

# Context size = input + cache-write + cache-read of the last real assistant turn.
# A compact_boundary after it means that number is stale, so stay silent until the next turn.
used=$(tail -n 40 "$TRANSCRIPT" | jq -rs '
  (map(select(.type=="assistant" and .isSidechain!=true and ((.message.usage.output_tokens // 0) > 0))) | length) as $n
  | if $n == 0 then empty else
      (to_entries
       | map(select(.value.type=="assistant" and .value.isSidechain!=true and ((.value.message.usage.output_tokens // 0) > 0)))
       | last) as $last
      | (to_entries | map(select(.value.type=="system" and .value.subtype=="compact_boundary")) | last // null) as $cb
      | if ($cb != null and $cb.key > $last.key) then empty
        else $last.value.message.usage
             | (.input_tokens // 0) + (.cache_creation_input_tokens // 0) + (.cache_read_input_tokens // 0)
        end
    end' 2>/dev/null)

case "$used" in ''|*[!0-9]*) exit 0 ;; esac
used_k=$((used / 1000))

[ "$used_k" -lt "$WARN_K" ] && exit 0

if [ "$used_k" -ge "$HARD_K" ]; then
  HANDOFF_LOG="$ROOT/ψ/inbox/handoff.log"

  # Already logged within the last hour? Then just show status.
  if [ -f "$HANDOFF_LOG" ]; then
    LAST_ENTRY=$(grep -E "^## [0-9]{4}-[0-9]{2}-[0-9]{2}" "$HANDOFF_LOG" | tail -1 | cut -d'|' -f1 | sed 's/## //')
    if [ -n "$LAST_ENTRY" ]; then
      LAST_TS=$(date -j -f "%Y-%m-%d %H:%M " "$LAST_ENTRY " +%s 2>/dev/null || echo 0)
      DIFF=$(($(date +%s) - LAST_TS))
      if [ "$DIFF" -lt 3600 ]; then
        echo "🚨 CONTEXT ${used_k}k (limit ${HARD_K}k) - Tell มอส now and suggest \`/forward\` + a fresh session before more work. (handoff logged $((DIFF / 60))m ago)"
        exit 0
      fi
    fi
  fi

  echo "🚨 CONTEXT ${used_k}k (limit ${HARD_K}k) - Tell มอส now and suggest \`/forward\` + a fresh session before more work. Every turn re-reads all ${used_k}k. Handoff logged to ψ/inbox/handoff.log"

  RECENT_COMMITS=$(git -C "$ROOT" log --oneline -3 2>/dev/null | sed 's/^/  /')
  FOCUS=$(grep "TASK:" "$ROOT/ψ/inbox/focus-agent-main.md" 2>/dev/null | head -1)
  [ -n "$FOCUS" ] || FOCUS="(no focus set)"

  mkdir -p "$(dirname "$HANDOFF_LOG")" 2>/dev/null
  {
    echo ""
    echo "---"
    echo "## $(date '+%Y-%m-%d %H:%M') | ${used_k}k"
    echo ""
    echo "**Focus**: $FOCUS"
    echo ""
    echo "**Commits**:"
    echo "$RECENT_COMMITS"
    echo ""
  } >> "$HANDOFF_LOG"
else
  echo "⚠️ CONTEXT ${used_k}k (warn ${WARN_K}k) - Mention to มอส that this session is getting long; suggest wrapping up this task and \`/forward\` into a fresh session."
fi
