---
pattern: Windows PowerShell 5.1's Invoke-RestMethod/Invoke-WebRequest resolve proxy via WinINET (per-user), not WinHTTP — netsh winhttp set proxy has zero effect on them; a service can't reach a destination the interactive user reaches unless the proxy is passed explicitly or set at the right layer
date: 2026-09-08
source: "rrr: ayami-oracle"
concepts: [windows, powershell, proxy, winhttp, wininet, gitlab-runner, windows-service, dns]
---

# WinINET vs WinHTTP: PowerShell's proxy cmdlets don't see `netsh winhttp set proxy`

## The trap

A Windows box has internet access confirmed via an interactive RDP PowerShell session —
`Invoke-WebRequest -Uri "https://some-external-host"` returns `200 OK`. A **Windows Service**
running on the same box (a GitLab Runner, a scheduled task, anything under `LocalSystem` or a
dedicated service account) then fails the *same kind of call* with:

```
Invoke-RestMethod : The remote name could not be resolved: 'some-external-host'
```

The obvious-looking fix — `netsh winhttp set proxy proxy-server="host:port"` (machine-wide,
should apply to any process, right?) — **does nothing**, because it's fixing the wrong subsystem.

## The actual mechanism

- **Windows PowerShell 5.1** (`Invoke-WebRequest`, `Invoke-RestMethod`) uses the legacy .NET
  `System.Net.WebRequest` stack, which resolves its default proxy via **WinINET** — the same
  store Internet Explorer uses, kept per-user at
  `HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Internet Settings`
  (`ProxyServer`, `ProxyEnable`).
- **WinHTTP** is a *separate* proxy configuration store (`netsh winhttp show/set proxy`), used by
  Windows Update, BITS, and some other system-level components — but **not** by WinINET-backed
  callers like classic PowerShell's web cmdlets.
- A Windows Service (any account, including the *same* account a human is interactively logged in
  as) does not inherit that user's `HKCU` WinINET settings the way an interactive process does —
  so the exact call that worked at the RDP prompt fails from the service, with a DNS-resolution
  error rather than an obvious "proxy required" error, because the underlying stack falls back to
  a direct connection attempt that has no real path to the internet.

## How to actually diagnose it

1. From the *interactive* session, confirm the working proxy:
   ```powershell
   netsh winhttp show proxy                                            # usually "Direct access" — a red herring
   Get-ItemProperty "HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings" |
     Select-Object ProxyServer, ProxyEnable                            # the one that's actually working
   ```
2. Confirm the mechanism is DNS/proxy-shaped and not something else by comparing a raw DNS
   lookup against the working HTTP call in the *same* interactive session:
   ```powershell
   Resolve-DnsName some-external-host      # times out — no direct path exists
   Invoke-WebRequest -Uri "https://some-external-host" -UseBasicParsing   # 200 OK — going through WinINET proxy
   ```
   If DNS alone fails but the HTTP call succeeds, the network truly has no direct route and
   everything is going through the proxy — confirming the WinINET-vs-WinHTTP theory rather than
   some other network quirk.

## The fix

Don't fight the OS config layer — pass the proxy **explicitly on the call itself**:

```powershell
Invoke-RestMethod -Uri "https://some-external-host/..." -Method Post `
  -Headers @{ "Authorization" = "Bearer $token" } -ContentType "application/json" -Body $payload `
  -Proxy "http://10.0.163.24:3128"
```

This works regardless of which account runs the process, whether it's a service or interactive,
and doesn't require touching machine-wide network config (which risks side effects on unrelated
traffic — e.g. don't forget a bypass list if you *do* go the `netsh winhttp` route for something
else, so internal/local traffic isn't needlessly proxied).

## Don't also do this

Don't reach for changing the **Windows Service logon account** as a fix for this — it won't help
(the WinINET settings are still per-user/per-session, not something a service account "picking up
the same identity" as an interactive user grants access to), and it risks an unrelated
regression: changing a `gitlab-runner` service (or similar) from `LocalSystem` to a specific user
account can silently break anything that relied on `LocalSystem`'s elevated local rights — e.g.
IIS app-pool management (`Start-WebAppPool`/`Stop-WebAppPool` need IIS management rights that a
plain user account doesn't have by default). Diagnose the proxy layer first; don't touch the
service identity chasing a network symptom.
