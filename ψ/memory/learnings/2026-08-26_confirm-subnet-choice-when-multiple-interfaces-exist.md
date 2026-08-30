---
pattern: When a machine has multiple network interfaces/subnets and the user's request is ambiguous about which one, surface the choice before scanning/acting instead of silently picking one
date: 2026-08-26
source: rrr: ayami-oracle
concepts: [networking, nmap, lan-scan, user-confirmation, ambiguity]
---

# Confirm subnet choice when multiple interfaces exist

When a user asks to "scan the LAN" or similar without naming a subnet, and the
machine turns out to have more than one active network interface (e.g. Wi-Fi +
Ethernet, or a VPN alongside a physical NIC), don't silently pick one and scan
it — even if picking the default-gateway interface is a reasonable heuristic.

**Why**: In this session the Mac had two live subnets (10.243.164.0/24 via
en0, 192.168.1.0/24 via en6/default gateway). The default-gateway subnet was
scanned without asking, which happened to be correct, but the choice was made
silently on the user's behalf. If a VPN or intentional dual-NIC setup were in
play, the default-gateway heuristic could scan the wrong network entirely
while looking successful.

**How to apply**: After detecting more than one candidate subnet
(`ifconfig | grep "inet "`, `route -n get default`), state the subnets found
and which one you're about to scan and why (e.g. "default gateway"), giving
the user a beat to redirect — rather than presenting only the final scan
result. This is cheap (one sentence) and avoids scanning the wrong network in
ambiguous multi-NIC/VPN setups.
