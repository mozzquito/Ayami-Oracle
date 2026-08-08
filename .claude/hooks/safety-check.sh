#!/bin/bash
# Safety check hook - blocks dangerous commands
# Input: JSON via stdin with tool_input.command
# Exit codes: 0 = allow, 1 = block (hooks expect 0=proceed, non-0=deny)
set -euo pipefail

# --- Input parsing (LOW: jq null handling on missing key) ---
INPUT=$(cat)
CMD=$(echo "$INPUT" | jq -r 'if .tool_input.command then .tool_input.command else "" end' 2>/dev/null) || CMD=""

# Bail early on empty/whitespace-only input
if [[ -z "${CMD// /}" ]]; then
  exit 0
fi

# --- Normalize for detection (HIGH: line-oriented checks miss multi-line commands) ---
# Convert real newlines to ';' (not a bare space) so a dangerous command hidden
# on a later line still lands right after a command-boundary token — the
# per-pattern regexes below all anchor matches to (^|;|&&|\|\|), so collapsing
# newlines to plain spaces would hide line 2+ from every check.
NORMALIZED=$(printf '%s' "$CMD" | tr '\r\n' ';;')

# Helper: check regex against the normalized command (returns 0 on match)
cmd_matches() {
  echo "$NORMALIZED" | grep -qE "$1"
}

# --- WORKTREE BOUNDARY CHECK ---
# If running from agents/N, block directory-change outside worktree AND block push to main
ROOT="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || true)}"
if [[ -n "$ROOT" && "$PWD" =~ $ROOT/agents/([0-9]+) ]]; then
  AGENT_ID="${BASH_REMATCH[1]}"
  MY_WORKTREE="$ROOT/agents/$AGENT_ID"

  # Resolve worktree to physical path (MEDIUM: symlink bypass)
  MY_WORKTREE_REAL=$(cd "$MY_WORKTREE" 2>/dev/null && pwd -P 2>/dev/null) || MY_WORKTREE_REAL="$MY_WORKTREE"

  # HIGH: only-first-cd checked — scan ALL cd/pushd targets, not just head -1
  # HIGH: pushd/CDPATH not blocked — also catch pushd/popd
  if cmd_matches '(^|;|&&|\|\|)\s*(cd|pushd)\s+'; then
    BLOCKED=0

    # Extract every cd/pushd target from the normalized command
    cd_targets=$(echo "$NORMALIZED" | grep -oE '(cd|pushd)\s+[^;&|]+' || true)
    while IFS= read -r entry; do
      [[ -z "$entry" ]] && continue
      DIR_TARGET=$(echo "$entry" | sed 's/^[a-z]*[[:space:]]*//' | sed 's/^["\x27]//;s/["\x27]$//' | sed 's/[[:space:]]*$//')

      # Resolve to absolute path
      if [[ "$DIR_TARGET" != /* ]]; then
        DIR_TARGET="$PWD/$DIR_TARGET"
      fi

      # Resolve symlinks for comparison (MEDIUM: symlink bypass)
      DIR_TARGET_REAL=$(cd "$DIR_TARGET" 2>/dev/null && pwd -P 2>/dev/null) || DIR_TARGET_REAL="$DIR_TARGET"

      if [[ ! "$DIR_TARGET_REAL" =~ ^${MY_WORKTREE_REAL}(/|$) ]]; then
        BLOCKED=1
        break
      fi
    done <<< "$cd_targets"

    if [[ "$BLOCKED" -eq 1 ]]; then
      echo "BLOCKED: Agent $AGENT_ID cannot cd/pushd outside worktree." >&2
      echo "Use 'git -C $ROOT ...' to operate on other paths." >&2
      exit 1
    fi
  fi

  # HIGH: spoofable git -C check removed — git -C is safe because it only
  # affects the git command itself, not the shell's working directory.
  # The cd/pushd check above already handles actual directory changes.

  # Block push to main from agent worktree
  if cmd_matches '(^|;|&&|\|\|)\s*git\s+(-C\s+[^\s;|]+\s+)?push(\s|$).*\bmain\b'; then
    echo "BLOCKED: Agent $AGENT_ID cannot push to main." >&2
    echo "Commit to your branch (agents/$AGENT_ID), then use: maw merge $AGENT_ID" >&2
    exit 1
  fi
fi

# === DANGEROUS PATTERNS ===

# HIGH: bypassable rm -rf regex — isolate the rm invocation, then check
# independently for a recursive flag and a force flag, in any order,
# combined or separate, short or long form (rm -rf, -fr, -r -f, -Rf,
# --recursive --force, etc.)
RM_SEGMENT=$(echo "$NORMALIZED" | grep -oE '(^|;|&&|\|\|)[[:space:]]*rm[[:space:]]+[^;&|]*' | head -1) || true
if [[ -n "$RM_SEGMENT" ]]; then
  RM_HAS_R=0
  RM_HAS_F=0
  echo "$RM_SEGMENT" | grep -qE -- '(^|[[:space:]])-[a-zA-Z]*[rR][a-zA-Z]*([[:space:]]|$)|--recursive' && RM_HAS_R=1
  echo "$RM_SEGMENT" | grep -qE -- '(^|[[:space:]])-[a-zA-Z]*[fF][a-zA-Z]*([[:space:]]|$)|--force' && RM_HAS_F=1
  if [[ "$RM_HAS_R" -eq 1 && "$RM_HAS_F" -eq 1 ]]; then
    echo "BLOCKED: rm -rf not allowed." >&2
    echo "Use: mv <path> /tmp/trash_\$(date +%Y%m%d_%H%M%S)_\$(basename <path>)" >&2
    echo "Recovery: ls /tmp/trash_*" >&2
    exit 1
  fi
fi

# MEDIUM: -f false positives on -filter/-follow/-file — use word-boundary-aware match
# Only block -f / --force as standalone flags (preceded by whitespace or start-of-flag-group)
if cmd_matches '(^|;|&&|\|\|)\s*(git|npm|yarn|pnpm)\s+[^;&|]*(\s-f(\s|$|[^a-zA-Z])|--force(\s|$))'; then
  echo "BLOCKED: Force flags not allowed. Use safe alternatives." >&2
  exit 1
fi

# Block reset --hard
if cmd_matches '(^|;|&&|\|\|)\s*git\s+reset\s+[^;&|]*--hard'; then
  echo "BLOCKED: git reset --hard not allowed." >&2
  exit 1
fi

# Block git commit --amend
if cmd_matches '(^|;|&&|\|\|)\s*git\s+commit\s+[^;&|]*--amend'; then
  echo "BLOCKED: Never use --amend in multi-agent setup. Creates hash divergence." >&2
  exit 1
fi

# gh pr merge - allowed (user can merge PRs when ready)
# Previously blocked, now permitted per user request 2025-12-30

exit 0
