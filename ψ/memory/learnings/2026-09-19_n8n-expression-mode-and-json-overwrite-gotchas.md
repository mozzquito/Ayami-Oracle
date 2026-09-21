---
pattern: In n8n, any {{ }} field needs an explicit Fixed→Expression toggle, and any node returning a fresh object overwrites $json for everything downstream — reference the source node explicitly instead of bare $json when an intermediate transform node sits in between.
date: 2026-09-19
source: rrr: ayami-oracle (evisa/Wayama n8n report-automation project)
concepts: [n8n, workflow-automation, expression-mode, debugging-patterns, line-messaging-api]
---

# n8n Expression-mode and $json-overwrite gotchas

Building a full n8n pipeline (webhook → AES-256 zip encrypt → Google Drive upload → LINE OA
notification) for the evisa/Wayama project surfaced the same handful of n8n UI traps repeatedly,
across many different node fields, before they were recognized as instances of one pattern rather
than fresh bugs each time.

## The traps, in order of how often they bit

1. **Fixed vs Expression toggle is not automatic.** Typing `{{ $json.x }}` (or `={{ $json.x }}`)
   into a field still in "Fixed" mode makes n8n store it as a literal string — nothing evaluates.
   The failure is silent: no syntax error, just a wrong/undefined value downstream, or (for an
   Authorization header) an opaque "invalid token" response from the remote API. This hit the
   Google Drive node's File Name and Parent Folder fields, and the LINE HTTP Request node's
   Authorization header — same bug, different field, five times before it was named as a checklist
   item rather than re-diagnosed from scratch each time.

2. **A node returning a new object overwrites `$json` for everything downstream — it does not
   merge with upstream fields.** A "Read File(s) From Disk" node between a Code node (which set
   `zipFilename`) and a Google Drive Upload node (which referenced `{{ $json.zipFilename }}`)
   silently produced `undefined`, because the Read node's own output (fileName, mimeType, etc.)
   replaced `$json` entirely. The fix is `{{ $('Code in JavaScript').first().json.zipFilename }}`
   — reference the originating node by name whenever an intermediate transform node sits between
   the value's source and its use. Critically, this bug only shows up with a full-chain test using
   real data; a shorter smoke test that skips the intermediate node won't catch it.

3. **Never wrap an entire JSON body in one `{{ }}` expression.** For an HTTP Request node's Body
   (Content Type: JSON, Specify Body: Using JSON), writing `{{ {"to": "...", ...} }}` as one big
   expression breaks — n8n confuses the JSON's own braces with the mustache delimiters, and raw
   unevaluated source text leaks into the request. The "Using JSON" body type already auto-
   templates `{{ }}` embedded in valid JSON text; write real JSON and embed mustaches only around
   the dynamic values.

4. **`\n` in text copy-pasted from a chat interface into an n8n textarea is unreliable.** Multiple
   attempts to add a multi-line LINE message via `\n` escapes, pasted from a chat code block, kept
   turning the source's word-wrapped display line breaks into real embedded newlines inside the
   destination JSON string — invalid JSON every time (`NodeOperationError: not valid JSON`), even
   after retyping and re-pasting carefully several times. This is the same underlying failure mode
   as RDP-paste corruption seen earlier in this project's broader history (a different clipboard
   path, same symptom class: source looks fine, destination is garbled at line boundaries). The
   fix that actually worked: stop using `\n` entirely and use a non-newline separator (` | `)
   instead — sidesteps the whole class of escaping bugs rather than fighting the paste mechanism.

## How to apply

When any n8n node field produces an unexpected value (wrong, undefined, or a literal-looking
`{{ }}` string in the output), check these four in order before assuming it's a new bug:
1. Is the field actually in Expression mode (not just typed to look like one)?
2. Is there an intermediate node between the value's source and this field that returns a fresh
   object? If so, reference the source node explicitly.
3. If this is a JSON body field, is the whole body wrapped in one `{{ }}` instead of using inline
   mustaches inside real JSON text?
4. If the field's content was pasted from elsewhere and needs `\n` line breaks, did a paste
   silently convert wrapped display text into real newlines? Consider a non-newline separator.

More generally: the first time a debugging loop repeats (same symptom shape, different field), stop
and write the pattern down before doing a fourth or fifth full diagnostic pass on what is probably
the same root cause.
