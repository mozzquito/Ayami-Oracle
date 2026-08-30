import type { APIRequestContext, BrowserContext, Page } from "playwright";

export interface GrafanaPanel {
  id: number;
  title: string;
  type: string;
  panels?: GrafanaPanel[];
}

export interface DashboardJson {
  dashboard: {
    uid: string;
    title: string;
    panels: GrafanaPanel[];
  };
}

const SKIP_PANEL_TYPES = new Set(["row", "text", "news", "dashlist"]);

export async function login(
  request: APIRequestContext,
  baseUrl: string,
  user: string,
  password: string,
): Promise<void> {
  const res = await request.post(`${baseUrl}/login`, {
    data: { user, password },
  });
  if (!res.ok()) {
    throw new Error(`Grafana login failed: HTTP ${res.status()} ${await res.text()}`);
  }
}

export async function listDashboards(
  request: APIRequestContext,
  baseUrl: string,
): Promise<Array<{ uid: string; title: string; url: string }>> {
  const res = await request.get(`${baseUrl}/api/search`);
  if (!res.ok()) throw new Error(`Dashboard search failed: HTTP ${res.status()}`);
  const results = (await res.json()) as Array<{ uid: string; title: string; url: string; type: string }>;
  return results.filter((r) => r.type === "dash-db");
}

export async function fetchDashboard(
  request: APIRequestContext,
  baseUrl: string,
  uid: string,
): Promise<DashboardJson> {
  const res = await request.get(`${baseUrl}/api/dashboards/uid/${uid}`);
  if (!res.ok()) throw new Error(`Fetch dashboard ${uid} failed: HTTP ${res.status()}`);
  return (await res.json()) as DashboardJson;
}

/** Flatten panels, descending into collapsed rows, dropping non-visual panel types. */
export function flattenPanels(panels: GrafanaPanel[]): GrafanaPanel[] {
  const out: GrafanaPanel[] = [];
  for (const p of panels) {
    if (p.type === "row" && p.panels?.length) {
      out.push(...flattenPanels(p.panels));
      continue;
    }
    if (SKIP_PANEL_TYPES.has(p.type)) continue;
    out.push(p);
  }
  return out;
}

function slugify(title: string): string {
  return (
    title
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "") || "panel"
  );
}

export interface ScreenshotOptions {
  from: string;
  to: string;
  theme: "light" | "dark";
  width: number;
  height: number;
}

export async function screenshotPanel(
  page: Page,
  baseUrl: string,
  dashUid: string,
  dashTitle: string,
  panel: GrafanaPanel,
  outPath: string,
  opts: ScreenshotOptions,
): Promise<void> {
  const slug = slugify(dashTitle);
  const url =
    `${baseUrl}/d-solo/${dashUid}/${slug}` +
    `?orgId=1&panelId=${panel.id}&from=${encodeURIComponent(opts.from)}&to=${encodeURIComponent(opts.to)}&theme=${opts.theme}`;

  await page.setViewportSize({ width: opts.width, height: opts.height });
  await page.goto(url, { waitUntil: "networkidle", timeout: 30_000 });
  // First load's panel data query frequently gets cancelled ("runRequest.catchError
  // {cancelled: true}") on this instance — the failing Grafana Live WebSocket
  // handshake (nginx in front doesn't proxy the Upgrade) appears to race the
  // panel's own query. A single reload reliably clears it. Confirmed by checking
  // for a <canvas> element (0 before reload, 1 after) during debugging.
  await page.waitForTimeout(1200);
  await page.reload({ waitUntil: "networkidle", timeout: 30_000 });
  await page.waitForTimeout(1200);
  await page.screenshot({ path: outPath });
}

export function panelOutFile(dashKey: string, panel: GrafanaPanel): string {
  return `${dashKey}__${panel.id}_${slugify(panel.title)}.png`;
}
