---
pattern: On OpenWrt/RUTOS routers, a VPN reaching the router's own admin UI does not mean it can reach LAN devices — check the zone-pair Forwarding policy (e.g. `wireguard ⇒ lan`), which commonly defaults to Reject even when Input is Accept.
date: 2026-09-02
source: rrr: ayami-oracle
concepts: [teltonika, rutos, openwrt, wireguard, firewall, networking, remote-troubleshooting]
---

# WireGuard road-warrior zone forwarding blocks LAN devices even when the VPN "works"

## The pattern

On OpenWrt-family routers (confirmed on Teltonika RUTOS), firewall zones separate
**Input** (traffic terminating at the router itself — e.g. its admin web UI) from
**Forwarding** (traffic passing through the router to another zone, e.g. a device on
LAN). When a WireGuard road-warrior interface is added, RUTOS creates a `wireguard`
zone whose Input policy is typically Accept (so you can reach the router's own admin
page) but whose zone-pair **Forwarding to `lan` defaults to Reject**.

This produces a specific, confusing symptom: the VPN client shows connected, the
router's own admin UI is reachable, `ping`/`curl` to the router's own LAN IP works —
but any *other* device on the LAN (a camera, a PLC, an NVR) is completely unreachable,
with no error beyond a silent timeout.

A second, independent requirement sits on the client side: the WireGuard client's
**Allowed IPs** must include the full destination subnet (e.g. `192.168.1.0/24`), not
just the peer/router's own tunnel address (`10.x.x.1/32`). Fixing the router's zone
policy alone does nothing if the client never routes LAN-bound traffic into the tunnel
in the first place. Both fixes are independent and both are required.

## Why this matters

The natural diagnostic instinct — "VPN connects, router admin page loads, so the
network path must be fine" — is wrong on these platforms specifically because Input
and Forwarding are separately configured per zone-pair. Reaching the gateway proves
nothing about reaching anything behind it.

## How to apply

When a VPN/gateway is reachable but a device behind it is not:
1. Check the gateway's firewall **zone-pair Forwarding policy** (not just Input/Output)
   for the VPN zone → LAN zone direction, before investigating the target device at all.
2. Check the VPN **client's Allowed IPs** covers the destination subnet, not just the
   gateway's own address.
3. Treat "reaches the gateway but not devices behind it" as diagnostic *evidence* for
   this exact pattern, not as a reason to suspect the target device's own configuration.

See [[teltonika-dhcp-leases-tmpfs]] for the related but distinct DHCP-lease-visibility
pattern that was layered on top of this in the session that produced this lesson.
