# Maestro Claude Code 운영 매뉴얼

> 최종 업데이트: 2026-03-09
> 대상 독자: Maestro Claude Code 운영자

---

## 목차

1. [설치 및 초기 설정](#1-설치-및-초기-설정)
2. [기본 사용법](#2-기본-사용법)
3. [LiteLLM Proxy 운용](#3-litellm-proxy-운용)
4. [멀티 AI 오케스트레이션](#4-멀티-ai-오케스트레이션)
5. [Phase 5 CCR 패턴 (에이전트 모델 라우팅)](#5-phase-5-ccr-패턴-에이전트-모델-라우팅)
6. [Project-Team 에이전트](#6-project-team-에이전트)
7. [Hook 시스템](#7-hook-시스템)
8. [서버 관리](#8-서버-관리)
9. [보안](#9-보안)
10. [Context 관리 (Compact 정책)](#10-context-관리-compact-정책)
11. [트러블슈팅](#11-트러블슈팅)
12. [참고 문서](#12-참고-문서)

---

## 1. 설치 및 초기 설정

### 1.1 사전 요구사항

**필수 도구**

| 도구 | 설치 확인 | 역할 |
|------|-----------|------|
| Claude Code (Anthropic 구독) | `claude --version` | 기본 오케스트레이터 |
| Python 3.10+ | `python3 --version` | Hook 스크립트 실행 환경 |
| Node.js v18+ | `node --version` | JS Hook 실행 환경 |
| LiteLLM 1.82+ | `litellm --version` | 모델 프록시 |
| jq | `jq --version` | JSON 파싱 (wrapper 스크립트) |
| curl | `curl --version` | API 호출 |

**선택 도구**

| 도구 | 설치 명령 | 역할 |
|------|-----------|------|
| Codex CLI | `npm install -g @openai/codex` | 코드 생성/리뷰/테스트 |
| Gemini CLI | `npm install -g @google/gemini-cli` | 디자인/UI/멀티모달 |
| Tailscale | [tailscale.com](https://tailscale.com) | nexus/cognit 서버 접근용 VPN |

**VPN 연결 확인 (자체 서버 사용 시)**

```bash
tailscale status
tailscale ping 100.124.117.46  # nexus (Qwen3.5-122B)
tailscale ping 100.121.138.74  # cognit (Qwen3-Coder-30B)
```

### 1.2 ~/.claude/maestro 심볼릭 링크 설정

프로젝트에 `~/.claude/maestro` 경로로 전역 접근할 수 있도록 심볼릭 링크를 생성합니다.

```bash
# 프로젝트 루트에서 실행
cd /path/to/maestro-claude-code

# ~/.claude/maestro 심볼릭 링크 생성
ln -sf "$(pwd)" ~/.claude/maestro

# 확인
ls ~/.claude/maestro
# → 프로젝트 파일 목록이 표시되면 정상

# 이후 어디서든 접근 가능
cd ~/.claude/maestro
./scripts/ccproxy-start.sh start
```

### 1.3 환경 변수 설정

```bash
cd ~/.claude/maestro
cp .env.example .env
```

**환경 변수 목록**

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| `ZAI_API_KEY` | ZAI Coding Plan API 키 (GLM-5 모드) | 필수 |
| `ANTHROPIC_API_KEY` | Anthropic API 키 (claude 모드) | 필수 |
| `OPENAI_API_KEY` | OpenAI API 키 (Codex/gpt-4o) | 선택 |
| `GOOGLE_API_KEY` | Google API 키 (Gemini) | 선택 |
| `NEXUS_HOST` | nexus Tailscale IP | `100.124.117.46` |
| `NEXUS_PORT` | nexus llama-server 포트 | `8080` |
| `COGNIT_HOST` | cognit Tailscale IP | `100.121.138.74` |
| `COGNIT_PORT` | cognit vLLM 포트 | `8000` |
| `CCPROXY_PORT` | LiteLLM Proxy 포트 | `4000` |
| `TAVILY_API_KEY` | Tavily 웹 검색 키 | 선택 |

**ZAI API 주의사항**

ZAI API는 일반 Anthropic 환경 변수와 다릅니다.

```bash
# 올바른 설정 (maestro.sh가 자동 처리)
ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic
ANTHROPIC_AUTH_TOKEN=${ZAI_API_KEY}  # ANTHROPIC_API_KEY가 아님!
```

### 1.4 claude-glm 명령어 등록

```bash
mkdir -p ~/.local/bin
ln -sf "$(pwd)/scripts/maestro.sh" ~/.local/bin/claude-glm

# PATH에 ~/.local/bin 추가 (없는 경우)
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# 확인
which claude-glm
claude-glm status
```

### 1.5 LiteLLM 설치

```bash
pip install litellm

# 버전 확인
litellm --version
```

### 1.6 스크립트 실행 권한 부여

```bash
cd ~/.claude/maestro
chmod +x scripts/*.sh
```

---

## 2. 기본 사용법

### 2.1 실행 모드 선택

| 모드 | 명령어 | 비용 | 용도 |
|------|--------|------|------|
| 기본 Claude | `claude` | $20/월 구독 | 아키텍처, 복잡한 분석 |
| GLM-5 저비용 | `claude-glm` 또는 `./scripts/maestro.sh` | $3/월 고정 | 일상 코드, 문서 |
| LiteLLM Proxy | 자동 (Proxy 경유) | 자동 라우팅 | Phase 5 에이전트별 최적화 |

```bash
# 기본 Claude Code 오케스트레이터
claude

# GLM-5 저비용 모드
claude-glm
# 또는
./scripts/maestro.sh

# 현재 설정 확인
./scripts/maestro.sh status
```

### 2.2 Wrapper 스크립트 직접 사용

**Qwen3.5-122B (nexus) — 고급 추론, 400K context**

```bash
# 직접 질문
./scripts/qwen35-cli.sh "복잡한 아키텍처 분석 요청"

# stdin 파이프
echo "이 코드의 성능 병목을 분석해줘" | ./scripts/qwen35-cli.sh

# 시스템 프롬프트 지정
./scripts/qwen35-cli.sh -s "시니어 백엔드 엔지니어로서" \
    "이 API 설계의 문제점을 찾아줘"

# 대용량 파일 분석 (400K ctx 활용)
cat src/complex-module.ts | ./scripts/qwen35-cli.sh "이 코드를 리뷰해줘"
```

**Qwen3-Coder-30B (cognit) — 코드 생성, 20K context**

```bash
# 코드 생성
./scripts/qwen-coder-cli.sh "Python FastAPI로 사용자 CRUD API 작성해줘"

# stdin 파이프
echo "이 함수를 리팩토링해줘" | ./scripts/qwen-coder-cli.sh
```

> cognit는 context **20K tokens 제한**. 대용량 파일 → nexus 사용.

### 2.3 멀티 AI 명령어 (Claude Code 세션 내)

```bash
# 역할별 최적 CLI에 태스크 위임
/multi-ai-run "사용자 인증 모듈 구현"

# 멀티 AI 코드 리뷰 (council 방식)
/multi-ai-review src/auth/

# 대규모 태스크 오케스트레이션 (wave/sprint)
/orchestrate-standalone wave "결제 시스템 전체 구현"
```

---

## 3. LiteLLM Proxy 운용

### 3.1 개요

LiteLLM Proxy(port 4000)는 6개 모델을 단일 OpenAI 호환 엔드포인트로 통합합니다.

- **인증**: `Bearer sk-maestro` (로컬 고정 키)
- **설정 파일**: `config/ccproxy.yaml`
- **Fallback 설정**: `config/litellm-fallback.yaml` (Tailscale 미연결 시)

### 3.2 시작 / 종료 / 상태

```bash
cd ~/.claude/maestro

# 시작 (Tailscale 연결 감지 → 설정 파일 자동 선택)
./scripts/ccproxy-start.sh start

# 상태 확인 (Tailscale + nexus/cognit 응답 여부 표시)
./scripts/ccproxy-start.sh status

# 종료
./scripts/ccproxy-start.sh stop

# 재시작
./scripts/ccproxy-start.sh restart
```

**상태 출력 예시**
```
================================
  ccproxy (LiteLLM Proxy) 상태
================================

  상태:   실행 중 (PID: 12345)
  포트:   4000
  로그:   logs/ccproxy/proxy.log

  Tailscale: 연결됨
  nexus:     ✅ 응답 (100.124.117.46:8080)
  cognit:    ✅ 응답 (100.121.138.74:8000)
```

### 3.3 모델별 테스트

```bash
# nexus (Qwen3.5-122B) 테스트
curl -s http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-maestro" \
  -d '{"model": "qwen3.5-122b", "messages": [{"role": "user", "content": "1+1=?"}], "max_tokens": 20}' \
  | jq '.choices[0].message.content'

# cognit (Qwen3-Coder-30B) 테스트
curl -s http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-maestro" \
  -d '{"model": "qwen3-coder-30b", "messages": [{"role": "user", "content": "Hello"}], "max_tokens": 20}' \
  | jq '.choices[0].message.content'

# Gemini 테스트
curl -s http://localhost:4000/v1/chat/completions \
  -H "Authorization: Bearer sk-maestro" \
  -d '{"model": "gemini-3.1-pro", "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 20}' \
  | jq '.choices[0].message.content'
```

### 3.4 Proxy 로그 확인

```bash
# 실시간 로그
tail -f ~/.claude/maestro/logs/ccproxy/proxy.log

# 최근 100줄
tail -100 ~/.claude/maestro/logs/ccproxy/proxy.log

# 에러만 필터링
grep -i error ~/.claude/maestro/logs/ccproxy/proxy.log | tail -20
```

### 3.5 Tailscale 미연결 시 (Fallback)

Tailscale이 연결되지 않거나 nexus/cognit에 접근 불가 시, `ccproxy-start.sh`가 자동으로 `config/litellm-fallback.yaml`을 사용합니다.

- Fallback 모드에서는 qwen3.5-122b / qwen3-coder-30b 요청 → glm-5 (ZAI) 또는 대체 모델로 라우팅됩니다.

---

## 4. 멀티 AI 오케스트레이션

### 4.1 2계층 라우팅 구조

| 계층 | 시스템 | 라우팅 대상 | 설정 |
|------|--------|------------|------|
| 에이전트 내부 | OMC + LiteLLM Proxy | 53개 OMC subagent → 6개 모델 | `config/agent-model-map.yaml` |
| 태스크 위임 | claude-imple-skills | 역할별 외부 CLI | `.claude/routing.config.yaml` |

두 계층은 **독립적**으로 동작하며 서로 간섭하지 않습니다.

### 4.2 routing.config.yaml 역할별 라우팅

```yaml
role_routing:
  # Claude 구독 전용
  architect: claude
  project-manager: claude
  security-specialist: claude

  # Codex 전용
  backend-specialist: codex
  test-specialist: codex
  api-designer: codex

  # Gemini 전용
  frontend-specialist: gemini
  chief-designer: gemini

task_type_routing:
  boilerplate: qwen-coder     # CRUD 모델, DTO
  complex_logic: claude        # 비즈니스 로직
  ui_component: gemini         # React, CSS
  documentation: claude-glm    # README, JSDoc
  long_context: qwen35         # 대용량 파일 분석
```

### 4.3 Wrapper CLI 경유 흐름

```
claude-imple-skills multi-ai-run
  └─► routing.config.yaml 조회
        ├─► codex exec  → OpenAI Codex API
        ├─► gemini      → Google Gemini API
        ├─► qwen35-cli.sh  → nexus:8080 (Tailscale)
        ├─► qwen-coder-cli.sh → cognit:8000 (Tailscale)
        └─► claude-glm  → ZAI API (GLM-5)
```

---

## 5. Phase 5 CCR 패턴 (에이전트 모델 라우팅)

OMC 에이전트(subagent)가 실행될 때 최적 모델로 자동 라우팅하는 시스템입니다.

### 5.1 동작 원리

```
Claude Code가 SubagentStart 이벤트 발생
  └─► .claude/hooks/subagent-router.py 실행
        ├─► config/agent-model-map.yaml에서 에이전트명 → 모델 조회
        ├─► logs/ccproxy/.agent-model-hint 파일에 기록 (TTL 30초, one-shot)
        └─► http://localhost:3456/event 관찰성 이벤트 전송 (선택)

LiteLLM Proxy가 다음 요청 수신
  └─► tools/litellm_callback.py (AgentRouter.async_pre_call_hook)
        ├─► .agent-model-hint 파일 읽기 (읽으면 즉시 삭제)
        └─► 요청 모델을 힌트 모델로 동적 오버라이드
```

### 5.2 에이전트 → 모델 매핑 티어

| 티어 | 모델 | 에이전트 예시 | 요청 비율 |
|------|------|-------------|---------|
| 아키텍처/보안 | `claude-sonnet-4-6` | architect, critic, security-specialist | ~1% |
| 코드 작업 | `gpt-5.4-medium` (gpt-4o) | executor, code-reviewer, backend-specialist | ~25% |
| 디자인/멀티모달 | `gemini-3.1-pro` | designer, vision, frontend-specialist | ~2% |
| 장문 분석 | `qwen3.5-122b` | analyst, scientist, explore-high | ~5% |
| 경량 코드 | `qwen3-coder-30b` | executor-low, build-fixer, tdd-guide-low | ~12% |
| 기본 | `glm-5` (fallback: qwen3.5-122b) | explore, researcher, writer, git-master | ~55% |

### 5.3 수동 테스트

```bash
cd ~/.claude/maestro

# 에이전트 라우팅 테스트 (힌트 파일 생성 확인)
echo '{"agent_name": "executor"}' | python3 .claude/hooks/subagent-router.py
cat logs/ccproxy/.agent-model-hint
# 출력: {"agent": "executor", "model": "gpt-5.4-medium"}

# 여러 에이전트 테스트
for agent in executor designer security-specialist architect executor-low explore; do
  result=$(echo "{\"agent_name\": \"$agent\"}" | python3 .claude/hooks/subagent-router.py 2>/dev/null)
  hint=$(cat logs/ccproxy/.agent-model-hint 2>/dev/null || echo "no hint")
  echo "$agent → $(echo $hint | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d.get(\"model\",\"?\"))' 2>/dev/null)"
  sleep 0.1
done
```

### 5.4 GLM-5 제약사항

```
⚠️  ZAI Coding Plan은 Claude CLI 전용 구독입니다.
    LiteLLM Proxy에서 GLM-5로 직접 API 호출 시 인증 실패.

    해결 방법:
    - GLM-5 사용: ./scripts/maestro.sh 또는 claude-glm 명령 사용
    - Proxy에서 glm-5 요청 시: qwen3.5-122b로 자동 fallback 처리됨
```

### 5.5 관련 파일

| 파일 | 역할 |
|------|------|
| `.claude/hooks/subagent-router.py` | SubagentStart hook, 에이전트→모델 매핑 |
| `config/agent-model-map.yaml` | 53개 에이전트 → 6개 모델 매핑 테이블 |
| `tools/litellm_callback.py` | LiteLLM CustomLogger, 힌트 파일 읽어 모델 오버라이드 |
| `config/litellm_callback.py` | symlink → tools/litellm_callback.py |
| `logs/ccproxy/.agent-model-hint` | 에이전트 모델 힌트 (TTL 30초, one-shot) |

---

## 6. Project-Team 에이전트

### 6.1 에이전트 목록 (7개, standard 모드)

| 에이전트 | 파일 | 역할 |
|----------|------|------|
| ChiefArchitect | `.claude/agents/chief-architect.md` | 아키텍처 설계, 기술 결정 |
| ProjectManager | `.claude/agents/project-manager.md` | 프로젝트 관리, 일정 조율 |
| BackendSpecialist | `.claude/agents/backend-specialist.md` | 백엔드 구현, API 설계 |
| FrontendSpecialist | `.claude/agents/frontend-specialist.md` | 프론트엔드 구현, UI |
| ChiefDesigner | `.claude/agents/chief-designer.md` | UI/UX 디자인 시스템 |
| SecuritySpecialist | `.claude/agents/security-specialist.md` | 보안 검사, 취약점 분석 |
| QAManager | `.claude/agents/qa-manager.md` | 품질 관리, 테스트 전략 |

### 6.2 에이전트 실행 방법

```bash
# claude-imple-skills orchestrate-standalone으로 일괄 실행
/orchestrate-standalone standard "새 기능 구현"

# 개별 에이전트 직접 호출
Task(subagent_type="chief-architect", prompt="...")
Task(subagent_type="backend-specialist", prompt="...")
```

---

## 7. Hook 시스템

### 7.1 활성 Hooks (`settings.json`)

| 이벤트 | Hook 파일 | 동작 |
|--------|-----------|------|
| SubagentStart | `subagent-router.py` | 에이전트 → 모델 힌트 기록 (Phase 5 CCR) |
| PreToolUse (Write/Edit) | `contract-gate.js` | API 계약 준수 검증 |
| PostToolUse (Write/Edit) | `security-scan.js` | 보안 취약점 스캔 |
| Stop | `task-sync.js` | TASKS.md 상태 업데이트 |

### 7.2 Hook 프로파일

| 프로파일 | Hooks 수 | 사용 시점 |
|----------|----------|---------|
| `lite` | 2개 | 핫픽스, 단순 변경 |
| `standard` | 4개 | 일반 개발 (기본값) |
| `full` | 16개 | 대규모 기능, 배포 전 |

프로파일 설정: `.claude/hooks/hook-profiles.yaml`

### 7.3 Hook 동작 확인

```bash
# Hook 등록 상태 확인
cat .claude/settings.json | jq '.hooks'

# subagent-router.py 수동 실행 테스트
echo '{"agent_name": "architect"}' | python3 .claude/hooks/subagent-router.py
echo "exit code: $?"
cat logs/ccproxy/.agent-model-hint
```

---

## 8. 서버 관리

### 8.1 nexus (Qwen3.5-122B)

```
역할:     고급 추론, 장문 분석, 400K context
모델:     Qwen3.5-122B-Q3_K_XL (llama-server)
IP:       100.124.117.46 (Tailscale)
포트:     8080
하드웨어: RTX 3090 x3 (72GB VRAM)
```

```bash
# Tailscale ping 테스트
tailscale ping 100.124.117.46

# 서버 직접 API 테스트
curl -s http://100.124.117.46:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "Qwen3.5-122B-Q3_K_XL", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 10}' \
  | jq '.choices[0].message.content'

# SSH 접속
ssh hwandam@100.124.117.46

# 서비스 상태 확인
ssh hwandam@100.124.117.46 "systemctl status llama-server"

# 방화벽 규칙 확인 (Tailscale 허용)
ssh hwandam@100.124.117.46 "sudo ufw status | grep 8080"
# → 100.0.0.0/8 ALLOW 8080 (Tailscale 대역 허용됨)
```

### 8.2 cognit (Qwen3-Coder-30B)

```
역할:     경량 코드 생성, 보일러플레이트
모델:     Qwen3-Coder-30B-A3B-Instruct AWQ-4bit (vLLM)
실제 model_id: qwen3-coder
IP:       100.121.138.74 (Tailscale)
포트:     8000
하드웨어: RTX 3080 Ti x2 (각 11.4GB/12GB 사용)
context:  16K tokens (GPU 메모리 제한)
```

```bash
# Tailscale ping 테스트
tailscale ping 100.121.138.74

# 가용 모델 목록 확인
curl -s http://100.121.138.74:8000/v1/models | jq '.data[].id'
# 출력: "qwen3-coder"

# 직접 API 테스트
curl -s http://100.121.138.74:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "qwen3-coder", "messages": [{"role": "user", "content": "Hello"}], "max_tokens": 10}' \
  | jq '.choices[0].message.content'

# SSH 접속
ssh hwandam@100.121.138.74

# 서비스 상태 확인 (systemd 자동 시작 설정됨)
ssh hwandam@100.121.138.74 "systemctl status vllm-qwen3-coder"

# 서비스 재시작
ssh hwandam@100.121.138.74 "sudo systemctl restart vllm-qwen3-coder"
```

### 8.3 전체 상태 점검

```bash
cd ~/.claude/maestro

# ccproxy 상태 (Tailscale + nexus + cognit)
./scripts/ccproxy-start.sh status

# 전체 서버 헬스 체크
./scripts/health-check.sh

# Tailscale 연결 상태
tailscale status
```

---

## 9. 보안

### 9.1 보안 스캔

```bash
cd ~/.claude/maestro

# 전체 보안 스캔 (시크릿, 취약점)
./scripts/security-scan.sh

# 빠른 시크릿 검사만 (커밋 전 권장)
./scripts/security-scan.sh --quick
```

### 9.2 API 키 관리

- API 키는 `.env` 파일에만 저장 (`.gitignore`에 포함됨)
- LiteLLM Proxy 마스터 키: `sk-maestro` (로컬 전용, 외부 노출 금지)
- ZAI_API_KEY는 `ANTHROPIC_AUTH_TOKEN`으로만 사용

```bash
# .env 파일이 Git에 포함되었는지 확인
git check-ignore -v .env
# 출력: .gitignore:X:.env → 정상
```

### 9.3 서버 방화벽

nexus 서버 UFW 규칙 (Tailscale 대역 허용):
```bash
# nexus에서 실행됨
sudo ufw allow from 100.0.0.0/8 to any port 8080
# Tailscale IP 대역 → port 8080 허용
```

---

## 10. Context 관리 (Compact 정책)

### 10.1 Compact 트리거

| 조건 | 동작 |
|------|------|
| Context 80% 도달 | 자동 compact (SessionStart hook 통해) |
| `/compact` 명령 | 수동 compact |
| 세션 종료 전 | task-sync.js로 TASKS.md 동기화 |

### 10.2 Memory 지속성

세션 간 중요 정보는 MEMORY.md에 저장됩니다.

```bash
# MEMORY.md 위치
~/.claude/projects/-Users-hwandam-workspace-maestro-claude-code/memory/MEMORY.md

# 또는 프로젝트 내 위치
~/.claude/maestro/.claude/memory/MEMORY.md
```

---

## 11. 트러블슈팅

### LiteLLM Proxy 시작 실패

```bash
# 로그 확인
tail -50 ~/.claude/maestro/logs/ccproxy/proxy.log

# 포트 충돌 확인
lsof -ti:4000

# 강제 종료 후 재시작
./scripts/ccproxy-start.sh stop
./scripts/ccproxy-start.sh start
```

### nexus 연결 실패 (400 Bad Request)

```bash
# UFW 방화벽 규칙 확인
ssh hwandam@100.124.117.46 "sudo ufw status | grep 8080"

# 규칙 없으면 추가
ssh hwandam@100.124.117.46 "sudo ufw allow from 100.0.0.0/8 to any port 8080"

# Tailscale IP 확인
tailscale status | grep nexus
```

### cognit 모델 404 에러

```bash
# 실제 model_id 확인
curl -s http://100.121.138.74:8000/v1/models | jq '.data[].id'
# "qwen3-coder" (짧은 이름 사용)

# config/ccproxy.yaml에서 확인
grep "model:" ~/.claude/maestro/config/ccproxy.yaml | grep cognit
# model: "openai/qwen3-coder"  ← 정상
```

### GLM-5 인증 실패

```bash
# ZAI는 Claude CLI 전용 — LiteLLM Proxy로 직접 접근 불가
# 해결: maestro.sh 또는 claude-glm 사용

./scripts/maestro.sh
# 또는
claude-glm
```

### subagent-router.py 에이전트 매핑 실패

```bash
# 힌트 파일 생성 테스트
echo '{"agent_name": "executor"}' | python3 ~/.claude/maestro/.claude/hooks/subagent-router.py

# 힌트 파일 확인
cat ~/.claude/maestro/logs/ccproxy/.agent-model-hint

# agent-model-map.yaml 경로 확인
ls ~/.claude/maestro/config/agent-model-map.yaml

# PROJECT_DIR 디버깅
python3 -c "
import os
SCRIPT_DIR = os.path.dirname(os.path.abspath('$HOME/.claude/maestro/.claude/hooks/subagent-router.py'))
PROJECT_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
print('PROJECT_DIR:', PROJECT_DIR)
print('CONFIG_PATH:', os.path.join(PROJECT_DIR, 'config', 'agent-model-map.yaml'))
"
```

### PYTHONPATH unbound variable 오류

```bash
# ccproxy-start.sh의 PYTHONPATH 설정 확인
grep PYTHONPATH ~/.claude/maestro/scripts/ccproxy-start.sh
# export PYTHONPATH="${PROJECT_DIR}:${PYTHONPATH:-}"
# → ${PYTHONPATH:-} 형식이어야 함 (기본값 빈 문자열)
```

### LiteLLM DB 오류

```bash
# general_settings에 설정 확인
grep -A 3 "general_settings" ~/.claude/maestro/config/ccproxy.yaml
# master_key: "sk-maestro"
# allow_requests_on_db_fail: true  ← 이 줄이 있어야 함
```

---

## 12. 참고 문서

| 문서 | 위치 |
|------|------|
| README (프로젝트 개요) | `~/. claude/maestro/README.md` |
| GitHub 적용 계획서 | `docs/계획서/GitHub-프로젝트-적용-계획서.md` |
| Phase 5 CCR 구현 보고서 | `docs/리포트/Phase5-ccr-구현보고서.md` |
| LiteLLM Proxy 설정 | `config/ccproxy.yaml` |
| 에이전트 모델 매핑 | `config/agent-model-map.yaml` |
| ZAI 공식 문서 | https://docs.z.ai/devpack/tool/claude |
| LiteLLM 문서 | https://docs.litellm.ai |
| Tailscale 문서 | https://tailscale.com/docs |

---

*최종 업데이트: 2026-03-09 | Phase 5 (CCR 패턴) 완료*
