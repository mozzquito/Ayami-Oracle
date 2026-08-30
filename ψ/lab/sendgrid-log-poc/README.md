# sendgrid-log-poc

POC: เก็บ SendGrid email event log (delivered/bounce/open/click ฯลฯ) ให้อยู่ได้นานกว่า retention เดิมของ SendGrid (สูงสุด 30 วันตามแผน ไม่ถึง 180 วัน) โดยรับผ่าน Event Webhook แล้วเก็บลง SQLite local — ไม่ใช้ AWS

คู่มือแบบละเอียดพร้อมเหตุผลการเลือกแต่ละขั้น: ดู Artifact "SendGrid Log Capture" ที่ publish ไว้ในเซสชันที่สร้างโปรเจคนี้

## Setup

```bash
bun install
cp .env.example .env
# ใส่ SENDGRID_API_KEY และ SENDGRID_WEBHOOK_PUBLIC_KEY ใน .env เอง (ไม่ commit)
```

## รัน

```bash
bun run dev          # เปิด local server รับ webhook ที่ :4000
ngrok http 4000       # แยก terminal อีกอัน — เปิด tunnel ให้ SendGrid ยิงเข้ามาได้
```

เอา URL จาก ngrok ไปตั้งที่ SendGrid → Settings → Mail Settings → Event Webhook พร้อมเปิด "Signed Event Webhook Requests" แล้ว copy public key มาใส่ `.env`

## ตรวจข้อมูลที่เก็บ

```bash
bun run query
```

## ขั้นต่อไป (production)

- ngrok URL ไม่ถาวร ต้องย้ายไป host จริงถ้าจะรันต่อเนื่อง
- SQLite ไฟล์เดียวไม่มี backup — ต้องมี backup policy ก่อนใช้จริงที่ ~450,000 อีเมล/เดือน
- ยังไม่มี retry/DLQ ถ้า server ล่มระหว่างรับ event
