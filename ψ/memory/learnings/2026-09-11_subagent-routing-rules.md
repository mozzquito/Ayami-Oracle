# Sub-agent routing rules: zcode / agy / grok

Source: มอสขอให้ทำ routing rule จริงหลัง zcode+agy research พบว่า "model routing แบบมีกฎ" คือสิ่งเดียวที่คุ้มลงมือทำตอนนี้ (session 2026-09-11) — อิงจากประวัติจริงใน `session-metrics.md` + skill docs ของแต่ละตัว ไม่ใช่แค่ทฤษฎี

## กฎการเลือก (ตามชนิดงาน)

| ชนิดงาน | ส่งใครก่อน | เหตุผล/ข้อควรระวัง |
|---|---|---|
| Second opinion / review โค้ด ทั่วไป | **agy** `--mode plan` | เร็ว, เลือก model ได้ (`agy models`); **แต่ต้อง verify ด้วย `git diff` เสมอ** — พบ 2 ครั้งแล้วที่ agy เขียนไฟล์จริงทั้งที่สั่ง `--mode plan` (2026-09-11) |
| Deep review / architecture critique | **agy** `--model gemini-3.1-pro-high` | reasoning depth สูงกว่า flash tier |
| Quick sanity check ไฟล์เดียว / bulk sweep หลายไฟล์ | **agy** `--model gemini-3.6-flash-high` (หรือ `3.5-flash-low` ถ้าจำนวนเยอะ) | ถูก เร็ว พอสำหรับงาน stake ต่ำ |
| งาน implement/scope เฉพาะที่ต้องเขียนไฟล์จริงใน `--cwd` ที่กำหนด | **zcode** | ให้ scope ชัดเจนต่อ instance; **คาดเผื่อ Z.ai backend ล่ม** (524 timeout/rate-limit เกิดซ้ำหลายครั้งในประวัติ) และตอบช้า (~10min เคยเกิดซ้ำ) — มี agy เป็น fallback พร้อมสลับทันทีถ้า zcode ค้าง/fail ไม่ต้อง retry ซ้ำ task เดิมกับ zcode ที่เพิ่งพังแบบเดียวกัน |
| งานต้องการ web search/research จริงจัง (citation, แหล่งข่าวสด) | **agy หรือ zcode ก่อน** (ทั้งคู่ค้นเน็ตได้จริง ยืนยันแล้ว 2026-09-11) — **grok คือตัวที่ออกแบบมาสำหรับสิ่งนี้แต่ยังใช้ไม่ได้จนกว่ามอสจะตั้ง `XAI_API_KEY`** | grok มี `web_fetch`/`web_search` (Tavily) โดยตรงในตัว เหมาะสุดเมื่อพร้อมใช้ |
| งาน audio/video (transcribe ฯลฯ) | **ไม่ส่งให้ agy/zcode** — ใช้ local `whisper-cpp`/`mlx_whisper` โดยตรง | agy เคย fail 2 ครั้งบนงาน audio (permission-denied headless, self-directed model download timeout) — ประวัติยืนยันแล้ว |
| ทุกกรณี ไม่ว่าใครก็ตาม | จำกัด output ในprompt เสมอ (bullet/บรรทัด) | ตาม `2026-09-11_agent-token-efficiency-playbook.md` |

## หลักคิดเบื้องหลัง

- **agy = default ตัวแรกสำหรับงาน review/research** (เร็ว, multi-model, แต่ต้อง verify diff เพราะ plan-mode ไม่ 100% read-only จริง)
- **zcode = ตัวเลือกเมื่อรู้ scope ชัดและต้องเขียนไฟล์จริง** แต่ต้องมี fallback พร้อมเสมอเพราะ backend ไม่เสถียร
- **grok = ยังเป็น placeholder** จนกว่าจะมี API key — ครั้งหน้าที่ต้องการ web research ให้ถามมอสว่าพร้อมตั้ง key หรือยัง ก่อนจะ default ไป agy/zcode แทน
