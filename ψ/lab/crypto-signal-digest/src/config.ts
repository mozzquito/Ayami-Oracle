import "dotenv/config";
import type { NewsSource } from "./types.js";

function required(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(
      `Missing ${name} in .env — run scripts/setup-wizard.sh to fill it in.`
    );
  }
  return value;
}

export const config = {
  openrouterApiKey: required("OPENROUTER_API_KEY"),
  firecrawlApiKey: required("FIRECRAWL_API_KEY"),
  taapiSecret: required("TAAPI_SECRET"),
  discordBotToken: required("DISCORD_BOT_TOKEN"),
  discordChannelId: required("DISCORD_CHANNEL_ID"),
  // NEWSAPI_KEY intentionally not required — live-tested 2026-08-27 and found
  // to have zero coverage of Thai financial sources (kaohoon.com, set.or.th,
  // moneychannel.co.th all returned 0 articles). Kept as an optional future
  // supplementary source for English-language crypto news, not load-bearing.
  newsapiKey: process.env.NEWSAPI_KEY,
};

// Verified live 2026-08-27 via Firecrawl — these return real, current headlines.
// Two sources from the original plan were dropped after live testing:
//   - moneychannel.co.th: doesn't resolve at all — turns out the station shut
//     down entirely (real news, not a broken link: search "Money Channel
//     ประกาศปิดสถานี"), replaced with Thairath Money below.
//   - set.or.th/th/market/news-and-alert/news: loads as a JS-rendered SPA:
//     Firecrawl's basic scrape only captured the page shell (nav, ticker
//     widgets), not the actual news list. Would need Firecrawl's JS-wait
//     options or a different approach — not attempted yet, see README.
export const NEWS_SOURCES: NewsSource[] = [
  { name: "Kaohoon", url: "https://www.kaohoon.com/" },
  { name: "ThairathMoney", url: "https://www.thairath.co.th/money" },
];

// Crypto pairs to enrich sentiment with technical-indicator alignment.
// Kept small for the prototype — expand once the sentiment step proves useful.
export const WATCHED_SYMBOLS = ["BTC/USDT", "ETH/USDT"];
