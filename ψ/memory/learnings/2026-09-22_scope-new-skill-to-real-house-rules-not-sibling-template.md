---
pattern: when asked to add a new tool/skill "into the same category as A, B, C", check the new thing's actual rules/constraints before copying A/B/C's template — it may not share their nature
date: 2026-09-22
source: "rrr: ayami-oracle"
concepts: [skills, delegation, house-rules, jev, typesafe]
---

# Scope a new skill to its real house rules, not a sibling's template

## Context

มอสขอเพิ่ม `/jev` เข้าไปในหมวด "เรียกใช้ AI ตัวอื่น" ข้าง `/zcode`, `/agy`, `/grok` — สามตัวนั้นเป็น
coding agent CLI ที่รับ open-ended task ทั่วไป (`-p "<prompt>" --cwd <path>`). ถ้า copy pattern มาตรงๆ
`/jev` จะกลายเป็น "delegate ทั่วไปให้ jev" ซึ่งผิดธรรมชาติของมันโดยสิ้นเชิง

## What we found

Jev (TypeSafe System One) มี prototype อยู่แล้วที่ `ψ/lab/jev-gate/` พร้อม README ที่เขียนกฎไว้ชัด:
- เป็น narrow typed decision API (Noul/Choice/Score) ไม่ใช่ agent ที่มี tool loop
- score ไม่ deterministic (±0.03–0.04) — ห้ามอ่าน single run เป็นค่าตายตัว
- **ต้องใช้คู่กับ `/zcode` + `/agy` เสมอ** ก่อนเปลี่ยน threshold, ผูกเข้า hook/bot, หรือ act ตามผล flagged/review
- ยัง prototype อยู่ branch แยก ไม่ merge เข้า main ไม่ wire เข้าอะไรทั้งนั้น
- data rule เข้มกว่า zcode/agy (ห้าม PII/eVisa เด็ดขาด เพราะ retention ของ TypeSafe ไม่ชัด)

ถ้าไม่เช็คตรงนี้ก่อน จะได้ skill ที่บอก user ผิดว่า jev ใช้แทน/คู่ขนานกับ zcode ได้อย่างอิสระ ทั้งที่ README
บอกชัดว่ามันต้อง "ไปด้วยกันเสมอ ห้ามเป็นเสียงเดียว"

## Rule

เมื่อ user ขอเพิ่มสิ่งใหม่ "เข้าไปในหมวดเดียวกับของเดิม A/B/C" — ก่อนเขียน:
1. หา source of truth ของสิ่งใหม่ (README, prototype code, memory file) ถ้ามีอยู่แล้วในโปรเจกต์
2. เทียบธรรมชาติกับ A/B/C จริงๆ ไม่ใช่แค่ "อยู่หมวดเดียวกัน = เขียนเหมือนกัน"
3. ถ้าสิ่งใหม่มีกฎการใช้ที่มีอยู่แล้ว (เช่น README บังคับให้ใช้คู่กับตัวอื่น) ให้ skill ใหม่ผูกกฎนั้นไว้ตรงๆ
   ไม่ใช่แค่ลิงก์ไปอ่านเอง — เพราะ skill description คือจุดแรกที่ agent ตัวอื่น (หรือ Ayami ในอนาคต) จะเห็น

## How to apply

Trigger เมื่อ: request รูปแบบ "เพิ่ม X เข้าไปในกลุ่ม/หมวดเดียวกับ Y" และ X เป็นของใหม่ที่ยังไม่เคยมี skill —
เช็คของจริงก่อนเขียนเสมอ แม้ว่า pattern ของ Y จะดู reusable ก็ตาม
