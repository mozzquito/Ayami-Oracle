# Auto Chess (Drodo) Assistant — MVP

โปรเจกต์ใหม่ใน `ψ/lab/autochess/` — เครื่องมือผู้ช่วยแนะนำบน Mac อ่านจอมือถือ Android (USB ADB) และแนะนำว่าควรซื้อ/ขาย piece อะไร **ไม่แตะแทน** (ไม่ใช่บอท ลดความเสี่ยงโดนแบน)

## เครื่องมือที่ต้องติดตั้ง
- `brew install android-platform-tools` (adb + screencap)
- Python 3 + venv: `opencv-python`, `pytesseract` (+ `brew install tesseract` สำหรับอ่านตัวเลขเงิน/เลเวล)

## โครงสร้าง
```
autochess/
├── README.md               # วิธีใช้แบบทีละขั้น (สำหรับคนไม่รู้ Python)
├── requirements.txt
├── setup.sh                # setup อัตโนมัติ: venv + install + ตรวจ adb
├── run.sh                  # รันตัวช่วย (ทำ source venv ให้)
└── app/
    ├── capture.py          # ADB screencap → numpy image (ทุก 1-2 วิ)
    ├── pieces.py           # ฐานข้อมูล piece: ชื่อ, cost, species, class
    ├── detect.py           # Template matching หา piece ใน shop/board/bench
    ├── ocr.py              # OCR อ่านเงิน, เลเวล, HP (เฉพาะตัวเลข)
    ├── advisor.py          # Logic แนะนำ: ให้ shop 5 ใบ + board ปัจจุบัน
    │                       # → คะแนนแต่ละใบ (synergy ต่อ piece, จับคู่ 2 ดาว, เศษ piece)
    └── main.py             # Loop หลัก + พิมพ์คำแนะนำลง terminal
└── templates/              # รูป piece ตัวอย่าง (crop จากจอจริงเก็บไว้ทีละตัว)
```

## วิธีทำงาน
1. **Calibration ครั้งแรก**: สคริปต์จับภาพจอเกม → ผู้ใช้ crop บริเวณ shop/board หนึ่งครั้ง → เก็บพิกัดเป็น config (จอเดียวกันใช้ซ้ำได้)
2. **เก็บ template**: โหมดพิเศษ `python -m app.main --learn` ให้คลิกบนรูปเพื่อบันทึกรูป piece แต่ละตัวเข้า `templates/` (ทำครั้งเดียวต่อ piece ~60 ตัว แต่ MVP เริ่มจาก piece ยอดนิยม ~15-20 ตัวก่อน)
3. **Runtime loop**: capture → detect pieces ใน shop 5 ช่อง + board → OCR เงิน → advisor คำนวณ → พิมพ์เช่น
   ```
   💰 23g | Lv.7 | Board: 3x Beast, 2x Warrior
   ซื้อ: Red Axe (จับ2ดาวได้) ✅, Poison Master ✅
   ข้าม: Pirate Captain ❌ (ไม่เข้า comp)
   ```

## Advisor logic (MVP)
คะแนนต่อ piece ใน shop = f(
- จับคู่ piece บน board/bench เพื่อรวมเป็น 2 ดาว (น้ำหนักสูงสุด)
- เพิ่ม synergy ที่ยังไม่ครบ threshold (3/6)
- ตาราง meta comp 5-6 อัน (hardcode จาก meta ปัจจุบัน)
) → แนะนำซื้อเฉพาะที่คะแนนเกิน threshold และเงินพอ

## ขั้นตอน implement
1. `setup.sh` + capture.py + ทดสอบจับภาพจากเครื่องจริง
2. Calibration + โหมด --learn เก็บ template
3. detect.py (opencv matchTemplate, threshold tuning)
4. pieces.py ฐานข้อมูล + advisor.py
5. main.py loop + README ภาษาไทย

## สิ่งที่ต้องมีจากคุณระหว่างทำ
- มือถือต่อ USB เปิด USB debugging เพื่อทดสอบจับภาพจริง
- ช่วย crop บันทึก template ครั้งแรก (สคริปต์จะนำทีละขั้น)

## นอกขอบเขต MVP
- แตะแทน (auto-play) — เสี่ยงโดนแบน
- รู้จำ piece ทั้งหมด ~60 ตัวตั้งแต่วันแรก (เริ่ม ~20 ตัว)
- วิเคราะห์ item/equipment