---
pattern: any relay/bridge that reacts to external device/API events by spawning a subprocess or opening a new outbound connection per event needs a concurrency cap and per-type cooldown from its first version, not added reactively after a flood
date: 2026-08-25
source: rrr: ayami-oracle
concepts: [notification-bridge, rate-limiting, process-spawn, iot, defense-in-depth]
---

# Cap per-event subprocess fan-out from the start, not after the flood

Building `alarm-bridge.mjs` (Megvii AI box → Discord + LINE), the first version's
Discord relay spawned a brand-new full `discord.js` gateway-login child process
per alarm, with no concurrency limit. A burst of real device events (the box
pushed far more event types than its configured filter implied — face/body
capture noise alongside the intended alert types) piled up 70+ zombie
processes before anyone noticed via `ps aux`, and LINE's broadcast API started
returning `429`s from the resulting request volume.

**Why this happened**: I had already learned earlier in the same session that
this device's real event volume didn't match its documented/configured filter
— but built the relay's fan-out logic before applying that knowledge
defensively. The bug was reactive-fixable (kill the processes, add a filter/
cooldown/cap) but the cost of over-defending from the start would have been
near zero, versus a real production incident once it happened.

**Rule**: when a relay's job is "react to an external event by doing an
expensive fan-out action" (spawn a process, open a new connection/login,
call a rate-limited third-party API), build the concurrency cap and
per-event-type cooldown into the very first version — especially when the
upstream event source's true volume/pattern hasn't been fully characterized
yet. Treat "the device's own filter will handle it" as insufficient; add a
second filter layer on the receiving side too (defense in depth), since a
device-side filter can silently pass more than expected.

Architecturally, the more durable fix here was removing the fan-out
mechanism itself: switching Discord from spawning a sibling script (a full
gateway login per message) to a stateless webhook HTTPS POST eliminated the
entire class of spawn-related risk, not just this instance of it.
