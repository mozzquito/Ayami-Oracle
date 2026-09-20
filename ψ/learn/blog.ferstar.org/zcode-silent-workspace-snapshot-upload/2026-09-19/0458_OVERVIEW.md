# ZCode silent workspace snapshot upload — overview

- **Source**: https://blog.ferstar.org/en/posts/zcode-silent-workspace-snapshot-upload/ (published 2026-09-18; reached via a Facebook `l.php` redirect, `fbclid` stripped)
- **Author**: ferstar (developer, blog author) — a single first-hand write-up, no vendor response in the article
- **Learned**: 2026-09-19 by Ayami (main agent, read inline — single article, no subagents)
- **Mode**: --fast equivalent (1 doc). Not a git repo, so no ghq clone / `origin/` symlink.

## What the article claims

While logged in, ZCode (Zhipu/Z.ai's Electron coding app) packs the **whole workspace including `.git`** (LFS cache, objects, logs), encrypts it, and uploads it to **Aliyun OSS**. The RSA public key comes from the server per upload; the private key lives only server-side, so the local `.enc` file can't be opened by the user or the app.

### Evidence on the author's machine
| Item | Value |
|------|-------|
| `~/.zcode` | 700MB+ |
| `~/.zcode/v2/checkpoints/` | 303MB, one `.enc` of 313MB |
| state file | `encryptedSizeBytes: 313070842`, `workspaceSizeBytes: 345549173`, `kind: "baseline"`, **`failureCount: 564`** |
| Manifest (42,411 files) | `.git/lfs` 56.8%, `.git/objects` 29.6%, `.git/logs` 0.2%, source+docs only 13.4% → **~86.6% is `.git`** |
| Workspace | commercial project, 10GB raw / 345MB after excluding deps |

### Mechanism (as the author reverse-engineered from `app.asar`)
1. `POST https://zcode.z.ai/api/v1/snapshot/upload-credential` → snapshot id, RSA public key, size limit, OSS form creds, callback URL
2. Locally: tar.gz → **AES-256-CTR** → symmetric key wrapped with **RSA-OAEP-SHA256**
3. Direct HTTP form POST to Aliyun OSS (bypasses ZCode servers)
4. OSS callback tells the Zhipu backend it arrived
5. Triggers: `captureBeforePrompt` (every prompt) and task completion tagged `repo-wiki-update`; one session produced up to 62 captures

### UI settings don't stop it (per author)
- **Optimize Experience** (`optimizeAgentExperienceEnabled`) → only the model-training consent
- **Repo Snapshot Indexing** (`repoSnapshotIndexingEnabled`) → only server-side indexing; packing + upload continue

### Mitigation given
```bash
# macOS
rm -rf ~/.zcode/v2/checkpoints
mkdir -p ~/.zcode/v2/checkpoints
chflags uchg ~/.zcode/v2/checkpoints
touch ~/.zcode/v2/checkpoints/test   # expect: Operation not permitted
# undo: chflags nouchg ~/.zcode/v2/checkpoints

# Linux
sudo chattr +i ~/.zcode/v2/checkpoints   # undo: sudo chattr -i
```
Trade-off: checkpoint/timeline (rollback) UI stops working; chat, autocomplete, tools still fine. Deleting alone doesn't help — it gets re-packed within ~30 min.

### Privacy policy
Mentions collecting "text, files, and code submitted during conversations" but nothing about silently packaging whole workspaces + full Git history. Author's framing: not a backup (user would hold the key), it's collection.

## Cross-check against Moss's machine (2026-09-19, ZCode.app 3.6.5, read-only)

| Blog claim | What I verified locally |
|-----------|-------------------------|
| Pack → AES-256-CTR → RSA-OAEP-SHA256 → OSS form upload | ✅ Same code in `app.asar`: `encryptArchive` uses `aes-256-ctr` + `RSA_PKCS1_OAEP_PADDING`/`sha256`; `x-oss-signature` form fields |
| Staging in `~/.zcode/v2/checkpoints/` | ✅ Code builds `<root>/checkpoints/<hash12>/{tmp,pending,manifests,state.json}`; legacy `repo-snapshots` was renamed to `checkpoints` |
| Trigger before every prompt | ✅ `captureBeforePrompt` → `captureBeforePromptUnsafe` |
| `failureCount` counter | ✅ `recordFailureCountAtTurnBoundary` |
| `repoSnapshotIndexingEnabled` doesn't gate upload | ✅ Only read by the Settings UI toggle + schema, never by capture code |
| "Unconditional at startup / any login" | ⚠️ Slightly different in 3.6.5: capture runs only if a **token exists** and the **server returns an upload key** (`if(!a) return`). So it is server-controlled, not literally unconditional — but no user-side switch. |
| Files piling up in `checkpoints/` | ❌ Not on this machine: no `~/.zcode/v2/checkpoints`, no state.json/manifests, no upload log lines. Inference: never captured here. |

The blog doesn't state its ZCode version; mine is 3.6.5 (3.11.2 was offered as an update). Behaviour may differ across versions.

## Takeaways
- Server-issued upload key = vendor can turn collection on per account without an app update.
- The only reliable user-side gates: **sign out** (no token → early return) and **immutable staging dir** (create it first, then lock it — a locked *pre-existing empty* dir is what the author tests with `touch`).
- Always add the `touch` test after locking; I had not tested the lock myself before this article.
- Not yet checked: the `zcode` **CLI** binary (`~/.zcode/cli`, used by `/zcode`) — separate from the Electron app this post covers.

## Related
- [[memory/project_zcode_silent_upload_check]] (auto-memory) — local verification notes
- Golden rule 7 (notify before accessing files outside repo) was followed during the local check.

---
## Follow-up 2026-09-19 05:2x (appended — earlier text kept as-is)

- **zcode CLI checked**: `zcode` = `node /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs` (12MB, inside the app bundle). Static string scan: **no** snapshot-upload code (0 hits: upload-credential, captureBeforePrompt, encryptedArtifact, x-oss, aes-256-ctr, RSA-OAEP, repo-snapshot). `zcode.z.ai/api/v1` there is the OAuth client (`ZaiCliOAuthError`); `checkpoints` refers to local `/rewind`. The 7 plugins under `glm/packages/` are clean too. → The blog's mechanism is Electron-app-only. Limit: static scan, no runtime traffic capture.
- **Lock applied** (Moss approved): `mkdir -p ~/.zcode/v2/checkpoints && chflags uchg ~/.zcode/v2/checkpoints`; `touch` inside → `Operation not permitted` ✅. Undo: `chflags nouchg`.

---
## Follow-up 2026-09-19 05:5x (rrr — appended)

Verified in ZCode.app 3.6.5 `app.asar` after the earlier notes:
- **Real UI labels** (English): "Index new folders" (Settings → Indexing → Codebase; = `repoSnapshotIndexingEnabled`) and "Improve experience" (same page as "Data storage path"/"Onboarding"; = `optimizeAgentExperienceEnabled`). The blog's names are the internal flag names.
- **Neither toggle gates capture**: `repoSnapshotIndexingEnabled` is read only by the settings UI; `optimizeAgentExperienceEnabled` has 26 occurrences = schema + migration + 5 settings-UI state uses, none in `captureBeforePromptUnsafe`. (My earlier "both verified" was said after checking only the first — closed here.)
- **`.git` is included**: the include-decision function returns `include:true` for root `.git` metadata and any path with a `.git` segment (`hasGitInternalSegment`).
- **Secret filter exists but skips `.git`**: `.env*`, `.npmrc`, `id_rsa*`, `*.pem/.key/.p12/.pfx`, names containing `token`/`secret` are excluded for normal files, but the `.git` include check comes first — old secrets in commit history are not filtered.
- Skipped dirs: `node_modules`, `.cache`, `.turbo`, `dist`, `build`, `out`, `.next`, `coverage`.
- Still unknown: why capture never ran on this machine.
