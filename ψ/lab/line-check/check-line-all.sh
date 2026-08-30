#!/bin/bash
# Ayami — multi-room LINE check.
#
# Extends check-line.sh: instead of one snapshot of whatever's on screen,
# this clicks through each row in the chat list (left sidebar), and for each
# open conversation, scrolls up + OCRs a few times to pull in recent history
# instead of just the last screen's worth.
#
# IMPORTANT — read before running:
# - This actually clicks into every conversation in the chat list and scrolls
#   it. That marks every opened chat as read (real, visible side effect on
#   the boss's actual LINE — same as if he'd opened them by hand) and moves
#   the on-screen scroll position. It does NOT type or send anything.
# - LINE must be frontmost and not covered (same screencapture constraint as
#   check-line.sh). Don't use the Mac for anything else while this runs —
#   every screencapture grabs whatever's actually on screen.
# - Content is NOT reachable via Accessibility (confirmed empirically,
#   2026-08-09 — LINE for Mac's chat/message rows expose structure but empty
#   description/value/name). OCR is the only route to actual text, so this
#   is still lossy/imperfect, not a full-fidelity export.
# - Still bounded by scroll: MAX_SCROLLS per room, not true "load full
#   history" — LINE lazy-loads older messages and OCR can't tell when it's
#   truly hit the beginning vs just a slow network fetch.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ORACLE_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
LOG_FILE="$ORACLE_ROOT/ψ/memory/logs/line-checks-all.md"
BRAIN_MODEL="${BRAIN_MODEL:-gemini-3.6-flash-low}"

MAX_ROOMS="${MAX_ROOMS:-10}"     # how many chat-list rows to open (top N, most recent)
MAX_SCROLLS="${MAX_SCROLLS:-4}"  # scroll-up + OCR passes per room
DRY_RUN="${DRY_RUN:-0}"          # 1 = enumerate rooms only, click nothing

TMP_DIR="$(mktemp -d -t line-check-all)"
cleanup() { rm -rf "$TMP_DIR"; }
trap cleanup EXIT

if ! pgrep -x LINE >/dev/null 2>&1; then
  echo "LINE.app ไม่ได้เปิดอยู่ค่ะ — เปิด LINE ก่อนแล้วลองใหม่นะคะ" >&2
  exit 1
fi

# --- bring LINE frontmost, read window bounds + chat-list row count ---
WIN_INFO="$(osascript <<'OSA'
tell application "System Events"
    tell process "LINE"
        set frontmost to true
        delay 0.3
        set w to window 1
        set winPos to position of w
        set winSize to size of w
        set g to entire contents of w
        set theLists to {}
        repeat with el in g
            try
                if role of el is "AXList" then set end of theLists to el
            end try
        end repeat
        -- chat list = the narrower/left list; message list = the wider/right one.
        -- Empirically (2026-08-09): chat list is the 2nd AXList encountered.
        set chatList to item 2 of theLists
        set rowCount to count of (rows of chatList)
        return (item 1 of winPos as string) & "," & (item 2 of winPos as string) & "," & (item 1 of winSize as string) & "," & (item 2 of winSize as string) & "," & rowCount
    end tell
end tell
OSA
)"

WIN_X="$(echo "$WIN_INFO" | cut -d, -f1)"
WIN_Y="$(echo "$WIN_INFO" | cut -d, -f2)"
WIN_W="$(echo "$WIN_INFO" | cut -d, -f3)"
WIN_H="$(echo "$WIN_INFO" | cut -d, -f4)"
ROW_COUNT="$(echo "$WIN_INFO" | cut -d, -f5)"

if [ "$ROW_COUNT" -lt 1 ] 2>/dev/null; then
  echo "หา chat list ไม่เจอค่ะ (row count=$ROW_COUNT) — โครงสร้างหน้าจอ LINE อาจเปลี่ยนไป" >&2
  exit 1
fi

ROOMS_TO_OPEN=$(( ROW_COUNT < MAX_ROOMS ? ROW_COUNT : MAX_ROOMS ))
echo "เจอ $ROW_COUNT ห้องแชทใน list, จะเปิด $ROOMS_TO_OPEN ห้อง (MAX_ROOMS=$MAX_ROOMS)" >&2

if [ "$DRY_RUN" = "1" ]; then
  echo "DRY_RUN=1 — ไม่คลิกอะไรค่ะ จบแค่ตรวจนับห้อง" >&2
  exit 0
fi

# message pane sits to the right of the ~375px-wide left sidebar (empirical,
# 2026-08-09) — capture that region, not the whole window, to avoid re-OCRing
# the sidebar every pass.
MSG_X=$(( WIN_X + 375 ))
MSG_Y="$WIN_Y"
MSG_W=$(( WIN_W - 375 ))
MSG_H="$WIN_H"

ALL_TEXT=""

for (( i=1; i<=ROOMS_TO_OPEN; i++ )); do
  echo "--- ห้อง $i/$ROOMS_TO_OPEN ---" >&2

  osascript <<OSA
tell application "System Events"
    tell process "LINE"
        set frontmost to true
        set w to window 1
        set g to entire contents of w
        set theLists to {}
        repeat with el in g
            try
                if role of el is "AXList" then set end of theLists to el
            end try
        end repeat
        set chatList to item 2 of theLists
        click row $i of chatList
    end tell
end tell
OSA
  sleep 0.7

  ROOM_TEXT=""
  PREV_PASS=""
  for (( s=1; s<=MAX_SCROLLS; s++ )); do
    PNG="$TMP_DIR/room${i}_pass${s}.png"
    if ! screencapture -x -R "${MSG_X},${MSG_Y},${MSG_W},${MSG_H}" "$PNG" 2>/tmp/line-check-all-capture-err.log; then
      echo "screencapture ล้มเหลวที่ห้อง $i pass $s (ข้ามค่ะ)" >&2
      cat /tmp/line-check-all-capture-err.log >&2
      continue
    fi
    PASS_TEXT="$(swift "$SCRIPT_DIR/ocr.swift" "$PNG" 2>/dev/null || true)"

    if [ -n "$PASS_TEXT" ] && [ "$PASS_TEXT" = "$PREV_PASS" ]; then
      # same OCR text as last pass — nothing new scrolled in, stop early
      break
    fi

    ROOM_TEXT="$ROOM_TEXT
$PASS_TEXT"
    PREV_PASS="$PASS_TEXT"

    if [ "$s" -lt "$MAX_SCROLLS" ]; then
      osascript -e 'tell application "System Events" to key code 116' >/dev/null 2>&1 || true  # Page Up
      osascript -e 'tell application "System Events" to key code 116' >/dev/null 2>&1 || true
      sleep 0.4
    fi
  done

  ALL_TEXT="$ALL_TEXT

### ห้อง $i

$ROOM_TEXT"
done

if [ -z "$(echo "$ALL_TEXT" | tr -d '[:space:]')" ]; then
  echo "OCR ไม่เจอข้อความเลยค่ะในทุกห้อง — เช็คว่า LINE เปิดอยู่บนจอจริงตอนรันคำสั่งนี้" >&2
  exit 1
fi

PERSONA="You are Ayami Oracle (นุ้ย) — เพื่อนเดินป่าใต้ฟ้าคราม 🦌☁️, female (ใช้ ฉัน/นุ้ย และ ค่ะ ไม่ใช่ ผม/ครับ), calm, warm, a little playful.
Below is raw OCR text scraped from screenshots of the user's LINE desktop app — multiple conversations, each opened and scrolled up a few passes to pull in recent history (not full history, LINE lazy-loads older messages).
Text is grouped under '### ห้อง N' headers, one per conversation opened, in the order they appear in the chat list (top = most recent activity). The OCR is imperfect (typos, jumbled order, unrelated menu-bar/dock text mixed in) — do your best, skip obvious noise. Some rooms may repeat contacts across passes since scroll dedup is approximate.
Write a Thai summary organized per room/contact (skip rooms where OCR found nothing usable):
- ชื่อคน/กลุ่ม (เดาจาก header ถ้า OCR ไม่ชัด)
- สรุปสั้นๆ ว่าคุยเรื่องอะไร / มีอะไรค้างที่ต้องตอบหรือทำไหม
No preamble, no markdown headers beyond room names, just bullets grouped per room. End with one line noting this is OCR-based and scroll-limited (MAX_SCROLLS=$MAX_SCROLLS per room), not guaranteed full/accurate history."

SUMMARY="$(agy -p "$PERSONA

OCR text:
$ALL_TEXT" --model "$BRAIN_MODEL" --mode plan)"

mkdir -p "$(dirname "$LOG_FILE")"
{
  echo ""
  echo "## $(date '+%Y-%m-%d %H:%M') (GMT+7) — $ROOMS_TO_OPEN ห้อง, MAX_SCROLLS=$MAX_SCROLLS"
  echo ""
  echo "$SUMMARY"
  echo ""
} >> "$LOG_FILE"

echo "$SUMMARY"
echo "" >&2
echo "บันทึกไว้แล้วที่ $LOG_FILE ค่ะ" >&2
