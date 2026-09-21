---
pattern: Self-hosted GitLab's instance-wide SSRF protection is OFF by default and silently rejects webhook URLs targeting localhost/the server's own IP with a generic "Invalid url given" error.
date: 2026-09-15
source: rrr: ayami-oracle (eVisa GitLab CE / LINE webhook session, 2026-09-07 to 2026-09-15)
concepts: [gitlab-ce, webhooks, ssrf, admin-settings, self-hosted]
---

# GitLab CE webhook creation to localhost fails until SSRF protection is explicitly enabled

Building a GitLab-webhook-triggered LINE notification relay that runs on the same box as GitLab
itself (`127.0.0.1:9999`), webhook creation against both `127.0.0.1` and the server's own real IP
failed with a generic `Invalid url given` error.

**Root cause**: GitLab's instance-wide setting **Admin Area → Settings → Network → Outbound
requests → "Allow requests to the local network from webhooks and integrations"** is OFF by
default. This is an anti-SSRF protection — GitLab is deliberately refusing to let a webhook
target the local network, including the GitLab server's own loopback/local IP.

**Fix**: enable that setting. Webhook creation to `127.0.0.1` then succeeded immediately with no
other change needed.

**How to apply**: whenever a self-hosted GitLab instance's webhook targeting a same-box or
local-network service fails to even save with a vague "Invalid url given," check this admin
setting before assuming the target URL, port, or firewall is the problem — it's an intentional
platform guard, not a networking bug.
