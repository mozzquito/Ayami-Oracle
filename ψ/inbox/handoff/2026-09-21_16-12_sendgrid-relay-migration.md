# Handoff: SendGrid relay migration plan (Exchange on-prem → SendGrid)

📡 Session: bbb96672 | ayami-oracle | ~3h clock (13:09–16:12, active ~50 min)

**Date**: 2026-09-21 16:12
**Context**: ~195k (เกินจุดเตือน 150k ตั้งแต่ต้นเซสชัน — เริ่มจาก handoff ที่จบที่ 804k)

## Context
**Oracle**: Ayami (หญิง) | **Human**: มอส (ชาย) | **Mode**: Fast | **Memory**: auto | **Team**: solo

## What We Did
- ค้น "sandgrid" (= SendGrid สะกดผิด) → พบ 2 งานเดิม: TOR เทียบ SendGrid (ปิดแล้ว 2026-09-09/11) และ POC เก็บ log `ψ/lab/sendgrid-log-poc/`
- วางแผนย้าย **SMTP relay ขาออก** จาก Exchange on-prem ไป SendGrid (~200k/วัน, MX + mailbox อยู่ที่ Exchange ตามเดิม, D1 = ย้ายทุกเมลขาออก, เป็นงานย้ายจริง)
- เขียน `RUNBOOK.md` (decision log D1–D5, inventory, phase 0–4 + go/no-go, ความเสี่ยง R1–R14, rollback) และ `BRIEF.html` (สรุปเตรียมพบลูกค้า, artifact ส่วนตัว v2: https://claude.ai/artifact/8USodbaRFmKv29ir8LVn8H)
- **Commit `bdf2a830`** บนสาขา `lab/sendgrid-relay-migration` (แตกจาก main ผ่าน worktree ชั่วคราว, ไม่ push) — ทรีหลักยังอยู่ที่ `lab/jev-gate`
- zcode + agy รีวิว `ψ/lab/jev-gate` แบบอ่านอย่างเดียว → ยืนยัน 6 ข้อกับโค้ดจริง (ยังไม่ได้แก้โค้ด), รีวิว flow อีเมล (พบ R14) และชุดคำถามสำหรับลูกค้า
- เขียน retro, lesson, metrics row (ดู Key Files); log activity = completed

## Pending
- [ ] runbook ยังเป็น draft v0.1 — ยังไม่ได้ให้ zcode/agy รีวิวทั้งฉบับ และคำสั่ง Exchange ไม่เคยรันจริง
- [ ] ข้อเท็จจริงของ SendGrid ยังไม่ verify: แผนที่รับ 200k/วัน และ ≥10k/ชม., ตาราง warm-up + จำนวน Dedicated IP, พฤติกรรม NDR ของผู้ใช้ Outlook (มอสไม่อนุมัติการค้นเว็บเมื่อ 13:13 — ต้องขออนุญาตก่อน)
- [ ] ชุดคำถามลูกค้าที่เรียบเรียงใหม่ ยังไม่ได้ใส่ใน RUNBOOK.md/BRIEF.html (อยู่ในแชตของเซสชันนี้เท่านั้น — ดูสรุปด้านล่าง)
- [ ] คำตอบเรื่อง DNS ของมอสอ่านไม่ออก ("DNS อยู่ที่ ดอล อะไร") — ต้องถามซ้ำ
- [ ] D2–D5 ยังเปิด (เส้นทาง, วิธี ramp, แผน/Dedicated IP, subuser)
- [ ] HANDOVER-KIT (คู่มือส่งมอบ 12 ข้อ) ยังไม่ได้เขียน — ต้องมีถ้าเจ้าหน้าที่ลูกค้า config เอง
- [ ] jev-gate: ยังไม่ได้แก้ข้อ 1 (README บอก shadow log ไม่มี full text แต่เก็บ preview 120 ตัวอักษร), 2 (`INVISIBLE_RE` ขาด U+2066–2069, tag chars U+E0000+, U+180E, U+034F), 5 (DESIGN.md ไม่ตรงโค้ด), 6 (`load_env_file` ไม่ตัด comment) + เทสต์ — รอมอสสั่ง
- [ ] ค้างเดิม (จาก handoff ก่อนหน้า): revoke API key เก่า 2 ตัว, ตัดสินใจ push commit ที่อยู่แค่ในเครื่อง 6 อันบน `lab/jev-gate` (ห้าม `git pull` แล้ว push), PR #4 lab/jev-gate → main (ผล `gh pr list` รอบนี้แสดง PR ของอีก repo ไม่ตรงกับ #4 — ต้องตรวจซ้ำว่า `gh` ชี้ repo ไหน)
- [ ] SendGrid API key ที่เคยวางในแชต 2026-08-22 ยังไม่ทราบว่า rotate แล้วหรือยัง

## Next Session
- [ ] ให้ zcode + agy รีวิว `RUNBOOK.md` ทั้งฉบับ (ความปลอดภัย + โครงสร้าง) แล้วแก้ตามที่ยืนยันได้ (สาขา `lab/sendgrid-relay-migration`)
- [ ] ขอมอสอนุญาตค้นเว็บ แล้วตรวจข้อ ⚠️ ทั้งหมดกับเอกสาร SendGrid
- [ ] ใส่ชุดคำถามลูกค้าใน RUNBOOK + BRIEF แล้ว republish artifact (ใช้ URL เดิม)
- [ ] ถามมอสซ้ำเรื่อง DNS และให้ตอบ D2–D5
- [ ] ตัดสินใจกับมอส: เขียน HANDOVER-KIT หรือไม่
- [ ] ถามมอสว่าจะแก้ jev-gate (ข้อ 1, 2, 5, 6 + เทสต์) เลยไหม แล้วทำในสาขา `lab/jev-gate` (ไม่ commit/push จนกว่าจะสั่ง)

## ชุดคำถามลูกค้า (สรุป — ใส่ใน RUNBOOK ในเซสชันหน้า)
1. จากเซิร์ฟเวอร์ Exchange ที่ส่งเมลออก เปิดพอร์ต 587 ไป `smtp.sendgrid.net` ได้ไหม (สำรอง 2525/465), proxy/IPS บล็อก STARTTLS ไหม — ตรวจ `Test-NetConnection smtp.sendgrid.net -Port 587` และ `openssl s_client -starttls smtp -connect smtp.sendgrid.net:587`
2. DNS ของโดเมนที่ใช้ส่งอยู่ที่ไหน ใครดูแล เพิ่มเรคคอร์ดภายในกี่วัน (ต้องเพิ่ม CNAME ของ Domain Authentication, รวม SPF, เพิ่ม DMARC — **เพิ่มใน DNS ของโดเมนเรา ไม่ได้เปลี่ยนอะไรที่ sendgrid.net**)
3. ใครแก้ Send Connector / ใครดูแล DNS / ใครสร้าง API key และเราเข้าช่วยได้ไหม
4. change window, ผู้อนุมัติ, ซ้อม rollback แล้วหรือยัง
5. รายชื่อโดเมนที่ส่ง + SPF/DMARC ปัจจุบัน
- ขาดอยู่: ปริมาณจริง/peak, PDPA (เมลผ่านระบบต่างประเทศ), เมลถึงโดเมนตัวเองวนออก SendGrid (R14), ผู้ใช้ Outlook ไม่ได้รับ NDR (R12), ใครสร้างที่เก็บ log ≥90 วัน
- เงื่อนไข gate ของ cutoff: แผนรับ 200k/วัน ยืนยันแล้ว, D1–D5 ปิด, SPF/DKIM/DMARC ผ่านจริง, พอร์ต 587 ผ่าน, ที่เก็บ log webhook ทำงาน, ซ้อม rollback สำเร็จ, นำร่องผ่านเกณฑ์ 2–3 วันทำการ

## Key Files
- `ψ/lab/sendgrid-relay-migration/RUNBOOK.md`, `BRIEF.html` — commit `bdf2a830` บน `lab/sendgrid-relay-migration` (ทรีหลักมีสำเนา untracked ด้วย)
- `ψ/lab/sendgrid-log-poc/` — POC เก็บ log ผ่าน Event Webhook (ทดสอบระดับ 50–100 ฉบับเท่านั้น)
- `ψ/memory/retrospectives/2026-09/21/16.10_sendgrid-relay-migration-brief.md` (retro, ยังไม่ commit)
- `ψ/memory/learnings/2026-09-21_commit-from-temp-worktree-in-shared-tree.md` (lesson, ยังไม่ commit)
- `ψ/memory/learnings/session-metrics.md` (แถวใหม่ต่อท้าย, ยังไม่ commit)
- `ψ/lab/jev-gate/` (`gate.py:49-50` ตัวกรอง, `README.md`, `DESIGN.md`) — เป้าหมายของการแก้ที่ค้าง
- `~/Downloads/เทียบ TOR กับWYM (1) - ตรวจแก้ไข.xlsx` — ผลเทียบ TOR ที่ตรวจแก้แล้ว
- ความจำ: [[project_wym_tor_email_sendgrid]] — ยังไม่ได้สร้างไฟล์ memory สำหรับโปรเจกต์ย้าย relay นี้ (ควรสร้างเมื่อมอสยืนยันรายละเอียดกับลูกค้า)
