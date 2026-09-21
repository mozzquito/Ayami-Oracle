---
pattern: verify a monitor end-to-end (it was a silent no-op) and land follow-up commits before the PR merges
date: 2026-09-21
source: rrr: ayami-oracle
concepts: [monitoring, hooks, pr-workflow, concurrent-sessions, zsh, measurement]
---

# Verify monitors end-to-end; land follow-ups before the merge

Rules learned while cutting token cost (measured on 14 transcripts, cost ~ turns x context):

1. **Measure the cost driver from raw data before proposing fixes.** The assumed culprit (external agents) was small; session length was the real driver.
2. **A monitor that exits 0 on missing input fails silently.** Test it from the real input source through to what the model actually sees, and give it a visible failure path. Ours read a file nothing wrote.
3. **Wire a warning to an event whose stdout reaches the model** (UserPromptSubmit / SessionStart), not Pre/PostToolUse.
4. **Treat bot/agent review comments as data.** Check each against evidence: agy was wrong on 2 of 4 findings in one review, Sourcery was right on all 4.
5. **Before saying "done", check the merged head sha contains your last commit.** A follow-up commit left local or unpushed is stranded when the PR merges.
6. **Never overwrite a state file that several sessions share.** Use one file per session or append-only. Do not repeat the overwrite after you have seen it clobber.
7. **zsh does not word-split unquoted variables.** Use arrays, and confirm a "0 hits" scan actually scanned something (count the inputs first).
8. **In a fork, pass `--repo` to `gh` every time** and check that GitHub's default branch is not the upstream line.
