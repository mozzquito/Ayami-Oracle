---
pattern: When a device auth failure only reproduces on one client (a platform) but not another (e.g. VLC), check the device's own auth-mode/protocol setting before theorizing about the failing client's implementation
date: 2026-09-22
source: rrr: ayami-oracle
concepts: [debugging, rtsp, auth, root-cause, hardware]
---

# Verify device auth config before theorizing about the platform client

When an RTSP (or similar) stream authenticates fine in one client (VLC) but fails
"Authentication failed" in another (a third-party ingest platform, here Megvii),
the fastest root cause is usually a setting on the **device itself** — not a guess
about how the failing platform's client library is implemented.

**What happened**: A Hikvision camera streamed fine in VLC but Megvii returned
"Authentication failed" across every URL format tried (with/without embedded
credentials, with/without stream path). The first hypothesis (strip credentials
from the URL since the platform has separate username/password fields) was wrong
and cost a retry cycle. The actual cause — found by opening the camera's own web
UI and checking Configuration → Network → Advanced Settings → RTSP — was that
**RTSP Authentication Mode was set to `digest`**, which the platform's RTSP client
apparently couldn't negotiate; VLC handles digest auth fine, so it never noticed.
A second recurrence a few days later was the camera's DHCP-assigned IP changing
over a weekend — again a device/network-side fact, not a platform bug.

**Why**: VLC and other general-purpose clients tend to implement the full RTSP/auth
spec (digest, basic, redirects); narrower third-party ingest platforms often don't.
Given a "same credentials, one client works, one doesn't" symptom, the device's own
auth-mode setting is cheap to check and was the actual answer twice in the same
troubleshooting thread — cheaper than iterating on URL formats or guessing about
the failing platform's internals.

**How to apply**: For any "works in tool A, fails in tool B, same credentials"
report involving a physical device (camera, IoT sensor, printer, etc.), check the
device's own admin/config page for an auth-mode or protocol-compatibility setting
before proposing changes to how the request is formatted for tool B.

See also: retrospective `ψ/memory/retrospectives/2026-09/22/10.29_cctv-rtsp-then-forward-rrr-wrapup.md`.
