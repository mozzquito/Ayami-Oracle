# Real Estate AI Video — Prototype

Photos + property details → Thai-narrated vertical (9:16) listing video.
Side-income idea #1 from [`ψ/writing/side-income-playbook.md`](../../writing/side-income-playbook.md).

This is a **CLI prototype**, not the LINE-bot/n8n production pipeline from the playbook — per
the plan, LINE/n8n integration is deferred to phase 2 until this pipeline itself is proven to
produce a video worth paying for.

## Setup

1. Get API keys for the 4 services (see `scripts/setup-wizard.sh` — run it, or fill `.env` by hand):
   - `OPENROUTER_API_KEY` — [openrouter.ai](https://openrouter.ai)
   - `CLOUDFLARE_API_TOKEN` + `CLOUDFLARE_ACCOUNT_ID` — [dash.cloudflare.com/profile/api-tokens](https://dash.cloudflare.com/profile/api-tokens) (Workers AI run permission — replaced fal.ai 2026-08-31, see below)
   - `SPEECHGEN_API_KEY` + `SPEECHGEN_EMAIL` — [speechgen.io](https://speechgen.io) (both required — SpeechGen's API needs the account email on every call, not just the token)
   - `CREATOMATE_API_KEY` — [creatomate.com](https://creatomate.com)
2. `npm install`
3. `npm run pipeline -- --photos "<url1>,<url2>" --price "..." --location "..." --agent-name "..." --agent-phone "..."`

Run `node dist/pipeline.js --help` (after `npm run build`) for the full flag list.

## What's actually verified (2026-08-27) vs. what's still assumed

Everything below was checked against the **live APIs with real keys**, not just docs — docs for
Creatomate and fal.ai turned out to be JS-rendered and unreadable by scraping, so the real
request/response shapes came from live probe calls instead.

| Step | Service | Status |
|---|---|---|
| Script writing | OpenRouter (`deepseek/deepseek-chat`) | ✅ **Fully verified live.** Real Thai script generated end-to-end, cost ~$0.0002/script. Caught and fixed a real bug: DeepSeek ignored the "no preamble" instruction on the first live run and prepended a markdown header — `script.ts` now has a second-line-of-defense strip in addition to the tightened prompt. |
| Video render | Creatomate | ✅ **Verified live** for `text` and `image` element types (3 real test renders, one with Thai text). ⚠️ **Not verified**: multiple images auto-sequenced on a shared `track`, and the `audio` element type — only ever rendered one image at a time in testing. Confirm with a real multi-photo + real audio run before trusting this for a paying customer. |
| Photo enhancement | Cloudflare Workers AI (`pruna/p-image-upscale`) | ⚠️ **Not live-tested yet.** Switched from fal.ai 2026-08-31 (that account got locked pending a credit top-up and was never actually verified live either — see git history). Endpoint, auth (`Bearer` + account ID in the URL path), and request/response shape are from Workers AI's own docs, not confirmed against a real call. It's an upscaler, not a pure lighting/color "adjust" model like fal.ai's Adjust V2 was — `enhance_details: true` is the closest available lever; watch real output quality, not just whether the call succeeds. Same per-photo fallback-to-original on failure as before. |
| Voiceover | SpeechGen | ⚠️ **Not live-tested** — blocked on `SPEECHGEN_EMAIL` not being set. Endpoint/params/response shape are from SpeechGen's own docs (confirmed real, not guessed), but two things need a live check the first time this runs: (1) form-urlencoded vs JSON body — implemented as form-urlencoded based on the PHP-router-style URL, not confirmed; (2) the actual Thai voice name — SpeechGen's docs didn't list one, `DEFAULT_THAI_VOICE` in `voiceover.ts` is a placeholder that **will fail** until replaced with a real voice name from your account's voice list. |

## Known gaps not yet decided (from the zcode + agy requirement review)

These matter before this becomes a real product, not before running the prototype once:

- **Unit economics** — no real per-video cost total yet. OpenRouter's slice is ~$0.0002; Creatomate is credit-based (used 3 of 50 trial credits during testing) with unknown $/credit at production volume; Workers AI and SpeechGen cost per call still unknown (both blocked from a real test). The Cloudflare-deployed version (`cloudflare/`) now persists `script_cost_usd`/`voiceover_cost_usd` per job in D1 to make this math possible once real calls succeed. Do this math before quoting ฿300/video to a customer.
- **Trial-tier render scale** — every test render came back at `render_scale: 0.25` (270×480 instead of the requested 1080×1920) regardless of what was requested. This looks like a Creatomate trial-account cap — check the billing/plan page before promising full-resolution output.
- **LINE delivery** (webhook timeout, ~10MB video size cap, push-message flow) — deliberately out of scope for this prototype, deferred to the n8n/LINE-bot phase.
- **Payment collection, business entity** — not a code problem, still open per the original requirement review.

## Files

- `src/enhance.ts` — Cloudflare Workers AI photo enhancement (per-photo fallback to original on failure)
- `src/script.ts` — OpenRouter/DeepSeek Thai script writing (structured inputs only, no freeform paste — mitigates script hallucination)
- `src/voiceover.ts` — SpeechGen Thai TTS
- `src/render.ts` — Creatomate video assembly + polling
- `src/pipeline.ts` — CLI entry point, runs all 4 steps in sequence
- `scripts/setup-wizard.sh` — interactive account/API-key setup (run once)
