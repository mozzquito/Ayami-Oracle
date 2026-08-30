---
pattern: before declaring an ML/AI detection feature "not working," check whether the vendor documents an explicit maturity/readiness tier for it — that reframes the debugging question from "is my config wrong" to "can I provide the conditions this needs"
date: 2026-08-25
source: rrr: ayami-oracle
concepts: [vendor-docs, ml-detection, debugging-strategy, iot, megvii]
---

# Check the vendor's own maturity tier before declaring an ML feature broken

Spent most of a session (dozens of live tests, threshold swept from 0.97 down
to 0.1, phone/toy-gun/real-knife test objects, multiple poses, a disabled
face-match gate, confirmed license + installed algorithm package) trying to
get a Megvii AI box's HOLDWEAPON (armed-personnel) detection to fire even
once. It never did. The answer was in a vendor-supplied PDF read partway
through: Megvii's own "Weapon custom warehouse" function-definition doc rates
HOLDWEAPON **"Maturity L4 — implementation stage"**, and specifies lab-clean
background, weapon held parallel to the forearm with the elbow visible, a
knife's flat side (not edge) toward the camera, and a 20–50cm physical object
size — conditions a live desk/office test never reliably reproduces.

**Rule**: when an ML/AI detection or classification feature refuses to fire
despite config being verified correct (license active, threshold permissive,
zone/target-type right), check the vendor's own documentation for an explicit
maturity or readiness rating before continuing to sweep config. A tier like
"beta," "L4/implementation stage," or "experimental" changes the nature of
the problem from "something is misconfigured" (keep debugging) to "this
needs lab conditions I may not be able to provide" (stop debugging config,
either reproduce the exact required conditions once as a sanity check, or
escalate to the vendor). This is a much cheaper check to do early than to do
after exhausting config-side possibilities.
