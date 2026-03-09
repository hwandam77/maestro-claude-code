/**
 * Maestro Observability Server
 * Bun HTTP 서버 - hook 이벤트 수신 + SQLite 저장 + 대시보드 서빙
 * Port: 3456
 */

import { Database } from "bun:sqlite";
import { readFileSync } from "fs";
import { join } from "path";

const PORT = 3456;
const DB_PATH = join(import.meta.dir, "events.db");
const SCHEMA_PATH = join(import.meta.dir, "schema.sql");
const PUBLIC_DIR = join(import.meta.dir, "public");

// SQLite 초기화
const db = new Database(DB_PATH, { create: true });
db.exec(readFileSync(SCHEMA_PATH, "utf-8"));

// Prepared statements
const insertEvent = db.prepare(`
  INSERT INTO events (event_type, session_id, tool_name, model, rule_matched, token_count, latency_ms, status, error_msg, payload)
  VALUES ($event_type, $session_id, $tool_name, $model, $rule_matched, $token_count, $latency_ms, $status, $error_msg, $payload)
`);

const queryStats = db.prepare(`
  SELECT
    model,
    COUNT(*) as call_count,
    SUM(CASE WHEN status = 'ok' THEN 1 ELSE 0 END) as success_count,
    SUM(CASE WHEN status != 'ok' THEN 1 ELSE 0 END) as error_count,
    AVG(latency_ms) as avg_latency_ms,
    MAX(created_at) as last_seen
  FROM events
  WHERE created_at >= datetime('now', '-24 hours')
  GROUP BY model
  ORDER BY call_count DESC
`);

const queryEventTypes = db.prepare(`
  SELECT
    event_type,
    COUNT(*) as count
  FROM events
  WHERE created_at >= datetime('now', '-24 hours')
  GROUP BY event_type
  ORDER BY count DESC
`);

const queryRecentEvents = db.prepare(`
  SELECT id, event_type, session_id, tool_name, model, status, error_msg, created_at
  FROM events
  ORDER BY id DESC
  LIMIT $limit
`);

const queryTotalCount = db.prepare(`
  SELECT COUNT(*) as total FROM events WHERE created_at >= datetime('now', '-24 hours')
`);

// JSON 응답 헬퍼
function jsonResponse(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "Content-Type": "application/json",
      "Access-Control-Allow-Origin": "*",
    },
  });
}

// HTML 서빙 헬퍼
function serveFile(filePath: string): Response {
  try {
    const content = readFileSync(filePath, "utf-8");
    const ext = filePath.split(".").pop() ?? "";
    const contentTypes: Record<string, string> = {
      html: "text/html; charset=utf-8",
      js: "application/javascript",
      css: "text/css",
    };
    return new Response(content, {
      headers: { "Content-Type": contentTypes[ext] ?? "text/plain" },
    });
  } catch {
    return new Response("Not Found", { status: 404 });
  }
}

// HTTP 서버
const server = Bun.serve({
  port: PORT,
  async fetch(req: Request): Promise<Response> {
    const url = new URL(req.url);
    const method = req.method;
    const path = url.pathname;

    // CORS preflight
    if (method === "OPTIONS") {
      return new Response(null, {
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
          "Access-Control-Allow-Headers": "Content-Type",
        },
      });
    }

    // POST /event - 이벤트 수신
    if (method === "POST" && path === "/event") {
      try {
        const body = await req.json() as Record<string, unknown>;
        insertEvent.run({
          $event_type: String(body.event_type ?? "Unknown"),
          $session_id: String(body.session_id ?? ""),
          $tool_name: String(body.tool_name ?? ""),
          $model: String(body.model ?? ""),
          $rule_matched: String(body.rule_matched ?? ""),
          $token_count: body.token_count != null ? Number(body.token_count) : null,
          $latency_ms: body.latency_ms != null ? Number(body.latency_ms) : null,
          $status: String(body.status ?? "ok"),
          $error_msg: String(body.error_msg ?? ""),
          $payload: String(body.payload ?? ""),
        });
        return jsonResponse({ ok: true });
      } catch (err) {
        return jsonResponse({ ok: false, error: String(err) }, 400);
      }
    }

    // GET /api/stats - 모델별 통계
    if (method === "GET" && path === "/api/stats") {
      const stats = queryStats.all();
      const eventTypes = queryEventTypes.all();
      const totalRow = queryTotalCount.get() as { total: number };
      return jsonResponse({
        total_24h: totalRow?.total ?? 0,
        by_model: stats,
        by_event_type: eventTypes,
        generated_at: new Date().toISOString(),
      });
    }

    // GET /api/events?limit=50 - 최근 이벤트 목록
    if (method === "GET" && path === "/api/events") {
      const limit = Math.min(Number(url.searchParams.get("limit") ?? 50), 200);
      const events = queryRecentEvents.all({ $limit: limit });
      return jsonResponse({ events, count: events.length });
    }

    // GET / - 대시보드 HTML
    if (method === "GET" && (path === "/" || path === "/index.html")) {
      return serveFile(join(PUBLIC_DIR, "index.html"));
    }

    // 정적 파일
    if (method === "GET") {
      return serveFile(join(PUBLIC_DIR, path));
    }

    return new Response("Not Found", { status: 404 });
  },
});

console.log(`[Maestro Observability] 서버 시작: http://localhost:${PORT}`);
console.log(`[Maestro Observability] DB: ${DB_PATH}`);
