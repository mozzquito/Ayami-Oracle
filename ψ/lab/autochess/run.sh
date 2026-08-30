#!/bin/bash
# รัน Auto Chess Assistant
cd "$(dirname "$0")"

if [ ! -d .venv ]; then
  echo "❌ ยังไม่ได้ setup — รัน ./setup.sh ก่อน"
  exit 1
fi

MODE="${1:-assist}"
case "$MODE" in
  calibrate) ./.venv/bin/python -m app.main --calibrate ;;
  learn)     ./.venv/bin/python -m app.main --learn ;;
  assist)    ./.venv/bin/python -m app.main ;;
  *) echo "วิธีใช้: ./run.sh [calibrate|learn|assist]"; exit 1 ;;
esac
