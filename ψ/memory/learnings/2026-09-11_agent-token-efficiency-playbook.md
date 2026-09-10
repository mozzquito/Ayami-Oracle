# Agent token-efficiency playbook (zcode + agy consult)

Source: มอสขอเชื่อมต่อ Brain MCP แล้วให้ /zcode + /agy ออกความเห็นเรื่อง "พัฒนา Ayami ให้เก่งขึ้น + ใช้ token ฉลาดขึ้น" (session 2026-09-11). /grok ยังต่อไม่ได้ตอนนั้น — ไม่มี `XAI_API_KEY` ตั้งค่าไว้.

## Checklist (นำไปใช้จริงในทุก session)

- [ ] **ค้น Brain MCP / auto-memory ก่อนโหลดไฟล์ context เต็มไฟล์** (CLAUDE.md, session-metrics.md, ฯลฯ) — query แบบ on-demand แทนการอ่านทั้งไฟล์ตั้งแต่ต้น session
- [ ] **Tiered memory**: auto-memory เก็บแค่ index/state สั้นๆ (< ~1000 tokens) ส่วนของลึก/ยาวให้อยู่ใน Brain MCP แล้ว query เฉพาะตอนต้องใช้จริง
- [ ] **Sub-agent output contract**: ทุกครั้งที่ delegate ให้ zcode/agy/grok ต้องระบุ "จำกัดกี่ bullet / กี่บรรทัด" ใน prompt เสมอ — จุดที่ token รั่วมากสุดคือ output ยาวเกินจำเป็นจาก sub-agent
- [ ] **Orchestrator–Worker**: Ayami คิด/วางแผน/สรุป ส่วนงานอ่าน raw log หรือไฟล์ใหญ่ยกให้ agy/zcode ทำแล้วรับกลับแค่สรุป
- [ ] **`/distill` เป็นกิจวัตร ไม่ใช่ตามอารมณ์**: จบ bug ยากหรืองาน complex แต่ละครั้ง สกัด pattern เข้า Brain MCP หรือเขียน learning file ทันที ไม่รอสะสม
- [ ] **ระวัง context ที่โหลดอัตโนมัติทุก turn** (skill descriptions, memory index) ให้เล็กที่สุด — ยังไม่ลงมือแก้ทั่ว `.claude/skills/` เพราะเป็น shared family skill ecosystem, blast radius สูง (ดูหมายเหตุด้านล่าง)
- [ ] **เก็บ metric การใช้ tool จริง** (จำนวนครั้งเรียก MCP / delegate / อ่านไฟล์ใหญ่ต่อ session) — ยังไม่ทำ เพราะ `session-metrics.md` ปัจจุบันเป็น prose format ที่ใช้มา 68+ session แล้ว การแทรก column ใหม่กลางทางจะทำลายความสม่ำเสมอ; ถ้าจะทำจริงควรแยกเป็นไฟล์ log ใหม่ต่างหาก

## หมายเหตุจากการสำรวจจริงระหว่างวางแผนนี้ (ตัวอย่าง live)

อ่าน `ψ/memory/learnings/session-metrics.md` ทั้งไฟล์ระหว่าง session นี้ กิน ~42k tokens ในการเรียกเดียว (135 บรรทัด, prose ยาวทุก cell ต่อ session) — เป็นตัวอย่างจริงของปัญหา "โหลด context ใหญ่เกินจำเป็นตอนไม่รู้ว่าต้องการแค่ไหน" ที่ playbook นี้พยายามแก้ บทเรียน: ก่อนอ่านไฟล์ log/metrics สะสมยาว ให้ลอง `tail`/`grep`/query เฉพาะช่วงที่ต้องใช้ก่อน แทนการ Read เต็มไฟล์

## ของที่ตั้งใจไม่ทำตอนนี้ (scope decision)

- ไม่ prune skill description ทั่ว `.claude/skills/` — ระบบ soul-sync ของ Oracle family ดูแลกลไกนี้อยู่ แก้เองฝ่ายเดียวเสี่ยงชนกัน
- ไม่ปรับโครงสร้าง `session-metrics.md` ให้มี column ตัวเลข — นอก scope, จะทำเป็นงานแยกถ้ามอสขอ
