# Phase 5 - CCR 패턴 (OMC 에이전트별 모델 매핑) 구현 보고서

**날짜**: 2026-03-09
**Phase**: 5 - Agent-Model Mapping (CCR 패턴 차용)

---

## 구현 내용

### 생성된 파일

| 파일 | 설명 |
|------|------|
| `config/agent-model-map.yaml` | 53개 OMC 에이전트 → 최적 모델 매핑 테이블 |
| `tools/litellm_callback.py` | LiteLLM CustomLogger - 힌트 파일 읽어 모델 동적 오버라이드 |

### 수정된 파일

| 파일 | 변경 내용 |
|------|----------|
| `.claude/hooks/subagent-router.py` | SubagentStart hook - YAML 파싱 + 힌트 파일 기록. PROJECT_DIR 경로 버그 수정 |
| `.claude/settings.json` | SubagentStart 이벤트에 subagent-router.py hook 등록 |
| `config/ccproxy.yaml` | `litellm_settings.callbacks`에 AgentRouter 등록 |

---

## 아키텍처

```
SubagentStart 이벤트
  └─> .claude/hooks/subagent-router.py
        ├─> config/agent-model-map.yaml 조회 (53개 에이전트)
        ├─> logs/ccproxy/.agent-model-hint 기록
        └─> http://localhost:3456/event 관찰성 이벤트 전송

LiteLLM Proxy 요청 수신
  └─> tools/litellm_callback.py (AgentRouter.async_pre_call_hook)
        ├─> .agent-model-hint 파일 읽기 (TTL 30초, one-shot)
        └─> request.model 동적 오버라이드
```

---

## 에이전트-모델 매핑 설계

| 티어 | 모델 | 에이전트 예시 | 근거 |
|------|------|-------------|------|
| 아키텍처/보안 | `claude-sonnet-4-6` | architect, critic, security-specialist | 최고 정밀도 필요 |
| 코드 작업 | `gpt-5.4-medium` | executor, code-reviewer, backend-specialist | Codex 구독 활용 |
| 디자인/멀티모달 | `gemini-3.1-pro` | designer, vision, frontend-specialist | Gemini 멀티모달 강점 |
| 장문 분석 | `qwen3.5-122b` | analyst, scientist, explore-high | 400K ctx, 무료 서버 |
| 경량 코드 | `qwen3-coder-30b` | executor-low, build-fixer, tdd-guide-low | 무료 서버, 경량 |
| 기본 (대다수) | `glm-5` | explore, researcher, writer, git-master | $3/월 고정 |

**총 53개 에이전트** 6개 티어(opus/sonnet/haiku/specialist/ultra-thin/governance)로 분류

---

## 버그 수정: PROJECT_DIR 경로 오류

### 문제
```python
# 수정 전 (오류)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
# 결과: PROJECT_DIR = /project/.claude/  ← 잘못됨
# config/agent-model-map.yaml 탐색: /project/.claude/config/ ← 존재하지 않음
```

### 해결
```python
# 수정 후 (정상)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
# 결과: PROJECT_DIR = /project/  ← 정상 (hooks → .claude → project root)
# config/agent-model-map.yaml 탐색: /project/config/ ← 정상
```

---

## 검증 결과

### 1단계: 에이전트 → 힌트 파일 라우팅 (6개 전부 PASS)

| 에이전트 | 기대 모델 | 실제 결과 |
|---------|----------|----------|
| `executor` | `gpt-5.4-medium` | ✅ PASS |
| `designer` | `gemini-3.1-pro` | ✅ PASS |
| `security-specialist` | `claude-sonnet-4-6` | ✅ PASS |
| `architect` | `claude-sonnet-4-6` | ✅ PASS |
| `executor-low` | `qwen3-coder-30b` | ✅ PASS |
| `explore` | `glm-5` | ✅ PASS |

### 2단계: Mac → LiteLLM Proxy → 실제 추론 테스트

| 모델 | 경로 | 응답시간 | 결과 |
|------|------|---------|------|
| `qwen3.5-122b` | nexus Tailscale(100.124.117.46:8080) | 0.8s | ✅ 정상 |
| `qwen3-coder-30b` | cognit Tailscale(100.121.138.74:8000) | 1.1s | ✅ 정상 |
| `glm-5` | ZAI api.z.ai | - | ❌ CLI 전용 |

### GLM-5 제약사항
ZAI Coding Plan은 Claude CLI(`claude-glm`) 전용 구독으로 LiteLLM Proxy 직접 API 호출 불가.
glm-5 에이전트 요청은 `maestro.sh`(claude-glm) 경로 사용. Proxy에서는 `qwen3.5-122b`로 fallback.

---

## 추가 버그 수정 (통합 테스트 중 발견)

| 문제 | 수정 내용 |
|------|---------|
| nexus Tailscale IP 오류 | `100.64.189.120` → `100.124.117.46` (실제 nexus IP) |
| cognit 모델명 오류 | `Qwen3-Coder-30B-A3B-Instruct` → `qwen3-coder` (vLLM 실제 model_id) |
| nexus 방화벽 차단 | UFW rule 추가: `sudo ufw allow from 100.0.0.0/8 to any port 8080` |
| LiteLLM 인증 오류 | `master_key: "sk-maestro"` + `allow_requests_on_db_fail: true` 추가 |
| LiteLLM DB 오류 | `master_key` + `allow_requests_on_db_fail: true` 조합으로 DB 없이 운용 |
| callback import 오류 | `config/litellm_callback.py` symlink 생성 (`../tools/litellm_callback.py`) |

## 파일명 변경

`tools/litellm-callback.py` → `tools/litellm_callback.py`
- Python import 시 하이픈(`-`)은 모듈명으로 사용 불가
- LiteLLM `callbacks: ["tools.litellm_callback.AgentRouter"]` 등록을 위해 언더스코어로 변경

---

## 비용 최적화 효과 (예상)

| 모델 | 예상 요청 비율 | 비용 |
|------|-------------|------|
| glm-5 | ~55% | $3/월 고정 |
| gpt-5.4-medium | ~25% | Codex 구독 포함 |
| qwen3-coder-30b | ~12% | 무료 (자체 서버) |
| qwen3.5-122b | ~5% | 무료 (자체 서버) |
| gemini-3.1-pro | ~2% | 무료 티어 |
| claude-sonnet-4-6 | ~1% | Claude 구독 포함 |

---

## 실행 방법

```bash
# 1. LiteLLM Proxy 시작 (ccproxy.yaml에 AgentRouter 등록됨)
./scripts/ccproxy-start.sh start

# 2. Claude Code에서 에이전트 사용 시 자동 라우팅
# SubagentStart 이벤트 → subagent-router.py → 힌트 파일
# LiteLLM → litellm_callback.py → 모델 오버라이드

# 3. 힌트 파일 수동 확인
cat logs/ccproxy/.agent-model-hint

# 4. 라우팅 테스트
echo '{"agent_name": "executor"}' | python3 .claude/hooks/subagent-router.py
```

---

## 참고사항

- 힌트 파일 TTL: 30초 (one-shot, 읽은 후 즉시 삭제)
- 매핑 없는 에이전트: 기본 GLM-5 사용 (관찰성 이벤트는 전송)
- 대시보드 미실행 시: 이벤트 전송 실패 무시 (exit 0 보장)
- LiteLLM Proxy 미실행 시: 힌트 파일만 기록, 정상 종료

---

## 트러블슈팅: claude-glm 401 Authentication Failed (2026-03-09 이후 발견)

### 증상
`claude-glm` 실행 시 ZAI API에서 401 Authentication Failed 반환.

### 근본 원인
`.env`의 `ZAI_API_KEY`가 만료/비활성 키(`bd9a6c6ef3de4387ab184f42e4a38b83.YCIIcqZz8N06nPxY`)로 설정되어 있었음.
올바른 키는 `GLM_CODING_PLAN_API_KEY`(`2ff9940f...` 형태).

### 추가 원인: ANTHROPIC_API_KEY 충돌
셸 환경에 Anthropic 구독 키(`sk-ant-...`)가 `ANTHROPIC_API_KEY`로 남아있으면 ZAI API 인증 실패.
`maestro.sh`의 `run_direct()` 함수에서 `unset ANTHROPIC_API_KEY`로 처리됨.

### 진단 명령
```bash
# 현재 ZAI_API_KEY로 직접 인증 테스트
curl -s https://api.z.ai/api/anthropic/v1/messages \
  -H "Authorization: Bearer $ZAI_API_KEY" \
  -H "Content-Type: application/json" \
  -H "anthropic-version: 2023-06-01" \
  -d '{"model":"claude-sonnet-4-6","max_tokens":10,"messages":[{"role":"user","content":"hi"}]}'
# 200 → 키 정상, 401 → 키 만료/오류
```

### 해결 절차
1. ZAI 콘솔에서 현재 활성 API 키 확인
2. `.env`의 `ZAI_API_KEY` 값을 활성 키로 교체
3. `maestro.sh`에서 `unset ANTHROPIC_API_KEY` 처리 확인
