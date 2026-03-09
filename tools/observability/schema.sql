CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  event_type TEXT NOT NULL,
  session_id TEXT,
  tool_name TEXT,
  model TEXT,
  rule_matched TEXT,
  token_count INTEGER,
  latency_ms INTEGER,
  status TEXT,
  error_msg TEXT,
  payload TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_model ON events(model);
CREATE INDEX IF NOT EXISTS idx_events_created ON events(created_at);
