---
pattern: When a device's web management UI blocks a feature on your OS ("not supported on Mac" / ActiveX-style plugin), check for bundled HTTP/WebSocket API docs before reaching for a VM or UA-spoofing workaround
date: 2026-08-21
source: rrr: ayami-oracle
concepts: [iot, network-debugging, api-reverse-engineering, macos, nmap, rtsp]
---

# IoT/surveillance device web UI blocked on Mac? Check for bundled API docs first

Chinese-made IoT/surveillance/AI-box devices (Megvii, Hikvision-adjacent, etc.) frequently ship a web management UI whose live-video preview widget is a Windows-only plugin (ActiveX/NPAPI-style), producing errors like "Currently does not support Mac system." This block is almost always a **frontend-only OS check** — the backend is a fully platform-agnostic HTTP/WebSocket API underneath.

**Why this matters**: the instinctive fixes (spin up a Windows VM, spoof the browser's User-Agent in DevTools) are slower and less durable than just talking to the device's API directly. In this session, the device (a MEGVII MegCube-B4H04-311 AI box) came with a full AIOTAP WebAPI doc bundle (mdBook-generated HTML, ~30 endpoint pages) sitting in the user's own Downloads folder — the exact feature the web UI blocked (drawing a detection-zone polygon for perimeter/intrusion algorithms) had a fully documented equivalent at `POST /intelli_manager/monitor` with a `warehouse_param.customized_options.area_list[].points` field taking normalized 0.0–1.0 coordinates.

**How to apply**:
1. Before reaching for a Windows VM or UA-spoofing, ask whether the vendor ships API docs (check the box, the product page, or ask the user — "did this come with an SDK/API doc folder?"). Enterprise/B2B security hardware almost always does.
2. Look specifically for a login/auth flow doc — most of these systems use a challenge-response pattern (`GET .../challenge` → salt+challenge, then `password_hash = SHA256(password + salt + challenge)`, `POST .../login`) rather than plain basic auth.
3. Cross-reference multiple doc pages when one page's field-name rendering looks garbled or incomplete (mdBook/static-doc HTML-to-text extraction can mangle nested JSON schema tables) — a dedicated "Algorithm Configuration Parameter Description" style page often has the same fields as raw, unambiguous JSON Schema.
4. Verify with the lightest possible read-only call first (a capability/`cap` endpoint) before attempting a state-changing POST, to confirm the auth flow actually works end-to-end.

**Related**: session also hit a duplicate-credential auth bug — when a device config form has BOTH a URL field with embedded `user:pass@host` AND separate username/password fields, filling both causes an otherwise-inexplicable "Authentication failed" even though the same credentials work standalone (verified via `ffprobe` directly against the camera). Fill credentials in exactly one place.
