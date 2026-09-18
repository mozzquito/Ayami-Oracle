---
pattern: "Learned ferstar/ZCode blog: ZCode.app packs full workspace + .git, encrypts with server-held RSA key, uploads to Aliyun OSS; UI toggles are not gates; sign-out or locking ~/.zcode/v2/checkpoints are"
date: 2026-09-19
source: learn: blog.ferstar.org/zcode-silent-workspace-snapshot-upload
concepts: ["learn", "privacy", "zcode", "data-exfiltration", "electron", "mitigation"]
---

# Learned: ZCode silent workspace snapshot upload

- **Mechanism**: `captureBeforePrompt` → tar.gz → AES-256-CTR → key wrapped with a server-issued RSA public key → presigned Aliyun OSS form upload. Private key is server-only, so the local `.enc` is undecryptable by the user. ~86.6% of the author's payload was `.git`, i.e. full history incl. deleted secrets.
- **Toggles lie by omission**: `optimizeAgentExperienceEnabled` = training consent only; `repoSnapshotIndexingEnabled` = server indexing only. Verified in ZCode.app 3.6.5 `app.asar`: the latter is read only by the settings UI.
- **Real gates**: no login token (sign out) or an immutable staging dir. Create the dir first, then `chflags uchg` (macOS) / `chattr +i` (Linux), and test with `touch` → "Operation not permitted". Costs checkpoint rollback.
- **Verify before believing, both ways**: the blog said "unconditional"; the installed 3.6.5 code actually also needs a server-issued upload key, and Moss's machine had zero staged data. Claim checked against local evidence → "code present, not triggered here".
- **Open**: `zcode` CLI binary (used by `/zcode`) not inspected.

Full write-up: `ψ/learn/blog.ferstar.org/zcode-silent-workspace-snapshot-upload/`
