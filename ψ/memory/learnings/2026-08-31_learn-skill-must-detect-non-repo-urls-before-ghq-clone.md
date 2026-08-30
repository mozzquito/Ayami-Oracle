---
pattern: "The /learn skill's default flow assumes every target is a GitHub-clonable repo (ghq get + symlink origin/ + 3-agent codebase exploration). When the argument is actually a docs page, blog article, or spec page (not a repo), that flow doesn't apply — the correct move is to skip ghq-clone entirely and go straight to WebFetch (or Playwright if the site blocks WebFetch, e.g. Medium's 403) → summarize → save directly to ψ/memory/learnings/ using the same Trace Connection frontmatter pattern, with no hub file or origin symlink needed."
date: 2026-08-31
source: rrr: ayami-oracle
concepts: ["learn-skill", "url-detection", "webfetch", "workflow-pattern"]
---

# /learn ต้องแยก URL-type ก่อนเข้า ghq-clone flow

ในเซสชันเดียว ผู้ใช้เรียก `/learn` 4 ครั้งด้วย URL 4 แบบ — มีแค่ 1 ครั้งที่เป็น GitHub repo จริง
(`virgiliojr94/book-to-skill`) อีก 3 ครั้งเป็นหน้าเอกสาร/บทความ (Medium article, Anthropic official docs,
agentskills.io spec page) ที่ ghq ไม่สามารถ clone ได้อยู่แล้ว (ไม่ใช่ git repo)

**กฎที่ควรใช้ทุกครั้งที่ `/learn` ได้รับ URL**:
1. เช็คก่อนว่า URL เป็น `github.com/owner/repo` pattern หรือไม่
2. ถ้าใช่ → ทำตาม flow เดิมของสกิล (ghq clone → symlink origin/ → spawn agent สำรวจ codebase → hub file)
3. ถ้าไม่ใช่ (docs page, blog post, spec page) → **ข้าม ghq-clone flow ทั้งหมด** ไปที่ WebFetch ตรงๆ
   - ถ้า WebFetch โดนบล็อก (เช่น Medium ตอบ 403) → fallback ไป Playwright browser +
     `document.querySelector('article').innerText`
   - สรุปเนื้อหา แล้วบันทึกเป็น `ψ/memory/learnings/YYYY-MM-DD_<slug>.md` ตรงๆ ด้วย frontmatter
     แบบเดียวกับ Trace Connection pattern ของสกิลเดิม — ไม่ต้องสร้าง hub file หรือ origin symlink
     เพราะไม่มี "codebase" ให้สำรวจ

## ทำไมถึงสำคัญ

สกิล `/learn` เขียนมาสำหรับ "codebase exploration" โดยเฉพาะ (มี SOURCE_DIR/DOCS_DIR, ghq, 3-5 subagent
สำรวจโครงสร้างไฟล์) — เอกสาร/บทความไม่มีโครงสร้างแบบนั้นให้สำรวจ การพยายามยัด URL ที่ไม่ใช่ repo เข้า flow
เดิมจะพังตั้งแต่ขั้น `ghq get` (ghq clone ได้แต่ git repo) ต้องรู้จักแยกแต่แรกแทนที่จะลองแล้วค่อยแก้ทีหลัง
