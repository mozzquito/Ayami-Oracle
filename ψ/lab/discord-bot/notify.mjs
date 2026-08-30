// One-shot Discord sender for external scripts (e.g. market-backtester's paper-trade
// launchd job). Deliberately NOT part of bot.mjs's always-running gateway session —
// logs in, sends one message to REPORT_CHANNEL_ID, disconnects. Reuses the same bot
// token/channel as the "สรุปงาน" feature so notifications come from the same bot identity.
//
// Usage: echo "message text" | node notify.mjs
//        echo "message text" | node notify.mjs /path/to/image.jpg   # attach an image too

import 'dotenv/config'
import { Client, GatewayIntentBits, Events, AttachmentBuilder } from 'discord.js'

const imagePath = process.argv[2] || null

const { DISCORD_BOT_TOKEN, REPORT_CHANNEL_ID } = process.env

if (!DISCORD_BOT_TOKEN || !REPORT_CHANNEL_ID || REPORT_CHANNEL_ID === 'xxx') {
  console.error('notify.mjs: DISCORD_BOT_TOKEN / REPORT_CHANNEL_ID not configured in .env')
  process.exit(1)
}

let input = ''
process.stdin.setEncoding('utf8')
for await (const chunk of process.stdin) input += chunk
input = input.trim()

if (!input) {
  console.error('notify.mjs: nothing on stdin, nothing to send')
  process.exit(0)
}

const DISCORD_MAX_LEN = 2000
const FENCE = '```\n'
const budget = DISCORD_MAX_LEN - FENCE.length - '\n```'.length
const body = input.length > budget ? input.slice(0, budget - 20) + '\n… (truncated)' : input

const client = new Client({ intents: [GatewayIntentBits.Guilds] })

client.once(Events.ClientReady, async () => {
  try {
    const channel = await client.channels.fetch(REPORT_CHANNEL_ID)
    const payload = { content: FENCE + body + '\n```' }
    if (imagePath) payload.files = [new AttachmentBuilder(imagePath)]
    await channel.send(payload)
  } catch (err) {
    console.error('notify.mjs: send failed —', err.message)
    process.exitCode = 1
  } finally {
    client.destroy()
  }
})

client.login(DISCORD_BOT_TOKEN).catch((err) => {
  console.error('notify.mjs: login failed —', err.message)
  process.exit(1)
})
