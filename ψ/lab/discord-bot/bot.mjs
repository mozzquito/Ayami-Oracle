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
import { promises as fsp } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const execFileP = promisify(execFile)
const __dirname = path.dirname(fileURLToPath(import.meta.url))
// moss-life.md already exists as Boss's personal diary (ψ/memory/logs/, gitignored —
// see 2026-08-09 retro "moss-personal-life-diary"). Diary entries append here directly;
// this is the only write-capable path in the bot — everything else stays read-only.
const DIARY_PATH = path.join(__dirname, '../../memory/logs/moss-life.md')
const DIARY_PHOTOS_DIR = path.join(__dirname, '../../memory/logs/diary-photos')

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
// Prefix a message with one of these to log it to the diary explicitly. Messages with an
// image attachment are ALWAYS logged as diary entries too (sending a photo already signals
// "record this"), even without a prefix — see hasImageAttachment in messageCreate.
const DIARY_TRIGGER_RE = /^(บันทึก|ไดอารี่|diary)\s*[:\-]?\s*/i
const DIARY_CATEGORIES = [
  { emoji: '🍜', label: 'กิน', re: /กิน|ทาน|อาหาร|ข้าว|กาแฟ|ก๋วยเตี๋ยว|อร่อย/ },
  { emoji: '🛍️', label: 'ซื้อของ', re: /ซื้อ|ช้อป|shopping|จ่ายตลาด/ },
  { emoji: '🏃', label: 'ออกกำลังกาย', re: /ออกกำลังกาย|วิ่ง|ยิม|เวท|gym|workout|ปั่นจักรยาน/ },
]
const DIARY_DEFAULT_CATEGORY = { emoji: '📝', label: 'กิจวัตรประจำวัน' }

function categorizeDiaryText(text) {
  return DIARY_CATEGORIES.find((c) => c.re.test(text)) || DIARY_DEFAULT_CATEGORY
}

// Downloads any image attachments, appends one Markdown entry (timestamp, category, text,
// image links) to moss-life.md. This is the only place bot.mjs writes to disk.
async function appendDiaryEntry(msg, rawText) {
  const text = rawText.replace(DIARY_TRIGGER_RE, '').trim()
  const category = categorizeDiaryText(text)
  const now = new Date()
  const dateStr = now.toLocaleDateString('sv-SE', { timeZone: 'Asia/Bangkok' }) // YYYY-MM-DD
  const timeStr = now.toLocaleTimeString('th-TH', {
    timeZone: 'Asia/Bangkok', hour: '2-digit', minute: '2-digit', hour12: false,
  })

  const imageLines = []
  const imageAttachments = [...msg.attachments.values()].filter((a) => a.contentType?.startsWith('image/'))
  if (imageAttachments.length > 0) {
    const dayDir = path.join(DIARY_PHOTOS_DIR, dateStr)
    await fsp.mkdir(dayDir, { recursive: true })
    let i = 0
    for (const att of imageAttachments) {
      i += 1
      const ext = path.extname(att.name || '') || '.jpg'
      const fname = `${timeStr.replace(':', '')}-${i}${ext}`
      const res = await fetch(att.url)
      const buf = Buffer.from(await res.arrayBuffer())
      await fsp.writeFile(path.join(dayDir, fname), buf)
      imageLines.push(`  ![](diary-photos/${dateStr}/${fname})`)
    }
  }

  const line = `- **${timeStr}** ${category.emoji} ${category.label}${text ? `: ${text}` : ''}`
  await fsp.appendFile(DIARY_PATH, [line, ...imageLines].join('\n') + '\n')
  return { category, imageCount: imageLines.length }
}

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
  const hasImageAttachment = [...msg.attachments.values()].some((a) => a.contentType?.startsWith('image/'))

  if (!text && !hasImageAttachment) {
    console.log('[msg] empty content, no image attachment — Message Content Intent may not be enabled')
    return
  }

  if (hasImageAttachment || DIARY_TRIGGER_RE.test(text)) {
    try {
      const { category, imageCount } = await appendDiaryEntry(msg, text)
      await msg.reply(
        `บันทึกแล้วค่ะ ${category.emoji} ${category.label}${imageCount ? ` (แนบรูป ${imageCount} รูป)` : ''}`,
      )
    } catch (err) {
      console.error('diary error:', err)
      await msg.reply(`ขอโทษค่ะ บันทึกไม่สำเร็จ: ${err.message}`)
    }
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
