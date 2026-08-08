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
