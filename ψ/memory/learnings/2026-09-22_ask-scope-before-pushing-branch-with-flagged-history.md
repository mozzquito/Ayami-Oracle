---
pattern: a short "push branch X" instruction is not blanket consent when memory/git-log shows that branch has previously-blocked sensitive commits — check divergence first, then ask for scope
date: 2026-09-22
source: "rrr: ayami-oracle"
concepts: [git, push, public-repo, evisa, data-sensitivity, ask-before-acting]
---

# Ask scope before pushing a branch with flagged history

## Context

มอสสั่งสั้นๆ ว่า "push branch lab/jev-gate" ไม่มี qualifier เพิ่มเติม ปกติ `git push` เป็น action ที่ user
สั่งตรงๆ แล้วทำได้เลย แต่ branch นี้มีประวัติเฉพาะ: memory (`project_typesafe_jev_trial.md` และ
session-metrics log ของวันก่อนหน้า) บันทึกไว้ชัดว่าเคย push branch นี้แล้วถูก auto-mode classifier บล็อก
2 ครั้ง (Data Exfiltration, Out-of-Place Publication) เพราะมี commit ที่มี eVisa/Wayama data และ repo
ปลายทาง (`mozzquito/Ayami-Oracle`) เป็น **PUBLIC** repo

## What we found

`git log origin/lab/jev-gate..lab/jev-gate --oneline` เผยว่า local นำหน้า origin 20 commits รวมถึง
commit ที่ตั้งชื่อตัวเองชัดเจนว่า `7d40feb7 memory: eVisa/Wayama retros, learnings and session metrics
(local only)` — ตรงกับความเสี่ยงที่เคยถูกบล็อกมาก่อนเป๊ะๆ ถ้า push ตามคำสั่งตรงตัวโดยไม่เช็คก่อน จะ publish
ข้อมูลลูกค้า (eVisa/Wayama) ไปที่ public GitHub repo จริง

## Rule

ก่อน push branch ใดๆ ตามคำสั่งสั้นของ user:
1. เช็คว่า remote เป็น public หรือ private repo (`gh repo view --json visibility`)
2. เช็ค divergence จริง: `git log <remote-branch>..<local-branch> --oneline`
3. สแกน commit message/diff ของ commit ที่จะ push หา keyword ที่เคยถูก flag ไว้ (eVisa, Wayama, PII,
   "(local only)", ชื่อโปรเจกต์ sensitive อื่นๆ ที่ memory เตือนไว้)
4. ถ้าพบ commit ที่ตรงกับความเสี่ยงที่เคยถูกบล็อกมาก่อน — หยุดถาม scope ก่อนเสมอ (AskUserQuestion หรือถามตรงๆ)
   อย่าตัดสินใจเองว่าจะ push ทั้งหมดหรือกรองอะไรออกโดยไม่แจ้ง ทั้งสองทางเลือกเสี่ยงเกินไปเมื่อ blast radius
   คือ public repo กับข้อมูลลูกค้าจริง
5. ถ้า user เลือก scope ที่แคบกว่า local branch เต็ม (เช่น "push แค่ commit ล่าสุด") ให้ใช้
   [[push-time-check-outgoing-commits-and-mutate-on-a-copy]] pattern — temp worktree + cherry-pick เฉพาะ
   commit ที่ต้องการ แล้ว push จาก worktree นั้น ไม่แตะ local branch ที่มี history เดิมอยู่

## How to apply

Trigger เมื่อ: คำสั่ง push/publish อะไรก็ตามที่ (a) ปลายทางเป็น public หรือ shared remote, (b) branch หรือ
repo มีประวัติที่ memory/session-metrics เคยบันทึกว่าเสี่ยงหรือเคยถูกบล็อกมาก่อน — เช็ค divergence และสแกน
ก่อน push เสมอ แม้คำสั่งจาก user จะสั้นและดูเหมือนไม่มีเงื่อนไข
