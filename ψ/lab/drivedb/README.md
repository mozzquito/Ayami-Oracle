# drivedb

**Personal video/audio transcriber** — upload files to your own Google Drive, transcribe them locally with whisper-cpp (free, offline), and full-text search the transcripts via SQLite FTS5.

Think of it as a personal, cost-conscious alternative to VideoDB. No cloud AI subscriptions, no per-minute transcription fees, no data leaving your machine except the original file (which goes to your own Drive).

## Prerequisites

| Tool | Install (macOS) | Verify |
|------|----------------|--------|
| Node.js ≥ 18 | `brew install node` | `node --version` |
| ffmpeg | `brew install ffmpeg` | `ffmpeg -version` |
| whisper-cpp | `brew install whisper-cpp` | `/opt/homebrew/opt/whisper-cpp/bin/whisper-cli --help` |
| whisper medium model | Download from [huggingface](https://huggingface.co/ggerganov/whisper.cpp/tree/main) | Save to `~/.local/share/whisper-cpp/models/ggml-medium.bin` |

### Screen Recording permission (required for `drivedb record`)

macOS requires the terminal app running `drivedb record` to have **Screen & System Audio Recording** permission. Without it, ffmpeg's avfoundation screen capture silently produces a black/empty video.

To grant permission:
1. Open **System Settings → Privacy & Security → Screen & System Audio Recording**
2. Add the terminal app you use (Terminal.app, iTerm2, Warp, etc.) to the allowed list
3. Restart the terminal app after granting permission

### Whisper model download

```bash
mkdir -p ~/.local/share/whisper-cpp/models
curl -L -o ~/.local/share/whisper-cpp/models/ggml-medium.bin \
  https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-medium.bin
```

## Install

```bash
cd drivedb
npm install
npm run build
npm link   # makes `drivedb` available system-wide
```

## Google Cloud OAuth2 Setup (Required — One Time)

drivedb uses OAuth2 to upload files to **your** Google Drive. You need to create an OAuth client in Google Cloud Console. Here are the exact steps:

### Step 1: Create a Google Cloud project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **Select a project** → **New Project**
3. Name it (e.g. "drivedb-personal") → **Create**
4. Make sure the new project is selected in the top bar

### Step 2: Enable the Drive API

1. Go to **APIs & Services** → **Library**
2. Search for **Google Drive API**
3. Click **Enable**

### Step 3: Configure the OAuth consent screen

1. Go to **APIs & Services** → **OAuth consent screen**
2. Choose **External** (since you're the only user) → **Create**
3. Fill in:
   - App name: `drivedb` (or whatever you like)
   - User support email: your email
   - Developer contact email: your email
4. Click **Save and Continue** through the Scopes step (we set scopes in code, not here)
5. On the **Test users** step, add your Google account email → **Save and Continue**
6. ⚠️ **CRITICAL**: Go back to the OAuth consent screen page. You'll see a **Publishing status** dropdown. Change it from **"Testing"** to **"In Production"** and click **Publish app** → **Confirm**.
   - **Why?** In "Testing" mode, Google refresh tokens expire after **7 days**. Your `drivedb auth` will seem to work, but a week later all uploads will fail with an auth error. "In Production" does NOT require Google's review for a personal/unpublished app — it simply means the tokens don't auto-expire.

### Step 4: Create the OAuth client credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth client ID**
3. Application type: **Desktop app** (NOT "Web application", NOT "iOS", NOT "Android")
4. Name: `drivedb-cli` (or anything you like)
5. Under **Authorized redirect URIs**, you should see `http://localhost` listed (or add it)
6. **Actually, we need a specific port.** Replace any default redirect URIs with exactly: `http://localhost:3000`
7. Click **Create**
8. A dialog will show your **Client ID** and **Client Secret**. Copy them.

### Step 5: Create the credentials file

Create the file `~/.drivedb/credentials.json` with this exact structure:

```json
{
  "installed": {
    "client_id": "YOUR_CLIENT_ID_HERE",
    "client_secret": "YOUR_CLIENT_SECRET_HERE",
    "redirect_uris": ["http://localhost:3000"]
  }
}
```

Replace `YOUR_CLIENT_ID_HERE` and `YOUR_CLIENT_SECRET_HERE` with the values from Step 4.

```bash
mkdir -p ~/.drivedb
nano ~/.drivedb/credentials.json   # paste the JSON above
```

### Step 6: Authenticate

```bash
drivedb auth
```

This will:
1. Print a URL — open it in your browser
2. Authorize the app to manage files it creates in your Drive
3. The browser will redirect to `http://localhost:3000` (a temporary local server) which captures the auth code
4. Token saved to `~/.drivedb/token.json`

You only need to do this once. The token (with refresh token) persists across sessions.

## Usage

### Upload a file

```bash
drivedb upload path/to/video.mp4
drivedb upload path/to/audio.mp3 --name "Meeting Notes 2024-01-15"
```

This will:
1. **Transcribe** the file locally using whisper-cli (the medium model, auto-detecting language)
2. **Upload** the original file to a "drivedb" folder in your Google Drive
3. **Store** the transcript + metadata in a local SQLite database

Output:
```
📁 File: interview.mp4
   Size: 245.3 MB
   Format: MP4

🎙️  Step 1/2: Transcribing locally...
  Converting to WAV: /var/folders/...
  Transcribing with whisper-cli (medium model)...
  ✅ Transcription complete (342.5s, duration ≈ 15:42)
  Preview: "สวัสดีครับวันนี้เราจะมาพูดถึง..."

☁️  Step 2/2: Uploading to Google Drive...
  ✅ Uploaded! Drive link: https://drive.google.com/file/d/...

✅ Record saved!
   ID:        1
   Drive:     https://drive.google.com/file/d/...
   Duration:  15:42
```

### Record your screen

```bash
drivedb record
drivedb record --name "Team Standup 2026-08-16"
```

This will:
1. **Detect** your screen capture device, microphone, and optionally BlackHole (system audio) via ffmpeg
2. **Record** screen + audio to a temp MP4 file (press Enter to stop)
3. **Transcribe** the recording locally with whisper-cli
4. **Upload** the recording to your Google Drive "drivedb" folder
5. **Store** the transcript + metadata in SQLite
6. **Clean up** the temp file automatically

The tool auto-detects avfoundation device indices at runtime — no hardcoded device numbers.

#### Capturing system audio (optional — BlackHole)

By default, `drivedb record` captures your microphone. To also capture **system audio** (browser tabs, music, notification sounds), install [BlackHole](https://github.com/ExistentialAudio/BlackHole) — a free, open-source virtual audio loopback driver:

```bash
brew install blackhole-2ch
```

After installing, create a **Multi-Output Device** in **Audio MIDI Setup** (found in `/Applications/Utilities/`) so you can still hear your own audio while it's being captured:

1. Open **Audio MIDI Setup** → click **+** (bottom-left) → **Create Multi-Output Device**
2. Check the box next to your **built-in speakers** (or your normal output)
3. Check the box next to **BlackHole 2ch**
4. **Uncheck** "Master" on BlackHole 2ch (prevents double-amplification)
5. Right-click the new Multi-Output Device → **Use This Device For Sound Output**

Now when you run `drivedb record`, it will automatically detect BlackHole and capture both your microphone and system audio mixed together. If BlackHole is not installed, the command still works with microphone-only and prints a one-time suggestion.

```bash
drivedb list
```

```
3 file(s) in drivedb:

ID    NAME                                     FORMAT SIZE        DURATION CREATED
--------------------------------------------------------------------------------
3     meeting-notes.mp4                       MP4    245.3 MB    15:42    2024-01-15 10:30:00
2     podcast-ep12.mp3                         MP3    45.2 MB     22:15    2024-01-10 08:00:00
1     interview-thai.mp4                       MP4    1.2 GB      45:30    2024-01-05 14:00:00
```

### Search transcripts (Thai + English)

```bash
drivedb search "ปัญญาประดิษฐ์"
drivedb search "machine learning"
drivedb search "การประชุม"
```

```
Found 2 result(s) for "ปัญญาประดิษฐ์":

  ID 3: meeting-notes.mp4
    …ในปี 2024 นี้ «ปัญญาประดิษฐ์» จะมีบทบาทสำคัญในอุตสาหกรรม…

  ID 1: interview-thai.mp4
    …เราเชื่อว่า «ปัญญาประดิษฐ์» จะช่วยแก้ปัญหา…
```

### Show full details

```bash
drivedb show 3
```

Prints full metadata + the complete transcript for record ID 3.

## Architecture

```
src/
  cli.ts          — Commander CLI entry point (auth, upload, list, search, show, record)
  db.ts           — SQLite + FTS5 setup, Thai word segmentation, CRUD queries
  drive.ts        — Google Drive OAuth2 flow + file upload
  record.ts       — macOS screen + audio recording via ffmpeg/avfoundation
  transcribe.ts  — whisper-cli + ffmpeg shell integration

~/.drivedb/
  credentials.json   — Your OAuth client credentials (you create this)
  token.json          — Saved OAuth token + refresh token (auto-generated)
  config.json         — Drive folder ID cache (auto-generated)
  drivedb.sqlite3     — Local database with all transcripts & metadata
```

### Thai text search

SQLite FTS5's default `unicode61` tokenizer cannot segment Thai text (no word boundaries). drivedb pre-processes all transcript text using Node.js `Intl.Segmenter` with locale `th` before insertion, inserting spaces between detected Thai words. This means FTS5 can properly tokenize and match Thai content. English and mixed Thai/English text works correctly too.

## Scope

**v1 does:**
- Upload audio/video to your Google Drive
- Record screen + audio locally (macOS)
- Local transcription with whisper-cpp (offline, free)
- Full-text search across transcripts (Thai + English)
- Persistent local SQLite database

**v1 does NOT:**
- Stream video from Drive
- Generate AI summaries
- Semantic/embedding-based search
- Multi-user support
- Any cloud API beyond Google Drive upload

## Troubleshooting

### "No saved token. Run `drivedb auth` first."
You need to authenticate first. Make sure `~/.drivedb/token.json` exists.

### Auth worked, but uploads fail after 7 days
Your refresh token expired because the OAuth consent screen is still in **"Testing"** mode. Go back to Google Cloud Console → OAuth consent screen → change Publishing status to **"In Production"**, then re-run `drivedb auth`.

### Port 3000 in use
The OAuth callback server uses port 3000. Close whatever's using it, or the flow won't complete.

### whisper-cli errors
- Make sure whisper-cpp is installed: `brew install whisper-cpp`
- Make sure the medium model exists at `~/.local/share/whisper-cpp/models/ggml-medium.bin`
- For very long files, whisper-cli may take a while — that's normal

### FTS5 not working for Thai
The Thai segmentation happens automatically via `Intl.Segmenter`. Make sure you're on Node.js ≥ 18 (which includes full Intl.Segmenter support).

## License

MIT
