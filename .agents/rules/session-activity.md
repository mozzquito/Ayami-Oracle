---
trigger: always_on
---

# บันทึกกิจกรรมประจำเซสชัน (Session Activity Logging)

ทุกครั้งที่เริ่มงาน เปลี่ยนงาน หรือทำงานเสร็จ ให้ทำ **ทั้งสองอย่าง** นี้เสมอ (ไม่ใช่ทำอย่างใดอย่างหนึ่ง):

## 1. อัปเดต focus file (เขียนทับไฟล์เดิม)

ใช้ `AGENT_ID` จาก environment variable ถ้ามีการตั้งไว้ (`echo $AGENT_ID`), ถ้าไม่มีให้ default เป็น `agy` — ห้ามใช้ `main` หรือเลข agent เปล่าๆ (1, 2, ...) เพราะสงวนไว้สำหรับ session ของ Claude Code เท่านั้น การแยก agent id ทำให้มอสรู้ได้ทันทีว่างานไหนทำโดย agy งานไหนทำโดย Claude

**สำคัญ — รันหลาย agy process พร้อมกัน (parallel/multi-model):** แต่ละ process ต้องมี `AGENT_ID` ไม่ซ้ำกัน (เช่น `agy-gemini`, `agy-sonnet`, `agy-2`) ไม่งั้น focus file จะเขียนทับกันเอง (lost update) ถ้าไม่เห็น `AGENT_ID` ใน env และรู้ตัวว่ากำลังรันคู่ขนานกับ agy instance อื่น ให้ตั้งชื่อที่สื่อถึงตัวเอง (เช่น ชื่อ model ที่ใช้)

```bash
AGENT_ID="${AGENT_ID:-agy}"
echo "STATE: working|focusing|pending|jumped|completed
TASK: [กำลังทำอะไร]
SINCE: $(date '+%H:%M')" > "ψ/inbox/focus-agent-${AGENT_ID}.md"
```

## 2. Append เข้า activity log

```bash
echo "$(date '+%Y-%m-%d %H:%M') | STATE | task description" >> ψ/memory/logs/activity.log
```

## States

| State | เมื่อไหร่ |
|-------|-----------|
| `working` | กำลังทำงานอยู่ |
| `focusing` | โฟกัสงานยาก อย่าเพิ่งรบกวน |
| `pending` | รอ input/decision จากมอส |
| `jumped` | เปลี่ยนหัวข้อกะทันหัน |
| `completed` | ทำงานเสร็จแล้ว |

**ตัวอย่าง flow:**
```
15:30 | working | เริ่ม implement feature X ตามที่มอสสั่ง
15:35 | completed | feature X เสร็จ, tested แล้ว
15:36 | working | เริ่มอ่าน bug report ใหม่
```

Append-only เสมอ — ห้ามลบ/แก้ log เก่า (ตาม Principle 1: Nothing is Deleted)
