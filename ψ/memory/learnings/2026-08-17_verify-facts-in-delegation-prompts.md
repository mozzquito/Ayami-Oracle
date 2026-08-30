---
pattern: A subagent follows a wrong technical fact in a delegation prompt as faithfully as a right one — verify CLI flags/API params against the real tool before writing them into a spec, not just against documentation or memory
date: 2026-08-17
source: "rrr: ayami-oracle (drivedb feature batch)"
concepts: [delegation, verification, whisper-cpp, zcode, subagents]
---

# Verify facts in delegation prompts, not just the delegated work

While delegating a "timestamped transcripts" feature to zcode for the drivedb
project, I wrote a detailed spec instructing it to add the `-otsv` flag to a
whisper-cli invocation to get tab-separated timestamp output. zcode implemented
exactly what was asked, `tsc`/`npm run build` passed clean, and its own report
looked complete.

The flag doesn't exist on this machine's whisper-cli build. Passing an
unrecognized flag makes whisper-cli print its usage text and exit 0 — no error,
no crash, just silent non-execution. The result: transcription broke entirely
(not just the new timestamps — the existing plain-text transcript too) for
every upload that went through this code path, and it shipped that way until a
real test with actual speech content came back with an empty transcript where
one was expected.

**Why this matters**: I had already established a strong discipline this
session of independently verifying every subagent's *implementation* (reading
the real diff, running typecheck/build, real end-to-end tests against real
data). That discipline caught this bug fast. But the discipline was reactive —
it caught the mistake, it didn't prevent it. The root cause was upstream of
implementation entirely: I asserted a fact (`-otsv` is a valid whisper-cli
flag) inside the delegation prompt itself, without checking it against the
actual installed binary first. A five-second `whisper-cli --help` before
writing the spec would have caught this before any subagent time was spent.

This is the same failure mode as [[feedback_verify_before_asserting]], just
redirected: that memory is about verifying before telling *the user* something
is true; this is about verifying before telling *a subagent* something is
true as an instruction to build against. A wrong fact fed to a subagent is
arguably worse, because the subagent has no way to know it's wrong — it will
build a correct implementation of an incorrect premise, and the implementation
review (diff read, typecheck, build) will look completely clean, because
nothing about the *code* is wrong. Only exercising the real behavior surfaces
it.

**Rule going forward**: when a delegation prompt states a specific CLI flag,
config key, API parameter, or file-format detail as a given fact (not as "figure
out the right approach"), verify that fact against the real tool/API/binary on
the machine that will actually run it — don't rely on general knowledge,
training-data recall, or documentation that may not match the installed
version. This is a small, cheap check to add before every technical delegation
prompt that names something specific, and the cost of skipping it (a silent
regression that passes every implementation-level review) is much higher than
the cost of paying it.
