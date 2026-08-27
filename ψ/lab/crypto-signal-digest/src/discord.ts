import { Client, GatewayIntentBits, Events } from "discord.js";
import { config } from "./config.js";
import type { StoredSignal } from "./store.js";

// One-shot sender pattern, deliberately matching ψ/lab/discord-bot/notify.mjs
// (the existing, already-in-production sender used by market-backtester):
// log in, send, disconnect. Reuses that project's bot token, posting to a
// separate channel so this product's signals don't mix into the same stream
// as market-backtester's own trade notifications.
const DISCORD_MAX_LEN = 2000;

const SENTIMENT_EMOJI: Record<string, string> = {
  positive: "🟢",
  negative: "🔴",
  neutral: "⚪",
};

function formatSignal(s: StoredSignal): string {
  const emoji = SENTIMENT_EMOJI[s.sentiment] ?? "⚪";
  const indicatorLine = s.indicator
    ? `\n   📊 ${s.indicator.symbol} RSI ${s.indicator.rsi.toFixed(1)} (${s.indicator.technicalState})`
    : "";
  const convictionTag = s.convictionLabel === "HIGH CONVICTION" ? " **[HIGH CONVICTION]**" : "";
  return `${emoji} **${s.subject}**${convictionTag}\n   ${s.reason}\n   <${s.url}>${indicatorLine}`;
}

function buildDigest(signals: StoredSignal[]): string {
  const header = `📰 **สรุปสัญญาณ ${signals.length} รายการ** — ${new Date().toLocaleString("th-TH", { timeZone: "Asia/Bangkok" })}\n_ไม่ใช่คำแนะนำการลงทุน — โปรดตรวจสอบก่อนตัดสินใจ_\n`;
  const body = signals.map(formatSignal).join("\n\n");
  const full = `${header}\n${body}`;
  if (full.length <= DISCORD_MAX_LEN) return full;
  return full.slice(0, DISCORD_MAX_LEN - 20) + "\n… (truncated)";
}

export async function sendDigest(signals: StoredSignal[]): Promise<void> {
  if (signals.length === 0) return;
  const client = new Client({ intents: [GatewayIntentBits.Guilds] });
  await new Promise<void>((resolve, reject) => {
    client.once(Events.ClientReady, async () => {
      try {
        const channel = await client.channels.fetch(config.discordChannelId);
        if (!channel?.isTextBased() || !("send" in channel)) {
          throw new Error(`Channel ${config.discordChannelId} is not text-sendable`);
        }
        await channel.send({ content: buildDigest(signals) });
        resolve();
      } catch (err) {
        reject(err);
      } finally {
        client.destroy();
      }
    });
    client.login(config.discordBotToken).catch(reject);
  });
}
