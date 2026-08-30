---
pattern: "Anthropic official Agent Skills docs: 3-level progressive disclosure (metadata always-loaded ~100 tok, SKILL.md body loaded on trigger <5k tok, bundled resources/scripts loaded only when referenced, scripts run via bash so their code never enters context) plus per-surface constraints (claude.ai/API/Claude Code differ on sharing scope, sync, network access) and security guidance (only trusted-source skills, audit bundled files, external-URL-fetching skills are high risk)"
date: 2026-08-31
source: docs: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview
concepts: ["skill.md", "agent-skills", "progressive-disclosure", "claude-code-skills", "anthropic-docs"]
---

# Agent Skills — เอกสารทางการของ Anthropic

ต่อยอดจาก [[2026-08-31_skill-md-pattern-works-beyond-coding-agents]] — คราวนี้อ่านจากต้นทาง (Anthropic เอง)
เรื่อง Agent Skills ที่ ayami-oracle ใช้อยู่ทุกวันผ่าน `.claude/skills/*/SKILL.md`

## 3 ระดับของ progressive disclosure (คำอธิบายที่ชัดที่สุดเท่าที่เจอ)

| Level | โหลดตอนไหน | Token cost | เนื้อหา |
|---|---|---|---|
| 1: Metadata | เสมอ ตอน startup | ~100 token/สกิล | `name` + `description` ใน YAML frontmatter — ใช้ match ว่าจะ trigger สกิลไหน |
| 2: Instructions | ตอนสกิลถูก trigger | <5k token | เนื้อหา body ของ SKILL.md — Claude ใช้ `bash: cat SKILL.md` อ่านเข้ามา |
| 3: Resources/scripts | ตามต้องการเท่านั้น | 0 จนกว่าจะถูกเปิด | ไฟล์อ้างอิง (โหลดเข้า context ถ้าอ่าน) / สคริปต์ (รันผ่าน bash, **โค้ดสคริปต์เองไม่เข้า context เลย มีแค่ output ที่เข้า**) |

จุดสำคัญที่ควรจำ: **สคริปต์ไม่มีค่า context** เพราะ Claude รันผ่าน bash แล้วรับแค่ output —
ดังนั้นสกิลที่มี logic แบบ deterministic (คำนวณ, validate) ควรทำเป็นสคริปต์ ไม่ใช่ให้ LLM คิดเองในเนื้อ SKILL.md
(ตรงกับที่ Microsoft Agent Framework ใช้ `script_runner` เหมือนกัน — สองระบบมาบรรจบที่หลักการเดียวกัน)

## กติกาของฟิลด์ name/description ที่ต้อง comply

- `name`: ≤64 ตัวอักษร, lowercase+ตัวเลข+ขีดกลางเท่านั้น, ห้ามมี XML tag, ห้ามใช้คำสงวน "anthropic"/"claude"
- `description`: ต้องไม่ว่าง, ≤1024 ตัวอักษร, ห้ามมี XML tag, **ต้องบอกทั้ง "ทำอะไร" และ "ใช้เมื่อไหร่"** —
  เพราะ Claude เอา description ไป match กับ request ของ user เพื่อตัดสินใจ trigger

## ความต่างข้ามแพลตฟอร์ม (สำคัญถ้าจะพอร์ตสกิลข้ามระบบ)

- **Skill ไม่ sync ข้าม surface** — อัปโหลดที่ claude.ai ≠ ใช้ได้ใน API ≠ ใช้ได้ใน Claude Code (filesystem-based แยกขาด)
- Sharing scope ต่างกัน: claude.ai = ต่อ user คนเดียว, API = workspace-wide, Claude Code = personal (`~/.claude/skills/`) หรือ project (`.claude/skills/`) หรือแชร์ผ่าน Plugin
- Network access ต่างกันมาก: **Claude Code = full network access เหมือนโปรแกรมทั่วไปบนเครื่อง user**, ส่วน API = ไม่มี network เลยและห้าม install package runtime, claude.ai = แล้วแต่ admin setting

## Security — ตรงกับ concern เรื่อง prompt injection ที่ต้องระวังอยู่แล้ว

Anthropic เตือนชัดเจนว่า skill ที่ fetch ข้อมูลจาก external URL คือความเสี่ยงสูงสุด (fetched content อาจมี
malicious instructions ฝังมา) และให้ใช้เฉพาะสกิลจากแหล่งที่เชื่อถือได้ — ถ้าจำเป็นต้องใช้สกิลจากแหล่งไม่รู้จัก
ให้ audit ทุกไฟล์ที่ bundle มา (SKILL.md, scripts, images) หา pattern แปลกๆ เช่น network call ที่ไม่ควรมี

## เกี่ยวข้องกับ ayami-oracle โดยตรง

- ยืนยันโครงสร้างที่ใช้อยู่แล้ว (`.claude/skills/*/SKILL.md`) ตรงตาม spec ทางการทุกจุด
- Claude Code ไม่มี pre-built document skills (pptx/xlsx/docx/pdf) แต่มี open-source "Claude API skill" bundled มาให้
- เปิด repo อ้างอิง open-source skills: https://github.com/anthropics/skills — น่า `/learn` ต่อถ้าอยากดูตัวอย่างสกิลทางการ
