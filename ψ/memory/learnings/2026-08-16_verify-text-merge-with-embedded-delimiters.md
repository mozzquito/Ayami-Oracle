---
pattern: When parsing/merging free-form text payloads (e.g. captured SQL), never split on a delimiter that the payload itself may contain — verify with a known-answer needle, not just row counts
date: 2026-08-16
source: "rrr: ayami-oracle"
concepts: [awk, data-parsing, text-processing, verification, sql-server-plan-cache]
---

# Verify text merges with a known-answer needle, not row counts

Merging deduplicated `count \t sql_text` rows from 5 SQL Server plan-cache CSV
dumps (~450MB total) using `awk -F'\t'` silently dropped/truncated entries
whose SQL text contained literal tab characters (common in T-SQL formatted
with tabs). Two of the most important findings — two undocumented triggers
guarding a 2022 production bug — vanished from the merged "top 10" list
without any error. They were only caught because a follow-up `grep` for the
trigger names by coincidence turned up zero matches in the merged file,
prompting a re-check.

**Why**: `-F'\t'` (or any single-char field separator) splits on *every*
occurrence of that character in the line, not just the one intended as the
record delimiter. If the payload can contain that character — which is
almost guaranteed for arbitrary captured text like SQL/log/user content —
the split silently corrupts data instead of erroring. Row counts before/after
a merge can match perfectly even when content is wrong, because corruption
truncates fields rather than dropping rows.

**How to apply**: When parsing or merging arbitrary text payloads (captured
queries, logs, user-submitted text) in awk/sed/cut:
1. Don't use a single character as `-F`/`FS` unless the payload is guaranteed
   not to contain it. For a two-field `count<sep>text` format, extract with
   `index()`/`substr()` to grab only the *first* occurrence of the separator,
   leaving the rest of the line untouched.
2. After any merge/dedupe step over unfamiliar data, pick one or two known
   values you expect to survive the merge and `grep` for them explicitly.
   Matching row counts is not sufficient evidence — content can be corrupted
   while counts stay identical.
3. This generalizes beyond awk: any pipeline that tokenizes free-form text
   (CSV parsers assuming no embedded commas, log parsers assuming no embedded
   newlines, etc.) needs the same "assume nothing about the payload" caution.
