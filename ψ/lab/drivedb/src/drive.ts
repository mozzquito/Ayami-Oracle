/**
 * Google Drive integration: OAuth2 authentication and file upload.
 *
 * Uses the "installed app" flow (redirect to localhost) which opens the
 * user's system browser once.  Credentials (client_id / client_secret) are
 * read from ~/.drivedb/credentials.json which the user creates manually.
 * The resulting token (with refresh_token) is persisted in ~/.drivedb/token.json.
 */

import { google } from "googleapis";
import type { Credentials } from "google-auth-library";
import { readFile, writeFile } from "node:fs/promises";
import { stat as statFile } from "node:fs/promises";
import { homedir } from "node:os";
import { join, resolve } from "node:path";
import { existsSync, mkdirSync, createReadStream } from "node:fs";
import { createServer, type IncomingMessage, type ServerResponse } from "node:http";

// ---------------------------------------------------------------------------
// Paths
// ---------------------------------------------------------------------------

const DRIVEDB_DIR = join(homedir(), ".drivedb");
const CREDENTIALS_PATH = join(DRIVEDB_DIR, "credentials.json");
const TOKEN_PATH = join(DRIVEDB_DIR, "token.json");
const CONFIG_PATH = join(DRIVEDB_DIR, "config.json");
const SESSIONS_PATH = join(DRIVEDB_DIR, "upload-sessions.json");

export const SCOPES = [
  "https://www.googleapis.com/auth/drive.file", // least-privilege: only files this app creates
];

// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------

interface OAuthCredentials {
  installed: {
    client_id: string;
    client_secret: string;
    redirect_uris: string[];
  };
}

interface StoredConfig {
  driveFolderId?: string;
}

function ensureDir(): void {
  if (!existsSync(DRIVEDB_DIR)) {
    mkdirSync(DRIVEDB_DIR, { recursive: true });
  }
}

// ---------------------------------------------------------------------------
// Resumable-upload session persistence
// ---------------------------------------------------------------------------

interface UploadSession {
  sessionUri: string;
  fileSize: number;
  fileName: string;
  mimeType: string;
  folderId: string;
  createdAt: string;
}

type SessionMap = Record<string, UploadSession>;

/** Read persisted upload sessions, returning {} if missing/unparseable. */
async function loadSessions(): Promise<SessionMap> {
  try {
    const raw = await readFile(SESSIONS_PATH, "utf-8");
    return JSON.parse(raw) as SessionMap;
  } catch {
    return {};
  }
}

/** Persist upload sessions to disk. */
async function saveSessions(sessions: SessionMap): Promise<void> {
  ensureDir();
  await writeFile(SESSIONS_PATH, JSON.stringify(sessions, null, 2), "utf-8");
}

/**
 * Obtain a fresh access token for the resumable-upload fetch calls.
 *
 * Re-reads credentials.json + token.json (same as getDriveClient), constructs
 * an OAuth2Client, and returns the current access token string.
 */
async function getAccessTokenForResumable(): Promise<string> {
  const token = await loadSavedToken();
  if (!token) {
    throw new Error(
      "No saved token. Run `drivedb auth` first.\n" +
        "If you already authenticated, check that ~/.drivedb/token.json exists.",
    );
  }

  const creds = await readCredentials();
  const oauth2Client = new google.auth.OAuth2(
    creds.client_id,
    creds.client_secret,
    creds.redirect_uri,
  );

  oauth2Client.setCredentials(token);

  // getAccessToken() handles refresh internally.
  const { token: accessToken } = await oauth2Client.getAccessToken();
  if (!accessToken) {
    throw new Error("Failed to obtain access token from Google OAuth2 client.");
  }
  return accessToken;
}

/** Read the Drive folder ID from config, or undefined if not set. */
export async function getDriveFolderId(): Promise<string | undefined> {
  try {
    const raw = await readFile(CONFIG_PATH, "utf-8");
    const cfg: StoredConfig = JSON.parse(raw);
    return cfg.driveFolderId;
  } catch {
    return undefined;
  }
}

/** Save the Drive folder ID to config. */
export async function saveDriveFolderId(folderId: string): Promise<void> {
  ensureDir();
  let cfg: StoredConfig = {};
  try {
    const raw = await readFile(CONFIG_PATH, "utf-8");
    cfg = JSON.parse(raw);
  } catch {
    // first time — empty config is fine
  }
  cfg.driveFolderId = folderId;
  await writeFile(CONFIG_PATH, JSON.stringify(cfg, null, 2), "utf-8");
}

/** Load saved token from disk, or return null. */
async function loadSavedToken(): Promise<Credentials | null> {
  try {
    const raw = await readFile(TOKEN_PATH, "utf-8");
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

/** Save token to disk. */
async function saveToken(token: Credentials): Promise<void> {
  ensureDir();
  await writeFile(TOKEN_PATH, JSON.stringify(token, null, 2), "utf-8");
}

/**
 * Run the OAuth2 installed-app flow.
 *
 * 1. Read credentials from ~/.drivedb/credentials.json
 * 2. Generate an auth URL and open it in the system browser
 * 3. Start a local HTTP server to receive the redirect callback
 * 4. Exchange the auth code for tokens
 * 5. Persist tokens to ~/.drivedb/token.json
 */
export async function authenticate(): Promise<void> {
  // --- Step 1: read credentials ---
  if (!existsSync(CREDENTIALS_PATH)) {
    console.error(
      "Error: ~/.drivedb/credentials.json not found.\n" +
        "Please create it with your Google Cloud OAuth client credentials.\n" +
        "See README.md for instructions.",
    );
    process.exit(1);
  }

  const credsRaw = await readFile(CREDENTIALS_PATH, "utf-8");
  const credentials: OAuthCredentials = JSON.parse(credsRaw);
  const { client_id, client_secret, redirect_uris } = credentials.installed;

  const redirectUri = redirect_uris?.[0] || "http://localhost:3000";

  const oauth2Client = new google.auth.OAuth2(
    client_id,
    client_secret,
    redirectUri,
  );

  // --- Step 2: generate auth URL ---
  const authUrl = oauth2Client.generateAuthUrl({
    access_type: "offline", // required to get a refresh_token
    scope: SCOPES,
    prompt: "consent", // force consent so we always get a refresh_token
  });

  console.log("\nAuthorize drivedb by visiting this URL in your browser:");
  console.log(authUrl);
  console.log(
    "\nWaiting for the authorization callback on " + redirectUri + " ...\n",
  );

  // --- Step 3: local redirect server ---
  const code = await new Promise<string>((resolve, reject) => {
    const server = createServer((req: IncomingMessage, res: ServerResponse) => {
      const url = new URL(req.url ?? "/", redirectUri);
      const authCode = url.searchParams.get("code");

      if (authCode) {
        res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
        res.end(
          "<h2>✅ Authorization successful!</h2>" +
            "<p>You can close this tab and return to the terminal.</p>",
        );
        resolve(authCode);
        setTimeout(() => server.close(), 500);
      } else {
        const error = url.searchParams.get("error");
        res.writeHead(400, { "Content-Type": "text/html; charset=utf-8" });
        res.end(
          `<h2>Authorization failed</h2><p>Error: ${error || "unknown"}</p>`,
        );
        reject(new Error(`OAuth error: ${error}`));
        setTimeout(() => server.close(), 500);
      }
    });

    server.listen(3000, "127.0.0.1", () => {
      // Server ready — user should visit the URL printed above.
    });

    server.on("error", (err: Error) => {
      if ((err as NodeJS.ErrnoException).code === "EADDRINUSE") {
        reject(
          new Error(
            "Port 3000 is already in use. Close the other process or change the redirect URI.",
          ),
        );
      } else {
        reject(err);
      }
    });
  });

  // --- Step 4: exchange code for tokens ---
  const { tokens } = await oauth2Client.getToken(code);

  // --- Step 5: persist ---
  await saveToken(tokens);
  console.log("✅ Token saved to ~/.drivedb/token.json");
}

// ---------------------------------------------------------------------------
// Create an authorized Drive client
// ---------------------------------------------------------------------------

export async function getDriveClient(): Promise<ReturnType<typeof google.drive>> {
  const token = await loadSavedToken();
  if (!token) {
    console.error(
      "Error: No saved token. Run `drivedb auth` first.\n" +
        "If you already authenticated, check that ~/.drivedb/token.json exists.",
    );
    process.exit(1);
  }

  const creds = await readCredentials();
  const oauth2Client = new google.auth.OAuth2(
    creds.client_id,
    creds.client_secret,
    creds.redirect_uri,
  );

  oauth2Client.setCredentials(token);

  // Auto-refresh token when expired.
  oauth2Client.on("tokens", async (newTokens) => {
    const merged = { ...token, ...newTokens };
    await saveToken(merged);
  });

  return google.drive({ version: "v3", auth: oauth2Client });
}

async function readCredentials(): Promise<{
  client_id: string;
  client_secret: string;
  redirect_uri: string;
}> {
  if (!existsSync(CREDENTIALS_PATH)) {
    console.error("Error: ~/.drivedb/credentials.json not found.");
    process.exit(1);
  }
  const raw = await readFile(CREDENTIALS_PATH, "utf-8");
  const creds: OAuthCredentials = JSON.parse(raw);
  return {
    client_id: creds.installed.client_id,
    client_secret: creds.installed.client_secret,
    redirect_uri: creds.installed.redirect_uris?.[0] || "http://localhost:3000",
  };
}

// ---------------------------------------------------------------------------
// Drive folder management
// ---------------------------------------------------------------------------

/**
 * Find or create the "drivedb" folder in Google Drive.
 * Returns the folder ID.
 */
export async function ensureDriveFolder(
  drive: Awaited<ReturnType<typeof getDriveClient>>,
): Promise<string> {
  // Check cached config first.
  const cached = await getDriveFolderId();
  if (cached) return cached;

  // Try to find an existing folder named "drivedb".
  const res = await drive.files.list({
    q: "name='drivedb' and mimeType='application/vnd.google-apps.folder' and trashed=false",
    fields: "files(id, name)",
    spaces: "drive",
    pageSize: 5,
  });

  if (res.data.files && res.data.files.length > 0) {
    const folderId = res.data.files[0].id!;
    await saveDriveFolderId(folderId);
    return folderId;
  }

  // Create it.
  const folder = await drive.files.create({
    requestBody: {
      name: "drivedb",
      mimeType: "application/vnd.google-apps.folder",
    },
    fields: "id",
  });

  const folderId = folder.data.id!;
  await saveDriveFolderId(folderId);
  return folderId;
}

// ---------------------------------------------------------------------------
// File upload (resumable/chunked)
// ---------------------------------------------------------------------------

export interface UploadResult {
  fileId: string;
  webViewLink: string;
}

/**
 * Upload a file to the drivedb folder using a hand-rolled resumable upload.
 *
 * Implements Google Drive's resumable upload protocol via fetch directly,
 * so that sessions can be persisted to disk and resumed across process
 * restarts.  The uploadFile(drive, filePath, fileName, mimeType) signature
 * is unchanged — the call-site in cli.ts needs no changes.
 */
export async function uploadFile(
  drive: Awaited<ReturnType<typeof getDriveClient>>,
  filePath: string,
  fileName: string,
  mimeType: string,
): Promise<UploadResult> {
  // (a) Compute file size.
  const absFilePath = resolve(filePath);
  const fileStat = await statFile(absFilePath);
  const fileSize = fileStat.size;

  // (b) Ensure the drivedb folder exists on Drive.
  const folderId = await ensureDriveFolder(drive);

  // (c) Check for an existing resumable session for this exact file path.
  const sessions = await loadSessions();
  const key = absFilePath;
  const existing = sessions[key];

  let sessionUri = "";
  let resumeFrom = 0;

  if (existing && existing.fileSize === fileSize) {
    // (d) Attempt to resume the existing session.
    const token = await getAccessTokenForResumable();

    const queryUrl = `${existing.sessionUri}`;
    const statusResp = await fetch(queryUrl, {
      method: "PUT",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Range": `bytes */${fileSize}`,
      },
      // Intentionally no body — empty PUT to query upload status.
    });

    if (statusResp.status === 200 || statusResp.status === 201) {
      // File was already fully uploaded in a prior run (process died after
      // Drive finished but before we cleaned up the session entry).
      const body = await statusResp.json() as { id?: string; webViewLink?: string };
      delete sessions[key];
      await saveSessions(sessions);
      const fileId = body.id!;
      let webViewLink = body.webViewLink || "";
      if (!webViewLink) {
        const fetched = await drive.files.get({ fileId, fields: "webViewLink" });
        webViewLink = fetched.data.webViewLink || "";
      }
      return { fileId, webViewLink };
    }

    if (statusResp.status === 308) {
      // Incomplete upload — figure out how many bytes Drive already has.
      const rangeHeader = statusResp.headers.get("Range"); // "bytes=0-12345"
      if (rangeHeader) {
        const match = rangeHeader.match(/^bytes=(\d+)-(\d+)$/);
        if (match) {
          resumeFrom = parseInt(match[2], 10) + 1;
        }
      }
      // If no Range header at all, nothing has been received yet — resumeFrom stays 0.
      sessionUri = existing.sessionUri;
    } else {
      // Session expired / invalid (404, 410, etc.) — fall through to (e).
      resumeFrom = -1; // sentinel: start a brand new session
    }
  } else {
    // No existing session, or file size changed — start fresh.
    resumeFrom = -1;
  }

  if (resumeFrom === -1) {
    // (e) Start a brand new resumable upload session.
    const token = await getAccessTokenForResumable();

    const initResp = await fetch(
      "https://www.googleapis.com/upload/drive/v3/files?uploadType=resumable&fields=id,webViewLink",
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json; charset=UTF-8",
        },
        body: JSON.stringify({
          name: fileName,
          mimeType,
          parents: [folderId],
        }),
      },
    );

    if (!initResp.ok) {
      const text = await initResp.text();
      throw new Error(
        `Failed to start resumable upload session with Google Drive (HTTP ${initResp.status}): ${text}`,
      );
    }

    sessionUri = initResp.headers.get("Location")!;
    if (!sessionUri) {
      throw new Error(
        "Failed to start resumable upload session with Google Drive: no Location header in response.",
      );
    }

    // Persist the session for future resume.
    sessions[key] = {
      sessionUri,
      fileSize,
      fileName,
      mimeType,
      folderId,
      createdAt: new Date().toISOString(),
    };
    await saveSessions(sessions);

    resumeFrom = 0;
  }

  // (f) Perform the actual upload PUT.
  const token = await getAccessTokenForResumable();
  const body = createReadStream(absFilePath, { start: resumeFrom }) as unknown as BodyInit;

  let uploadResp: Response;
  try {
    // duplex:"half" is required by Node's fetch/undici when body is a stream,
    // but TS DOM types don't include it — cast to bypass.
    uploadResp = await fetch(sessionUri, {
      method: "PUT",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Range": `bytes ${resumeFrom}-${fileSize - 1}/${fileSize}`,
        "Content-Length": String(fileSize - resumeFrom),
      },
      body,
      duplex: "half",
    } as RequestInit);
  } catch (err) {
    // Leave the session entry intact so a future retry can resume.
    throw new Error(
      `Upload interrupted: ${(err as Error).message}. Re-run the same upload command to resume from where it left off.`,
    );
  }

  if (uploadResp.status !== 200 && uploadResp.status !== 201) {
    // Leave session intact so the user can retry.
    const text = await uploadResp.text();
    throw new Error(
      `Upload failed with HTTP ${uploadResp.status}: ${text}. Re-run the same upload command to resume from where it left off.`,
    );
  }

  // Parse success response.
  const result = (await uploadResp.json()) as { id?: string; webViewLink?: string };
  const fileId = result.id!;
  let webViewLink = result.webViewLink || "";

  // (g) webViewLink is sometimes empty right after create; fetch it explicitly.
  if (!webViewLink) {
    const fetched = await drive.files.get({ fileId, fields: "webViewLink" });
    webViewLink = fetched.data.webViewLink || "";
  }

  // Upload complete — remove the session entry.
  delete sessions[key];
  await saveSessions(sessions);

  return { fileId, webViewLink };
}
