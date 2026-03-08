# Context Compact 정책 (C6)

Spacebot Compactor 개념을 재해석한 context 압력 관리 정책.

## 개요

Spacebot은 context 점유율을 3단계(80/85/95%)로 감시하고 자동 압축한다.
Maestro에서는 Claude Code의 auto-compact + orchestrate wave 중간 검증으로 대체한다.

## 압력 단계

| 단계 | 점유율 | Spacebot 동작 | Maestro 대응 |
|------|--------|---------------|-------------|
| NORMAL | < 80% | - | 정상 작업 |
| WARNING | 80-85% | 알림 | orchestrate wave 중간 검증 실행, 불필요 context 정리 |
| CRITICAL | 85-95% | 자동 압축 | Claude Code strategic-compact 활용, handoff 문서 작성 |
| OVERFLOW | > 95% | 강제 분할 | 세션 종료 + handoff → 새 세션에서 재개 |

## 적용 방식

### 1. 단일 세션 작업

Claude Code의 내장 auto-compact에 의존한다.
OMC의 `<remember>` 태그로 핵심 정보를 보존한다.

```
<remember priority>아키텍처 결정: JWT + Redis 세션 방식 채택</remember>
```

### 2. orchestrate wave 모드

wave 단위(20-40 tasks)로 자연스럽게 context가 분할된다.
Phase 2(Cross-Review Gate)에서 중간 검증 시:

- 이전 wave의 context를 handoff 문서로 기록
- 다음 wave는 handoff + contracts만 참조하여 시작
- 이전 wave의 상세 context는 폐기

### 3. 대규모 작업 (80+ tasks)

```
wave 1 (tasks 1-30)
  → Phase 2 검증 → handoff 작성
  → context 정리
wave 2 (tasks 31-60)
  → handoff 참조 + contracts 기반 작업
  → Phase 2 검증 → handoff 작성
  → context 정리
wave 3 (tasks 61-80+)
  → ...
```

## handoff에 포함할 정보

| 항목 | 필수 여부 | 설명 |
|------|----------|------|
| 완료 태스크 목록 | 필수 | ID + 산출물 경로 |
| 핵심 결정 사항 | 필수 | 아키텍처/기술 선택 |
| contracts 경로 | 필수 | API 계약 파일 위치 |
| 미해결 이슈 | 필수 | 차단 요소, 기술 부채 |
| 상세 구현 메모 | 선택 | 다음 wave에서 참고할 팁 |

## 모니터링

현재는 수동 판단에 의존한다.
향후 Claude Code의 context usage API가 제공되면 자동화 검토.

## 관련 문서

- `docs/work-log/handoff-template.md` — handoff 문서 포맷
- `docs/work-log/spacebot-concept-mapping.md` — Spacebot 개념 매핑
- `.claude/skills/orchestrate-standalone/SKILL.md` — wave 모드 상세
