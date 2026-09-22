---
pattern: Check where an artifact came from before attributing it, repeat stochastic measurements before quoting a result, read the real system before ranking options, and cross-audit multi-agent claims (gold before the run, interpretation after)
date: 2026-09-21
source: rrr: ayami-oracle
concepts: ["rrr", "verification", "multi-agent", "stochastic-models", "provenance", "jev", "zcode", "agy"]
---

# Rules from the Jev trial (generalizable)
1. **Provenance before attribution.** A screenshot, file or quote in the user's message is not necessarily theirs; check where it came from (filename pattern, folder, source) before writing "you have X" into notes or answers.
2. **Repeat stochastic measurements (>=10x) before quoting a zero-error result.** One run of a model whose scores vary by about +/-0.04 turned a borderline case (mean 0.51) into a fake "0 false alarms". Report the spread, and place decision bands so that the observed noise cannot flip a result to "safe".
3. **Read the real system before ranking integration options.** A proposal ranked second turned out to solve a problem the target (owner-only bot, prefix routing) never had.
4. **Multi-agent review loop:** (a) fix the gold labels and the decision rule before running; (b) have the agents cross-audit each other's gold labels and the design; (c) after the run, have them critique your interpretation; (d) verify every reviewer claim against the cited lines yourself. Reviewers over-claim in both directions (called disclosed limits "deceptive"; believed a probability was binary; swapped a reason between two items).
5. **Compare variants under the same protocol** (e.g. count "unsure" as wrong for both) before declaring one better; retract the claim when the comparison was unfair.
6. **Secrets pasted into chat:** store in a 0600 file outside the repo, never echo them, scan new files for key patterns before each commit, and tell the user to revoke; better, offer a channel that never touches the chat before asking for the key.
Related: [[2026-09-21_typesafe-docs-team-learn]]. Details: ψ/learn/docs.typesafe.ai/2026-09-21/0141_TEAM-LEARN.md.
