---
pattern: For a SaaS/cloud vendor against a hardware-shaped TOR, build the compliance matrix first — a missing formal datasheet is expected, not a gap to fill; and never trust a subagent's negative finding ("this is fabricated/doesn't exist") without checking the URL/method it used to reach that conclusion.
date: 2026-09-11
source: rrr: ayami-oracle
concepts: [tor-procurement, saas-vendor-evidence, subagent-verification, zcode, agy, compliance-matrix, thai-government-procurement]
---

# SaaS-vendor TOR evidence, and verifying subagent negative findings

## Pattern 1 — "No official datasheet" is the expected state for SaaS/cloud vendors, not a gap

When a TOR is written with hardware/on-prem procurement assumptions (a formal "datasheet" or
"catalog" attachment) but the actual product being proposed is a SaaS/cloud service, don't treat
the absence of a formal vendor datasheet as a problem to solve by fabricating a datasheet-shaped
document. Real Thai government TOR text confirms the opposite:

- สตง. TOR ข้อ 15.2: bidders must submit a catalog **and** a self-authored comparison table
  (ข้อกำหนดตาม TOR / ความสอดคล้อง / รายละเอียดข้อเสนอ / เอกสารอ้างอิง — with page-number references),
  with underlining/highlighting/annotation tying each line to its TOR clause. The catalog itself
  is often marked conditional ("ถ้ามี").
- A GISTDA cloud-computing-service TOR explicitly lists "แคตตาล็อกและ/หรือแบบรูปรายการรายละเอียด
  คุณลักษณะเฉพาะ **(ถ้ามี)**" as one acceptable evidence type, alongside the same comparison-table
  requirement.

**How to apply**: when proposing a SaaS/cloud vendor against this kind of TOR, prioritize building
the compliance-matrix table (TOR item → verdict → evidence page reference) over chasing or
compiling a formal datasheet. The accepted evidence substitute for the missing catalog is official
vendor web-doc printouts (with URL + access date) plus the matrix — not a fabricated PDF styled to
look like an OEM spec sheet. See also [[project_wym_tor_email_sendgrid]] for the specific SendGrid
verdicts this pattern was built around.

## Pattern 2 — Internal consistency within a reviewed document matters as much as any single claim

A vendor/reseller-authored spec document can state a tier caveat correctly in one place (prose:
"EU data residency... higher entitlements") while dropping it in a summary table row elsewhere
("Data Residency (EU): Included", no qualifier). A procurement evaluator skimming only the compact
table sees the unqualified version. When reviewing this kind of document for accuracy, check that
every qualifier stated once appears everywhere the same fact is repeated — not just whether each
individual line is independently true.

## Pattern 3 — Verify a subagent's negative finding as carefully as a positive one

zcode flagged "Sender Engagement Quality Score" (a real, documented SendGrid feature) as fabricated
— but the actual problem was that zcode checked a single guessed URL
(`twilio.com/docs/sendgrid/glossary/sender-engagement-quality`, a 404) instead of the real doc
location (`docs.sendgrid.com/api-reference/sendgrid-engagement-quality-api/*`, both HTTP 200).
Separately in the same project, agy invented two Comptroller-General circular numbers (ว521, ว214)
with plausible content that didn't match what those real circulars actually say.

**How to apply**: "verified false / doesn't exist / fabricated" from a subagent is a claim about
the subagent's own search, not a fact about the world. Before propagating a negative finding into
a document (especially a correction that removes or contradicts something already believed true),
re-check it directly — a wrong negative is exactly as damaging in a procurement document as a
fabricated positive citation.
