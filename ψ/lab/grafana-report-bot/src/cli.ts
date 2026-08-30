#!/usr/bin/env node
import { Command } from "commander";
import { chromium, type Browser } from "playwright";
import { config as loadEnv } from "dotenv";
import { mkdirSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import {
  login,
  listDashboards,
  fetchDashboard,
  flattenPanels,
  screenshotPanel,
  panelOutFile,
} from "./grafana.js";
import {
  peakCpuByInstance,
  peakMemoryByInstance,
  worstStorageByInstance,
  peakNetworkByInstance,
  peakDiskIoByInstance,
  currentlyDownInstances,
} from "./prometheus.js";
import { resolveTime } from "./time.js";
import {
  buildReportHtml,
  countRiskyRows,
  type DownHostFinding,
  type GroupFinding,
  type PanelShot,
  type RiskRow,
} from "./report.js";
import { DASHBOARDS, HOST_GROUPS, CPU_THRESHOLD_PCT, MEMORY_THRESHOLD_PCT } from "./config.js";
import { hasDiscordWebhook, sendReportFile, sendTextAlert, DiscordUploadTooLargeError } from "./discord.js";

loadEnv();

const GRAFANA_URL = process.env.GRAFANA_URL ?? "";
const GRAFANA_USER = process.env.GRAFANA_USER ?? "";
const GRAFANA_PASSWORD = process.env.GRAFANA_PASSWORD ?? "";
const PROMETHEUS_DS_UID = process.env.PROMETHEUS_DS_UID ?? "";

function requireEnv() {
  const missing = [
    ["GRAFANA_URL", GRAFANA_URL],
    ["GRAFANA_USER", GRAFANA_USER],
    ["GRAFANA_PASSWORD", GRAFANA_PASSWORD],
    ["PROMETHEUS_DS_UID", PROMETHEUS_DS_UID],
  ].filter(([, v]) => !v);
  if (missing.length) {
    console.error(`Missing env vars: ${missing.map(([k]) => k).join(", ")}`);
    console.error("Copy .env.example to .env and fill it in.");
    process.exit(1);
  }
}

interface GenerateOptions {
  from: string;
  to: string;
  out: string;
  dashboardKeys: string; // comma-separated
  width: number;
  height: number;
  format: "html" | "pdf" | "both";
  deliver: boolean;
  /** prefixes the Discord message content, e.g. "📊 Grafana Daily Report" */
  label: string;
  /** skip per-panel screenshot capture entirely (still runs Prometheus peak extraction) — for a fast, gallery-free run */
  skipScreenshots?: boolean;
  /** false = strip screenshot galleries from the rendered report (independent of skipScreenshots, but implied by it) */
  includeGalleries?: boolean;
}

/** Screenshots dashboards + pulls Prometheus peaks, writes the report(s) to disk, and (if enabled) delivers to Discord. Guarantees the browser closes even on failure. */
async function runGenerate(opts: GenerateOptions): Promise<void> {
  requireEnv();
  const runId = new Date().toISOString().replace(/[:.]/g, "-");
  const screenshotDir = join("screenshots", runId);
  mkdirSync(screenshotDir, { recursive: true });
  mkdirSync("reports", { recursive: true });

  const wantedKeys = new Set(opts.dashboardKeys.split(","));
  const targets = DASHBOARDS.filter((d) => wantedKeys.has(d.key));

  let browser: Browser | undefined;
  try {
    console.log(`Launching headless Chromium…`);
    browser = await chromium.launch();
    const context = await browser.newContext();
    const page = await context.newPage();

    console.log(`Logging into ${GRAFANA_URL}…`);
    await login(context.request, GRAFANA_URL, GRAFANA_USER, GRAFANA_PASSWORD);

    // Zero-tolerance check, independent of which dashboards were requested —
    // "up == 0" right now, not a windowed peak. Cheap (one instant query), so
    // it runs unconditionally, including in skipScreenshots/quickref mode.
    //
    // Scoped to HOST_GROUPS only (confirmed 2026-08-23, after a live test
    // surfaced 7 down instances entirely outside our tracked fleet — this
    // Prometheus scrapes more than just Backoffice/E-VISA/MSSQL, and an
    // unscoped alert would be noisy/untrustworthy from day one).
    const allDownInstances = await currentlyDownInstances(context.request, GRAFANA_URL, PROMETHEUS_DS_UID);
    const downHosts: DownHostFinding[] = allDownInstances.flatMap((instance) => {
      const group = HOST_GROUPS.find((g) => g.instances.includes(instance));
      return group ? [{ instance, group: group.name }] : [];
    });
    if (downHosts.length) {
      console.log(`\n❌ ${downHosts.length} tracked host(s) currently down: ${downHosts.map((d) => d.instance).join(", ")}`);
    }
    const untrackedDown = allDownInstances.length - downHosts.length;
    if (untrackedDown) {
      console.log(`  (${untrackedDown} other down instance(s) outside HOST_GROUPS — not tracked, not alerted)`);
    }

    const findings: GroupFinding[] = [];
    const galleries: Record<string, PanelShot[]> = {};
    const riskRows: RiskRow[] = [];

    for (const target of targets) {
      console.log(`\n== ${target.title} (${target.uid}) ==`);
      const { dashboard } = await fetchDashboard(context.request, GRAFANA_URL, target.uid);
      const panels = flattenPanels(dashboard.panels);
      console.log(`  ${panels.length} panel(s) to capture`);

      const shots: PanelShot[] = [];
      if (opts.skipScreenshots) {
        console.log(`  (skipping screenshot capture — quick-reference mode)`);
      } else {
        for (const panel of panels) {
          const fileName = panelOutFile(target.key, panel);
          const outPath = join(screenshotDir, fileName);
          process.stdout.write(`  - ${panel.title} … `);
          try {
            await screenshotPanel(page, GRAFANA_URL, target.uid, dashboard.title, panel, outPath, {
              from: opts.from,
              to: opts.to,
              theme: "dark",
              width: opts.width,
              height: opts.height,
            });
            shots.push({ dashboardTitle: target.title, panelTitle: panel.title, filePath: outPath });
            console.log("ok");
          } catch (err) {
            console.log(`FAILED (${(err as Error).message})`);
          }
        }
      }
      galleries[target.title] = shots;

      if (target.extractPeaks) {
        const promStart = resolveTime(opts.from);
        const promEnd = resolveTime(opts.to);
        for (const group of HOST_GROUPS) {
          const [cpuPeaks, memPeaks, storageReadings, networkPeaks, diskIoPeaks] = await Promise.all([
            peakCpuByInstance(context.request, GRAFANA_URL, PROMETHEUS_DS_UID, group.instances, promStart, promEnd),
            peakMemoryByInstance(context.request, GRAFANA_URL, PROMETHEUS_DS_UID, group.instances, promStart, promEnd),
            worstStorageByInstance(context.request, GRAFANA_URL, PROMETHEUS_DS_UID, group.instances, promStart, promEnd),
            peakNetworkByInstance(context.request, GRAFANA_URL, PROMETHEUS_DS_UID, group.instances, promStart, promEnd),
            peakDiskIoByInstance(context.request, GRAFANA_URL, PROMETHEUS_DS_UID, group.instances, promStart, promEnd),
          ]);
          findings.push({ groupName: group.name, metric: "CPU", threshold: CPU_THRESHOLD_PCT, peaks: cpuPeaks });
          findings.push({ groupName: group.name, metric: "Memory", threshold: MEMORY_THRESHOLD_PCT, peaks: memPeaks });
          console.log(
            `  [Prometheus] ${group.name}: CPU peak ${cpuPeaks[0]?.value.toFixed(1)}% · Mem peak ${memPeaks[0]?.value.toFixed(1)}% · Storage worst ${storageReadings[0]?.value.toFixed(1)}%`,
          );

          for (const instance of group.instances) {
            riskRows.push({
              instance,
              group: group.name,
              cpu: cpuPeaks.find((p) => p.instance === instance),
              memory: memPeaks.find((p) => p.instance === instance),
              storage: storageReadings.filter((s) => s.instance === instance),
              network: networkPeaks.find((p) => p.instance === instance),
              diskIo: diskIoPeaks.find((p) => p.instance === instance),
            });
          }
        }
      }
    }

    const riskCount = countRiskyRows(riskRows);
    const reportInput = {
      period: { from: opts.from, to: opts.to },
      findings,
      riskRows,
      galleries,
      downHosts,
      includeGalleries: opts.includeGalleries ?? true,
    };
    const html = buildReportHtml(reportInput);
    const basePath = opts.out || join("reports", runId);
    const htmlPath = basePath.endsWith(".html") || basePath.endsWith(".pdf") ? basePath : `${basePath}.html`;
    const pdfPath = htmlPath.replace(/\.html$/, ".pdf");

    if (opts.format === "html" || opts.format === "both") {
      writeFileSync(htmlPath, html, "utf-8");
      console.log(`\nHTML report written to ${htmlPath}`);
    }

    if (opts.format === "pdf" || opts.format === "both") {
      // page.pdf() needs the content to actually be on disk (or reachable) —
      // write it to a temp file even if only PDF output was requested.
      const sourceHtmlPath = opts.format === "pdf" ? `${pdfPath}.tmp.html` : htmlPath;
      if (opts.format === "pdf") writeFileSync(sourceHtmlPath, html, "utf-8");

      const pdfPage = await context.newPage();
      await pdfPage.goto(`file://${resolve(sourceHtmlPath)}`, { waitUntil: "networkidle" });
      await pdfPage.pdf({
        path: pdfPath,
        format: "A4",
        printBackground: true,
        margin: { top: "14mm", bottom: "16mm", left: "10mm", right: "10mm" },
        displayHeaderFooter: true,
        headerTemplate: `<span></span>`,
        footerTemplate: `
          <div style="width:100%; font-size:9px; color:#8d99ab; text-align:center; font-family:Arial,sans-serif;">
            Grafana Weekly Report &nbsp;·&nbsp; หน้า <span class="pageNumber"></span> / <span class="totalPages"></span>
          </div>`,
      });
      console.log(`PDF report written to ${pdfPath}`);

      if (opts.format === "pdf") {
        const { unlinkSync } = await import("node:fs");
        unlinkSync(sourceHtmlPath);
      }
    }

    if (opts.deliver && hasDiscordWebhook() && (opts.format === "html" || opts.format === "both")) {
      const downAlert = downHosts.length
        ? `🔴 เครื่องล่มตอนนี้ ${downHosts.length} เครื่อง: ${downHosts.map((d) => `${d.instance} (${d.group})`).join(", ")}\n`
        : "";
      const summary = `${downAlert}${opts.label} — ${opts.from} → ${opts.to}\nเข้าเกณฑ์เสี่ยง ${riskCount}/${riskRows.length} เครื่อง`;
      try {
        await sendReportFile(htmlPath, summary);
        console.log("Delivered to Discord.");
      } catch (err) {
        if (err instanceof DiscordUploadTooLargeError) {
          console.log(`Report too large for Discord (${err.message}) — sending compact fallback (no screenshots).`);
          const compactPath = htmlPath.replace(/\.html$/, ".compact.html");
          const compactHtml = buildReportHtml({
            ...reportInput,
            includeGalleries: false,
            compactNote: `ฉบับเต็มมีขนาดเกิน limit ของ Discord (${(err.byteLength / 1024 / 1024).toFixed(1)}MB) — ตัดรูป screenshot ออก ดูฉบับเต็มได้ที่เครื่อง: ${resolve(htmlPath)}`,
          });
          writeFileSync(compactPath, compactHtml, "utf-8");
          try {
            await sendReportFile(compactPath, `${summary}\n⚠️ ฉบับเต็มเกิน limit — แนบฉบับย่อ (ไม่มีรูป)`);
            console.log("Delivered compact fallback to Discord.");
          } catch (err2) {
            console.error(`Compact fallback delivery also failed: ${(err2 as Error).message}`);
            await sendTextAlert(
              `⚠️ ${opts.label} generate สำเร็จ (${resolve(htmlPath)}) แต่ส่งเข้า Discord ไม่สำเร็จแม้จะย่อแล้ว: ${(err2 as Error).message}`,
            );
          }
        } else {
          console.error(`Discord delivery failed: ${(err as Error).message}`);
          await sendTextAlert(
            `⚠️ ${opts.label} generate สำเร็จ (${resolve(htmlPath)}) แต่ส่งเข้า Discord ไม่สำเร็จ: ${(err as Error).message}`,
          );
        }
      }
    } else if (opts.deliver && !hasDiscordWebhook()) {
      console.log("DISCORD_WEBHOOK_URL not set — report saved locally only.");
    }
  } finally {
    if (browser) await browser.close();
  }
}

const program = new Command();
program.name("grafana-report").description("Headless Grafana screenshot + report bot");

program
  .command("list")
  .description("List dashboards visible to this Grafana account")
  .action(async () => {
    requireEnv();
    const browser = await chromium.launch();
    try {
      const context = await browser.newContext();
      await login(context.request, GRAFANA_URL, GRAFANA_USER, GRAFANA_PASSWORD);
      const dashboards = await listDashboards(context.request, GRAFANA_URL);
      for (const d of dashboards) console.log(`${d.uid}\t${d.title}`);
    } finally {
      await browser.close();
    }
  });

program
  .command("generate")
  .description("Screenshot dashboards + compose an on-demand HTML/PDF report")
  .option("-f, --from <time>", "Grafana relative/absolute from-time", "now-7d")
  .option("-t, --to <time>", "Grafana relative/absolute to-time", "now")
  .option("-o, --out <path>", "Output report path", "")
  .option("--dashboards <keys>", "Comma-separated dashboard keys to include", "server,iis,mssql")
  .option("--width <px>", "Panel screenshot width", "1000")
  .option("--height <px>", "Panel screenshot height", "500")
  .option("--format <type>", "Output format: html, pdf, or both", "both")
  .option("--deliver", "Send the report to Discord after generating (needs DISCORD_WEBHOOK_URL)", false)
  .action(async (opts) => {
    await runGenerateWithAlert({
      from: opts.from,
      to: opts.to,
      out: opts.out,
      dashboardKeys: String(opts.dashboards),
      width: Number(opts.width),
      height: Number(opts.height),
      format: opts.format,
      deliver: Boolean(opts.deliver),
      label: "📊 Grafana Report",
    });
  });

program
  .command("daily")
  .description("Generate + deliver the daily report (last 24h, all dashboards)")
  .option("--deliver", "Send to Discord (needs DISCORD_WEBHOOK_URL)", true)
  .option("--no-deliver", "Skip Discord delivery, save locally only")
  .action(async (opts) => {
    await runGenerateWithAlert({
      from: "now-24h",
      to: "now",
      out: "",
      dashboardKeys: "server,iis,mssql",
      width: 1000,
      height: 500,
      format: "html",
      deliver: Boolean(opts.deliver),
      label: "📊 Grafana Daily Report",
    });
  });

program
  .command("weekly")
  .description("Generate + deliver the weekly report (last 7 days, all dashboards)")
  .option("--deliver", "Send to Discord (needs DISCORD_WEBHOOK_URL)", true)
  .option("--no-deliver", "Skip Discord delivery, save locally only")
  .action(async (opts) => {
    await runGenerateWithAlert({
      from: "now-7d",
      to: "now",
      out: "",
      dashboardKeys: "server,iis,mssql",
      width: 1000,
      height: 500,
      format: "html",
      deliver: Boolean(opts.deliver),
      label: "🗓️ Grafana Weekly Report",
    });
  });

program
  .command("quickref")
  .description("Fast, screenshot-free PDF — risk matrix + root-cause hints only, for a quick personal check")
  .option("-f, --from <time>", "Grafana relative/absolute from-time", "now-24h")
  .option("-t, --to <time>", "Grafana relative/absolute to-time", "now")
  .option("-o, --out <path>", "Output PDF path", "")
  .action(async (opts) => {
    const peakDashboardKeys = DASHBOARDS.filter((d) => d.extractPeaks)
      .map((d) => d.key)
      .join(",");
    await runGenerateWithAlert({
      from: opts.from,
      to: opts.to,
      out: opts.out,
      dashboardKeys: peakDashboardKeys,
      width: 1000,
      height: 500,
      format: "pdf",
      deliver: false,
      label: "🖨️ Grafana Quick Reference",
      skipScreenshots: true,
      includeGalleries: false,
    });
  });

const MAX_ATTEMPTS = 3;
const RETRY_DELAY_MS = 60_000;

/**
 * Wraps runGenerate with a retry loop and, on final failure, a Discord alert
 * instead of failing silently in an unattended cron/launchd run.
 *
 * Added after a real failure on 2026-08-23: an unattended `daily` run hit
 * `apiRequestContext.post: Timeout 30000ms exceeded` on Grafana login — the
 * VPN this depends on is intermittently flaky, confirmed by a manual retry
 * succeeding minutes later. No attempt to distinguish error types (VPN blip
 * vs. wrong credentials, say) — a bad-credentials run will just burn ~2
 * extra minutes retrying uselessly before alerting, which is an acceptable
 * cost for not having to maintain an error-classification list.
 */
async function runGenerateWithAlert(opts: GenerateOptions): Promise<void> {
  let lastError: Error | undefined;
  for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt++) {
    try {
      await runGenerate(opts);
      return;
    } catch (err) {
      lastError = err as Error;
      console.error(`Attempt ${attempt}/${MAX_ATTEMPTS} failed: ${lastError.message}`);
      if (attempt < MAX_ATTEMPTS) {
        console.log(`Retrying in ${RETRY_DELAY_MS / 1000}s…`);
        await new Promise((r) => setTimeout(r, RETRY_DELAY_MS));
      }
    }
  }
  const message = lastError?.message ?? "unknown error";
  console.error(`Report generation failed after ${MAX_ATTEMPTS} attempts: ${message}`);
  await sendTextAlert(`❌ ${opts.label} generation FAILED after ${MAX_ATTEMPTS} attempts: ${message}`);
  process.exitCode = 1;
}

program.parseAsync(process.argv);
