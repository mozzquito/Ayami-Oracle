#!/usr/bin/env bash
# apply-moves.sh — mechanical executor for /triage
#
# Reads JSON-Lines on stdin, one move request per line:
#   {"src":"ψ/inbox/foo.md","dst":"ψ/lab/concepts/007-foo.md","index_file":"ψ/lab/concepts/INDEX.md","index_row":"| 007 | ... |"}
#
# index_file / index_row are optional (omit or null when the destination has no INDEX.md convention).
# Pipe characters in index_row must already be escaped by the caller (\|) — this script does not touch table syntax.
#
# Does ONLY mechanical work: no classification, no judgment calls. Never aborts the whole
# batch on one item's failure — every line gets an independent result.
#
# Output: JSON-Lines on stdout, one result object per input line, same order:
#   {"src":"...","dst":"...","status":"moved","index_updated":true}
#   {"src":"...","dst":null,"status":"error","error":"src not found"}
#
# Order of operations per item (deliberate): INDEX.md is updated BEFORE the file is moved.
# If the move then fails, the src file is still sitting untouched in ψ/inbox — safe, self-healing
# on the next /triage run (still-present-in-inbox = still pending). The reverse order would risk a
# moved-but-unindexed file, which is a silent, harder-to-notice loss.
#
# Not safe for concurrent /triage runs (no locking on INDEX.md). Fine for this single-user repo.
#
# Exit code is always 0 once stdin is consumed, even if every item errored — per-item
# success/failure lives only in the JSON-Lines output, not the process exit code. Callers
# MUST read the output; don't gate on `$?`.

set -uo pipefail

ORACLE_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
cd "$ORACLE_ROOT" || exit 1

if ! command -v jq >/dev/null 2>&1; then
  echo '{"status":"error","error":"jq is required but not found on PATH"}'
  exit 1
fi

# resolve_dst <dst> — if dst exists, append -2, -3, ... before the extension until free.
resolve_dst() {
  local dst="$1"
  if [ ! -e "$dst" ]; then
    printf '%s' "$dst"
    return
  fi
  local dir base ext n candidate
  dir=$(dirname "$dst")
  base=$(basename "$dst")
  if [[ "$base" == *.* ]]; then
    ext=".${base##*.}"
    base="${base%.*}"
  else
    ext=""
  fi
  n=2
  while :; do
    candidate="$dir/${base}-${n}${ext}"
    if [ ! -e "$candidate" ]; then
      printf '%s' "$candidate"
      return
    fi
    n=$((n + 1))
  done
}

while IFS= read -r line || [ -n "$line" ]; do
  [ -z "$line" ] && continue

  src=$(printf '%s' "$line" | jq -r '.src // empty')
  dst_req=$(printf '%s' "$line" | jq -r '.dst // empty')
  index_file=$(printf '%s' "$line" | jq -r '.index_file // empty')
  index_row=$(printf '%s' "$line" | jq -r '.index_row // empty')

  if [ -z "$src" ] || [ -z "$dst_req" ]; then
    echo '{"status":"error","error":"missing src or dst","raw":'"$(printf '%s' "$line" | jq -c .)"'}'
    continue
  fi

  if [ ! -f "$src" ]; then
    printf '{"src":%s,"dst":null,"status":"error","error":"src not found"}\n' "$(printf '%s' "$src" | jq -R .)"
    continue
  fi

  dst=$(resolve_dst "$dst_req")

  if ! mkdir -p "$(dirname "$dst")" 2>/tmp/triage-mkdir-err; then
    err=$(cat /tmp/triage-mkdir-err); rm -f /tmp/triage-mkdir-err
    printf '{"src":%s,"dst":null,"status":"error","error":%s}\n' \
      "$(printf '%s' "$src" | jq -R .)" "$(printf 'mkdir failed: %s' "$err" | jq -R .)"
    continue
  fi
  rm -f /tmp/triage-mkdir-err

  index_updated=false
  if [ -n "$index_file" ] && [ "$index_file" != "null" ] && [ -n "$index_row" ] && [ "$index_row" != "null" ]; then
    tmp_index=$(mktemp)
    if [ -f "$index_file" ]; then
      cp "$index_file" "$tmp_index"
      # guard against a missing trailing newline concatenating onto the last existing row
      if [ -s "$tmp_index" ] && [ -z "$(tail -c1 "$tmp_index")" ]; then :; else
        printf '\n' >> "$tmp_index"
      fi
    fi
    printf '%s\n' "$index_row" >> "$tmp_index"
    if mv "$tmp_index" "$index_file" 2>/tmp/triage-index-err; then
      index_updated=true
      git add "$index_file" 2>/dev/null || true
    else
      err=$(cat /tmp/triage-index-err); rm -f /tmp/triage-index-err "$tmp_index"
      printf '{"src":%s,"dst":null,"status":"error","error":%s}\n' \
        "$(printf '%s' "$src" | jq -R .)" "$(printf 'index update failed: %s' "$err" | jq -R .)"
      continue
    fi
  fi

  src_tracked=false
  git ls-files --error-unmatch "$src" >/dev/null 2>&1 && src_tracked=true
  dst_ignored=false
  git check-ignore -q "$dst" 2>/dev/null && dst_ignored=true

  if [ "$dst_ignored" = true ]; then
    # Destination pillar is intentionally gitignored (e.g. ψ/memory/logs/ — ephemeral).
    # Physical file is still preserved (Nothing is Deleted); it just leaves git's index.
    if [ "$src_tracked" = true ]; then
      move_err=$(mv "$src" "$dst" 2>&1 && git rm --cached -q "$src" 2>&1)
    else
      move_err=$(mv "$src" "$dst" 2>&1)
    fi
    move_status=$?
  elif [ "$src_tracked" = true ]; then
    move_err=$(git mv "$src" "$dst" 2>&1)
    move_status=$?
  else
    move_err=$(mv "$src" "$dst" 2>&1 && git add "$dst" 2>&1)
    move_status=$?
  fi

  if [ "$move_status" -ne 0 ]; then
    printf '{"src":%s,"dst":%s,"status":"error","error":%s,"index_updated":%s}\n' \
      "$(printf '%s' "$src" | jq -R .)" "$(printf '%s' "$dst" | jq -R .)" \
      "$(printf '%s' "$move_err" | jq -R .)" "$index_updated"
    continue
  fi

  printf '{"src":%s,"dst":%s,"status":"moved","index_updated":%s}\n' \
    "$(printf '%s' "$src" | jq -R .)" "$(printf '%s' "$dst" | jq -R .)" "$index_updated"

done
