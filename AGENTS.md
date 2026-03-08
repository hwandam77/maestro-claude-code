# AGENTS.md

This file provides guidance to AI assistants when working with code in this repository.

## 언어 원칙

- 사용자와의 대화 및 설명은 **한글**로 진행한다.
- 코드, 변수명, 함수명은 영어를 사용한다.

## 프로젝트 개요

**Maestro Claude Code**는 6개의 AI 모델을 역할별로 라우팅하는 멀티 LLM 오케스트레이션 시스템이다.
Claude Code 구독을 중심으로, claude-imple-skills의 multi-ai-run이 태스크 단위로 최적 CLI에 위임한다.

### 6-Model Orchestra

| # | 모델 | 제공 | CLI/접근 | 용도 | Context |
|---|------|------|----------|------|---------|
| 1 | Claude (구독) | Anthropic | `claude` | 오케스트레이션, 아키텍처, 기획 | 200K |
| 2 | GLM-5 | ZAI Coding Plan ($3/월) | `claude-glm` | 저비용 Claude 대체 | - |
| 3 | gpt-5.3-codex | OpenAI | `codex exec` | 코드 생성, 리뷰, 테스트 | - |
| 4 | gemini-3.1-pro-preview | Google | `gemini` | 디자인, UI, 멀티모달 | - |
| 5 | Qwen3.5-122B (Q3_K_XL) | nexus (자체) | `./scripts/qwen35-cli.sh` | 고급 추론, 장문 컨텍스트 | 400K |
| 6 | Qwen3-Coder-30B-A3B (AWQ-4bit) | cognit (자체) | `./scripts/qwen-coder-cli.sh` | 코드 생성, 리팩토링 | 20K |

## 명령어

### 환경 설정
```bash
cp .env.example .env
# .env 파일에 ZAI_API_KEY, 서버 호스트/포트 입력
```

### 실행
```bash
# 기본 모드 (Anthropic 구독)
claude

# GLM-5 저비용 모드
claude-glm
# 또는
./scripts/maestro.sh

# 상태 확인
./scripts/maestro.sh status
```

### 멀티 AI 명령
```bash
# 역할별 최적 CLI에 태스크 위임
/multi-ai-run

# 멀티 AI 코드 리뷰 (council)
/multi-ai-review

# 대규모 태스크 오케스트레이션
/orchestrate-standalone --mode=standard
```

### 유지보수
```bash
# 서버 상태 점검
./scripts/health-check.sh

# 보안 스캔
./scripts/security-scan.sh

# 빠른 시크릿 검사
./scripts/security-scan.sh --quick
```

## 아키텍처

### 라우팅 흐름

```
사용자 요청
  -> Claude Code (구독, 오케스트레이터)
    -> OMC 에이전트 (Claude Code 내부 subagent, 같은 API)
    -> claude-imple-skills multi-ai-run (태스크 위임)
      -> codex exec (gpt-5.3-codex)     : 코드 생성/리뷰
      -> gemini (gemini-3.1-pro)         : 디자인/UI
      -> wrapper -> nexus:8080 (Qwen3.5) : 고급 추론
      -> wrapper -> cognit:8000 (Qwen3-Coder) : 코드 생성
    -> hooks (품질 게이트)
    -> orchestrate (wave/sprint 태스크 관리)
```

### 2계층 라우팅

| 계층 | 시스템 | 라우팅 대상 | 설정 |
|------|--------|------------|------|
| 에이전트 내부 | OMC | Claude Code subagent | Claude 구독 API |
| 태스크 위임 | claude-imple-skills | 역할별 CLI | `.claude/routing.config.yaml` |

OMC 에이전트와 claude-imple-skills의 project-team은 **별개 시스템**이며 서로 간섭하지 않는다.

### 역할별 라우팅 (routing.config.yaml)

| 역할 | CLI | 모델 |
|------|-----|------|
| orchestrator, project-manager, chief-architect | claude | Claude (구독) |
| backend-specialist, test-specialist, api-designer, security-specialist | codex | gpt-5.3-codex |
| frontend-specialist, chief-designer | gemini | gemini-3.1-pro |

### Project-Team 에이전트 (7개, standard 모드)

| 에이전트 | 역할 |
|----------|------|
| ChiefArchitect | 아키텍처 설계, 기술 결정 |
| ProjectManager | 프로젝트 관리, 일정 조율 |
| BackendSpecialist | 백엔드 구현 |
| FrontendSpecialist | 프론트엔드 구현 |
| ChiefDesigner | UI/UX 디자인 |
| SecuritySpecialist | 보안 검사, 취약점 분석 |
| QAManager | 품질 관리, 테스트 전략 |

## Hook 시스템

### 활성 Hooks (settings.json)

| 이벤트 | Hook | 동작 |
|--------|------|------|
| PreToolUse (Write/Edit) | contract-gate.js | API 계약 준수 검증 |
| PostToolUse (Write/Edit) | security-scan.js | 보안 취약점 스캔 |
| Stop | task-sync.js | TASKS.md 상태 업데이트 |

### Hook 프로파일

| 프로파일 | Hooks | 용도 |
|----------|-------|------|
| lite | 2개 | 핫픽스, 단순 변경 |
| standard | 6개 | 일반 개발 (기본값) |
| full | 16개 | 대규모 기능, 배포 전 |

설정: `.claude/hooks/hook-profiles.yaml`

## 핵심 파일

| 파일 | 설명 |
|------|------|
| `.claude/routing.config.yaml` | 6개 모델 라우팅 설정 |
| `.claude/council.config.yaml` | 멀티 AI 리뷰 council 설정 |
| `.claude/settings.json` | Claude Code hooks 등록 |
| `.claude/hooks/` | 품질 게이트 hooks (16개) |
| `.claude/agents/` | project-team 에이전트 (7개) |
| `scripts/maestro.sh` | GLM-5 (ZAI) 모드 런처 |
| `scripts/qwen35-cli.sh` | nexus wrapper (Qwen3.5-122B) |
| `scripts/qwen-coder-cli.sh` | cognit wrapper (Qwen3-Coder-30B) |
| `scripts/health-check.sh` | 서버 상태 점검 |
| `scripts/security-scan.sh` | 보안 스캔 |
| `.env` | API 키 및 서버 설정 (Git 추적 안함) |

## 제약 사항

### Qwen3-Coder 20K 토큰 제한
- 동시 요청 1개 권장 (GPU당 11.4GB/12GB)
- 긴 파일 처리 불가 -> Claude 또는 Codex로 에스컬레이션

### 서버 접근 (VPN 필수)
- nexus/cognit 접근에 Tailscale VPN 필요
- VPN 미연결 시 fallback -> Claude가 직접 처리

### GLM-5 (ZAI) 제한
- ZAI Coding Plan 구독 필요 ($3/월)
- ANTHROPIC_BASE_URL, ANTHROPIC_AUTH_TOKEN으로 인증

## 참고 문서

| 문서 | 위치 |
|------|------|
| 운영 가이드 | `docs/운영가이드.md` |
| 상세 매뉴얼 | `docs/MANUAL.md` |
| 고도화 계획서 | `docs/계획서/MAESTRO_UPGRADE_PLAN.md` |
| Quality Gate 순서 | `docs/work-log/verify-quality-gate-order.md` |
| Spacebot 개념 매핑 | `docs/work-log/spacebot-concept-mapping.md` |
| Handoff 템플릿 | `docs/work-log/handoff-template.md` |
| Compact 정책 | `docs/work-log/compact-policy.md` |
