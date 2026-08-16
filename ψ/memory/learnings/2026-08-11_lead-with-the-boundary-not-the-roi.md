---
pattern: "When explaining what a benchmarking/evaluation tool does, lead with the boundary (what it does NOT change) before any positive/ROI framing"
date: 2026-08-11
source: "rrr: ayami-oracle"
concepts: ["communication", "benchmarking", "scope-clarity", "clawwork"]
---

# Lead with the boundary, not the ROI

After getting HKUDS/ClawWork's economic-agent benchmark fully working end-to-end (real Qwen model, real payment, $142.50 earned from $0.12 in tokens), the first explanation of "what's this good for" led with the impressive numbers — cost efficiency, quality scores, ROI-flavored language. The user had to ask a second, sharper question ("ทำให้ claude zcode gya qwen ทำงานดีขึ้นไหม ลดการใช้งาน token หรือเปล่า") before getting the fully honest answer: **ClawWork doesn't improve, optimize, or reduce token cost for any model — it's a pure benchmark/leaderboard.** Running it teaches you nothing about the model that persists after the run; it only produces a comparative report a human uses to make an external decision.

**Why**: getting something to actually work (after ~6 rounds of debugging) built up investment that colored how the result got framed — enthusiasm about the pipeline working leaked into overselling what the pipeline's output was *for*. A tool that measures X but doesn't change X will always look inflated if you lead with the measurement's numbers instead of the boundary.

**How to apply**: any time explaining a benchmark, eval harness, leaderboard, or scoring tool — state what it does NOT do (train, fine-tune, optimize, cache, reduce cost) in the first sentence, before any of the positive numbers. Cheaper to say the boundary first than to be pushed into saying it second after a user's skepticism forces the correction.

See also [[2026-08-11_learned-clawwork]] for the technical details of what ClawWork actually is.
