#!/usr/bin/env node
import { Command } from "commander";
import { fetchAllHeadlines } from "./news.js";
import { classifySentiment } from "./sentiment.js";
import { getAllWatchedIndicators } from "./indicators.js";
import { saveSignal, getUnsentSignals, markSent } from "./store.js";
import { sendDigest } from "./discord.js";
import type { ConvictionLabel, Signal } from "./types.js";
import { WATCHED_SYMBOLS } from "./config.js";

const program = new Command();
program
  .name("crypto-signal-digest")
  .description("One poll cycle: scrape Thai finance headlines -> sentiment -> indicator alignment -> Discord digest")
  .option("--dry-run", "print signals instead of sending to Discord", false)
  .option("--limit <n>", "max headlines to classify per run", "20");
program.parse();
const opts = program.opts();

// A crypto-mentioning headline gets checked against BTC/ETH indicators for
// alignment; anything else is sentiment-only. Deliberately simple keyword
// match for the prototype — a real version would map subject -> symbol more
// carefully instead of a blanket "does the title mention crypto" check.
function relevantSymbol(title: string): string | null {
  const lower = title.toLowerCase();
  if (lower.includes("bitcoin") || lower.includes("บิทคอยน์") || lower.includes("btc")) return "BTC/USDT";
  if (lower.includes("ethereum") || lower.includes("อีเธอเรียม") || lower.includes("eth")) return "ETH/USDT";
  return null;
}

function conviction(sentiment: string, technicalState: string | undefined): ConvictionLabel {
  if (sentiment === "positive" && technicalState === "oversold") return "HIGH CONVICTION";
  if (sentiment === "negative" && technicalState === "overbought") return "HIGH CONVICTION";
  return "sentiment only";
}

async function main() {
  console.log("▸ 1/4 fetching Thai financial headlines...");
  const headlines = await fetchAllHeadlines();
  const limited = headlines.slice(0, Number(opts.limit));
  console.log(`  found ${headlines.length} headlines (classifying ${limited.length})`);
  if (limited.length === 0) {
    console.log("no headlines to process, exiting");
    return;
  }

  console.log("▸ 2/4 classifying sentiment...");
  const classified = await classifySentiment(limited);
  console.log(`  classified ${classified.length} items`);

  console.log(`▸ 3/4 checking indicator alignment (${WATCHED_SYMBOLS.join(", ")})...`);
  const indicators = await getAllWatchedIndicators();

  const signals: Signal[] = classified.map((c) => {
    const symbol = relevantSymbol(c.title);
    const indicator = symbol ? indicators.get(symbol) ?? null : null;
    return {
      ...c,
      indicator,
      convictionLabel: conviction(c.sentiment, indicator?.technicalState),
    };
  });

  let newCount = 0;
  for (const signal of signals) {
    if (saveSignal(signal)) newCount++;
  }
  console.log(`  ${newCount} new signal(s) saved (${signals.length - newCount} already seen)`);

  console.log("▸ 4/4 sending digest...");
  const unsent = getUnsentSignals(10);
  if (unsent.length === 0) {
    console.log("  nothing new to send");
    return;
  }
  if (opts.dryRun) {
    console.log(`  [dry-run] would send ${unsent.length} signal(s):`);
    for (const s of unsent) {
      console.log(`  - [${s.sentiment}] ${s.subject}: ${s.reason}${s.convictionLabel === "HIGH CONVICTION" ? " ⚡ HIGH CONVICTION" : ""}`);
    }
  } else {
    await sendDigest(unsent);
    markSent(unsent.map((s) => s.id));
    console.log(`  ✓ sent ${unsent.length} signal(s) to Discord`);
  }
}

main().catch((err) => {
  console.error(`\n✗ pipeline failed: ${(err as Error).message}`);
  process.exit(1);
});
