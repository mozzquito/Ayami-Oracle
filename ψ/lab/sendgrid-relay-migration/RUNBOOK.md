# Runbook: ย้าย SMTP Relay ขาออก Exchange on-prem → Twilio SendGrid

> สถานะ: **DRAFT v0.1** — เขียน 2026-09-21 โดย Ayami Oracle (AI) จากข้อมูลที่มอสยืนยันในแชต
> เป็นงานย้ายจริง (ไม่ใช่แค่เตรียม TOR) — เอกสารนี้เป็น **แผน** ยังไม่มีขั้นตอนไหนถูกรันจริง
>
> **สัญลักษณ์:** ⚠️ = ยังไม่ได้ verify กับเอกสาร/แผนราคาของ SendGrid หรือกับ Exchange จริง — ต้องเช็กก่อนลงมือ
> ☐ = งานที่ต้องทำ / ตรวจ

## 0. ขอบเขต (Scope)

| หัวข้อ | ค่า |
|---|---|
| ย้ายอะไร | เมล **ขาออก** ที่ส่งผ่าน Exchange on-prem (SMTP relay) ไปออกทาง SendGrid |
| **ไม่ย้าย** | MX (เมลขาเข้า), mailbox, Outlook/OWA — อยู่ที่ Exchange เหมือนเดิม |
| ปริมาณ | ~200,000 ฉบับ/วัน (≈ 8,300/ชม. เฉลี่ย ≈ 6 ล้าน/เดือน) — peak จริงยังไม่ทราบ |
| Exchange | on-prem (เวอร์ชัน: **ยังไม่ทราบ**) |
| ตัวอย่างข้อกำหนด TOR ที่เกี่ยว | ≥200,000 ฉบับ/วัน หรือ ≥10,000/ชม. (4.6), log ≥90 วัน (4.8), SPF (4.7) |

### สิ่งที่ SendGrid ทำไม่ได้ (รู้ไว้ก่อน — จาก [[project_wym_tor_email_sendgrid]])
- ไม่ใช่ email hosting ไม่มี mailbox
- Email Activity เก็บเองสูงสุด 30 วันแม้แผนจ่ายเงิน → log ≥90 วันต้องเก็บเอง (ดูหัวข้อ 7)
- ขนาดข้อความสูงสุด 30MB (รวม encoding) → ไฟล์แนบจริงเล็กกว่านั้น ⚠️

---

## 1. การตัดสินใจที่ต้องปิดก่อนเริ่ม (Decision Log)

| # | คำถาม | ตัวเลือก | ผู้ตัดสิน | ผล |
|---|---|---|---|---|
| D1 | ย้าย **ทุกเมลขาออก (รวม user Outlook)** หรือ **เฉพาะเมลจากแอป/ระบบ**? | (A) ทุกอย่าง — ง่าย แต่ต้องนับ user เข้าใน 200k และเมล user ออกทาง IP SendGrid<br>(B) เฉพาะแอป — ต้องมี relay ตัวใหม่ หรือแอปต่อ SendGrid ตรง | มอส + เจ้าของ Exchange | **(A) ทุกเมลขาออก** (มอสแจ้ง 2026-09-21 — ยังไม่ยืนยันกับลูกค้า; ปริมาณรวม user ต้องไม่เกิน 200k/วัน) |
| D2 | เส้นทางของแอป | (1) แอป → Exchange → SendGrid (แอปไม่ต้องแก้)<br>(2) แอป → SendGrid ตรง (แก้ทีละแอป) | มอส | แนะนำ (1): มีหลายระบบและหลายทีม (frontend/backend + server) การให้แอปไม่ต้องแก้และเปลี่ยนที่ Send Connector จุดเดียวลดการประสานงาน — **รอมอสยืนยัน** |
| D3 | วิธี ramp/warm-up | (X) ตาม **domain ผู้รับ** ผ่าน address space ของ Send Connector<br>(Y) ตาม **แอป** (ย้ายทีละแอปไปต่อตรง) | มอส | ☐ |
| D4 | แผน SendGrid + จำนวน Dedicated IP | ต้องคุย sales — ⚠️ 200k/วัน น่าจะเกินแผนมาตรฐาน | มอส + procurement | ☐ |
| D5 | ใช้ subuser แยกตามระบบไหม | ช่วยแยก reputation/สถิติ ต่อระบบ ⚠️ | มอส | ☐ |

> หมายเหตุ D1: ตามที่จำได้ Send Connector ของ Exchange on-prem ไม่เลือกเส้นทางตาม "ผู้ส่ง" ได้โดยตรง ⚠️ ต้องให้ Exchange admin ยืนยันในสภาพแวดล้อมจริง
> หมายเหตุ D3: การ ramp แบบ "% ของปริมาณ" ผ่าน Exchange อย่างเดียวทำไม่ได้ (connector สลับแบบ all-or-nothing ต่อ address space) จึงต้อง ramp ด้วย domain ผู้รับ (X) หรือด้วยแอป (Y)

---

## 2. Inventory (ต้องกรอกให้ครบก่อน Phase 1)

### 2.1 ระบบที่ส่งเมลผ่าน Exchange

| ระบบ/แอป | เจ้าของ | เชื่อม Exchange แบบ | From address | ฉบับ/วัน | peak ฉบับ/ชม. | ขนาดเฉลี่ย/สูงสุด | parse NDR/bounce? | ประเภท (transactional/bulk) |
|---|---|---|---|---|---|---|---|---|
| | | anonymous relay / SMTP AUTH | | | | | ☐ ใช่ ☐ ไม่ | |

- ☐ ดึงตัวเลขจริงจาก Exchange message tracking log อย่างน้อย 30 วัน (ไม่เดา): ต่อวัน, ต่อชั่วโมง, ต่อผู้ส่ง — ระวัง **ตัวเลข "300,000/เดือน" กับ "ต่อวัน/ต่อชม."** ต่างหน่วยกัน (บทเรียนจาก TOR)
- ☐ หา peak สูงสุดในรอบ 30 วัน และช่วงที่มี burst (รายงาน/แจ้งเตือนรายเดือน)
- ☐ สัดส่วนผู้รับ **ตาม domain ปลายทาง** (gmail.com, outlook.com, yahoo, .go.th ฯลฯ) — ใช้วางแผน ramp แบบ D3-X

### 2.2 Domain และ DNS

| Domain ที่ใช้ส่ง | ผู้ดูแล DNS | DNS อยู่ที่ (Cloudflare/อื่น) | SPF ปัจจุบัน | DKIM ปัจจุบัน | DMARC ปัจจุบัน |
|---|---|---|---|---|---|
| | | | | | |

- ☐ SPF มีได้ **record เดียวต่อ domain** — ต้อง merge ห้ามเพิ่ม record ที่สอง
- ☐ ถ้า DNS อยู่บน Cloudflare: CNAME ของ SendGrid ต้อง **DNS-only (ไม่เปิดเมฆส้ม)** — เคยเจอตอน POC 2026-08-22 ทั้งเรื่อง proxy และ record ที่หาย

### 2.3 Exchange
- ☐ เวอร์ชันและ CU ปัจจุบัน
- ☐ รายชื่อ Send Connector / Receive Connector ที่ใช้อยู่ (export ค่าปัจจุบันเก็บไว้ก่อนแตะ)
- ☐ ขนาดข้อความสูงสุด (org/connector) เทียบกับ 30MB ของ SendGrid
- ☐ ตั้งค่า queue retry/expiry ปัจจุบัน
- ☐ ใครมีสิทธิ์แก้ connector และมี change window เมื่อไร

### 2.4 เครือข่าย
- ☐ Exchange (หรือ relay/แอป) ออกพอร์ต **587** (สำรอง 2525, 465) ไป `smtp.sendgrid.net` ได้ ⚠️ ทดสอบจริงด้วย `Test-NetConnection smtp.sendgrid.net -Port 587`
- ☐ ไม่มี proxy/inspection ที่บล็อก STARTTLS

---

## 3. Phase 0 — เตรียมการ (≈ 1 สัปดาห์)

- ☐ ปิด Decision Log D1–D5
- ☐ กรอก Inventory ข้อ 2 ให้ครบ
- ☐ ขอใบเสนอราคา/ยืนยันเป็นลายลักษณ์อักษรจาก SendGrid: รองรับ **≥200,000/วัน และ ≥10,000/ชม.**, จำนวน Dedicated IP, ตาราง warm-up, SLA ⚠️
- ☐ แจ้งเจ้าของแอปทุกตัว: bounce/NDR จะเปลี่ยนที่มา (ดูหัวข้อ 6 ความเสี่ยง R1)
- ☐ revoke/rotate SendGrid API key เก่าที่เคยวางในแชต (2026-08-22) — key ใหม่ห้ามวางในแชตอีก
- ☐ ตั้ง change window + ผู้อนุมัติ + ช่องทางแจ้งเหตุ

**Go/No-go ออกจาก Phase 0:** ได้ยืนยันแผนจาก SendGrid + Decision Log ปิดครบ + Inventory ครบ

---

## 4. Phase 1 — ตั้งค่า SendGrid (≈ 1 สัปดาห์)

### 4.1 บัญชีและสิทธิ์
- ☐ สร้างบัญชีตามแผนที่ตกลง; เปิด 2FA ให้ทุก Teammate
- ☐ สร้าง **API key แบบจำกัดสิทธิ์เฉพาะ Mail Send** (ต่อ 1 ระบบ/ subuser ต่อ 1 key ถ้าทำได้) เก็บใน secret store ห้าม commit/วางแชต
- ☐ (ถ้า D5) สร้าง subuser ต่อระบบ

### 4.2 Domain Authentication (ทุก domain ที่ส่ง)
- ☐ ทำ Domain Authentication ใน SendGrid → ได้ CNAME (ประมาณ: 1 อัน mail/return-path + 2 อัน DKIM) ⚠️ ชื่อและจำนวนจริงดูจากหน้า Settings
- ☐ เพิ่ม CNAME ใน DNS (DNS-only ถ้า Cloudflare) → กด Verify
- ☐ Merge SPF ของเดิมกับสิ่งที่ SendGrid กำหนด (ห้ามมี SPF record ซ้ำ)
- ☐ DMARC: ถ้ายังไม่มี ให้เริ่มที่ `p=none` + rua ก่อน แล้วค่อยเข้มขึ้นหลังมีข้อมูล ⚠️
- ☐ ตรวจด้วย `dig` จากภายนอก (ไม่พึ่งแค่ปุ่ม Verify)

### 4.3 Dedicated IP และ Warm-up
- ☐ ซื้อ/จัด Dedicated IP ตามที่ตกลง จัด IP pool
- ☐ ยืนยันตารางเพิ่มปริมาณกับ SendGrid ⚠️ **ห้ามเดาตัวเลขในเอกสารนี้**
- ☐ เปิด Automated IP Warmup ถ้าแผนรองรับ ⚠️

### 4.4 Mail Settings (สำคัญกับเมลระบบ)
- ☐ **ปิด Click Tracking และ Open Tracking** สำหรับเมลระบบ/ราชการ (กันลิงก์ถูกเขียนใหม่) ⚠️ เช็กค่า default ของบัญชี
- ☐ ตรวจ Suppression settings (bounce/spam/unsubscribe)
- ☐ ตั้ง Event Webhook + **Signed Event Webhook** (เปิดหลัง Save แล้วกลับมา edit — UI ซ่อนตอนแรก)

### 4.5 ทดสอบ deliverability (ก่อนแตะ Exchange)
- ☐ ส่งทดสอบด้วย API/SMTP จากเครื่องทดสอบไปยัง: Gmail, Outlook.com, Yahoo, โดเมนลูกค้าจริง, โดเมนราชการ
- ☐ ตรวจ header: SPF=pass, DKIM=pass, DMARC=pass และ alignment
- ☐ **ดูผลจริงที่กล่อง inbox/junk** — ตอน POC เจอ Gmail รับแล้วทิ้งเงียบๆ (ไม่มี bounce) และอีกโดเมนเข้า Junk อย่าเชื่อแค่สถานะ "delivered"

**Go/No-go ออกจาก Phase 1:** SPF/DKIM/DMARC ผ่านทุก domain + เมลทดสอบถึง inbox ของผู้ให้บริการหลัก

---

## 5. Phase 2–4 — ตั้งค่า Exchange, นำร่อง, ย้ายจริง

### 5.1 ตั้ง Send Connector ไป SendGrid (ตัวอย่าง — ⚠️ ต้องทดสอบใน lab/นอกเวลาก่อน)

```powershell
# 0) สำรองค่าเดิมก่อนแตะอะไร
Get-SendConnector | Export-Clixml .\sendconnector-backup-$(Get-Date -f yyyyMMdd).xml
Get-ReceiveConnector | Export-Clixml .\receiveconnector-backup-$(Get-Date -f yyyyMMdd).xml

# 1) สร้าง connector ใหม่ (ยังไม่เปิดใช้จริง — Enabled = $false)
#    user = "apikey", password = API key  → ใส่ผ่าน Get-Credential ห้ามเขียนลงสคริปต์
$cred = Get-Credential   # Username: apikey
New-SendConnector -Name "SendGrid-Relay" `
  -AddressSpaces "SMTP:<domain-ผู้รับที่จะ ramp>;1" `
  -SmartHosts "smtp.sendgrid.net" -Port 587 `
  -SmartHostAuthMechanism BasicAuthRequireTLS -AuthenticationCredential $cred `
  -DNSRoutingEnabled $false -RequireTLS $true `
  -SourceTransportServers "<ชื่อ transport server>" -Enabled $false
```

- ⚠️ ชื่อพารามิเตอร์และพฤติกรรม cost/address space ต้องยืนยันกับเวอร์ชัน Exchange จริง
- Rollback = `Set-SendConnector "SendGrid-Relay" -Enabled $false` (เส้นทางเดิมกลับมาทันที) — **ต้องซ้อมก่อนใช้จริง**
- ☐ ทดสอบ: `Send-MailMessage` / telnet ผ่าน Exchange ไปยัง domain ทดสอบ 1 ฉบับ แล้วเช็กใน SendGrid Activity + webhook log

### 5.2 Phase 2 — นำร่อง (≈ 1 สัปดาห์)
- ☐ เลือก **ระบบ/โดเมนผู้รับเสี่ยงต่ำ** (ตาม D3) ประมาณ ≤5% ของปริมาณ
- ☐ เปิด connector สำหรับ scope นำร่องเท่านั้น
- ☐ ดูทุกวัน: bounce rate, spam complaint, deferral/block, ความสำเร็จของ webhook, เวลาส่งถึง
- ☐ เทียบจำนวนที่ Exchange ส่งออก vs ที่ SendGrid บันทึก (ใช้ `reconcile.ts` ใน `ψ/lab/sendgrid-log-poc/` เป็นแนวทาง — ตอน POC ตรง 52/52)

**Go/No-go ออกจาก Phase 2 (ค่าเกณฑ์เป็นข้อเสนอ ต้องให้มอสปรับ):**
- bounce (hard) < ~2% และไม่สูงกว่า baseline เดิมของ Exchange
- spam complaint ≈ 0
- ไม่มีเมลหายเงียบ (reconcile ตรง)
- เจ้าของแอปยืนยันว่าแอปทำงานปกติ

### 5.3 Phase 3 — ขยายปริมาณ (≈ 2–4 สัปดาห์ ⚠️ ขึ้นกับ warm-up)
- ☐ เพิ่มตามตาราง warm-up ที่ SendGrid ยืนยัน (ไม่ข้ามขั้น)
- ☐ ถ้า ramp ด้วย domain ผู้รับ: เพิ่ม address space ทีละ ISP/กลุ่ม domain ตามสัดส่วนที่เก็บใน Inventory 2.1
- ☐ ทุกครั้งที่เพิ่ม: ค้าง 2–3 วันทำการ ตรวจ metrics ก่อนเพิ่มต่อ
- ☐ ถ้า metrics แย่ลง → **หยุดที่ระดับเดิมหรือถอยหนึ่งขั้น** ไม่ดันต่อ

### 5.4 Phase 4 — ตัดจบและปิดงาน (≈ 1–2 สัปดาห์)
- ☐ ย้ายปริมาณเต็ม 100% ผ่าน SendGrid
- ☐ เก็บเส้นทางเดิมของ Exchange (connector เดิม) ไว้พร้อมใช้ตลอดช่วงสังเกตการณ์ — ห้ามลบ ("Nothing is Deleted")
- ☐ ตรวจ peak สูงสุดจริงเทียบกับ limit ของแผน
- ☐ อัปเดต SPF: เอา IP/ข้อความของเส้นทางเดิมออก **เฉพาะเมื่อมั่นใจว่าไม่มีใครส่งทางนั้นแล้ว** (เช็กจาก Exchange log)
- ☐ ปิดงาน: บันทึก retro + learnings (`rrr`)

---

## 6. ความเสี่ยงและวิธีรับมือ

| # | ความเสี่ยง | ผลกระทบ | มาตรการ |
|---|---|---|---|
| R1 | แอปที่ parse NDR/bounce | bounce ไปที่ return-path ของ SendGrid ไม่กลับ Exchange → แอปไม่รู้ว่าเมลเด้ง | ถามเจ้าของแอปทุกตัวใน Phase 0; เปลี่ยนเป็นอ่านจาก webhook/API |
| R2 | Suppression list | ผู้รับที่เคย bounce/unsub ถูกหยุดส่ง ต่างจาก Exchange ที่ส่งซ้ำ | แจ้งเจ้าของแอป; มี process ลบ suppression เมื่อจำเป็น |
| R3 | Click/Open tracking เปิดอยู่ | ลิงก์ในเมลถูกเขียนใหม่ | ปิดตั้งแต่ Phase 1 |
| R4 | SPF ซ้ำ/เกิน 10 lookups | SPF permerror → เมลเข้า spam | merge, นับ lookup |
| R5 | IP ไม่ warm / ปริมาณกระโดด | ถูก throttle, เข้า spam, IP reputation เสีย | ทำตามตาราง warm-up; ห้ามข้ามขั้น |
| R6 | เกิน rate limit ของแผน (POC: trial ส่งได้ 52/100) | เมลค้าง/ตกหล่น | ยืนยันแผนใน Phase 0; monitor 429/deferral |
| R7 | เมล user Outlook ถูกรวมโดยไม่ตั้งใจ (D1-A) | ปริมาณเกิน, เมลส่วนตัวออกทาง SendGrid | ตัดสินใจ D1 ให้ชัดก่อน |
| R8 | เมลขนาดใหญ่ | ถูก SendGrid ปฏิเสธ (30MB) | เทียบกับ limit ของ Exchange; แจ้งเจ้าของแอป |
| R9 | เมลหายเงียบที่ปลายทาง (Gmail ทิ้งหลังรับ) | ผู้ใช้ไม่ได้รับ ไม่มี bounce | seed test หลายผู้ให้บริการ; เทียบกับ inbox จริง |
| R10 | API key รั่ว | ถูกใช้ส่งสแปมในนามองค์กร | key จำกัดสิทธิ์, secret store, rotate, ไม่วางแชต |
| R12 | ผู้ใช้ Outlook ไม่ได้รับ NDR เมื่อพิมพ์ที่อยู่ผิด (D1-A) ⚠️ | SendGrid รับเมลแล้วบันทึก bounce เป็น event ตามที่จำได้ ไม่ส่ง NDR กลับกล่องผู้ใช้ | แจ้งผู้ใช้ก่อนย้าย; ตัดสินใจว่าจะทำ notification จาก webhook หรือไม่; ยืนยันพฤติกรรมกับ SendGrid |
| R13 | ปริมาณจริงไม่ทราบ | เลือกแผน/กำหนด warm-up ไม่ถูก, เกิน limit แล้วเมลค้าง | ดึงตัวเลขจาก Exchange message tracking ก่อนตกลงแผน (ทำเองได้ ไม่ต้องรอลูกค้า) หรืออย่างน้อยวัดช่วงนำร่อง |
| R14 | เมลที่ส่งถึงโดเมนของเราเอง (internal-to-internal) อาจวนออกไป SendGrid แล้ววนกลับมา MX ของ Exchange ⚠️ (zcode + agy ชี้ตรงกัน) | ขึ้นกับว่าโดเมนเป็น authoritative ใน Exchange และตั้ง address space/cost ของ Send Connector อย่างไร; เมลวนช้า/ผ่านนอกองค์กรโดยไม่จำเป็น และ Receive Connector อาจมองเป็น spoof | ตั้งค่าให้โดเมนของเราถูกส่งภายในเสมอ (ไม่ใช้ address space `*` ครอบโดเมนตัวเอง) และ **ทดสอบใน lab ก่อน** อย่าเดา |
| R11 | ผ่าน Exchange แล้ว SendGrid ล่ม | เมลค้างใน queue ของ Exchange | ตั้ง queue retry/expiry ให้เพียงพอ; ซ้อมสลับกลับ |

---

## 7. Log และ Monitoring

- ☐ **Event Webhook → เก็บลง DB ของเราเอง** เพราะ SendGrid เก็บ Activity ได้สูงสุด 30 วัน แต่ TOR ต้องการ ≥90 วัน (POC: `ψ/lab/sendgrid-log-poc/` — server.ts รับ webhook + reconcile.ts กระทบยอดรายวัน)
- ☐ POC นี้ทดสอบที่ระดับหลัก 50–100 ฉบับ **ยังไม่เคยรับ 200,000/วัน** — ต้องทำ capacity test ก่อนใช้จริง (มีเอกสาร capacity/RPO/RTO ที่ 500k/วัน ใน retro `2026-08/22/04.43_sendgrid-poc-to-production-planning.md`)
- ☐ Dashboard/alert อย่างน้อย: ฉบับ/ชม., delivered %, bounce %, deferred, blocked, spam report, webhook ล้มเหลว, ขนาดคิวฝั่ง Exchange
- ☐ Reconcile รายวัน: Exchange message tracking vs SendGrid events (ตัวเลขต้องตรง ±ตามที่ตกลง)

---

## 8. Rollback และ Incident

| สถานการณ์ | ทำอะไร | ใครตัดสิน |
|---|---|---|
| Bounce/complaint พุ่ง | หยุดเพิ่มปริมาณ → ถอยขั้นก่อนหน้า → ตรวจสาเหตุ | มอส |
| SendGrid ล่ม/ถูกระงับบัญชี | `Set-SendConnector "SendGrid-Relay" -Enabled $false` → เส้นทางเดิมกลับ | มอส / Exchange admin |
| เมลหายเงียบ | หยุดขยาย, seed test, เปิด ticket กับ SendGrid | มอส |
| API key รั่ว | revoke ทันที, สร้างใหม่, ตรวจ Activity หาการส่งผิดปกติ | มอส |

- ☐ **ซ้อม rollback อย่างน้อย 1 ครั้งก่อนเริ่ม Phase 2** และจับเวลา

---

## 9. ประมาณการเวลา (ยังไม่ได้อ้างอิงเอกสาร)

| Phase | งาน | ระยะเวลา |
|---|---|---|
| 0 | เตรียมการ, ยืนยันแผน | ~1 สัปดาห์ |
| 1 | ตั้งค่า SendGrid + ทดสอบ deliverability | ~1 สัปดาห์ |
| 2 | นำร่อง | ~1 สัปดาห์ |
| 3 | ขยายปริมาณ/warm-up | ~2–4 สัปดาห์ ⚠️ |
| 4 | ตัดจบ + สังเกตการณ์ | ~1–2 สัปดาห์ |
| **รวม** | | **~6–9 สัปดาห์** |

ตัวขับเวลาหลักคือ warm-up และ change window ของ Exchange

---

## 10. คำถามที่ยังเปิดอยู่

**ข้อมูลที่มอสแจ้ง 2026-09-21 (ยังไม่ยืนยันกับลูกค้า):**
- ขอบเขต: ทุกเมลขาออกไป SendGrid, รับได้ ~200k/วัน (D1=A)
- ระบบที่ส่งเมล: มากกว่า 3 ระบบ, ทีม frontend/backend ดูแลฝั่งแอป และอีกทีมดูแลฝั่ง server
- ปริมาณจริง: **ไม่ทราบ** (มอสระบุว่าไม่สนใจ) → ความเสี่ยง: ปริมาณจริงกำหนดขนาดแผนและตาราง warm-up
- แอปที่ parse NDR/bounce: **ไม่มี** (ปิด R1 ตามที่มอสแจ้ง แต่ผู้ใช้ Outlook ยังอาจคาดหวัง NDR ดู R12)
- Exchange: เวอร์ชันไม่ทราบ, ไม่เป็นอุปสรรคตามที่มอสแจ้ง
- DNS: ผู้ให้บริการ/ผู้ดูแล **ยังไม่ชัด** (คำตอบไม่ชัดเจน ต้องถามซ้ำ)
- เครือข่าย: **ยังไม่ทราบ** ต้องทดสอบพอร์ต 587 ก่อน
- Log: ตั้งใจใช้ SendGrid API — ⚠️ API/Activity เก็บย้อนหลังได้สูงสุด ~30 วัน ไม่พอสำหรับ TOR ≥90 วัน ต้องเก็บผ่าน Event Webhook เอง

**ยังเปิดอยู่:**
1. D2 (ยืนยันเส้นทาง), D3, D4, D5 (หัวข้อ 1)
2. ผู้ให้บริการและผู้ดูแล DNS
3. ผลทดสอบพอร์ต 587 จากเครือข่ายจริง
4. รายชื่อแอปและเจ้าของแต่ละระบบ (Inventory 2.1)
5. ข้อกำหนด log retention จริง (≥90 วันตาม TOR หรือมากกว่า) และวิธีเก็บ
6. ข้อกำหนดด้านข้อมูล: เมลมีข้อมูลส่วนบุคคล/ความลับราชการหรือไม่ — เมลจะวิ่งผ่านระบบ SendGrid (ต่างประเทศ) ต้องตรวจ PDPA/ข้อกำหนดของลูกค้า ⚠️ **ยังไม่ได้พิจารณาในเอกสารนี้**
7. ⚠️ ทุกจุดที่มีเครื่องหมายนี้ ต้อง verify กับเอกสาร SendGrid / Exchange จริง

---

## อ้างอิงภายใน

- [[project_wym_tor_email_sendgrid]] — ผลเทียบ TOR และข้อจำกัดของ SendGrid
- `ψ/lab/sendgrid-log-poc/` — POC เก็บ log ผ่าน Event Webhook + reconcile
- `ψ/memory/learnings/2026-08-21_sendgrid-native-retention-caps-at-30-days.md`
- `ψ/memory/retrospectives/2026-08/22/04.43_sendgrid-poc-to-production-planning.md`
