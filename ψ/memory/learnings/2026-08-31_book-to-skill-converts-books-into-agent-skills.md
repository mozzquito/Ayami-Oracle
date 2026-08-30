---
pattern: "Learned book-to-skill (virgiliojr94): converts books/long documents (PDF/EPUB/DOCX/HTML/RTF/TXT, MOBI/AZW via Calibre) into structured Agent Skills (SKILL.md) — extracts frameworks/principles/techniques/anti-patterns rather than summarizing, achieving 24x-51x token reduction vs raw-text-in-context. Multilingual chapter detection (10+ languages incl. Thai/Chinese/Persian) with built-in prompt-injection sanitization (strips 33+ invisible/zero-width/bidi Unicode codepoints — Trojan Source class attack) on all extracted text."
date: 2026-08-31
source: learn: virgiliojr94/book-to-skill
concepts: ["learn", "codebase", "agent-skills", "skill.md", "prompt-injection", "document-extraction", "cli-tool"]
---

# Learned book-to-skill

## สิ่งที่ทำ
รับหนังสือ/เอกสารยาว (PDF, EPUB, DOCX, HTML, RTF, TXT, MOBI/AZW ผ่าน Calibre) แล้วสกัดเป็น
**Agent Skill (SKILL.md)** ที่พร้อมใช้กับ Claude Code/Copilot CLI/Amp/Codex — ไม่ใช่แค่สรุปเนื้อหา
แต่ดึง framework/principle/technique/anti-pattern ออกมาให้เรียกใช้ซ้ำได้ตอนเขียนโค้ดจริง

**ตัวเลขที่น่าสนใจ**: ประหยัด token 24×–51× เทียบกับการยัดหนังสือทั้งเล่มเข้า context ตรงๆ
(หนังสือ 150K+ token → skill ที่โหลดจริงแค่ ~19K token) เหตุผลเดียวกับ progressive disclosure
ที่เรียนไปจาก Anthropic Agent Skills docs ก่อนหน้านี้ในเซสชันนี้ — เก็บบนดิสก์ โหลดเข้า context
เฉพาะบทที่ต้องใช้จริง

## จุดที่น่าจดจำเป็นพิเศษ

1. **Security-first extraction**: sanitize invisible Unicode codepoint 33+ ตัว (zero-width chars,
   bidi control chars ที่ใช้ทำ Trojan Source attack, Unicode tag block) ออกจากข้อความที่สกัดมา
   ก่อนส่งเข้า context เลย — ป้องกัน prompt injection ที่แอบซ่อนในไฟล์ต้นฉบับ (PDF/EPUB ที่มาจาก
   แหล่งไม่รู้จัก)
2. **Multilingual chapter detection จริงจัง**: รองรับ 10+ ภาษารวมถึงไทย จีน เปอร์เซีย ฮินดี เบงกาลี
   เกาหลี — แต่ละภาษามี regex pattern + ตัวแปลงเลขเฉพาะของตัวเอง (เช่น เลขไทย/เลขจีนต้อง parse ต่าง
   จาก Arabic numeral)
3. **Fallback chain ต่อ format**: PDF ใช้ 4 เครื่องมือไล่ลำดับ (docling → pdftotext → pypdf →
   pdfminer), EPUB มี 2 backend — ถ้าตัวแรกพังยังมีตัวสำรอง ทำให้ batch job ไม่ล้มทั้งชุดเพราะไฟล์เดียว

## เชื่อมกับสิ่งที่เรียนในเซสชันนี้

ต่อยอดตรงจาก [[2026-08-31_anthropic-agent-skills-official-docs]] และ [[2026-08-31_agentskills-io-open-spec]] —
นี่คือเครื่องมือที่เอาแนวคิด SKILL.md progressive disclosure ไปใช้แก้ปัญหาจริง (จัดการหนังสือ/เอกสารอ้างอิงยาวๆ)
น่าลองใช้ถ้ามีหนังสือ/เอกสารเทคนิคที่อยากให้ Ayami อ้างอิงซ้ำได้โดยไม่ต้องยัด context ทุกครั้ง
