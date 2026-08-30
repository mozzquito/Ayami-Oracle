---
pattern: "SKILL.md / Agent Skills pattern (progressive disclosure) is not exclusive to coding agents — Microsoft Agent Framework implements the same architecture for general-purpose business/domain agents via SkillsProvider"
date: 2026-08-31
source: article: https://medium.com/@boatchrnthn/skill-md-is-also-applied-with-microsoft-agent-framework-a360e91a5cc0
concepts: ["skill.md", "agent-framework", "progressive-disclosure", "microsoft-agent-framework", "skills-provider"]
---

# SKILL.md ไม่ใช่ของเฉพาะ coding agent

Microsoft Agent Framework รองรับ "Agent Skills" ด้วยโครงสร้างเดียวกับที่ Claude Code ใช้
(`SKILL.md` + `references/` + `scripts/` + `assets/`) แต่ใช้กับ agent ทั่วไปได้ — ตัวอย่างในบทความคือ
สกิล "customer-support" ที่ไม่เกี่ยวกับโค้ดเลย (นโยบายรีฟันด์, ขั้นตอนตอบลูกค้า)

**หลักการที่ใช้ร่วมกัน**: progressive disclosure — agent ไม่โหลดความรู้ทั้งหมดเข้า context ทันที
แต่ค้นพบสกิลก่อน แล้วโหลดคำสั่ง/อ่านไฟล์เสริม/รันสคริปต์เมื่อจำเป็นเท่านั้น

**กลไกใน Microsoft Agent Framework**: `SkillsProvider.from_paths(skill_paths=...)` ส่งเข้า
`context_providers` ของ `Agent` object → framework มี tools ให้ agent เรียกเอง คือ
`load_skill`, `read_skill_resource`, `run_skill_script` — รองรับ skill หลายแบบ
(file-based, code-based, class-based, MCP-based) และดึงจากหลายโฟลเดอร์พร้อมกัน
(แยก company-skills / team-skills ได้)

**จุดที่น่าเอามาปรับใช้**: สกิลรันสคริปต์ Python จริงได้ผ่าน `script_runner` parameter —
ให้ logic ที่ deterministic (เช่นคำนวณ refund) รันเป็นโค้ดแทนให้ LLM คิดเอง เข้ากับแนวทาง
`.claude/skills/*/SKILL.md` ที่ ayami-oracle ใช้อยู่แล้ว (agy, zcode, learn ฯลฯ)

**Note**: WebFetch โดน Medium บล็อก (403) ต้องใช้ Playwright browser (`document.querySelector('article').innerText`)
ดึงเนื้อหาแทน — เก็บไว้เป็น fallback pattern เวลา WebFetch โดนบล็อกโดย Medium/เว็บที่กัน bot
