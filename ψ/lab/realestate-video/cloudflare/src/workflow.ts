import { WorkflowEntrypoint, WorkflowStep } from "cloudflare:workers";
import type { WorkflowEvent } from "cloudflare:workers";
import { enhancePhotos } from "../../src/enhance.js";
import { writeScript } from "../../src/script.js";
import { generateVoiceover } from "../../src/voiceover.js";
import { renderVideo } from "../../src/render.js";
import type { PipelineConfig, PropertyInput } from "../../src/types.js";
import type { Env } from "./types.js";

type Params = { jobId: string; input: PropertyInput };

// Not typed as `WorkflowStepConfig` by name — in the installed
// @cloudflare/workers-types version that type is nested inside the
// "cloudflare:pipelines" ambient module, not exported globally or from
// "cloudflare:workers". `as const` lets it structurally satisfy step.do's
// overload instead.
const API_STEP_CONFIG = {
  retries: { limit: 3, delay: "10 seconds", backoff: "exponential" },
} as const;

export class RealEstateVideoWorkflow extends WorkflowEntrypoint<Env, Params> {
  async run(event: WorkflowEvent<Params>, step: WorkflowStep) {
    const { jobId, input } = event.payload;
    const cfg: PipelineConfig = {
      openrouterApiKey: this.env.OPENROUTER_API_KEY,
      falApiKey: this.env.FAL_API_KEY,
      speechgenApiKey: this.env.SPEECHGEN_API_KEY,
      speechgenEmail: this.env.SPEECHGEN_EMAIL,
      creatomateApiKey: this.env.CREATOMATE_API_KEY,
    };

    try {
      const photos = await step.do("enhance-photos", API_STEP_CONFIG, async () => {
        await this.setStatus(jobId, "enhancing");
        return enhancePhotos(input.photoUrls, cfg);
      });

      const { script } = await step.do("write-script", API_STEP_CONFIG, async () => {
        await this.setStatus(jobId, "scripting");
        const result = await writeScript(input, cfg);
        await this.env.DB.prepare(
          "UPDATE jobs SET script = ?, script_cost_usd = ?, updated_at = datetime('now') WHERE id = ?"
        )
          .bind(result.script, result.costUsd, jobId)
          .run();
        return { script: result.script, scriptCostUsd: result.costUsd };
      });

      const voiceover = await step.do("generate-voiceover", API_STEP_CONFIG, async () => {
        await this.setStatus(jobId, "voiceover");
        const result = await generateVoiceover(script, undefined, cfg);
        await this.env.DB.prepare(
          "UPDATE jobs SET audio_url = ?, voiceover_cost_usd = ?, updated_at = datetime('now') WHERE id = ?"
        )
          .bind(result.audioUrl, result.costUsd ?? null, jobId)
          .run();
        return result;
      });

      const rendered = await step.do("render-video", API_STEP_CONFIG, async () => {
        await this.setStatus(jobId, "rendering");
        return renderVideo(photos, voiceover, input.agentName, input.agentPhone, cfg);
      });

      await this.env.DB.prepare(
        "UPDATE jobs SET status = 'done', video_url = ?, updated_at = datetime('now') WHERE id = ?"
      )
        .bind(rendered.videoUrl, jobId)
        .run();

      return rendered;
    } catch (err) {
      await this.env.DB.prepare(
        "UPDATE jobs SET status = 'failed', error = ?, updated_at = datetime('now') WHERE id = ?"
      )
        .bind((err as Error).message, jobId)
        .run();
      throw err;
    }
  }

  private async setStatus(jobId: string, status: string) {
    await this.env.DB.prepare(
      "UPDATE jobs SET status = ?, updated_at = datetime('now') WHERE id = ?"
    )
      .bind(status, jobId)
      .run();
  }
}
