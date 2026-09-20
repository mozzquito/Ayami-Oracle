# Evidence for this small change (measured 2026-09-21 on 10 real Claude Code transcripts, 863 user prompts)
- Distance (in JSONL lines) from the last main-chain assistant line that has usage, to the next real user prompt:
  median 4, p95 17, p99 22, max 40. Exactly 1 of 863 prompts had a distance >= 40.
- Change 1: `tail -n 40` -> `tail -n 100` in the jq window (a miss only skips ONE warning; the next prompt recovers).
- Change 2: when the project dir ($ROOT) cannot be resolved, the hard-limit branch now prints the warning and exits
  instead of building HANDOFF_LOG="/ψ/inbox/handoff.log" and running mkdir -p there.
- Tested: 7 cases pass (real 804k transcript, 61k silent, 90 filler lines after last assistant -> still warns,
  130 filler lines -> silent as documented, no-ROOT case prints warning and creates no /ψ, compact_boundary silent,
  empty/missing/{} payload silent). The hook is already live: it printed "CONTEXT 166k (warn 150k)" in a real session.
