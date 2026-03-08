# Spacebot 개념 매핑 문서 (B5)

## 개요

Spacebot(spacedriveapp/spacebot)은 Rust + Tokio + Rig 기반 AI 에이전트 시스템이다.
코드 이식은 불가하나, 운영 철학과 아키텍처 개념을 claude-imple-skills 구조에 재해석한다.

## 개념 매핑 테이블

| Spacebot 개념 | 설명 | Maestro 대응 | 구현 위치 |
|---------------|------|-------------|-----------|
| **Channel** | 대화 전담, heavy task 미수행 | Claude Code 오케스트레이터 역할 | `claude` CLI (구독) |
| **Branch** | 독립 사고 단위 | orchestrate-standalone의 **wave** 단위 | `.claude/skills/orchestrate-standalone` |
| **Worker** | task 전용 프로세스 | multi-ai-run의 CLI 위임 | `routing.config.yaml` → codex/gemini/wrapper |
| **Compactor** | context 점유율 감시 (80/85/95%) | orchestrate wave 중간 검증 + OMC strategic-compact | wave Phase 2 (Cross-Review Gate) |
| **Cortex-lite** | 운영 가시성 (로그, 메트릭) | run log + quality gate 결과 기록 | `artifacts/runs/` |
| **다중 프로바이더 fallback** | Provider chain | `routing.config.yaml` fallback_enabled | defaults.fallback_enabled: true |

## 상세 매핑

### Channel → Claude Code 오케스트레이터

Spacebot에서 Channel은 사용자 대화만 담당하고 무거운 작업을 직접 수행하지 않는다.
Maestro에서는 Claude Code(구독)가 이 역할을 한다:
- 사용자 의도 파악 및 태스크 분해
- OMC 에이전트 또는 multi-ai-run으로 위임
- 결과 수집 및 보고

### Branch → Wave 단위

Spacebot의 Branch는 독립적 사고 단위로, 각각 자체 context를 가진다.
orchestrate-standalone의 wave가 이에 대응:
- Wave 크기: 20-40 tasks
- 각 wave는 독립적으로 병렬 실행
- wave 간 중간 검증으로 일관성 보장

### Worker → CLI 위임

Spacebot Worker가 task 전용 프로세스인 것처럼,
multi-ai-run이 역할별 CLI에 태스크를 위임:
- codex exec: 코드 생성/리뷰 (gpt-5.3-codex)
- gemini: UI/디자인 (gemini-3.1-pro)
- qwen35-cli.sh: 고급 추론 (nexus, 400K context)
- qwen-coder-cli.sh: 경량 코드 생성 (cognit, 16K context)

### Compactor → Wave 중간 검증

Spacebot Compactor의 context 압력 감지(80/85/95%)를 직접 구현하지 않는다.
대신 orchestrate wave의 Phase 2(Cross-Review Gate)가 유사 기능을 수행:
- 각 에이전트가 다른 에이전트 결과물 검토
- contract 준수 검증
- 중복/불일치 탐지

## 제외 사항 및 사유

| Spacebot 기능 | 제외 사유 |
|---------------|-----------|
| Memory Graph | Rust 전용 구현, OMC notepad + memory 스킬로 대체 |
| Secret Store | .env + Claude Code 내장 보안으로 충분 |
| Subprocess Containment | Claude Code sandbox + codex --sandbox로 대체 |
| 메시징 어댑터 (Discord 등) | CLI 도구이므로 불필요 |
| Cron Jobs | Claude Code에는 해당 없음 |
