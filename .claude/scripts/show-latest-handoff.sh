#!/bin/bash
# Show latest handoff - checks handoff.log for recent entries
# Only shows if there are entries from today/yesterday

ROOT="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null)}"
HANDOFF_LOG="$ROOT/ψ/inbox/handoff.log"

[ ! -f "$HANDOFF_LOG" ] && exit 0

# This session's own ID, so we can tell whether the last logged handoff is
# ours or a concurrent sibling session's. Without this, a resumed session was
# shown whatever ANY session last logged, including unrelated sibling work —
# directly observed causing 5+ near-misattributed retrospectives, 2026-09-23.
THIS_SESSION_SHORT="unknown"
if [ ! -t 0 ] && command -v jq >/dev/null 2>&1; then
  HOOK_INPUT=$(cat 2>/dev/null)
  SID=$(printf '%s' "$HOOK_INPUT" | jq -r '.session_id // empty' 2>/dev/null)
  [ -n "$SID" ] && THIS_SESSION_SHORT="${SID:0:8}"
fi

# Check for entries from today or yesterday
TODAY=$(date '+%Y-%m-%d')
YESTERDAY=$(date -v-1d '+%Y-%m-%d' 2>/dev/null || date -d 'yesterday' '+%Y-%m-%d' 2>/dev/null)

if grep -q "$TODAY\|$YESTERDAY" "$HANDOFF_LOG" 2>/dev/null; then
  ENTRY=$(awk '/^---$/{found=1; buffer=""} found{buffer=buffer $0 "\n"} END{print buffer}' "$HANDOFF_LOG" | head -8)
  # Older entries (pre-fix) have no Session line — treat as unknown, not a mismatch.
  ENTRY_SESSION=$(printf '%s' "$ENTRY" | sed -n 's/^\*\*Session\*\*: //p' | head -1)

  if [ -n "$ENTRY_SESSION" ] && [ "$ENTRY_SESSION" != "unknown" ] && [ "$ENTRY_SESSION" != "$THIS_SESSION_SHORT" ]; then
    echo "⚠️ Last logged handoff belongs to a DIFFERENT session ($ENTRY_SESSION), not this one (${THIS_SESSION_SHORT}) — shown as sibling context, not necessarily this session's own history. Verify (e.g. session-clock / this session's own .jsonl) before assuming continuity:"
  else
    echo "📋 Previous session ended at high context. Last handoff:"
  fi
  echo ""
  printf '%s\n' "$ENTRY"
  echo ""
  echo "💡 Run /recap to orient, check latest retrospective for context."
fi
