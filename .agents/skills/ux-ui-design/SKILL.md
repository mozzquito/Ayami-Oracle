---
name: ux-ui-design
description: Apply core UX/UI design principles when building, reviewing, or critiquing frontend/UI work — usability heuristics, visual hierarchy, typography, color & contrast, spacing/layout, interaction feedback, accessibility, responsive design. Use when creating a UI, reviewing a design/screenshot, or the user asks about design quality, "ux", "ui", "design feedback", "ทำไม UI ดูแปลกๆ", "ช่วยดู design หน่อย". Works alongside the Frontend Development Workflow in CLAUDE.md (dev-browser → /debate → ux-critic).
---

# UX/UI Design Principles

> "Design is not just what it looks like. Design is how it works." — Steve Jobs

## Usage

```
/ux-ui-design              # แสดงหลักการทั้งหมด
/ux-ui-design check        # Alignment check กับงาน UI ที่กำลังทำอยู่
/ux-ui-design [screenshot]  # วิจารณ์ screenshot/mockup ที่แนบมา
```

---

## The 8 Core Principles

### 1. Visibility & Feedback

> ระบบต้องบอกผู้ใช้เสมอว่า "เกิดอะไรขึ้น" — ภายในเวลาที่เหมาะสม

- ทุก action ที่ผู้ใช้ทำ ต้องมี feedback ทันที (hover, click, loading, success, error)
- Loading state ต้องมี — อย่าปล่อยหน้าจอค้างเฉยๆ ให้คนสงสัยว่าพัง
- Error message ต้องบอก "เกิดอะไร" + "แก้ยังไง" ไม่ใช่แค่ "Error 500"

**Anti-pattern:** ปุ่มกดแล้วไม่มีอะไรเกิดขึ้นเลยจนกว่า request จะเสร็จ

---

### 2. Consistency & Standards

> อย่าให้ผู้ใช้ต้องเรียนรู้ใหม่ทุกหน้า — ใช้ pattern เดิมที่คนคุ้นเคยอยู่แล้ว

- ปุ่ม/ไอคอน/สี ที่ทำหน้าที่เดียวกัน ต้องหน้าตาเหมือนกันทั้งแอป
- ตาม platform convention (เช่น ปุ่มยืนยันอยู่ขวา ปุ่มยกเลิกอยู่ซ้าย บน desktop web)
- Terminology ต้องสม่ำเสมอ (อย่าเรียก "ลบ" หน้าหนึ่ง แล้ว "นำออก" อีกหน้า สำหรับ action เดียวกัน)

---

### 3. Visual Hierarchy

> สายตาต้องรู้ว่าอะไรสำคัญที่สุดใน 3 วินาทีแรก

- ใช้ ขนาด / น้ำหนักตัวอักษร / สี / ระยะห่าง เพื่อจัดลำดับความสำคัญ ไม่ใช่ทำทุกอย่างเด่นเท่ากันหมด
- 1 หน้าจอ ควรมี primary action ชัดเจนแค่ 1 อัน (ไม่ใช่ปุ่มสีเด่น 5 ปุ่มแข่งกัน)
- F-pattern / Z-pattern สำหรับ layout ที่มีข้อความเยอะ

**Type scale ที่ใช้ได้จริง (ตัวอย่าง):** 12 / 14 / 16 / 20 / 24 / 32 / 48px — อย่าสุ่มขนาดฟอนต์เอง ใช้ scale ที่มีสัดส่วนชัด

---

### 4. Color & Contrast (Accessibility)

> สีสวยแต่อ่านไม่ออกก็ไม่มีประโยชน์

- **WCAG AA minimum**: contrast ratio ≥ 4.5:1 สำหรับข้อความปกติ, ≥ 3:1 สำหรับข้อความใหญ่ (18px+ bold หรือ 24px+)
- อย่าใช้สีสื่อความหมายเพียงอย่างเดียว (เช่น แดง=error, เขียว=success) — ต้องมี icon/text ประกอบด้วย เผื่อคน color-blind
- Dark mode ต้องคิดแยก ไม่ใช่แค่ invert สี — เทียบ contrast ใหม่ทุกครั้ง

---

### 5. Spacing & Grouping (Gestalt Principles)

> ของที่เกี่ยวข้องกัน ต้องอยู่ใกล้กัน — ของที่ไม่เกี่ยวกัน ต้องมีระยะห่างชัดเจน

- ใช้ spacing scale ที่เป็นทวีคูณ (เช่น 4/8/12/16/24/32/48px) อย่าสุ่มค่า margin/padding
- Whitespace ไม่ใช่พื้นที่ว่างเปล่า — มันคือเครื่องมือจัดกลุ่ม (proximity) และให้หายใจ (breathing room)
- Related elements (label + input, title + description) ต้องอยู่ใกล้กันมากกว่าอยู่ใกล้ element ข้างเคียงที่ไม่เกี่ยวกัน

---

### 6. Affordance & Signifiers

> ผู้ใช้ต้องรู้ได้เองว่า "กดตรงนี้ได้" โดยไม่ต้องอ่านคู่มือ

- ปุ่มต้องดูเหมือนปุ่ม (shadow/border/hover state) ไม่ใช่ text ธรรมดาที่บังเอิญ clickable
- Cursor เปลี่ยนเป็น pointer เมื่อ hover element ที่กดได้
- Disabled state ต้องดู "กดไม่ได้" ชัดเจน (opacity ลด, cursor not-allowed) ไม่ใช่หน้าตาเหมือนกดได้แต่ไม่มีอะไรเกิดขึ้น

---

### 7. Error Prevention over Error Messages

> ป้องกันไม่ให้ผู้ใช้ทำผิดพลาด ดีกว่าบอกทีหลังว่าผิด

- Disable ปุ่ม submit จนกว่าฟอร์มจะ valid แทนที่จะให้กดแล้วค่อย error
- Confirm ก่อน action ที่ทำลาย/กลับไม่ได้ (delete, force push equivalents)
- Inline validation ทันทีที่พิมพ์ผิด format ไม่ใช่รอจนกด submit

---

### 8. Responsive & Adaptive

> Layout ต้องใช้งานได้จริงทั้งจอเล็กและจอใหญ่ ไม่ใช่แค่ "ไม่พัง"

- Breakpoint มาตรฐาน (โดยประมาณ): mobile <640px, tablet 640–1024px, desktop >1024px
- Touch target ขั้นต่ำ 44×44px บน mobile (นิ้วกดแม่นกว่า cursor)
- ทดสอบจริงบนขนาดจอเล็กสุดที่รองรับ ไม่ใช่แค่ resize browser แล้วเดา

---

## Quick Review Checklist

เมื่อ review งาน UI/UX ของตัวเองหรือคนอื่น ให้เช็คตามนี้:

```markdown
## UX/UI Alignment Check

| Principle | Status | Note |
|-----------|--------|------|
| Visibility & Feedback | ✓/⚠/✗ | ... |
| Consistency & Standards | ✓/⚠/✗ | ... |
| Visual Hierarchy | ✓/⚠/✗ | ... |
| Color & Contrast (A11y) | ✓/⚠/✗ | ... |
| Spacing & Grouping | ✓/⚠/✗ | ... |
| Affordance & Signifiers | ✓/⚠/✗ | ... |
| Error Prevention | ✓/⚠/✗ | ... |
| Responsive & Adaptive | ✓/⚠/✗ | ... |
```

---

## Workflow Integration

ตาม Frontend Development Workflow ใน CLAUDE.md:

1. Build feature (Bun/React/Vite)
2. Capture ด้วย dev-browser (screenshot ทุกหน้า)
3. รัน `/ux-ui-design check` กับ screenshot — ได้ alignment check ตาราง
4. ถ้ามีข้อ ✗/⚠ เยอะ → ใช้ `/debate` เพื่อถกกับ critic agent อีกที
5. แก้ตาม feedback แล้ว capture ใหม่ วนจนผ่าน

---

## Sources

- Jakob Nielsen's 10 Usability Heuristics (NN/g)
- WCAG 2.1 AA contrast guidelines
- Gestalt principles of visual perception
- Google Material Design / Apple HIG (platform convention references)
