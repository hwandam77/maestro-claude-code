# TOP 5 GitHub 프로젝트 적용 보고서

**작성일**: 2026-03-10
**프로젝트**: Maestro Claude Code

## 개요

23개 유사 GitHub 프로젝트를 조사하여 TOP 5를 선정하고, 핵심 패턴을 Maestro Claude Code에 적용하였다.

## 적용된 프로젝트 및 패턴

### 1. claude-code-mux (9j/claude-code-mux) → subagent-router.py 강화

**차용한 패턴**: CCM-SUBAGENT-MODEL 환경변수 기반 모델 오버라이드

**구현 내용**:
- `MAESTRO_SUBAGENT_MODEL` 전역 ENV 오버라이드
- `MAESTRO_MODEL_{AGENT_NAME}` 에이전트별 ENV 오버라이드
- 우선순위: per-agent ENV > global ENV > YAML config > default
- Provider failover 체인 (5개 모델 fallback 정의)
- 풍부한 힌트 파일 (agent, model, source, complexity_score, failover_chain, timestamp)

**수정 파일**: `.claude/hooks/subagent-router.py`

### 2. MassGen (massgen/MassGen) → 비용 추적 시스템

**차용한 패턴**: LiteLLM 비용 추적 + 대시보드 메트릭

**구현 내용**:
- 7개 모델 가격 데이터베이스 (TOKEN 단가 + 고정 비용)
- `estimate_cost()`: 모델별 비용 추정
- `log_cost()`: JSONL 일별 비용 로그
- `get_daily_summary()` / `get_monthly_summary()`: 비용 집계
- CLI 인터페이스 (daily/monthly/estimate/log 서브커맨드)
- SQLite 스키마 확장: input_tokens, output_tokens, cost_usd, agent_name, complexity_score, routing_source
- daily_costs 테이블 신규

**신규 파일**: `tools/cost-tracker.py`
**수정 파일**: `tools/observability/schema.sql`

### 3. NadirClaw (doramirdor/NadirClaw) + RouteLLM → 복잡도 기반 자동 라우팅

**차용한 패턴**: 프롬프트 복잡도 분석 → 모델 자동 선택

**구현 내용**:
- 5가지 복잡도 요인 (길이, 키워드, 코드 지표, 도메인, 치명도)
- 4단계 티어: SIMPLE(0-2) → MODERATE(3-5) → COMPLEX(6-8) → CRITICAL(9+)
- 도메인 감지: security→claude, ui→gemini, analysis→qwen3.5, code→codex
- 자동 에스컬레이션: cheap 모델 + 높은 복잡도 → 상위 모델로 승격
- CLI 인터페이스: `python3 complexity-analyzer.py "프롬프트"`

**신규 파일**: `tools/complexity-analyzer.py`

### 4. everything-claude-code (affaan-m/everything-claude-code) → 대시보드 API 확장

**차용한 패턴**: /model-route 커맨드의 비용/복잡도 추적 + 품질 게이트

**구현 내용**:
- `GET /api/costs`: 24시간 모델/에이전트별 비용 요약
- `GET /api/costs/monthly?month=YYYY-MM`: 월간 비용 집계 + 활성 일수
- `GET /api/routing`: 라우팅 소스별 통계 + 복잡도 티어 분포
- POST /event에 신규 6개 필드 수신 지원

**수정 파일**: `tools/observability/server.ts`

### 5. sub-agents-mcp (shinpr/sub-agents-mcp) → 세션 추적 + 이벤트 확장

**차용한 패턴**: MCP 기반 세션 관리 + CLI 위임 메타데이터

**구현 내용**:
- 세션 ID 자동 생성/지속 (ENV → /tmp 파일 → UUID)
- 힌트 파일에서 complexity_score, routing_source 추출
- cost-tracker 연동 비용 추정 (graceful fallback)
- 이벤트 페이로드 7개 필드 확장
- LiteLLM callback: failover 체인 지원, 비용 로깅, 인메모리 메트릭

**수정 파일**: `.claude/hooks/send-event.py`, `tools/litellm_callback.py`

## 변경 파일 요약

| 파일 | 상태 | 변경 내용 |
|------|------|----------|
| `.claude/hooks/subagent-router.py` | 수정 | ENV 오버라이드 + failover + 복잡도 휴리스틱 |
| `.claude/hooks/send-event.py` | 수정 | 세션 추적 + 비용 추정 + 이벤트 확장 |
| `tools/litellm_callback.py` | 수정 | failover 체인 + 비용 로깅 + 메트릭 |
| `tools/observability/server.ts` | 수정 | 3개 API 엔드포인트 + insertEvent 확장 |
| `tools/observability/schema.sql` | 수정 | 6개 컬럼 + daily_costs 테이블 |
| `tools/cost-tracker.py` | 신규 | 비용 추적 모듈 (7개 모델, CLI) |
| `tools/complexity-analyzer.py` | 신규 | 복잡도 분석기 (4티어, 도메인 감지) |

## 검증 결과

| 테스트 | 결과 |
|--------|------|
| Python 구문 검증 (5개 파일) | ✅ 전체 통과 |
| 복잡도 분석: "fix typo" | ✅ SIMPLE → qwen3-coder-30b |
| 복잡도 분석: "security audit" | ✅ CRITICAL(23점) → claude-sonnet-4-6 |
| 복잡도 분석: "design CSS component" | ✅ ui 도메인 → gemini-3.1-pro |
| 비용 추정: claude-sonnet-4-6 1000토큰 | ✅ $0.006000 |
| 비용 추정: glm-5 5000토큰 | ✅ $0.000000 (고정비) |
| subagent-router: executor | ✅ gpt-5.4-medium (yaml_map) |
| subagent-router: ENV 오버라이드 | ✅ claude-opus (env_per_agent) |
| subagent-router: 복잡도 에스컬레이션 | ✅ explore glm-5→gpt-5.4-medium (complexity_escalation) |

## 아키텍처 변화

```
[이전]
SubagentStart → subagent-router.py → YAML 조회 → 힌트 파일 → litellm_callback

[이후]
SubagentStart → subagent-router.py
  ├── ENV 오버라이드 확인 (전역/에이전트별)
  ├── YAML 매핑 조회
  ├── 복잡도 분석 (키워드 + 도메인)
  ├── 에스컬레이션 판단 (cheap 모델 + 높은 복잡도)
  └── 풍부한 힌트 파일 기록 (model + failover + score)
       ├── litellm_callback → 모델 오버라이드 + failover + 비용 로깅
       └── send-event.py → 세션 추적 + 비용 추정 + 대시보드 전송
            └── server.ts → SQLite 저장 (확장 스키마)
                 ├── /api/costs → 비용 요약
                 ├── /api/costs/monthly → 월간 비용
                 └── /api/routing → 라우팅 통계
```

## 적용하지 않은 패턴 (향후 검토)

| 패턴 | 출처 | 이유 |
|------|------|------|
| MCP 서버 래핑 | sub-agents-mcp | 규모가 크고 현재 shell wrapper로 충분 |
| TUI 대시보드 | MassGen | Bun 웹 대시보드가 이미 존재 |
| BERT 기반 라우팅 | RouteLLM | ML 모델 의존성 추가 불필요 |
| WASM 보안 커널 | ruflo | 현재 규모에서 과잉 |
| Web UI 라우터 설정 | claude-code-router | YAML + ENV 방식이 더 유연 |
