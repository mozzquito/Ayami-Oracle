#!/bin/bash
# Auto Chess Assistant — setup ครั้งแรก (สำหรับ macOS)
set -e
cd "$(dirname "$0")"

echo "==> ตรวจ Homebrew"
if ! command -v brew &>/dev/null; then
  echo "❌ ไม่พบ Homebrew — ติดตั้งก่อน: https://brew.sh"
  exit 1
fi

echo "==> ติดตั้ง adb (android-platform-tools) และ tesseract ถ้ายังไม่มี"
command -v adb &>/dev/null || brew install --cask android-platform-tools
command -v tesseract &>/dev/null || brew install tesseract

echo "==> สร้าง Python virtual environment"
python3 -m venv .venv
./.venv/bin/pip install --upgrade pip
./.venv/bin/pip install -r requirements.txt

echo ""
echo "✅ Setup เสร็จแล้ว! ขั้นต่อไป:"
echo "  1. ต่อมือถือ Android ด้วยสาย USB และเปิด USB Debugging"
echo "  2. ยืนยัน 'Allow USB debugging' บนมือถือ"
echo "  3. รัน: ./run.sh calibrate   (ตั้งค่าตำแหน่ง shop/board ครั้งแรก)"
