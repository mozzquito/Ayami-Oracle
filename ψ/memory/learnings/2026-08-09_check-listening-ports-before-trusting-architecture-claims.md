---
pattern: Verify architecture with `ss -tlnp`/`ps aux` before trusting a one-word answer like "ใช้ nginx" — the process list is ground truth, the human's mental model of their own infra may be stale or incomplete
date: 2026-08-09
source: rrr: ayami-oracle
concepts: [ssh, kubernetes, cert-manager, gateway-api, ssl, diagnosis, tls-certificates]
---

# Check listening ports before trusting architecture claims

When mอส said "ใช้ nginx" for the impactwildlife.com server, the natural next step (and the one initially taken) was to walk through certbot/nginx SSL setup. That path was wrong: `ss -tlnp | grep 443` revealed `kube-apiserver` on 6443 and an internal nginx LB on a non-standard port (16443) — the box was a Kubernetes control-plane node, and the real website's TLS was managed by cert-manager + an Envoy Gateway (Gateway API), not system nginx at all. nginx was just serving Ubuntu's default placeholder page.

**Rule**: before recommending an SSL/infra setup path based on a human's verbal description of their stack, run one cheap read-only command (`ss -tlnp`, `ps aux | grep -E 'nginx|kube|docker'`) to confirm what's actually listening/running. A human's answer describes their mental model, which may be years out of date or describe only the piece they personally touch — the process table doesn't lie.

**Corollary — cert existence ≠ cert serving traffic**: in the same investigation, a `cert-manager` `Certificate` object for `www.impactwildlife.com` showed `Ready: True` and looked fully valid, but no Gateway `listener` or `HTTPRoute` referenced its secret anywhere in the cluster — it was provisioned but never wired to serve traffic. When auditing TLS status in a Gateway-API/Ingress cluster, always trace the full chain (Certificate → Secret → Listener certificateRefs → HTTPRoute → Service), not just "does a Ready Certificate object exist."

**Corollary — wildcard certs don't cover the apex domain**: `*.impactwildlife.com` has SAN `DNS:*.impactwildlife.com` only — it does not cover bare `impactwildlife.com`. Always read the actual SAN list (`openssl x509 -noout -ext subjectAltName`) rather than assuming a wildcard is a blanket cover for the whole domain family.
