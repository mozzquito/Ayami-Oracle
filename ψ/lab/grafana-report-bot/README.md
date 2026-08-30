# grafana-report-bot

Headlessly screenshots Grafana dashboards (Playwright, no `grafana-image-renderer`
plugin needed), pulls peak CPU/Memory values straight from Prometheus for the
Server Monitoring dashboard, and composes it all into one self-contained HTML
report — automating the weekly VM health report workflow from
`ψ/memory/retrospectives/2026-08/22/01.04_grafana-vmware-weekly-report-investigation.md`.

## Why Playwright, not the official Render API

The target Grafana instance (`10.0.163.250`) doesn't have the
`grafana-image-renderer` plugin installed (`rendererAvailable: false`, checked
2026-08-21). Playwright screenshotting each panel's `d-solo` embed view works
without any server-side install — see that session's retro for the tradeoffs.

## Setup

```bash
bun install
cp .env.example .env   # fill in GRAFANA_URL / GRAFANA_USER / GRAFANA_PASSWORD / DISCORD_WEBHOOK_URL

# Use a freshly ROTATED Grafana password — never the one pasted in chat on 2026-08-21.
```

Requires network access (VPN) to `10.0.163.250`, same as the manual `curl`
workflow used in the investigation session. `DISCORD_WEBHOOK_URL` is optional
— leave it blank to save reports locally only.

## Usage

**Run compiled output under Node, not `bun run src/cli.ts` directly** —
Playwright's cookie parsing throws (`"/login" cannot be parsed as a URL`)
under Bun's `node:http` shim during the login redirect. `bun install` for
speed is fine; execution needs real Node (`node -v` showed v22.13.1 when this
was built — any recent Node works).

```bash
# list dashboards + their UIDs (in case the fleet changes)
npm run list

# generate an on-demand report (all 3 dashboards, last 7 days, html+pdf)
npm run generate

# just the Server Monitoring dashboard (the one with peak-value extraction),
# a custom time range, and a specific output path — call the built CLI directly
# for extra flags, same rule (node, not bun) applies:
npm run build
node dist/cli.js generate --dashboards server --from now-24h --to now -o reports/today.html

# the scheduled presets (what cron/launchd actually calls) — html only,
# delivers to Discord if DISCORD_WEBHOOK_URL is set, --no-deliver to skip:
node dist/cli.js daily     # last 24h
node dist/cli.js weekly    # last 7 days

# on-demand personal quick-check — PDF only, risk matrix + hints, no
# screenshots (skips the slow panel-capture loop entirely), never sent to
# Discord:
node dist/cli.js quickref
node dist/cli.js quickref --from now-7d   # last 7 days instead of 24h
```

Screenshots land in `screenshots/<run-timestamp>/`, the composed report in
`reports/<run-timestamp>.html` (both gitignored).

## What's in the report

- **❌ เครื่องล่มตอนนี้ (down-host alert)** — zero-tolerance, always the first
  section when non-empty: any host in `HOST_GROUPS` currently reporting
  `up == 0` (Prometheus instant query, not a windowed peak — mirrors the
  "❌ เครื่องล่มตอนนี้" stat panel on the `eapp-frontend-errors` dashboard,
  confirmed 2026-08-23). Deliberately scoped to our tracked fleet only — a
  live test found 7 down instances entirely outside `HOST_GROUPS` (this
  Prometheus scrapes more than just our 3 host groups); alerting on those
  too would make the report noisy/untrustworthy from day one. Also prefixed
  onto the Discord message content when non-empty, so it's visible without
  opening the file.
- **Server Monitoring** (CPU/Memory panels): peak value per host, flagged
  against the agreed thresholds (CPU/Memory > 80%) — same logic manually
  applied while building the weekly `.docx` report. A breached finding gets a
  **root-cause hint box** (`src/rootcause.ts`) suggesting where to
  investigate next (Event Viewer, IIS logs, `sys.dm_exec_requests` for MSSQL
  hosts, etc.) — edit that file's `HINT_RULES` table to tune the hints, no
  need to touch the render logic.
- **Storage**: any host+volume under the free-space threshold gets its own
  finding card (grouped by host group) with the same hint treatment.
- **Network / Disk I/O**: informational only, no threshold — shown in the
  risk-matrix table as reference data, never flagged.
- **IIS Monitoring / MSSQL Monitor**: every panel captured as a screenshot
  gallery, grouped by dashboard. No peak-value extraction here — those
  dashboards have many heterogeneous counters without pre-agreed thresholds,
  so they're included as visual reference/appendix material rather than
  auto-flagged findings.

## Scheduling (launchd)

Two LaunchAgents in `launchd/` — daily every day at 16:00, weekly Fridays at
16:00 (both fire on Fridays by design: a daily digest *and* a separate weekly
rollup). They call `scripts/run-report.sh`, which shells out to a hardcoded
absolute `node` path (launchd gives the process a bare `PATH`, so nvm shims
don't resolve).

```bash
# after any source change:
npm run build

# install (copies into ~/Library/LaunchAgents, then loads):
cp launchd/com.ayami.grafana-report.daily.plist  ~/Library/LaunchAgents/
cp launchd/com.ayami.grafana-report.weekly.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.ayami.grafana-report.daily.plist
launchctl load ~/Library/LaunchAgents/com.ayami.grafana-report.weekly.plist

# to uninstall:
launchctl unload ~/Library/LaunchAgents/com.ayami.grafana-report.daily.plist
launchctl unload ~/Library/LaunchAgents/com.ayami.grafana-report.weekly.plist
rm ~/Library/LaunchAgents/com.ayami.grafana-report.{daily,weekly}.plist
```

Logs land in `logs/daily.log` / `logs/weekly.log` (gitignored, `*.log`).

### Reliability fixes (2026-08-23, after the first real automated run failed twice)

Both the 16:00 launchd trigger and a manual `launchctl start` failed on
first real-world use: the scheduled job didn't actually start until 16:36
(36 min late — the Mac had been asleep), and once it did start, Chromium's
own `launch()` timed out at 180s. Root cause: this Mac's **battery-power
idle sleep is 1 minute** (`pmset -g batt` → `sleep 1`), far shorter than a
full report run (~12 min) — the machine was falling back asleep *during*
the run itself. Separately, a manual run failed on `Grafana login timeout`
minutes after VPN had tested reachable, confirming the VPN here is
intermittently flaky, not just an occasional cold-start thing.

Two fixes shipped for this:

1. **`caffeinate -s`** now wraps the actual `node dist/cli.js <cmd>` call in
   `scripts/run-report.sh` — holds a sleep-prevent assertion for the run's
   duration, released automatically on exit. Fixes the mid-run sleep/Chromium
   timeout. Does **not** fix a machine that's already asleep before launchd
   even fires (see below).
2. **Retry with backoff**: `runGenerateWithAlert` in `cli.ts` now retries the
   whole generate flow up to 3× with a 60s delay between attempts before
   giving up and alerting. No error-type classification — any failure gets
   retried the same way, which is a deliberate simplicity tradeoff (a
   bad-credentials run just wastes ~2 minutes before alerting, same as a
   real VPN blip).

**Still unresolved — needs มอส, not fixable from here:**

- **If the Mac is fully asleep before 16:00, launchd still won't wake it.**
  `caffeinate` can't help — the job hasn't started yet. Two options, neither
  attempted automatically (both are system-wide power changes I can't make
  without sudo, and `pmset repeat wake` schedule-based wake is known to be
  flaky on battery-only MacBooks anyway):
  - **Simplest: keep the Mac plugged into AC power** around 16:00 — `pmset -g
    custom` already shows `sleep 0` (never sleep) on AC power on this
    machine, so this alone should prevent the problem without any further
    change.
  - Or, if มอส wants a real wake-from-sleep schedule regardless of power
    source, run this once (requires sudo password, interactive terminal —
    not something I can run from here):
    ```bash
    sudo pmset repeat wake MTWRFSU 15:55:00
    ```
    This wakes the Mac at 15:55 daily/weekly, 5 minutes before the launchd
    trigger, on every day of the week (harmless on days neither job fires).
- No catch-up/backfill logic if a scheduled run is skipped entirely (e.g.
  Mac was off, not just asleep) — it simply doesn't run until the next
  scheduled time.

**If `nvm`'s default node version changes**, update `NODE_BIN` in
`scripts/run-report.sh` to match (`which node` after `nvm use`).

## PDF quick-reference (`quickref`)

Design decisions (2026-08-22, confirmed with มอส): PDF is an **internal
quick-reference for personal use, not a client deliverable** — so it stays
lean on purpose:

- **Risk matrix + root-cause hints only, no screenshot galleries.** Reuses
  the same `includeGalleries:false` render path built for the Discord
  size-cap fallback (`report.ts`), just triggered intentionally here instead
  of as an error-path fallback.
- **On-demand only** — not part of the `daily`/`weekly` cron/launchd jobs,
  and never delivered to Discord (`deliver: false` always).
- **Skips screenshot capture entirely** (`skipScreenshots`), and only
  targets dashboards with peak-value extraction (`server` — see
  `DASHBOARDS` in `config.ts`), since a screenshot-free PDF has no use for
  the IIS/MSSQL panel galleries anyway. This is the slow part of a normal
  run (network round-trip + settle waits per panel), so `quickref` is
  meaningfully faster than `generate --format pdf`.

## Discord delivery

- Both `daily` and `weekly` render the *same* report shape (full screenshot
  galleries) and attach the HTML file to `DISCORD_WEBHOOK_URL` as-is —
  observed report sizes (1–16MB) are comfortably under Discord's 25MB
  webhook upload cap, so there's no pre-emptive compression (YAGNI, per
  design review 2026-08-22).
- **If a report ever exceeds the cap**, `src/discord.ts` catches it and
  `cli.ts` automatically re-renders a compact version with
  `includeGalleries: false` (risk matrix + root-cause hints only, no
  screenshots) and sends that instead, with a note pointing at the full
  local file path.
- **If Grafana/VPN is unreachable, or the Discord POST itself fails**, a
  text-only alert is sent to the same webhook (`sendTextAlert`) so a failure
  is never silent in an unattended cron/launchd run — check `logs/*.log` for
  the full error either way.

## Known limitations (v1)

- Host groups (`src/config.ts`) are manually curated from this session's
  findings, not auto-discovered from Grafana's template variables. Update
  `HOST_GROUPS` if the VM fleet changes.
- Root-cause hints (`src/rootcause.ts`) are a small static table matched on
  metric type + a host-group-name substring (e.g. "mssql") — not a full
  runbook system. Expected to need occasional hand-editing as the infra
  changes.
- No explicit request timeout on Prometheus queries (`prometheus.ts`, pre-existing
  pattern) — if the Grafana datasource proxy hangs, the whole run stalls. Flagged
  by zcode's code review (2026-08-23), not yet fixed.
- No retry logic for a failed Discord POST or an unreachable Grafana/VPN —
  both just alert-and-exit. No dedup/lock-file guard against a manual run
  overlapping a scheduled one.
- Screenshot waits use `networkidle` + a fixed 1.2s settle delay rather than
  a Grafana-specific "panel finished loading" signal — reliable in testing
  but may need tuning if panels grow noticeably heavier.
- HTML → PDF export *design* (styling/layout for print, beyond the existing
  `--format pdf` plumbing) is a separate later phase, out of scope here.
