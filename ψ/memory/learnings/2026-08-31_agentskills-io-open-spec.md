---
pattern: "agentskills.io publishes an open, vendor-neutral spec for Agent Skills (skills-ref reference validator at github.com/agentskills/agentskills) that extends Anthropic's SKILL.md format with extra optional frontmatter fields: license, compatibility, metadata, allowed-tools — plus stricter name rules (must match parent dir name, no consecutive hyphens)"
date: 2026-08-31
source: docs: https://agentskills.io/specification
concepts: ["skill.md", "agent-skills", "open-spec", "progressive-disclosure", "skills-ref"]
---

# agentskills.io — สเปคเปิดสำหรับ Agent Skills

ต่อยอดจาก [[2026-08-31_anthropic-agent-skills-official-docs]] และ [[2026-08-31_skill-md-pattern-works-beyond-coding-agents]] —
เว็บนี้คือสเปคที่เป็นกลาง (vendor-neutral) ของฟอร์แมต SKILL.md ไม่ใช่ของ Anthropic โดยตรง
มี reference validator: `skills-ref validate ./my-skill` (repo: github.com/agentskills/agentskills)

## ต่างจากเอกสาร Anthropic ตรงไหน

Anthropic docs พูดถึงแค่ `name` + `description` เป็น required field แต่ spec ของ agentskills.io
มี **optional field เพิ่ม 4 ตัว** ที่ Anthropic ไม่ได้พูดถึง:

- `license` — ชื่อ license หรือ pointer ไปไฟล์ license ที่ bundle มา
- `compatibility` (≤500 ตัวอักษร) — ระบุ environment ที่ต้องการ เช่น `"Requires git, docker, jq, and access to the internet"` หรือ `"Designed for Claude Code (or similar products)"`
- `metadata` — key-value string map อิสระ ให้ client เก็บข้อมูลเพิ่มเติมนอกสเปค (เช่น `author`, `version`)
- `allowed-tools` (experimental) — string คั่นด้วยช่องว่างของ tool ที่ pre-approve ให้สกิลใช้ เช่น `"Bash(git:*) Bash(jq:*) Read"` — รองรับไม่เท่ากันในแต่ละ agent implementation

## กติกา `name` field ที่เข้มกว่าที่คิด

นอกจาก lowercase+ตัวเลข+ขีดกลาง, ห้ามขึ้นต้น/ลงท้ายด้วยขีดกลาง ยังมีเพิ่ม:
- **ห้ามมีขีดกลางติดกัน** (`pdf--processing` ผิด)
- **ต้องตรงกับชื่อโฟลเดอร์ parent เป๊ะๆ** — ข้อนี้ไม่ได้พูดใน Anthropic docs แต่เป็นเงื่อนไขบังคับใน spec นี้

## คำแนะนำเชิงปฏิบัติที่ได้เพิ่มจาก spec นี้

- **SKILL.md ควรอยู่ใต้ 500 บรรทัด** — ตัวเลขที่ชัดกว่า "under 5k tokens" ของ Anthropic docs
- **File reference ควรลึกแค่ 1 ชั้นจาก SKILL.md** — หลีกเลี่ยง reference chain ที่ลึกหลายชั้น (เช่น SKILL.md → A.md → B.md)
- ตัวอย่าง description ที่ดี/แย่ชัดเจน: "Helps with PDFs." = แย่ (ไม่บอกว่าใช้เมื่อไหร่), ต้องระบุ keyword เฉพาะที่ agent จะ match ได้

## เกี่ยวข้องกับ ayami-oracle

Skill ใน `.claude/skills/*/SKILL.md` ของ repo นี้ยังไม่ได้ใช้ field เสริมพวกนี้เลย (license/compatibility/metadata/allowed-tools)
— ถ้าจะแจกจ่ายสกิลให้คนอื่นใช้ต่อ หรืออยาก validate ให้ตรงสเปค ควรพิจารณาเพิ่ม field เหล่านี้และรัน `skills-ref validate`
ก่อน commit สกิลใหม่
