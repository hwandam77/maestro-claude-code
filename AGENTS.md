# AGENTS.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## 언어 원칙

- 사용자와의 대화 및 설명은 **한글**로 진행한다.
- 코드, 커밋 메시지, 변수명은 영어를 사용한다.

## 프로젝트 개요

**Maestro Claude Code**는 4개의 LLM 모델을 오케스트라처럼 협업시키는 하이브리드 에이전트 라우팅 시스템이다.

### 4-Model Orchestra

| 역할 | 모델 | 용도 | 사용률 |
|------|------|------|--------|
| 🎼 Maestro | Claude Opus 4.5 | 전략 수립, 아키텍처 설계, 품질 검증 | 10% |
| 🎻 Concertmaster | GLM-4.7 (Z.AI) | 핵심 코드 구현, 비즈니스 로직 | 35% |
| 🎹 Principal | GPT-5.2 Codex | 대규모 컨텍스트 처리 (60K+ tokens) | 5% |
| 🥁 Ensemble | Qwen3-Coder-30B (vLLM) | 반복 작업, 파일 조작, 배경 실행 | 50% |

## 명령어

### 환경 설정
```bash
# 환경 변수 설정
cp .env.example .env
# .env 파일에 API 키 입력 (ZAI_API_KEY, OPENAI_API_KEY, TAVILY_API_KEY, VLLM_ENDPOINT)

# Claude Code 인증 (Opus용 - API 키 대신 사용)
claude login
```

### 실행
```bash
# 라우터 + Claude Code 시작
./scripts/start.sh

# 또는 수동으로:
source .env
ccr start --config config/config.json &
eval "$(ccr activate)" && claude
```

### Docker 실행
```bash
# 빌드
docker-compose build

# 실행
docker-compose up -d
docker exec -it maestro-claude-code bash
```

### 테스트
```bash
# 환경 변수 로드 필수
source .env

# vLLM 연결 테스트
./tests/t4_vllm_connection.sh

# Phase 1 라우팅 검증
./tests/t5_phase1_verify.sh

# 폴백 시나리오 테스트
./tests/t10_fallback_test.sh
```

### 라우터 관리
```bash
ccr start --config config/config.json  # 시작
ccr stop                                # 중지
curl http://127.0.0.1:3456/health       # 헬스체크
```

## 아키텍처

### 라우팅 흐름

```
사용자 요청 → claude-code-router (port 3456)
                    ↓
            custom-router.js (에이전트 감지)
                    ↓
    ┌───────────────┼───────────────┐
    ↓               ↓               ↓
  opus          sonnet          haiku
(Anthropic)    (Z.AI)         (vLLM)
```

### 라우팅 우선순위 (custom-router.js)

1. **프롬프트 태그**: `provider,model` 태그가 있으면 해당 모델로 직행
2. **에이전트 매핑**: 시스템 프롬프트의 `subagent_type`으로 티어 결정
3. **config.json 기본 라우팅**: think/default/background/longContext 카테고리

### 에이전트-티어 매핑 (config/custom-router.js)

- **opus (16개)**: architect, planner, critic, analyst, designer, vision, writer 등
- **sonnet (20개)**: executor, researcher, git-master, frontend/backend-specialist 등
- **haiku (14개)**: executor-low, architect-low, researcher-low 등 `-low` 접미사 에이전트

### 폴백 체인

```
background(Qwen3) 장애 → GLM-4.7 대행
default(GLM-4.7) 장애 → Opus 폴백
longContext(GPT-5.2) 장애 → Opus 200K 대체
전체 Cloud API 장애 → Qwen3-Coder만 (제한 모드)
```

## 핵심 파일

| 파일 | 설명 |
|------|------|
| `config/config.json` | 라우터 설정 - 프로바이더, 모델, 라우팅 규칙 |
| `config/custom-router.js` | 에이전트→모델 매핑 로직, vLLM 헬스체크 |
| `scripts/start.sh` | 라우터 시작 스크립트 |
| `.env` | API 키 및 엔드포인트 (Git 추적 안함) |

## 제약 사항

### Qwen3-Coder 16K 토큰 제한
- **1T1F 원칙**: One Task, One File
- 500줄 이상 파일 처리 불가 → 자동 에스컬레이션
- 도구 호출 4회 초과 시 컨텍스트 오버플로우 위험

### GLM-4.7 동시성 제한
- `GLM_MAX_CONCURRENCY = 1` (순차 처리 강제)
- ultrawork 병렬 실행 시 haiku 에이전트 우선 사용

### 네트워크 의존성
- vLLM 서버 접근: VPN 필수 (VLLM_ENDPOINT)
- VPN 단절 시 자동으로 Cloud API 폴백
