import { readFileSync } from "fs";

const apiKey = process.env.SENDGRID_API_KEY;
if (!apiKey) {
  throw new Error("SENDGRID_API_KEY is not set — check .env");
}

const FROM_EMAIL = process.env.FROM_EMAIL ?? "phongcheat.phus@gmail.com";
const DELAY_MS = Number(process.env.SEND_DELAY_MS ?? 300);

const file = process.argv[2];
if (!file) {
  console.error("usage: bun run send-batch.ts <path-to-email-list.txt>");
  process.exit(1);
}

const emails = readFileSync(file, "utf-8")
  .split("\n")
  .map((line) => line.trim())
  .filter(Boolean);

console.log(`sending to ${emails.length} recipient(s) from ${file}, ${DELAY_MS}ms apart`);

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

let sent = 0;
let failed = 0;

for (const [i, to] of emails.entries()) {
  const res = await fetch("https://api.sendgrid.com/v3/mail/send", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      personalizations: [{ to: [{ email: to }] }],
      from: { email: FROM_EMAIL, name: "sendgrid-log-poc" },
      subject: `log poc batch test #${i + 1}`,
      content: [
        {
          type: "text/html",
          value: `ทดสอบ batch #${i + 1} ไปที่ ${to} — <a href="https://claude.ai">คลิกลิงก์นี้เพื่อทดสอบ click event</a>`,
        },
      ],
      tracking_settings: {
        click_tracking: { enable: true },
        open_tracking: { enable: true },
      },
    }),
  });

  if (res.status === 202) {
    sent++;
    console.log(`[${i + 1}/${emails.length}] ok  → ${to}`);
  } else {
    failed++;
    const body = await res.text();
    console.log(`[${i + 1}/${emails.length}] FAIL (${res.status}) → ${to}: ${body}`);
  }

  if (i < emails.length - 1) {
    await sleep(DELAY_MS);
  }
}

console.log(`done. sent=${sent} failed=${failed}`);
