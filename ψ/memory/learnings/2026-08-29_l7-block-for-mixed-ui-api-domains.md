---
pattern: When asked to block public access to a domain that also serves an API other systems depend on, default to L7 (WAF path/header-aware) blocking, not L3/L4 network/firewall blocking — network layer can't tell UI traffic from API traffic sharing the same domain/IP.
date: 2026-08-29
source: rrr: ayami-oracle
concepts: [network-architecture, waf, firewall, incident-response, evisa, wayama]
---

# Block public UI access without breaking a shared-domain API

## The pattern

A request like "block public users from a website" often gets solved reflexively at the network
edge (Cloud Firewall, disabling a Load Balancer) — and that's fine **until** the same domain also
serves an API that other systems (partners, mobile apps, backoffice integrations) depend on.
Network-layer blocking (L3/L4) is IP/port-based and has no visibility into URL paths or request
headers, so it cannot selectively preserve one path while blocking another on the same domain.

## What actually works

Move the block to a layer that can see the request shape:

- **Path-based WAF rule** — allow `/api-prefix/*`, block/deny the rest. Works but requires
  enumerating every path that must stay alive, which is fragile if the full API surface isn't
  known (a real risk on legacy/undocumented systems).
- **Accept-header-based rule (preferred when the API surface is uncertain)** — browsers loading a
  page send `Accept: text/html`; JS/XHR calls to APIs typically send `Accept: application/json`.
  Block on `Accept: text/html` → serve a static maintenance page; default-allow everything else.
  This flips the risk: unknown API paths keep working because the default is *allow*, not *deny*.
- **App-level maintenance flag** — cleanest when the app itself can distinguish "public UI login"
  from "service-to-service call" in its own business logic, but requires a deploy from the app/dev
  team rather than a pure infra change.

## What doesn't work at scale

Per-account disable (turning off individual user accounts in DB/AD/IIS) is **not** a valid
"close the whole site" mechanism for a public self-service portal — it doesn't scale to the real
user base and doesn't stop new signups. It's a tool for banning individual bad actors, not a bulk
maintenance-mode switch.

## Why this matters

This surfaced mid-conversation in an eVisa (Wayama) infra consult: the initial plan (block at
Cloud Firewall) was reasonable *until* the user flagged that `/ApiGateway/Authentication/signin`
had to stay alive for another system. The whole blocking strategy had to be re-architected from
L3/L4 to L7 as a result. Ask "does this domain serve anything besides the browser-facing site?"
**before** recommending a network-layer block, not after.

## Related

[[2026-08-18_evisa-oracle-backoffice-schema-mapping]] — same eVisa/Wayama project context.
