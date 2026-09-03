---
pattern: "Before running a skill's literal shell pipeline against prose/narrative content, trace what the operation does to structure, not just whether it errors — sort/uniq-style dedup destroys chronological order in transcripts and chat logs"
date: 2026-09-03
source: "rrr: ayami-oracle (fb-video-review-and-claude-tag-team-repo)"
concepts: ["skills", "shell-pipelines", "watch-skill", "transcript-cleaning", "verification-before-use"]
---

# Sanity-check skill shell pipelines against prose content before using the output

The `/watch` skill's transcript-cleaning step uses
`sed ... | sed 's/<[^>]*>//g' | sort -u` to strip SRT formatting and dedupe
caption lines. `sort -u` alphabetizes lines as a side effect of
deduplication — harmless for unordered data (config lines, log lines) but
it silently destroyed the chronological order of a spoken-video transcript
in this session. The corruption was only caught because the intermediate
output happened to be read before being used downstream; had it been piped
straight into analysis, the resulting summary would have been built on
jumbled, incoherent source material with no error or warning anywhere in
the pipeline.

**Rule**: before executing a skill's literal shell command against prose,
narrative, or otherwise sequential text (transcripts, chat logs, ordered
instructions), mentally trace what the operation does to structure — not
just whether it runs without error. Order-preserving dedup
(`awk '!seen[$0]++'`) is the safe default for any pipeline touching
sequential text; `sort -u` is only safe for genuinely unordered data.

This generalizes beyond the `/watch` skill: any time a skill or template
prescribes a shell one-liner, treat it as a suggestion to verify against
the actual content shape, not a command to execute blindly — especially
when the content is prose rather than structured/tabular data.

See [[fb-video-review-and-claude-tag-team-repo]] retrospective for the
concrete incident this was distilled from.
