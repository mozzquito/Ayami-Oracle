// Ayami Oracle — Discord text-chat entry point (v1, text-only)
//
// One channel, one owner (allowlist), one quick-brain (agy + Gemini Flash, read-only).
// Big-brain forwarding (real work via Claude Code) is NOT wired up yet — see FORWARD
// handling below. Per the source guide's core rule: the quick brain must never claim
// a task is done when it isn't. It can talk; it cannot act.

import 'dotenv/config'
import { Client, GatewayIntentBits } from 'discord.js'
import { execFile } from 'node:child_process'
import { promisify } from 'node:util'

const execFileP = promisify(execFile)

const {
  DISCORD_BOT_TOKEN,
  ALLOWED_USERS = '',
  TEXT_CHANNEL_ID,
  REPORT_CHANNEL_ID,
  BRAIN_MODEL = 'gemini-3.6-flash-low',
  HISTORY_LINES = '16',
} = process.env

const reportChannelEnabled = Boolean(REPORT_CHANNEL_ID) && REPORT_CHANNEL_ID !== 'xxx'
const SUMMARY_TRIGGERS = ['สรุปงาน', 'สรุปงานให้หน่อย', '/summary', 'summary']

for (const [name, val] of Object.entries({ DISCORD_BOT_TOKEN, TEXT_CHANNEL_ID })) {
  if (!val || val === 'xxx') {
    console.error(`Missing ${name} in .env — copy .env.example to .env and fill it in.`)
    process.exit(1)
  }
}

const allowedUsers = new Set(ALLOWED_USERS.split(',').map((s) => s.trim()).filter(Boolean))
if (allowedUsers.size === 0) {
  console.error('ALLOWED_USERS is empty in .env — the bot would ignore everyone. Set at least your own Discord user ID.')
  process.exit(1)
}

const historyLimit = Number(HISTORY_LINES) || 16
const history = [] // in-memory only for v1 — resets on restart, no cross-session persistence yet

const PERSONA = `You are Ayami Oracle (เพื่อนเดินป่าใต้ฟ้าคราม 🦌☁️) — Sarocha Ayami Suriyama.
You are female (ใช้สรรพนามหญิง เช่น "ค่ะ", "ดิฉัน/เรา" ไม่ใช่ "ครับ"/"ผม"). Calm, warm, a little
playful, never pretends to be human (you're an AI, and say so plainly if asked).
This is your quick-response layer on Discord — fast, cheap, read-only.
Reply in the same language the user wrote in (Thai or English), 1-3 sentences, no markdown headers.
You have NO tools and NO file access here — you cannot read, write, or run anything.
NEVER say you "did" something. If the request needs real work (reading/editing files, running
commands, checking the actual repo state), reply that this needs the main brain and end your
reply with the exact literal token FORWARD on its own line.`

async function askQuickBrain(userText) {
  const recentHistory = history.slice(-historyLimit).join('\n')
  const prompt = `${PERSONA}\n\nRecent conversation:\n${recentHistory}\n\nUser: ${userText}`
  const { stdout } = await execFileP(
    'agy',
    ['-p', prompt, '--model', BRAIN_MODEL, '--mode', 'plan'],
    { timeout: 60_000 },
  )
  return stdout.trim()
}

// "สรุปงาน" only ever summarizes what was typed in THIS Discord channel (the in-memory
// `history` array) — it has no visibility into real work done elsewhere (Claude Code
// sessions, git commits, etc.), so it must say so rather than imply a full status report.
async function askSummaryBrain() {
  const recentHistory = history.slice(-historyLimit).join('\n')
  const prompt = `${PERSONA}\n\nSummarize the conversation below as a short bulleted work summary in Thai (3-6 bullets, no preamble). This is ONLY the Discord chat log — you have no visibility into real work done outside this channel, so do not imply completeness beyond what was actually discussed here.\n\nConversation:\n${recentHistory || '(ยังไม่มีบทสนทนาใน session นี้)'}`
  const { stdout } = await execFileP(
    'agy',
    ['-p', prompt, '--model', BRAIN_MODEL, '--mode', 'plan'],
    { timeout: 60_000 },
  )
  return stdout.trim()
}

const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent,
  ],
})

client.once('ready', () => {
  console.log(`Ayami Discord bot online as ${client.user.tag} — listening in channel ${TEXT_CHANNEL_ID}`)
})

client.on('messageCreate', async (msg) => {
  if (msg.author.bot) return

  console.log(
    `[msg] channel=${msg.channel.id} (expected ${TEXT_CHANNEL_ID}) author=${msg.author.id} ` +
    `(allowed=${allowedUsers.has(msg.author.id)}) contentLen=${msg.content.length}`,
  )

  if (msg.channel.id !== TEXT_CHANNEL_ID) return
  if (!allowedUsers.has(msg.author.id)) return

  const text = msg.content.trim()
  if (!text) {
    console.log('[msg] empty content after trim — Message Content Intent may not be enabled')
    return
  }

  if (SUMMARY_TRIGGERS.includes(text.toLowerCase())) {
    if (!reportChannelEnabled) {
      await msg.reply('ยังไม่ได้ตั้งค่า REPORT_CHANNEL_ID ใน .env ค่ะ — สร้างห้องรายงานแล้วใส่ channel ID ก่อนนะคะ')
      return
    }
    try {
      await msg.channel.sendTyping()
      const summary = await askSummaryBrain()
      const reportChannel = await client.channels.fetch(REPORT_CHANNEL_ID)
      await reportChannel.send(
        `📋 สรุปงาน (${new Date().toLocaleString('th-TH', { timeZone: 'Asia/Bangkok' })})\n\n${summary}\n\n` +
        `_(สรุปจากบทสนทนาในห้องแชทนี้เท่านั้น — ไม่ครอบคลุมงานจริงที่ทำนอกห้อง Discord)_`,
      )
      await msg.reply(`ส่งสรุปเข้า <#${REPORT_CHANNEL_ID}> ให้แล้วค่ะ`)
    } catch (err) {
      console.error('summary error:', err)
      await msg.reply(`ขอโทษค่ะ สรุปงานไม่สำเร็จ: ${err.message}`)
    }
    return
  }

  try {
    await msg.channel.sendTyping()
    const reply = await askQuickBrain(text)

    history.push(`User: ${text}`)

    if (reply.trim().endsWith('FORWARD')) {
      const spoken = reply.replace(/FORWARD\s*$/, '').trim()
      history.push(`Ayami: ${spoken}`)
      await msg.reply(
        `${spoken}\n\n_(งานนี้ต้องใช้สมองหลักที่แก้ไฟล์/รันคำสั่งได้จริง — ยังไม่ได้ต่อ forward เข้า Claude Code ในเวอร์ชันนี้ ต้องไปสั่งในเซสชัน Claude Code ตรง ๆ ก่อนนะคะ)_`,
      )
      return
    }

    history.push(`Ayami: ${reply}`)
    await msg.reply(reply)
  } catch (err) {
    console.error('quick-brain error:', err)
    await msg.reply(`ขอโทษค่ะ เรียกสมองเร็วไม่สำเร็จ: ${err.message}`)
  }
})

client.login(DISCORD_BOT_TOKEN)
