# Maestro Claude Code 고도화 종합계획서

<!-- markdownlint-disable MD013 -->

작성자: hwandam77
작성일: 2026-03-07
문서 상태: v4 (ccr 제거 + claude-imple-skills 기반 전환)

## 0. Task Contract

- Task ID: `DOC-PLAN-2026-03-07-02`
- Input:
  - 이전 계획서 v3 (참고 저장소 교차 검증 반영)
  - ccr(claude-code-router) 제거 결정 및 실행 완료
  - claude-imple-skills 설치 확인 (심볼릭 링크, 글로벌)
  - 6개 모델 인프라 확정 (Claude 구독, GLM-5, gpt-5.3-codex, Gemini, Qwen3.5-122B, Qwen3-Coder-30B)
  - Cognit vLLM 구축 완료 (Qwen3-Coder-30B-A3B-Instruct AWQ-4bit, systemd)
  - 외부 참조 4종: spacebot, agent-council, everything-claude-code, claude-imple-skills
- 기대 출력:
  - ccr 제거 후 claude-imple-skills 기반 아키텍처를 반영한 고도화 계획서
- 검증 기준:
  - 삭제된 파일(ccr 관련)을 참조하지 않을 것
  - 현재 가용 인프라 6개 모델과 일치할 것
  - claude-imple-skills의 실제 기능(routing.config.yaml, multi-ai-run, project-team, hooks)에 기반할 것

## 1. 개요

본 문서는 `Maestro Claude Code`를 ccr(claude-code-router) 기반 API 프록시 구조에서 **claude-imple-skills 기반 CLI 레벨 멀티 AI 오케스트레이션** 구조로 전환하기 위한 종합 계획서다.

핵심 전환:

- **이전**: ccr 프록시(port 3456)가 Claude Code의 API 요청을 가로채 ZAI/OpenAI/vLLM으로 라우팅
- **이후**: Claude Code 구독을 기본으로 사용하고, claude-imple-skills의 multi-ai-run이 태스크 단위로 최적 CLI(claude/codex/gemini) + 자체 서버(nexus/cognit)에 위임

외부 참고 저장소에서의 차용 원칙:

- `spacebot` — 운영 모델 reference (Rust 기반, 코드 이식 불가, 개념만 재해석)
- `agent-council` — 선택적 sidecar 의사결정 도구 (multi-ai-review와 연계)
- `everything-claude-code` — hook/verify/session lifecycle 패턴 선별 도입
- `claude-imple-skills` — 핵심 기반 도구 (routing + agents + hooks + orchestration)

## 2. 목표 및 성공 기준

### 2.1 핵심 목표

- 목표 1: 6개 모델 체제의 역할별 라우팅 확정
  - 성공 기준: `routing.config.yaml`에 6개 모델이 역할별로 매핑되고 fallback이 정의된다.
- 목표 2: claude-imple-skills의 project-team 에이전트를 프로젝트에 맞게 커스텀
  - 성공 기준: 10개 에이전트의 CLI 할당이 현재 인프라와 일치한다.
- 목표 3: 자체 서버(nexus/cognit) 모델을 CLI로 활용 가능하게 래핑
  - 성공 기준: wrapper 스크립트가 nexus:8080, cognit:8000 API를 CLI처럼 호출한다.
- 목표 4: Spacebot 철학을 orchestrate-standalone의 wave/sprint 모드에 재해석
  - 성공 기준: Branch/Worker/Compactor 개념이 orchestrate 모드와 매핑 문서화된다.
- 목표 5: hook/verify/quality gate 체계 확립
  - 성공 기준: claude-imple-skills hooks(lite/standard/full)와 verify 순서가 적용된다.

### 2.2 비목표

- ccr 또는 API 프록시 구조의 재도입
- Spacebot 기능의 직접 포팅 (Rust + Rig 기반)
- Everything Claude Code 전체 플러그인 흡수
- Agent Council을 가중치 합의 플랫폼으로 확장

## 3. 현재 상태

### 3.1 인프라 (6개 모델)

| # | 모델 | 제공 | CLI/접근 | 용도 | Context |
|---|------|------|----------|------|---------|
| 1 | Claude (구독) | Anthropic | `claude` | 오케스트레이션, 아키텍처, 기획 | 200K |
| 2 | GLM-5 | ZAI Coding Plan ($3/월) | `claude-glm` (maestro.sh) | 저비용 Claude 대체 | - |
| 3 | gpt-5.3-codex | OpenAI | `codex exec` | 코드 생성, 리뷰, 테스트 | - |
| 4 | gemini-3.1-pro-preview | Google | `gemini` | 디자인, UI, 멀티모달 | - |
| 5 | Qwen3.5-122B (Q3_K_XL) | nexus (자체) | wrapper → :8080 | 고급 추론, 장문 컨텍스트 | 400K |
| 6 | Qwen3-Coder-30B-A3B (AWQ-4bit) | cognit (자체) | wrapper → :8000 | 코드 생성, 리팩토링 | 16K |

### 3.2 서버 현황

| 서버 | GPU | 서빙 | 포트 | systemd | 비고 |
|------|-----|------|------|---------|------|
| nexus | RTX 3090 x3 (72GB) | llama-server | 8080 | - | Qwen3.5-122B 상시 구동, VRAM ~63GB 사용 |
| cognit | RTX 3080 Ti x2 (24GB) | vLLM | 8000 | vllm-qwen3-coder.service (enabled) | GPU당 11.4GB/12GB, ollama도 공존 (port 11434) |

### 3.3 설치된 도구

- **Claude Code**: Anthropic 구독 (기본 `claude` 실행)
- **claude-imple-skills**: 심볼릭 링크로 설치됨 (`/Users/hwandam/workspace/claude-imple-skills/`)
  - multi-ai-run, multi-ai-review, orchestrate-standalone 미설치 (스킬 디렉터리 없음)
  - agile, architecture, changelog, checkpoint, coverage, deps, governance-setup, impact, quality-auditor, recover, tasks-init, tasks-migrate, workflow-guide — 설치됨
- **OMC (oh-my-claudecode)**: 기존 스킬/에이전트 다수 공존
- **scripts/maestro.sh**: ZAI(GLM-5) 모드 런처 (`claude-glm` 심볼릭 링크 예정)

### 3.4 삭제된 파일 (ccr 관련)

| 파일 | 사유 |
|------|------|
| config/config.template.json | ccr 스키마 설정 |
| config/config.json | ccr 런타임 생성물 |
| config/custom-router.js | ccr 에이전트 티어 매핑 (60개) |
| scripts/start.sh | ccr 시작 스크립트 |
| scripts/entrypoint.sh | Docker ccr 모드 |
| Dockerfile | ccr 기반 Docker |
| docker-compose.yml | ccr 컨테이너 |
| tests/t4_vllm_connection.sh | vLLM 연결 테스트 |
| tests/t5_phase1_verify.sh | ccr Phase 1 검증 |
| tests/t10_fallback_test.sh | ccr 폴백 테스트 |

## 4. 아키텍처

### 4.1 개요

```text
사용자 요청
  → Claude Code (구독, 오케스트레이터)
    → OMC 에이전트 (Claude Code 내부 subagent, 전부 같은 API)
    → claude-imple-skills multi-ai-run (태스크 위임)
      → codex exec (gpt-5.3-codex)     : 코드 생성/리뷰
      → gemini (gemini-3.1-pro)         : 디자인/UI
      → wrapper → nexus:8080 (Qwen3.5)  : 고급 추론
      → wrapper → cognit:8000 (Qwen3-Coder) : 코드 생성
    → claude-imple-skills hooks (품질 게이트)
    → claude-imple-skills orchestrate (wave/sprint 태스크 관리)
```

### 4.2 라우팅 계층

두 계층이 독립적으로 동작한다:

| 계층 | 시스템 | 라우팅 대상 | 설정 |
|------|--------|------------|------|
| **에이전트 내부** | OMC | Claude Code subagent (architect, executor 등) | 전부 Claude 구독 API |
| **태스크 위임** | claude-imple-skills | 역할별 CLI (codex/gemini/wrapper) | `routing.config.yaml` |

핵심: OMC의 에이전트와 claude-imple-skills의 project-team은 **별개 시스템**이며, 서로 간섭하지 않는다.

### 4.3 routing.config.yaml 설계

```yaml
version: 1.0

cli_models:
  claude:
    command: "claude"
    model: "sonnet"
    emoji: "🧠"

  codex:
    command: "codex exec"
    model: "gpt-5.3-codex"
    args: "--sandbox workspace-write"
    emoji: "🤖"

  gemini:
    command: "gemini"
    model: "gemini-3.1-pro-preview"
    args: "--output-format text"
    emoji: "💎"

  qwen35:
    command: "./scripts/qwen35-cli.sh"
    model: "Qwen3.5-122B"
    emoji: "🔮"

  qwen-coder:
    command: "./scripts/qwen-coder-cli.sh"
    model: "Qwen3-Coder-30B"
    emoji: "⚡"

  claude-glm:
    command: "./scripts/maestro.sh"
    model: "GLM-5"
    emoji: "🌐"

role_routing:
  # 전략/설계 → Claude
  orchestrator: claude
  project-manager: claude
  chief-architect: claude

  # 코드 구현 → Codex (gpt-5.3-codex)
  backend-specialist: codex
  test-specialist: codex
  api-designer: codex
  security-specialist: codex

  # 디자인/UI → Gemini
  frontend-specialist: gemini
  chief-designer: gemini

  # 고급 추론 → Qwen3.5-122B (nexus)
  # (400K context, 복잡한 분석)

  # 코드 생성 경량 → Qwen3-Coder-30B (cognit)
  # (16K context, 빠른 코드 생성)

task_type_routing:
  code_generation: codex
  code_review: codex
  refactoring: codex
  testing: codex
  ui_implementation: gemini
  design_review: gemini
  styling: gemini
  architecture: claude
  planning: claude
  coordination: claude

defaults:
  model: claude
  fallback_enabled: true
  timeout: 120
  retry_count: 2
```

### 4.4 wrapper 스크립트 설계

nexus/cognit의 OpenAI 호환 API를 CLI처럼 호출하는 래퍼:

```bash
# scripts/qwen35-cli.sh — nexus:8080 (Qwen3.5-122B, llama-server)
# scripts/qwen-coder-cli.sh — cognit:8000 (Qwen3-Coder-30B, vLLM)
#
# 공통 동작:
# 1. stdin 또는 인자로 프롬프트 수신
# 2. OpenAI 호환 API 호출 (curl → /v1/chat/completions)
# 3. 응답 텍스트를 stdout으로 출력
# 4. 서버 접근 불가 시 exit 1 (claude-imple-skills가 Claude fallback)
```

### 4.5 스위칭 체계

| 명령 | 백엔드 | 용도 |
|------|--------|------|
| `claude` | Anthropic 구독 | 기본 사용 |
| `claude-glm` (또는 `./scripts/maestro.sh`) | ZAI GLM-5 | 저비용 대체 |

## 5. 외부 소스 분석 (요약)

### 5.1 spacebot — 운영 모델 reference

Rust + Tokio + Rig v0.30 기반. 코드 이식 불가, 개념만 차용.

| 차용 개념 | 본 프로젝트 대응 |
|-----------|-----------------|
| Channel (대화 전담, heavy task 미수행) | Claude Code 오케스트레이터 역할 |
| Branch (독립 사고 단위) | orchestrate-standalone의 wave 단위 |
| Worker (task 전용 프로세스) | multi-ai-run의 CLI 위임 |
| Compactor (context 점유율 감시, 80/85/95%) | strategic-compact + orchestrate wave 중간 검증 |
| Cortex-lite (운영 가시성) | run log + quality gate 결과 기록 |
| 다중 프로바이더 fallback chain | routing.config.yaml fallback_enabled |

제외: memory graph, secret store, subprocess containment, 메시징 어댑터, Cron Jobs

### 5.2 agent-council — sidecar 의사결정

claude-imple-skills의 `multi-ai-review`가 council.config.yaml을 이미 포함.
upstream 3단계 구조(병렬 전달 → 수집 → chairman 종합)를 그대로 활용.

제외: weighted consensus engine, 추가 런타임 의존성

### 5.3 everything-claude-code — hook/verify 패턴

| 선별 도입 | 대응 |
|-----------|------|
| hook 이벤트 체계 (PreToolUse/PostToolUse/Stop) | claude-imple-skills hooks (lite/standard/full) |
| session lifecycle 스크립트 | claude-imple-skills project-team hooks |
| strategic compaction | orchestrate wave 중간 검증으로 대체 |
| verify 순서 (build→type→lint→test→security→git) | quality-auditor 스킬 활용 |
| AgentShield security scan | 별도 설치, CI exit code 2 |

제외: plugin 전체 흡수, ECC_HOOK_PROFILE 미검증 기능, continuous learning 기본 활성화

### 5.4 claude-imple-skills — 핵심 기반

이미 설치됨. 활용 범위:

| 기능 | 상태 | 활용 |
|------|------|------|
| multi-ai-run | 설치됨 | 6개 모델 라우팅의 핵심 |
| multi-ai-review | 설치됨 (council.config.yaml 포함) | 멀티 AI 코드 리뷰 |
| orchestrate-standalone | **미설치** | wave/sprint 오케스트레이션 — 설치 필요 |
| project-team (10 agents + 15 hooks) | **미설치** | 에이전트 팀 — 설치 필요 |
| quality-auditor | 설치됨 | 품질 게이트 |
| routing.config.yaml | 설치됨 (기본값) | 커스텀 필요 |

## 6. 설계 원칙

### 6.1 문서 우선

코드보다 문서가 먼저 명확해야 한다.

### 6.2 claude-imple-skills 기본 구조 존중

기존 스킬/에이전트 구조를 수정하지 않고, routing.config.yaml 커스텀과 wrapper 스크립트 추가로 확장한다.

### 6.3 의존성 명시

- 필수: Claude Code (구독), Node.js
- 선택: Codex CLI, Gemini CLI, nexus/cognit 서버 접근 (VPN)
- 서버 미접근 시: claude-imple-skills의 fallback으로 Claude가 직접 처리

### 6.4 서버명과 역할 분리

`nexus`, `cognit`는 물리 서버명. 라우팅에서는 `qwen35`, `qwen-coder` 등 모델 alias를 사용한다.

### 6.5 보안 우선

- council/multi-ai-review에 민감 정보 전달 금지
- wrapper 스크립트에 API 키 하드코딩 금지 (.env 참조)
- 각 CLI의 sandbox 모드 활용 (codex: `--sandbox workspace-write`)

## 7. Phase별 실행 계획

### Phase A — 기반 구축 (1-3일)

목표: 6개 모델 라우팅이 동작하는 최소 구조 확보

| # | 작업 | 산출물 |
|---|------|--------|
| A1 | routing.config.yaml 커스텀 (6개 모델) | `.claude/routing.config.yaml` |
| A2 | nexus wrapper 스크립트 (Qwen3.5-122B) | `scripts/qwen35-cli.sh` |
| A3 | cognit wrapper 스크립트 (Qwen3-Coder-30B) | `scripts/qwen-coder-cli.sh` |
| A4 | claude-glm 심볼릭 링크 등록 | `~/.local/bin/claude-glm` |
| A5 | 각 CLI 동작 검증 (claude, codex, gemini, wrapper x2) | 테스트 결과 기록 |
| A6 | .env.example 최종 정리 | `.env.example` |

검증:
- 각 CLI에 간단한 프롬프트를 보내 응답 확인
- fallback 동작 확인 (서버 미접근 시 Claude 처리)

### Phase B — 오케스트레이션 통합 (1주)

목표: claude-imple-skills의 orchestrate + hooks + multi-ai-review 활성화

| # | 작업 | 산출물 |
|---|------|--------|
| B1 | orchestrate-standalone 설치 | 스킬 심볼릭 링크 |
| B2 | project-team 설치 (standard 모드: 7 agents + 4 hooks) | agents/ + hooks/ |
| B3 | multi-ai-review council.config.yaml 커스텀 | council 설정 |
| B4 | verify/quality gate 순서 확정 | quality-auditor 연동 |
| B5 | Spacebot 개념 매핑 문서 작성 (Branch↔wave, Worker↔CLI 위임 등) | 설계 문서 |
| B6 | handoff 문서 포맷 정의 (ECC 차용) | 템플릿 |

검증:
- `/orchestrate --multi-ai` 로 실제 태스크 실행
- `/multi-ai-review`로 코드 리뷰 실행
- quality-auditor로 품질 게이트 통과 확인

### Phase C — 운영 안정화 (2-4주)

목표: 관측성, 보안, 운영 자동화

| # | 작업 | 산출물 |
|---|------|--------|
| C1 | run log 및 artifact 디렉터리 구조화 | `artifacts/runs/` |
| C2 | hook profile 확장 (standard → full) | hooks 설정 |
| C3 | AgentShield 연동 (security scan) | CI 연동 |
| C4 | nexus/cognit 모니터링 (health check 스크립트) | `scripts/health-check.sh` |
| C5 | 운영 가이드 작성 | `docs/운영가이드.md` |
| C6 | Spacebot Compactor 개념 도입 (context 압력 감지 → compact 제안) | compact 정책 |

## 8. 리스크 및 대응

### 8.1 기술 리스크

| 리스크 | 대응 |
|--------|------|
| nexus/cognit VPN 접근 불가 | claude-imple-skills fallback → Claude 직접 처리 |
| Qwen3-Coder VRAM 부족 (GPU당 11.4/12GB) | context 16K 제한 유지, 동시 요청 1개 제한 |
| Codex/Gemini CLI 인증 만료 | 사전 `command -v` + auth 체크 |
| wrapper 스크립트 타임아웃 | defaults.timeout: 120초 + retry_count: 2 |

### 8.2 운영 리스크

| 리스크 | 대응 |
|--------|------|
| OMC 에이전트와 claude-imple-skills 에이전트 혼동 | 문서에 "별개 시스템" 명시, 각 역할 명확화 |
| routing.config.yaml 변경 시 기존 스킬 영향 | 프로젝트 로컬 설정 우선 (.claude/routing.config.yaml) |
| nexus llama-server 재시작 시 모델 로딩 시간 | wrapper에 health check + 대기 로직 |

### 8.3 보안 리스크

| 리스크 | 대응 |
|--------|------|
| wrapper 스크립트에 API 키 노출 | .env 참조만 사용, .gitignore에 .env 포함 |
| multi-ai-review에 민감 코드 전달 | council 대상 작업 범위 제한 |
| 외부 CLI(codex/gemini)에 소스코드 전송 | sandbox 모드 활용, 민감 파일 제외 |

## 9. 산출물 체크리스트

- [ ] routing.config.yaml 커스텀 (6개 모델)
- [ ] scripts/qwen35-cli.sh (nexus wrapper)
- [ ] scripts/qwen-coder-cli.sh (cognit wrapper)
- [ ] claude-glm 심볼릭 링크
- [ ] orchestrate-standalone 설치
- [ ] project-team 설치 (standard)
- [ ] council.config.yaml 커스텀
- [ ] verify/quality gate 순서 문서
- [ ] Spacebot 개념 매핑 문서
- [ ] 운영 가이드
- [ ] health check 스크립트

## 10. 참고 자료

- Spacebot: [spacebot README](https://github.com/spacedriveapp/spacebot?tab=readme-ov-file)
- Agent Council: [agent-council repository](https://github.com/team-attention/agent-council/tree/main)
- Everything Claude Code: [everything-claude-code repository](https://github.com/affaan-m/everything-claude-code)
- claude-imple-skills: [claude-imple-skills repository](https://github.com/insightflo/claude-imple-skills)
