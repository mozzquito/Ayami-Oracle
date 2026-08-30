# megvii-box

CLI client for the MEGVII MegCube-B4H04-311 AI box's AIOTAP WebAPI — bypasses
the box's web UI, whose live-preview/rule-drawing widget refuses to run on
Mac ("Currently does not support Mac system").

Background + payload-format gotchas (verified 2026-08-24 against a live
device, not just the docs): `ψ/memory/learnings/2026-08-21_iot-device-blocked-plugin-check-for-bundled-api-docs.md`

## Setup

```bash
export MEGVII_HOST=192.168.1.100   # box's IP
export MEGVII_USER=admin
export MEGVII_PASSWORD='...'       # do not commit this anywhere
```

## Usage

```bash
python3 megvii_client.py cap                              # read-only capability check
python3 megvii_client.py list                              # list configured monitors + device_id mapping
python3 megvii_client.py add-rule --device-id 2 --event-type INTRUSION \
  --points 0,0 0,1 1,1 1,0                                  # whole-frame zone (normalized 0.0-1.0)
python3 megvii_client.py alarm-history --minutes 30 \
  --minor-types HOLDWEAPON                                  # query the box's own on-device alarm log
```

Run `python3 megvii_client.py --help` for all flags.

`add-rule` figures out `device_id` → camera mapping from `list`'s output. If
that device/channel already has a "bypass"-type monitor (the box only allows
one per channel), the new rule is appended to it instead of creating a
conflicting second monitor — matches how the box's own UI adds rules.

## alarm-bridge.mjs — Discord + LINE notifications

Receives the box's Active Alarm Push (multipart POST with a JSON `alarm_info`
field + optional snapshot image) and relays to Discord (webhook) and LINE OA
(Messaging API broadcast), with an alarm-photo upload to Cloudinary so LINE
has a public URL to fetch the image from.

```bash
npm install
cp .env.example .env   # fill in DISCORD_WEBHOOK_URL, LINE_CHANNEL_ACCESS_TOKEN, CLOUDINARY_URL
node alarm-bridge.mjs
```

Point the box at it once running:

```bash
python3 megvii_client.py configure-push --server-path <host>:<port> --minor-types SMOKING HOLDWEAPON
```

### Running it — two options

**Local (launchd)** — keeps this Mac's terminal-free background process alive
across reboots, but the box can only reach it while this Mac is on, awake, and
on the same LAN. See `~/Library/LaunchAgents/com.ayami.megvii-alarm-bridge.plist`
(same pattern as `../discord-bot`'s README) — `launchctl bootstrap gui/$(id -u) ...`.

**Railway (recommended for 24/7)** — deploys `alarm-bridge.mjs` as a public
HTTPS service, so the box pushes straight to Railway's URL over the internet
instead of a local IP. Nothing needs to stay on at home.

```bash
railway init          # or `railway link` to an existing project
railway variables set DISCORD_WEBHOOK_URL=... LINE_CHANNEL_ACCESS_TOKEN=... CLOUDINARY_URL=... ALARM_BRIDGE_ALLOWED_TYPES=...
railway up
railway domain        # generates/shows the public https://....up.railway.app URL
```

Then point the box at the Railway domain instead of a local IP:

```bash
python3 megvii_client.py configure-push --server-path <project>.up.railway.app:443 --link-type https --minor-types SMOKING HOLDWEAPON
```
