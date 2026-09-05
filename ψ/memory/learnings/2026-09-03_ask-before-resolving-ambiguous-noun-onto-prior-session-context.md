---
pattern: When a follow-up request opens with an ambiguous noun that could pattern-match onto the immediately-preceding session's context, ask which referent is meant instead of silently picking the most recent one — especially when candidate meanings map to different, consequential actions.
date: 2026-09-03
source: rrr: ayami-oracle
concepts: [clarifying-questions, ambiguity, teltonika, session-continuity]
---

# Ask before resolving an ambiguous noun onto prior-session context

## The pattern

A follow-up request can open with a short, ambiguous noun ("delete the device", "fix
the config", "reset it") right after a session that gave that noun a strong recency
bias toward one specific referent. It's tempting to resolve it automatically to
whatever the prior session was about — but recency is not the same as intent, and
prior sessions often touch several distinct things that could plausibly answer to the
same short noun.

Concretely: after a session entirely about one Teltonika RUT200 router (its WireGuard
VPN, its firewall zones, its DHCP leases), the next-session request "ลบ device" could
correctly mean the RMS-registered router itself, a WireGuard peer/client entry, or a
DHCP static lease/reservation for a device behind it — three different UI locations,
three different consequences, and none of them is the "obviously correct" reading from
context alone.

## Why this matters

These candidate meanings aren't interchangeable — unregistering a router from RMS,
removing a VPN peer, and deleting a DHCP reservation have genuinely different blast
radii and are not easily confused for each other once you're looking at the right UI
screen. Picking wrong costs a full round-trip at best; at worst it's actioned before
the mistake is caught.

## How to apply

When a request's key noun is ambiguous and the ambiguity resolves to actions with
materially different consequences, use a clarifying question (AskUserQuestion or
equivalent) rather than defaulting to the most-recently-discussed referent. This is
especially worth doing right after a prior session's own retro flagged an
overconfident-hypothesis mistake (see
[[wireguard-zone-forwarding-blocks-lan-devices]]) — the fix for "I anchored on the
wrong theory before checking" is to ask before committing to an interpretation, not
just to be more careful next time.
