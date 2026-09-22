---
name: jev
description: Consult TypeSafe's Jev (System One typed decision model — Noul/Choice/Score) as a narrow advisory screen/verifier via the ψ/lab/jev-gate prototype (gate.py / live_eval.py). Use when the user says "jev", "ask jev", "screen with jev", "typesafe", "system one", or wants a signal on prompt-injection/intent screening for external text. Jev is NOT a general coding delegate like /zcode, /agy, or /grok — it gives one narrow, non-deterministic, vendor-tuned judgment, and per ψ/lab/jev-gate/README.md must always be paired with /zcode and /agy before any threshold/wording change, any wiring into a hook/skill/bot, or any act-on-result decision. Do NOT trigger for general second-opinion coding tasks (use /zcode, /agy, or /grok), and do not treat this as production-ready — it is an uncommitted-to-main prototype living on branch `lab/jev-gate`.
---

# /jev — Consult TypeSafe's Jev (System One) as an advisory screen

> Jev is not a coding agent. It's TypeSafe AI's typed decision API (`api.typesafe.ai/v1/systemone`, pinned `jev-1.13.0`) —
> given text, it returns typed Noul/Choice/Score judgments. The only wiring that exists today is the **prototype** at
> `ψ/lab/jev-gate/` (branch `lab/jev-gate`): a prompt-injection/intent screen for text from *outside* the conversation
> (web pages, docs, pasted blocks). Nothing calls it automatically — no hook, bot, or skill is wired to it.

## When to use

- User explicitly asks for jev / TypeSafe / "System One" / a screening pass on external text
- Wants a second *signal* (not a verdict) on whether pasted/fetched content contains injected instructions
- Wants Jev tried as a claim verifier alongside Claude's own check (per the 2026-09-21 trial — see Status below)

Do NOT reach for this as a general "second opinion on my code" tool — that's `/zcode`, `/agy`, or `/grok`. Jev only
answers narrow typed questions about a piece of text.

## Invocation

```bash
cd ψ/lab/jev-gate
uv run python gate.py screen page.txt --send-external --env-file /path/to/.env   # or: ... screen - < text
uv run --with pytest pytest -q                                                    # offline tests, no key needed
uv run python live_eval.py --env-file /path/to/.env                               # live synthetic eval (~100 requests)
```

| exit | verdict | meaning |
|---|---|---|
| 0 | no_instructions_detected | everything scored below 0.35, no code signals — **not** a safety guarantee |
| 2 | review | score 0.35–0.65, or invisible chars / base64-like blob seen → a human should look |
| 3 | flagged | a chunk scored ≥ 0.65 |
| 4 | unscored | API error, truncated (>40 chunks / >200k chars), or refused → UNKNOWN, never OK |

## Hard rules (from ψ/lab/jev-gate/README.md — do not relax these)

- `--send-external` is required every run: text goes to `api.typesafe.ai` (retention unspecified). **Public/web content
  only — never PII, eVisa, email, secrets, or any Wayama work data** without Wayama's sign-off first.
- Key comes from env `TYPESAFE_API_KEY` or `--env-file`; never store it in this repo. `shadow.jsonl` (gitignored) keeps
  hash + length + verdict only, no full text.
- Scores are **not deterministic** (±0.03–0.04 on identical input). Thresholds were set post-hoc on ~30 synthetic cases.
  Treat a single run's exact score as noise; treat the verdict band as the signal.

## Required: pair with /zcode and /agy

Jev is one narrow, non-deterministic, vendor-tuned voice — never the only opinion behind a decision that matters.
Ayami (Claude) drives; `/zcode` (GLM) and `/agy` (Gemini/Claude Sonnet) give independent second opinions in parallel.

**Always ask both** (read-only) before you:
- change thresholds/bands, the Noul question wording, or the pinned model;
- wire jev-gate into any hook, skill, bot, or workflow;
- act on, or dismiss, a `flagged` / `review` result;
- use Jev for anything beyond screening (routing, verifying, scoring), or change how trial results are read.

```bash
zcode -p "<task + file paths>" --cwd "/Users/phongcheatphus/ayami-oracle" --disallowedTools "Edit Write"   # background: use `node .../zcode.cjs`, not the alias
agy   -p "<task + file paths>" --mode plan [--model gemini-3.1-pro-high]
```

How to work together:
1. Split by scope (different files/questions per agent), not the same question three times.
2. Read-only for reviewers — Ayami writes any change; zcode/agy never edit this repo.
3. Ayami verifies every reviewer claim against source lines/output before it goes into a note or commit (reviewers
   over-claim: 2026-09-21, agy called disclosed benchmark limits "deceptive," zcode wrongly said error types were
   hidden — both caught only by re-checking).
4. Disagreement resolves toward caution: if Jev finds nothing but zcode/agy see a risk, treat it as `review`. Never
   vote a `flagged` result down to "safe" — a human decides.
5. The data rule covers all three — zcode and agy also send prompts to third-party models. Public/non-sensitive
   content only, same as Jev.

## Safety notes

- This shells out to a separate Python process (`uv run`) inside `ψ/lab/jev-gate/` — it is not a Claude subagent and
  won't appear in tool-call history except as the Bash command and its stdout.
- Never auto-block or auto-act on a Jev verdict. It's advisory input to a human/Ayami decision, not a gate that
  decides by itself — the directory is literally named for that ("prototype, advisory only").
- Two API keys were pasted into chat during the 2026-09-20 trial and still need revoking as of the last check —
  do not assume they're safe to reuse; ask มอส before relying on any cached credential for this.

## Status

Prototype only, branch `lab/jev-gate` (2 commits: `af04554e`, `782ac746`), not merged to main, not wired into any
hook/bot/skill. 2026-09-20 trial: 98% on easy synthetic intent, 12/12 + 12/12 on synthetic injection sets, Thai
untested at scale. 2026-09-21 team run (Claude + zcode + agy + Jev-as-verifier): Jev scored 29/33 as a claim verifier
against Claude's gold set (false support on a one-digit number swap, missed arithmetic) — reinforces "advisory only,
never sole voice." See `ψ/lab/jev-gate/DESIGN.md` and `ψ/learn/docs.typesafe.ai/2026-09-20/0931_OVERVIEW.md` /
`ψ/learn/docs.typesafe.ai/2026-09-21/0141_TEAM-LEARN.md` for full detail.
