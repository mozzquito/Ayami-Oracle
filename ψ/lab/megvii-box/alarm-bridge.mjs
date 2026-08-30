// alarm-bridge.mjs — HTTP receiver for the Megvii box's Active Alarm Push.
//
// The box POSTs two kinds of requests here once configured (see
// `python3 megvii_client.py configure-push --server-path <host>:<port>`):
//   1. Heartbeat: application/json {timestamp, sn} — must reply 200 or the box
//      considers the push server dead and stops sending real alarms.
//   2. Alarm: multipart/form-data, field "alarm_info" (JSON text) + up to 3
//      optional "picture" file parts — must also reply 200 to acknowledge.
//
// Every alarm gets relayed to:
//   - Discord, via a channel Webhook URL (plain HTTPS POST — no bot gateway
//     login, no sibling-process spawn). Deliberately NOT the discord-bot's
//     notify.mjs pattern: that shells out to a sibling file, which only works
//     when this runs next to that repo checkout. A standalone HTTPS call is
//     what makes this deployable on its own, e.g. to Railway (see README).
//   - LINE OA, via the Messaging API's `broadcast` endpoint (sends to every
//     friend of the OA — fine for a personal single-user OA; switch to
//     `push` with a specific userId if the OA ever gets more than one friend)
//
// Deployable two ways — same code, no branching needed:
//   - Locally via launchd (see README) — requires this Mac to stay on and
//     reachable from the box's LAN.
//   - On Railway (or any PaaS) — the box pushes to a public HTTPS URL instead
//     of a local IP, so nothing needs to stay on at home at all. Listens on
//     process.env.PORT when the platform sets one (Railway does), falling
//     back to ALARM_BRIDGE_PORT/8788 for local runs.

import 'dotenv/config'
import http from 'node:http'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import Busboy from 'busboy'
import { v2 as cloudinary } from 'cloudinary'

const PORT = process.env.PORT || process.env.ALARM_BRIDGE_PORT || 8788
const LINE_CHANNEL_ACCESS_TOKEN = process.env.LINE_CHANNEL_ACCESS_TOKEN
const DISCORD_WEBHOOK_URL = process.env.DISCORD_WEBHOOK_URL

// LINE needs a public HTTPS URL for image messages (it fetches the image itself —
// can't just POST bytes like Discord). Cloudinary's free tier (25 credits/mo, forever
// free as of 2026) gives us that: upload the alarm snapshot, get a public URL back,
// hand that URL to LINE. Configure via CLOUDINARY_URL="cloudinary://key:secret@cloud_name"
// in .env — the SDK picks it up automatically, no explicit .config() call needed.
const CLOUDINARY_ENABLED = Boolean(process.env.CLOUDINARY_URL)

async function uploadToCloudinary(imagePath) {
  if (!CLOUDINARY_ENABLED) return null
  try {
    // No auto-expiry configured — free-tier Cloudinary has no simple "delete after N days"
    // upload flag. Images accumulate in the "megvii-alarms" folder until manually cleared.
    // At 25 free credits/month (~25GB) this is a non-issue at alarm-photo volume, but if it
    // ever matters, add a periodic cleanup (e.g. cloudinary.api.delete_resources_by_prefix).
    const result = await cloudinary.uploader.upload(imagePath, { folder: 'megvii-alarms' })
    return result.secure_url
  } catch (err) {
    console.error('[cloudinary] upload failed —', err.message)
    return null
  }
}

// Defense in depth: filter + rate-limit here even though the device is also configured
// with its own alarm_type/minor_type filter (see megvii_client.py configure_alarm_push).
// Learned the hard way (2026-08-24): the device pushed way more event types than the
// configured filter implied (face/body_capture/device_connect_state alongside the
// intended alert_alarm events), and a single test session firing bursts of INTRUSION
// spawned 70+ concurrent notify.mjs processes (each a full Discord gateway login) before
// anyone noticed — silently piling up rather than erroring loudly. Never assume the
// device-side filter is the only thing standing between "real event" and "flood".
//
// ALARM_BRIDGE_ALLOWED_TYPES: comma-separated minor types to actually relay, e.g.
// "HOLDWEAPON" or "HOLDWEAPON,INTRUSION". Unset/empty = relay everything (not
// recommended for anything but debugging — prefer setting this explicitly).
const ALLOWED_TYPES = (process.env.ALARM_BRIDGE_ALLOWED_TYPES || '')
  .split(',')
  .map((s) => s.trim())
  .filter(Boolean)

const COOLDOWN_MS = Number(process.env.ALARM_BRIDGE_COOLDOWN_MS || 30_000)
const lastSentAt = new Map() // minorType -> timestamp ms

async function sendDiscord(text, imageUrl = null) {
  if (!DISCORD_WEBHOOK_URL) {
    console.error('[discord] DISCORD_WEBHOOK_URL not set — skipping')
    return
  }
  const payload = { content: text.slice(0, 2000) }
  // Reuse the same Cloudinary URL as LINE gets — one upload, both channels. Discord
  // renders an embed image straight from the URL, no separate file upload needed.
  if (imageUrl) payload.embeds = [{ image: { url: imageUrl } }]
  try {
    const res = await fetch(DISCORD_WEBHOOK_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    if (!res.ok) console.error('[discord] webhook failed:', res.status, await res.text())
  } catch (err) {
    console.error('[discord] webhook error —', err.message)
  }
}

async function sendLine(text, imageUrl = null) {
  if (!LINE_CHANNEL_ACCESS_TOKEN) {
    console.error('[line] LINE_CHANNEL_ACCESS_TOKEN not set — skipping')
    return
  }
  const messages = [{ type: 'text', text: text.slice(0, 5000) }]
  if (imageUrl) {
    // LINE requires HTTPS JPEG URLs it can fetch itself — reachable at send time AND
    // whenever the recipient later opens the chat, so this can't be a local/LAN path.
    // previewImageUrl reuses the same URL (Cloudinary's default upload is already
    // reasonably sized for a chat thumbnail; a dedicated w_240 transform URL would be
    // more correct but this is fine at alarm-photo volume/quality).
    messages.push({ type: 'image', originalContentUrl: imageUrl, previewImageUrl: imageUrl })
  }
  try {
    const res = await fetch('https://api.line.me/v2/bot/message/broadcast', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${LINE_CHANNEL_ACCESS_TOKEN}`,
      },
      body: JSON.stringify({ messages }),
    })
    if (!res.ok) console.error('[line] broadcast failed:', res.status, await res.text())
  } catch (err) {
    console.error('[line] broadcast error —', err.message)
  }
}

const EVENT_LABELS = {
  INTRUSION: '🚨 มีคนบุกรุกเข้าพื้นที่ (INTRUSION)',
  TRIPWIRE: '🚨 มีคนข้ามเส้นที่กำหนด (TRIPWIRE)',
  SMOKING: '🚬 ตรวจพบการสูบบุหรี่ (SMOKING)',
  HOLDWEAPON: '🔪 ตรวจพบอาวุธ (HOLDWEAPON)',
  FIGHT: '🥊 ตรวจพบการทะเลาะวิวาท (FIGHT)',
}

function parseAlarm(alarmInfoText) {
  let data
  try {
    data = JSON.parse(alarmInfoText)
  } catch {
    return { minor: 'PARSE_ERROR', text: `Megvii alarm (raw, parse failed): ${alarmInfoText.slice(0, 300)}` }
  }
  const minor =
    data?.additional?.alarm_minor ||
    data?.warehouseV20Events?.alarmEvents?.[0]?.eventType ||
    'UNKNOWN'
  const label = EVENT_LABELS[minor] || `⚠️ ${minor}`
  const deviceId = data?.additional?.device_id ?? '?'
  const tsRaw = data?.additional?.alarm_time || data?.global_info?.time_ms
  const time = tsRaw
    ? new Date(Number(tsRaw)).toLocaleString('th-TH', { timeZone: 'Asia/Bangkok' })
    : new Date().toLocaleString('th-TH', { timeZone: 'Asia/Bangkok' })
  return { minor, text: `${label}\nกล้อง: hik (device_id=${deviceId})\nเวลา: ${time}` }
}

const server = http.createServer((req, res) => {
  const contentType = req.headers['content-type'] || ''

  if (req.method === 'POST' && contentType.includes('application/json')) {
    // Heartbeat — just drain the body and ack.
    req.on('data', () => {})
    req.on('end', () => {
      res.writeHead(200)
      res.end('ok')
    })
    return
  }

  if (req.method === 'POST' && contentType.includes('multipart/form-data')) {
    const bb = Busboy({ headers: req.headers })
    let alarmInfo = null
    let imagePath = null // only the first "picture" part is kept — one image is plenty for a chat notification
    const pendingWrites = []

    bb.on('field', (name, val) => {
      if (name === 'alarm_info') alarmInfo = val
    })
    bb.on('file', (name, file, info) => {
      if (name !== 'picture' || imagePath !== null) {
        file.resume() // not an image part, or we already captured one — drain it
        return
      }
      const ext = path.extname(info?.filename || '') || '.jpg'
      const tmpPath = path.join(os.tmpdir(), `megvii-alarm-${Date.now()}${ext}`)
      const writeStream = fs.createWriteStream(tmpPath)
      file.pipe(writeStream)
      pendingWrites.push(
        new Promise((resolve) => {
          writeStream.on('finish', () => {
            imagePath = tmpPath
            resolve()
          })
          writeStream.on('error', (err) => {
            console.error('[alarm] failed to save alarm picture —', err.message)
            resolve()
          })
        }),
      )
    })
    bb.on('finish', async () => {
      res.writeHead(200)
      res.end('ok')
      await Promise.all(pendingWrites)
      if (alarmInfo) {
        const { minor, text } = parseAlarm(alarmInfo)
        const allowed = ALLOWED_TYPES.length === 0 || ALLOWED_TYPES.includes(minor)
        const now = Date.now()
        const last = lastSentAt.get(minor) || 0
        const cooledDown = now - last >= COOLDOWN_MS

        if (!allowed) {
          console.log('[alarm]', text.replace(/\n/g, ' | '), '— filtered out (not in ALARM_BRIDGE_ALLOWED_TYPES)')
        } else if (!cooledDown) {
          console.log('[alarm]', text.replace(/\n/g, ' | '), `— skipped, within ${COOLDOWN_MS}ms cooldown for ${minor}`)
        } else {
          lastSentAt.set(minor, now)
          console.log('[alarm]', text.replace(/\n/g, ' | '), imagePath ? '(+image)' : '')
          const cloudinaryUrl = imagePath ? await uploadToCloudinary(imagePath) : null
          if (imagePath && !cloudinaryUrl) console.error('[alarm] cloudinary upload failed or disabled — sending text only')
          await Promise.all([sendDiscord(text, cloudinaryUrl), sendLine(text, cloudinaryUrl)])
        }
      }
      if (imagePath) fs.unlink(imagePath, () => {})
    })
    req.pipe(bb)
    return
  }

  // Unknown request shape — ack anyway so the box doesn't retry-storm.
  res.writeHead(200)
  res.end('ok')
})

server.listen(PORT, () => {
  console.log(`Megvii alarm-bridge listening on :${PORT}`)
})
