# Handoff: /recap --visual — Excalidraw session-log board

**Date**: 2026-09-22 10:55
**Context**: ~205k tokens (over 150k warn threshold — this is why we're closing now)
📡 Session: a74ad5cd | ayami-oracle

## Context
**Oracle**: Ayami Oracle (หญิง) | **Human**: มอส (ชาย)
**Mode**: Fast | **Memory**: auto

## What We Did
- Built a new `/recap --visual` mode: renders the last 25 rows of `session-metrics.md`
  as a rebuilt (not appended) Excalidraw board — one card per closed session (session id,
  date, one-line summary).
- Design was consulted with zcode + agy in parallel (both converged): don't write to
  Excalidraw at `/rrr`-close time (network/race risk); make the board a lazily-rebuilt
  *derived* view at `/recap` time instead; cap it (~25 sessions) to avoid canvas bloat.
  มอส confirmed both trade-offs via AskUserQuestion (opt-in `--visual` flag, 25-session cap).
- New script `session-board.ts` reads `ψ/memory/learnings/session-metrics.md` and outputs
  JSON. First version truncated the `done` column at a hard 90-char slice, which chopped
  words mid-string ("...requirements (c", "...coverag") — มอส caught this as "อ่านไม่เข้าใจ".
  Fixed: `truncateClause()` now cuts at the first `;`/`.` or the last word boundary, with
  a trailing `…`, never mid-word.
- Live-tested end-to-end (not just designed): created a real scene "Ayami Session Log —
  ayami-oracle" in the `Main` Excalidraw+ collection, rendered 25 session cards, verified
  visually with `take_screenshot`, then rebuilt it in place with the truncation fix.
- **Live board**: https://app.excalidraw.com/s/3oGho4k5kPa/2tlFvkC4yIn
- Pointer file written: `ψ/memory/logs/excalidraw-session-board.md` (scene_url/scene_id/
  collection_id/repo/updated) — gitignored, workspace-local, lets the next `/recap --visual`
  run reuse this same scene instead of creating a new one.
- **Found and fixed a real bug while testing via the actual `/forward`/`/recap` slash
  commands**: those commands load skills from `~/.claude/skills/` (the global "shelf"),
  NOT from this project's `.claude/skills/` — so every edit made to
  `ayami-oracle/.claude/skills/recap/SKILL.md` (+ the `.agents/`/`.codex/` mirrors inside
  the repo) never actually took effect. This is exactly the staleness class recap's own
  SKILL.md Step 2.5 warns about; the global shelf here was ~26.5.16, over a month behind
  the project's ~26.8.23-alpha.2112. Patched `~/.claude/skills/recap/SKILL.md` directly
  (added the same VISUAL MODE section + argument-hint, minimal patch — did not pull in
  other unrelated upstream version differences) and copied the fixed `session-board.ts`
  there too. Verified with a smoke-test run against the real `ψ/memory/` path.
- มอส also raised: should this per-session summary live in Google Drive instead? Answered
  inline (no new zcode/agy round, to conserve context) — recommended keeping Excalidraw as
  the "visual glance" layer (already built + tested) and treating a Google Sheet as a
  possible future durable append-only log if that's ever wanted; not built.

## Pending
- [ ] Commit the 6 modified files (`.claude/`, `.agents/`, `.codex/` × `SKILL.md` +
      `session-board.ts` inside the repo) — currently uncommitted on `lab/jev-gate`.
      These are the project-local mirrors; real behavior now depends on the
      `~/.claude/skills/recap/` patch (already applied, not committed anywhere since it's
      outside the repo).
- [ ] `~/.codex/skills/recap/` (Codex's own global shelf) still has the OLD recap SKILL —
      same staleness bug, not yet patched. `~/.agents/skills/recap/` does not exist at all
      on this machine, so no action needed there.
- [ ] Never actually re-ran the real `/recap --visual` slash command end-to-end through the
      now-patched global shelf (only ran the underlying script + MCP calls manually). Worth
      one real invocation next session to confirm the full skill-driven path works, not
      just the pieces.
- [ ] Google Sheet-as-durable-log idea floated by มอส — not designed or built, just discussed.

## Next Session
- [ ] Run `/recap --visual` for real (not manual MCP calls) to confirm the patched global
      skill actually drives the whole flow correctly.
- [ ] Decide whether to commit the 6 mirrored project files now or fold into a larger commit.
- [ ] If มอส wants it: patch `~/.codex/skills/recap/SKILL.md` + script too, same minimal-diff approach.

## Key Files
- `/Users/phongcheatphus/ayami-oracle/.claude/skills/recap/SKILL.md` (+ `.agents/`, `.codex/` mirrors)
- `/Users/phongcheatphus/ayami-oracle/.claude/skills/recap/session-board.ts` (+ mirrors)
- `/Users/phongcheatphus/.claude/skills/recap/SKILL.md` — **the actually-live global copy**, patched
- `/Users/phongcheatphus/.claude/skills/recap/session-board.ts` — copied here, fixed truncation
- `ψ/memory/logs/excalidraw-session-board.md` — scene pointer
- `ψ/memory/learnings/session-metrics.md` — data source (unchanged, just read)
