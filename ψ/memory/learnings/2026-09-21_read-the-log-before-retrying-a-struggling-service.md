---
pattern: When a request times out against a service with heavy lazy initialisation, read its log and memory state before retrying; retries can multiply the load and kill it. Load once at startup and serialise requests.
date: 2026-09-21
source: rrr: ayami-oracle
concepts: ["rrr", "retry", "oom", "lazy-init", "lru_cache", "local-model", "third-party-code", "verification"]
---

# Read the log before you retry
**What happened**: a local model server (0.8B, ~3 GB in fp32) loaded its model lazily on the first request behind `functools.lru_cache`. The client's default 10 s timeout fired during that load,
and the SDK plus my own manual retry each sent another request; every concurrent first request loaded its own copy, RAM (8 GB, already swapping) ran out, and the OS killed the process (exit 137).
The log showed the "Loading weights" bar repeating 5+ times; I only looked after the second failure, after first suspecting the SDK.

**Rules**
1. On a timeout or reset from a stateful/heavy-init service, look at the service log and machine memory (`memory_pressure`, swap) BEFORE sending the request again; a retry is not free.
2. `lru_cache` does not lock while computing: concurrent first calls all compute. Make heavy initialisation eager (at startup) or guard it with a lock, and serialise inference on small machines.
3. Give first-call clients a long timeout (warm-up), or warm the service before measuring.
4. Third-party model code: diff the code that will run against a source you read, pin the revision, verify the file hash, install in an isolated venv, and prefer loading through a reviewed package over `trust_remote_code`.
5. Treat a summary produced by a small model (web-fetch tools) and a reviewer agent's claims as leads: re-check each decision-critical detail against the primary file (here: Python version, pickle vs safetensors).
Related: [[2026-09-21_openthai-systemone-local-eval]], [[2026-09-21_repeat-measurements-check-provenance-cross-audit]].
