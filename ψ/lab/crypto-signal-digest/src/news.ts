import { config, NEWS_SOURCES } from "./config.js";
import type { NewsItem, NewsSource } from "./types.js";

// Verified live 2026-08-27: POST https://api.firecrawl.dev/v1/scrape with
// {url, formats:["markdown"], onlyMainContent:true} returns real, current
// Thai financial headlines as markdown link syntax, e.g.
// "[**เปิดโผ 29 หุ้น mai กำไร Q2 โตเกิน 100%**](https://www.kaohoon.com/news/857846)"
const FIRECRAWL_ENDPOINT = "https://api.firecrawl.dev/v1/scrape";

interface FirecrawlResponse {
  success: boolean;
  data?: { markdown?: string };
  error?: string;
}

// Markdown links whose visible text is short/noisy (nav items, "opens in a
// new tab", bare images) are filtered out — a real headline is long enough
// to be a sentence fragment, not a menu label.
const MIN_TITLE_LENGTH = 12;

function extractHeadlines(markdown: string, source: NewsSource): NewsItem[] {
  const linkPattern = /\[\*{0,2}([^\]]+?)\*{0,2}\]\((https?:\/\/[^\s)]+)\)/g;
  const seen = new Set<string>();
  const items: NewsItem[] = [];
  let match: RegExpExecArray | null;
  while ((match = linkPattern.exec(markdown)) !== null) {
    const title = match[1].trim();
    const url = match[2];
    if (title.length < MIN_TITLE_LENGTH) continue;
    if (!url.includes(new URL(source.url).hostname)) continue;
    if (seen.has(url)) continue;
    seen.add(url);
    items.push({ source: source.name, title, url });
  }
  return items;
}

async function fetchOne(source: NewsSource): Promise<NewsItem[]> {
  const res = await fetch(FIRECRAWL_ENDPOINT, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${config.firecrawlApiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ url: source.url, formats: ["markdown"], onlyMainContent: true }),
  });
  if (!res.ok) {
    console.warn(`  ⚠ Firecrawl failed for ${source.name} (${res.status}): ${await res.text()}`);
    return [];
  }
  const data = (await res.json()) as FirecrawlResponse;
  if (!data.success || !data.data?.markdown) {
    console.warn(`  ⚠ Firecrawl returned no content for ${source.name}: ${data.error ?? "unknown"}`);
    return [];
  }
  return extractHeadlines(data.data.markdown, source);
}

export async function fetchAllHeadlines(): Promise<NewsItem[]> {
  const results = await Promise.all(NEWS_SOURCES.map(fetchOne));
  return results.flat();
}
