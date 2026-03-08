# Handoff 문서 포맷 (B6)

Everything Claude Code(ECC)의 session lifecycle 패턴에서 차용.
에이전트 간 또는 세션 간 작업 인계 시 사용하는 표준 포맷.

## 템플릿

```yaml
# === HANDOFF DOCUMENT ===
handoff:
  from: "<에이전트 또는 세션 ID>"
  to: "<대상 에이전트 또는 다음 세션>"
  timestamp: "<ISO 8601>"
  phase: "<현재 Phase>"

context:
  objective: "<작업 목표 한 줄 요약>"
  decisions:
    - "<핵심 결정 1>"
    - "<핵심 결정 2>"
  constraints:
    - "<제약 조건>"

progress:
  completed:
    - task: "<완료 태스크>"
      artifacts: ["<산출물 경로>"]
  in_progress:
    - task: "<진행 중 태스크>"
      status: "<진행률 또는 상태>"
      blockers: ["<차단 요소>"]
  remaining:
    - task: "<미착수 태스크>"
      priority: "<high/medium/low>"

environment:
  branch: "<git 브랜치>"
  last_commit: "<커밋 해시>"
  failing_tests: ["<실패 테스트>"]
  open_issues: ["<미해결 이슈>"]

notes: |
  <자유 형식 메모, 주의사항, 팁>
```

## 사용 시점

| 시점 | 용도 |
|------|------|
| Phase 전환 | 이전 Phase 결과를 다음 Phase에 전달 |
| 세션 종료 | 다음 세션에서 이어서 작업할 수 있도록 상태 기록 |
| 에이전트 위임 | orchestrate에서 worker에게 태스크 전달 시 컨텍스트 공유 |
| 장애/중단 복구 | /recover 스킬에서 참조하여 작업 재개 |

## 예시

```yaml
handoff:
  from: "orchestrator-wave-1"
  to: "orchestrator-wave-2"
  timestamp: "2026-03-08T10:00:00+09:00"
  phase: "Phase B"

context:
  objective: "사용자 인증 모듈 구현"
  decisions:
    - "JWT + refresh token 방식 채택"
    - "Redis 세션 저장소 사용"
  constraints:
    - "기존 /api/v1 경로 호환 유지"

progress:
  completed:
    - task: "T1.1 - Auth API 설계"
      artifacts: ["contracts/auth-api.yaml"]
    - task: "T1.2 - JWT 유틸 구현"
      artifacts: ["src/utils/jwt.ts"]
  in_progress:
    - task: "T1.3 - 미들웨어 통합"
      status: "70%"
      blockers: ["Redis 연결 설정 미완료"]
  remaining:
    - task: "T1.4 - 통합 테스트"
      priority: "high"

environment:
  branch: "feature/auth-module"
  last_commit: "a1b2c3d"
  failing_tests: []
  open_issues: ["Redis 연결 타임아웃 설정"]

notes: |
  Redis 호스트는 .env의 REDIS_URL에서 읽도록 구현 중.
  cognit 서버의 Qwen-Coder는 JWT 유틸 코드 생성에 활용됨.
```
