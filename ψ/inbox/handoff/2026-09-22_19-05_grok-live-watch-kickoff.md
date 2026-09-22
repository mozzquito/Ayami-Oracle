# Handoff: Grok Live Watch — read-only monitor kickoff for real-money Grok Bot trading

📡 Session: 2d5ed472 | ayami-oracle | ~7h

**Date**: 2026-09-22 19:05
**Context**: ~172k (long session, hence this handoff)

## Context
**Oracle**: Ayami Oracle (หญิง) | **Human**: มอส (ชาย)
**Mode**: Fast | **Memory**: Auto

## What We Did

มอสถามว่าอยากให้ Ayami ช่วยรันแทน Grok Bot ที่เทรดเงินจริงบน Binance TH (token แพง) — ทำตาม SDLC gate เต็มขั้นตอน requirement → design → develop start:

- **Requirement**: ยืนยันว่า Grok Bot agent "treade" (remote Cursor sandbox, `mcp__grokbot__*`) เทรดเงินจริงด้วย API key จริง มอสต้องการให้ Ayami รับหน้าที่แค่ **monitor/report + วิเคราะห์สัญญาณ** เท่านั้น — ไม่เคยกดออเดอร์เอง, /agy /zcode ช่วยแค่ design/review
- **Design**: ส่งโจทย์ให้ /zcode + /agy รีวิวพร้อมกัน — สรุปตรงกัน: build แยกขาดจาก sandbox เดิม (local cron), key ต้อง read-only แยกจาก key เทรดจริง, strategy ต้องเป็น snapshot แบบ frozen (ขอ export จาก treade ไม่ใช่เข้าไปแก้ sandbox), ระวัง split-brain drift / rate-limit ชนกัน / dead-man risk (Grok Bot ล่มระหว่างถือ position) / scope creep จาก "วิเคราะห์" เป็น "สั่งเทรด"
- **ติดต่อ Grok Bot "treade"** ผ่าน `grokbot_send` (messageId `5d6d1664-8c06-4949-8ad9-9b47106fcf3b`) ขอ strategy summary + ถามช่องทางรายงาน — treade ตอบกลับ:
  - กลยุทธ์: สแกน USDT allowlist, heuristic score จาก external feed, timeframe ~15min, Spot/long-only, entry score ≥~22 top-N ภายใต้ max concurrent ~2, size ~10 USDT, TP≈1.5%/SL≈1% market, มี cooldown กันเข้าซ้ำ
  - ไม่มีช่องรายงานภายนอกให้ reuse (แจ้งเตือนอยู่ในแชต Grok Bot เองเท่านั้น ไม่มี Discord/LINE/Telegram/email/Slack) → มอสตัดสินใจ: ใช้ **Discord bot เดิม** ที่ `market-backtester` + `grok-crypto-paper-trading` แชร์กันอยู่แล้ว
- **สร้าง read-only Binance TH API key** — มอสสร้างเอง, ตั้งค่าถูกต้อง (read-only, ปิด trade/withdraw)
- **⚠️ Security incident + fixed**: ตอน verify key ตัวแรก Ayami รัน `sed` redaction command ที่ format ไม่ match ไฟล์จริง (ไฟล์ใช้ `API Key : xxx` ไม่ใช่ `KEY=xxx`) ทำให้ key+secret จริงหลุดเข้า conversation — มอส revoke ทันทีแล้วสร้างใหม่, ใส่ค่าใหม่ในไฟล์ `.env` ถูก format (`KEY=VALUE`), verify แบบ length-only สำเร็จโดยไม่เห็นค่าจริงเลย — บันทึก lesson ไว้ใน memory (`feedback_secrets_file_command_safety.md`) และ SendFeedback แล้ว
- Scaffold `ψ/lab/grok-live-watch/` (README เต็ม + `.env.example` + `.env` ที่มอสกรอกแล้ว, gitignore ยืนยันครอบแล้ว) — **ยังไม่มีโค้ดจริง**

## Pending

- [ ] เขียน read-only Binance TH client — **ต้องเช็ค REST API base/auth shape ของ Binance TH ก่อน** (ห้ามสมมติว่าเหมือน `data-api.binance.vision` ของ paper-trading sibling — ไม่เคยยืนยัน)
- [ ] Logic ดึง position/P&L/alert + เทียบกับ strategy snapshot เพื่อวิเคราะห์สัญญาณ
- [ ] ต่อ Discord notify (reuse `DISCORD_BOT_TOKEN`/`REPORT_CHANNEL_ID` + pattern จาก `paper_trading/notify.py` ใน grok-crypto-paper-trading)
- [ ] Local cron/launchd scheduling
- [ ] เขียน test ก่อนเชื่อผลลัพธ์ใดๆ บนบัญชีเงินจริง (real-money account — มาตรฐานสูงกว่าปกติ)
- [ ] Re-export strategy snapshot จาก treade เป็นระยะ (อาจ drift จากที่บันทึกไว้วันนี้)

## Cleanup needed (ไม่ใช่ของ session นี้ — เจอตอน check git status)

Repo มีไฟล์ที่ modified/untracked จาก session/agent อื่นที่รันคู่ขนานอยู่ (ไม่ใช่งานของ Ayami ใน session นี้ — ไม่แตะ):
- `ψ/inbox/focus-agent-agy.md`, `ψ/inbox/focus-agent-main.md`, `ψ/memory/learnings/session-metrics.md` (modified)
- `ψ/memory/learnings/2026-09-22_check-content-modality-before-heavy-pipeline.md`, `ψ/memory/learnings/2026-09-22_learned-jaturapornchai-zcode.md`, `ψ/memory/retrospectives/2026-09/22/18.56_video-ocr-evisa-name-bug-mssql-query.md` (untracked)
- หลาย worktree ค้างอยู่ (`worktree-calm-swinging-castle`, `worktree-commit-remaining-outside-lab`, `worktree-immutable-zooming-yeti`, `worktree-lab-commit-triage`) — เช็ค `maw peek` ว่ายังทำงานอยู่ไหมก่อนเก็บกวาด
- `ψ/lab/grok-live-watch/` เป็นของ session นี้ — **untracked ตั้งใจ** ยังไม่ commit เพราะยังไม่มีโค้ดจริง รอ session หน้า

## Key Files

- `ψ/lab/grok-live-watch/README.md` — design, boundaries, strategy snapshot, incident log, status
- `ψ/lab/grok-live-watch/.env` — key พร้อมใช้แล้ว (gitignored, ห้าม cat/print ทั้งไฟล์)
- `~/.claude/projects/-Users-phongcheatphus-ayami-oracle/memory/project_grok_live_watch.md` — memory เต็ม
- `~/.claude/projects/-Users-phongcheatphus-ayami-oracle/memory/feedback_secrets_file_command_safety.md` — lesson จาก incident
- Sibling refs: `ψ/lab/grok-crypto-paper-trading/` (notify.py pattern), `ψ/lab/market-backtester/` (Discord bot/channel env vars, deploy pattern)
