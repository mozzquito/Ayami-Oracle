---
pattern: verify a tool's actual interception layer before claiming it solves a named problem
date: 2026-09-11
source: "rrr: ayami-oracle"
concepts: [delegation, tool-recommendation, verification, brain-mcp, overclaiming]
---

# Verify a tool's mechanism before claiming it fixes a stated problem

During the 2026-09-11 session, Ayami recommended and later helped install three tools
(cc-bash-guard, simonw/llm, Docling) based on research zcode/agy did overnight. Three
separate overclaims surfaced only when มอส asked direct follow-up questions:

1. **cc-bash-guard** was pitched as the fix for "agy writes files to disk despite being
   invoked with `--mode plan`" — but cc-bash-guard hooks Claude Code's own `Bash` tool
   calls (`PreToolUse`). It has no visibility into what a subprocess (agy) does internally
   once it starts running. Different layer entirely; it doesn't touch the stated problem.

2. **simonw/llm** was pitched as giving cost/usage visibility into zcode/agy/grok
   delegation — but `llm` only logs calls made *through the `llm` CLI itself*. zcode, agy,
   and grok are separate programs with their own API calls that never pass through `llm`,
   so nothing about them would ever appear in its logs.

3. **Docling** was described as "just `pip install`, no special hardware requirement" —
   it actually depends on PyTorch + transformers + a real vision-language model
   (Granite-Docling, 258M params), with a 2-4GB disk footprint and a real RAM spike during
   active use. On a machine already known to be RAM-constrained, this is a materially
   different cost than "just pip install."

## The pattern

All three followed the same shape: a tool's *description* overlapped with the *stated
problem* at a surface level, and that overlap was treated as confirmation without tracing
where in the stack the tool actually intercepts, or what its dependency chain actually
costs. The mismatch was caught only because the user pushed with a specific follow-up
("ทั้ง 3 ตัวติดตั้งเเล้วกิน ทรัพยากร อะไรไหม") — not because a check ran before the claim
was made.

## Rule

Before telling a user "tool X solves problem Y," answer one extra question first: *at
what layer does X actually operate, and does the named problem live at that same layer?*
For a permission/hook tool, that means checking what event it hooks and what it can and
cannot see. For a logging/tracking tool, that means checking whether the thing you want
tracked actually routes through it. For a "lightweight" claim, that means actually reading
the dependency list, not inferring weight from a one-line description.

This generalizes past this session: fit-claims between a tool and a named pain point are
the single highest-value place to slow down and verify, because they sound most confident
exactly when they're built on the least verification.
