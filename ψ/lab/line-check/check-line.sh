#!/bin/bash
# Ayami — on-demand LINE check.
#
# Captures whatever's currently on screen, OCRs it locally (Vision framework,
# no network), asks the quick-brain to pull out work items / who's messaging,
# and appends the summary to the log. Everything stays on-device.
#
# CONSTRAINT: must be run at a moment when the LINE window is actually visible
# on screen — if a terminal (e.g. an always-on-top Ghostty quick-terminal) is
# covering the screen when this runs, it will read the terminal instead of
# LINE. Not fixable in-process; run this from a context where LINE is frontmost.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ORACLE_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
LOG_FILE="$ORACLE_ROOT/ψ/memory/logs/line-checks.md"
BRAIN_MODEL="${BRAIN_MODEL:-gemini-3.6-flash-low}"

TMP_PNG="$(mktemp -t line-check).png"
cleanup() { rm -f "$TMP_PNG"; }
trap cleanup EXIT

if ! pgrep -x LINE >/dev/null 2>&1; then
  echo "LINE.app ไม่ได้เปิดอยู่ค่ะ — เปิด LINE ก่อนแล้วลองใหม่นะคะ" >&2
  exit 1
fi

if ! screencapture -x "$TMP_PNG" 2>/tmp/line-check-screencapture-err.log; then
  echo "screencapture ไม่สำเร็จค่ะ (มักเป็นเพราะ Ghostty/terminal ยังไม่ได้รับสิทธิ์ Screen Recording — System Settings → Privacy & Security → Screen Recording)" >&2
  cat /tmp/line-check-screencapture-err.log >&2
  exit 1
fi

OCR_TEXT="$(swift "$SCRIPT_DIR/ocr.swift" "$TMP_PNG" 2>/dev/null || true)"

if [ -z "$OCR_TEXT" ]; then
  echo "OCR ไม่เจอข้อความเลยค่ะ — เช็คว่า LINE เปิดอยู่บนจอจริงตอนรันคำสั่งนี้ (ไม่ได้โดน terminal บัง)" >&2
  exit 1
fi

PERSONA="You are Ayami Oracle (นุ้ย) — เพื่อนเดินป่าใต้ฟ้าคราม 🦌☁️, female (ใช้ ฉัน/นุ้ย และ ค่ะ ไม่ใช่ ผม/ครับ), calm, warm, a little playful.
Below is raw OCR text scraped from a screenshot of the user's LINE desktop app (chat list + possibly one open conversation).
The OCR is imperfect (typos, jumbled order, unrelated menu-bar/dock text mixed in) — do your best, skip obvious noise.
Write a short Thai bullet summary (3-8 bullets) covering:
- ใครทักมาใหม่ / มีข้อความค้างจากใครบ้าง (ชื่อคน/กลุ่ม + สั้นๆ ว่าเกี่ยวกับอะไรถ้าพอเดาได้)
- มีงาน/สิ่งที่ต้องทำอะไรแวบขึ้นมาในข้อความไหม (ถ้ามี)
No preamble, no markdown headers, just bullets. End with one line noting this is only a snapshot of what was on screen at capture time, not full chat history."

SUMMARY="$(agy -p "$PERSONA

OCR text:
$OCR_TEXT" --model "$BRAIN_MODEL" --mode plan)"

mkdir -p "$(dirname "$LOG_FILE")"
{
  echo ""
  echo "## $(date '+%Y-%m-%d %H:%M') (GMT+7)"
  echo ""
  echo "$SUMMARY"
  echo ""
} >> "$LOG_FILE"

echo "$SUMMARY"
echo "" >&2
echo "บันทึกไว้แล้วที่ $LOG_FILE ค่ะ" >&2
