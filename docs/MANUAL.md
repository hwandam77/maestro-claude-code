# Maestro Claude Code 운영 매뉴얼

> 최종 업데이트: 2026-03-08
> 대상 독자: Maestro Claude Code 운영자

---

## 목차

1. [설치 및 초기 설정](#1-설치-및-초기-설정)
2. [기본 사용법](#2-기본-사용법)
3. [멀티 AI 오케스트레이션](#3-멀티-ai-오케스트레이션)
4. [Project-Team 에이전트](#4-project-team-에이전트)
5. [Hook 시스템](#5-hook-시스템)
6. [서버 관리](#6-서버-관리)
7. [보안](#7-보안)
8. [Context 관리](#8-context-관리-compact-정책)
9. [트러블슈팅](#9-트러블슈팅)
10. [참고 문서](#10-참고-문서)

---

## 1. 설치 및 초기 설정

### 1.1 사전 요구사항

Maestro Claude Code를 운영하려면 아래 도구가 필요합니다.

**필수 도구**

| 도구 | 설치 확인 | 역할 |
|------|-----------|------|
| Claude Code (Anthropic 구독) | `claude --version` | 기본 오케스트레이터 |
| Node.js | `node --version` | 스크립트 실행 환경 |
| jq | `jq --version` | JSON 파싱 (wrapper 스크립트) |
| curl | `curl --version` | API 호출 |

**선택 도구**

| 도구 | 설치 명령 | 역할 |
|------|-----------|------|
| Codex CLI | `npm install -g @openai/codex` | 코드 생성/리뷰/테스트 |
| Gemini CLI | `brew install gemini` 또는 `npm install -g @google/gemini-cli` | 디자인/UI/멀티모달 |
| Tailscale | [tailscale.com](https://tailscale.com) | nexus/cognit 서버 접근용 VPN |

**VPN 연결 확인 (자체 서버 사용 시)**

```bash
tailscale status
ping 100.64.189.120  # nexus
ping 100.89.224.48   # cognit
```

### 1.2 환경 변수 설정

프로젝트 루트에서 `.env` 파일을 생성합니다.

```bash
cp .env.example .env
```

`.env` 파일을 열어 실제 값을 입력합니다.

```bash
# .env 편집
nano .env  # 또는 선호하는 편집기 사용
```

**각 환경 변수 설명**

| 변수명 | 설명 | 획득 방법 |
|--------|------|-----------|
| `ZAI_API_KEY` | ZAI Coding Plan API 키 (GLM-5 저비용 모드용) | [open.z.ai](https://open.z.ai) 가입 후 발급 |
| `NEXUS_HOST` | Qwen3.5-122B 서버 IP (Tailscale) | 기본값: `100.64.189.120` |
| `NEXUS_PORT` | nexus llama-server 포트 | 기본값: `8080` |
| `QWEN35_TIMEOUT` | nexus API 타임아웃 (초) | 기본값: `120` |
| `COGNIT_HOST` | Qwen3-Coder-30B 서버 IP (Tailscale) | 기본값: `100.89.224.48` |
| `COGNIT_PORT` | cognit vLLM 포트 | 기본값: `8000` |
| `QWEN_CODER_TIMEOUT` | cognit API 타임아웃 (초) | 기본값: `120` |
| `TAVILY_API_KEY` | Tavily 웹 검색 API 키 | [tavily.com](https://tavily.com) |

**ZAI API 주의사항**

ZAI API는 일반 Anthropic 환경 변수와 다릅니다.

```bash
# 올바른 설정 (maestro.sh가 자동 처리)
ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic
ANTHROPIC_AUTH_TOKEN=${ZAI_API_KEY}  # ANTHROPIC_API_KEY가 아님!
```

### 1.3 claude-glm 심볼릭 링크 생성

`claude-glm` 명령어를 어디서나 사용하려면 심볼릭 링크를 등록합니다.

```bash
# ~/.local/bin 디렉터리 생성 (없는 경우)
mkdir -p ~/.local/bin

# 심볼릭 링크 생성
ln -sf "$(pwd)/scripts/maestro.sh" ~/.local/bin/claude-glm

# PATH에 ~/.local/bin 추가 (쉘 설정 파일에 추가)
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# 확인
which claude-glm
claude-glm status
```

### 1.4 claude-imple-skills 연동 확인

Maestro는 `claude-imple-skills`의 스킬을 활용합니다.

```bash
# 설치 확인
ls ~/.claude/skills/ | grep -E "multi-ai|orchestrate"

# 글로벌 심볼릭 링크 확인
ls -la ~/.claude/skills/orchestrate-standalone
ls -la ~/.claude/skills/multi-ai-run
ls -la ~/.claude/skills/multi-ai-review
```

설치되지 않은 경우, claude-imple-skills 저장소에서 설치합니다.

```bash
# claude-imple-skills 저장소 클론 (별도 위치)
git clone https://github.com/insightflo/claude-imple-skills ~/workspace/claude-imple-skills

# 스킬 심볼릭 링크 등록 (orchestrate-standalone)
ln -sf ~/workspace/claude-imple-skills/orchestrate-standalone \
    ~/.claude/skills/orchestrate-standalone
```

### 1.5 스크립트 실행 권한 확인

```bash
chmod +x scripts/*.sh

# 권한 확인
ls -la scripts/
# -rwxr-xr-x  maestro.sh
# -rwxr-xr-x  qwen35-cli.sh
# -rwxr-xr-x  qwen-coder-cli.sh
# -rwxr-xr-x  health-check.sh
# -rwxr-xr-x  security-scan.sh
```

---

## 2. 기본 사용법

### 2.1 Claude Code 실행 모드

Maestro는 두 가지 Claude 실행 모드를 제공합니다.

```bash
# 기본 모드: Anthropic 구독 (Claude opus/sonnet/haiku)
claude

# 저비용 모드: ZAI API 경유 GLM-5
claude-glm

# 스크립트 직접 실행
./scripts/maestro.sh          # ZAI GLM-5 모드
./scripts/maestro.sh status   # 현재 설정 확인
```

**언제 어떤 모드를 쓸까?**

| 상황 | 권장 모드 | 이유 |
|------|-----------|------|
| 아키텍처 설계, 복잡한 분석 | `claude` | Claude 구독의 최고 품질 |
| 일상적인 코드 수정, 문서 작성 | `claude-glm` | 월 $3 고정비용으로 비용 절약 |
| 코드 생성, 리뷰 | `codex` CLI 또는 `claude` | Codex는 코드 특화 |
| 디자인, UI 작업 | `gemini` CLI | 멀티모달 강점 |

### 2.2 현재 설정 확인

```bash
./scripts/maestro.sh status
```

출력 예시:
```
Maestro Claude Code
===================
  GLM-5 모드:  ZAI Coding Plan
  Endpoint:    https://api.z.ai/api/anthropic
  비용:        ~$3/월 (구독제)

  실행: ./scripts/maestro.sh
  구독: claude (환경변수 없이)
```

### 2.3 Wrapper 스크립트 사용법

자체 서버(nexus/cognit)를 CLI처럼 호출하는 래퍼 스크립트입니다.

**Qwen3.5-122B (nexus) — 고급 추론, 400K context**

```bash
# 방법 1: 인자로 직접 전달
./scripts/qwen35-cli.sh "복잡한 아키텍처 분석 요청"

# 방법 2: stdin으로 파이프
echo "이 코드의 성능 병목을 분석해줘" | ./scripts/qwen35-cli.sh

# 방법 3: 시스템 프롬프트 지정
./scripts/qwen35-cli.sh -s "당신은 시니어 백엔드 엔지니어입니다." \
    "이 API 설계의 문제점을 찾아줘"

# 대용량 파일 분석
cat src/complex-module.ts | ./scripts/qwen35-cli.sh -s \
    "코드 리뷰어로서 이슈를 찾아줘" \
    "위 TypeScript 코드의 버그와 개선점을 알려줘"
```

**Qwen3-Coder-30B (cognit) — 코드 생성, 20K context**

```bash
# 코드 생성 요청
./scripts/qwen-coder-cli.sh "Python FastAPI로 사용자 CRUD API 작성해줘"

# stdin 파이프
echo "이 함수를 리팩토링해줘" | ./scripts/qwen-coder-cli.sh

# 시스템 프롬프트 지정
./scripts/qwen-coder-cli.sh -s "TypeScript 전문가로서" \
    "다음 JavaScript 코드를 TypeScript로 변환해줘"
```

**주의사항**

- 두 스크립트 모두 서버 접근 불가 시 에러 메시지와 함께 `exit 1`로 종료합니다.
- `.env` 파일에서 설정을 자동 로드합니다.
- cognit (Qwen-Coder)는 **context 20K tokens 제한**이 있습니다. 대용량 파일은 nexus를 사용하세요.

---

## 3. 멀티 AI 오케스트레이션

### 3.1 아키텍처 개요

Maestro는 두 계층의 라우팅이 독립적으로 동작합니다.

```
사용자 요청
  → Claude Code (구독, 오케스트레이터)
    → OMC 에이전트 (Claude Code 내부 subagent)
      [architect, executor, designer 등 — 전부 Anthropic API 사용]
    → claude-imple-skills multi-ai-run (태스크 위임)
      → codex exec  (gpt-5.3-codex)    : 코드 생성/리뷰/테스트
      → gemini      (gemini-3.1-pro)   : 디자인/UI/멀티모달
      → qwen35-cli  (nexus:8080)       : 고급 추론, 장문 컨텍스트
      → qwen-coder  (cognit:8000)      : 빠른 코드 생성
      → claude-glm  (ZAI GLM-5)        : 저비용 Claude 대체
    → claude-imple-skills hooks (품질 게이트)
    → claude-imple-skills orchestrate (wave/sprint 태스크 관리)
```

**핵심 원칙**: OMC 에이전트(architect, executor 등)와 claude-imple-skills의 project-team 에이전트는 **별개 시스템**입니다. 서로 간섭하지 않습니다.

### 3.2 routing.config.yaml 이해

라우팅 규칙은 `routing.config.yaml` 파일로 관리됩니다.

```yaml
version: 1.0

cli_models:
  claude:
    command: "claude"
    model: "sonnet"

  codex:
    command: "codex exec"
    model: "gpt-5.3-codex"
    args: "--sandbox workspace-write"

  gemini:
    command: "gemini"
    model: "gemini-3.1-pro-preview"
    args: "--output-format text"

  qwen35:
    command: "./scripts/qwen35-cli.sh"
    model: "Qwen3.5-122B"

  qwen-coder:
    command: "./scripts/qwen-coder-cli.sh"
    model: "Qwen3-Coder-30B"

  claude-glm:
    command: "./scripts/maestro.sh"
    model: "GLM-5"

role_routing:
  orchestrator:       claude
  chief-architect:    claude
  project-manager:    claude
  backend-specialist: codex
  test-specialist:    codex
  api-designer:       codex
  security-specialist: codex
  frontend-specialist: gemini
  chief-designer:     gemini

task_type_routing:
  code_generation:  codex
  code_review:      codex
  refactoring:      codex
  testing:          codex
  ui_implementation: gemini
  design_review:    gemini
  styling:          gemini
  architecture:     claude
  planning:         claude
  coordination:     claude

defaults:
  model: claude
  fallback_enabled: true
  timeout: 120
  retry_count: 2
```

**설정 우선순위**

1. 프로젝트 로컬: `.claude/routing.config.yaml` (우선 적용)
2. 글로벌: `~/.claude/routing.config.yaml`

프로젝트별로 다른 라우팅이 필요하면 프로젝트 로컬 파일을 생성하세요.

```bash
# 프로젝트 로컬 routing 설정 생성
mkdir -p .claude
cp ~/.claude/routing.config.yaml .claude/routing.config.yaml
# 이후 .claude/routing.config.yaml 편집
```

### 3.3 /multi-ai-run 사용

태스크를 역할별 최적 CLI에 위임합니다.

```bash
# Claude Code 세션 내에서 실행
/multi-ai-run "코드 리뷰해줘"
# → routing.config.yaml의 task_type_routing에 따라 codex로 라우팅

/multi-ai-run "사용자 로그인 UI 컴포넌트 작성"
# → ui_implementation → gemini로 라우팅

/multi-ai-run "마이크로서비스 아키텍처 설계"
# → architecture → claude로 라우팅
```

**라우팅 결정 순서**

1. `role_routing`에 에이전트 역할이 명시된 경우 → 해당 CLI 사용
2. `task_type_routing`에 태스크 유형이 매핑된 경우 → 해당 CLI 사용
3. 없으면 `defaults.model` (claude) 사용

**fallback 동작**

```
codex 실행 실패 → claude로 자동 전환
gemini 실행 실패 → claude로 자동 전환
qwen35-cli 실패 (서버 다운) → claude로 자동 전환
qwen-coder-cli 실패 → claude로 자동 전환
```

### 3.4 /multi-ai-review 사용

여러 AI가 병렬로 코드를 리뷰하고 Claude(chairman)가 종합 의견을 제시합니다.

```bash
# Claude Code 세션 내에서 실행
/multi-ai-review
```

**council 방식 동작**

1. `council.config.yaml`에 정의된 3개 AI에 리뷰 요청을 병렬로 전송
2. 각 AI의 리뷰 결과 수집
3. Claude (chairman)가 의견들을 종합하여 최종 리뷰 제시

**council.config.yaml 커스텀**

```yaml
# .claude/council.config.yaml (예시)
panel:
  - model: codex
    role: code-quality-reviewer
    focus: "버그, 성능, 코드 품질"

  - model: gemini
    role: design-reviewer
    focus: "아키텍처, 패턴 적용"

  - model: qwen35
    role: security-reviewer
    focus: "보안 취약점, 엣지 케이스"

chairman: claude
```

**보안 주의사항**: council 리뷰에 민감한 비즈니스 로직, API 키, 개인정보가 포함된 코드를 전달하지 마세요.

### 3.5 /orchestrate-standalone 사용

대규모 태스크를 구조화하여 관리합니다.

```bash
# Claude Code 세션 내에서 실행

# lite 모드: 경량 (30-50 tasks), 핫픽스용
/orchestrate-standalone --mode=lite

# standard 모드: 일반 개발 (50-80 tasks), 기본값
/orchestrate-standalone --mode=standard

# wave 모드: 대규모 (80-200 tasks), Hybrid Wave 방식
/orchestrate-standalone --mode=wave
```

**Wave 모드 상세 (대규모 작업)**

Wave 모드는 대규모 태스크를 4단계 Phase로 관리합니다.

```
Phase 0: Shared Foundation (계약 확정)
  - API 계약, 데이터 모델, 코딩 표준 확정
  - contracts/ 디렉터리에 문서화
  - 모든 에이전트가 공유하는 기반 마련

Phase 1: Domain Parallelism (병렬 실행)
  - 도메인별 에이전트가 병렬로 태스크 실행
  - backend-specialist, frontend-specialist 등이 동시에 진행
  - wave 단위(20-40 tasks)로 분할 처리

Phase 2: Cross-Review Gate (교차 검증)
  - 도메인 간 인터페이스 검증
  - /multi-ai-review로 코드 리뷰
  - handoff 문서 작성 (다음 wave 인수인계)
  - context 정리 (이전 wave 상세 context 폐기)

Phase 3: Integration & Polish (통합)
  - 전체 빌드 및 테스트
  - quality-auditor로 품질 게이트 통과
  - 최종 architect 검증
```

**모드별 비교**

| 항목 | lite | standard | wave |
|------|------|----------|------|
| 태스크 수 | 30-50 | 50-80 | 80-200 |
| Hook 프로파일 | lite (2개) | standard (6개) | full (16개) |
| 적합한 상황 | 핫픽스, 긴급 수정 | 일반 기능 개발 | 대규모 리팩토링, 신규 시스템 |
| 멀티 AI 리뷰 | 선택 | 선택 | 포함 |

---

## 4. Project-Team 에이전트

Claude Code 세션 내에서 전문 에이전트로 태스크를 위임할 수 있습니다.

### 4.1 에이전트 목록

| 에이전트 | 역할 | CLI 매핑 | 모델 |
|----------|------|----------|------|
| **ChiefArchitect** | 아키텍처 설계, 기술 표준 정의, VETO 권한 | claude | opus |
| **ProjectManager** | 프로젝트 관리, 일정, 우선순위 | claude | sonnet |
| **BackendSpecialist** | API 설계/구현, DB, 성능 최적화 | codex | sonnet |
| **FrontendSpecialist** | 프론트엔드 구현, 컴포넌트 | gemini | sonnet |
| **ChiefDesigner** | UI/UX 디자인, 디자인 시스템 | gemini | sonnet |
| **SecuritySpecialist** | 보안 검사, 취약점 분석 | codex | sonnet |
| **QAManager** | 품질 관리, 테스트 전략, 커버리지 | codex | sonnet |

### 4.2 에이전트 호출

```bash
# Claude Code 세션에서 직접 에이전트로 위임
# (OMC의 Task 도구 사용 방식)

# 아키텍처 검토 요청
"이 마이크로서비스 설계를 검토해줘. ChiefArchitect로 처리해줘"

# 보안 검사 요청
"이 인증 코드의 보안 취약점을 찾아줘. SecuritySpecialist 역할로"

# 테스트 전략 요청
"이 모듈의 테스트 전략과 커버리지 계획을 세워줘. QAManager로"
```

### 4.3 ChiefArchitect VETO 권한

ChiefArchitect는 아키텍처 위반 시 병합을 차단하는 VETO 권한을 가집니다.

**VETO 발동 조건**

| 사유 | 설명 | 해제 조건 |
|------|------|-----------|
| 아키텍처 위반 | 정의된 레이어/모듈 구조 위반 | 구조 수정 후 재검토 |
| 기술 표준 위반 | 코딩 컨벤션, API 표준 미준수 | 표준 준수 후 재검토 |
| 보안 취약점 | SQL Injection, XSS 등 | 취약점 해결 후 재검토 |

VETO 발동 시 다음 형식으로 알림이 옵니다.

```markdown
## VETO: [위반 유형]
- **File**: [파일 경로]
- **Line**: [라인 번호]
- **Violation**: [위반 내용]
- **Standard**: [관련 표준 문서]
- **Fix**: [수정 방법]
```

### 4.4 BackendSpecialist 코드 패턴

BackendSpecialist가 사용하는 표준 패턴입니다.

**RESTful API 표준**

```
리소스 경로: 복수형 명사 (/users, /orders)
계층 구조: 중첩 경로 (/users/{id}/orders)
버전 관리: URL Path (/api/v1/, /api/v2/)
```

**응답 형식**

```json
// 성공
{ "data": {...}, "meta": {...} }

// 에러
{ "error": { "code": "ERROR_CODE", "message": "설명", "details": {...} } }

// 페이지네이션
{ "data": [...], "meta": { "total": 100, "page": 1, "limit": 20, "hasMore": true } }
```

---

## 5. Hook 시스템

### 5.1 Hook 프로파일 선택

Hook 프로파일은 품질 게이트의 강도를 결정합니다.

설정 파일: `.claude/hooks/hook-profiles.yaml`

| 프로파일 | Hook 수 | 용도 | 적합한 상황 |
|----------|---------|------|------------|
| **lite** | 2개 | 최소 검증 | 긴급 핫픽스, 문서 수정 |
| **standard** | 6개 | 일반 개발 게이트 | 일반 기능 개발 (기본값) |
| **full** | 16개 | 전체 품질 게이트 | 프로덕션 배포 전, 대규모 기능 |

```bash
# 오케스트레이션 모드로 프로파일 선택
/orchestrate-standalone --mode=lite      # lite 훅 프로파일
/orchestrate-standalone --mode=standard  # standard 훅 프로파일 (기본)
/orchestrate-standalone --mode=full      # full 훅 프로파일
```

### 5.2 개별 Hook 설명

**lite 프로파일 (2개)**

| Hook | 실행 시점 | 기능 |
|------|-----------|------|
| `policy-gate` | 태스크 실행 전 | 권한 + 코딩 표준 확인 |
| `quality-gate` | 태스크 완료 후 | 빌드/타입/린트/테스트 통과 확인 |

**standard 프로파일 (6개)**

| Hook | 실행 시점 | 기능 |
|------|-----------|------|
| `policy-gate` | Pre-Dispatch | 권한 + 코딩 표준 확인 |
| `risk-gate` | Pre-Dispatch | 영향도 + 위험도 평가 |
| `contract-gate` | Post-Task | API 계약 준수 검증 |
| `quality-gate` | Post-Task | 빌드/타입/린트/테스트 |
| `security-scan` | Post-Task | 보안 취약점 스캔 |
| `task-sync` | Post-Task | TASKS.md 상태 업데이트 |

**full 프로파일 (16개 — standard에 추가)**

| Hook | 실행 시점 | 기능 |
|------|-----------|------|
| `coverage-gate` | Post-Task | 테스트 커버리지 >= 80% 강제 |
| `dependency-check` | Pre-Dispatch | 의존성 취약점 스캔 |
| `performance-gate` | Post-Task | 성능 회귀 감지 |
| `docs-sync` | Post-Task | 문서와 코드 동기화 |
| `changelog-gate` | Phase Barrier | CHANGELOG.md 업데이트 확인 |
| `migration-gate` | Phase Barrier | DB 마이그레이션 정합성 |
| `bundle-size-gate` | Phase Barrier | 번들 크기 회귀 감지 |
| `type-coverage-gate` | Phase Barrier | 타입 커버리지 기준 |
| `accessibility-gate` | Phase Barrier | 접근성 기준 통과 |
| `final-quality-auditor` | Final Gate | 종합 품질 감사 |

### 5.3 게이트 실행 순서

전체 게이트는 4단계로 순서가 정해져 있습니다.

```
1. Pre-Dispatch Gate (태스크 실행 전)
   policy-gate → risk-gate

2. Post-Task Gate (태스크 완료 후)
   contract-gate → quality-gate → security-scan → task-sync

3. Phase/Layer Barrier Gate (Phase 전환 시)
   build → types → lint → test → security → console-cleanup

4. Final Gate (PR/완료 선언 전)
   /quality-auditor → /multi-ai-review → architect 검증
```

**현재 기본 설정: standard** (7 agents + 4 hooks)

```
적용 hooks: contract-gate, quality-gate, security-scan, task-sync
```

---

## 6. 서버 관리

### 6.1 전체 Health Check

```bash
# 전체 서버 + CLI 도구 상태 확인
./scripts/health-check.sh

# 개별 확인
./scripts/health-check.sh nexus    # nexus 서버만
./scripts/health-check.sh cognit   # cognit 서버만
./scripts/health-check.sh cli      # CLI 도구만 (claude, codex, gemini, claude-glm)
```

출력 예시:
```
================================
  Maestro Health Check
================================

[CLI Tools]
claude:      OK (/usr/local/bin/claude)
codex:       OK (/usr/local/bin/codex)
gemini:      OK (/usr/local/bin/gemini)
claude-glm:  OK (/Users/hwandam/.local/bin/claude-glm)

[Self-hosted Servers]
nexus:       HEALTHY (model: Qwen3.5-122B)
cognit:      HEALTHY (model: Qwen3-Coder-30B-A3B-Instruct)

================================
```

**상태 코드 의미**

| 상태 | 의미 | 조치 |
|------|------|------|
| `HEALTHY` | 정상 작동 | 없음 |
| `DEGRADED` | Ping OK, API 응답 없음 | 서비스 재시작 필요 |
| `UNREACHABLE` | Ping 실패 | VPN 연결 확인 |
| `NOT FOUND` | CLI 미설치 | 해당 CLI 설치 |

### 6.2 nexus 서버 관리

| 항목 | 값 |
|------|----|
| 호스트 | `100.64.189.120` (Tailscale) |
| 포트 | `8080` |
| 모델 | Qwen3.5-122B (Q3_K_XL) |
| 서비스 | llama-server (상시 구동) |
| GPU | RTX 3090 x3 (VRAM 72GB) |
| Context | 400K tokens |

```bash
# SSH 접속 (VPN 필요)
ssh nexus  # ~/.ssh/config에 Host nexus 설정 필요

# 또는 IP 직접 접속
ssh user@100.64.189.120

# llama-server 상태 확인
ssh nexus "ps aux | grep llama-server"

# API 연결 테스트
curl -s http://100.64.189.120:8080/v1/models | jq '.data[0].id'

# 간단한 추론 테스트
./scripts/qwen35-cli.sh "안녕하세요, 테스트입니다."
```

**nexus 서버 재시작**

```bash
ssh nexus

# llama-server 프로세스 확인
ps aux | grep llama-server

# 재시작 (서버에서 실행하는 명령 — 실제 명령은 운영자 확인 필요)
# llama-server 재시작 후 모델 로딩에 수 분 소요됨
```

### 6.3 cognit 서버 관리

| 항목 | 값 |
|------|----|
| 호스트 | `100.89.224.48` (Tailscale) |
| 포트 | `8000` |
| 모델 | Qwen3-Coder-30B-A3B-Instruct AWQ-4bit |
| 서비스 | vLLM (systemd) |
| GPU | RTX 3080 Ti x2 (GPU당 11.4GB/12GB 사용) |
| Context | **20K tokens** (AWQ-4bit 확인 완료) |
| Ollama | 포트 11434 (공존, qwen3.5:27b 등) |

```bash
# vLLM 서비스 상태 확인
ssh cognit "systemctl status vllm-qwen3-coder.service"

# 서비스 재시작 (sudo 필요)
ssh cognit "sudo systemctl restart vllm-qwen3-coder.service"

# 서비스 중지/시작
ssh cognit "sudo systemctl stop vllm-qwen3-coder.service"
ssh cognit "sudo systemctl start vllm-qwen3-coder.service"

# 로그 확인
ssh cognit "journalctl -u vllm-qwen3-coder.service -n 50"
ssh cognit "journalctl -u vllm-qwen3-coder.service -f"  # 실시간 로그

# API 연결 테스트
curl -s http://100.89.224.48:8000/v1/models | jq '.data[0].id'

# 간단한 코드 생성 테스트
./scripts/qwen-coder-cli.sh "Python으로 Hello World를 출력하는 함수를 작성해줘"
```

**cognit GPU 사용량 모니터링**

```bash
ssh cognit "nvidia-smi"
# 기대 출력: GPU 0 ~11.4GB, GPU 1 ~11.4GB
```

**중요 제약사항**

- `Qwen3-Coder-Next-AWQ-8bit` (24B 모델)은 VRAM 부족으로 사용 불가 (확인됨)
- 동시 요청은 **1개를 권장**합니다. 병렬 요청 시 OOM 위험

### 6.4 SSH config 설정

`~/.ssh/config`에 아래를 추가하면 `ssh nexus`, `ssh cognit`으로 간편하게 접속합니다.

```
Host nexus
    HostName 100.64.189.120
    User your-username
    IdentityFile ~/.ssh/your-key

Host cognit
    HostName 100.89.224.48
    User your-username
    IdentityFile ~/.ssh/your-key
```

---

## 7. 보안

### 7.1 Security Scan 실행

```bash
# 전체 보안 스캔 (4단계)
./scripts/security-scan.sh

# 빠른 스캔 (시크릿 하드코딩만)
./scripts/security-scan.sh --quick
```

**4단계 보안 검사 내용**

| 단계 | 검사 항목 | 실패 조건 |
|------|-----------|-----------|
| 1/4 | 시크릿 하드코딩 | API 키, 비밀번호, 토큰, 개인키 패턴 발견 시 |
| 2/4 | .env git 추적 | .env 파일이 git에 추적되는 경우 |
| 3/4 | 스크립트 권한 | 과도한 파일 권한 (755/775 초과) |
| 4/4 | 민감 파일 존재 | credentials.json, *.pem, *.key, id_rsa |

**종료 코드**

- `exit 0`: 보안 검사 통과
- `exit 2`: 보안 이슈 발견 (CI/CD에서 배포 차단)

**CI/CD 통합**

```yaml
# GitHub Actions 예시
- name: 보안 스캔
  run: ./scripts/security-scan.sh
  # exit 2 시 파이프라인 중단
```

### 7.2 보안 운영 규칙

**API 키 관리**

```bash
# 올바른 방법: .env 파일 사용
echo "ZAI_API_KEY=your-actual-key" >> .env

# 틀린 방법: 코드에 직접 입력 (절대 금지)
# ZAI_API_KEY="sk-xxxx"  ← 하드코딩 금지
```

**시크릿이 노출된 경우**

1. 즉시 해당 API 키 폐기/재발급
2. git history에서 시크릿 제거 (`git filter-branch` 또는 `git-filter-repo`)
3. 관련 서비스에 침해 여부 확인

**council/multi-ai-review 보안**

```bash
# 금지: 민감 정보가 포함된 코드를 council 리뷰에 전달
/multi-ai-review  # 내부 API 키, 개인정보, 핵심 비즈니스 로직 제외

# 권장: 민감 부분을 마스킹 후 리뷰 요청
```

**Codex sandbox 모드**

```bash
# Codex는 반드시 sandbox 모드로 실행
codex exec --sandbox workspace-write "코드 생성 요청"
# workspace-write: 작업 디렉터리 내 파일 쓰기만 허용
```

**wrapper 스크립트 보안 원칙**

- wrapper 스크립트에 API 키 직접 입력 금지 (`.env` 참조만 허용)
- 서버 접근은 Tailscale VPN 경유 (공개 인터넷 노출 금지)
- cognit/nexus 서버의 포트는 VPN 내부에서만 접근 가능하도록 방화벽 설정 필요

---

## 8. Context 관리 (Compact 정책)

### 8.1 압력 단계

Maestro는 Spacebot의 context 압력 감시 개념을 재해석하여 적용합니다.

| 단계 | Context 점유율 | 대응 방법 |
|------|----------------|-----------|
| **NORMAL** | < 80% | 정상 작업 계속 |
| **WARNING** | 80-85% | orchestrate wave 중간 검증 실행, 불필요 context 정리 |
| **CRITICAL** | 85-95% | Claude Code strategic-compact 활용, handoff 문서 작성 |
| **OVERFLOW** | > 95% | 세션 종료 + handoff → 새 세션에서 재개 |

### 8.2 단일 세션 작업

소규모 작업에서는 Claude Code의 내장 auto-compact에 의존합니다.

중요한 정보를 보존할 때는 `<remember>` 태그를 사용합니다.

```
# 일반 보존 (7일)
<remember>아키텍처 결정: JWT + Redis 세션 방식 채택</remember>

# 영구 보존
<remember priority>DB 스키마: users 테이블에 soft_delete 컬럼 추가됨</remember>
```

### 8.3 wave 모드 Context 분할

wave 단위(20-40 tasks)로 context가 자연스럽게 분할됩니다.

```
wave 1 (tasks 1-30)
  → 작업 완료
  → Phase 2: handoff 문서 작성
  → context 정리 (상세 내용 폐기)

wave 2 (tasks 31-60)
  → handoff 문서 + contracts만 참조하여 시작
  → 이전 wave 상세 context 없이 진행
  → Phase 2: handoff 작성
  → context 정리

wave 3 (tasks 61-80+)
  → ...
```

### 8.4 handoff 문서 작성

wave 전환 시 다음 항목을 `docs/work-log/handoff-[날짜].md`에 기록합니다.

| 항목 | 필수 여부 | 설명 |
|------|----------|------|
| 완료 태스크 목록 | 필수 | ID + 산출물 경로 |
| 핵심 결정 사항 | 필수 | 아키텍처/기술 선택 |
| contracts 경로 | 필수 | API 계약 파일 위치 |
| 미해결 이슈 | 필수 | 차단 요소, 기술 부채 |
| 상세 구현 메모 | 선택 | 다음 wave 참고 팁 |

handoff 템플릿: `docs/work-log/handoff-template.md` 참조

---

## 9. 트러블슈팅

### 9.1 서버 접근 불가 (nexus/cognit)

**증상**: `UNREACHABLE (ping failed - VPN 확인)` 또는 API 타임아웃

**원인과 해결**

```bash
# 1단계: Tailscale VPN 상태 확인
tailscale status

# 2단계: VPN 재연결
tailscale up

# 3단계: 서버 ping 테스트
ping -c 3 100.64.189.120  # nexus
ping -c 3 100.89.224.48   # cognit

# 4단계: 여전히 안 되면 fallback 활성화
# routing.config.yaml에서 해당 CLI 제거 또는 클라우드 Claude로 임시 대체
```

**즉각 fallback**

nexus/cognit 접근 불가 시, routing.config.yaml의 `fallback_enabled: true` 설정에 의해 클라우드 Claude가 자동으로 처리합니다. 별도 조치 없이 작업을 계속할 수 있습니다.

### 9.2 Wrapper 스크립트 타임아웃

**증상**: `[qwen35-cli] API 호출 실패` 또는 curl 타임아웃

**해결**

```bash
# .env 파일에서 타임아웃 조정
# 기본값 120초 → 더 긴 작업은 300초로 증가
QWEN35_TIMEOUT=300
QWEN_CODER_TIMEOUT=300

# 즉각 테스트
./scripts/qwen35-cli.sh "짧은 테스트 질문"
```

### 9.3 CLi 인증 만료

**증상**: `codex: authentication required` 또는 `gemini: auth error`

```bash
# Codex 재인증
codex login

# Gemini 재인증
gemini auth login

# 인증 상태 확인
codex whoami
gemini auth status
```

### 9.4 ZAI API 연결 오류 (claude-glm)

**증상**: `claude-glm` 실행 시 401/403 에러

**원인**: 환경 변수 미설정 또는 잘못된 변수명

```bash
# 올바른 설정 확인
cat .env | grep ZAI

# 필수: ANTHROPIC_AUTH_TOKEN 사용 (ANTHROPIC_API_KEY 아님!)
# maestro.sh가 자동으로 변환하지만, 수동 실행 시 아래 확인
export ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic
export ANTHROPIC_AUTH_TOKEN=$(grep ZAI_API_KEY .env | cut -d= -f2)

# 연결 테스트
claude-glm status
```

**ZAI Coding Plan 전용 엔드포인트**

반드시 `/api/anthropic` 경로를 사용해야 합니다. 표준 API(`/paas/v4`)는 별도 과금됩니다.

```bash
# 올바른 엔드포인트
ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic  ✓

# 틀린 엔드포인트 (별도 과금 발생!)
ANTHROPIC_BASE_URL=https://api.z.ai/paas/v4  ✗
```

### 9.5 cognit VRAM 부족

**증상**: vLLM OOM 에러, 요청 거부, 응답 없음

**원인**: context 초과 또는 동시 요청 과부하

```bash
# GPU 상태 확인
ssh cognit "nvidia-smi"

# 동시 요청 확인 (1개 초과 시 위험)
ssh cognit "curl -s http://localhost:8000/metrics | grep num_running_requests"

# vLLM 서비스 재시작
ssh cognit "sudo systemctl restart vllm-qwen3-coder.service"

# 재시작 후 상태 확인 (30-60초 대기)
sleep 60
./scripts/health-check.sh cognit
```

**예방 조치**

- Qwen-Coder 사용 시 **context 20K tokens 이하** 유지
- 동시 요청 **1개만** 전송
- 대용량 파일은 nexus(400K context) 사용
- `Qwen3-Coder-Next-AWQ-8bit` (24B) 모델은 VRAM 부족으로 사용 불가

### 9.6 Hook 실패

**증상**: quality-gate, security-scan 등 hook이 실패하여 태스크 차단

```bash
# hook 로그 확인 (orchestrate-standalone 실행 중인 경우)
cat .omc/logs/hook-*.log | tail -50

# lite 프로파일로 임시 전환 (긴급 상황)
/orchestrate-standalone --mode=lite

# 개별 hook 비활성화 (설정 파일 수정)
# .claude/hooks/hook-profiles.yaml에서 해당 hook 주석 처리
```

**가장 흔한 hook 실패 원인**

| Hook | 실패 원인 | 해결 |
|------|-----------|------|
| `quality-gate` | 빌드 에러, 타입 에러, 린트 위반 | 코드 수정 후 재실행 |
| `security-scan` | 시크릿 하드코딩 발견 | 시크릿 제거, .env 사용 |
| `contract-gate` | API 계약 불일치 | contracts/ 파일과 구현 일치시키기 |
| `coverage-gate` | 테스트 커버리지 < 80% | 테스트 추가 |

### 9.7 routing.config.yaml 미적용

**증상**: multi-ai-run이 항상 claude로만 실행됨

```bash
# 설정 파일 위치 확인
ls .claude/routing.config.yaml          # 로컬 설정 (우선순위 높음)
ls ~/.claude/routing.config.yaml        # 글로벌 설정

# 설정 파일 문법 검증 (YAML)
cat .claude/routing.config.yaml | python3 -c "import yaml,sys; yaml.safe_load(sys.stdin); print('OK')"

# claude-imple-skills 스킬 확인
ls ~/.claude/skills/multi-ai-run
ls ~/.claude/commands/multi-ai-run  # 또는 commands 디렉터리
```

---

## 10. 참고 문서

### 내부 문서

| 문서 | 경로 | 내용 |
|------|------|------|
| 운영 가이드 | `docs/운영가이드.md` | 간결한 일상 운영 참조 |
| 고도화 종합계획서 | `docs/계획서/MAESTRO_UPGRADE_PLAN.md` | 전체 아키텍처 설계 결정 |
| Compact 정책 | `docs/work-log/compact-policy.md` | Context 관리 정책 |
| Handoff 템플릿 | `docs/work-log/handoff-template.md` | wave 전환 인수인계 포맷 |
| Quality Gate 순서 | `docs/work-log/verify-quality-gate-order.md` | 게이트 실행 순서 |
| Spacebot 개념 매핑 | `docs/work-log/spacebot-concept-mapping.md` | Spacebot 철학 재해석 |
| 작업 기록 | `docs/work-log/` | 세션별 작업 기록 |

### 외부 저장소

| 저장소 | URL | 참조 이유 |
|--------|-----|-----------|
| claude-imple-skills | https://github.com/insightflo/claude-imple-skills | 핵심 기반 도구 (routing + agents + hooks) |
| spacebot | https://github.com/spacedriveapp/spacebot | 운영 모델 reference (개념 차용) |
| agent-council | https://github.com/team-attention/agent-council | 멀티 AI 의사결정 참조 |
| everything-claude-code | https://github.com/affaan-m/everything-claude-code | hook/verify/lifecycle 패턴 |

### 비용 구조

| 서비스 | 비용 | 비고 |
|--------|------|------|
| Claude (Anthropic) | 구독 월정액 | opus/sonnet/haiku 포함 |
| GLM-5 / GLM-4.5-Air (ZAI) | $3/월 Coding Plan | `/api/anthropic` 엔드포인트 전용 |
| gpt-5.3-codex (OpenAI) | OpenAI 구독 | codex CLI |
| gemini-3.1-pro (Google) | Google 구독 | gemini CLI |
| nexus 서버 (Qwen3.5-122B) | 전기료만 | RTX 3090 x3, 자체 운영 |
| cognit 서버 (Qwen3-Coder-30B) | 전기료만 | RTX 3080 Ti x2, 자체 운영 |

**비용 절감 전략**

- 일반 작업은 `claude-glm` 우선 → Anthropic 구독 소모 절약
- 대형 context 작업은 nexus 활용 → API 비용 0
- 반복적 코드 생성은 cognit 활용 → API 비용 0
- ZAI API는 반드시 Coding Plan 전용 엔드포인트(`/api/anthropic`)만 사용
