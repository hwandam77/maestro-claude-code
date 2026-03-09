# Phase 2 - 관찰성 대시보드 구현 보고서

**날짜**: 2026-03-09
**Phase**: 2 - Observability Layer

---

## 구현 내용

### 생성된 파일

| 파일 | 설명 |
|------|------|
| `tools/observability/package.json` | Bun 프로젝트 설정 |
| `tools/observability/schema.sql` | SQLite 스키마 (events 테이블 + 3개 인덱스) |
| `tools/observability/server.ts` | Bun HTTP 서버 (port 3456) |
| `tools/observability/public/index.html` | 실시간 대시보드 (순수 HTML+JS, Tailwind CDN) |
| `.claude/hooks/send-event.py` | Claude Code hook → 서버 이벤트 전송기 |

### 수정된 파일

| 파일 | 변경 내용 |
|------|----------|
| `.claude/settings.json` | 기존 3개 hook 유지 + 관찰성 hooks 추가 (PreToolUse/PostToolUse/Stop/SubagentStart/SubagentStop) |
| `scripts/ccproxy-start.sh` | `--with-dashboard` 플래그 / `WITH_DASHBOARD=true` 대시보드 자동 시작 옵션 추가 |

---

## 아키텍처

```
Claude Code hook 이벤트
  └─> send-event.py (stdin JSON 파싱)
        └─> POST http://localhost:3456/event
              └─> Bun server.ts (SQLite 저장)
                    └─> GET /api/stats, /api/events
                          └─> public/index.html (5초 폴링)
```

---

## API 명세

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/event` | POST | hook 이벤트 수신 및 SQLite 저장 |
| `/api/stats` | GET | 24시간 모델별 + 이벤트타입별 통계 |
| `/api/events?limit=N` | GET | 최근 N개 이벤트 목록 (최대 200) |
| `/` | GET | 대시보드 HTML 서빙 |

---

## 모델별 컬러 코드

| 모델 | 색상 | HEX |
|------|------|-----|
| GLM-5 | 초록 | `#4CAF50` |
| Qwen3-Coder | 파랑 | `#2196F3` |
| Qwen3.5 | 보라 | `#9C27B0` |
| Gemini | 주황 | `#FF9800` |
| Codex/GPT | 빨강 | `#F44336` |
| Claude | 금색 | `#FFD700` |

---

## 검증 결과

| 항목 | 결과 |
|------|------|
| Bun 서버 port 3456 응답 | PASS |
| `GET /api/stats` JSON 반환 | PASS (`total_24h`, `by_model`, `by_event_type` 포함) |
| `POST /event` SQLite 저장 | PASS (이벤트 2개 누적 확인) |
| `GET /api/events` 목록 반환 | PASS (count: 2 확인) |
| send-event.py 정상 실행 | PASS (exit code 0) |
| send-event.py 서버 미실행 시 실패 방지 | PASS (exit code 0, 예외 무시) |

---

## 실행 방법

```bash
# 대시보드 단독 시작
cd tools/observability && bun run start

# ccproxy와 함께 시작
WITH_DASHBOARD=true ./scripts/ccproxy-start.sh start

# 개발 모드 (hot reload)
cd tools/observability && bun run dev

# 브라우저에서 확인
open http://localhost:3456
```

---

## 참고사항

- 대시보드가 미실행 상태여도 Claude Code hook 동작에 영향 없음 (timeout 3초, 예외 전체 무시)
- SQLite DB 위치: `tools/observability/events.db` (자동 생성)
- 이벤트 수집 범위: PreToolUse, PostToolUse, Stop, SubagentStart, SubagentStop
- 외부 npm 패키지 없음 (Bun 내장 API + SQLite만 사용)
