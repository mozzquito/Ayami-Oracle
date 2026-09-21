---
pattern: When a network/proxy fix works on one machine but an identically-configured second machine still fails, diff the two machines' actual resolution paths before proposing a second fix — don't guess at a different subsystem.
date: 2026-09-15
source: rrr: ayami-oracle (eVisa GitLab CE / LINE webhook session, 2026-09-07 to 2026-09-15)
concepts: [windows, powershell, proxy, winhttp, wininet, gitlab-ci, iis, service-account, regression]
---

# Diff against the working machine before proposing a second proxy fix

On the eVisa project, a LINE-notification `Invoke-RestMethod` call worked fine from one Windows
GitLab Runner (`10.0.160.10`) but failed with a TLS "connection closed" error from a second,
identically-configured runner (`172.16.6.206`). Two fixes were proposed in sequence before the
real cause was found, and the second one caused a genuine regression.

**What happened**: `netsh winhttp set proxy` was tried first (zero effect — wrong subsystem).
Then the `gitlab-runner` service account was changed from `LocalSystem` to a named
(`.\systemadmin`) account, guessing that credential/network context was the issue. This broke
`Start-WebAppPool`/`Stop-WebAppPool` on the same runner, because the new account lacked IIS
management rights — a real regression in a production-track UAT deploy pipeline, requiring an
emergency revert (`sc.exe config gitlab-runner obj= "LocalSystem"`) before the next deploy could
run.

**Root cause**: PowerShell 5.1's `Invoke-RestMethod` resolves proxy settings via **WinINET**
(a per-user `HKCU` registry setting), not **WinHTTP** (the machine-wide setting `netsh winhttp`
controls). The two runners differed in which interactive user had ever configured a proxy in
their profile — that's a WinINET-layer difference, invisible to any WinHTTP-layer diagnostic or
fix.

**The fix that actually worked**: pass `-Proxy "http://<proxy-host>:<port>"` explicitly on the
`Invoke-RestMethod` call, bypassing the ambiguity entirely. One line, no service/account changes
needed.

**Why this matters generally**: when two nominally-identical machines diverge on a
network-reachability symptom, the fastest correct diagnostic is comparing the *working* machine's
actual resolution path (registry keys, active env vars, per-process proxy settings) against the
failing one — not escalating to broader changes (service accounts, firewall rules, DNS config)
one at a time and hoping. Broader changes also carry hidden blast radius: a service account is
often relied on for more than the one thing being debugged (here, the same `gitlab-runner`
account also drove IIS app-pool control), so changing it to fix an unrelated symptom risks
breaking something the debugging session never considered.

**How to apply**: before proposing a second fix for a "works here, fails there" network/proxy
symptom, explicitly ask "what's different about resolution path between these two machines" and
check that first — registry, env vars, per-user vs per-machine settings — rather than reaching
for the next broader-scoped change.
