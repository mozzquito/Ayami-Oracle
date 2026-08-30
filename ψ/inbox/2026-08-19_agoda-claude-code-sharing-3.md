# Agoda — Claude Code Sharing ครั้งที่ 3

**วันที่**: 2026-08-19
**สถานที่**: Agoda (meeting)
**บันทึกโดย**: Ayami

## Notes

### Flow: Routine → Fix Code

- **Routine** → **Fix code**
- ให้ Claude ไปดู GitHub แล้วตรวจสอบว่า CI/CD pipeline ทำไม fail หรือ deploy มีปัญหา
- การตรวจสอบใช้ routine (รันตามรอบ/schedule)

### Note: Anthropic Cloud

- Anthropic Cloud มีให้ใช้งานแบบ free
- มอสจะไปลองเล่นดู
- **ข้อจำกัด**: ใช้งานได้เฉพาะ repo ที่อยู่บน GitHub เท่านั้น
- **Repo ใหญ่ = setup ยากขึ้น** — ถ้า codebase ต้องมี local setup ที่ซับซ้อน (dependencies, env vars, services ที่ต้องรันคู่กัน ฯลฯ) บน cloud ก็จะเจอปัญหา setup ยากเหมือนกัน (ไม่ได้ทำให้ง่ายขึ้นอัตโนมัติ)

### Tip: Skills ใช้บน Cloud ไม่ได้ (ต้อง sync เอง)

- **Skills ใช้งานไม่ได้บนตัว cloud โดยตรง** (skills ที่ตั้งไว้ local ไม่ได้ตามไปอัตโนมัติ)
- วิธีแก้: ต้องทำ **script** เพื่อ copy skills + CLAUDE.md ขึ้นไปบน cloud repo (เช่น commit เข้า repo แล้วให้ cloud pull จาก GitHub)
- แปลว่าต้องมี process sync skills/CLAUDE.md → push ขึ้น GitHub → cloud pull ไปใช้เอง

### Tip: Clear Space/Log — ทำเป็น Routine Restart

- Clear พื้นที่/log เป็นประจำ → ทำเป็น **routine restart** (รีสตาร์ทตามรอบ ไม่ปล่อยให้ log/space สะสมจนเป็นปัญหา)
- คำถามที่ยกในวง: clear log ใช้ **mole** ได้ไหม? (⚠️ ยังไม่ชัดเจนว่า "mole" คือเครื่องมือ/คำสั่งอะไร — รอมอส clarify)

### สิ่งที่ทำให้มั่นใจและมีประสิทธิภาพ — Tools 9 อย่าง (MCP/Integrations)

1. GitHub
2. GitHub Project
3. Slack
4. AWS
5. Databricks
6. Datadog
7. HubSpot
8. Firefile (⚠️ สะกดตามที่พูด — ไม่แน่ใจชื่อเต็ม อาจเป็น Figma/Fireflies/อื่นๆ รอ confirm)
9. Google Workspace

**หมายเหตุ**: ทั้ง 9 อย่างมีจุดร่วมกันคือ — มี **MCP สำหรับ Claude Code** หรือ **plugin ของ Claude** รองรับ

### Tools มี 2 แบบ: IDE และ Orca

- **แบบที่ 1 — IDE**: Code editor / IDE → คุณ → Editor → Code (ทำงานทีละคน ทีละ session)
- **แบบที่ 2 — Orca**: คุณ → เปิดหลาย window → รัน **Agent 1 – Agent 5** พร้อมกัน (หลาย agent ขนานกันในหลาย window)

### หัวข้อ: ทำอย่างไรให้ Agent มี Productivity

- Flow: **You → Orca → Agent 1 – Agent 5**
- **Orca เป็นแอปจริง** — Flow เต็ม: **iPhone (Orca app) → MacBook Orca → Agent 1 – Agent 5**
  - ควบคุม/สั่งงานผ่าน Orca app บน iPhone → ส่งต่อไปที่ Orca บน MacBook → กระจายงานให้ Agent 1-5 ทำงานขนานกัน
- **Orca มี tools สำหรับ manage Claude หลาย account พร้อมกัน**

### Research: Orca คืออะไร (ค้นเพิ่มหลัง meeting)

- **Orca** = Agent Development Environment (ADE) — นี่คือที่มาของคำว่า "ade" ที่จดผิดไว้ตอนแรก (ADE ไม่ใช่ orchestrator แยก แต่เป็น "ประเภท" ของ tool ที่ Orca เป็นตัวอย่าง)
- Open source, MIT license, ทำโดย Stably AI, GitHub stars 20,000+
- รัน CLI coding agent หลายตัวพร้อมกันแบบขนาน (Claude Code, Codex, Cursor, OpenCode, Gemini ฯลฯ) โดยแยก isolated ด้วย **Git Worktree**
- มี terminalในตัว (WebGL, split screen ไม่จำกัด), diff review, live agent status
- **Account hot-swap**: สลับ Claude account ได้ทีเดียวคลิกเดียว แม้มี session รันอยู่ก็สลับได้ปลอดภัย (มี guard กัน auth refresh ชนกัน) + มี usage/rate-limit tracking ในตัว
- **Mobile**: มีแอป companion (Orca Mobile) บน iOS/Android — pair กับเครื่อง desktop แล้ว mirror terminal session ดูจากมือถือได้ (ตรงกับที่จดว่า iPhone Orca app → MacBook Orca)
- **Setup คร่าวๆ บน macOS**:
  1. ติดตั้ง Claude Code ปกติ (`npm i -g @anthropic-ai/claude-code`) แล้ว login ผ่าน terminal ครั้งนึง
  2. ติดตั้ง Orca desktop app → มันจะ detect `~/.claude` ให้เองอัตโนมัติ ไม่ต้อง config เพิ่ม
  3. เพิ่ม Claude account อื่นเข้าไปในแอป → สลับ (hot-swap) ได้จาก UI
- **ลิงก์**: [onorca.dev](https://www.onorca.dev/) | [Orca docs — Claude Code](https://www.onorca.dev/docs/agents/claude-code) | [App Store](https://apps.apple.com/us/app/orca-ide/id6766130217)

**สถานะ**: ค้นข้อมูลเสร็จแล้ว ยังไม่ได้ติดตั้ง/ตั้งค่าจริง — รอมอสตัดสินใจว่าจะให้ไปลองตั้งบนเครื่องนี้เลยไหม

(รอมอสเพิ่มเนื้อหา)
