---
pattern: "Memory-architecture evaluation (6 Soul-Brews-Studio repos): keep local markdown+LanceDB as primary; session-search is the one concretely actionable addition"
date: 2026-09-03
source: "learn: Soul-Brews-Studio/{memory-lab-2sep,memory-horizon,session-viewer,session-search,higher-order-mcp,arra-memory-lab}"
concepts: ["memory-architecture", "decision", "mcp", "cloudflare", "session-search"]
---

# Memory architecture evaluation — decision

On 2026-09-03 morning, 6 repos were `/learn --fast`'d in parallel to evaluate whether any should extend or replace Ayami's current memory stack (`ψ/memory/` git-tracked markdown + local LanceDB + duckdb queries, fully local, no cloud dependency). An agy second-opinion pass on `psi-memory-lab` priority ran afterward but its actual answer was never saved anywhere findable — this doc reconstructs the decision from the six `/learn` analysis docs themselves (`ψ/learn/Soul-Brews-Studio/*/2026-09-03/1144_OVERVIEW.md`), which turned out to be more substantive than a recovered chat answer would have been anyway.

## Verdict per repo

| Repo | What it is | Verdict |
|---|---|---|
| **session-search** | MCP-callable search + age-bucketed ("horizon") layer over session-viewer's index | **Adopt** — its own doc says "Ready to wire up as Ayami's MCP tool. No setup required beyond passing `--db`." Complementary to the existing lance-indexer, not redundant (MCP-callable during conversation vs. lance-indexer's browser-only UI). |
| **session-viewer** | macOS native (Swift) indexer/search for Claude Code JSONL transcripts — the backing index session-search needs | **Adopt as a dependency of session-search.** Solid, zero third-party deps, 118 tests passing. One real risk flagged: a Unicode-path (`ψ`) build/import bug likely lives in session-search's Bun/Node build step, not session-viewer itself — verify with a symlinked ASCII path before committing to it as the indexer. |
| **memory-horizon** | Local, read-only governance/audit tool — classifies work as LIVE/COOLING/DORMANT/STALE/DEPRECATED with evidence links | **Worth adding, low priority.** No cloud, no billing risk, orthogonal to search (governance vs. discovery). Alpha maturity (v26.9.1-alpha.2106) — real-world mileage unproven. |
| **memory-lab-2sep** | Cloud MCP memory server on Cloudflare Workers + D1, substring search only | **Skip for now.** No semantic search (current LanceDB has Thai-aware embeddings), cloud latency (33-51ms Bangkok / 745ms from US where claude.ai runs), and adds a Cloudflare account dependency for a feature (cloud access) that's low-priority for a solo user. |
| **arra-memory-lab** | Structured memory w/ evidence lineage, preview-before-mutation, Cloudflare Workers AI embeddings | **Skip for now, revisit at scale.** The evidence-lineage and mutation-safety model is genuinely good design, but it requires Cloudflare + Workers AI billing exposure (~$5-15/month) for a problem (observation-chain tracking) Ayami doesn't have yet. Its own doc's recommendation: "revisit if Ayami grows to 500+ memories" or if a multi-user scenario emerges. |
| **higher-order-mcp** | Production MCP server template — dynamic tool creation/hiding at runtime, no redeploy | **Skip.** Solves a problem Ayami doesn't have (a solo user with a small, stable MCP tool set doesn't need runtime tool composition). Its own doc: "Skip if Ayami needs 1-3 static tools." |

## Decision

**Keep `ψ/memory/` markdown + local LanceDB/duckdb as the primary memory stack — none of the 6 repos justify replacing it.** Every doc that touched the topic independently converged on the same answer: local-first, no cloud dependency, is the right fit for a solo user right now.

**The one concrete action item**: adopt `session-search` (+ `session-viewer` as its backing indexer) as an MCP tool, since it fills a real gap — the existing lance-indexer is browser-only and can't be invoked mid-conversation by Ayami herself. Verify the Unicode-path build issue first with a symlinked ASCII test path before wiring it in for real.

**Not yet decided / left open**: whether to add `memory-horizon` as a low-cost governance layer — no blocker found, just never revisited after this survey.

---

## Superseded update — 2026-09-03, later same day (session `450dbd0e`)

A concurrent/later session ran a much deeper 2-day survey-and-adopt pass over this same repo set and **moved past this doc's "not yet decided" items into actual deployment**. Per that session's retro (`ψ/memory/retrospectives/2026-09/03/15.34_memory-tooling-survey-and-adoption.md`) and its `session-metrics.md` row (`450dbd0e`, 15:34):

- **`psi-memory-lab` + `memory-horizon` were adopted**, both wired to `launchd` crons (psi-memory-lab daily 12:35, memory-horizon weekly Fri 12:40), alongside a `lanceglass` cron from day 1 (12:30).
- **`lance-indexer` was fully embedded** (7,980 vectors) — a tool this doc didn't cover at all (it wasn't in the 6-repo set this doc synthesized).
- **The Unicode-path (`ψ`) risk this doc flagged as needing verification before adopting `session-search`/`session-viewer` was tested directly and disproved** — the real root cause of the earlier suspected bug was a skipped `init-db` step, not Unicode path handling. So the caution in this doc's "one concrete action item" section no longer applies as written.
- `session-search`'s MCP wiring specifically is still listed as **not started** even in the later session — so that part of this doc's recommendation is still open, just no longer blocked on the Unicode-path concern.

**Read this doc as the early, narrower pass** — for the fuller, tested picture, go to session `450dbd0e`'s retro directly rather than treating this doc's verdict table as current.
