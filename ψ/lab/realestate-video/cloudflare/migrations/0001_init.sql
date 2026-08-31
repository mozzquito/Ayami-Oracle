CREATE TABLE jobs (
  id TEXT PRIMARY KEY,
  status TEXT NOT NULL DEFAULT 'pending',
  input_json TEXT NOT NULL,
  script TEXT,
  script_cost_usd REAL,
  audio_url TEXT,
  voiceover_cost_usd REAL,
  video_url TEXT,
  error TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
