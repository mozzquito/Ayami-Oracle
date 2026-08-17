// Ayami Oracle — Discord text-chat entry point (v1, text-only)
//
// One channel, one owner (allowlist), one quick-brain (agy + Gemini Flash, read-only).
// Big-brain forwarding (real work via Claude Code) is NOT wired up yet — see FORWARD
// handling below. Per the source guide's core rule: the quick brain must never claim
// a task is done when it isn't. It can talk; it cannot act.

import 'dotenv/config'
import { Client, GatewayIntentBits, Partials, AttachmentBuilder } from 'discord.js'
import { execFile } from 'node:child_process'
import { promisify } from 'node:util'
import { promises as fsp } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import sharp from 'sharp'

const execFileP = promisify(execFile)
const __dirname = path.dirname(fileURLToPath(import.meta.url))
// moss-life.md already exists as Boss's personal diary (ψ/memory/logs/, gitignored —
// see 2026-08-09 retro "moss-personal-life-diary"). Diary entries append here directly;
// this is the only write-capable path in the bot — everything else stays read-only.
const DIARY_PATH = path.join(__dirname, '../../memory/logs/moss-life.md')
const DIARY_PHOTOS_DIR = path.join(__dirname, '../../memory/logs/diary-photos')
// Real-money trade log — separate from the market-backtester's paper-trading simulation.
// Same gitignored memory/logs/ location and append-only pattern as the diary.
const TRADE_PATH = path.join(__dirname, '../../memory/logs/moss-real-trades.md')
const TRADE_PHOTOS_DIR = path.join(__dirname, '../../memory/logs/trade-photos')
// Shopee affiliate content drafts — same gitignored append-only pattern as diary/trade.
const AFFILIATE_PATH = path.join(__dirname, '../../memory/logs/affiliate-drafts.md')
const AFFILIATE_PHOTOS_DIR = path.join(__dirname, '../../memory/logs/affiliate-photos')

const {
  DISCORD_BOT_TOKEN,
  ALLOWED_USERS = '',
  TEXT_CHANNEL_ID,
  REPORT_CHANNEL_ID,
  BRAIN_MODEL = 'gemini-3.6-flash-low',
  HISTORY_LINES = '16',
  TRADE_LOG_WEBHOOK_URL,
  TRADE_LOG_WEBHOOK_TOKEN,
  PEXELS_API_KEY,
} = process.env

// Same watchlist as ψ/lab/market-backtester/backtester/cloud_run.py's SYMBOLS — kept as a
// plain list here rather than importing across languages. A loose substring match on the
// message text, purely to help eyeball real-vs-paper trades on the dashboard side by side;
// never used for anything numeric.
const KNOWN_SYMBOLS = ['BTC', 'ETH', 'SOL', 'TRX', 'BNB', 'NEAR', 'EURUSD', 'GBPUSD', 'AUDUSD']
function guessSymbol(text) {
  const upper = text.toUpperCase()
  return KNOWN_SYMBOLS.find((s) => upper.includes(s)) || null
}

// Mirrors a real-trade log entry to the dashboard's Redis via its webhook, so the
// cloud-hosted dashboard (no access to this Mac's local filesystem) can show something
// about Boss's real trades next to the paper-trading signals. Best-effort: the local
// moss-real-trades.md write already happened by the time this runs, so a webhook/network
// failure here must never surface as "your trade didn't get logged."
async function pushTradeToWebhook(text, symbolHint) {
  if (!TRADE_LOG_WEBHOOK_URL || !TRADE_LOG_WEBHOOK_TOKEN) return
  try {
    const res = await fetch(TRADE_LOG_WEBHOOK_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${TRADE_LOG_WEBHOOK_TOKEN}` },
      body: JSON.stringify({ text, symbol_hint: symbolHint }),
      signal: AbortSignal.timeout(5000),
    })
    if (!res.ok) console.error(`trade webhook responded ${res.status} (non-fatal)`)
  } catch (err) {
    console.error('trade webhook push failed (non-fatal):', err.message)
  }
}

const reportChannelEnabled = Boolean(REPORT_CHANNEL_ID) && REPORT_CHANNEL_ID !== 'xxx'
const SUMMARY_TRIGGERS = ['สรุปงาน', 'สรุปงานให้หน่อย', '/summary', 'summary']
// Prefix a message with one of these to log it to the diary explicitly. Messages with an
// image attachment are ALWAYS logged as diary entries too (sending a photo already signals
// "record this"), even without a prefix — see hasImageAttachment in messageCreate.
const DIARY_TRIGGER_RE = /^(บันทึก|ไดอารี่|diary)\s*[:\-：]?\s*/i
// Checked BEFORE DIARY_TRIGGER_RE in the handler — "บันทึกเทรด" would otherwise also match
// the bare "บันทึก" diary trigger and get misfiled as a generic diary entry.
const TRADE_TRIGGER_RE = /^(บันทึกเทรด|เทรดจริง|log\s*trade)\s*[:\-：]?\s*/i
// Checked BEFORE DIARY_TRIGGER_RE too — an affiliate message with a product screenshot
// attached would otherwise get swallowed by the "any photo = diary entry" rule.
const AFFILIATE_TRIGGER_RE = /^(โปรโมท|affiliate|ขายของ)\s*[:\-：]?\s*/i
// Machine-readable marker market-backtester's advisor.py embeds in a real ENTER-signal
// Discord message (see backtester/advisor.py's _quick_action_link + the [trade-signal:...]
// line). Lets the bot parse structured fields back out of plain message text instead of
// requiring a second data channel — one message, one marker, one unambiguous reaction target
// (cloud_run.py sends each entry as its own message specifically so this holds).
const TRADE_SIGNAL_RE = /\[trade-signal:([A-Z]+):(\w+):entry=([\d.]+):stop=([\d.]+|none):target=([\d.]+|none):size=([\d.]+)\]/
// Strips invisible Unicode that Thai mobile IMEs sometimes inject (ZWJ, variation
// selectors, zero-width spaces, etc.). Applied ONCE before all trigger checks so
// no invisible prefix can dodge the ^ anchor.
function stripInvisiblePrefix(s) {
  return s.replace(/^[\u200B\u200C\u200D\uFEFF\u200E\u200F\u2060\u2061\u2062\u2063\u2064]+/, '')
}
const URL_RE = /https?:\/\/\S+/g
// Fixed MVP niche (2026-08-15 requirement gate) — hardcoded like PERSONA rather than an
// env var, since changing niche is a deliberate product decision, not per-deploy config.
const AFFILIATE_NICHE = 'อุปกรณ์โต๊ะทำงานสายเทค (Tech Desk Setup) งบไม่เกิน 1,500 บาทต่อชิ้น — คีย์บอร์ด, ที่ชาร์จ, แขนจับจอ, สายเคเบิล, อุปกรณ์จัดโต๊ะ'
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

// Logs Boss's own real-money trades — deliberately NOT parsed into structured fields (symbol,
// price, pnl). Free-form text logged verbatim, same as the diary: simpler, can't misparse a
// number wrong, and Boss can review/summarize the raw file later if he wants totals. Supports
// screenshot attachments (trade confirmations) the same way the diary supports photos.
async function appendTradeEntry(msg, rawText) {
  const text = rawText.replace(TRADE_TRIGGER_RE, '').trim()
  const now = new Date()
  const dateStr = now.toLocaleDateString('sv-SE', { timeZone: 'Asia/Bangkok' })
  const timeStr = now.toLocaleTimeString('th-TH', {
    timeZone: 'Asia/Bangkok', hour: '2-digit', minute: '2-digit', hour12: false,
  })

  const imageLines = []
  const imageAttachments = [...msg.attachments.values()].filter((a) => a.contentType?.startsWith('image/'))
  if (imageAttachments.length > 0) {
    const dayDir = path.join(TRADE_PHOTOS_DIR, dateStr)
    await fsp.mkdir(dayDir, { recursive: true })
    let i = 0
    for (const att of imageAttachments) {
      i += 1
      const ext = path.extname(att.name || '') || '.jpg'
      const fname = `${timeStr.replace(':', '')}-${i}${ext}`
      const res = await fetch(att.url)
      const buf = Buffer.from(await res.arrayBuffer())
      await fsp.writeFile(path.join(dayDir, fname), buf)
      imageLines.push(`  ![](trade-photos/${dateStr}/${fname})`)
    }
  }

  const line = `- **${timeStr}** 💰 เทรดจริง${text ? `: ${text}` : ''}`
  await fsp.appendFile(TRADE_PATH, [line, ...imageLines].join('\n') + '\n')

  if (text) await pushTradeToWebhook(text, guessSymbol(text))

  return { imageCount: imageLines.length }
}

// Quick-confirm flow (2026-08-17): reacting ✅/❌ on a market-backtester ENTER-signal
// message logs it exactly like typing "บันทึกเทรด ..." would, just one tap instead of
// typing. This ONLY logs intent — it never touches a broker API or places any order; the
// human still does that themselves on Binance/Exness (see the 🔗 link in the signal
// message). Reuses the same append-only log + webhook bridge as the manual trade trigger.
async function appendReactionTradeEntry(signal, confirmed) {
  const now = new Date()
  const dateStr = now.toLocaleDateString('sv-SE', { timeZone: 'Asia/Bangkok' })
  const timeStr = now.toLocaleTimeString('th-TH', {
    timeZone: 'Asia/Bangkok', hour: '2-digit', minute: '2-digit', hour12: false,
  })
  const detail = `${signal.symbol} (${signal.market}) entry=${signal.entry}` +
    (signal.stop !== 'none' ? ` stop=${signal.stop}` : '') +
    (signal.target !== 'none' ? ` target=${signal.target}` : '') +
    ` size=${signal.size}`
  const status = confirmed ? '💰 เทรดจริง (ยืนยันผ่าน reaction ✅)' : '⏭️ ข้ามสัญญาณ (reaction ❌)'
  const line = `- **${timeStr}** ${status}: ${detail}`
  await fsp.appendFile(TRADE_PATH, line + '\n')
  if (confirmed) await pushTradeToWebhook(detail, signal.symbol)
}

// agy is asked for TWO things in one call (caption + an English Pexels search query) rather
// than two separate calls, so the search keywords stay consistent with what the model
// itself understood the product to be, instead of a second crude regex-based guess.
const AFFILIATE_PROMPT_TEMPLATE = (productText) => `You are Ayami Oracle, writing a Thai Facebook/Instagram promotional caption for a Shopee affiliate post. You are female — use female Thai particles/pronouns ("ค่ะ", "นะคะ", "เรา"), NEVER "ครับ"/"ผม". Usual niche: ${AFFILIATE_NICHE} — but write about whatever product the human actually gives you below, even if it's outside that niche; never force-fit an unrelated product into the niche framing.

Product info from the human:
${productText}

CRITICAL: NEVER invent a price. Only state a price if a number is explicitly present in the
product info above. If no price is given, omit the price line entirely (or write "ราคาดูในลิงก์ค่ะ")
— do NOT reuse the niche's budget ceiling or any other number as if it were this product's price.

Reply in EXACTLY this format, nothing else before or after:
CAPTION:
<Thai caption, 1 hook line + 2-4 benefit bullets + a call-to-action + 2-4 hashtags, and a price line ONLY if a real price was given above. No markdown headers, no code fences.>
SEARCH_QUERY:
<one line, English, 3-6 keywords for a stock photo/video library search. Describe a real person actually using a product like this (e.g. "person typing wireless keyboard desk"). No brand names, no Thai text.>`

async function askAffiliateBrain(productText) {
  const { stdout } = await execFileP(
    'agy',
    ['-p', AFFILIATE_PROMPT_TEMPLATE(productText), '--model', BRAIN_MODEL, '--mode', 'plan'],
    { timeout: 60_000 },
  )
  const raw = stdout.trim()
  const captionMatch = raw.match(/CAPTION:\s*([\s\S]*?)\s*SEARCH_QUERY:/i)
  const searchQueryMatch = raw.match(/SEARCH_QUERY:\s*([\s\S]*)$/i)
  // agy occasionally misreads a content-writing request as a CODING task and drafts an
  // "implementation plan" artifact instead of just answering (observed 2026-08-15 — asked
  // for an approval that a one-shot non-interactive call can never give). If the expected
  // CAPTION:/SEARCH_QUERY: markers aren't both present, this is NOT a usable caption — fail
  // loudly instead of silently shipping whatever agy said as if it were the real caption.
  if (!captionMatch || !searchQueryMatch) {
    throw new Error('agy ตอบไม่ตรงรูปแบบที่ต้องการ (อาจไปตีความเป็นงาน coding แทนที่จะตอบตรงๆ) ลองใหม่อีกทีนะคะ')
  }
  const caption = captionMatch[1].trim()
  const searchQuery = searchQueryMatch[1].trim()
  // Markers-present isn't proof of REAL content — agy has also echoed the prompt's own
  // placeholder text back verbatim (observed 2026-08-16: literally "<Thai caption...>"
  // instead of an actual caption). A genuine caption is Thai prose; it never starts with
  // "<" or contains the template's own instruction wording.
  const looksLikeEchoedPlaceholder =
    caption.startsWith('<') || /thai caption|hook line|benefit bullet/i.test(caption) || caption.length < 15
  if (looksLikeEchoedPlaceholder) {
    throw new Error('agy ตอบเป็น placeholder ไม่ใช่แคปชันจริง ลองใหม่อีกทีนะคะ')
  }
  return { caption, searchQuery }
}

// Real stock photo of a real person, via Pexels (free API key, no anime/AI-art — replaced
// 2026-08-15 per requirement change). Picks the first search result; best-effort like every
// other image step here — a search/download failure never blocks the caption reply.
async function searchPexelsPhoto(query, dayDir, filenameBase) {
  if (!PEXELS_API_KEY || PEXELS_API_KEY === 'xxx') throw new Error('PEXELS_API_KEY not set in .env')
  const searchRes = await fetch(
    `https://api.pexels.com/v1/search?query=${encodeURIComponent(query)}&per_page=5&orientation=square`,
    { headers: { Authorization: PEXELS_API_KEY }, signal: AbortSignal.timeout(20_000) },
  )
  if (!searchRes.ok) throw new Error(`pexels photo search responded ${searchRes.status}`)
  const data = await searchRes.json()
  const photo = data.photos?.[0]
  if (!photo) throw new Error(`no stock photo found for "${query}"`)

  const imgRes = await fetch(photo.src.large, { signal: AbortSignal.timeout(30_000) })
  if (!imgRes.ok) throw new Error(`pexels photo download responded ${imgRes.status}`)
  const buf = Buffer.from(await imgRes.arrayBuffer())
  await fsp.mkdir(dayDir, { recursive: true })
  const fname = `${filenameBase}-stock.jpg`
  await fsp.writeFile(path.join(dayDir, fname), buf)
  return { buf, fname, credit: `Photo by ${photo.photographer} on Pexels` }
}

// Real stock video clip, same Pexels source/key as the photo search. Picks the smallest
// file at least 480px wide (keeps Discord attachment size small) rather than the largest,
// since this is a short social-media clip, not archival footage.
async function searchPexelsVideo(query, dayDir, filenameBase) {
  if (!PEXELS_API_KEY || PEXELS_API_KEY === 'xxx') throw new Error('PEXELS_API_KEY not set in .env')
  const searchRes = await fetch(
    `https://api.pexels.com/videos/search?query=${encodeURIComponent(query)}&per_page=5&orientation=square`,
    { headers: { Authorization: PEXELS_API_KEY }, signal: AbortSignal.timeout(20_000) },
  )
  if (!searchRes.ok) throw new Error(`pexels video search responded ${searchRes.status}`)
  const data = await searchRes.json()
  const video = data.videos?.[0]
  if (!video) throw new Error(`no stock video found for "${query}"`)

  const files = [...(video.video_files || [])].sort((a, b) => (a.width || 0) - (b.width || 0))
  const file = files.find((f) => f.width && f.width >= 480) || files[files.length - 1]
  if (!file) throw new Error('stock video result had no usable file')

  const vidRes = await fetch(file.link, { signal: AbortSignal.timeout(45_000) })
  if (!vidRes.ok) throw new Error(`pexels video download responded ${vidRes.status}`)
  const buf = Buffer.from(await vidRes.arrayBuffer())
  await fsp.mkdir(dayDir, { recursive: true })
  const fname = `${filenameBase}-stock.mp4`
  await fsp.writeFile(path.join(dayDir, fname), buf)
  return { buf, fname, credit: `Video by ${video.user?.name || 'unknown'} on Pexels` }
}

// Composites the REAL product photo (untouched, never redrawn by an AI — a Shopee affiliate
// post showing the wrong product ruins trust) into a framed card over the anime background,
// so the two images read as one picture instead of two disconnected ones. Pure local image
// processing (sharp), zero extra API calls. Prototyped and visually checked 2026-08-15.
async function compositeAffiliateImage(animeBuf, screenshotBuf) {
  const CANVAS = 1080
  const FRAME = 460 // product-photo square size
  const PAD = 20 // white padding between photo and card edge
  const RADIUS = 24
  const MARGIN = 24 // extra canvas room so the drop-shadow isn't clipped
  const RECT = FRAME + PAD * 2
  const CARD_CANVAS = RECT + MARGIN * 2

  const background = await sharp(animeBuf).resize(CANVAS, CANVAS, { fit: 'cover' }).toBuffer()

  const roundedMask = Buffer.from(
    `<svg width="${FRAME}" height="${FRAME}"><rect width="${FRAME}" height="${FRAME}" rx="${RADIUS}" ry="${RADIUS}"/></svg>`,
  )
  const roundedPhoto = await sharp(screenshotBuf)
    .resize(FRAME, FRAME, { fit: 'cover' })
    .composite([{ input: roundedMask, blend: 'dest-in' }])
    .png()
    .toBuffer()

  const cardSvg = `<svg width="${CARD_CANVAS}" height="${CARD_CANVAS}" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <filter id="shadow" x="-50%" y="-50%" width="200%" height="200%">
        <feDropShadow dx="0" dy="6" stdDeviation="10" flood-color="black" flood-opacity="0.45"/>
      </filter>
    </defs>
    <rect x="${MARGIN}" y="${MARGIN}" width="${RECT}" height="${RECT}" rx="${RADIUS + 10}" fill="white" filter="url(#shadow)"/>
  </svg>`
  const card = await sharp(Buffer.from(cardSvg))
    .composite([{ input: roundedPhoto, top: MARGIN + PAD, left: MARGIN + PAD }])
    .png()
    .toBuffer()

  return sharp(background).composite([{ input: card, gravity: 'south' }]).jpeg({ quality: 90 }).toBuffer()
}

// Extracts product URL(s) from the raw message BEFORE anything is sent to agy, and the
// verbatim string is re-appended after the AI caption comes back — the LLM never sees or
// regenerates the link, so a hallucinated/mangled URL can never break commission attribution.
function extractProductUrls(text) {
  return [...text.matchAll(URL_RE)].map((m) => m[0])
}

async function appendAffiliateDraft(msg, rawText) {
  const stripped = rawText.replace(AFFILIATE_TRIGGER_RE, '').trim()
  const urls = extractProductUrls(stripped)
  const productText = stripped.replace(URL_RE, '').trim()
  const now = new Date()
  const dateStr = now.toLocaleDateString('sv-SE', { timeZone: 'Asia/Bangkok' })
  const timeStr = now.toLocaleTimeString('th-TH', {
    timeZone: 'Asia/Bangkok', hour: '2-digit', minute: '2-digit', hour12: false,
  })
  const dayDir = path.join(AFFILIATE_PHOTOS_DIR, dateStr)

  // Product screenshot attachment (optional), same download pattern as diary/trade. The
  // FIRST screenshot's buffer is kept in memory (not just written to disk) so it can be
  // composited with the anime background below.
  const screenshotLines = []
  let firstScreenshotBuf = null
  const imageAttachments = [...msg.attachments.values()].filter((a) => a.contentType?.startsWith('image/'))
  if (imageAttachments.length > 0) {
    await fsp.mkdir(dayDir, { recursive: true })
    let i = 0
    for (const att of imageAttachments) {
      i += 1
      const ext = path.extname(att.name || '') || '.jpg'
      const fname = `${timeStr.replace(':', '')}-screenshot-${i}${ext}`
      const res = await fetch(att.url)
      const buf = Buffer.from(await res.arrayBuffer())
      if (i === 1) firstScreenshotBuf = buf
      await fsp.writeFile(path.join(dayDir, fname), buf)
      screenshotLines.push(`  ![](affiliate-photos/${dateStr}/${fname})`)
    }
  }

  let caption, searchQuery
  try {
    // One silent retry: agy has twice (2026-08-15/16) misfired on this structured-output
    // task in ways plain format-checking catches (a coding "implementation plan" instead
    // of an answer; the prompt's own placeholder echoed back) — both looked like one-off
    // model flukes on retry, not a persistent failure, so retry once before giving up
    // rather than making มอส manually resend the whole message for a transient glitch.
    let brainResult
    try {
      brainResult = await askAffiliateBrain(productText)
    } catch (firstErr) {
      console.error('affiliate brain first attempt failed, retrying once:', firstErr.message)
      brainResult = await askAffiliateBrain(productText)
    }
    caption = brainResult.caption
    searchQuery = brainResult.searchQuery
  } catch (err) {
    // Caption generation failed — still log the raw product text so it isn't lost
    // (Nothing is Deleted), then rethrow so the caller can tell the user honestly.
    const failLine = `- **${timeStr}** 🛒 [แคปชันสร้างไม่สำเร็จ] ${productText}${urls.length ? ` — ${urls.join(', ')}` : ''}`
    await fsp.appendFile(AFFILIATE_PATH, [failLine, ...screenshotLines].join('\n') + '\n')
    throw err
  }

  const urlNote = urls.length === 0
    ? '⚠️ ยังไม่มีลิงก์ Shopee นะคะ — ใส่ลิงก์ก่อนโพสต์จริงด้วย'
    : `🔗 ${urls[0]}`
  const extraUrlWarning = urls.length > 1
    ? `\n(เจอลิงก์ ${urls.length} อัน ใช้อันแรกให้ค่ะ ที่เหลือ: ${urls.slice(1).join(', ')})`
    : ''
  const draft = `${caption}\n\n${urlNote}${extraUrlWarning}`

  // Real stock photo of a real person using something like this product (2026-08-15,
  // replaced the earlier anime-image approach per requirement change). Best-effort — a
  // Pexels failure never blocks the caption reply.
  let stockPhoto = null
  if (searchQuery) {
    try {
      stockPhoto = await searchPexelsPhoto(searchQuery, dayDir, timeStr.replace(':', ''))
    } catch (err) {
      console.error('affiliate stock photo search failed (non-fatal):', err.message)
    }
  }

  // Phase 1 (2026-08-15): composite the real product photo over the real stock-photo
  // background into one cohesive image. Falls back to the plain stock photo if there's no
  // screenshot, or if compositing fails — never blocks the reply.
  let finalImage = stockPhoto
  if (stockPhoto && firstScreenshotBuf) {
    try {
      const compositeBuf = await compositeAffiliateImage(stockPhoto.buf, firstScreenshotBuf)
      const compositeFname = `${timeStr.replace(':', '')}-composite.jpg`
      await fsp.writeFile(path.join(dayDir, compositeFname), compositeBuf)
      finalImage = { buf: compositeBuf, fname: compositeFname, credit: stockPhoto.credit }
    } catch (err) {
      console.error('affiliate composite failed (non-fatal):', err.message)
    }
  }

  // Phase 2 (2026-08-15): a real stock video clip of a real person, same Pexels source as
  // the photo — replaced the earlier synthetic ffmpeg Ken Burns zoom. Best-effort.
  let clip = null
  if (searchQuery) {
    try {
      clip = await searchPexelsVideo(searchQuery, dayDir, timeStr.replace(':', ''))
    } catch (err) {
      console.error('affiliate stock video search failed (non-fatal):', err.message)
    }
  }

  const imageLines = [...screenshotLines]
  if (finalImage) {
    imageLines.push(`  ![](affiliate-photos/${dateStr}/${finalImage.fname})`)
    if (finalImage.credit) imageLines.push(`  (${finalImage.credit})`)
  }
  if (clip) {
    imageLines.push(`  [clip](affiliate-photos/${dateStr}/${clip.fname})`)
    if (clip.credit) imageLines.push(`  (${clip.credit})`)
  }
  const logLine = `- **${timeStr}** 🛒 ${productText}${urls.length ? ` — ${urls.join(', ')}` : ' (ไม่มีลิงก์)'}\n  > ${draft.replace(/\n/g, '\n  > ')}`
  await fsp.appendFile(AFFILIATE_PATH, [logLine, ...imageLines].join('\n') + '\n')

  return { draft, image: finalImage, clip }
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
    GatewayIntentBits.GuildMessageReactions,
  ],
  // Reactions/messages arrive as "partial" when they weren't already in the gateway
  // cache — which is always true for the trade-signal messages, since notify.py (a
  // separate Python process) posts them via raw REST using the same bot token, so this
  // client never saw the messageCreate event that "should" have cached them. Without
  // partials enabled, reaction events on those messages would be silently dropped.
  partials: [Partials.Message, Partials.Reaction, Partials.Channel],
})

client.once('ready', () => {
  console.log(`Ayami Discord bot online as ${client.user.tag} — listening in channel ${TEXT_CHANNEL_ID}`)
})

client.on('messageCreate', async (msg) => {
  if (msg.author.bot) {
    // Pre-add the ✅/❌ reactions on the bot's own trade-signal messages (posted by
    // notify.py via REST using the same token) so มอส has something to tap immediately
    // instead of hunting for the right emoji. Only in the report channel — never reacts
    // to arbitrary bot messages elsewhere.
    if (
      msg.author.id === client.user.id &&
      reportChannelEnabled &&
      msg.channel.id === REPORT_CHANNEL_ID &&
      TRADE_SIGNAL_RE.test(msg.content)
    ) {
      try {
        await msg.react('✅')
        await msg.react('❌')
      } catch (err) {
        console.error('failed to pre-add trade-signal reactions (non-fatal):', err.message)
      }
    }
    return
  }

  console.log(
    `[msg] channel=${msg.channel.id} (expected ${TEXT_CHANNEL_ID}) author=${msg.author.id} ` +
    `(allowed=${allowedUsers.has(msg.author.id)}) contentLen=${msg.content.length}`,
  )

  if (msg.channel.id !== TEXT_CHANNEL_ID) return
  if (!allowedUsers.has(msg.author.id)) return

  let text = msg.content.trim()
  text = stripInvisiblePrefix(text)
  const hasImageAttachment = [...msg.attachments.values()].some((a) => a.contentType?.startsWith('image/'))

  if (!text && !hasImageAttachment) {
    console.log('[msg] empty content, no image attachment — Message Content Intent may not be enabled')
    return
  }

  if (TRADE_TRIGGER_RE.test(text)) {
    console.log('[trigger] category=trade')
    try {
      const { imageCount } = await appendTradeEntry(msg, text)
      await msg.reply(`บันทึกเทรดแล้วค่ะ 💰${imageCount ? ` (แนบรูป ${imageCount} รูป)` : ''}`)
    } catch (err) {
      console.error('trade log error:', err)
      await msg.reply(`ขอโทษค่ะ บันทึกเทรดไม่สำเร็จ: ${err.message}`)
    }
    return
  }

  if (AFFILIATE_TRIGGER_RE.test(text)) {
    console.log('[trigger] category=affiliate')
    const afterTrigger = text.replace(AFFILIATE_TRIGGER_RE, '').trim()
    if (!afterTrigger && !hasImageAttachment) {
      await msg.reply(
        'พิมพ์ชื่อสินค้า/ราคา/ลิงก์ Shopee ต่อท้ายด้วยนะคะ เช่น "โปรโมท: คีย์บอร์ด Logitech K380 690 บาท https://shopee.co.th/..."',
      )
      return
    }
    try {
      await msg.channel.sendTyping()
      const { draft, image, clip } = await appendAffiliateDraft(msg, text)
      const files = []
      if (image) files.push(new AttachmentBuilder(image.buf, { name: image.fname }))
      if (clip) files.push(new AttachmentBuilder(clip.buf, { name: clip.fname }))
      await msg.reply({ content: `✅ ร่างแคปชันแล้วค่ะ\n\n${draft}`, files })
    } catch (err) {
      console.error('affiliate draft error:', err)
      await msg.reply(`ขอโทษค่ะ สร้างแคปชันไม่สำเร็จ: ${err.message} (บันทึกข้อมูลสินค้าดิบไว้ให้แล้วนะคะ)`)
    }
    return
  }

  if (hasImageAttachment || DIARY_TRIGGER_RE.test(text)) {
    console.log('[trigger] category=diary')
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
    console.log('[trigger] category=summary')
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

  console.log('[trigger] category=quick-brain-fallback')

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

// Tracks message IDs already processed this run, so a slow double-click or a duplicate
// gateway event can't log the same signal twice. In-memory only (v1, same as `history`) —
// resets on restart, which just means a signal could theoretically be re-confirmed once
// after a bot restart; low-stakes since this only logs intent, never places an order.
const processedSignals = new Set()

client.on('messageReactionAdd', async (reaction, user) => {
  if (user.bot) return
  if (!allowedUsers.has(user.id)) return
  if (!['✅', '❌'].includes(reaction.emoji.name)) return

  try {
    if (reaction.partial) await reaction.fetch()
    if (reaction.message.partial) await reaction.message.fetch()
  } catch (err) {
    console.error('failed to fetch partial reaction/message:', err.message)
    return
  }

  const msg = reaction.message
  if (!reportChannelEnabled || msg.channel.id !== REPORT_CHANNEL_ID) return

  const match = TRADE_SIGNAL_RE.exec(msg.content)
  if (!match) return // not a trade-signal message — ignore (diary/summary/etc. reactions)

  const dedupeKey = `${msg.id}:${reaction.emoji.name}`
  if (processedSignals.has(dedupeKey)) return
  processedSignals.add(dedupeKey)

  const [, symbol, market, entry, stop, target, size] = match
  const confirmed = reaction.emoji.name === '✅'

  try {
    await appendReactionTradeEntry({ symbol, market, entry, stop, target, size }, confirmed)
    await msg.channel.send(
      confirmed
        ? `<@${user.id}> ✅ บันทึกว่าเข้าไม้ ${symbol} จริงแล้วค่ะ`
        : `<@${user.id}> ⏭️ บันทึกว่าข้ามสัญญาณ ${symbol} แล้วค่ะ`,
    )
  } catch (err) {
    console.error('reaction trade-log error:', err)
    processedSignals.delete(dedupeKey) // allow retry — the log write itself failed
    await msg.channel.send(`<@${user.id}> ขอโทษค่ะ บันทึกไม่สำเร็จ: ${err.message}`)
  }
})

client.login(DISCORD_BOT_TOKEN)
