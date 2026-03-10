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
  INSERT INTO events (event_type, session_id, tool_name, model, rule_matched, token_count, latency_ms, status, error_msg, payload, input_tokens, output_tokens, cost_usd, agent_name, complexity_score, routing_source)
  VALUES ($event_type, $session_id, $tool_name, $model, $rule_matched, $token_count, $latency_ms, $status, $error_msg, $payload, $input_tokens, $output_tokens, $cost_usd, $agent_name, $complexity_score, $routing_source)
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

// 비용 집계 - 24시간, 모델별
const queryCosts = db.prepare(`
  SELECT
    model,
    COUNT(*) as calls,
    SUM(input_tokens) as total_input_tokens,
    SUM(output_tokens) as total_output_tokens,
    SUM(cost_usd) as total_cost
  FROM events
  WHERE created_at >= datetime('now', '-24 hours') AND cost_usd > 0
  GROUP BY model
  ORDER BY total_cost DESC
`);

// 비용 집계 - 24시간, 에이전트별
const queryAgentCosts = db.prepare(`
  SELECT
    agent_name,
    COUNT(*) as calls,
    SUM(cost_usd) as total_cost
  FROM events
  WHERE created_at >= datetime('now', '-24 hours') AND agent_name != ''
  GROUP BY agent_name
  ORDER BY total_cost DESC
`);

// 라우팅 통계 - 24시간
const queryRouting = db.prepare(`
  SELECT
    routing_source,
    COUNT(*) as count,
    AVG(complexity_score) as avg_complexity
  FROM events
  WHERE created_at >= datetime('now', '-24 hours') AND routing_source != ''
  GROUP BY routing_source
`);

// 월간 비용 집계 - 모델별
const queryCostsMonthly = db.prepare(`
  SELECT
    model,
    COUNT(*) as calls,
    SUM(input_tokens) as total_input_tokens,
    SUM(output_tokens) as total_output_tokens,
    SUM(cost_usd) as total_cost
  FROM events
  WHERE strftime('%Y-%m', created_at) = $month AND cost_usd > 0
  GROUP BY model
  ORDER BY total_cost DESC
`);

// 월간 비용 집계 - 에이전트별
const queryAgentCostsMonthly = db.prepare(`
  SELECT
    agent_name,
    COUNT(*) as calls,
    SUM(cost_usd) as total_cost
  FROM events
  WHERE strftime('%Y-%m', created_at) = $month AND agent_name != ''
  GROUP BY agent_name
  ORDER BY total_cost DESC
`);

// 월간 활성 일수
const queryMonthlyDays = db.prepare(`
  SELECT COUNT(DISTINCT date(created_at)) as days_active
  FROM events
  WHERE strftime('%Y-%m', created_at) = $month
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
          $input_tokens: body.input_tokens != null ? Number(body.input_tokens) : 0,
          $output_tokens: body.output_tokens != null ? Number(body.output_tokens) : 0,
          $cost_usd: body.cost_usd != null ? Number(body.cost_usd) : 0.0,
          $agent_name: String(body.agent_name ?? ""),
          $complexity_score: body.complexity_score != null ? Number(body.complexity_score) : 0,
          $routing_source: String(body.routing_source ?? ""),
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

    // GET /api/costs - 비용 요약 (24시간)
    if (method === "GET" && path === "/api/costs") {
      const byModel = queryCosts.all() as Array<{
        model: string; calls: number;
        total_input_tokens: number; total_output_tokens: number; total_cost: number;
      }>;
      const byAgent = queryAgentCosts.all() as Array<{
        agent_name: string; calls: number; total_cost: number;
      }>;
      const totalCost = byModel.reduce((sum, r) => sum + (r.total_cost ?? 0), 0);
      return jsonResponse({
        total_cost: totalCost,
        by_model: byModel.map(r => ({
          model: r.model,
          calls: r.calls,
          cost: r.total_cost,
          input_tokens: r.total_input_tokens,
          output_tokens: r.total_output_tokens,
        })),
        by_agent: byAgent.map(r => ({
          agent: r.agent_name,
          calls: r.calls,
          cost: r.total_cost,
        })),
        generated_at: new Date().toISOString(),
      });
    }

    // GET /api/costs/monthly?month=YYYY-MM - 월간 비용 요약
    if (method === "GET" && path === "/api/costs/monthly") {
      const month = url.searchParams.get("month") ??
        new Date().toISOString().slice(0, 7); // 기본값: 현재 월
      const byModel = queryCostsMonthly.all({ $month: month }) as Array<{
        model: string; calls: number;
        total_input_tokens: number; total_output_tokens: number; total_cost: number;
      }>;
      const byAgent = queryAgentCostsMonthly.all({ $month: month }) as Array<{
        agent_name: string; calls: number; total_cost: number;
      }>;
      const daysRow = queryMonthlyDays.get({ $month: month }) as { days_active: number };
      const totalCost = byModel.reduce((sum, r) => sum + (r.total_cost ?? 0), 0);
      return jsonResponse({
        month,
        total_variable: totalCost,
        total_fixed: 0,       // 고정 비용(구독료 등)은 외부 입력 필요
        total_cost: totalCost,
        by_model: byModel.map(r => ({
          model: r.model,
          calls: r.calls,
          cost: r.total_cost,
          input_tokens: r.total_input_tokens,
          output_tokens: r.total_output_tokens,
        })),
        by_agent: byAgent.map(r => ({
          agent: r.agent_name,
          calls: r.calls,
          cost: r.total_cost,
        })),
        days_active: daysRow?.days_active ?? 0,
        generated_at: new Date().toISOString(),
      });
    }

    // GET /api/routing - 라우팅 통계 (24시간)
    if (method === "GET" && path === "/api/routing") {
      const rows = queryRouting.all() as Array<{
        routing_source: string; count: number; avg_complexity: number | null;
      }>;
      const totalRouted = rows.reduce((sum, r) => sum + r.count, 0);

      // complexity_tier 별 집계는 별도 컬럼 없을 경우 avg_complexity로 추정
      const byComplexity: Array<{ tier: string; count: number; avg_score: number }> = [];
      // 티어 구간: 0-2 SIMPLE, 3-5 MODERATE, 6-8 COMPLEX, 9+ CRITICAL
      const tierMap: Record<string, { count: number; scoreSum: number }> = {
        SIMPLE: { count: 0, scoreSum: 0 },
        MODERATE: { count: 0, scoreSum: 0 },
        COMPLEX: { count: 0, scoreSum: 0 },
        CRITICAL: { count: 0, scoreSum: 0 },
      };
      for (const row of rows) {
        const avg = row.avg_complexity ?? 0;
        const tier = avg <= 2 ? "SIMPLE" : avg <= 5 ? "MODERATE" : avg <= 8 ? "COMPLEX" : "CRITICAL";
        tierMap[tier].count += row.count;
        tierMap[tier].scoreSum += avg * row.count;
      }
      for (const [tier, data] of Object.entries(tierMap)) {
        if (data.count > 0) {
          byComplexity.push({
            tier,
            count: data.count,
            avg_score: data.count > 0 ? data.scoreSum / data.count : 0,
          });
        }
      }

      return jsonResponse({
        total_routed: totalRouted,
        by_source: rows.map(r => ({ source: r.routing_source, count: r.count })),
        by_complexity: byComplexity,
        escalations: 0, // 에스컬레이션 카운트는 별도 이벤트 타입으로 추적 필요
        generated_at: new Date().toISOString(),
      });
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
