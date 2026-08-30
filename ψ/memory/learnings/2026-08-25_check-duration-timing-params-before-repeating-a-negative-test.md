---
pattern: when a device-side test is repeated multiple times with the same negative result, re-check the live config for timing/duration parameters before repeating the test identically again
date: 2026-08-25
source: rrr: ayami-oracle
concepts: [debugging, iot, config-verification, megvii, test-methodology]
---

# Check duration/timing params before repeating a negative test

Boss asked to re-check Megvii HOLDWEAPON (weapon detection) live five times
in a row across ~15 minutes, each time holding a knife up to the camera for
a few seconds. All five came back negative on the box's own on-device alarm
log. Only on the fourth round did I think to re-read the live rule config
directly — and found `duration: 5` sitting in the HOLDWEAPON rule's
`extendParams`, meaning the algorithm requires the target to hold the
weapon steady, in-zone, for a full 5 continuous seconds before it even
becomes a detection candidate. Every quick hold before that point was very
likely under that threshold.

The config was equally readable on round 1 — nothing changed between rounds
that made it newly relevant. I just didn't think to check it until enough
repeated negative results made me look for what I might be missing, instead
of checking upfront what conditions the test actually needed to satisfy.

**Rule**: before repeating an unchanged live test that already failed once,
pull the full live configuration for the thing being tested and look
specifically for timing/duration/dwell-time fields, not just the obvious
threshold/sensitivity fields. A duration requirement invalidates every test
run shorter than it, silently, with no error — it just looks identical to
"the feature doesn't work" until someone checks. This is cheap to check
early and expensive to discover only after several repeated attempts.
