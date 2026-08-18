/**
 * drivedb — Local read-only web UI.
 *
 * Serves a single self-contained HTML page with inline CSS/JS and a few JSON
 * API endpoints backed by the same SQLite database used by the CLI commands.
 * Binds to 127.0.0.1 only (never 0.0.0.0) since it exposes local recordings.
 *
 * Note: the `new URL(req.url, ...)` call here parses the incoming request
 * path/query — it does NOT make any outbound network request.
 */

import { createServer, type IncomingMessage, type ServerResponse } from "node:http";
import { initDb, listFiles, getFileById, searchFiles, getSegmentsByFileId } from "./db.js";

// ---------------------------------------------------------------------------
// Helpers (duplicated from cli.ts — that function is module-private)
// ---------------------------------------------------------------------------

function formatMs(ms: number): string {
  const totalSecs = Math.floor(ms / 1000);
  const hrs = Math.floor(totalSecs / 3600);
  const mins = Math.floor((totalSecs % 3600) / 60);
  const secs = totalSecs % 60;
  if (hrs > 0) {
    return `${hrs}:${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
  }
  return `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
}

// ---------------------------------------------------------------------------
// Inline HTML page
// ---------------------------------------------------------------------------

const HTML_PAGE = `\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>drivedb</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; color: #1d1d1f; background: #f5f5f7; line-height: 1.5; }
  a { color: #0066cc; text-decoration: none; }
  a:hover { text-decoration: underline; }
  .container { max-width: 960px; margin: 0 auto; padding: 24px 16px; }
  h1 { font-size: 1.4rem; font-weight: 600; margin-bottom: 16px; }
  .search-bar { margin-bottom: 16px; display: flex; gap: 8px; }
  .search-bar input { flex: 1; padding: 8px 12px; border: 1px solid #d1d1d6; border-radius: 8px; font-size: 0.95rem; background: #fff; }
  .search-bar input:focus { outline: none; border-color: #0066cc; box-shadow: 0 0 0 2px rgba(0,102,204,0.2); }
  .search-bar button { padding: 8px 16px; border: none; border-radius: 8px; background: #0066cc; color: #fff; cursor: pointer; font-size: 0.95rem; }
  .search-bar button:hover { background: #0055aa; }
  table { width: 100%; border-collapse: collapse; background: #fff; border-radius: 10px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
  th, td { text-align: left; padding: 10px 14px; border-bottom: 1px solid #e5e5ea; font-size: 0.9rem; }
  th { background: #fafafa; font-weight: 600; color: #6e6e73; text-transform: uppercase; font-size: 0.75rem; letter-spacing: 0.04em; }
  tr:hover { background: #f9f9fb; }
  .mono { font-family: "SF Mono", Menlo, Consolas, monospace; font-size: 0.85rem; }
  .empty { text-align: center; padding: 32px; color: #8e8e93; }
  .back-link { display: inline-block; margin-bottom: 16px; font-size: 0.9rem; }
  .detail-card { background: #fff; border-radius: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); padding: 20px; margin-bottom: 16px; }
  .detail-card h2 { font-size: 1.15rem; font-weight: 600; margin-bottom: 12px; }
  .detail-card h3 { font-size: 0.95rem; font-weight: 600; margin: 16px 0 8px; color: #6e6e73; }
  .meta { font-size: 0.9rem; color: #6e6e73; }
  .meta span { margin-right: 16px; }
  .transcript { white-space: pre-wrap; font-size: 0.9rem; line-height: 1.7; }
  .segment { font-family: "SF Mono", Menlo, Consolas, monospace; font-size: 0.85rem; margin-bottom: 4px; }
  .segment .ts { color: #0066cc; font-weight: 600; margin-right: 8px; }
  .snippet { color: #6e6e73; font-size: 0.85rem; max-width: 500px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .drive-link { display: inline-block; margin-top: 8px; padding: 6px 14px; border: 1px solid #d1d1d6; border-radius: 8px; font-size: 0.9rem; background: #fff; }
  .drive-link:hover { background: #f5f5f7; text-decoration: none; }
</style>
</head>
<body>
<div class="container">
  <div id="app"></div>
</div>
<script>
const app = document.getElementById("app");

function router() {
  const params = new URLSearchParams(location.search);
  const id = params.get("id");
  if (id) return showDetail(id);
  showList();
}

/* ---- List view ---- */
async function showList() {
  const q = new URLSearchParams(location.search).get("q");
  let files;
  if (q) {
    const res = await fetch("/api/search?q=" + encodeURIComponent(q));
    files = await res.json();
  } else {
    const res = await fetch("/api/files");
    files = await res.json();
  }
  app.innerHTML =
    '<h1>drivedb</h1>' +
    '<div class="search-bar">' +
      '<input id="searchInput" type="text" placeholder="Search transcripts..." value="' + escHtml(q || "") + '">' +
      '<button onclick="doSearch()">Search</button>' +
    '</div>' +
    (files.length === 0
      ? '<div class="empty">No recordings found.</div>'
      : '<table><thead><tr><th>Name</th><th>Format</th><th>Duration</th><th>Created</th><th>Tags</th></tr></thead><tbody>' +
        files.map(f =>
          '<tr style="cursor:pointer" onclick="location.href=\\'?id=' + f.id + '\\'">' +
            '<td>' + escHtml(f.fileName) + (f.snippet ? '<br><span class="snippet">' + (f.timestamp ? '[' + escHtml(f.timestamp) + '] ' : '') + escHtml(f.snippet) + '</span>' : '') + '</td>' +
            '<td class="mono">' + escHtml(f.format || '-') + '</td>' +
            '<td class="mono">' + escHtml(f.duration || '-') + '</td>' +
            '<td class="mono">' + escHtml((f.createdAt || "").slice(0, 19).replace("T", " ")) + '</td>' +
            '<td class="mono">' + escHtml(f.tags || '') + '</td>' +
          '</tr>'
        ).join("") +
        '</tbody></table>'
    );
  const input = document.getElementById("searchInput");
  if (input) input.addEventListener("keydown", e => { if (e.key === "Enter") doSearch(); });
}

function doSearch() {
  const v = document.getElementById("searchInput").value.trim();
  location.href = v ? "/?q=" + encodeURIComponent(v) : "/";
}

/* ---- Detail view ---- */
async function showDetail(id) {
  const res = await fetch("/api/files/" + encodeURIComponent(id));
  if (res.status === 404) {
    app.innerHTML = '<h1>Not found</h1><p><a href="/">Back to list</a></p>';
    return;
  }
  const f = await res.json();
  const segmentsHtml = (f.segments || []).map(s =>
    '<div class="segment"><span class="ts">[' + escHtml(s.timestamp) + ']</span>' + escHtml(s.text) + '</div>'
  ).join("");

  app.innerHTML =
    '<a href="/" class="back-link">&larr; Back to list</a>' +
    '<div class="detail-card">' +
      '<h2>' + escHtml(f.fileName) + '</h2>' +
      '<div class="meta">' +
        '<span>Format: ' + escHtml(f.format || "-") + '</span>' +
        '<span>Duration: ' + escHtml(f.duration || "-") + '</span>' +
        '<span>Created: ' + escHtml((f.createdAt || "").slice(0, 19).replace("T", " ")) + '</span>' +
        (f.tags ? '<span>Tags: ' + escHtml(f.tags) + '</span>' : '') +
      '</div>' +
      (f.driveFileLink ? '<a href="' + escAttr(f.driveFileLink) + '" target="_blank" rel="noopener" class="drive-link">Open in Drive</a>' : '') +
    '</div>' +
    (f.summary
      ? '<div class="detail-card"><h2>Summary</h2><p class="transcript">' + escHtml(f.summary) + '</p></div>'
      : '') +
    '<div class="detail-card">' +
      '<h2>Transcript</h2>' +
      (segmentsHtml
        ? '<div class="transcript">' + segmentsHtml + '</div>'
        : '<p class="transcript">' + escHtml(f.transcript || "(no transcript)") + '</p>') +
    '</div>';
}

/* ---- Utilities ---- */
function escHtml(s) {
  const d = document.createElement("div");
  d.textContent = s;
  return d.innerHTML;
}
function escAttr(s) {
  return s.replace(/&/g,"&amp;").replace(/"/g,"&quot;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}

router();
window.addEventListener("popstate", router);
</script>
</body>
</html>`;

// ---------------------------------------------------------------------------
// Server
// ---------------------------------------------------------------------------

function json(res: ServerResponse, data: unknown, status = 200): void {
  const body = JSON.stringify(data);
  res.writeHead(status, {
    "Content-Type": "application/json",
    "Content-Length": Buffer.byteLength(body),
  });
  res.end(body);
}

export async function startServer(port: number): Promise<void> {
  const db = initDb();
  const dbHandle = db.db; // better-sqlite3 Database instance

  const server = createServer((req: IncomingMessage, res: ServerResponse) => {
    // Parse the incoming request's URL path and query params.
    // This does NOT make any outbound network request — it only parses a string.
    const url = new URL(req.url ?? "/", "http://localhost");
    const pathname = url.pathname;

    try {
      // GET / — serve the HTML shell
      if (pathname === "/" && req.method === "GET") {
        res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
        res.end(HTML_PAGE);
        return;
      }

      // GET /api/files — list all files
      if (pathname === "/api/files" && req.method === "GET") {
        const files = listFiles(dbHandle);
        json(res, files);
        return;
      }

      // GET /api/files/:id — single file + segments
      const fileMatch = pathname.match(/^\/api\/files\/(\d+)$/);
      if (fileMatch && req.method === "GET") {
        const id = Number(fileMatch[1]);
        const file = getFileById(dbHandle, id);
        if (!file) {
          json(res, { error: "not found" }, 404);
          return;
        }
        const segments = getSegmentsByFileId(dbHandle, id);
        json(res, {
          ...file,
          segments: segments.map((s) => ({
            startMs: s.startMs,
            endMs: s.endMs,
            text: s.text,
            timestamp: formatMs(s.startMs),
          })),
        });
        return;
      }

      // GET /api/search?q=...
      if (pathname === "/api/search" && req.method === "GET") {
        const q = url.searchParams.get("q");
        if (!q) {
          json(res, []);
          return;
        }
        const results = searchFiles(dbHandle, q);
        json(
          res,
          results.map((r) => ({
            ...r,
            timestamp: r.startMs !== null ? formatMs(r.startMs) : null,
          })),
        );
        return;
      }

      // Anything else → 404
      json(res, { error: "not found" }, 404);
    } catch (err) {
      console.error("server error:", err);
      json(res, { error: "internal server error" }, 500);
    }
  });

  await new Promise<void>((resolve, reject) => {
    server.on("error", (err: Error) => {
      if ((err as NodeJS.ErrnoException).code === "EADDRINUSE") {
        reject(new Error(`Port ${port} is already in use. Try another port with -p.`));
      } else {
        reject(err);
      }
    });
    server.listen(port, "127.0.0.1", () => {
      resolve();
    });
  });

  console.log(`drivedb web UI running at http://127.0.0.1:${port}`);

  // Keep the process alive — the caller (cli.ts) awaits startServer which
  // resolves after listen(). The process stays up because the HTTP server
  // holds the event loop open until the user hits Ctrl+C.
}
