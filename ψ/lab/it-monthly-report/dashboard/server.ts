// Local-only API server for the IT Service Monthly Report dashboard.
// Reads/writes the YAML data files that generate.py also consumes, and
// shells out to zcode/agy for the "AI ช่วยวิเคราะห์" feature.
//
// Data layout: data/<client_code>/<file>.yaml   (client_code = a-z0-9_- slug)
//              data/<client_code>/profile.yaml   (client metadata)
//
// Run: bun run server.ts   (listens on :8787, proxied by vite dev server)
import { existsSync, mkdirSync, readdirSync, readFileSync, writeFileSync } from "fs";
import { join, resolve } from "path";
import { spawn } from "child_process";
import yaml from "js-yaml";

const REPORT_ROOT = resolve(import.meta.dirname, "..");
const DATA_DIR = join(REPORT_ROOT, "data");
const GENERATE_PY = join(REPORT_ROOT, "generate.py");
const SCHEMA_YAML = join(REPORT_ROOT, "schema.yaml");
const VENV_PYTHON = join(REPORT_ROOT, ".venv", "bin", "python");

if (!existsSync(DATA_DIR)) mkdirSync(DATA_DIR, { recursive: true });

/** Sanitize a client code: lowercase a-z0-9 and hyphens/underscores only. */
function safeClientCode(raw: string): string {
  // lowercase FIRST — the old order stripped A-Z before .toLowerCase() could
  // see them, silently mapping "Kittisampan" -> "ittisampan"
  const slug = raw.toLowerCase().replace(/[^a-z0-9_-]/g, "");
  if (slug.length === 0) throw new Error("invalid client code");
  if (slug.includes("..")) throw new Error("invalid client code");
  if (slug === "profile" || slug.startsWith("_")) throw new Error("reserved client code");
  return slug;
}

function safeFileName(name: string): string {
  const base = name.replace(/[^a-zA-Z0-9._-]/g, "");
  if (!base.endsWith(".yaml")) throw new Error("filename must end with .yaml");
  if (base.includes("..")) throw new Error("invalid filename");
  return base;
}

function clientDir(clientCode: string): string {
  return join(DATA_DIR, safeClientCode(clientCode));
}

function json(data: unknown, init?: ResponseInit): Response {
  return new Response(JSON.stringify(data), {
    ...init,
    headers: { "content-type": "application/json", ...(init?.headers ?? {}) },
  });
}

function runCommand(cmd: string, args: string[], opts: { cwd?: string; timeoutMs?: number } = {}) {
  return new Promise<{ stdout: string; stderr: string; code: number | null }>((resolvePromise) => {
    const child = spawn(cmd, args, { cwd: opts.cwd ?? REPORT_ROOT });
    let stdout = "";
    let stderr = "";
    const timeout = setTimeout(() => {
      child.kill("SIGKILL");
    }, opts.timeoutMs ?? 10 * 60 * 1000);
    child.stdout.on("data", (d) => (stdout += d.toString()));
    child.stderr.on("data", (d) => (stderr += d.toString()));
    child.on("close", (code) => {
      clearTimeout(timeout);
      resolvePromise({ stdout, stderr, code });
    });
    child.on("error", (err) => {
      clearTimeout(timeout);
      resolvePromise({ stdout, stderr: String(err), code: -1 });
    });
  });
}

// ---------------------------------------------------------------------------
// Feature 2: Carry-forward helper — copies asset baseline from previous month
// ---------------------------------------------------------------------------

interface ReportData {
  [key: string]: unknown;
}

/** Fields to copy as baseline from previous month. */
const CARRY_FORWARD_KEYS = [
  "computers",
  "software.os_licenses",
  "software.office_licenses",
  "server.physical_servers",
  "server.guest_vms",
  "server.backup.scheduled_status",
  "server.backup.last_restore_test",
  "firewall_gateway.devices",
  "network.devices",
  "scope_of_work",
  "prepared_by",
  "checked_by",
  "report.client_name",
] as const;

/** Fields to reset every month — must NOT carry forward. */
const RESET_KEYS = [
  "health",
  "sla",
  "tickets",
  "recommendations",
  "sign_off",
  "report.report_date",
  "report.onsite_ma_date",
  "report.monitor_date",
] as const;

function getNestedValue(obj: unknown, path: string): unknown {
  const keys = path.split(".");
  let cur: unknown = obj;
  for (const k of keys) {
    if (cur === null || cur === undefined || typeof cur !== "object") return undefined;
    cur = (cur as Record<string, unknown>)[k];
  }
  return cur;
}

function setNestedValue(obj: Record<string, unknown>, path: string, value: unknown) {
  const keys = path.split(".");
  let cur = obj;
  for (let i = 0; i < keys.length - 1; i++) {
    const k = keys[i];
    if (cur[k] === null || cur[k] === undefined || typeof cur[k] !== "object") {
      cur[k] = {};
    }
    cur = cur[k] as Record<string, unknown>;
  }
  cur[keys[keys.length - 1]] = value;
}

/** Deep clone via JSON round-trip. */
function cloneDeep<T>(v: T): T {
  return JSON.parse(JSON.stringify(v));
}

/**
 * Carry forward asset baseline from prevData into a new month template.
 * Returns { data, carried: true } if prev month existed and data was carried,
 * or { data, carried: false, prevMonth } if first month (no carry-forward).
 */
function carryForward(
  prevData: ReportData | null,
  monthName: string,
  year: number,
): { data: ReportData; carried: boolean; prevMonth?: string } {
  if (!prevData) {
    // No previous month — return empty report
    return { data: emptyServerReportData(monthName, year), carried: false };
  }

  // Start with fresh empty, then overlay carried fields
  const data = emptyServerReportData(monthName, year);
  for (const key of CARRY_FORWARD_KEYS) {
    const val = getNestedValue(prevData, key);
    if (val !== undefined && val !== null) {
      setNestedValue(data as Record<string, unknown>, key, cloneDeep(val));
    }
  }

  // Clear license_alerts on carried software (recalculated every time)
  const software = data["software"] as Record<string, unknown> | undefined;
  if (software) {
    software["license_alerts"] = [];
  }

  return { data, carried: true };
}

/** Minimal empty report data on the server side (mirrors emptyReportData in types.ts). */
function emptyServerReportData(month: string, year: number): ReportData {
  return {
    report: {
      title: "IT Service Monthly Report",
      month,
      year,
      client_name: null,
      report_date: null,
      onsite_ma_date: null,
      monitor_date: null,
    },
    prepared_by: { name: null, role: "IT Specialist", phone: null, email: null },
    checked_by: { name: null, role: "Project Manager", phone: null, email: null },
    health: { overall_status: null, highlights: [], critical_alerts: [] },
    sla: {
      uptime_percent: null,
      avg_response_hours: null,
      avg_resolution_hours: null,
      sla_met_percent: null,
    },
    trend_mom: {
      ticket_count: { this_month: null, last_month: null },
      uptime_percent: { this_month: null, last_month: null },
      recurring_issues: [],
    },
    computers: {
      contract_count: null,
      serviced_count: null,
      by_type: { desktop: 0, laptop: 0, all_in_one: 0, macbook: 0 },
      hard_disk: { normal: 0, caution: 0 },
      battery: { ok: 0, degraded: 0 },
      age_distribution: { under_1y: 0, "1_2y": 0, "2_4y": 0, "5_7y": 0, over_7y: 0 },
      replacement_recommendation: null,
    },
    software: { os_licenses: [], office_licenses: [], license_alerts: [] },
    server: {
      contract_count: null,
      serviced_count: null,
      physical_servers: [],
      guest_vms: [],
      backup: { scheduled_status: null, last_restore_test: null },
    },
    firewall_gateway: { devices: [], warning_critical_log: null },
    network: { devices: [], warning_critical_log: null },
    tickets: {
      incident_count: 0,
      service_request_count: 0,
      status: { in_progress: 0, pending: 0, done: 0 },
      list: [],
    },
    scope_of_work: [],
    recommendations: [],
    sign_off: { client_signer_name: null, client_signed_date: null },
  };
}

// ---------------------------------------------------------------------------
// Feature 3: Changelog — compare two months and produce bullet list
// ---------------------------------------------------------------------------

function buildChangelog(currentData: ReportData, prevData: ReportData): string[] {
  const changes: string[] = [];

  // Computer count
  const curComp = (currentData["computers"] as Record<string, unknown>)?.["contract_count"] as number | null;
  const prevComp = (prevData["computers"] as Record<string, unknown>)?.["contract_count"] as number | null;
  if (curComp !== null && prevComp !== null && curComp !== prevComp) {
    const diff = curComp - prevComp;
    changes.push(`จำนวนคอมพิวเตอร์เปลี่ยนจาก ${prevComp} เป็น ${curComp} (${diff > 0 ? "+" : ""}${diff})`);
  }

  // Critical alerts
  const curAlerts = (currentData["health"] as Record<string, unknown>)?.["critical_alerts"] as Array<{ title?: string }> | undefined;
  const prevAlerts = (prevData["health"] as Record<string, unknown>)?.["critical_alerts"] as Array<{ title?: string }> | undefined;
  const curTitles = new Set((curAlerts ?? []).map((a) => a.title).filter(Boolean));
  const prevTitles = new Set((prevAlerts ?? []).map((a) => a.title).filter(Boolean));
  for (const t of curTitles) { if (!prevTitles.has(t)) changes.push(`Critical alert ใหม่: "${t}"`); }
  for (const t of prevTitles) { if (!curTitles.has(t)) changes.push(`Critical alert หายไป: "${t}"`); }

  // SLA uptime
  const curUp = (currentData["sla"] as Record<string, unknown>)?.["uptime_percent"] as number | null;
  const prevUp = (prevData["sla"] as Record<string, unknown>)?.["uptime_percent"] as number | null;
  if (curUp !== null && prevUp !== null && curUp !== prevUp) {
    changes.push(`SLA uptime เปลี่ยนจาก ${prevUp}% เป็น ${curUp}%`);
  }

  // Ticket count
  const curTickets = (currentData["tickets"] as Record<string, unknown>)?.["incident_count"] as number | undefined;
  const prevTickets = (prevData["tickets"] as Record<string, unknown>)?.["incident_count"] as number | undefined;
  const curSR = (currentData["tickets"] as Record<string, unknown>)?.["service_request_count"] as number | undefined;
  const prevSR = (prevData["tickets"] as Record<string, unknown>)?.["service_request_count"] as number | undefined;
  const curTotal = (curTickets ?? 0) + (curSR ?? 0);
  const prevTotal = (prevTickets ?? 0) + (prevSR ?? 0);
  if (curTotal !== prevTotal) {
    changes.push(`จำนวน ticket เปลี่ยนจาก ${prevTotal} เป็น ${curTotal}`);
  }

  // License expiry: newly expiring within 30 days
  const today = new Date();
  const thirtyDaysMs = 30 * 24 * 60 * 60 * 1000;
  function checkLicenses(key: string, label: string) {
    const curLic = (currentData["software"] as Record<string, unknown>)?.[key] as Array<{ name?: string; expire?: string }> | undefined;
    const prevLic = (prevData["software"] as Record<string, unknown>)?.[key] as Array<{ name?: string; expire?: string }> | undefined;
    const prevExpiring = new Set((prevLic ?? []).filter((l) => l.expire).map((l) => l.name));
    for (const l of curLic ?? []) {
      if (!l.expire || !l.name) continue;
      const d = new Date(l.expire);
      const diffMs = d.getTime() - today.getTime();
      if (diffMs <= thirtyDaysMs && diffMs > -thirtyDaysMs && !prevExpiring.has(l.name)) {
        changes.push(`${label} "${l.name}" ${diffMs < 0 ? "หมดอายุแล้ว" : `จะหมดอายุใน ${Math.ceil(diffMs / (24 * 60 * 60 * 1000))} วัน`}`);
      }
    }
  }
  checkLicenses("os_licenses", "OS License");
  checkLicenses("office_licenses", "Office License");

  return changes;
}

// ---------------------------------------------------------------------------
// Route helpers
// ---------------------------------------------------------------------------

/** List month data files (YYYY-MM.yaml only) in a client directory.
 *  Helper files (profile.yaml, history.yaml, ...) are excluded so the UI's
 *  month picker — and carry-forward/changelog prev-month lookup — only ever
 *  see real monthly reports (mirrors find_previous_month in generate.py). */
function listClientMonths(clientCode: string): string[] {
  const dir = clientDir(clientCode);
  if (!existsSync(dir)) return [];
  const monthFile = /^\d{4}-\d{2}\.yaml$/;
  return readdirSync(dir)
    .filter((f) => monthFile.test(f))
    .sort()
    .reverse();
}

/** Find the latest month file sorting before the given file. Works for
 *  files that don't exist yet (new-month carry-forward) as well as existing
 *  ones (changelog). The old indexOf() version returned null for any
 *  not-yet-created file, so carry-forward never ran. */
function findPreviousMonth(clientCode: string, currentFile: string): string | null {
  const months = listClientMonths(clientCode).sort(); // ascending
  const earlier = months.filter((m) => m < currentFile);
  return earlier.length ? earlier[earlier.length - 1] : null;
}

/**
 * Parse URL to extract client code and optional file param.
 * /api/clients/:client/...[:file]...
 * Returns null if the path doesn't match.
 */
function parseClientPath(pathname: string): { clientCode: string; file?: string; rest: string } | null {
  const m = pathname.match(/^\/api\/clients\/([^/]+)(.*)/);
  if (!m) return null;
  return { clientCode: m[1], rest: m[2] };
}

// ---------------------------------------------------------------------------
// HTTP Server
// ---------------------------------------------------------------------------

const server = Bun.serve({
  port: 8787,
  async fetch(req) {
    const url = new URL(req.url);
    const { pathname } = url;

    // GET /api/schema — raw schema.yaml text, used to build AI-assist prompts
    if (pathname === "/api/schema" && req.method === "GET") {
      return json({ schema: readFileSync(SCHEMA_YAML, "utf-8") });
    }

    // GET /api/clients — list client directories in data/
    if (pathname === "/api/clients" && req.method === "GET") {
      try {
        const entries = readdirSync(DATA_DIR, { withFileTypes: true })
          .filter((d) => d.isDirectory() && !d.name.startsWith(".") && !d.name.startsWith("_"))
          .map((d) => d.name);
        return json({ clients: entries.sort() });
      } catch (e) {
        return json({ error: String(e) }, { status: 400 });
      }
    }

    // POST /api/ai-assist — shell out to zcode or agy
    // NOTE: must stay ABOVE the client-scoped guard below — it is not a
    // /api/clients/... route, so the guard used to 404 it before the
    // handler could ever run (QA-found: the whole "AI ช่วยวิเคราะห์"
    // feature was dead code).
    if (pathname === "/api/ai-assist" && req.method === "POST") {
      try {
        const body = (await req.json()) as { tool: "zcode" | "agy"; prompt: string };
        if (!body.prompt || body.prompt.trim().length === 0) {
          return json({ error: "prompt is empty" }, { status: 400 });
        }
        let result;
        if (body.tool === "zcode") {
          result = await runCommand(
            "zcode",
            ["-p", body.prompt, "--cwd", REPORT_ROOT, "--disallowedTools", "Edit Write"],
            { timeoutMs: 5 * 60 * 1000 },
          );
        } else if (body.tool === "agy") {
          result = await runCommand("agy", ["-p", body.prompt, "--mode", "plan"], {
            timeoutMs: 5 * 60 * 1000,
          });
        } else {
          return json({ error: "tool must be zcode or agy" }, { status: 400 });
        }
        if (result.code !== 0 && !result.stdout) {
          return json({ error: result.stderr || `${body.tool} exited ${result.code}` }, { status: 500 });
        }
        return json({ ok: true, output: result.stdout });
      } catch (e) {
        return json({ error: String(e) }, { status: 400 });
      }
    }

    // ----- Client-scoped routes -----

    const parsed = parseClientPath(pathname);
    if (!parsed) return json({ error: "not found" }, { status: 404 });
    const clientCode = safeClientCode(parsed.clientCode);
    const cDir = clientDir(clientCode);

    // GET /api/clients/:client/profile
    if (parsed.rest === "/profile" && req.method === "GET") {
      try {
        const profilePath = join(cDir, "profile.yaml");
        if (!existsSync(profilePath)) return json({ error: "profile not found" }, { status: 404 });
        const data = yaml.load(readFileSync(profilePath, "utf-8"));
        return json({ data });
      } catch (e) {
        return json({ error: String(e) }, { status: 400 });
      }
    }

    // POST /api/clients/:client/profile
    if (parsed.rest === "/profile" && req.method === "POST") {
      try {
        if (!existsSync(cDir)) mkdirSync(cDir, { recursive: true });
        const body = await req.json();
        writeFileSync(join(cDir, "profile.yaml"), yaml.dump(body, { lineWidth: 100 }), "utf-8");
        return json({ ok: true });
      } catch (e) {
        return json({ error: String(e) }, { status: 400 });
      }
    }

    // GET /api/clients/:client/months
    if (parsed.rest === "/months" && req.method === "GET") {
      return json({ files: listClientMonths(clientCode) });
    }

    // GET /api/clients/:client/data/:file
    const dataMatch = parsed.rest.match(/^\/data\/(.+)$/);
    if (dataMatch && req.method === "GET") {
      try {
        const file = safeFileName(dataMatch[1]);
        const full = join(cDir, file);
        if (!existsSync(full)) return json({ error: "not found" }, { status: 404 });
        const data = yaml.load(readFileSync(full, "utf-8"));
        return json({ data });
      } catch (e) {
        return json({ error: String(e) }, { status: 400 });
      }
    }

    // POST /api/clients/:client/data/:file — write a data file
    if (dataMatch && req.method === "POST") {
      try {
        const file = safeFileName(dataMatch[1]);
        if (file === "profile.yaml") return json({ error: "use /profile endpoint" }, { status: 400 });
        if (!existsSync(cDir)) mkdirSync(cDir, { recursive: true });
        const body = await req.json();
        writeFileSync(join(cDir, file), yaml.dump(body, { lineWidth: 100 }), "utf-8");
        return json({ ok: true });
      } catch (e) {
        return json({ error: String(e) }, { status: 400 });
      }
    }

    // POST /api/clients/:client/new-month — create new month with carry-forward
    const newMonthMatch = parsed.rest.match(/^\/new-month$/);
    if (newMonthMatch && req.method === "POST") {
      try {
        if (!existsSync(cDir)) mkdirSync(cDir, { recursive: true });
        const body = (await req.json()) as { file: string; month: string; year: number };
        const file = safeFileName(body.file);
        if (file === "profile.yaml") return json({ error: "cannot use profile.yaml" }, { status: 400 });
        if (!/^\d{4}-(0[1-9]|1[0-2])\.yaml$/.test(file)) {
          return json({ error: "file ต้องเป็น YYYY-MM.yaml เช่น 2026-08.yaml" }, { status: 400 });
        }
        const full = join(cDir, file);
        if (existsSync(full)) return json({ error: "file already exists" }, { status: 409 });

        // Find previous month for carry-forward
        let prevData: ReportData | null = null;
        let prevMonth: string | undefined;
        const prevFile = findPreviousMonth(clientCode, file);
        if (prevFile) {
          prevMonth = prevFile;
          const prevFull = join(cDir, prevFile);
          if (existsSync(prevFull)) {
            prevData = yaml.load(readFileSync(prevFull, "utf-8")) as ReportData | null;
          }
        }

        const result = carryForward(prevData, body.month, body.year);
        writeFileSync(full, yaml.dump(result.data, { lineWidth: 100 }), "utf-8");
        return json({ ok: true, data: result.data, carried: result.carried, prevMonth: prevMonth });
      } catch (e) {
        return json({ error: String(e) }, { status: 400 });
      }
    }

    // POST /api/clients/:client/generate/:file — run generate.py --docx
    const genMatch = parsed.rest.match(/^\/generate\/(.+)$/);
    if (genMatch && req.method === "POST") {
      try {
        const file = safeFileName(genMatch[1]);
        const full = join(cDir, file);
        if (!existsSync(full)) return json({ error: "not found" }, { status: 404 });
        const relPath = join("data", clientCode, file);
        const result = await runCommand(VENV_PYTHON, ["generate.py", relPath, "--docx"], {
          timeoutMs: 60_000,
        });
        if (result.code !== 0) return json({ error: result.stderr || "generate.py failed" }, { status: 500 });
        return json({
          ok: true,
          md: file.replace(/\.yaml$/, ".md"),
          docx: file.replace(/\.yaml$/, ".docx"),
          stdout: result.stdout,
        });
      } catch (e) {
        return json({ error: String(e) }, { status: 400 });
      }
    }

    // GET /api/clients/:client/report/:file(.md) — read rendered markdown
    const reportMatch = parsed.rest.match(/^\/report\/(.+)$/);
    if (reportMatch && req.method === "GET") {
      try {
        const file = reportMatch[1].replace(/[^a-zA-Z0-9._-]/g, "");
        const full = join(cDir, file);
        if (!existsSync(full)) return json({ error: "not found — generate first" }, { status: 404 });
        return json({ markdown: readFileSync(full, "utf-8") });
      } catch (e) {
        return json({ error: String(e) }, { status: 400 });
      }
    }

    // GET /api/clients/:client/changelog/:file — compute changelog vs previous month
    const changelogMatch = parsed.rest.match(/^\/changelog\/(.+)$/);
    if (changelogMatch && req.method === "GET") {
      try {
        const file = safeFileName(changelogMatch[1]);
        const full = join(cDir, file);
        if (!existsSync(full)) return json({ error: "not found" }, { status: 404 });

        const prevFile = findPreviousMonth(clientCode, file);
        if (!prevFile) return json({ changelog: [], prevMonth: null });

        const prevFull = join(cDir, prevFile);
        if (!existsSync(prevFull)) return json({ changelog: [], prevMonth: null });

        const curData = yaml.load(readFileSync(full, "utf-8")) as ReportData;
        const prevData = yaml.load(readFileSync(prevFull, "utf-8")) as ReportData;
        return json({ changelog: buildChangelog(curData, prevData), prevMonth: prevFile });
      } catch (e) {
        return json({ error: String(e) }, { status: 400 });
      }
    }

    return json({ error: "not found" }, { status: 404 });
  },
});

console.log(`IT report dashboard API listening on http://localhost:${server.port}`);
