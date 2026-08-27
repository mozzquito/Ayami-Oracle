import { config } from "./config.js";
import type { NewsItem, Sentiment, SentimentResult } from "./types.js";

const OPENROUTER_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions";
const MODEL = "deepseek/deepseek-chat";

interface OpenRouterResponse {
  choices: { message: { content: string } }[];
}

interface RawClassification {
  index: number;
  subject: string;
  sentiment: Sentiment;
  reason: string;
}

function buildPrompt(items: NewsItem[]): string {
  const list = items.map((item, i) => `${i}. ${item.title}`).join("\n");
  return [
    "คุณคือนักวิเคราะห์ข่าวการเงิน วิเคราะห์หัวข้อข่าวต่อไปนี้ทีละข้อ",
    "สำหรับแต่ละข้อ ระบุ: บริษัท/เซกเตอร์/สินทรัพย์ที่พูดถึง (subject), sentiment (positive/negative/neutral),",
    "และเหตุผล 1 ประโยคสั้นๆ เป็นภาษาไทย (reason)",
    "",
    "ระวังสำนวนปฏิเสธซ้อน เช่น \"ขาดทุนลดลง\" คือ positive (ฟื้นตัว) ไม่ใช่ negative",
    "",
    "หัวข้อข่าว:",
    list,
    "",
    "ตอบเป็น JSON array เท่านั้น ไม่มีคำนำ ไม่มี markdown code fence รูปแบบ:",
    '[{"index":0,"subject":"...","sentiment":"positive","reason":"..."}]',
  ].join("\n");
}

function extractJson(raw: string): string {
  const fenced = raw.match(/```(?:json)?\s*([\s\S]*?)```/);
  if (fenced) return fenced[1].trim();
  const start = raw.indexOf("[");
  const end = raw.lastIndexOf("]");
  if (start !== -1 && end !== -1 && end > start) return raw.slice(start, end + 1);
  return raw.trim();
}

export async function classifySentiment(items: NewsItem[]): Promise<SentimentResult[]> {
  if (items.length === 0) return [];
  const res = await fetch(OPENROUTER_ENDPOINT, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${config.openrouterApiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: MODEL,
      messages: [{ role: "user", content: buildPrompt(items) }],
    }),
  });
  if (!res.ok) throw new Error(`OpenRouter ${res.status}: ${await res.text()}`);
  const data = (await res.json()) as OpenRouterResponse;
  const raw = data.choices[0]?.message.content;
  if (!raw) throw new Error("OpenRouter returned an empty response");

  let parsed: RawClassification[];
  try {
    parsed = JSON.parse(extractJson(raw));
  } catch (err) {
    throw new Error(`Failed to parse sentiment JSON: ${(err as Error).message}\nRaw: ${raw.slice(0, 300)}`);
  }

  return parsed
    .filter((p) => items[p.index])
    .map((p) => ({
      title: items[p.index].title,
      url: items[p.index].url,
      source: items[p.index].source,
      subject: p.subject,
      sentiment: p.sentiment,
      reason: p.reason,
    }));
}
