import { join } from "path";
import { Database } from "bun:sqlite";
import { EventWebhook, EventWebhookHeader } from "@sendgrid/eventwebhook";
import { renderDashboard } from "./dashboard";

// absolute path — running this from a different cwd must never silently
// create/open a second, separate events.db
const db = new Database(join(import.meta.dir, "events.db"));
db.run("PRAGMA journal_mode = WAL");
db.run(`
  CREATE TABLE IF NOT EXISTS events (
    sg_event_id   TEXT PRIMARY KEY,
    sg_message_id TEXT,
    email         TEXT,
    event         TEXT,
    ts            INTEGER,
    raw           TEXT,
    source        TEXT DEFAULT 'webhook',
    reason        TEXT,
    ip            TEXT,
    useragent     TEXT,
    url           TEXT
  )
`);

const publicKeyEnv = process.env.SENDGRID_WEBHOOK_PUBLIC_KEY;
if (!publicKeyEnv) {
  throw new Error("SENDGRID_WEBHOOK_PUBLIC_KEY is not set — copy it from SendGrid → Settings → Mail Settings → Event Webhook");
}

const ew = new EventWebhook();
const publicKey = ew.convertPublicKeyToECDSA(publicKeyEnv);

const insert = db.prepare(`
  INSERT OR IGNORE INTO events
    (sg_event_id, sg_message_id, email, event, ts, raw, reason, ip, useragent, url)
  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
`);

const port = Number(process.env.PORT ?? 4000);

Bun.serve({
  port,
  async fetch(req) {
    if (req.method !== "POST") {
      return new Response("not found", { status: 404 });
    }

    const rawBody = await req.text();
    const signature = req.headers.get(EventWebhookHeader.SIGNATURE());
    const timestamp = req.headers.get(EventWebhookHeader.TIMESTAMP());

    let isValid = false;
    try {
      isValid = !!(signature && timestamp && ew.verifySignature(publicKey, rawBody, signature, timestamp));
    } catch {
      isValid = false; // malformed signature/timestamp header — treat as unverified, not a crash
    }

    if (!isValid) {
      return new Response("invalid signature", { status: 401 });
    }

    // signature alone doesn't prevent replay — reject stale timestamps per SendGrid's own guidance
    const ageSeconds = Math.abs(Date.now() / 1000 - Number(timestamp));
    if (ageSeconds > 180) {
      return new Response("stale timestamp", { status: 401 });
    }

    let events: any[];
    try {
      events = JSON.parse(rawBody);
    } catch {
      return new Response("invalid JSON body", { status: 400 });
    }

    for (const e of events) {
      insert.run(
        e.sg_event_id,
        e.sg_message_id,
        e.email,
        e.event,
        e.timestamp,
        JSON.stringify(e),
        e.reason ?? null,
        e.ip ?? null,
        e.useragent ?? null,
        e.url ?? null
      );
    }

    console.log(`stored ${events.length} event(s)`);
    return new Response("ok");
  },
});

console.log(`listening on :${port}`);

// separate port, NOT tunneled by ngrok — dashboard shows real emails/IPs,
// keep it local-only rather than reachable from the public webhook URL
const dashboardPort = Number(process.env.DASHBOARD_PORT ?? 4001);

Bun.serve({
  port: dashboardPort,
  hostname: "127.0.0.1",
  fetch(req) {
    const { pathname } = new URL(req.url);
    if (pathname !== "/dashboard" && pathname !== "/") {
      return new Response("not found", { status: 404 });
    }
    return new Response(renderDashboard(db), { headers: { "Content-Type": "text/html; charset=utf-8" } });
  },
});

console.log(`dashboard on http://127.0.0.1:${dashboardPort}/dashboard (local only)`);
