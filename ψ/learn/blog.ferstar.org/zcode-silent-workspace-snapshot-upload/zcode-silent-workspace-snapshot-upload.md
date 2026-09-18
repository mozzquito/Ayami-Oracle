# zcode-silent-workspace-snapshot-upload Learning Index

## Source
- **Article**: https://blog.ferstar.org/en/posts/zcode-silent-workspace-snapshot-upload/ (2026-09-18)
- **Type**: blog post (no git origin — nothing to symlink/offload)

## Explorations

### 2026-09-19 0458 (--fast, inline)
- [[2026-09-19/0458_OVERVIEW|Overview + local cross-check]]

**Key insights**: ZCode's Electron app can pack the full workspace + `.git` history, encrypt it with a server-held RSA key, and push it to Aliyun OSS; UI toggles don't stop it. On Moss's machine (3.6.5) the code exists but nothing was ever staged. Real gates: sign out, or lock `~/.zcode/v2/checkpoints`.
