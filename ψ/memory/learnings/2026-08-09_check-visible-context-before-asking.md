---
pattern: Before building a clarifying question from scratch, check what's already visible in the session's own context (recent commits, git status, prior retros) — it often already narrows the ambiguity.
date: 2026-08-09
source: rrr: ayami-oracle
concepts: [clarifying-questions, context-awareness, ask-vs-check, worktree-isolation, nohup-durability]
---

# Check visible context before asking

When a user's request is ambiguous, the instinct to ask a clarifying question is correct —
but *how* that question gets built matters. Building it purely from imagination, without
first checking context already available in the session (recent git commits, git status,
open files, prior retrospectives), wastes the user's turn and can present options that
have nothing to do with what they actually meant.

**Concrete case**: Boss asked "ต่อเข้ามือถืออย่างไงดี" (how do I connect [something] to my
phone) with zero further context. The assistant's session-start system context already
listed the repo's most recent commit as `discord-bot: add "สรุปงาน" trigger that posts work
summaries to a separate channel` — strong evidence the request was about the Discord bot
already in progress. Instead of using that, the assistant asked a 4-option question
spanning unrelated guesses (SSH access, Telegram/MQTT notifications, FindMy location
tracking). Boss rejected it and had to spell out the answer himself.

**How to apply**: Before building a clarifying-question with multiple speculative branches,
spend one grep/ls/git-log pass checking what's already in view. If evidence points strongly
in one direction, either ask a narrower, evidence-informed question, or state the likely
interpretation and ask for confirmation rather than presenting it as one option among several
unrelated ones.

## Related, smaller findings from the same session

- **Worktree "fresh" mode branches from the remote tracking branch, not local `HEAD`.**
  If local `main` has unpushed commits, a fresh-mode worktree silently omits them rather
  than erroring — verify with `git log origin/main..main` or a quick `ls` of expected files
  before trusting worktree contents.
- **Not every write needs git-worktree isolation.** Files a project's own convention keeps
  deliberately untracked (e.g. this repo's `ψ/memory/retrospectives/` vault files, which its
  own `/rrr` skill explicitly says never to `git add`) don't benefit from isolate-then-merge —
  there's nothing to merge back. When an isolation guard blocks this class of write, fall back
  to a direct write (e.g. via Bash) rather than fighting the guard.
- **`nohup`-started long-running services don't survive Mac sleep/restart.** If a user needs
  a service reachable across hours (e.g. from their phone), a bare `nohup` isn't durable —
  proactively offer `launchd`/`pm2` once the underlying need for persistence is clear.

See also: [[2026-08-08_session-detection-breaks-under-concurrent-forks]] for a related but
distinct pattern (checking session identity before trusting subagent output).
