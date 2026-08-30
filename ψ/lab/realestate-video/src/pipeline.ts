#!/usr/bin/env node
import { Command } from "commander";
import { loadConfig } from "./config.js";
import { enhancePhotos } from "./enhance.js";
import { writeScript } from "./script.js";
import { generateVoiceover, DEFAULT_THAI_VOICE } from "./voiceover.js";
import { renderVideo } from "./render.js";
import type { PropertyInput } from "./types.js";

const cfg = loadConfig();

const program = new Command();

program
  .name("realestate-video")
  .description("Photos + property details -> Thai-narrated vertical listing video")
  .requiredOption("--photos <urls>", "comma-separated public photo URLs")
  .requiredOption("--price <price>", 'e.g. "3.5 ล้านบาท"')
  .requiredOption("--location <location>", 'e.g. "ทองหล่อ กรุงเทพ"')
  .requiredOption("--agent-name <name>")
  .requiredOption("--agent-phone <phone>")
  .option("--bts <station>")
  .option("--sqm <sqm>")
  .option("--bedrooms <n>")
  .option("--highlights <text>", "extra selling points, freeform")
  .option("--voice <voice>", "SpeechGen Thai voice name", DEFAULT_THAI_VOICE)
  .option("--skip-enhance", "skip fal.ai photo enhancement (use original photos as-is)", false);

program.parse();
const opts = program.opts();

const input: PropertyInput = {
  photoUrls: (opts.photos as string).split(",").map((s) => s.trim()).filter(Boolean),
  price: opts.price,
  location: opts.location,
  btsStation: opts.bts,
  sqm: opts.sqm,
  bedrooms: opts.bedrooms,
  extraHighlights: opts.highlights,
  agentName: opts.agentName,
  agentPhone: opts.agentPhone,
};

async function main() {
  console.log(`▸ 1/4 enhancing ${input.photoUrls.length} photo(s)...`);
  const photos = opts.skipEnhance
    ? input.photoUrls.map((originalUrl) => ({ originalUrl, enhancedUrl: originalUrl, fellBackToOriginal: true }))
    : await enhancePhotos(input.photoUrls, cfg);
  const fellBack = photos.filter((p) => p.fellBackToOriginal).length;
  if (fellBack > 0) console.log(`  ⚠ ${fellBack}/${photos.length} photo(s) used original (enhancement skipped or failed)`);

  console.log("▸ 2/4 writing Thai script...");
  const { script, costUsd: scriptCost } = await writeScript(input, cfg);
  console.log(`  script (${script.length} chars, $${scriptCost.toFixed(6)}):\n  ${script.replace(/\n/g, "\n  ")}`);

  console.log("▸ 3/4 generating Thai voiceover...");
  const voiceover = await generateVoiceover(script, opts.voice, cfg);
  console.log(`  audio: ${voiceover.audioUrl} (${voiceover.durationSec}s)`);

  console.log("▸ 4/4 rendering video...");
  const result = await renderVideo(photos, voiceover, input.agentName, input.agentPhone, cfg);
  console.log(`\n✓ done: ${result.videoUrl}`);
  console.log(`  ${result.widthPx}x${result.heightPx}, ${(result.fileSizeBytes / 1024).toFixed(0)}KB`);
  if (result.widthPx < 1080) {
    console.log(`  ⚠ output is below the requested 1080px width — check your Creatomate plan/render_scale`);
  }
}

main().catch((err) => {
  console.error(`\n✗ pipeline failed: ${(err as Error).message}`);
  process.exit(1);
});
