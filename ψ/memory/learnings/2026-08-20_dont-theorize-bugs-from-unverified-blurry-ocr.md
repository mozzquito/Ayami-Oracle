---
pattern: When a "bug" hypothesis rests on OCR-by-eye from a blurry photo/video, verify against an authoritative source before proposing a technical root cause — don't let a plausible-sounding theory (especially one that fits a topic just discussed) substitute for confirming the underlying reading was even correct
date: 2026-08-20
source: "rrr: ayami-oracle"
concepts: [ocr-confidence, root-cause-analysis, overconfidence, evidence-verification, database-investigation]
---

# Don't theorize bugs from unverified blurry OCR

## What happened

Investigating an eVisa incident, I extracted frames from a handheld phone video of a laptop
screen (motion-blurred, 300x540 source resolution) and read a "Date of Issue" field as changing
from "10 Apr 2025" to "09 Apr 2025" between two points in the same video. Because timezone/offset
inconsistencies between the two databases involved (MSSQL `DATETIMEOFFSET +00:00` vs Oracle
`TIMESTAMP WITH TIME ZONE ASIA/BANGKOK`) had just been established earlier in the same
conversation, I proposed a "timezone off-by-one-day bug" as the root cause — a theory that sounded
technically coherent and connected neatly to prior findings.

When the user later pulled the actual database records (both MSSQL and Oracle, for the real
application), the date had never changed — it was `10-APR-2025` consistently in both systems. My
"09 Apr" reading was simply a misread of blurry text (0 and 1, or 9 and 0, look similar at that
resolution). The real, unrelated issue was a human data-entry error: the applicant's first
submission had the *year* wrong (2026 instead of 2025), caught by consular staff, and corrected
via resubmission — nothing to do with timezones at all.

## Why it happened

A plausible technical explanation (timezone bug) was available and matched a pattern already
active in context (timezone offsets had just been discussed). That made it easy to reach for
without first asking "how confident am I in the raw observation this theory is built on?" The
OCR reading itself was never cross-verified against a second source before the theory was voiced.

## The rule

Before proposing a root-cause theory built on a manually-read value from a blurry image/video/scan:
1. State the confidence level of the reading explicitly (e.g., "hard to tell 09 vs 10 from this
   frame") rather than presenting it as fact.
2. Cross-check across multiple frames/crops if available — but even consistent misreads across
   frames aren't proof, since the same blur artifact repeats.
3. If an authoritative source (database, original document, a second independent capture) can
   settle the reading, get that before building a technical theory on top of the uncertain read.
4. Be extra suspicious of a theory that conveniently reuses a concept already active in the
   conversation (recency bias) — that fit is not evidence.

## How to apply

Applies to any investigation where visual/audio transcription of low-quality source material
(blurry photos, handheld video, noisy audio) feeds into a causal explanation — not just this
eVisa case. When in doubt, hedge the reading and ask for corroboration before theorizing.
