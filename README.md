# 🎼 Maestro Claude Code

> **멀티 LLM 오케스트레이션 시스템** — Claude Code를 지휘자로, 6개 AI 모델을 역할별로 라우팅하여 비용을 절감하고 품질을 높입니다.

---

## 📖 목차

1. [프로젝트 소개](#1-프로젝트-소개)
2. [아키텍처 개요](#2-아키텍처-개요)
3. [모델 인프라](#3-모델-인프라)
4. [빠른 시작](#4-빠른-시작)
5. [LiteLLM Proxy (CCR 패턴)](#5-litellm-proxy-ccr-패턴)
6. [디렉터리 구조](#6-디렉터리-구조)
7. [라우팅 설정](#7-라우팅-설정)
8. [주요 명령어](#8-주요-명령어)
9. [Hook 프로파일](#9-hook-프로파일)
10. [서버 관리](#10-서버-관리)
11. [참고 자료](#11-참고-자료)

---

## 1. 🚀 프로젝트 소개

**Maestro Claude Code**는 Claude Code를 중심 오케스트레이터로 삼아, 작업 유형과 복잡도에 따라 6개의 AI 모델에 태스크를 자동 위임하는 CLI 레벨 멀티 LLM 오케스트레이션 시스템입니다.

### 실행 경로

```bash
# 심볼릭 링크를 통한 전역 접근
~/.claude/maestro          # → /Users/hwandam/workspace/maestro-claude-code (symlink)

# 프로젝트 루트에서 직접 실행
cd ~/.claude/maestro
./scripts/maestro.sh       # GLM-5 모드
./scripts/ccproxy-start.sh start  # LiteLLM Proxy 시작
```

### 핵심 가치

- **비용 최적화**: 고비용 Claude API 호출을 로컬 서버(Qwen3.5-122B, Qwen3-Coder-30B) 또는 저비용 API(GLM-5, $3/월)로 대체
- **역할 특화**: 코드 생성은 Codex/Qwen-Coder, 디자인은 Gemini, 추론은 Qwen3.5-122B 등 모델별 강점 활용
- **Phase 5 CCR 패턴**: 53개 OMC 에이전트 → 최적 모델 자동 라우팅 (SubagentStart hook 기반)
- **LiteLLM Proxy**: 단일 엔드포인트(port 4000)로 6개 모델 통합 관리
- **품질 게이트**: Hook을 통한 자동 검증 (lint, type-check, security-scan, test)

---

## 2. 🏗️ 아키텍처 개요

### 실행 흐름

```
사용자 요청
  │
  ▼
Claude Code (구독, 오케스트레이터)
  ├─► OMC 에이전트 (Claude Code 내부 subagent, 50개 풀)
  │     └─ SubagentStart → subagent-router.py → LiteLLM Proxy (CCR 패턴)
  │
  ├─► LiteLLM Proxy (port 4000)
  │     ├─► GLM-5 alias → qwen3.5-122b (ZAI CLI 전용, fallback)
  │     ├─► qwen3.5-122b → nexus:8080 (Tailscale 100.124.117.46)
  │     ├─► qwen3-coder-30b → cognit:8000 (Tailscale 100.121.138.74)
  │     ├─► gemini-3.1-pro → gemini-2.0-flash (Google API)
  │     └─► gpt-5.4-medium → gpt-4o (OpenAI API)
  │
  ├─► claude-imple-skills multi-ai-run (태스크 위임)
  │     ├─► codex exec (gpt-5.3-codex)    : 코드 생성 / 리뷰
  │     ├─► gemini (gemini-3.1-pro)        : 디자인 / UI / 멀티모달
  │     ├─► wrapper ──► nexus:8080         : Qwen3.5-122B — 고급 추론
  │     └─► wrapper ──► cognit:8000        : Qwen3-Coder-30B — 코드 생성
  │
  ├─► hooks (품질 게이트)
  │     ├─ pre-tool: contract-gate.js
  │     ├─ post-tool: security-scan.js
  │     └─ stop: task-sync.js
  │
  └─► orchestrate (wave / sprint 태스크 관리)
```

### 2계층 라우팅 구조

| 계층 | 시스템 | 라우팅 대상 | 설정 파일 |
|------|--------|------------|---------|
| 에이전트 내부 | OMC + LiteLLM Proxy | 53개 OMC 에이전트 → 6개 모델 | `config/agent-model-map.yaml` |
| 태스크 위임 | `claude-imple-skills` | 역할별 외부 CLI | `.claude/routing.config.yaml` |

---

## 3. 🤖 모델 인프라

| # | 모델 ID | 제공처 | CLI / 접근 | 주요 용도 | Context |
|---|---------|--------|-----------|---------|---------|
| 1 | **claude-sonnet-4-6** | Anthropic 구독 | `claude` | 오케스트레이션, 아키텍처 설계, 보안 감사 | 200K |
| 2 | **glm-5 → qwen3.5-122b** | ZAI ($3/월) + 자체서버 | `claude-glm` | 저비용 Claude 대체 (CLI 전용) | 400K |
| 3 | **gpt-5.4-medium → gpt-4o** | OpenAI | `codex exec` | 코드 생성, 리뷰, 디버깅 | - |
| 4 | **gemini-3.1-pro → gemini-2.0-flash** | Google | `gemini` | 디자인, UI, 멀티모달 분석 | - |
| 5 | **qwen3.5-122b** | nexus 자체서버 | Proxy/직접 | 고급 추론, 장문 분석, 400K ctx | 400K |
| 6 | **qwen3-coder-30b** | cognit 자체서버 | Proxy/직접 | 코드 생성, 보일러플레이트 | 20K |

### 자체 서버 인프라

| 서버 | Tailscale IP | 포트 | 모델 | 하드웨어 |
|------|-------------|------|------|---------|
| nexus | `100.124.117.46` | `8080` | Qwen3.5-122B Q3_K_XL | RTX 3090 x3 |
| cognit | `100.121.138.74` | `8000` | Qwen3-Coder-30B AWQ-4bit | RTX 3080 Ti x2 |

### 비용 구조

```
월간 예상 비용 (중간 규모 프로젝트 기준)
──────────────────────────────────────────
Claude 구독      : $20/월  (오케스트레이션 위주, 코드 생성 최소화)
GLM-5 (ZAI)     : $3/월   (Coding Plan 정액, Claude CLI 전용)
qwen3.5-122b    : 무료    (nexus 자체 서버 — 전기료만)
qwen3-coder-30b : 무료    (cognit 자체 서버 — 전기료만)
gemini-3.1-pro  : 무료 티어 / 사용량 과금
gpt-5.4-medium  : Codex 구독 포함
──────────────────────────────────────────
Claude 단독 대비 약 40~60% 비용 절감 목표
```

### 에이전트별 모델 배정 (Phase 5 CCR 패턴)

| 티어 | 모델 | 에이전트 예시 | 비율 |
|------|------|-------------|------|
| 아키텍처/보안 | `claude-sonnet-4-6` | architect, critic, security-specialist | ~1% |
| 코드 작업 | `gpt-5.4-medium` | executor, code-reviewer, backend-specialist | ~25% |
| 디자인/멀티모달 | `gemini-3.1-pro` | designer, vision, frontend-specialist | ~2% |
| 장문 분석 | `qwen3.5-122b` | analyst, scientist, explore-high | ~5% |
| 경량 코드 | `qwen3-coder-30b` | executor-low, build-fixer, tdd-guide-low | ~12% |
| 기본 (대다수) | `glm-5` (fallback: qwen3.5-122b) | explore, researcher, writer, git-master | ~55% |

---

## 4. ⚡ 빠른 시작

### 사전 요구사항

| 항목 | 버전 | 확인 명령 |
|------|------|---------|
| Claude Code CLI | 최신 | `claude --version` |
| Node.js | v18+ | `node --version` |
| Python | 3.10+ | `python3 --version` |
| LiteLLM | 1.82+ | `litellm --version` |
| oh-my-claudecode (OMC) | 3.3.8+ | `claude /oh-my-claudecode:doctor` |
| ZAI API 키 | - | `echo $ZAI_API_KEY` |
| Tailscale VPN | - | `tailscale status` (자체 서버 사용 시) |

### 설치

```bash
# 1. 저장소 클론 (또는 ~/.claude/maestro symlink 사용)
git clone https://github.com/your-org/maestro-claude-code.git
cd maestro-claude-code

# ~/.claude/maestro 심볼릭 링크 생성 (전역 접근)
ln -sf "$(pwd)" ~/.claude/maestro

# 2. 환경 변수 설정
cp .env.example .env
# .env 파일에 API 키 입력:
#   ZAI_API_KEY=...
#   OPENAI_API_KEY=...
#   GOOGLE_API_KEY=...
#   ANTHROPIC_API_KEY=...

# 3. 스크립트 실행 권한 부여
chmod +x scripts/*.sh

# 4. LiteLLM Proxy 시작
./scripts/ccproxy-start.sh start

# 5. 서버 상태 확인
./scripts/ccproxy-start.sh status
./scripts/health-check.sh
```

### 첫 실행

```bash
# [경로 1] ~/.claude/maestro에서 실행 (심볼릭 링크)
cd ~/.claude/maestro
./scripts/maestro.sh           # GLM-5 모드 (ZAI Coding Plan)

# [경로 2] 프로젝트 루트에서 직접 실행
claude                         # 기본 Claude Code 오케스트레이터
claude-glm                     # GLM-5 저비용 모드 (alias)
./scripts/maestro.sh           # GLM-5 모드 런처 스크립트

# LiteLLM Proxy 관리
./scripts/ccproxy-start.sh start    # 시작
./scripts/ccproxy-start.sh stop     # 종료
./scripts/ccproxy-start.sh status   # 상태 확인
./scripts/ccproxy-start.sh restart  # 재시작
```

### 멀티 AI 태스크 위임

```bash
# Claude Code 세션 내에서:
/multi-ai-run "사용자 인증 모듈 구현"
/multi-ai-review src/auth/
/orchestrate-standalone wave "결제 시스템 전체 구현"

# LiteLLM Proxy 직접 테스트
curl -s http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-maestro" \
  -d '{"model": "qwen3.5-122b", "messages": [{"role": "user", "content": "Hello"}]}'
```

---

## 5. 🔌 LiteLLM Proxy (CCR 패턴)

Phase 5에서 구현된 LiteLLM Proxy 기반 에이전트별 모델 라우팅입니다.

### 아키텍처

```
SubagentStart 이벤트
  └─► .claude/hooks/subagent-router.py
        ├─► config/agent-model-map.yaml 조회 (53개 에이전트)
        ├─► logs/ccproxy/.agent-model-hint 기록 (TTL 30초, one-shot)
        └─► http://localhost:3456/event 관찰성 이벤트 전송

LiteLLM Proxy (port 4000) 요청 수신
  └─► tools/litellm_callback.py (AgentRouter.async_pre_call_hook)
        ├─► .agent-model-hint 파일 읽기 (읽은 후 즉시 삭제)
        └─► request.model 동적 오버라이드
```

### Proxy 설정 (`config/ccproxy.yaml`)

```yaml
model_list:
  - model_name: "claude-sonnet-4-6"  # OMC 기본 요청 → ZAI GLM-5
    litellm_params:
      model: "openai/claude-sonnet-4-6"
      api_base: "https://api.z.ai/api/anthropic"
      api_key: "os.environ/ZAI_API_KEY"

  - model_name: "qwen3.5-122b"       # 장문 분석용 → nexus
    litellm_params:
      model: "openai/Qwen3.5-122B-Q3_K_XL"
      api_base: "http://100.124.117.46:8080/v1"

  - model_name: "qwen3-coder-30b"    # 경량 코드 → cognit
    litellm_params:
      model: "openai/qwen3-coder"
      api_base: "http://100.121.138.74:8000/v1"

  - model_name: "gemini-3.1-pro"     # 디자인/UI → Google
    litellm_params:
      model: "gemini/gemini-2.0-flash"

  - model_name: "gpt-5.4-medium"     # 코드 작업 → OpenAI
    litellm_params:
      model: "openai/gpt-4o"
```

### GLM-5 제약 사항

```
⚠️  ZAI Coding Plan은 Claude CLI 전용 구독입니다.
    LiteLLM Proxy에서 GLM-5로 직접 API 호출 시 인증 실패.

    → GLM-5 사용: ./scripts/maestro.sh (claude-glm 명령)
    → Proxy에서 glm-5 요청 시: qwen3.5-122b로 자동 fallback
```

### LiteLLM Proxy 실행 확인

```bash
# 힌트 파일 확인 (에이전트 라우팅 디버깅)
cat logs/ccproxy/.agent-model-hint

# 에이전트 라우팅 수동 테스트
echo '{"agent_name": "executor"}' | python3 .claude/hooks/subagent-router.py

# 실제 추론 테스트 (nexus)
curl -s http://localhost:4000/v1/chat/completions \
  -H "Authorization: Bearer sk-maestro" \
  -d '{"model": "qwen3.5-122b", "messages": [{"role": "user", "content": "1+1=?"}]}'

# 실제 추론 테스트 (cognit)
curl -s http://localhost:4000/v1/chat/completions \
  -H "Authorization: Bearer sk-maestro" \
  -d '{"model": "qwen3-coder-30b", "messages": [{"role": "user", "content": "Hello"}]}'
```

---

## 6. 📁 디렉터리 구조

```
~/.claude/maestro/  (symlink → /Users/hwandam/workspace/maestro-claude-code)
│
├── .claude/
│   ├── hooks/
│   │   ├── subagent-router.py         # Phase 5: SubagentStart → 모델 힌트 기록
│   │   ├── contract-gate.js           # PreToolUse: API 계약 준수 검증
│   │   ├── security-scan.js           # PostToolUse: 보안 취약점 스캔
│   │   └── task-sync.js               # Stop: TASKS.md 상태 업데이트
│   ├── agents/                        # project-team 에이전트 (7개)
│   ├── settings.json                  # Claude Code hooks 등록
│   ├── routing.config.yaml            # 6개 모델 역할별 라우팅
│   └── council.config.yaml            # 멀티 AI 리뷰 설정
│
├── config/
│   ├── ccproxy.yaml                   # LiteLLM Proxy 설정 (6개 모델)
│   ├── agent-model-map.yaml           # 53개 OMC 에이전트 → 모델 매핑
│   ├── litellm_callback.py            # symlink → tools/litellm_callback.py
│   └── litellm-fallback.yaml          # Tailscale 미연결 시 fallback 설정
│
├── scripts/
│   ├── maestro.sh                     # GLM-5 (ZAI) 모드 런처
│   ├── ccproxy-start.sh               # LiteLLM Proxy 시작/종료/상태
│   ├── qwen35-cli.sh                  # nexus wrapper (Qwen3.5-122B, port 8080)
│   ├── qwen-coder-cli.sh              # cognit wrapper (Qwen3-Coder-30B, port 8000)
│   ├── health-check.sh                # 전체 서버 상태 점검
│   └── security-scan.sh               # 시크릿/취약점 스캔
│
├── tools/
│   ├── litellm_callback.py            # LiteLLM CustomLogger (AgentRouter)
│   ├── __init__.py                    # Python 패키지 초기화
│   └── observability/                 # 관찰성 대시보드 (port 3456)
│
├── logs/
│   └── ccproxy/
│       ├── proxy.log                  # LiteLLM Proxy 로그
│       ├── proxy.pid                  # Proxy PID 파일
│       └── .agent-model-hint          # 에이전트 모델 힌트 (TTL 30초)
│
├── docs/
│   ├── MANUAL.md                      # 운영 매뉴얼
│   ├── 계획서/                        # 구현 계획서
│   └── 리포트/                        # 구현 보고서
│
├── .env                               # API 키 및 서버 설정 (Git 추적 안함)
├── .env.example                       # 환경 변수 템플릿
├── CLAUDE.md                          # Claude Code 지침
└── README.md                          # 이 파일
```

---

## 7. 🔀 라우팅 설정

### 에이전트별 모델 매핑 (`config/agent-model-map.yaml`)

Phase 5 CCR 패턴: SubagentStart hook이 에이전트 이름을 파싱하여 최적 모델로 라우팅합니다.

```yaml
# 아키텍처/보안 티어 → Claude (최고 정밀도)
architect: "claude-sonnet-4-6"
critic: "claude-sonnet-4-6"
security-specialist: "claude-sonnet-4-6"

# 코드 작업 티어 → Codex (gpt-4o)
executor: "gpt-5.4-medium"
code-reviewer: "gpt-5.4-medium"
backend-specialist: "gpt-5.4-medium"

# 디자인 티어 → Gemini
designer: "gemini-3.1-pro"
vision: "gemini-3.1-pro"
frontend-specialist: "gemini-3.1-pro"

# 장문 분석 티어 → Qwen3.5-122B (400K ctx)
analyst: "qwen3.5-122b"
scientist: "qwen3.5-122b"
explore-high: "qwen3.5-122b"

# 경량 코드 티어 → Qwen3-Coder-30B (무료)
executor-low: "qwen3-coder-30b"
build-fixer: "qwen3-coder-30b"
tdd-guide-low: "qwen3-coder-30b"

# 기본 티어 → GLM-5 (대다수, ~55%)
explore: "glm-5"
researcher: "glm-5"
writer: "glm-5"
git-master: "glm-5"
```

### 역할 기반 라우팅 (`.claude/routing.config.yaml`)

| 역할 | 라우팅 대상 | 이유 |
|------|------------|------|
| `architect`, `project-manager` | Claude 구독 | 시스템 설계는 최고 수준 추론 필요 |
| `backend-specialist`, `test-specialist` | codex | 코드 생성 특화 모델 |
| `frontend-specialist`, `chief-designer` | gemini | 멀티모달, UI 강점 |
| `security-specialist` | Claude 구독 | 보안 판단은 신뢰도 우선 |
| `documenter`, `writer` | GLM-5 | 문서 작성은 저비용으로 충분 |
| `reasoner`, `analyst` | Qwen3.5-122B | 400K context, 장문 추론 |

---

## 8. 🖥️ 주요 명령어

### LiteLLM Proxy 관리

```bash
cd ~/.claude/maestro

# 시작 (Tailscale 연결 감지 → ccproxy.yaml 또는 litellm-fallback.yaml 자동 선택)
./scripts/ccproxy-start.sh start

# 상태 확인 (Tailscale + nexus/cognit 응답 여부 표시)
./scripts/ccproxy-start.sh status

# 종료
./scripts/ccproxy-start.sh stop

# 재시작
./scripts/ccproxy-start.sh restart
```

### GLM-5 모드 (ZAI Coding Plan)

```bash
# maestro.sh로 claude-glm 실행
cd ~/.claude/maestro
./scripts/maestro.sh

# 또는 alias 직접 사용
claude-glm

# 상태 확인
./scripts/maestro.sh status
```

### 서버 상태 점검

```bash
cd ~/.claude/maestro

# 전체 서버 상태
./scripts/health-check.sh

# Tailscale + nexus/cognit ping 테스트
tailscale ping 100.124.117.46   # nexus
tailscale ping 100.121.138.74   # cognit

# nexus 직접 API 테스트
curl -s http://100.124.117.46:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "Qwen3.5-122B-Q3_K_XL", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 10}'
```

### 멀티 AI 오케스트레이션 (Claude Code 세션 내)

```bash
# 역할별 최적 CLI에 태스크 위임
/multi-ai-run

# 멀티 AI 코드 리뷰 (council)
/multi-ai-review

# 대규모 태스크 오케스트레이션
/orchestrate-standalone --mode=standard
```

### 보안 스캔

```bash
cd ~/.claude/maestro

# 전체 스캔
./scripts/security-scan.sh

# 빠른 시크릿 검사
./scripts/security-scan.sh --quick
```

---

## 9. 🔧 Hook 프로파일

### 활성 Hooks (`settings.json`)

| 이벤트 | Hook | 동작 |
|--------|------|------|
| SubagentStart | `subagent-router.py` | 에이전트명 → 모델 힌트 기록 (Phase 5 CCR) |
| PreToolUse (Write/Edit) | `contract-gate.js` | API 계약 준수 검증 |
| PostToolUse (Write/Edit) | `security-scan.js` | 보안 취약점 스캔 |
| Stop | `task-sync.js` | TASKS.md 상태 업데이트 |

### Hook 프로파일

| 프로파일 | Hooks | 용도 |
|----------|-------|------|
| lite | 2개 | 핫픽스, 단순 변경 |
| standard | 4개 | 일반 개발 (기본값) |
| full | 16개 | 대규모 기능, 배포 전 |

프로파일 설정: `.claude/hooks/hook-profiles.yaml`

---

## 10. 🖧 서버 관리

### nexus (Qwen3.5-122B)

```bash
# Tailscale IP: 100.124.117.46
# 포트: 8080 (llama-server)
# 모델: Qwen3.5-122B-Q3_K_XL
# VRAM: RTX 3090 x3 (72GB)
# Context: 400K tokens

# SSH 접속
ssh hwandam@100.124.117.46

# 서비스 상태
ssh hwandam@100.124.117.46 "systemctl status llama-server"

# UFW 방화벽 (Tailscale 허용)
# sudo ufw allow from 100.0.0.0/8 to any port 8080
```

### cognit (Qwen3-Coder-30B)

```bash
# Tailscale IP: 100.121.138.74
# 포트: 8000 (vLLM)
# 모델: qwen3-coder (Qwen3-Coder-30B-A3B-Instruct AWQ-4bit)
# VRAM: RTX 3080 Ti x2 (24GB, 각 11.4GB 사용)
# Context: 16K tokens

# SSH 접속
ssh hwandam@100.121.138.74

# 서비스 상태
ssh hwandam@100.121.138.74 "systemctl status vllm-qwen3-coder"

# 가용 모델 목록
curl -s http://100.121.138.74:8000/v1/models | jq '.data[].id'
```

### Tailscale VPN 요구사항

nexus, cognit 서버 접근에는 Tailscale VPN 연결이 필수입니다.

```bash
tailscale up            # VPN 연결
tailscale status        # 연결 상태 확인
tailscale ping 100.124.117.46  # nexus 응답 테스트
tailscale ping 100.121.138.74  # cognit 응답 테스트
```

Tailscale 미연결 시: `scripts/ccproxy-start.sh`가 자동으로 `config/litellm-fallback.yaml`로 전환합니다.

---

## 11. 📚 참고 자료

| 문서 | 위치 |
|------|------|
| 운영 매뉴얼 (상세) | `docs/MANUAL.md` |
| GitHub 적용 계획서 | `docs/계획서/GitHub-프로젝트-적용-계획서.md` |
| Phase 5 CCR 구현 보고서 | `docs/리포트/Phase5-ccr-구현보고서.md` |
| LiteLLM 설정 | `config/ccproxy.yaml` |
| 에이전트 모델 매핑 | `config/agent-model-map.yaml` |
| ZAI 공식 문서 | https://docs.z.ai/devpack/tool/claude |

---

## 라이선스

MIT License — 자세한 내용은 [LICENSE](LICENSE) 파일 참조

---

*최종 업데이트: 2026-03-09 | Phase 5 (CCR 패턴) 완료*
