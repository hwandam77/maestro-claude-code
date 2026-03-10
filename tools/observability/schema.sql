-- Maestro Claude Code 관찰성 데이터베이스 스키마
-- events 테이블: 모든 훅 이벤트 기록 (비용 추적 컬럼 포함)
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
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

  -- 비용 추적 컬럼
  input_tokens INTEGER DEFAULT 0,
  output_tokens INTEGER DEFAULT 0,
  cost_usd REAL DEFAULT 0.0,
  agent_name TEXT DEFAULT '',
  complexity_score INTEGER DEFAULT 0,
  routing_source TEXT DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_model ON events(model);
CREATE INDEX IF NOT EXISTS idx_events_created ON events(created_at);
CREATE INDEX IF NOT EXISTS idx_events_agent ON events(agent_name);

-- 일별 비용 요약 테이블
CREATE TABLE IF NOT EXISTS daily_costs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  date TEXT NOT NULL UNIQUE,
  total_cost REAL DEFAULT 0.0,
  total_calls INTEGER DEFAULT 0,
  total_input_tokens INTEGER DEFAULT 0,
  total_output_tokens INTEGER DEFAULT 0,
  by_model_json TEXT DEFAULT '{}',
  by_agent_json TEXT DEFAULT '{}',
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_daily_costs_date ON daily_costs(date);
