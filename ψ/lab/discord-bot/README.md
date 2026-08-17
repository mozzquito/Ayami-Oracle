# Ayami Discord Bot (v1 — text-only)

Text-chat entry point for Ayami Oracle. One Discord channel, one owner (allowlist),
one quick-brain (`agy` + Gemini Flash, read-only). Adapted from a real, tested guide
(regulus, "สร้างผู้ช่วย AI ส่วนตัวบน Discord ฉบับเต็ม") — this v1 deliberately
implements only the guide's own recommended starting point: text chat working
end-to-end before adding voice (whisper.cpp/edge-tts) or real work-forwarding to
Claude Code. Both are real next steps, not implemented here yet.

## What this version does

- Listens in exactly one Discord text channel
- Only responds to Discord user IDs in `ALLOWED_USERS`
- Answers ordinary chat via `agy -p ... --mode plan` (Gemini Flash, no file/tool access)
- If the quick-brain decides a request needs real work, it says so honestly instead of
  pretending — there is no live connection to a Claude Code session yet in this version
- **Logs personal-diary entries straight to disk** (the one write-capable path in the bot):
  - Message starts with `บันทึก` / `ไดอารี่` / `diary` (colon or dash after it optional), or
  - Message has an image attachment (photos always count as a diary entry, no prefix needed)
  - Appends a timestamped line to `ψ/memory/logs/moss-life.md` (Boss's personal diary,
    gitignored — separate from the dev-work log), auto-tagged 🍜 กิน / 🛍️ ซื้อของ /
    🏃 ออกกำลังกาย / 📝 กิจวัตรประจำวัน by keyword match on the message text
  - Any image attachments are downloaded to `ψ/memory/logs/diary-photos/YYYY-MM-DD/` and
    linked from the diary entry

### Diary examples

| You type in Discord | Ayami logs |
|---|---|
| `บันทึก: กินก๋วยเตี๋ยวเจ๊หนึ่ง` | 🍜 กิน: กินก๋วยเตี๋ยวเจ๊หนึ่ง |
| `ไดอารี่ ซื้อของที่ตลาด` | 🛍️ ซื้อของ: ซื้อของที่ตลาด |
| photo of the gym + caption "เพิ่งวิ่งเสร็จ" | 🏃 ออกกำลังกาย: เพิ่งวิ่งเสร็จ + saved photo |
| any photo, no caption | 📝 กิจวัตรประจำวัน + saved photo |

### Real-trade log (separate from the market-backtester's paper-trading bot)

- Message starts with `บันทึกเทรด` / `เทรดจริง` / `log trade` (checked *before* the diary trigger, since "บันทึกเทรด" would otherwise also match the bare "บันทึก" diary prefix)
- Appends a timestamped line to `ψ/memory/logs/moss-real-trades.md` (gitignored, same `memory/logs/` rule as the diary) — logged **verbatim, not parsed into fields**, so a number can't get silently misparsed; Boss can summarize the raw file later if he wants totals
- Screenshot attachments (trade confirmations) download to `ψ/memory/logs/trade-photos/YYYY-MM-DD/`, same pattern as diary photos
- Example: `บันทึกเทรด: BTC เข้า 63000 ออก 65000 กำไร 2000` → `💰 เทรดจริง: BTC เข้า 63000 ออก 65000 กำไร 2000`
- This is **Boss's own real-money trades** — unrelated to `ψ/lab/market-backtester`'s automated $10 paper-trading loop on Railway, which tracks its own separate history in Redis/the dashboard
- **Also mirrors to the dashboard** (2026-08-15): after writing the local file, best-effort POSTs the same text (plus a loose keyword-guessed symbol, never a parsed number) to the market-backtester dashboard's `/api/log-real-trade` webhook — `TRADE_LOG_WEBHOOK_URL` + `TRADE_LOG_WEBHOOK_TOKEN` in `.env`. Lets the cloud dashboard show real trades next to paper-trading signals for manual comparison (its "Execution Tracker" section). If the webhook is unset or the network call fails, the local file write still succeeds — this is additive, not required.

### Quick-confirm reactions on trade signals (2026-08-17)

- `market-backtester`'s cron job posts fresh ENTER signals as their own Discord message
  (via `notify.py`, same bot token, REST API — not through this file's own `messageCreate`
  handler) containing a hidden `[trade-signal:SYMBOL:market:entry=...:stop=...:target=...:size=...]`
  marker. This bot auto-reacts ✅/❌ to any message it posted itself in `REPORT_CHANNEL_ID`
  matching that marker.
- Tapping ✅ logs "took this trade" exactly like typing `บันทึกเทรด` would (same file, same
  dashboard webhook mirror); tapping ❌ logs "skipped this signal" — see
  `appendReactionTradeEntry()`. Needs `GatewayIntentBits.GuildMessageReactions` +
  `Partials.Message/Reaction/Channel` (added 2026-08-17) since these messages arrive from a
  separate process and were never in this client's own gateway cache.
- **This never places a real order or holds a broker API key** — it only makes the *logging*
  step one tap instead of typing a message. Boss explicitly asked about full unattended
  auto-trading first; that was declined (a bot silently holding real trade-execution credentials
  removes the human from the loop entirely) — this is the safe version of the same request.

### Affiliate content drafts (2026-08-15) — Shopee affiliate MVP

- Message starts with `โปรโมท` / `affiliate` / `ขายของ` (colon or dash optional), followed by
  a product name/price and (ideally) a Shopee link. A product screenshot can be attached too.
- Niche is fixed in code (`AFFILIATE_NICHE` constant) at **Tech Desk Setup, ≤1,500 บาท/ชิ้น**
  — a deliberate MVP scope decision (requirement gate 2026-08-15), not a `.env` setting.
- Any URL in the message is extracted with a regex **before** the text goes to `agy`, and
  re-appended verbatim after the caption comes back — the LLM never sees or regenerates the
  link, so it can't hallucinate/mangle the affiliate URL and break commission attribution.
- `agy` returns both a Thai FB/IG-style caption (hook + benefit bullets + price + CTA +
  hashtags) and an English image-gen prompt in one call, parsed from a `CAPTION:` /
  `IMAGE_PROMPT:` format — one call keeps the image prompt grounded in the same product
  understanding as the caption, instead of a second guess.
- The image prompt is sent to **Pollinations.ai** (`image.pollinations.ai`, keyless, free —
  chosen 2026-08-15 for zero budget; commercial-use ToS for the free tier isn't fully clear,
  accepted as low risk at this personal/small-scale posting volume) to generate an
  **anime-style illustration** related to the product. Image generation is best-effort — a
  Pollinations failure never blocks the caption reply.
- Ayami replies in Discord with the ready-to-copy caption + the generated image attached —
  Boss copies both to Facebook/Instagram **manually**. No direct social API posting in this
  MVP (Meta requires Business verification + App Review, which needs real lead time — see
  requirement-gate notes 2026-08-15).
- Everything (raw product text, URL(s), caption, image path) is appended to
  `ψ/memory/logs/affiliate-drafts.md` (gitignored, same append-only pattern as diary/trade)
  and images saved to `ψ/memory/logs/affiliate-photos/YYYY-MM-DD/` — even if caption
  generation fails, the raw product text is still logged so nothing is lost.
- Example: `โปรโมท: คีย์บอร์ดไร้สาย Logitech K380 690 บาท https://shopee.co.th/xxx` → a Thai
  caption + anime-style desk-setup illustration + the same Shopee link re-attached verbatim.
- **Deferred to a later phase** (not built): automatic product discovery, a posting queue/
  schedule, direct FB/IG auto-posting, and custom click/earnings tracking (Shopee's own
  affiliate dashboard covers tracking for now).

#### Phase 1 — real product photo composited into the anime image (2026-08-15)

The raw anime illustration and the real product screenshot used to be two disconnected
images. If a product screenshot was attached, `sharp` now composites it — untouched, never
redrawn by an AI (a wrong-looking product photo would break affiliate trust) — into a white
rounded card with a soft drop-shadow, placed over the anime background. Pure local image
processing, zero extra API calls. Falls back to the plain anime image if there's no
screenshot attached, or if compositing fails.

#### Phase 2 — short video clip via local ffmpeg (2026-08-15)

Whichever still image comes out of Phase 1 (composite or plain anime) is turned into a
5-second 1080×1080 Ken Burns pan/zoom `.mp4` via a local `ffmpeg` call (`zoompan` filter,
`libx264`, `crf 28` — a few hundred KB, well under Discord's attachment limit). No cloud
text-to-video service — those need paid tiers, have watermarks/queues, and would blow the
zero-budget constraint. Best-effort like every other image step here: a failed clip never
blocks the caption+image reply. **`ffmpeg` must be reachable via `PATH` under launchd** —
same class of bug that broke `agy` (see the plist note below); already covered since the
`EnvironmentVariables/PATH` fix includes `/opt/homebrew/bin`, where Homebrew installs it.

## Setup — things only you can do (Discord account required)

1. Go to <https://discord.com/developers/applications> → **New Application**, name it
2. **Bot** tab → **Reset Token** → copy it immediately (shown once)
3. Same tab → enable **Privileged Gateway Intents** → turn on **Message Content Intent**
4. **OAuth2 → URL Generator** → scope `bot`, permissions `View Channels`, `Send Messages`
   → open the generated URL → invite the bot to your server
5. In Discord: **Settings → Advanced → Developer Mode** (turn on)
6. Right-click the one channel the bot should listen in → **Copy Channel ID**
7. Right-click your own name/avatar → **Copy User ID**

## Setup — the part I can do with you

```bash
cd ψ/lab/discord-bot
cp .env.example .env
# then fill in .env:
#   DISCORD_BOT_TOKEN  = token from step 2 above
#   ALLOWED_USERS      = your user ID from step 7
#   TEXT_CHANNEL_ID    = channel ID from step 6
npm install    # already done once, re-run if you clone fresh
node bot.mjs
```

If it starts correctly you'll see: `Ayami Discord bot online as <name> — listening in channel <id>`

## Running it persistently (launchd)

Running `node bot.mjs` in a terminal (even with `nohup`) doesn't survive the terminal/shell
session dying. For 24/7 uptime (so it's always reachable from Boss's phone), it's registered
as a `launchd` user agent instead:

```bash
# install / start (also runs automatically on every future login)
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.ayami.discord-bot.plist

# check status
launchctl print gui/$(id -u)/com.ayami.discord-bot | head -10

# stop + unregister
launchctl bootoff gui/$(id -u)/com.ayami.discord-bot   # or: launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.ayami.discord-bot.plist

# logs
tail -f ψ/lab/discord-bot/launchd.out.log   # stdout
tail -f ψ/lab/discord-bot/launchd.err.log   # stderr
```

The plist (`~/Library/LaunchAgents/com.ayami.discord-bot.plist`, outside this repo — it's a
per-machine system config, not project code) sets `RunAtLoad` (starts at login) and
`KeepAlive.SuccessfulExit=false` (auto-restarts only on crash, not after a clean exit). Uses
an absolute `node` path (`nvm`-installed, `which node` to find it on a new machine) since
`launchd` doesn't inherit your shell's `PATH`.

## `notify.mjs` — one-shot sends from other scripts/jobs

`bot.mjs` only reacts to Discord gateway events — it has no IPC, file-watcher, or polling loop, so an external script (e.g. another launchd job) can't ask the *running* bot process to send something. `notify.mjs` is the workaround: a separate, short-lived script that logs in with the same `DISCORD_BOT_TOKEN`, sends one message to `REPORT_CHANNEL_ID`, and disconnects — no changes to `bot.mjs`, no second always-on process.

```bash
echo "your message" | /path/to/nvm/node notify.mjs
```

First consumer: `ψ/lab/market-backtester/run_advise_paper.sh` pipes its twice-daily paper-trade check result through this. Reuse the same pattern for any other script that needs to post a result without becoming its own Discord bot.

## Safety notes (same standard as the rest of Ayami's tooling)

- `.env` holds the bot token — never commit it (`.gitignore` already excludes it). If it
  ever leaks, go back to the Bot tab and **Reset Token** immediately.
- `ALLOWED_USERS` is a hard allowlist — anyone not on it is ignored even in the same channel.
- The quick-brain runs `--mode plan` (read-only) always. It cannot edit files or run
  commands, and its persona explicitly forbids claiming work is done.
- Do not set `Administrator` on the bot's Discord permissions — the two scopes above are
  the only ones it needs.

## Next steps (not built yet, on request)

- Wire `FORWARD` replies to an actual running Claude Code session (the source guide uses
  `tmux send-keys` into a pane) instead of just telling the user it can't act yet
- Voice channel support (whisper.cpp STT + edge-tts TTS) — guide's Part 2
- Cross-restart memory, meeting-notes mode, scheduled check-ins — guide's Part 4
