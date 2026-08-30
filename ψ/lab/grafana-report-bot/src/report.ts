import { readFileSync } from "node:fs";
import type { PeakReading, StorageReading } from "./prometheus.js";
import { CPU_THRESHOLD_PCT, MEMORY_THRESHOLD_PCT, STORAGE_REMAINING_THRESHOLD_PCT } from "./config.js";
import { rootCauseHints, type MetricType } from "./rootcause.js";

export interface GroupFinding {
  groupName: string;
  metric: "CPU" | "Memory";
  threshold: number;
  peaks: PeakReading[];
}

export interface RiskRow {
  instance: string;
  group: string;
  cpu?: PeakReading;
  memory?: PeakReading;
  storage: StorageReading[];
  /** bits/sec, peak combined sent+received. No agreed threshold — informational only. */
  network?: PeakReading;
  /** bytes/sec, peak combined read+write. No agreed threshold — informational only. */
  diskIo?: PeakReading;
}

export interface DownHostFinding {
  instance: string;
  /** resolved host-group name, or "ไม่ทราบกลุ่ม" if the instance isn't in any configured HOST_GROUPS */
  group: string;
}

export interface PanelShot {
  dashboardTitle: string;
  panelTitle: string;
  filePath: string;
}

export interface ReportInput {
  period: { from: string; to: string };
  findings: GroupFinding[];
  riskRows: RiskRow[];
  galleries: Record<string, PanelShot[]>; // dashboardTitle -> panels
  /** instances currently reporting up==0 — right now, not a windowed peak. Zero-tolerance: any entry is critical. */
  downHosts?: DownHostFinding[];
  /** false = strip screenshot galleries (compact/Discord-size-cap fallback render) */
  includeGalleries?: boolean;
  /** shown as a banner near the top when set, e.g. explaining a compact fallback */
  compactNote?: string;
}

function toDataUri(filePath: string): string {
  const bytes = readFileSync(filePath);
  return `data:image/png;base64,${bytes.toString("base64")}`;
}

function severity(value: number, threshold: number): "critical" | "good" {
  return value > threshold ? "critical" : "good";
}

function hintsBlock(metric: MetricType, groupName: string): string {
  const steps = rootCauseHints(metric, groupName);
  if (!steps.length) return "";
  const items = steps.map((s) => `<li>${s}</li>`).join("");
  return `
    <div class="hints">
      <div class="hints-label">แนะนำจุดที่ควรไปตรวจต่อ</div>
      <ul class="hints-list">${items}</ul>
    </div>`;
}

function downHostsSection(downHosts: DownHostFinding[]): string {
  if (!downHosts.length) return "";
  const rows = downHosts
    .map(
      (d) => `
      <tr>
        <td class="mono">${d.instance}</td>
        <td>${d.group}</td>
      </tr>`,
    )
    .join("");
  return `
  <section id="down-hosts" class="finding critical down-alert">
    <div class="finding-head">
      <span class="tag">❌ เครื่องล่มตอนนี้ (ขณะสร้างรายงาน)</span>
      <span class="peak-value critical">${downHosts.length}</span>
      <span class="threshold">เกณฑ์ &gt; 0 = วิกฤต</span>
    </div>
    <table class="finding-table">
      <thead><tr><th>Host</th><th>Group</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>
    ${hintsBlock("Down", "")}
  </section>`;
}

function findingCard(f: GroupFinding): string {
  const top = f.peaks[0];
  if (!top) return "";
  const sev = severity(top.value, f.threshold);
  const rows = f.peaks
    .slice(0, 8)
    .map(
      (p) => `
      <tr>
        <td class="mono">${p.instance}</td>
        <td class="mono num ${severity(p.value, f.threshold)}">${p.value.toFixed(1)}%</td>
        <td class="mono">${new Date(p.timestampMs).toLocaleString("th-TH")}</td>
      </tr>`,
    )
    .join("");
  return `
  <div class="finding ${sev}">
    <div class="finding-head">
      <span class="tag">${f.metric} · ${f.groupName}</span>
      <span class="peak-value ${sev}">${top.value.toFixed(1)}%</span>
      <span class="threshold">เกณฑ์ ${f.threshold}%</span>
    </div>
    <table class="finding-table">
      <thead><tr><th>Host</th><th>Peak</th><th>เวลา</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>
    ${sev === "critical" ? hintsBlock(f.metric, f.groupName) : ""}
  </div>`;
}

function cpuMemCell(reading: PeakReading | undefined, threshold: number): string {
  if (!reading) return `<td class="mono cell-empty">—</td>`;
  const sev = severity(reading.value, threshold);
  return `<td class="mono cell-metric ${sev}">${reading.value.toFixed(1)}%</td>`;
}

function formatBits(bitsPerSec: number): string {
  if (bitsPerSec >= 1_000_000) return `${(bitsPerSec / 1_000_000).toFixed(1)} Mbps`;
  if (bitsPerSec >= 1_000) return `${(bitsPerSec / 1_000).toFixed(1)} Kbps`;
  return `${bitsPerSec.toFixed(0)} bps`;
}

function formatBytesPerSec(bytesPerSec: number): string {
  if (bytesPerSec >= 1_048_576) return `${(bytesPerSec / 1_048_576).toFixed(1)} MB/s`;
  if (bytesPerSec >= 1_024) return `${(bytesPerSec / 1_024).toFixed(1)} KB/s`;
  return `${bytesPerSec.toFixed(0)} B/s`;
}

/** No agreed threshold exists for network/disk I/O — always neutral, informational only. */
function neutralCell(reading: PeakReading | undefined, format: (v: number) => string): string {
  if (!reading) return `<td class="mono cell-empty">—</td>`;
  return `<td class="mono cell-neutral">${format(reading.value)}</td>`;
}

function storageCell(readings: StorageReading[]): string {
  if (!readings.length) return `<td class="mono cell-empty">—</td>`;
  const parts = readings
    .slice(0, 4)
    .map((r) => {
      const sev = r.value < STORAGE_REMAINING_THRESHOLD_PCT ? "critical" : "good";
      return `<span class="storage-chip ${sev}">${r.volume} ${r.value.toFixed(1)}%</span>`;
    })
    .join(" ");
  return `<td class="cell-storage">${parts}</td>`;
}

function storageFindingCards(rows: RiskRow[]): string {
  const byGroup = new Map<string, { instance: string; volume: string; value: number }[]>();
  for (const row of rows) {
    for (const s of row.storage) {
      if (s.value < STORAGE_REMAINING_THRESHOLD_PCT) {
        const list = byGroup.get(row.group) ?? [];
        list.push({ instance: row.instance, volume: s.volume, value: s.value });
        byGroup.set(row.group, list);
      }
    }
  }
  return [...byGroup.entries()]
    .map(([group, items]) => {
      const tableRows = items
        .sort((a, b) => a.value - b.value)
        .slice(0, 8)
        .map(
          (i) => `
      <tr>
        <td class="mono">${i.instance}</td>
        <td class="mono">${i.volume}</td>
        <td class="mono num critical">${i.value.toFixed(1)}%</td>
      </tr>`,
        )
        .join("");
      return `
  <div class="finding critical">
    <div class="finding-head">
      <span class="tag">Storage · ${group}</span>
      <span class="threshold">เกณฑ์เหลือ &lt; ${STORAGE_REMAINING_THRESHOLD_PCT}%</span>
    </div>
    <table class="finding-table">
      <thead><tr><th>Host</th><th>Volume</th><th>เหลือ</th></tr></thead>
      <tbody>${tableRows}</tbody>
    </table>
    ${hintsBlock("Storage", group)}
  </div>`;
    })
    .join("\n");
}

function rowHasRisk(row: RiskRow): boolean {
  const cpuRisk = row.cpu ? row.cpu.value > CPU_THRESHOLD_PCT : false;
  const memRisk = row.memory ? row.memory.value > MEMORY_THRESHOLD_PCT : false;
  const storageRisk = row.storage.some((s) => s.value < STORAGE_REMAINING_THRESHOLD_PCT);
  return cpuRisk || memRisk || storageRisk;
}

export function countRiskyRows(rows: RiskRow[]): number {
  return rows.filter(rowHasRisk).length;
}

function riskMatrixSection(rows: RiskRow[]): string {
  const sorted = [...rows].sort((a, b) => Number(rowHasRisk(b)) - Number(rowHasRisk(a)));
  const riskCount = rows.filter(rowHasRisk).length;

  const tableRows = sorted
    .map((row) => {
      const risky = rowHasRisk(row);
      return `
      <tr class="${risky ? "row-risk" : ""}">
        <td>${risky ? '<span class="risk-dot"></span>' : ""}</td>
        <td class="mono">${row.instance}</td>
        <td>${row.group}</td>
        ${cpuMemCell(row.cpu, CPU_THRESHOLD_PCT)}
        ${cpuMemCell(row.memory, MEMORY_THRESHOLD_PCT)}
        ${storageCell(row.storage)}
        ${neutralCell(row.network, formatBits)}
        ${neutralCell(row.diskIo, formatBytesPerSec)}
      </tr>`;
    })
    .join("");

  return `
  <section class="risk-section" id="risk-matrix">
    <div class="risk-header">
      <h2 style="border:none;margin:0;padding:0;">สรุปจุดเสี่ยง — CPU / Memory / Storage</h2>
      <span class="risk-badge ${riskCount ? "critical" : "good"}">${riskCount} จาก ${rows.length} เครื่องเข้าเกณฑ์เสี่ยง</span>
    </div>
    <div class="risk-legend mono">เกณฑ์: CPU/Memory &gt; ${CPU_THRESHOLD_PCT}% (สีแดง) · Storage เหลือ &lt; ${STORAGE_REMAINING_THRESHOLD_PCT}% (สีแดง) · Network/Disk I/O แสดงเป็นข้อมูลอ้างอิง ยังไม่มีเกณฑ์ที่ตกลงกันไว้</div>
    <table class="risk-table">
      <thead>
        <tr><th></th><th>Host</th><th>Group</th><th>CPU peak</th><th>Memory peak</th><th>Storage (แย่สุดต่อไดรฟ์)</th><th>Network peak</th><th>Disk I/O peak</th></tr>
      </thead>
      <tbody>${tableRows}</tbody>
    </table>
  </section>`;
}

function slugify(s: string): string {
  return s
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function gallerySection(dashboardTitle: string, shots: PanelShot[]): string {
  const cards = shots
    .map(
      (s) => `
    <figure class="panel-shot">
      <img src="${toDataUri(s.filePath)}" alt="${s.panelTitle}" />
      <figcaption>${s.panelTitle}</figcaption>
    </figure>`,
    )
    .join("");
  return `
  <section class="gallery-section" id="dash-${slugify(dashboardTitle)}">
    <h2>${dashboardTitle}</h2>
    <div class="gallery-grid">${cards}</div>
  </section>`;
}

function coverPage(period: { from: string; to: string }, hostCount: number, riskCount: number, downCount: number): string {
  const generatedAt = new Date().toLocaleString("th-TH");
  return `
  <section class="cover">
    <div class="cover-eyebrow mono">Infrastructure Monitoring Report</div>
    <h1 class="cover-title">Grafana Weekly Report</h1>
    <div class="cover-sub">Backoffice · E-VISA · MSSQL — VMware vSphere Health Report</div>
    <div class="cover-period">
      <div class="cover-period-label">ช่วงเวลารายงาน</div>
      <div class="cover-period-value mono">${period.from} &rarr; ${period.to}</div>
    </div>
    <div class="cover-meta">
      <div><span class="cover-meta-k">เครื่องล่มตอนนี้</span><span class="cover-meta-v mono ${downCount ? "critical" : "good"}">${downCount}</span></div>
      <div><span class="cover-meta-k">เครื่องที่ตรวจสอบ</span><span class="cover-meta-v mono">${hostCount}</span></div>
      <div><span class="cover-meta-k">เข้าเกณฑ์เสี่ยง</span><span class="cover-meta-v mono ${riskCount ? "critical" : "good"}">${riskCount}</span></div>
      <div><span class="cover-meta-k">สร้างเมื่อ</span><span class="cover-meta-v mono">${generatedAt}</span></div>
    </div>
  </section>`;
}

function tocSection(dashboardTitles: string[], hasStorageFindings: boolean, hasDownHosts: boolean): string {
  const items = [
    ...(hasDownHosts ? [{ id: "down-hosts", label: "❌ เครื่องล่มตอนนี้" }] : []),
    { id: "risk-matrix", label: "สรุปจุดเสี่ยง — CPU / Memory / Storage" },
    { id: "server-findings", label: "Server Monitoring — CPU / Memory รายกลุ่ม" },
    ...(hasStorageFindings ? [{ id: "storage-findings", label: "Storage — รายกลุ่ม" }] : []),
    ...dashboardTitles.map((t) => ({ id: `dash-${slugify(t)}`, label: t })),
  ];
  const rows = items
    .map((it, i) => `<li><a href="#${it.id}"><span class="toc-num mono">${String(i + 1).padStart(2, "0")}</span>${it.label}</a></li>`)
    .join("");
  return `
  <section class="toc">
    <h2 style="border:none;">สารบัญ</h2>
    <ul class="toc-list">${rows}</ul>
  </section>`;
}

export function buildReportHtml(input: ReportInput): string {
  const includeGalleries = input.includeGalleries ?? true;
  const downHosts = input.downHosts ?? [];
  const downSection = downHostsSection(downHosts);
  const riskMatrix = riskMatrixSection(input.riskRows);
  const riskCount = input.riskRows.filter(rowHasRisk).length;
  const findingCards = input.findings.map(findingCard).join("\n");
  const storageCards = storageFindingCards(input.riskRows);
  const dashboardTitles = includeGalleries ? Object.keys(input.galleries) : [];
  const galleries = includeGalleries
    ? Object.entries(input.galleries)
        .map(([title, shots]) => gallerySection(title, shots))
        .join("\n")
    : "";
  const cover = coverPage(input.period, input.riskRows.length, riskCount, downHosts.length);
  const toc = tocSection(dashboardTitles, Boolean(storageCards), downHosts.length > 0);
  const compactBanner = input.compactNote
    ? `<div class="compact-note">${input.compactNote}</div>`
    : "";

  return `<!doctype html>
<html lang="th">
<head>
<meta charset="utf-8" />
<title>Grafana Weekly Report</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Sarabun:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #f5f7fa; --surface: #fff; --text: #1a2330; --text-muted: #5c6b7d;
    --border: #dde3ec; --accent: #2b6cb0;
    --critical: #c23b34; --critical-soft: #fbe9e7;
    --good: #2f7d54; --good-soft: #e6f3ec;
  }
  * { box-sizing: border-box; }
  body { margin:0; background:var(--bg); color:var(--text); font-family:"Sarabun","Segoe UI",sans-serif; padding:32px 20px; }
  .page { max-width: 1000px; margin: 0 auto; }
  .mono { font-family:"IBM Plex Mono",Consolas,monospace; font-variant-numeric: tabular-nums; }
  h1 { font-size: 26px; margin: 0 0 4px; }
  .meta { color: var(--text-muted); font-size: 13px; margin-bottom: 28px; }
  h2 { font-size: 17px; margin: 32px 0 12px; border-bottom: 2px solid var(--text); padding-bottom: 8px; }
  .finding { border: 1px solid var(--border); border-radius: 10px; margin-bottom: 14px; overflow: hidden; }
  .finding-head { display:flex; align-items:center; gap:12px; padding:10px 16px; background: var(--surface); }
  .finding.critical .finding-head { background: var(--critical-soft); }
  .finding.good .finding-head { background: var(--good-soft); }
  .tag { font-size: 12px; font-weight:600; text-transform:uppercase; letter-spacing:.04em; color: var(--text-muted); }
  .peak-value { margin-left: auto; font-family:"IBM Plex Mono",monospace; font-size: 20px; font-weight:700; }
  .peak-value.critical { color: var(--critical); }
  .peak-value.good { color: var(--good); }
  .threshold { font-size: 11px; color: var(--text-muted); font-family:"IBM Plex Mono",monospace; }
  .finding-table { width:100%; border-collapse: collapse; font-size: 13px; }
  .finding-table th { text-align:left; padding: 6px 16px; color: var(--text-muted); font-weight:500; font-size:11px; text-transform:uppercase; }
  .finding-table td { padding: 5px 16px; border-top: 1px solid var(--border); }
  .num.critical { color: var(--critical); font-weight:600; }
  .num.good { color: var(--good); }
  .hints { margin: 0 16px 14px; padding: 10px 14px; background: var(--critical-soft); border-radius: 8px; }
  .hints-label { font-size: 11px; font-weight:600; text-transform:uppercase; letter-spacing:.04em; color: var(--critical); margin-bottom: 4px; }
  .hints-list { margin: 0; padding-left: 18px; font-size: 13px; color: var(--text); }
  .hints-list li { margin: 2px 0; }
  .compact-note { background: #fff6e0; border: 1px solid #e8c766; color: #6b4e00; border-radius: 8px; padding: 10px 16px; font-size: 13px; margin-bottom: 20px; }
  .down-alert { margin-bottom: 28px; border: 2px solid var(--critical); }
  .down-alert .finding-head { background: var(--critical-soft); }
  .gallery-grid { display:grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px; }
  .panel-shot { margin:0; background: #14181f; border-radius: 8px; padding: 6px; border: 1px solid var(--border); }
  .panel-shot img { width:100%; display:block; border-radius: 4px; }
  .panel-shot figcaption { color: var(--text-muted); font-size: 11px; padding: 6px 4px 2px; }

  .risk-section { margin-bottom: 36px; }
  .risk-header { display:flex; align-items:center; gap: 14px; flex-wrap: wrap; margin-bottom: 6px; }
  .risk-badge { font-family:"IBM Plex Mono",monospace; font-size: 12px; font-weight:600; padding: 4px 10px; border-radius: 6px; }
  .risk-badge.critical { background: var(--critical-soft); color: var(--critical); }
  .risk-badge.good { background: var(--good-soft); color: var(--good); }
  .risk-legend { font-size: 11px; color: var(--text-muted); margin-bottom: 12px; }
  .risk-table { width:100%; border-collapse: collapse; background: var(--surface); border: 1px solid var(--border); border-radius: 10px; overflow: hidden; font-size: 13px; }
  .risk-table th { text-align:left; padding: 8px 12px; color: var(--text-muted); font-weight:500; font-size:11px; text-transform:uppercase; border-bottom: 2px solid var(--border); }
  .risk-table td { padding: 7px 12px; border-top: 1px solid var(--border); vertical-align: middle; }
  .risk-table tr.row-risk { background: var(--critical-soft); }
  .risk-dot { display:inline-block; width:8px; height:8px; border-radius:50%; background: var(--critical); }
  .cell-empty { color: var(--text-muted); }
  .cell-metric { font-weight: 600; }
  .cell-metric.critical { color: var(--critical); }
  .cell-metric.good { color: var(--good); }
  .cell-neutral { color: var(--text-muted); }
  .storage-chip { display:inline-block; font-family:"IBM Plex Mono",monospace; font-size: 11px; padding: 2px 6px; border-radius: 4px; margin: 1px 3px 1px 0; }
  .storage-chip.critical { background: var(--critical-soft); color: var(--critical); font-weight:600; }
  .storage-chip.good { background: var(--good-soft); color: var(--good); }

  .cover {
    max-width: 1000px; margin: 0 auto 40px; padding: 60px 20px 40px;
    border-bottom: 3px solid var(--text);
  }
  .cover-eyebrow { color: var(--accent); font-size: 12px; letter-spacing:.1em; text-transform:uppercase; font-weight:600; }
  .cover-title { font-size: 42px; margin: 14px 0 4px; }
  .cover-sub { color: var(--text-muted); font-size: 15px; margin-bottom: 32px; }
  .cover-period-label { font-size: 12px; color: var(--text-muted); text-transform:uppercase; letter-spacing:.05em; }
  .cover-period-value { font-size: 26px; font-weight:700; margin-top: 4px; }
  .cover-meta { display:flex; gap: 32px; margin-top: 28px; padding-top: 20px; border-top: 1px solid var(--border); flex-wrap: wrap; }
  .cover-meta-k { display:block; font-size: 11px; color: var(--text-muted); text-transform:uppercase; letter-spacing:.05em; }
  .cover-meta-v { display:block; font-size: 20px; font-weight:700; margin-top: 2px; }
  .cover-meta-v.critical { color: var(--critical); }
  .cover-meta-v.good { color: var(--good); }

  .toc { margin-bottom: 32px; }
  .toc-list { list-style:none; margin:0; padding:0; }
  .toc-list li { border-bottom: 1px dashed var(--border); }
  .toc-list a { display:flex; align-items:center; gap:14px; padding: 10px 4px; color: var(--text); text-decoration:none; font-size: 14px; }
  .toc-num { color: var(--accent); font-weight:600; }

  @media print {
    body { padding: 0; background: #fff; }
    .cover { page-break-after: always; margin-bottom: 0; }
    .toc { page-break-after: always; }
    .gallery-section { page-break-before: always; }
  }
</style>
</head>
<body>
${cover}
<div class="page">
  ${compactBanner}
  ${toc}

  ${downSection}

  ${riskMatrix}

  <section id="server-findings">
    <h2>Server Monitoring — CPU / Memory รายกลุ่ม (เกณฑ์ CPU/Mem &gt; ${CPU_THRESHOLD_PCT}% / ${MEMORY_THRESHOLD_PCT}%)</h2>
    ${findingCards}
  </section>

  ${
    storageCards
      ? `<section id="storage-findings">
    <h2>Storage รายกลุ่ม (เกณฑ์เหลือ &lt; ${STORAGE_REMAINING_THRESHOLD_PCT}%)</h2>
    ${storageCards}
  </section>`
      : ""
  }

  ${galleries}
</div>
</body>
</html>`;
}
