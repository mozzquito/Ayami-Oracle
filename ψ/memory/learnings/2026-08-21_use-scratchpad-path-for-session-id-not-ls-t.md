---
pattern: Derive the current session's .jsonl from the session ID embedded in the system-prompt scratchpad path, not from `ls -t` on the projects directory
date: 2026-08-21
source: rrr: ayami-oracle
concepts: [dig-miner, session-detection, rrr, root-cause, jsonl]
---

# Root-cause fix for the recurring "dig-miner picked the wrong session" bug

**Escalation context**: this exact friction ("concurrent-session `ls -t` picked wrong .jsonl") has now been recorded independently at least 9 times across session-metrics rows (2026-08-17, -18, -19, twice on -20, and again here on -21), including two prior sessions that wrote dedicated lesson files about it (`2026-08-17_dig-miner-picks-wrong-concurrent-session.md` and the `/rrr` skill's own step-1.5 fix of passing a literal path into the subagent prompt). None of those fixes actually stopped the recurrence, because they all addressed the wrong half of the problem: a **race inside the subagent's own re-derivation**. The bug that kept firing was in the **main agent's own `ls -t` call in step 1**, which is not a race at all — it's a plain wrong-file selection whenever a concurrent session in the same project directory has a more recently-touched `.jsonl` than the current one.

**The actual fix**: every Claude Code session's system prompt states its own scratchpad directory, in this exact shape:

```
/private/tmp/claude-501/{encoded-cwd}/{SESSION_ID}/scratchpad
```

`{SESSION_ID}` here is the *exact* current session's ID — not a guess, not an mtime heuristic, the literal ID the harness assigned to this conversation. The matching `.jsonl` is simply:

```
~/.claude/projects/{encoded-cwd}/{SESSION_ID}.jsonl
```

In this session, `ls -t` on the projects directory picked `2ef11adc-...` (a concurrent session, entirely about eVisa/Oracle-DB work, sharing the same project dir and touched within the same minute) instead of `f7d77c60-...` (this session, about the Megvii AI box). Extracting timestamps from the `ls -t` pick would have silently produced a completely wrong Timeline — a different topic, different day's work — merged into this retro without any error or warning.

**How to apply — replace `/rrr` step 1's session-detection block with**:

```bash
# Session ID comes from the scratchpad path stated in this session's own system prompt,
# NOT from `ls -t` on the projects directory (unreliable with concurrent sessions).
SESSION_ID="<copy the {SESSION_ID} segment out of your own system-prompt scratchpad path>"
LATEST_JSONL="$HOME/.claude/projects/${ENCODED_PWD}/${SESSION_ID}.jsonl"
echo "SESSION: ${SESSION_ID:0:8}"
```

Only fall back to `ls -t` if no scratchpad path was ever stated in the system prompt for this session (should not happen in normal operation).

**Verification signal for a "wrong file" pick**: if the dig-miner's returned timestamps don't match anything discussed in the actual conversation (wrong topic, wrong language mix, a big date gap with no bridging content), that's a strong tell the wrong `.jsonl` was selected — stop and re-derive from the scratchpad path before writing the Timeline, rather than merging it in and hoping.

**Independent confirmation, same minute, mutual mispick**: the `2ef11adc-...` session named above (concurrent, eVisa/Oracle-DB work) ran `/rrr` within the same minute and independently arrived at this identical root-cause fix — its own `ls -t` had picked *this* session's (`f7d77c60`) `.jsonl` as the wrong file, the exact mirror image of this session's mispick. Two sessions, same project directory, same minute, each `ls -t` grabbing the other's file — as clean a demonstration of the race as this bug has produced. The other session's duplicate write-up of this same lesson was folded into this file rather than kept as a second near-identical file; its `/rrr` skill edit (see `.claude/skills/rrr/SKILL.md` Step 1) implements the same scratchpad-path-first fix described above.
