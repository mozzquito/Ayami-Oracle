#!/usr/bin/env bun
// Data source for /recap --visual: last N rows of session-metrics.md as JSON.
// Read-only, no MCP calls here — this only gathers data; the calling skill
// (SKILL.md) does the Excalidraw create/update itself, since MCP tools are
// only callable by the agent, not by a shelled-out script.
// Usage: bun session-board.ts [limit]

import { $ } from "bun";
import { existsSync, realpathSync } from "fs";
import { join } from "path";

const limit = Number(process.argv[2]) || 25;

const root = (await $`git rev-parse --show-toplevel 2>/dev/null`.text()).trim() || process.cwd();
process.chdir(root);

const psi = existsSync("ψ") ? realpathSync("ψ") : "ψ";
const repoName = root.split("/").pop() || "";
const metricsFile = join(psi, "memory", "learnings", "session-metrics.md");

type Entry = { when: string; session: string; done: string };

// Cut at the first clause break (; or .) when that lands within range, else at
// the last word boundary before maxLen — never mid-word, so cards read as
// whole phrases instead of chopped fragments like "requirements (c".
function truncateClause(s: string, maxLen = 100): string {
  const semi = s.indexOf(";");
  const period = s.indexOf(". ");
  let stop = -1;
  if (semi !== -1) stop = semi;
  if (period !== -1 && (stop === -1 || period < stop)) stop = period;
  let cut = stop !== -1 && stop <= maxLen * 1.5 ? s.slice(0, stop) : s;
  if (cut.length > maxLen) {
    const lastSpace = cut.lastIndexOf(" ", maxLen);
    cut = cut.slice(0, lastSpace > 0 ? lastSpace : maxLen);
  }
  cut = cut.trim();
  return cut.length < s.trim().length ? `${cut}…` : cut;
}

let entries: Entry[] = [];

if (existsSync(metricsFile)) {
  const text = await Bun.file(metricsFile).text();
  const rows = text
    .split("\n")
    .filter((l) => l.startsWith("|"))
    .filter((l) => !/^\|\s*-+\s*\|/.test(l)) // drop the header separator row
    .filter((l) => !/^\|\s*when\s*\|/i.test(l)); // drop the header row itself

  for (const row of rows) {
    const cols = row.split("|").map((c) => c.trim());
    // | when | session | done | stuck | win | friction | error |
    // split("|") on a leading/trailing-pipe row yields ["", when, session, done, ..., ""]
    const when = cols[1] ?? "";
    const session = cols[2] ?? "";
    const done = truncateClause(cols[3] ?? "", 100);
    if (when && session) entries.push({ when, session, done });
  }
}

entries = entries.slice(-limit);

console.log(JSON.stringify({ repo: repoName, count: entries.length, entries }, null, 2));
