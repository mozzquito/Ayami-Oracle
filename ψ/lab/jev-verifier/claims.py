"""Claim set for the Jev-as-verifier experiment. GOLD = Claude's manual verification on 2026-09-21 (see
ψ/learn/docs.typesafe.ai/2026-09-21/0141_TEAM-LEARN.md), fixed BEFORE any Jev call. Do not edit after running.
Each claim: (id, source, claim text, file key, (first_line, last_line), gold, must_contain keywords that PROVE the passage supports it)
file keys: "docs" = .tmp/typesafe-team/docs-full.txt ; "gate" = ψ/lab/jev-gate/gate.py
gold: "supported" = the passage supports the claim exactly as stated; "not_supported" = contradicted, absent, or over-stated.
"""
CLAIMS = [
 # ---- agy (cookbook / evidence review), reworded from its output; some split into fact vs characterisation ----
 ("A1", "agy", "The self-consistency cookbook repeats ONE borderline moderation post 15 times.", "docs", (4861, 4880), "supported", ("one borderline user post", "15 times")),
 ("A2", "agy", "TypeSafe's latency was sampled sequentially after the LLM pool had closed, while the LLMs ran under 16-way thread contention.", "docs", (5410, 5416), "supported", ("sequentially", "16-way")),
 ("A3a", "agy", "The cookbook's cost figures use historical price assumptions, not verified jev-latest billing amounts.", "docs", (5440, 5446), "supported", ("historical price assumptions", "not verified")),
 ("A3b", "agy", "The '444.6x cheaper' headline figure comes from this cookbook's pricing.", "docs", (5440, 5446), "not_supported", ()),
 ("A4a", "agy", "TypeSafe's agreement rises to 99.2% only after answers below a 0.60 top probability are sent to human review, leaving 74.2% of answers labelled automatically.", "docs", (4892, 4898), "supported", ("99.2%", "74.2%", "0.60")),
 ("A4b", "agy", "The docs conceal that the 99.2% figure leaves out the hardest cases, so the number is artificially inflated.", "docs", (4892, 4898), "not_supported", ()),
 ("A5a", "agy", "The cookbook's samples are cached in json_cache.json so re-rendering needs no API spend.", "docs", (5242, 5246), "supported", ("json_cache.json", "no API spend")),
 ("A5b", "agy", "Because of the cache, the published numbers do not come from independent live API draws.", "docs", (5242, 5246), "not_supported", ()),
 ("A6", "agy", "The docs bury that the speed comparison favours TypeSafe, which invalidates the 193.6x faster claim.", "docs", (5410, 5416), "not_supported", ()),
 ("A7", "agy", "Jev accepts text only; images, audio and video are not supported.", "docs", (912, 922), "supported", ("text input only", "not supported")),
 ("A8", "agy", "More than a quarter of TypeSafe's answers in that cookbook fall below the 0.60 gate and go to human review.", "docs", (4892, 4898), "supported", ("99.2%", "74.2%")),
 # ---- zcode (API / SDK reference + gate.py audit) ----
 ("Z1", "zcode", "Both jev-latest and jev-preview currently resolve to jev-1.13.0.", "docs", (12858, 12870), "supported", ("jev-latest", "jev-preview", "jev-1.13.0")),
 ("Z2", "zcode", "The rate limit is 250,000 tokens per second and 1,200 requests per minute.", "docs", (12840, 12850), "supported", ("250,000", "1,200")),
 ("Z3", "zcode", "Context length is 64k tokens per request, with 32k tokens for the state plus the longest question.", "docs", (12840, 12850), "supported", ("64k", "32k")),
 ("Z4", "zcode", "The Python SDK's DEFAULT_TIMEOUT is 10.0 seconds.", "docs", (18155, 18162), "supported", ("DEFAULT_TIMEOUT = 10.0",)),
 ("Z5", "zcode", "RetryPolicy.timeout is the total retry budget per SDK call, including the initial attempt and the delays, not a per-attempt timeout.", "docs", (18424, 18431), "supported", ("Total retry budget", "initial attempt")),
 ("Z6", "zcode", "Noul answers carry no confidence value.", "docs", (1154, 1158), "supported", ("Noul answers don't carry one",)),
 ("Z7", "zcode", "gate.py hides which exception type made a chunk fail, so authentication errors and bad requests look identical in its output.", "gate", (96, 102), "not_supported", ("type(e).__name__",)),
 ("Z8", "zcode", "AI_GATEWAY_API_KEY is not one of the SDK's documented environment variables.", "docs", (18085, 18163), "supported", ("TYPESAFE_API_KEY",)),
 ("Z9", "zcode", "The jaggedness page lists adversarial content as a known failure mode of jev-1.13.", "docs", (12690, 12700), "supported", ("Adversarial content",)),
 # ---- planted controls (written by Claude): 6 plainly false, 2 true paraphrases ----
 ("P1", "planted", "Jev accepts image and audio input in addition to text.", "docs", (912, 922), "not_supported", ()),
 ("P2", "planted", "The rate limit is 100 requests per minute.", "docs", (12840, 12850), "not_supported", ()),
 ("P3", "planted", "Noul answers include a confidence field.", "docs", (1154, 1158), "not_supported", ()),
 ("P4", "planted", "The Python SDK's default timeout is 60 seconds.", "docs", (18155, 18162), "not_supported", ()),
 ("P5", "planted", "Output tokens are billed at the same $0.042 per million as input tokens.", "docs", (12846, 12849), "not_supported", ()),
 ("P6", "planted", "jev-preview points to an older model than jev-latest.", "docs", (12858, 12870), "not_supported", ()),
 ("P7", "planted", "Only input tokens are charged; output tokens are free.", "docs", (12846, 12849), "supported", ("Charged per input token", "Output tokens are free")),
 ("P8", "planted", "The model cannot reliably count characters or occurrences of a term.", "docs", (12710, 12716), "supported", ("does not count reliably",)),
 # ---- SUBTLE planted controls (added after zcode/agy review, BEFORE any Jev call): swapped numbers / conditions ----
 ("S1", "subtle", "The rate limit is 1,200 tokens per second and 250,000 requests per minute.", "docs", (12840, 12850), "not_supported", ()),
 ("S2", "subtle", "Context length is 32k tokens per request, with 64k tokens for the state plus the longest question.", "docs", (12840, 12850), "not_supported", ()),
 ("S3", "subtle", "RetryPolicy.timeout is a per-attempt timeout that restarts for every retry.", "docs", (18424, 18431), "not_supported", ()),
 ("S4", "subtle", "TypeSafe's agreement rises to 99.2% once answers below a 0.06 top probability are sent to human review, leaving 74.2% labelled automatically.", "docs", (4892, 4898), "not_supported", ()),
 ("S5", "subtle", "Choice answers carry no confidence value, while Noul answers do.", "docs", (1154, 1158), "not_supported", ()),
]

# Claims that rest on ABSENCE (silence of the passage) — arguable gold, reported separately (flagged by zcode/agy review).
ABSENCE = {"A3b", "Z8"}
