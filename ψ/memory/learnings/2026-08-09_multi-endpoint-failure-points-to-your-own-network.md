---
pattern: When several endpoints that previously worked all start timing out simultaneously, suspect your own network path (VPN/route) before theorizing about a remote block
date: 2026-08-09
source: "rrr: ayami-oracle"
concepts: [ssh, networking, vpn, diagnosis, root-cause]
---

# Multi-endpoint failure points to your own network, not a remote block

While auditing a 5-node Kubernetes cluster over SSH, a working connection (node1, `192.168.28.1`) suddenly started timing out along with four other nodes that had never connected (`.2`-`.5`). The first theory offered was "rate-limit/firewall block from bursting connection attempts to unreachable IPs" — a plausible-sounding technical explanation. The real cause, given by the human a message later, was simpler: the VPN had dropped.

**Rule**: if a previously-working endpoint fails at the same moment several other endpoints fail, that's a "my route to everything just changed" signal, not a "the remote side blocked me" signal. Remote-side blocks (rate limiting, fail2ban) almost always affect one endpoint at a time, tied to that endpoint's own auth/connection history — they don't retroactively kill an already-established working path to a *different* host at the same instant. A dropped VPN, changed route table, or network interface flap explains simultaneous failure across unrelated endpoints far better.

**How to apply**: before reaching for a remote-side explanation (rate limit, firewall, block), run one cheap local check first — `ifconfig`/`scutil --nc list` for VPN status, or compare a route/traceroute to the endpoint that used to work. This is the same root-cause-before-workaround discipline that applies to `ss -tlnp`-before-assuming-nginx: check the state you can see for free before inventing an explanation for the state you can't.
