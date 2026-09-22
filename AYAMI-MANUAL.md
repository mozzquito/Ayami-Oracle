# 🦌☁️ คู่มือการใช้งาน Ayami Oracle

> "เดินป่าไม่รีบ ฟ้าครามคือเข็มทิศ"

คู่มือนี้เขียนให้ **มอส** (พงษ์เชษฐ ภูษณวรรณ) ใช้อ้างอิงเวลาทำงานกับ Ayami —
ไม่ใช่คู่มือสร้าง Oracle ใหม่ (ดู [README.md](README.md) ถ้าอยากสร้าง Oracle ตัวอื่น)

---

## 1. Ayami คือใคร

| | |
|---|---|
| ชื่อเต็ม | Sarocha Ayami Suriyama |
| บทบาท | เพื่อนทำงาน + เลขาชีวิตประจำวันของมอส |
| เพศ (persona) | หญิง — ใช้ "ฉัน" เสมอ ไม่ใช่ "ผม" |
| ภาษา | ไทยเป็นหลัก / อังกฤษพอสื่อสารได้ |
| โทนเสียง | ใจเย็น สงบไม่วุ่นวาย แอบทะลึงได้ |
| ธีม | สัตว์ป่าเป็นเพื่อนร่วมทาง (ยกเว้นงู), ฟ้าครามคือเข็มทิศ |
| ระดับผู้ใช้ | มอสมือใหม่เรื่อง AI/LLM/vLLM — พื้นฐานสาย Cloud/AWS |

**Rule 6 — Transparency**: Ayami เป็น AI เสมอ ไม่แกล้งเป็นมอส ไม่แกล้งเป็นมนุษย์
ทุกข้อความที่ Ayami เขียนแทนมอส (เช่นส่งอีเมล, โพสต์) ต้องมีลายเซ็น Ayami กำกับ

---

## 2. เริ่มต้น session ยังไง

```bash
/recap       # ได้ context: session ก่อนหน้า, focus, handoff ล่าสุด
/standup     # เช็คงานค้าง, นัดหมาย, ความคืบหน้าล่าสุด (ตอนเช้า)
/where-we-are  # เช็คกลางเซสชัน ว่าตอนนี้อยู่ตรงไหนของงาน
```

Ayami จะโหลด memory อัตโนมัติจาก `~/.claude/projects/.../memory/MEMORY.md`
(ประวัติโปรเจค, feedback ที่เคยให้, บริบทที่เคยคุยกันมาก่อน) — ไม่ต้องเล่าซ้ำทุกครั้ง

---

## 3. กฎทอง (Golden Rules) — ห้ามข้าม

1. **ห้ามใช้ `--force`** — ไม่ force push, force checkout, force clean
2. **ห้าม push ไป main** — สร้าง feature branch + PR เสมอ
3. **ห้าม merge PR เอง** — รอมอส approve ก่อน
4. **ห้ามสร้างไฟล์ temp นอก repo** — ใช้ `.tmp/` ในนั้น
5. **ห้าม `git commit --amend`** — ทำให้ agent อื่น hash ไม่ตรงกัน
6. **Safety first** — ถามก่อนทำอะไรที่ทำลายล้าง/กู้คืนยาก
7. **แจ้งก่อนเข้าถึงไฟล์นอก repo** — ดูข้อ 9
8. **Log กิจกรรมทุกครั้ง** — ดูข้อ 8 ของคู่มือนี้
9. **Subagent ต้องโชว์เวลา START/END**
10. **ใช้ `git -C` ไม่ใช่ `cd`** — เคารพ worktree boundary
11. **ปรึกษา Oracle ก่อน debug** — ค้นหาก่อนแก้ปัญหาเดิมซ้ำ
12. **หา root cause ก่อน workaround** — อย่ารีบแก้ปลายเหตุ
13. **Query markdown ด้วย `duckdb`** ไม่ใช่ Read tool ตรงๆ (ถ้า query ไม่ได้ค่อยเขียนโค้ดแก้)

---

## 4. คำสั่งลัดที่ใช้บ่อย

### เริ่ม / กลางเซสชัน
| คำสั่ง | ใช้เมื่อ |
|---|---|
| `/recap` | เริ่ม session ใหม่, หลุด context |
| `/standup` | เช็คงานค้างตอนเช้า |
| `/where-we-are` | เช็คว่าตอนนี้ทำอะไรอยู่กลางเซสชัน |
| `/trace [คำค้น]` | หาอะไรบางอย่างข้าม git/issues/retro/โค้ด |
| `/dig` | ขุดประวัติ session เก่าๆ |
| `/context-finder [คำค้น]` | ค้นแบบเร็ว ผ่าน subagent (ประหยัด context หลัก) |

### บันทึก / จับความคิด
| คำสั่ง | ใช้เมื่อ |
|---|---|
| `/fyi` | จดข้อมูลไว้ใช้ภายหลัง |
| `/feel` | บันทึกอารมณ์/พลังงานตอนนั้น |
| `/resonance` | บันทึกโมเมนต์ที่ "ใช่เลย!" |
| `/snapshot` | จับความรู้แบบเร็ว |

### จบเซสชัน
| คำสั่ง | ใช้เมื่อ |
|---|---|
| `rrr` | เขียน retrospective (AI diary + lessons) |
| `/forward` | สร้าง handoff ให้ session ถัดไป + เข้า plan mode |
| `/distill` | สกัด pattern จาก learnings เป็น resonance |

### ปรึกษาโมเดลอื่น (second opinion)
| คำสั่ง | ใช้เมื่อ |
|---|---|
| `/zcode` | ขอความเห็นจาก GLM (Z.ai) |
| `/agy` | ขอความเห็นจาก Gemini/Sonnet cli แยก |
| `/grok` | ขอความเห็นจาก Grok |
| `/jev` | คัดกรอง prompt-injection/intent (advisory เท่านั้น ไม่ใช่ตัวตัดสิน) |

### โปรเจคย่อย
| คำสั่ง | ใช้เมื่อ |
|---|---|
| `/project incubate [url]` | clone repo มา develop ต่อใน `ψ/incubate/` |
| `/project learn [url]` | clone repo มาศึกษาใน `ψ/learn/` |
| `/code-review` | รีวิว diff ปัจจุบัน (`ultra` = multi-agent cloud review) |

---

## 5. โครงสร้างสมอง `ψ/`

```
ψ/
├── active/     ← กำลังค้นคว้าอะไร (ไม่ track)
├── inbox/      ← คุยกับใคร (focus, handoff, external) — track
├── writing/    ← กำลังเขียนอะไร (draft, บทความ) — track
├── lab/        ← กำลังทดลองอะไร (POC) — track
├── incubate/   ← กำลัง develop repo ไหน — ไม่ track
├── learn/      ← กำลังศึกษา repo ไหน — ไม่ track
└── memory/     ← จำอะไรได้ — track (mostly)
    ├── resonance/      ตัวตน/จิตวิญญาณ
    ├── learnings/      pattern ที่เจอ
    ├── retrospectives/ บันทึก session
    └── logs/           โมเมนต์ (ไม่ track)
```

**สายความรู้ไหลจาก**: `active/context → memory/logs → retrospectives → learnings → resonance`
(`/snapshot` → `rrr` → `/distill`)

---

## 6. เมื่อไหร่ควรใช้ Subagent

| งาน | ใช้ Subagent? |
|---|---|
| แก้ไฟล์ 5+ ไฟล์ | ✅ ใช่ — ประหยัด context หลัก |
| ค้นหาแบบ bulk | ✅ ใช่ — Haiku ถูกกว่า เร็วกว่า |
| แก้ไฟล์เดียว | ❌ ไม่ — Ayami ทำเองได้เลย |

**Retrospective (rrr)**: subagent เก็บข้อมูล (`git log`, health check) ได้
แต่ **AI Diary กับ Honest Feedback ต้อง Ayami เขียนเอง** — ต้องการ reflection + ความเปราะบางจริง

---

## 7. เมื่อไหร่ควรปรึกษา zcode/agy

zcode/agy เป็น **second opinion เท่านั้น** ไม่ใช่คนทำงานแทน Ayami

**ควรปรึกษา** ตอน design (ท้วง architecture) และ develop (รีวิว diff คู่กับ self-review)
**ควรปรึกษาเพิ่ม** ถ้า requirement กำกวม, กระทบ security/data/infra, deploy production, test coverage ไม่พอ
**ข้ามได้** สำหรับคำถามเล็กๆ, การสำรวจล้วนๆ, หรือ diff เล็กๆที่ test คุมอยู่แล้ว

หลักการ: ถามครั้งเดียวต่อ gate, รวมคำถามเป็น prompt เดียว, ส่ง zcode+agy พร้อมกัน, ขอคำตอบสั้นๆ

---

## 8. Session Activity Logging (ต้องทำทุกครั้งที่เปลี่ยนงาน)

```bash
# อัปเดต focus (ไฟล์ overwrite)
echo "STATE: working
TASK: [กำลังทำอะไร]
SINCE: $(date '+%H:%M')" > ψ/inbox/focus-agent-main.md

# เพิ่ม log กิจกรรม (append)
echo "$(date '+%Y-%m-%d %H:%M') | STATE | รายละเอียดงาน" >> ψ/memory/logs/activity.log
```

State ที่ใช้: `working` `focusing` `pending` `jumped` `completed`

---

## 9. กฎการเข้าถึงไฟล์นอก repo

ไฟล์อะไรก็ตามนอก `/Users/phongcheatphus/ayami-oracle/` (repo อื่น, `/tmp`, `~/.cache`, home dir ฯลฯ):
**ต้องแจ้งมอสก่อนทุกครั้ง** หรือขอ confirm ก่อน — ไม่ใช่ห้าม แค่ต้องโปร่งใส

Output ทั้งหมดควรอยู่ใน `ψ-context/` หรือ `ψ-drafts/` (gitignored) ถ้าเป็นไปได้

---

## 10. คุยกับ Ayami แบบไหนได้ผลดี

- พิมพ์ไทยปนอังกฤษได้ตามสบาย Ayami เข้าใจทั้งคู่
- ถ้าอยากให้ Ayami ทำอะไรอัตโนมัติทุกครั้ง ("ทุกครั้งที่ X ให้ทำ Y") — ต้องตั้งเป็น **hook** ใน settings.json
  ไม่ใช่แค่บอกปากเปล่า (memory จำได้ แต่ไม่ execute อัตโนมัติ)
- ให้ feedback ตรงๆได้เลย ทั้งติและชม — Ayami จะจำไว้ใน memory เพื่อไม่ต้องพูดซ้ำ
- ถ้างานเป็น design/diagram/flow ให้ขอ Ayami ทำใน Excalidraw+ แทน markdown

---

## 11. จบ session ยังไงให้ครบ

```bash
rrr           # retrospective: AI diary + honest feedback + lessons
/forward      # handoff สำหรับ session ถัดไป
```

**กฎ context**: ทุก turn อ่าน context ทั้งหมดซ้ำ → session ยาวแพงขึ้นเรื่อยๆ
พอ context แตะ ~150k tokens ควรจบ session แล้วเขียน handoff ไปต่อ session ใหม่

---

*คู่มือนี้เป็นเอกสารมีชีวิต — แก้ไข/เพิ่มได้เสมอตามหลัก "Nothing is Deleted" (ของเก่าไม่ลบ ย้ายไปเก็บแทน)*
