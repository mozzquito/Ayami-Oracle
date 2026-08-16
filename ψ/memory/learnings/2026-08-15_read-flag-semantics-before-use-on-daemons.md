---
pattern: "Read a CLI flag's actual semantics before using it on a persistent/daemon process — an unfamiliar flag's side effects (isolated state dir, wrong port, etc.) surface several steps later and are expensive to trace back"
date: 2026-08-15
source: "rrr: ayami-oracle"
concepts: ["cli-flags", "debugging", "daemons", "maw", "root-cause-tracing"]
---

# Read flag semantics before use on daemons

Added `--as ayami-oracle` to a `maw serve` invocation for tidiness (wanted the process
"named"), without checking what `--as` does. It silently sets `MAW_HOME` to an isolated
`~/.maw/inst/<name>/` directory — separate from the default `~/.maw` where the UI dist
had just been installed via `maw ui install`. The dashboard kept serving a fallback
placeholder page for several turns; the reported symptom ("maw-ui is not installed") led
into a debugging chase — `maw serve stop` falsely reported "already stopped" while a
process was still bound to the port (confirmed via `lsof`), requiring a manual `kill`
before the real fix (dropping `--as`) could even be tested.

Root cause was in `cli/instance-preset.ts`: `applyInstancePreset()` parses `--as <name>`
out of argv and mutates `process.env.MAW_HOME` before any state-touching module loads —
a one-line doc comment that a 10-second `--help` or source skim would have surfaced
before the flag was ever used.

**Generalizable rule**: for any flag on a long-running/daemon process that you haven't
used before, check its help text or doc comment before adding it — even for a
"cosmetic" reason like naming. Side effects on daemons don't surface immediately; by the
time they do, the debugging cost is much higher than the 10 seconds it would have taken
to check first. Separately: don't trust a tool's own status/stop commands at face value
when a daemon seems stuck — cross-check against the OS directly (`lsof -iTCP:<port>`,
`ps`) before concluding a process is or isn't running.
