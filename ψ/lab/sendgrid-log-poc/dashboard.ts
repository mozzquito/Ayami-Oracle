import type { Database } from "bun:sqlite";

function escapeHtml(s: string) {
  return s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]!));
}

export function renderDashboard(db: Database): string {
  const totals = db.query("SELECT COUNT(*) as n FROM events").get() as { n: number };
  const recipients = db.query("SELECT COUNT(DISTINCT email) as n FROM events").get() as { n: number };
  const messages = db.query("SELECT COUNT(DISTINCT sg_message_id) as n FROM events").get() as { n: number };

  const byEvent = db
    .query("SELECT event, COUNT(*) as n FROM events GROUP BY event ORDER BY n DESC")
    .all() as { event: string; n: number }[];
  const maxN = Math.max(...byEvent.map((r) => r.n), 1);

  const reasons = db
    .query(
      "SELECT event, reason, COUNT(*) as n FROM events WHERE reason IS NOT NULL AND reason != '' GROUP BY event, reason ORDER BY n DESC LIMIT 15"
    )
    .all() as { event: string; reason: string; n: number }[];

  const recent = db
    .query(
      "SELECT email, event, datetime(ts,'unixepoch') as when_utc, reason, source FROM events ORDER BY ts DESC LIMIT 30"
    )
    .all() as { email: string; event: string; when_utc: string; reason: string | null; source: string }[];

  const delivered = byEvent.find((r) => r.event === "delivered")?.n ?? 0;
  const processed = byEvent.find((r) => r.event === "processed")?.n ?? 0;
  const deliveryRate = processed > 0 ? ((delivered / processed) * 100).toFixed(1) : "—";

  const eventBars = byEvent
    .map(
      (r) => `
      <div class="bar-row">
        <span class="bar-label">${escapeHtml(r.event)}</span>
        <div class="bar-track"><div class="bar-fill" style="width:${(r.n / maxN) * 100}%"></div></div>
        <span class="bar-n">${r.n}</span>
      </div>`
    )
    .join("");

  const reasonRows = reasons
    .map(
      (r) => `<tr><td><span class="pill warn">${escapeHtml(r.event)}</span></td><td>${escapeHtml(r.reason)}</td><td>${r.n}</td></tr>`
    )
    .join("");

  const recentRows = recent
    .map(
      (r) => `<tr>
        <td class="time">${r.when_utc}</td>
        <td class="mono">${escapeHtml(r.email)}</td>
        <td><span class="pill ${["open", "click", "group_resubscribe"].includes(r.event) ? "good" : ["bounce", "dropped", "spamreport", "unsubscribe", "group_unsubscribe"].includes(r.event) ? "warn" : "neutral"}">${escapeHtml(r.event)}</span></td>
        <td class="mono muted">${r.reason ? escapeHtml(r.reason) : ""}</td>
        <td class="muted">${escapeHtml(r.source)}</td>
      </tr>`
    )
    .join("");

  return `<!doctype html>
<html lang="th">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>sendgrid-log-poc dashboard</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Serif+Thai:wght@600;700&family=IBM+Plex+Sans+Thai:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
  :root {
    --bg: #EEF2F1; --surface: #fff; --surface-sunken: #E4EAE8;
    --text: #1B2320; --text-muted: #55625D;
    --accent: #1F6F6B; --accent-strong: #154E4B; --accent-soft: #D9EBE9;
    --warn: #B2611B; --warn-soft: #F5E3D0; --neutral-soft: #E7EAE9;
    --border: #D3DBD8;
  }
  @media (prefers-color-scheme: dark) {
    :root { --bg:#10161A; --surface:#182027; --surface-sunken:#0D1215; --text:#E6ECEA; --text-muted:#93A6A1;
      --accent:#4FD1C7; --accent-strong:#7EE4DA; --accent-soft:#1D3A38; --warn:#E3A15C; --warn-soft:#3A2A18;
      --neutral-soft:#232C31; --border:#29343A; }
  }
  * { box-sizing: border-box; }
  body { background: var(--bg); color: var(--text); font-family: "IBM Plex Sans Thai", sans-serif; margin: 0; padding: 32px 20px 60px; }
  .wrap { max-width: 980px; margin: 0 auto; }
  h1 { font-family: "Noto Serif Thai", serif; font-size: 26px; margin: 0 0 4px; }
  .sub { color: var(--text-muted); font-size: 13.5px; margin: 0 0 28px; font-family: "IBM Plex Mono", monospace; }
  h2 { font-family: "Noto Serif Thai", serif; font-size: 18px; margin: 36px 0 12px; }
  .stat-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px,1fr)); gap: 12px; }
  .stat { background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 14px 16px; }
  .stat .n { font-family: "IBM Plex Mono", monospace; font-size: 24px; font-weight: 500; color: var(--accent-strong); display: block; }
  .stat .l { font-size: 11.5px; color: var(--text-muted); text-transform: uppercase; letter-spacing: .05em; }
  .card { background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 18px 20px; }
  .bar-row { display: grid; grid-template-columns: 130px 1fr 40px; align-items: center; gap: 10px; font-size: 13px; margin-bottom: 8px; font-family: "IBM Plex Mono", monospace; }
  .bar-track { background: var(--surface-sunken); border-radius: 4px; height: 10px; overflow: hidden; }
  .bar-fill { background: var(--accent); height: 100%; }
  .bar-n { text-align: right; color: var(--text-muted); }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th, td { text-align: left; padding: 7px 10px; border-bottom: 1px solid var(--border); }
  th { font-family: "IBM Plex Mono", monospace; font-size: 10.5px; text-transform: uppercase; color: var(--text-muted); font-weight: 500; }
  .mono { font-family: "IBM Plex Mono", monospace; }
  .muted { color: var(--text-muted); }
  .time { font-family: "IBM Plex Mono", monospace; color: var(--text-muted); white-space: nowrap; }
  .table-wrap { overflow-x: auto; }
  .pill { display: inline-block; font-family: "IBM Plex Mono", monospace; font-size: 11px; padding: 1px 8px; border-radius: 999px; }
  .pill.neutral { background: var(--neutral-soft); color: var(--text-muted); }
  .pill.good { background: var(--accent-soft); color: var(--accent-strong); }
  .pill.warn { background: var(--warn-soft); color: var(--warn); }
  .refresh { font-size: 12px; color: var(--text-muted); }
  a { color: var(--accent-strong); }
</style>
</head>
<body>
<div class="wrap">
  <h1>sendgrid-log-poc</h1>
  <p class="sub">live query จาก events.db · ไม่ auto-refresh · <a href="/dashboard">reload</a></p>

  <div class="stat-row">
    <div class="stat"><span class="n">${totals.n}</span><span class="l">events ทั้งหมด</span></div>
    <div class="stat"><span class="n">${messages.n}</span><span class="l">messages</span></div>
    <div class="stat"><span class="n">${recipients.n}</span><span class="l">recipients</span></div>
    <div class="stat"><span class="n">${deliveryRate}%</span><span class="l">delivered / processed</span></div>
  </div>

  <h2>Event breakdown</h2>
  <div class="card">${eventBars}</div>

  <h2>เหตุผลที่ส่งไม่สำเร็จ (reason)</h2>
  <div class="card table-wrap">
    <table>
      <thead><tr><th>Event</th><th>Reason</th><th>จำนวน</th></tr></thead>
      <tbody>${reasonRows || '<tr><td colspan="3" class="muted">ยังไม่มี event ที่มี reason</td></tr>'}</tbody>
    </table>
  </div>

  <h2>Event ล่าสุด 30 รายการ</h2>
  <div class="card table-wrap">
    <table>
      <thead><tr><th>เวลา (UTC)</th><th>Email</th><th>Event</th><th>Reason</th><th>Source</th></tr></thead>
      <tbody>${recentRows}</tbody>
    </table>
  </div>
</div>
</body>
</html>`;
}
