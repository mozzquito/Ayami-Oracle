# Langfuse vs Arize Phoenix — feasibility survey on this machine

Source: มอสขอสำรวจจริงจังว่า Langfuse/Arize Phoenix (พบจาก agy's round-2 research) ติดตั้งกับ setup เรา (Claude Code + zcode/agy/grok เป็น subprocess CLI แยก ไม่ได้เรียกผ่าน SDK) ได้จริงไหม — สรุปจากการค้นเน็ต + เช็ค local environment จริง (2026-09-11)

## สถาปัตยกรรมที่เราต้องเชื่อม

Claude Code เองเรียก Anthropic API ภายในตัว harness — ไม่มี SDK hook ให้ instrument ตรงๆ แต่ zcode/agy/grok ทั้งหมดถูกเรียกผ่าน `Bash` tool เป็น subprocess ที่เราคุมเต็มที่ → **จุดเชื่อมที่ทำได้จริงคือห่อ (wrap) การเรียก subprocess เหล่านี้ด้วย OTel span เอง** (manual instrumentation) ไม่ใช่ auto-instrument ผ่าน SDK ปกติ — ทั้ง Langfuse และ Phoenix รองรับ manual OTel ingestion แบบนี้ได้ ([Langfuse OTel endpoint](https://langfuse.com/docs/api-and-data-platform/features/public-api), [Phoenix OTel setup](https://arize.com/docs/phoenix/tracing/how-to-tracing/setup-tracing/setup-using-phoenix-otel)) — ทางที่ practical สุดคือทำ Claude Code hook (`PostToolUse` จับ Bash command ที่ match `zcode`/`agy`/`grok`) ยิง span ออกไปอัตโนมัติ ไม่ต้องพึ่งให้ Ayami จำเรียกเอง

## เช็ค local environment จริง (2026-09-11)

- Docker + Docker Compose: **มีอยู่แล้ว** (Docker 27.5.1, Compose 2.32.4)
- RAM รวมเครื่อง: **8 GB**
- RAM ว่างตอนเช็ค (`vm_stat`): **free ~268 MB**, inactive ~1.1 GB (reclaimable) → available จริงๆ ประมาณ ~1.4 GB ไม่ใช่ 8 GB
- ตรงกับ pattern ที่เคยเจอมาก่อนในโปรเจกต์ (session-metrics.md เคยบันทึก "severe memory pressure, ~104MB free" ตอนรัน ollama) — เครื่องนี้แน่นเรื่อง RAM เป็นปกติ ไม่ใช่ครั้งนี้ครั้งเดียว

## ผลสรุป

| | Langfuse (self-host) | Arize Phoenix (self-host) |
|---|---|---|
| Stack | Postgres + ClickHouse + Redis + MinIO + app (5+ container) | container เดียว (UI port 6006, OTel gRPC port 4317) |
| ความหนักบน RAM 8GB (free จริง ~1.4GB) | **ไม่แนะนำตอนนี้** — stack หนักเกินไป เสี่ยงเครื่องช้า/OOM ซ้ำรอยเดิม | เบากว่ามาก เป็นตัวเลือกที่เป็นไปได้จริงมากกว่า |
| ทางเลือกถ้าไม่อยาก self-host | Langfuse Cloud (free tier มี) — ข้าม resource เครื่องไปเลย | ยังไม่ชัดว่ามี hosted free-tier แบบเดียวกัน ต้องเช็คเพิ่ม |
| Ingestion path | OTel endpoint (legacy Ingestion API เลิกใช้ 16 พ.ย. 2026) | `arize-phoenix-otel` (Python/JS) — wrapper บาง เขียน span เองได้ตรงไปตรงมา |

## คำแนะนำ

**Arize Phoenix self-host คือตัวเลือกที่เป็นไปได้จริงมากกว่าบนเครื่องนี้** (container เดียว, เบา) แต่เครื่องมี RAM ว่างจริงจำกัดมาก (~1.4GB) — ควรทดสอบแบบจำกัด resource (`docker run --memory=512m`) และดูผลก่อนตัดสินใจรันถาวร ไม่ควรรันแบบไม่จำกัดในสภาพเครื่องตอนนี้

**Langfuse** แนะนำให้ใช้ทาง **Cloud free tier แทนการ self-host** ถ้ามอสสนใจตัวนี้เป็นพิเศษ — self-host stack หนักเกินไปสำหรับเครื่องที่มี RAM ว่างจริงระดับ 1GB กว่าๆ

**ยังไม่ได้ลงมือติดตั้งอะไรจริง** ในรอบนี้ — เป็นแค่ feasibility survey ตามที่ขอ รอ มอส ตัดสินใจว่าจะทดลอง Phoenix (resource-limited) หรือ Langfuse Cloud ก่อน
