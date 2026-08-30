---
pattern: "Anthropic's 'Telephone Game' problem in multi-agent coding pipelines (Planner→Implementer→Tester→Reviewer): agents spend more tokens coordinating handoffs than doing work, and each handoff summarizes/truncates/reinterprets context. OpenAI Agents SDK (handoffs primitive) and Google ADK (parent→sub-agent context control) both assume you know the routing in advance. Flint AI's Switch (sandbox-quantum/switch) proposes the opposite: put humans + agents in a shared channel (Matrix homeserver backend) so the next agent reads prior report/evidence directly instead of a human relaying summaries — no pre-declared handoff needed for ad-hoc decisions."
date: 2026-08-31
source: user-shared summary + repo check: https://github.com/sandbox-quantum/switch
concepts: ["multi-agent", "telephone-game", "context-handoff", "shared-channel", "matrix-homeserver", "agent-orchestration"]
---

# Switch (Flint AI) — shared-channel แก้ปัญหา Telephone Game ระหว่าง agent

## แนวคิดหลักที่น่าเก็บไว้ (ไม่ผูกกับตัว tool)

Anthropic ทดลองแบ่งงาน coding ให้ 4 agent role (Planner/Implementer/Tester/Reviewer) แล้วพบว่า
**token ส่วนใหญ่หมดไปกับการประสานงาน ไม่ใช่ทำงานจริง** เรียกปัญหานี้ว่า "Telephone Game" — ทุกครั้งที่ส่งต่องาน
ข้อมูลถูกสรุป/ตัดทอน/เปลี่ยนความหมาย

**นี่ตรงกับ anti-pattern ที่ CLAUDE.md ของ ayami-oracle เองเตือนไว้อยู่แล้ว**:
> ❌ Subagent เขียน draft → Main แค่ commit (Anti-pattern เพราะ Main ไม่มีบริบทพอ)
> ✅ Subagent หาข้อมูล → Main เขียนทุกอย่างเอง (ต้อง reflect ด้วยตัวเอง)

สองแนวทางแก้ที่มีอยู่ตอนนี้ทั้งคู่ **ต้องรู้เส้นทาง handoff ล่วงหน้า**:
- OpenAI Agents SDK: `handoffs` primitive — กำหนดว่า agent ไหนส่งงานให้ agent ไหน
- Google ADK: ควบคุมว่า context จาก parent agent จะไหลไปยัง sub-agent มากแค่ไหน

**Switch เสนอทางที่ 3**: อย่า pre-declare route เลย ให้ human + agents ทุกตัวอยู่ใน **shared channel เดียวกัน**
(Matrix homeserver เป็น backend) — agent ตัวถัดไปอ่าน report/evidence ของ agent ก่อนหน้าได้โดยตรง
ไม่ต้องให้คนเป็นคนขนข้อมูล (แก้ 3 ปัญหา: agent ใหม่ไม่มีบริบท, เห็นแต่ข้อสรุปไม่เห็น evidence, ผลลัพธ์บางอย่างเช่น
"no regression" หายไปไม่ถูกส่งต่อ)

## เกี่ยวกับตัว repo (สำหรับพิจารณาในอนาคต — ยังไม่ติดตั้ง)

- `sandbox-quantum/switch` — โปรดักต์ Flint AI, สร้างโดย SandboxAQ (บริษัทจริง), repo อายุ ~6 สัปดาห์ (2026-07-16), 449⭐
- License: Apache 2.0 + Commons Clause (self-host ฟรี, ห้ามขายต่อเป็นบริการ)
- Architecture จริง = Desktop app (Switch Console) + local server + **Matrix homeserver (Tuwunel)** +
  PostgreSQL + Agent Bridge (เชื่อม Claude Code/Codex/OpenCode/HTTP-MCP) + Collaboration Bridge
  (Slack/Teams/Discord/Telegram/Mattermost) — เป็น full infra stack ไม่ใช่ skill เบาๆ

## ทำไมยังไม่ติดตั้งตอนนี้

มอสทำงานคนเดียว (solo) ไม่มีทีมที่ใช้ Slack/Teams/Discord ร่วมกันสำหรับ ops/incident response —
คุณค่าหลักของ Switch คือ "คนหลายคน + agent หลายตัวคุยกันใน channel เดียว" ซึ่งเป็นปัญหาระดับทีม
ตอนนี้ ayami-oracle มี MAW (multi-agent worktree orchestrator ผ่าน tmux) และสกิล `team-agents`/`talk-to`/`hey`
รองรับ coordinate agent หลายตัวแบบเบาๆ อยู่แล้วโดยไม่ต้องรัน Matrix homeserver + Postgres

**ถ้าจะพิจารณาใหม่ในอนาคต**: เช็คว่ามีทีมจริงที่ใช้ Slack/Discord ร่วมกันหรือยัง ถ้ามีค่อยกลับมาดู repo นี้อีกที
