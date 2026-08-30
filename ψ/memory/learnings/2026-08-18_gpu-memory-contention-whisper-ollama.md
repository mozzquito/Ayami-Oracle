---
pattern: "Two local GPU-accelerated services (whisper-cpp + Ollama on Apple Silicon) can OOM each other just from one being idle-but-loaded — verify a design against real hardware measurement before trusting an estimated timeout or a 'sound design' review"
date: 2026-08-18
source: "rrr: ayami-oracle (drivedb)"
concepts: [gpu-memory, ollama, whisper-cpp, apple-silicon, auto-summarize, timeout-tuning]
---

# Idle-but-loaded GPU models can OOM each other on Apple Silicon

While implementing an "auto-summarize after transcription" feature in drivedb
(calls a local Ollama server right after a local whisper-cpp transcription
completes), a real, 100%-reproducible bug surfaced only through actual
end-to-end testing: if Ollama has a model resident in GPU/unified memory
(even completely idle, not answering a request) when whisper-cli tries to run
its own Metal backend, whisper-cli crashes outright:

```
ggml_metal_synchronize: error: command buffer 1 failed with status 5
error: Insufficient Memory (00000008:kIOGPUCommandBufferCallbackErrorOutOfMemory)
```

On the machine this was found on (Apple M1, `recommendedMaxWorkingSetSize`
~5.7GB), whisper's medium model (~1.5GB) plus Ollama's qwen2.5:7b (~4.6GB)
together exceed the available budget. This isn't a "both running at the
exact same instant" collision — Ollama keeps a model loaded for its
`keep_alive` window (default several minutes) regardless of whether it's
actively processing anything, so *any* whisper-cli invocation during that
window can fail, not just a literally-concurrent one.

**Why this was almost missed**: a design review (including a second-model
sanity-check from a different AI) approved the auto-summarize design as
"sound" before this was ever run for real. The bug only surfaced because two
test uploads happened to run close together while Ollama was still warm from
an unrelated manual reachability check — a lucky test-ordering accident, not
a deliberate test of this specific interaction. A cleanly-separated test
sequence (test each feature in isolation, always waiting for Ollama to fully
idle out between tests) would likely have shipped this silently broken.

**Fix**: Ollama's `/api/generate` endpoint accepts a `keep_alive` field in
the request body; passing `0` unloads the model immediately after
responding, instead of leaving it resident for the default keep-alive
window. Use this for any *auto-triggered* call path (where the caller isn't
necessarily going to make another Ollama call soon), while leaving it unset
for *manually-invoked* paths (where staying warm is a legitimate convenience
if the user runs several summaries back-to-back).

**Related, separately-discovered finding on the same testing pass**: the
originally-planned 20-second timeout for the auto-triggered summarize call
(itself already a refinement suggested by a design-review pass, down from
Ollama's cold-load risk) was still too short in practice — real measured
cold-load times on this machine ranged from 18s to over 70s across repeated
tests, not the ~15-20s the design review estimated. No single "reasonable"
timeout reliably covers that variance; the final choice (60s) is a
data-driven compromise, not a guaranteed fix. **Rule**: don't trust an
estimated timeout — even one that survived a careful design review — without
checking it against real measured latency on the actual target hardware.
Cold-loading a multi-gigabyte model is exactly the kind of operation where a
single test run understates real-world variance.

**Broader rule**: when two local processes both do hardware-accelerated
inference on the same machine (any Metal/CUDA/GPU-backed local AI tooling —
not just this specific whisper+Ollama pairing), assume they compete for the
same memory pool even when not literally concurrent, and test the "one just
finished, the other starts shortly after" sequence explicitly rather than
only testing each in isolation.
