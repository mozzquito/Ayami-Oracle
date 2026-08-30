import { join } from "path";
import { Database } from "bun:sqlite";

const apiKey = process.env.SENDGRID_API_KEY;
if (!apiKey) {
  throw new Error("SENDGRID_API_KEY is not set — check .env");
}

// absolute path — must always hit the same DB file regardless of cwd
const db = new Database(join(import.meta.dir, "events.db"));
db.run("PRAGMA journal_mode = WAL");

// source column tells webhook rows (real-time) apart from reconcile rows (daily catch-up)
try {
  db.run("ALTER TABLE events ADD COLUMN source TEXT DEFAULT 'webhook'");
} catch (err) {
  const msg = err instanceof Error ? err.message : String(err);
  if (!msg.includes("duplicate column name")) {
    throw err; // a real failure (locked DB, disk full, etc.) — don't hide it
  }
}

const insert = db.prepare(`
  INSERT OR IGNORE INTO events
    (sg_event_id, sg_message_id, email, event, ts, raw, source, reason)
  VALUES (?, ?, ?, ?, ?, ?, 'reconcile', ?)
`);

const existsStmt = db.prepare(
  "SELECT 1 FROM events WHERE sg_message_id = ? AND event = ? LIMIT 1"
);

// default window: yesterday 00:00 UTC → today 00:00 UTC
function isoDate(d: Date) {
  return d.toISOString().slice(0, 10);
}

const now = new Date();
const yesterday = new Date(now);
yesterday.setUTCDate(now.getUTCDate() - 1);

const sinceArg = process.argv[2] ?? isoDate(yesterday);
const untilArg = process.argv[3] ?? isoDate(now);

console.log(`reconciling window: ${sinceArg}T00:00:00Z → ${untilArg}T00:00:00Z`);

// walk hour by hour so each request stays well under the 1000-result limit
// even at ~15,000 emails/day (~625/hour average)
const start = new Date(`${sinceArg}T00:00:00Z`);
const end = new Date(`${untilArg}T00:00:00Z`);

let checked = 0;
let added = 0;
let apiCalls = 0;

for (let t = new Date(start); t < end; t.setUTCHours(t.getUTCHours() + 1)) {
  const hourStart = new Date(t);
  const hourEnd = new Date(t);
  hourEnd.setUTCHours(hourEnd.getUTCHours() + 1);

  const query = `last_event_time > TIMESTAMP "${hourStart.toISOString()}" AND last_event_time < TIMESTAMP "${hourEnd.toISOString()}"`;
  const url = `https://api.sendgrid.com/v3/messages?limit=1000&query=${encodeURIComponent(query)}`;

  let res = await fetch(url, { headers: { Authorization: `Bearer ${apiKey}` } });
  apiCalls++;

  // back off and retry on rate limit — this is a daily batch job, latency doesn't matter
  let retries = 0;
  while (res.status === 429 && retries < 5) {
    const wait = 2000 * 2 ** retries;
    console.log(`  [${hourStart.toISOString()}] rate limited, retrying in ${wait}ms`);
    await new Promise((r) => setTimeout(r, wait));
    res = await fetch(url, { headers: { Authorization: `Bearer ${apiKey}` } });
    apiCalls++;
    retries++;
  }

  if (res.status !== 200) {
    console.log(`  [${hourStart.toISOString()}] API error ${res.status}: ${await res.text()}`);
    await new Promise((r) => setTimeout(r, 1000));
    continue;
  }

  const body = (await res.json()) as { messages: Array<Record<string, any>> };
  const messages = body.messages ?? [];
  if (messages.length === 0) continue;

  console.log(`  [${hourStart.toISOString()}] ${messages.length} message(s) from API`);

  for (const m of messages) {
    checked++;
    const msgId: string = m.msg_id;
    const status: string = m.status; // processed/delivered/deferred/dropped/bounced/blocked
    const toEmail: string = m.to_email;
    const lastEventTs = Math.floor(new Date(m.last_event_time).getTime() / 1000);

    if (existsStmt.get(msgId, status)) continue; // webhook already has this exact status logged

    const syntheticId = `reconcile-${msgId}-${status}`;
    insert.run(syntheticId, msgId, toEmail, status, lastEventTs, JSON.stringify(m), m.reason ?? null);
    added++;
  }

  // gentle pacing — avoid hammering the API across a full day's worth of hourly requests
  await new Promise((r) => setTimeout(r, 1000));
}

console.log(`done. api_calls=${apiCalls} checked=${checked} added_by_reconcile=${added}`);
