# 🎼 Maestro Claude Code

> **멀티 LLM 오케스트레이션 시스템** — Claude Code를 지휘자로, 6개 AI 모델을 역할별로 라우팅하여 비용을 절감하고 품질을 높입니다.

---

## 📖 목차

1. [프로젝트 소개](#1-프로젝트-소개)
2. [아키텍처 개요](#2-아키텍처-개요)
3. [모델 인프라](#3-모델-인프라)
4. [빠른 시작](#4-빠른-시작)
5. [디렉터리 구조](#5-디렉터리-구조)
6. [라우팅 설정](#6-라우팅-설정)
7. [주요 명령어](#7-주요-명령어)
8. [Hook 프로파일](#8-hook-프로파일)
9. [서버 관리](#9-서버-관리)
10. [참고 자료](#10-참고-자료)
11. [라이선스](#11-라이선스)

---

## 1. 🚀 프로젝트 소개

**Maestro Claude Code**는 Claude Code를 중심 오케스트레이터로 삼아, 작업 유형과 복잡도에 따라 6개의 AI 모델에 태스크를 자동 위임하는 CLI 레벨 멀티 LLM 오케스트레이션 시스템입니다.

### 핵심 가치

- **비용 최적화**: 고비용 Claude API 호출을 로컬 서버(Qwen3.5-122B, Qwen3-Coder-30B) 또는 저비용 API(GLM-5, $3/월)로 대체
- **역할 특화**: 코드 생성은 Codex/Qwen-Coder, 디자인은 Gemini, 추론은 Qwen3.5-122B 등 모델별 강점 활용
- **품질 게이트**: 16개 Hook을 통한 자동 검증 (lint, type-check, security-scan, test)
- **CLI 투명성**: Docker/서버 없이 표준 CLI 명령어(`codex exec`, `gemini`, `claude-glm`)로 동작

### 기술 기반

[`claude-imple-skills`](https://github.com/insightflo/claude-imple-skills)를 핵심 기반으로 채택하여 다음을 구현합니다.

| 구성요소 | 역할 |
|---------|------|
| `routing.config.yaml` | role / task_type / domain 3계층 라우팅 |
| `project-team` | 10 에이전트 + 15 Hook (lite/standard/full 모드) |
| `orchestrate-standalone` | wave/sprint/lite 오케스트레이션 |

---

## 2. 🏗️ 아키텍처 개요

### 실행 흐름

```
사용자 요청
  │
  ▼
Claude Code (구독, 오케스트레이터)
  ├─► OMC 에이전트 (Claude Code 내부 subagent)
  │     └─ 50개 에이전트 풀 (architect, executor, designer ...)
  │
  ├─► claude-imple-skills multi-ai-run (태스크 위임)
  │     ├─► codex exec (gpt-5.3-codex)    : 코드 생성 / 리뷰
  │     ├─► gemini (gemini-3.1-pro)        : 디자인 / UI / 멀티모달
  │     ├─► wrapper ──► nexus:8080         : Qwen3.5-122B — 고급 추론
  │     └─► wrapper ──► cognit:8000        : Qwen3-Coder-30B — 코드 생성
  │
  ├─► hooks (품질 게이트)
  │     ├─ pre-tool: context-injector, intent-validator
  │     ├─ post-tool: lint-check, type-check, test-runner
  │     └─ stop: security-scan, summary-generator
  │
  └─► orchestrate (wave / sprint 태스크 관리)
        ├─ Wave 모드: 병렬 단계별 실행
        └─ Sprint 모드: TDD 기반 반복 개선
```

### 2계층 라우팅 구조

| 계층 | 시스템 | 라우팅 대상 | 설정 파일 |
|------|--------|------------|---------|
| 에이전트 내부 | OMC (`oh-my-claudecode`) | Claude Code subagent | `~/.claude/CLAUDE.md` |
| 태스크 위임 | `claude-imple-skills` | 역할별 외부 CLI | `.claude/routing.config.yaml` |

> **설계 원칙**: Claude Code가 오케스트레이터 역할을 유지하고, 개별 태스크를 비용·속도·품질 기준으로 최적 모델에 위임합니다. 에이전트 간 통신은 표준 CLI stdin/stdout을 사용하므로 추가 인프라가 필요 없습니다.

---

## 3. 🤖 모델 인프라

| # | 모델 | 제공처 | CLI / 접근 | 주요 용도 | Context |
|---|------|--------|-----------|---------|---------|
| 1 | **Claude (구독)** | Anthropic | `claude` | 오케스트레이션, 아키텍처 설계 | 200K |
| 2 | **GLM-5** | ZAI ($3/월) | `claude-glm` | 저비용 Claude 대체, 범용 작업 | - |
| 3 | **gpt-5.3-codex** | OpenAI | `codex exec` | 코드 생성, 리뷰, 디버깅 | - |
| 4 | **gemini-3.1-pro** | Google | `gemini` | 디자인, UI, 멀티모달 분석 | - |
| 5 | **Qwen3.5-122B** | nexus (자체) | `qwen35-cli.sh` | 고급 추론, 장문 분석 | 400K |
| 6 | **Qwen3-Coder-30B** | cognit (자체) | `qwen-coder-cli.sh` | 코드 생성, 보일러플레이트 | 16K |

### 비용 구조

```
월간 예상 비용 (중간 규모 프로젝트 기준)
─────────────────────────────────────────
Claude 구독     : ~~$20/월~~ (오케스트레이션 위주, 직접 코드 생성 최소화)
GLM-5 (ZAI)    : $3/월    (Coding Plan, 정액)
Codex          : 사용량 과금 (OpenAI API)
Gemini         : 무료 티어 / 사용량 과금
nexus 서버      : 전기료 (RTX 3090 x3, 자체 호스팅)
cognit 서버     : 전기료 (RTX 3080 Ti x2, 자체 호스팅)
─────────────────────────────────────────
Claude 단독 대비 약 40~60% 비용 절감 목표
```

### ZAI API 설정

```bash
# ZAI API는 Anthropic 프로토콜 호환 엔드포인트를 사용합니다.
export ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic
export ANTHROPIC_AUTH_TOKEN=${ZAI_API_KEY}   # ANTHROPIC_API_KEY가 아님!

# 모델 매핑
# opus/sonnet → GLM-5
# haiku       → GLM-4.5-Air
```

> 공식 문서: https://docs.z.ai/devpack/tool/claude

---

## 4. ⚡ 빠른 시작

### 사전 요구사항

| 항목 | 버전 | 확인 명령 |
|------|------|---------|
| Claude Code CLI | 최신 | `claude --version` |
| Node.js | v18+ | `node --version` |
| Python | 3.10+ | `python3 --version` |
| oh-my-claudecode (OMC) | 3.3.8+ | `claude /oh-my-claudecode:doctor` |
| ZAI API 키 | - | `echo $ZAI_API_KEY` |
| VPN 연결 | 10.5.5.x | `ping 10.5.5.14` (자체 서버 사용 시) |

### 설치

```bash
# 1. 저장소 클론
git clone https://github.com/your-org/maestro-claude-code.git
cd maestro-claude-code

# 2. 환경 변수 설정
cp .env.example .env
# .env 파일에 API 키 입력:
#   ZAI_API_KEY=...
#   OPENAI_API_KEY=...
#   GOOGLE_API_KEY=...

# 3. 스크립트 실행 권한 부여
chmod +x scripts/*.sh

# 4. 서버 상태 확인 (자체 서버 사용 시)
./scripts/health-check.sh

# 5. 보안 스캔 (환경 변수 노출 여부 확인)
./scripts/security-scan.sh
```

### 첫 실행

```bash
# 기본 Claude Code 실행 (오케스트레이터)
claude

# GLM-5 저비용 모드 실행
./scripts/maestro.sh
# 또는
claude-glm

# 자체 서버 연결 확인
./scripts/health-check.sh
```

### 멀티 AI 태스크 위임

Claude Code 내에서 다음 명령어로 외부 AI에 태스크를 위임합니다.

```bash
# 멀티 AI 태스크 실행 (routing.config.yaml 기반 자동 라우팅)
/multi-ai-run "사용자 인증 모듈 구현"

# 멀티 AI 코드 리뷰 (Codex + Gemini + Qwen 동시 리뷰)
/multi-ai-review src/auth/

# 대규모 태스크 오케스트레이션
/orchestrate-standalone wave "결제 시스템 전체 구현"
```

---

## 5. 📁 디렉터리 구조

```
maestro-claude-code/
├── .claude/
│   ├── routing.config.yaml        # 6개 모델 역할별 라우팅 설정
│   ├── council.config.yaml        # 멀티 AI 리뷰 설정 (agent-council)
│   ├── agents/                    # project-team 에이전트 (7개)
│   │   ├── architect.md           # 아키텍처 설계 전문 에이전트
│   │   ├── executor.md            # 코드 실행 전문 에이전트
│   │   ├── reviewer.md            # 코드 리뷰 에이전트
│   │   ├── tester.md              # 테스트 작성 에이전트
│   │   ├── designer.md            # UI/UX 디자인 에이전트
│   │   ├── security.md            # 보안 감사 에이전트
│   │   └── docs.md                # 문서 작성 에이전트
│   ├── hooks/                     # 품질 게이트 hooks (16개)
│   │   ├── pre-tool/              # 도구 실행 전 검증
│   │   │   ├── context-injector.py
│   │   │   └── intent-validator.py
│   │   ├── post-tool/             # 도구 실행 후 검증
│   │   │   ├── lint-check.py
│   │   │   ├── type-check.py
│   │   │   └── test-runner.py
│   │   └── stop/                  # 세션 종료 시 처리
│   │       ├── security-scan.py
│   │       └── summary-generator.py
│   └── memory/                    # 세션 간 메모리 (MEMORY.md)
│
├── scripts/
│   ├── maestro.sh                 # GLM-5 (ZAI) 모드 런처
│   ├── qwen35-cli.sh              # nexus wrapper (Qwen3.5-122B, port 8080)
│   ├── qwen-coder-cli.sh          # cognit wrapper (Qwen3-Coder-30B, port 8000)
│   ├── health-check.sh            # 전체 서버 상태 점검
│   ├── security-scan.sh           # 시크릿/취약점 스캔
│   └── status.sh                  # 현재 시스템 상태 요약
│
├── docs/
│   ├── 계획서/
│   │   ├── Nexus-vLLM-벤치마크-계획서.md
│   │   └── MAESTRO_UPGRADE_PLAN.md
│   ├── planning/
│   │   ├── PRD.md                 # 제품 요구사항 정의서
│   │   └── TASKS.md               # 태스크 목록
│   ├── work-log/                  # 작업 기록
│   └── 리포트/                    # 분석 리포트
│
├── artifacts/
│   └── runs/                      # 실행 로그 및 결과물 (gitignore)
│
├── .env.example                   # 환경 변수 템플릿
├── .gitignore                     # Git 제외 목록
├── AGENTS.md                      # AI 에이전트 문서 (agent-council용)
└── README.md                      # 이 파일
```

---

## 6. 🔀 라우팅 설정

`.claude/routing.config.yaml`에서 3계층 라우팅 규칙을 정의합니다.

### 역할 기반 라우팅 (role_routing)

| 역할 | 라우팅 대상 | 이유 |
|------|------------|------|
| `architect` | Claude (구독) | 시스템 설계는 최고 수준 추론 필요 |
| `code_generator` | Codex / Qwen-Coder | 코드 생성 특화 모델 |
| `code_reviewer` | Codex + Gemini (멀티) | 다각도 리뷰 |
| `designer` | Gemini | 멀티모달, UI 강점 |
| `security_auditor` | Claude (구독) | 보안 판단은 신뢰도 우선 |
| `documenter` | GLM-5 | 문서 작성은 저비용 모델로 충분 |
| `reasoner` | Qwen3.5-122B | 400K context, 장문 추론 |
| `tester` | Qwen-Coder / Codex | 테스트 코드 생성 특화 |

### 태스크 유형 기반 라우팅 (task_type_routing)

| 태스크 유형 | 라우팅 대상 | 예시 |
|------------|------------|------|
| `boilerplate` | Qwen-Coder (cognit) | CRUD 모델, DTO, 마이그레이션 |
| `complex_logic` | Claude / Qwen3.5-122B | 알고리즘, 비즈니스 로직 |
| `ui_component` | Gemini | React 컴포넌트, CSS, 디자인 |
| `code_review` | Codex exec | PR 리뷰, 버그 탐지 |
| `documentation` | GLM-5 | README, JSDoc, API 문서 |
| `architecture` | Claude (구독) | 시스템 설계, ERD, 시퀀스 다이어그램 |
| `security_check` | Claude (구독) | 취약점 분석, 코드 감사 |
| `long_context` | Qwen3.5-122B | 대용량 파일 분석, 코드베이스 요약 |

### 설정 예시

```yaml
# .claude/routing.config.yaml
version: "1.0"

models:
  claude_default:
    command: "claude"
    description: "Anthropic 구독 (오케스트레이터)"
  glm5:
    command: "claude-glm"
    description: "ZAI GLM-5 (저비용)"
  codex:
    command: "codex exec"
    description: "OpenAI gpt-5.3-codex"
  gemini:
    command: "gemini"
    description: "Google gemini-3.1-pro"
  qwen35:
    command: "./scripts/qwen35-cli.sh"
    description: "nexus Qwen3.5-122B (자체 서버)"
  qwen_coder:
    command: "./scripts/qwen-coder-cli.sh"
    description: "cognit Qwen3-Coder-30B (자체 서버)"

role_routing:
  architect:      claude_default
  code_generator: [codex, qwen_coder]
  designer:       gemini
  documenter:     glm5
  reasoner:       qwen35

task_type_routing:
  boilerplate:    qwen_coder
  ui_component:   gemini
  long_context:   qwen35
  documentation:  glm5
  architecture:   claude_default
  security_check: claude_default
```

---

## 7. 💻 주요 명령어

### 기본 실행

| 명령어 | 설명 |
|--------|------|
| `claude` | 기본 Claude Code 실행 (Anthropic 구독, 오케스트레이터) |
| `claude-glm` | GLM-5 저비용 모드 (ZAI API, $3/월 정액) |
| `./scripts/maestro.sh` | GLM-5 모드 런처 (환경 변수 자동 설정 포함) |

### 멀티 AI 명령어 (Claude Code 내부)

| 명령어 | 설명 |
|--------|------|
| `/multi-ai-run [태스크]` | routing.config.yaml 기반 자동 모델 선택 후 태스크 실행 |
| `/multi-ai-review [경로]` | 여러 AI 모델로 동시 코드 리뷰 (Codex + Gemini + Qwen) |
| `/orchestrate-standalone wave [태스크]` | Wave 모드: 태스크를 병렬 단계로 분해하여 실행 |
| `/orchestrate-standalone sprint [태스크]` | Sprint 모드: TDD 기반 반복 개선 사이클 |
| `/orchestrate-standalone lite [태스크]` | Lite 모드: 경량 오케스트레이션 (단순 태스크용) |

### 자체 서버 CLI

| 명령어 | 설명 |
|--------|------|
| `./scripts/qwen35-cli.sh "[프롬프트]"` | nexus 서버 Qwen3.5-122B 직접 호출 |
| `./scripts/qwen-coder-cli.sh "[프롬프트]"` | cognit 서버 Qwen3-Coder-30B 직접 호출 |

### 유지보수

| 명령어 | 설명 |
|--------|------|
| `./scripts/health-check.sh` | 전체 서버(nexus, cognit) 및 API 상태 점검 |
| `./scripts/security-scan.sh` | .env 시크릿 노출, 하드코딩 키 탐지 |
| `./scripts/status.sh` | 현재 시스템 상태 요약 출력 |

### OMC 매직 키워드 (Claude Code 내부)

```bash
# 자동화 실행
"autopilot: REST API 구현"        # 완전 자동화 실행
"ralph: 버그 수정 완료까지"        # 완료까지 지속 실행
"ulw: 전체 리팩토링"              # 최대 병렬 실행
"plan: 새 기능 설계"              # 기획 인터뷰 시작
"eco: 문서 작성"                  # 토큰 절약 모드
```

---

## 8. 🔗 Hook 프로파일

Hook은 Claude Code의 도구 실행 전후에 자동으로 실행되는 품질 게이트입니다. 3단계 프로파일로 프로젝트 규모와 요구사항에 맞게 선택합니다.

### Lite 프로파일 (빠른 반복 개발)

```
활성화 Hook: 5개
├── pre-tool: context-injector (컨텍스트 주입)
├── post-tool: lint-check (기본 문법 오류 탐지)
└── stop: security-scan (시크릿 노출 방지)

적합한 상황: 프로토타입, POC, 빠른 기능 검증
소요 오버헤드: 낮음 (~2초/작업)
```

### Standard 프로파일 (기본 권장)

```
활성화 Hook: 10개
├── pre-tool: context-injector, intent-validator
├── post-tool: lint-check, type-check, test-runner (단위 테스트)
└── stop: security-scan, summary-generator

적합한 상황: 일반 개발, 팀 협업, 기능 브랜치
소요 오버헤드: 중간 (~5초/작업)
```

### Full 프로파일 (프로덕션 배포 전)

```
활성화 Hook: 16개
├── pre-tool: context-injector, intent-validator, risk-assessor
├── post-tool: lint-check, type-check, test-runner (전체),
│             coverage-check (≥80%), dependency-audit,
│             performance-profiler, docs-verifier
└── stop: security-scan, compliance-check,
          summary-generator, changelog-updater

적합한 상황: PR 병합 전, 배포 준비, 보안 감사
소요 오버헤드: 높음 (~15초/작업)
```

### 프로파일 전환

```bash
# .claude/settings.json에서 설정
{
  "hookProfile": "standard"   # "lite" | "standard" | "full"
}
```

---

## 9. 🖥️ 서버 관리

### 서버 사양

| 서버 | VPN IP | GPU | 모델 | 포트 | 서비스 |
|------|--------|-----|------|------|--------|
| **nexus** | `10.5.5.14` | RTX 3090 × 3 | Qwen3.5-122B (Q3_K_XL) | 8080 | llama-server |
| **cognit** | - | RTX 3080 Ti × 2 | Qwen3-Coder-30B-A3B AWQ-4bit | 8000 | vLLM |

> **주의**: 두 서버 모두 VPN 연결(`10.5.5.x`)이 필요합니다. 접속 전 `ping 10.5.5.14` 로 연결을 확인하세요.

### nexus 서버 관리

```bash
# 서버 상태 확인
curl http://10.5.5.14:8080/health

# 직접 API 호출 테스트
curl -X POST http://10.5.5.14:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "qwen3.5-122b", "messages": [{"role": "user", "content": "hello"}]}'

# CLI 래퍼 사용
./scripts/qwen35-cli.sh "설계 문서를 분석해줘"
```

### cognit 서버 관리

```bash
# 서비스 상태 (원격)
ssh cognit "systemctl status vllm-qwen3-coder.service"

# 서비스 재시작
ssh cognit "sudo systemctl restart vllm-qwen3-coder.service"

# GPU 사용량 확인
ssh cognit "nvidia-smi"

# CLI 래퍼 사용
./scripts/qwen-coder-cli.sh "FastAPI CRUD 엔드포인트 생성"
```

### cognit 서버 상세 사양

```
모델: Qwen3-Coder-30B-A3B-Instruct AWQ-4bit
VRAM: GPU당 11.4GB / 12GB (RTX 3080 Ti × 2)
Context: 16K tokens
서비스: vllm-qwen3-coder.service (systemd, 자동시작 enabled)
추가: ollama (port 11434, qwen3.5:27b 등 보유)

제약: Qwen3-Coder-Next-AWQ-8bit (24B)는 VRAM 부족으로 불가
```

### 전체 상태 점검

```bash
./scripts/health-check.sh

# 출력 예시:
# [OK]  Claude Code    : claude --version
# [OK]  ZAI API        : api.z.ai 응답 정상
# [OK]  nexus (8080)   : Qwen3.5-122B 응답 정상 (latency: 1.2s)
# [OK]  cognit (8000)  : Qwen3-Coder-30B 응답 정상 (latency: 0.8s)
# [--]  Codex          : OPENAI_API_KEY 설정 필요
# [OK]  Gemini         : GOOGLE_API_KEY 유효
```

---

## 10. 📚 참고 자료

### 핵심 참고 저장소

| 저장소 | 역할 | 적용 방식 |
|--------|------|---------|
| [insightflo/claude-imple-skills](https://github.com/insightflo/claude-imple-skills) | **핵심 기반** — routing, agents, hooks, orchestration | 직접 도입 및 커스터마이징 |
| [spacedriveapp/spacebot](https://github.com/spacedriveapp/spacebot) | 운영 모델 레퍼런스 (Rust 기반) | 개념만 차용 (코드 이식 불가) |
| [team-attention/agent-council](https://github.com/team-attention/agent-council) | 멀티 AI 의사결정 — `council.config.yaml` | 선택적 sidecar로 도입 |
| [affaan-m/everything-claude-code](https://github.com/affaan-m/everything-claude-code) | Hook / verify / session lifecycle 패턴 | 선별 도입 |

### 내부 문서

| 문서 | 내용 |
|------|------|
| [`AGENTS.md`](./AGENTS.md) | AI 에이전트 역할 및 권한 정의 |
| [`docs/planning/PRD.md`](./docs/planning/PRD.md) | 제품 요구사항 정의서 |
| [`docs/planning/TASKS.md`](./docs/planning/TASKS.md) | 태스크 목록 및 진행 현황 |
| [`docs/계획서/MAESTRO_UPGRADE_PLAN.md`](./docs/계획서/MAESTRO_UPGRADE_PLAN.md) | 고도화 계획서 |
| [`docs/계획서/Nexus-vLLM-벤치마크-계획서.md`](./docs/계획서/Nexus-vLLM-벤치마크-계획서.md) | nexus 서버 벤치마크 계획 |

### 외부 문서

| 문서 | URL |
|------|-----|
| ZAI API (Claude 호환) | https://docs.z.ai/devpack/tool/claude |
| Claude Code 공식 문서 | https://docs.anthropic.com/claude-code |
| oh-my-claudecode (OMC) | `claude /oh-my-claudecode:help` |
| Qwen3 모델 정보 | https://huggingface.co/Qwen |

---

## 11. 📄 라이선스

이 프로젝트는 내부 인프라 운영 목적으로 작성되었습니다.

기반 도구인 `claude-imple-skills`의 라이선스를 따릅니다.

---

<div align="center">

**Maestro Claude Code** — 여러 AI를 하나의 지휘봉으로

`claude` · `codex` · `gemini` · `glm` · `qwen`

</div>
