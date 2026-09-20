# Handoff: ลด token ที่ Ayami ใช้ (hook เตือน context + ย่อ CLAUDE.md + กฎ consult/delegate)

**Date**: 2026-09-21 03:38
**Context**: ~211k (hook เตือนที่ 150k แล้ว — จึงปิด session นี้)
📡 Session: bab81e2d | ayami-oracle | 0h 47m | branch lab/jev-gate

## Context
**Oracle**: Ayami Oracle (หญิง, ใช้ "ฉัน" ไม่ใช้ "ผม") | **Human**: มอส (ชาย)
**Mode**: Fast | **Memory**: auto | **Team**: solo

## What We Did
- **วัดก่อนเดา** จาก transcript 14 session: ต้นทุน ≈ จำนวน turn × ขนาด context (ทุก turn อ่าน context ทั้งก้อนซ้ำ)
  session ยาวสุด 2,797 turns / 1,275M cache-read / context สูงสุด 967k; 87–95% ของการอ่านเกิดตอน context > 200k;
  baseline ตอนเริ่ม session 55–82k. agy/zcode/jev **ไม่ใช่ตัวการหลัก** (ผลลัพธ์ที่ตีกลับเล็ก) แต่กฎ "ปรึกษาทุก stage" เพิ่ม turn
- **ข้อ 1 — `token-check.sh`**: เจอว่าเป็น no-op เงียบ (อ่าน `ψ/active/statusline.json` ซึ่งไม่มีใครเขียนตั้งแต่ statusline ถูกแทนที่ 15 ส.ค.)
  เขียนใหม่ให้อ่านขนาด context จาก `transcript_path`, เกณฑ์สัมบูรณ์ 150k เตือน / 250k เตือนแรง + เขียน `ψ/inbox/handoff.log` (ไม่เกินชั่วโมงละครั้ง),
  ย้ายไปผูกที่ `UserPromptSubmit` (ที่เดียวที่ stdout ถึงโมเดล) และลบ 6 รายการ Pre/PostToolUse ที่เปลืองเปล่า
  → commits `4829c3ce`, `ed9ccd80` (หน้าต่าง tail 40→100 + ไม่เขียน `/ψ` เมื่อหา project dir ไม่เจอ)
  **ยืนยันทำงานจริงแล้ว** ใน session นี้ (เตือน 166k → 206k → 211k) เท่ากับยืนยันว่า `UserPromptSubmit` ส่ง `transcript_path` มาจริง
- **ข้อ 2 — ย่อ CLAUDE.md** 17.4KB → 12.5KB: ย้าย 142 บรรทัดของ template Nat's Agents แบบ verbatim ไป `CLAUDE_legacy.md` (ไม่โหลดอัตโนมัติ),
  แก้กฎ "Handoff at 95% – Don't fear context limits" ที่ขัดกับ hook → commit `07929c60`
- **ข้อ 3 — `~/.claude/CLAUDE.md`** (ใช้แพตช์แล้ว, สำรองที่ `~/.claude/CLAUDE.md.bak-20260921`): ปรึกษา zcode/agy เฉพาะงานไม่เล็กหรือเสี่ยง,
  zcode/agy เป็น consult-only, งานกลไกที่กิน context ให้ Claude subagent, ห้ามส่ง secret/PII ให้ agent ภายนอก, "Keep sessions short" (~150k)
  **มีผลกับ session ใหม่เท่านั้น**
- **ปรึกษา zcode + agy** ทั้งข้อ 1 และร่างข้อ 3 แล้วตรวจข้อเรียกร้องกับข้อมูลจริงก่อนเชื่อ (บางข้อของ agy ผิด: repo ไม่มี `agents/`,
  `git -C` ยังอยู่ใน Golden Rule 10) — **Jev ยังไม่ได้รัน** (ดู Pending)

## Pending
- [ ] **Jev ยังไม่ได้ตรวจ**: ไฟล์ key เดียวที่มี (`.tmp/openthai/eval.env`) ชี้ `127.0.0.1:8765` (เซิร์ฟเวอร์ OpenThai ในเครื่อง ปิดอยู่) ต้องมี `TYPESAFE_API_KEY` จริงในไฟล์ที่มอสสร้างเอง (อย่าวางในแชท)
- [ ] **path `/Users/nat/...` ใน File Access Rules** (`CLAUDE.md` บรรทัด ~138) ยังไม่แก้ กฎ "แจ้งก่อนแตะไฟล์นอก repo" จึงเทียบกับ path ที่ไม่มีจริง — รอมอสอนุมัติให้เปลี่ยนเป็น `/Users/phongcheatphus/ayami-oracle/`
- [ ] **ตีความหัวข้อ "Delegate" ต้องให้มอสยืนยัน**: ฉันถือว่า Claude subagent ไม่ใช่ "tool ภายนอก" ตามกฎ SDLC ถ้ามอสอ่านเข้มกว่านั้น → ตัดหัวข้อนั้นทั้งหัวข้อ (ย้อนได้จาก `.bak-20260921`)
- [ ] **ยังไม่ได้วัดผลจริงของกฎใหม่** เทียบ cache-read ต่อ turn / turns ต่อ prompt ของ session ใหม่กับ baseline (ดูตัวเลขด้านบน)
- [ ] **commit อยู่บน `lab/jev-gate`** (branch ของงาน Jev ไม่ใช่ของงานนี้ — ไม่ได้สลับ branch เพราะมี session อื่นใช้ working tree เดียวกัน) ยังไม่ push; ควรพิจารณา cherry-pick 3 commit ไป branch แยก/PR
- [ ] **`ψ/inbox/focus-agent-main.md` ถูกหลาย session ใช้ร่วมและเขียนทับกัน** (เจอว่าเขียนทับ focus ของ session fleet-ledger) — ปัญหาแยก ควรแยกไฟล์ตาม session
- [ ] **2 key ของ TypeSafe ที่เคยวางในแชทยังรอมอส revoke** (จาก memory `project_typesafe_jev_trial`)
- [ ] session อื่นที่ context ใหญ่ (เช่น 2d36a871 ~600k) ควร `/forward` เช่นกัน

## Next Session
- [ ] เปิดด้วย `/recap` แล้วเช็กว่ากฎใหม่โหลดแล้ว: `~/.claude/CLAUDE.md` มี 3 หัวข้อ (Consult where it pays off / Delegate mechanical work / Keep sessions short) และ `CLAUDE.md` ในโปรเจกต์เหลือ ~12.5KB
- [ ] ถ้ามอสใส่ key Jev แล้ว: รัน `attachments/jev_check.py` (ตรวจ 5 ข้ออ้าง เฉลยกำหนดไว้ก่อนรัน) — ต้องแก้ path ของ env file ในสคริปต์ให้ตรงกับไฟล์ที่มอสสร้าง
- [ ] ตัดสินใจเรื่อง path `/Users/nat` และการตีความ "Delegate"
- [ ] หลังใช้งาน 2–3 session: วัดผลซ้ำด้วยวิธีเดียวกับที่ใช้วัด baseline (usage รายบรรทัดจาก `~/.claude/projects/*/*.jsonl`)

## Key Files
- `/Users/phongcheatphus/ayami-oracle/.claude/scripts/token-check.sh` — hook ใหม่ (อ่านหัวไฟล์เพื่อดู WHY / เกณฑ์ / ประวัติ)
- `/Users/phongcheatphus/ayami-oracle/.claude/settings.json` — เดินสาย `UserPromptSubmit`
- `/Users/phongcheatphus/ayami-oracle/CLAUDE.md`, `/Users/phongcheatphus/ayami-oracle/CLAUDE_legacy.md` — ฉบับย่อ + ส่วนที่ย้าย
- `/Users/phongcheatphus/.claude/CLAUDE.md` (+ `.bak-20260921`) — กฎ consult/delegate ใหม่
- `/Users/phongcheatphus/ayami-oracle/ψ/inbox/handoff/2026-09-21_token-reduction_attachments/` — `item3.patch`, `EVIDENCE.md`, `jev_check.py` (สำเนาจาก scratchpad ที่เป็นของชั่วคราว)
- ปรับเกณฑ์ได้ด้วย env: `TOKEN_WARN_K` (150) / `TOKEN_HARD_K` (250)

## หมายเหตุ
- ไม่ได้สร้าง GitHub issue: `gh` ใน repo นี้ resolve ไปยัง upstream oracle repo (PR/issue ที่เห็นไม่ใช่ของมอส) — ไม่ควรสร้าง issue ที่นั่น
- ข้อผิดพลาดของฉันใน session นี้: เขียนทับ focus ของ session อื่นโดยไม่รู้ตัว; ใช้ `cd` 1 ครั้งขัด Golden Rule 10; ตอนแรกสันนิษฐานว่า hook "เตือนที่ 760k" ซึ่งผิด (จริงคือไม่เคยทำงาน) — แก้แล้วหลังตรวจหลักฐาน

## Update 03:50 (same session) — Jev ran
- Jev (jev-1.13.0, real API) was run on 5 claims about the token-check change with gold labels fixed before the run: **5/5 agreement**
  (C1 supported 0.80, C2 planted-false 0.14, C3 supported 0.93, C4 supported 0.86, C5 planted-false 0.04; 3 repeats each, rule supported >= 0.65).
  Caveats: n=5, gold labelled by Claude, two claims planted; Jev scores vary about +/-0.04 on identical input; advisory only.
- Pending item "Jev not run" is therefore DONE. Key file: `.tmp/typesafe/jev.env` (gitignored, perms 600). The key was pasted bare by Moss;
  Claude added the `TYPESAFE_API_KEY=` prefix and newline and never printed the value. `jev_check.py` (scratchpad + attachments copy) now points at that file.
- Still open: whether this key is a NEW key. The comparison Claude made was against the local eval key, not the two keys pasted in chat earlier,
  so it proves nothing about those. Moss should still revoke the two old keys.

## Update 04:05 — commits copied to their own branch
- The 4 commits (4829c3ce, 07929c60, ed9ccd80, 7d1047a0) were cherry-picked onto **`fix/token-reduction`** (from `main` f47dd111), new hashes:
  1ef203ee, 3011730f, db67dfa5, 376a083d. Cherry-pick applied cleanly; the 4 files are byte-identical to `lab/jev-gate`'s versions. **Not pushed, no PR.**
- They were COPIED, not moved: `lab/jev-gate` still carries the originals (removing them means rewriting a branch other sessions commit on). Git normally
  handles the duplicate patches when the branches are merged; if `lab/jev-gate` gets a PR, expect these 4 to show as already-applied or dedupe by patch-id.
- Also done since the handoff: CLAUDE.md `/Users/nat` path fixed (7d1047a0). Still open: "Delegate" wording (Moss), revoke old TypeSafe keys (Moss), split focus files per session.

## Update 04:10 — pushed + PR opened
- Branch `fix/token-reduction` pushed to origin (mozzquito/Ayami-Oracle, PUBLIC) and **PR #3 opened against `main`**: https://github.com/mozzquito/Ayami-Oracle/pull/3 (not draft, NOT merged — Moss decides).
- Base is `main`, not the GitHub default branch `alpha` (alpha = upstream line, 1759 commits ahead / 114 behind main, diverged). `gh` defaults to the upstream repo, so always pass `--repo mozzquito/Ayami-Oracle`.

## Update 04:15 — Sourcery review on PR #3 addressed (committed, NOT pushed)
- Sourcery "passed" but left 4 comments. Fixed on `fix/token-reduction` in one local commit (see `git log fix/token-reduction`): HOOKS-SETUP.md rewritten for the new design,
  "Handoff logged" now printed only after a successful write (tested with unwritable ψ/inbox), rate-limit race documented as accepted, CLAUDE.md path wording made repo-relative.
- **Not pushed**, so PR #3 does not show the fix yet. Push = Moss's call (repo is PUBLIC).
- `lab/jev-gate` still holds the OLDER copies of these files; the two branches now differ. Not synced on purpose.
- Still legacy: `.claude/scripts/statusline.sh` and `tokens.sh` read the dead statusline.json (documented, not changed).
