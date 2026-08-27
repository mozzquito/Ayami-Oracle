import { config } from "./config.js";
import type { PropertyInput } from "./types.js";

// Verified live 2026-08-27: endpoint, auth, model slug, and response shape
// all confirmed with a real Thai-language call (deepseek/deepseek-chat via
// OpenRouter, cost was ~$0.00001 for a 2-token reply).
const OPENROUTER_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions";
const MODEL = "deepseek/deepseek-chat";

interface OpenRouterResponse {
  choices: { message: { content: string } }[];
  usage?: { cost?: number };
}

// Structured fields only (never freeform pasted listing text) — this is the
// mitigation for the "script hallucination" risk zcode's review flagged:
// DeepSeek can't invent a BTS distance or price it was never given.
function buildPrompt(input: PropertyInput): string {
  const lines = [
    `ราคา: ${input.price}`,
    `ทำเล: ${input.location}`,
    input.btsStation ? `ใกล้ BTS: ${input.btsStation}` : null,
    input.sqm ? `พื้นที่: ${input.sqm} ตร.ม.` : null,
    input.bedrooms ? `ห้องนอน: ${input.bedrooms}` : null,
    input.extraHighlights ? `จุดเด่นอื่นๆ: ${input.extraHighlights}` : null,
  ].filter(Boolean);

  return [
    "คุณคือนักเขียนสคริปต์วิดีโอขายอสังหาริมทรัพย์มืออาชีพ เขียนสคริปต์พากย์เสียงภาษาไทย",
    "สำหรับวิดีโอแนวตั้ง 30-45 วินาที จากข้อมูลต่อไปนี้เท่านั้น ห้ามเติมข้อมูลที่ไม่ได้ให้มา:",
    "",
    ...lines,
    "",
    "ข้อกำหนด:",
    "- น้ำเสียงกระชับ น่าสนใจ ไม่โอเวอร์",
    "- ปิดท้ายด้วยการชวนติดต่อ (ไม่ต้องใส่เบอร์โทร จะใส่เป็นข้อความซ้อนทับวิดีโอแยกต่างหาก)",
    "- ห้ามใส่หัวข้อ ป้ายกำกับ เครื่องหมายดอกจัน หรือ markdown ใดๆ ทั้งสิ้น",
    "- ห้ามมีวงเล็บอธิบายฉาก",
    "- ตอบกลับด้วยเนื้อหาสคริปต์ล้วนๆ เริ่มที่ประโยคแรกทันที (ห้ามขึ้นต้นด้วยคำว่า \"สคริปต์\" หรือคำอธิบายใดๆ ก่อนเนื้อหาจริง)",
  ].join("\n");
}

// DeepSeek doesn't reliably follow "no preamble" instructions — caught live
// 2026-08-27 when it prepended a "**สคริปต์พากย์เสียงภาษาไทย...**" header
// despite being told not to. Strip common leftover markdown/header patterns
// as a second line of defense so a stray heading never gets read aloud by
// the TTS step.
function stripPreamble(raw: string): string {
  return raw
    .split("\n")
    .filter((line) => {
      const trimmed = line.trim();
      if (!trimmed) return false;
      // A line that's just a bolded/markdown label (e.g. "**สคริปต์...**")
      if (/^\*{1,2}.*\*{1,2}$/.test(trimmed) && trimmed.length < 80) return false;
      return true;
    })
    .join("\n")
    .replace(/\*\*/g, "")
    .trim();
}

export async function writeScript(input: PropertyInput): Promise<{ script: string; costUsd: number }> {
  const res = await fetch(OPENROUTER_ENDPOINT, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${config.openrouterApiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: MODEL,
      messages: [{ role: "user", content: buildPrompt(input) }],
    }),
  });
  if (!res.ok) {
    throw new Error(`OpenRouter ${res.status}: ${await res.text()}`);
  }
  const data = (await res.json()) as OpenRouterResponse;
  const raw = data.choices[0]?.message.content?.trim();
  if (!raw) throw new Error("OpenRouter returned an empty script");
  const script = stripPreamble(raw);
  if (!script) throw new Error("OpenRouter returned only a stripped preamble, no real script content");
  return { script, costUsd: data.usage?.cost ?? 0 };
}
