const http = require("http");
const { execFile } = require("child_process");
const path = require("path");

const PORT = 8787;
const ZCODE_ENTRY = "/Applications/ZCode.app/Contents/Resources/glm/zcode.cjs";
const ZCODE_CWD = path.join(require("os").tmpdir(), "esp32-zcode-chat");

require("fs").mkdirSync(ZCODE_CWD, { recursive: true });

function askZcode(prompt, callback) {
  execFile(
    "node",
    [
      ZCODE_ENTRY,
      "-p",
      prompt,
      "--cwd",
      ZCODE_CWD,
      "--disallowedTools",
      "Edit Write Bash",
    ],
    { timeout: 60_000, maxBuffer: 10 * 1024 * 1024 },
    (err, stdout, stderr) => {
      if (err) {
        callback(`[error] ${err.message}`);
        return;
      }
      callback(stdout.trim());
    }
  );
}

const server = http.createServer((req, res) => {
  if (req.method !== "POST" || req.url !== "/ask") {
    res.writeHead(404, { "content-type": "application/json" });
    res.end(JSON.stringify({ error: "POST /ask only" }));
    return;
  }

  let body = "";
  req.on("data", (chunk) => (body += chunk));
  req.on("end", () => {
    let prompt;
    try {
      prompt = JSON.parse(body).prompt;
    } catch {
      res.writeHead(400, { "content-type": "application/json" });
      res.end(JSON.stringify({ error: "invalid json body, expected {prompt}" }));
      return;
    }
    if (!prompt || typeof prompt !== "string") {
      res.writeHead(400, { "content-type": "application/json" });
      res.end(JSON.stringify({ error: "missing prompt string" }));
      return;
    }

    console.log(`[esp32] ${prompt}`);
    askZcode(prompt, (answer) => {
      console.log(`[zcode] ${answer}`);
      res.writeHead(200, { "content-type": "application/json" });
      res.end(JSON.stringify({ answer }));
    });
  });
});

server.listen(PORT, "0.0.0.0", () => {
  console.log(`zcode bridge listening on http://0.0.0.0:${PORT}/ask`);
});
