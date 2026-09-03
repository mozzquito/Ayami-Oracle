---
pattern: OpenWrt/RUTOS DHCP lease tables live in /tmp (tmpfs) and are wiped by any reboot — an empty/incomplete lease table is not proof a device is statically configured.
date: 2026-09-02
source: rrr: ayami-oracle
concepts: [teltonika, rutos, openwrt, dhcp, networking, remote-troubleshooting]
---

# Empty DHCP leases after reboot ≠ device is static

## The pattern

OpenWrt-family routers (confirmed on Teltonika RUTOS) store the dnsmasq DHCP lease
file on `/tmp`, which is tmpfs (RAM-backed) — it is wiped on every reboot. Right after
a reboot the leases list is empty and repopulates gradually as each client renews or
re-requests, not instantly.

This is easy to misread as "this device must have a static IP, it's not talking DHCP
at all" — a real and common failure mode for IoT/camera devices, but not provable from
an empty lease table alone, especially soon after a reboot.

## How to apply

Before concluding a device is statically configured because it's absent from DHCP
leases:
- Check the timestamp/age of other leases in the table — if everything is fresh
  (recently reissued), the table may simply not have caught up yet after a reboot.
- Give it a few minutes and re-check, or trigger a link-state change on the device if
  possible, before reaching for vendor discovery tools (e.g. SADP for Hikvision) as if
  static IP were confirmed.
- MAC OUI prefixes (first 3 octets) are a fast way to shortlist a vendor's devices in
  an ARP table (`cat /proc/net/arp`) when a hostname field is empty — useful regardless
  of whether the device turns out to be static or DHCP.

See [[wireguard-zone-forwarding-blocks-lan-devices]] for a firewall-side pattern that
produced an unrelated but similarly-shaped "device unreachable" symptom in the same
session.
