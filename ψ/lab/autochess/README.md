# Auto Chess Assistant 🦌

ผู้ช่วยแนะนำสำหรับ **Auto Chess Mobile (Drodo)** — อ่านจอมือถือ Android แล้วบอกว่า
ควร **ซื้อ/ข้าม** piece ไหน (แค่แนะนำ **ไม่ใช่บอท** ไม่แตะแทน ลดความเสี่ยงโดนแบน)

## สิ่งที่ต้องมี
- Mac + มือถือ Android ต่อสาย USB เปิด **USB Debugging**
  (Settings → About → กด Build number 7 ครั้ง → Developer options → USB Debugging)

## ติดตั้ง (ครั้งเดียว)
```bash
./setup.sh
```

## การใช้งาน — 3 ขั้นตอน

### 1. Calibrate ตำแหน่ง (ครั้งแรกเท่านั้น / เปลี่ยนเครื่อง)
เปิดเกมเข้าหน้าร้านแล้วรัน:
```bash
./run.sh calibrate
```
จะมีหน้าต่างรูปภาพเด้งขึ้น ให้ **ลากกรอบ** ทีละบริเวณ: shop (แถบร้าน 5 ใบ),
board (กระดาน), bench (ม้านั่งสำรอง), gold (ตัวเลขเงิน) — กด ENTER ยืนยันทีละอัน

### 2. บันทึกรูป piece (ครั้งแรกเท่านั้น)
```bash
./run.sh learn
```
ในเกม ให้ piece ที่ต้องการโผล่ใน shop/board แล้วลากกรอบคลุมตัวมัน
พิมพ์ชื่อ (เช่น `red_axe`) — ทำเท่าที่ต้องการ (เริ่มแค่ 10-20 ตัวก็ใช้ได้)
รูปจะเก็บใน `templates/`

### 3. รันตัวช่วย
```bash
./run.sh
```
เข้าเกมปกติ — terminal จะอัปเดตคำแนะนำทุก 2 วินาที เช่น
```
💰 23g | Board: 2xbeast, 2xwarrior | Comp ใกล้เคียง: Beast Warrior
ซื้อ: Red Axe (slot 1, conf 0.91) — คะแนน 13 ✅
ข้าม: Pirate Captain (slot 3, conf 0.82) — คะแนน 3 ❌
```

## เพิ่ม piece ใหม่
1. เพิ่ม entry ใน `app/pieces.py` (ชื่อ, cost, species, class)
2. รัน `./run.sh learn` บันทึกรูปของมัน

## แก้ปัญหา
| อาการ | วิธีแก้ |
|---|---|
| "ไม่พบมือถือ" | กดยืนยัน Allow USB debugging บนมือถือ, ลอง `adb devices` |
| ตรวจ piece ไม่แม่น | ลบ `templates/<ชื่อ>.png` แล้ว `./run.sh learn` ใหม่ ให้กรอบคลุมแค่ตัว piece |
| อ่านเงินผิด | รัน `./run.sh calibrate` ตั้งกรอบ gold ให้คลุมแค่ตัวเลข |

## ⚠️ ข้อจำกัด
- เครื่องมือนี้ **อ่านจอเท่านั้น** ไม่ส่ง input ใด ๆ เข้าเกม — แต่การใช้เครื่องมือช่วย
  อาจขัดเงื่อนไขบริการของ Drodo โปรดใช้พิจารณาและรับความเสี่ยงเอง
- MVP: นับ piece บน board ยังเป็น best-effort (detect ทีละ best match ต่อ template)
