---
pattern: Before handing raw production data to an external AI agent/API (zcode, agy, or any third-party model), check data sensitivity and filter down to the minimum needed — don't delegate the raw dump by default
date: 2026-08-16
source: "rrr: ayami-oracle"
concepts: [security, data-sensitivity, delegation, zcode, agy, external-api, production-data]
---

# Check sensitivity before external-agent delegation, not after

มอส asked to hand off 5 CSV files (~450MB) of captured SQL Server plan-cache
text — real production queries and business logic from a Thai government
e-Visa system — to `/zcode` (Z.ai/GLM backend) and `/agy` (Gemini/external
Claude backend) for analysis. Both are separate CLI agents that call external
third-party APIs. The reflex would have been to just proxy the files over,
since that's literally what the user asked for.

Caught before executing: the project folder already contained documented
concern about a prior data-leak incident on this exact government system
(`STREAM-L0620-MFA-DCS-26-XX-ข้อมูลรั่วไหล.docx` and related attack-investigation
docs). Sending unfiltered production business logic to third-party model APIs
would have been a real, avoidable exposure — not a hypothetical one — for
convenience that a local `grep`-based filter could have avoided entirely.

Asked the user first via a explicit tradeoff question (send raw / filter
first / keep everything local with no external agent at all). User chose
"filter first." The filtered result turned out small enough (9 lines) that
local analysis alone answered the question — no external agent was needed
at all in the end.

**Rule**: when a user asks to delegate data to an external AI agent/API
(zcode, agy, or any third-party service), don't treat "the user asked for
it" as clearance to send the raw payload. First assess: (1) is this
production/regulated/PII-adjacent data, (2) has this project shown any prior
sensitivity signal (leak incidents, compliance docs, explicit prior caution),
(3) can local filtering reduce the payload to only what's needed before it
leaves the machine. If sensitivity is plausible, surface the tradeoff to the
user explicitly (via a real choice, not a buried caveat) before executing —
don't silently proceed and don't silently refuse either. Often the filtered,
local-first path turns out sufficient on its own, making the external
delegation unnecessary.
