# GitHub 오픈소스 적용 계획서

> 작성일: 2026-03-09
> 대상: Maestro Claude Code 6-Model Orchestra
> 목적: 검증된 오픈소스를 활용하여 라우팅 지능화, 관찰성, 운영 효율을 개선
> **진입점: `claude-glm` (ZAI $3/월 기반)**

---

## 목차

1. [핵심 전제](#핵심-전제-claude-glm-기반-실행)
2. [현재 아키텍처](#현재-아키텍처-요약)
3. [6개 모델 특성](#6개-모델-특성-매트릭스-비용-우선-정렬)
4. [Phase 1: ccproxy 지능형 라우팅](#phase-1-지능형-프록시-라우팅-ccproxy-적용)
5. [Phase 2: 관찰성 대시보드](#phase-2-멀티에이전트-관찰성-대시보드)
6. [Phase 3: 크로스 도구 동기화](#phase-3-크로스-도구-설정-동기화)
7. [Phase 4: 병렬 세션 관리](#phase-4-병렬-세션-관리-선택)
8. [Phase 5: CCR 패턴 차용](#phase-5-참조-아키텍처-벤치마크)
9. [전체 로드맵](#전체-로드맵)
10. [적용 제외 프로젝트](#적용하지-않는-프로젝트와-사유)

---

## 핵심 전제: `claude-glm` 기반 실행

Maestro는 `claude` (Anthropic 구독)가 아닌 **`claude-glm` (ZAI API, $3/월)**을 기본 진입점으로 사용한다.

```bash
# maestro.sh 실행 원리
ANTHROPIC_BASE_URL="https://api.z.ai/api/anthropic" \
ANTHROPIC_AUTH_TOKEN="${ZAI_API_KEY}" \
exec claude "$@"
```

Claude Code CLI는 ZAI API를 통해 GLM-5 모델과 통신하며, 이 GLM-5가 **기본 오케스트레이터**이다.
비싼 모델(Codex, Gemini, Claude 구독)은 **필요할 때만 에스컬레이션**한다.

### 설계 원칙

1. **비용 최소화 우선**: GLM-5($3/월) + 자체 서버(무료)로 90%+ 처리
2. **구독 모델 적극 활용**: Codex(gpt-5.4-medium) 구독이므로 코드 작업에 부담 없이 사용
3. **투명한 에스컬레이션**: 사용자가 모델을 의식하지 않고 자동 최적 라우팅
4. **안전한 fallback**: 모든 에스컬레이션 실패 시 GLM-5로 복귀

---

## 현재 아키텍처 요약

```
사용자 요청
  → claude-glm (ZAI API, GLM-5, $3/월 기본 오케스트레이터)
    → OMC 에이전트 (Claude Code 내부 subagent, GLM-5로 실행)
    → maestro-route.sh (쉘 기반 정적 라우팅, 외부 CLI 위임)
      → codex --yolo       : gpt-5.4-medium (코드 에스컬레이션)
      → gemini              : gemini-3.1-pro (디자인 에스컬레이션)
      → qwen35-cli.sh       : Qwen3.5-122B (장문 에스컬레이션)
      → qwen-coder-cli.sh   : Qwen3-Coder-30B (경량 코드, 무료)
    → hooks (quality gate)
```

### 비용 구조

| 모델 | 비용 | 역할 |
|------|------|------|
| **GLM-5** | $3/월 (구독) | 기본 — 대부분의 작업 처리 |
| **Qwen3.5-122B** | 무료 (자체 서버) | 장문 분석 보조 |
| **Qwen3-Coder-30B** | 무료 (자체 서버) | 경량 코드 생성 보조 |
| **Codex** | 구독제 | 고품질 코드 필요 시 (구독 내 활용) |
| **Gemini** | 무료/종량제 | 디자인/멀티모달 필요 시만 |
| **Claude 구독** | 구독료 | 최종 에스컬레이션 (거의 안 씀) |

### 현재 한계점

| 문제 | 영향 | 현재 우회책 |
|------|------|-----------|
| 정적 라우팅 | task_type 키워드 매칭만 가능, 컨텍스트 크기·복잡도 무시 | 수동 `/code`, `/design` 커맨드 |
| Codex TTY 문제 | `codex exec` 실행 불안정 | qwen-coder fallback |
| GLM-5 한계 인식 없음 | GLM-5가 못하는 작업도 GLM-5가 처리 | 사용자가 수동 판단 |
| 관찰성 부재 | 어떤 모델이 언제 호출됐는지 추적 불가 | 없음 |
| 설정 파편화 | Claude/Codex/Gemini 각각 별도 설정 | 수동 동기화 |
| 비용 추적 없음 | 에스컬레이션 빈도·비용 파악 불가 | 없음 |

---

## 6개 모델 특성 매트릭스 (비용 우선 정렬)

| 우선순위 | 모델 | 비용 | 강점 | 약점 | 에스컬레이션 조건 |
|---------|------|------|------|------|-----------------|
| **기본** | **GLM-5** (ZAI $3/월) | $3/월 고정 | Claude 호환 API, 범용 | 최상위 추론 부족 | — (기본값) |
| 보조 1 | **Qwen3-Coder-30B** (cognit) | 무료 | 빠른 코드 생성 | 20K ctx 제한 | 단순 코드 스니펫 요청 시 |
| 보조 2 | **Qwen3.5-122B** (nexus) | 무료 | 400K ctx, 고급 추론 | Tailscale 필수, 느림 | 60K+ 토큰 컨텍스트 |
| 에스컬 1 | **Gemini 3.1 Pro** | 무료/종량 | 디자인, 멀티모달 | 코드 약함 | UI/디자인/이미지 작업 |
| 에스컬 2 | **gpt-5.4-medium** | 구독제 | 코드 생성 최강 | TTY 문제 | 고품질 코드 필수 시 |
| 최종 | **Claude** (구독) | 구독료 | 최고 추론, 아키텍처 | 가장 비쌈 | 보안/아키텍처/최종 에스컬레이션 |

### 모델별 상세 스펙

| 모델 | Context Window | 서버 | 접속 | GPU | 제약 |
|------|---------------|------|------|-----|------|
| GLM-5 | — | ZAI Cloud | HTTPS | — | API rate limit (구독 플랜) |
| Qwen3-Coder-30B | 20K tokens | cognit (100.89.224.48:8000) | Tailscale | RTX 3080 Ti x2 (11.4GB/12GB) | 동시 요청 1개, VRAM 한계 |
| Qwen3.5-122B | 400K tokens | nexus (100.64.189.120:8080) | Tailscale | RTX 3090 x3 | 속도 느림 (Q3_K_XL 양자화) |
| Gemini 3.1 Pro | — | Google Cloud | HTTPS | — | 무료 티어 RPM 제한 |
| gpt-5.4-medium | — | OpenAI Cloud | HTTPS | — | 구독 플랜 내 제한 |
| Claude Sonnet 4.6 | 200K tokens | Anthropic Cloud | HTTPS | — | 구독 플랜 내 제한 |

---

## Phase 1: 지능형 프록시 라우팅 (ccproxy 적용)

> 출처: [starbaser/ccproxy](https://github.com/starbaser/ccproxy) (178 stars)
> 기간: 1주
> 난이도: 중
> 의존성: 없음 (독립 실행 가능)

### 1.1 핵심 아이디어

```
현재:
  claude-glm → ZAI API (GLM-5) → 모든 요청을 GLM-5가 처리

적용 후:
  claude-glm → ccproxy (localhost:4000) → 조건 분기
    ├─ 기본 (50%) ──────→ ZAI API (GLM-5, $3/월)
    ├─ 코드 (25%) ──────→ Codex (gpt-5.4-medium, 구독)
    ├─ 경량 (12%) ──────→ cognit (Qwen3-Coder-30B, 무료)
    ├─ 장문 (5%) ───────→ nexus (Qwen3.5-122B, 무료)
    ├─ 디자인 (5%) ─────→ Gemini 3.1 Pro (무료 티어)
    └─ 추론 (3%) ───────→ Claude 구독 (최종 에스컬레이션)
```

**GLM-5가 기본값이고, 비싼 모델은 조건 충족 시에만 에스컬레이션된다.**

### 1.2 왜 ccproxy인가

| 비교 항목 | 현재 (maestro-route.sh) | ccproxy 적용 후 |
|----------|------------------------|-----------------|
| 기본 모델 | GLM-5 (maestro.sh 고정) | GLM-5 (default rule) |
| 에스컬레이션 | 사용자가 수동 `/code`, `/design` | 자동 rule 매칭 |
| 라우팅 기준 | task_type 키워드 1가지 | 토큰 수, 도구 사용, 모델명, thinking 등 4가지 |
| 자체 모델 지원 | 별도 wrapper 스크립트 | `api_base`로 직접 연결 |
| fallback | 하드코딩 | rule chain → GLM-5 (항상 안전) |
| 비용 추적 | 없음 | LangFuse 연동 가능 |
| 투명성 | 사용자가 CLI 선택 | Claude Code가 자동 라우팅 (사용자 무관) |

### 1.3 디렉토리 구조

```
maestro-claude-code/
├── config/
│   ├── ccproxy.yaml              # LiteLLM 모델 목록 + 라우팅 규칙
│   ├── ccproxy.env               # ccproxy 환경변수 (포트, 로그 레벨)
│   └── litellm-fallback.yaml     # Tailscale 끊김 시 대체 설정 (자체 모델 제외)
├── scripts/
│   ├── maestro.sh                # 수정: ccproxy 자동 시작 + 프록시 연결
│   ├── ccproxy-start.sh          # 신규: ccproxy 독립 시작/종료/상태
│   ├── ccproxy-health.sh         # 신규: 프록시 + 백엔드 모델 health check
│   └── health-check.sh           # 수정: ccproxy 상태 항목 추가
└── logs/
    └── ccproxy/                  # 라우팅 로그 (자동 생성)
```

### 1.4 모델별 라우팅 규칙 설계

```yaml
# config/ccproxy.yaml — Maestro 6-Model 라우팅
# 핵심 원칙: GLM-5 기본, 에스컬레이션은 조건부

# ============================================================
# 모델 목록 (LiteLLM 형식)
# ============================================================
model_list:

  # ─── 기본: GLM-5 ($3/월) ───
  # ZAI Coding Plan 구독. Claude API 호환 엔드포인트.
  # ANTHROPIC_AUTH_TOKEN으로 인증 (ANTHROPIC_API_KEY 아님!)
  - model_name: "glm-5"
    litellm_params:
      model: "anthropic/claude-sonnet-4-6"
      api_base: "https://api.z.ai/api/anthropic"
      api_key: "os.environ/ZAI_API_KEY"
    model_info:
      description: "기본 오케스트레이터. 대부분의 요청 처리."
      cost_per_month: "$3 고정"

  # ─── 무료 보조: Qwen3-Coder-30B (cognit) ───
  # AWQ-4bit 양자화, vLLM 서빙.
  # GPU: RTX 3080 Ti x2 (11.4GB/12GB 사용)
  # 제약: 동시 요청 1개, 20K ctx
  - model_name: "qwen3-coder-30b"
    litellm_params:
      model: "openai/Qwen3-Coder-30B-A3B-Instruct"
      api_base: "http://100.89.224.48:8000/v1"
      api_key: "not-needed"
    model_info:
      description: "경량 코드 생성. haiku 티어 대체."
      max_tokens: 20000
      requires_tailscale: true
      server: "cognit"

  # ─── 무료 보조: Qwen3.5-122B (nexus) ───
  # Q3_K_XL 양자화, llama-server 서빙.
  # GPU: RTX 3090 x3
  # 장점: 400K context window
  - model_name: "qwen3.5-122b"
    litellm_params:
      model: "openai/Qwen3.5-122B-Q3_K_XL"
      api_base: "http://100.64.189.120:8080/v1"
      api_key: "not-needed"
    model_info:
      description: "장문 분석, 대규모 코드 리뷰."
      max_tokens: 400000
      requires_tailscale: true
      server: "nexus"

  # ─── 에스컬레이션: Gemini 3.1 Pro ───
  # 무료 티어 RPM 제한 있음.
  # 멀티모달(이미지, 비디오), 웹 검색에 강점.
  - model_name: "gemini-3.1-pro"
    litellm_params:
      model: "gemini/gemini-3.1-pro-preview"
      api_key: "os.environ/GOOGLE_API_KEY"
    model_info:
      description: "디자인, UI/UX, 멀티모달 분석."

  # ─── 에스컬레이션: Codex gpt-5.4-medium (구독) ───
  # Codex 구독이므로 코드 작업에 적극 활용.
  # 추가 비용 없음.
  - model_name: "gpt-5.4-medium"
    litellm_params:
      model: "openai/gpt-5.4-medium"
      api_key: "os.environ/OPENAI_API_KEY"
    model_info:
      description: "고품질 코드 생성/리뷰. 구독 내 무제한."
      cost_per_month: "구독 포함"

  # ─── 최종 에스컬레이션: Claude 구독 ───
  # thinking/extended thinking이 필요한 고급 추론만.
  # 사용 빈도: ~3%
  - model_name: "claude-sonnet-4-6"
    litellm_params:
      model: "claude-sonnet-4-6"
      api_key: "os.environ/ANTHROPIC_API_KEY"
    model_info:
      description: "보안 감사, 아키텍처 설계, 최종 에스컬레이션."

# ============================================================
# 라우팅 규칙 (우선순위 순, 먼저 매칭되면 실행)
# 모든 규칙 미매칭 시 → 기본(GLM-5)
# ============================================================
routing_rules:

  # ── Rule 1: 장문 컨텍스트 → Qwen3.5 (무료, 400K ctx) ──
  # GLM-5의 ctx 한계 초과 시 무료 대안으로 라우팅.
  # Tailscale 미연결 시 이 rule은 비활성화 → GLM-5 fallback.
  - name: "long-context"
    rule: "TokenCountRule"
    threshold: 60000
    route_to: "qwen3.5-122b"
    fallback: "glm-5"
    condition: "tailscale_reachable(nexus)"

  # ── Rule 2: thinking 요청 → Claude 구독 ──
  # extended_thinking, <thinking> 태그, 복잡 추론 요청.
  # GLM-5로는 품질이 부족한 고급 추론만 에스컬레이션.
  - name: "deep-thinking"
    rule: "ThinkingRule"
    route_to: "claude-sonnet-4-6"
    fallback: "glm-5"

  # ── Rule 3: 멀티모달 → Gemini (무료 티어) ──
  # 웹 검색, 이미지 분석, 스크린샷 해석.
  # GLM-5/Qwen은 멀티모달 미지원.
  - name: "multimodal"
    rule: "MatchToolRule"
    tools: ["WebSearch", "ImageAnalysis", "BrowserScreenshot"]
    route_to: "gemini-3.1-pro"
    fallback: "glm-5"

  # ── Rule 4: 코드 생성/편집 → Codex (구독, 추가비용 없음) ──
  # Write/Edit 도구 사용 시 gpt-5.4-medium으로 라우팅.
  # Codex 구독이므로 적극 활용.
  - name: "code-work"
    rule: "MatchToolRule"
    tools: ["Write", "Edit"]
    route_to: "gpt-5.4-medium"
    fallback: "glm-5"

  # ── Rule 5: haiku 경량 요청 → Qwen3-Coder (무료) ──
  # OMC가 haiku 티어로 보내는 단순 조회, 스니펫 생성.
  # Tailscale 미연결 시 GLM-5 fallback.
  - name: "simple-task"
    rule: "MatchModelRule"
    pattern: "haiku"
    route_to: "qwen3-coder-30b"
    fallback: "glm-5"
    condition: "tailscale_reachable(cognit)"

  # ── Rule 6: 기본 → GLM-5 ($3/월) ──
  # 위 규칙에 매칭되지 않는 모든 요청.
  # 대화, 기획, 문서 작성, 일반 질문 등.
  - name: "default"
    rule: "DefaultRule"
    route_to: "glm-5"

# ============================================================
# 참고: maestro-route.sh와의 역할 분담
# ============================================================
# ccproxy: API 레벨 자동 라우팅 (Claude Code ↔ 백엔드 모델)
#   - Claude Code의 모든 API 호출을 가로채서 조건부 라우팅
#   - 사용자 개입 없이 투명하게 동작
#
# maestro-route.sh: CLI 레벨 명시적 위임 (/code, /design 커맨드)
#   - 사용자가 의도적으로 특정 CLI에 태스크 위임
#   - ccproxy 미지원 기능 (Codex CLI의 --yolo 모드 등)
#
# 두 시스템은 보완적으로 공존:
#   ccproxy → 자동 (90% 커버)
#   maestro-route.sh → 수동 + fallback (10%)
```

### 1.5 maestro.sh 수정안

```bash
#!/bin/bash
# Maestro Claude Code - GLM-5 (ZAI) 모드 런처
#
# 변경 전: claude-glm → ZAI API 직접
# 변경 후: claude-glm → ccproxy → ZAI API (+ 조건부 에스컬레이션)
#
# 사용법:
#   ./scripts/maestro.sh           → ccproxy 경유 GLM-5 모드
#   ./scripts/maestro.sh direct    → ZAI API 직접 (ccproxy 우회)
#   ./scripts/maestro.sh status    → 설정 및 프록시 상태 확인

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CCPROXY_PORT=4000
CCPROXY_CONFIG="${PROJECT_DIR}/config/ccproxy.yaml"
CCPROXY_LOG="${PROJECT_DIR}/logs/ccproxy/proxy.log"

# .env에서 API 키 로드
if [ -f "${PROJECT_DIR}/.env" ]; then
    set -a; source "${PROJECT_DIR}/.env"; set +a
fi
: "${ZAI_API_KEY:?ZAI_API_KEY 미설정. .env 파일 확인}"

# ─── 함수 정의 ───

start_ccproxy() {
    if curl -s "http://localhost:${CCPROXY_PORT}/health" > /dev/null 2>&1; then
        echo "[maestro] ccproxy 이미 실행 중 (port ${CCPROXY_PORT})"
        return 0
    fi

    echo "[maestro] ccproxy 시작 중..."
    mkdir -p "$(dirname "$CCPROXY_LOG")"

    # Tailscale 상태 확인 → 자체 모델 가용 여부 판단
    # cognit(100.89.224.48), nexus(100.64.189.120)는 Tailscale 네트워크 내 서버
    if tailscale status --json 2>/dev/null | grep -q '"Online": true'; then
        # Tailscale 연결됨 → 개별 서버 도달 가능 여부 확인
        COGNIT_OK=$(tailscale ping --c 1 --timeout 3s 100.89.224.48 2>/dev/null && echo "yes" || echo "no")
        NEXUS_OK=$(tailscale ping --c 1 --timeout 3s 100.64.189.120 2>/dev/null && echo "yes" || echo "no")

        if [ "$COGNIT_OK" = "yes" ] || [ "$NEXUS_OK" = "yes" ]; then
            echo "[maestro] Tailscale 연결 확인 → 자체 모델 활성"
            [ "$COGNIT_OK" = "yes" ] && echo "  cognit (Qwen3-Coder): ✅"
            [ "$NEXUS_OK" = "yes" ]  && echo "  nexus  (Qwen3.5):     ✅"
            [ "$COGNIT_OK" = "no" ]  && echo "  cognit (Qwen3-Coder): ❌ 미응답"
            [ "$NEXUS_OK" = "no" ]   && echo "  nexus  (Qwen3.5):     ❌ 미응답"
            CONFIG_FILE="$CCPROXY_CONFIG"
        else
            echo "[maestro] Tailscale 연결됨, 서버 미응답 → 클라우드 모델만 사용"
            CONFIG_FILE="${PROJECT_DIR}/config/litellm-fallback.yaml"
        fi
    else
        echo "[maestro] Tailscale 미연결 → GLM-5 + 클라우드 모델만 사용"
        echo "  hint: 'tailscale up' 으로 연결 후 재시도"
        CONFIG_FILE="${PROJECT_DIR}/config/litellm-fallback.yaml"
    fi

    ccproxy run --config "$CONFIG_FILE" \
                --port ${CCPROXY_PORT} \
                >> "$CCPROXY_LOG" 2>&1 &
    CCPROXY_PID=$!
    echo $CCPROXY_PID > "${PROJECT_DIR}/logs/ccproxy/proxy.pid"

    # 프록시 준비 대기 (최대 10초)
    for i in $(seq 1 10); do
        if curl -s "http://localhost:${CCPROXY_PORT}/health" > /dev/null 2>&1; then
            echo "[maestro] ccproxy 준비 완료 (PID: $CCPROXY_PID)"
            return 0
        fi
        sleep 1
    done
    echo "[maestro] 경고: ccproxy 시작 실패, ZAI API 직접 연결로 fallback"
    return 1
}

run_with_proxy() {
    ANTHROPIC_BASE_URL="http://localhost:${CCPROXY_PORT}" \
    ANTHROPIC_AUTH_TOKEN="${ZAI_API_KEY}" \
    exec claude "$@"
}

run_direct() {
    echo "[maestro] GLM-5 (ZAI) 직접 모드"
    ANTHROPIC_BASE_URL="https://api.z.ai/api/anthropic" \
    ANTHROPIC_AUTH_TOKEN="${ZAI_API_KEY}" \
    exec claude "$@"
}

show_status() {
    echo "Maestro Claude Code"
    echo "==================="
    echo ""
    echo "  진입점:      claude-glm (ZAI Coding Plan)"
    echo "  비용:        ~\$3/월 (구독제)"
    echo ""

    # ccproxy 상태
    if curl -s "http://localhost:${CCPROXY_PORT}/health" > /dev/null 2>&1; then
        echo "  ccproxy:     ✅ 실행 중 (port ${CCPROXY_PORT})"
    else
        echo "  ccproxy:     ❌ 미실행"
    fi

    # Tailscale 상태
    if tailscale status --json 2>/dev/null | grep -q '"Online": true'; then
        echo "  Tailscale:   ✅ 연결됨"
        tailscale ping --c 1 --timeout 3s 100.89.224.48 > /dev/null 2>&1 \
            && echo "  Qwen3-Coder: ✅ cognit (100.89.224.48:8000)" \
            || echo "  Qwen3-Coder: ❌ cognit 미응답"
        tailscale ping --c 1 --timeout 3s 100.64.189.120 > /dev/null 2>&1 \
            && echo "  Qwen3.5:     ✅ nexus (100.64.189.120:8080)" \
            || echo "  Qwen3.5:     ❌ nexus 미응답"
    else
        echo "  Tailscale:   ❌ 미연결 (자체 모델 비활성)"
        echo "  hint:        'tailscale up' 으로 연결"
    fi
    echo ""
    echo "  실행: ./scripts/maestro.sh"
    echo "  직접: ./scripts/maestro.sh direct"
    echo "  구독: claude (환경변수 없이)"
}

# ─── 메인 ───

case "${1:-run}" in
    status)
        show_status
        ;;
    direct)
        shift
        run_direct "$@"
        ;;
    *)
        if start_ccproxy; then
            run_with_proxy "$@"
        else
            run_direct "$@"
        fi
        ;;
esac
```

### 1.6 Tailscale fallback 설정

```yaml
# config/litellm-fallback.yaml
# Tailscale 미연결 시 사용. 자체 서버(nexus/cognit) 제외.
# GLM-5 + 클라우드 모델만 사용.

model_list:
  - model_name: "glm-5"
    litellm_params:
      model: "anthropic/claude-sonnet-4-6"
      api_base: "https://api.z.ai/api/anthropic"
      api_key: "os.environ/ZAI_API_KEY"

  - model_name: "gemini-3.1-pro"
    litellm_params:
      model: "gemini/gemini-3.1-pro-preview"
      api_key: "os.environ/GOOGLE_API_KEY"

  - model_name: "gpt-5.4-medium"
    litellm_params:
      model: "openai/gpt-5.4-medium"
      api_key: "os.environ/OPENAI_API_KEY"

  - model_name: "claude-sonnet-4-6"
    litellm_params:
      model: "claude-sonnet-4-6"
      api_key: "os.environ/ANTHROPIC_API_KEY"

routing_rules:
  - name: "deep-thinking"
    rule: "ThinkingRule"
    route_to: "claude-sonnet-4-6"
  - name: "code-work"
    rule: "MatchToolRule"
    tools: ["Write", "Edit"]
    route_to: "gpt-5.4-medium"
  - name: "multimodal"
    rule: "MatchToolRule"
    tools: ["WebSearch", "ImageAnalysis"]
    route_to: "gemini-3.1-pro"
  - name: "default"
    rule: "DefaultRule"
    route_to: "glm-5"
```

### 1.7 에스컬레이션 빈도 예상

| 규칙 | 예상 빈도 | 비용 영향 | 비고 |
|------|----------|----------|------|
| 기본 (GLM-5) | ~50% | $3/월 (고정) | 대화, 기획, 문서, 분석 |
| Codex gpt-5.4-medium (Write/Edit) | ~20% | 구독 내 (추가 비용 없음) | 코드 생성, 편집 |
| Qwen3-Coder (haiku 경량) | ~12% | 무료 | 단순 조회, 스니펫 |
| Qwen3.5 (장문 >60K) | ~5% | 무료 | 대규모 코드 리뷰 |
| Gemini (멀티모달) | ~5% | 무료 티어 | UI/디자인/이미지 |
| Claude 구독 (thinking) | ~3% | 구독 내 | 보안 감사, 아키텍처 |
| Codex CLI (maestro-route.sh) | ~5% | 구독 내 | 명시적 /code 커맨드 |

> **Codex 구독 효과**: 코드 작업(Write/Edit)의 ~25%를 gpt-5.4-medium이 처리.
> GLM-5 부담 70% → 50%로 감소. 추가 비용 없이 코드 품질 향상.

### 1.8 작업 목록 (상세)

| # | 작업 | 산출물 | 검증 방법 | 소요 |
|---|------|--------|----------|------|
| 1-1 | ccproxy 설치 및 의존성 확인 | `pip install ccproxy` 성공 | `ccproxy --version` | 30분 |
| 1-2 | `config/ccproxy.yaml` 작성 | 설정 파일 | ccproxy 파싱 성공 | 1시간 |
| 1-3 | `config/litellm-fallback.yaml` 작성 | Tailscale fallback 설정 | 파싱 성공 | 30분 |
| 1-4 | nexus/cognit 연결 테스트 | curl로 `/v1/models` 확인 | HTTP 200 응답 | 30분 |
| 1-5 | `maestro.sh` 수정 | 프록시 자동 시작 | `./maestro.sh status` 정상 | 2시간 |
| 1-6 | `scripts/ccproxy-start.sh` 작성 | 독립 시작/종료 스크립트 | start/stop/status 동작 | 1시간 |
| 1-7 | `scripts/ccproxy-health.sh` 작성 | 프록시 + 백엔드 health | 모든 모델 상태 출력 | 1시간 |
| 1-8 | `health-check.sh` 수정 | ccproxy 항목 추가 | 기존 + ccproxy 상태 | 30분 |
| 1-9 | 통합 테스트: GLM-5 기본 라우팅 | 일반 대화가 GLM-5로 | 로그에서 glm-5 확인 | 1시간 |
| 1-10 | 통합 테스트: Write/Edit → Codex | 코드 편집 시 gpt-5.4-medium | 로그에서 모델 확인 | 1시간 |
| 1-11 | 통합 테스트: Tailscale 끊김 fallback | `tailscale down` → fallback 설정 | GLM-5만 사용 확인 | 1시간 |
| 1-12 | `.env.example` 업데이트 | ccproxy 관련 변수 추가 | 문서 정확성 | 15분 |

### 1.9 리스크 및 대응

| 리스크 | 확률 | 영향 | 대응 |
|--------|------|------|------|
| ccproxy가 Claude Code API 스펙 변경에 깨짐 | 중 | 높음 | `maestro.sh direct` fallback 유지 |
| LiteLLM이 Anthropic streaming 미완벽 지원 | 중 | 높음 | ccproxy 이슈 트래커 선행 확인 |
| Tailscale 끊김 시 nexus/cognit 타임아웃 | 높음 | 중 | `tailscale status` 감지 + fallback 설정 자동 전환 |
| ccproxy 프로세스 크래시 | 낮음 | 중 | PID 파일 + 자동 재시작 로직 |
| ZAI API 키 노출 | 낮음 | 높음 | `.env` gitignore + 런타임만 메모리 |

### 1.10 롤백 계획

```bash
# ccproxy 문제 발생 시 즉시 롤백:
# 1. ccproxy 중지
kill $(cat logs/ccproxy/proxy.pid)

# 2. 기존 방식으로 직접 실행
./scripts/maestro.sh direct

# 또는 원래 maestro.sh (git checkout)
git checkout scripts/maestro.sh
```

---

## Phase 2: 멀티에이전트 관찰성 대시보드

> 출처: [disler/claude-code-hooks-multi-agent-observability](https://github.com/disler/claude-code-hooks-multi-agent-observability)
> 기간: 3일
> 난이도: 중
> 의존성: Phase 1 (ccproxy 이벤트 연동)

### 2.1 현재 vs 적용 후

| 항목 | 현재 | 적용 후 |
|------|------|--------|
| 에이전트 추적 | 없음 | 12종 이벤트 실시간 모니터링 |
| 모델별 호출 통계 | 없음 | SQLite 기반 이벤트 로그 |
| 실패 감지 | 수동 확인 | PostToolUseFailure 자동 알림 |
| 서브에이전트 가시성 | 없음 | SubagentStart/Stop 추적 |
| ccproxy 라우팅 추적 | 없음 | ModelRouted 이벤트로 가시화 |

### 2.2 아키텍처

```
┌─────────────────────────────────────────────────────┐
│                    Claude Code                       │
│  claude-glm → ccproxy → 6개 모델                     │
│      │                                               │
│      ▼                                               │
│  Hook Scripts (Python/uv)                            │
│  ┌──────────────────────────────┐                    │
│  │ PreToolUse   → send_event() │                    │
│  │ PostToolUse  → send_event() │                    │
│  │ Stop         → send_event() │                    │
│  │ SubagentStart→ send_event() │                    │
│  │ SubagentStop → send_event() │                    │
│  │ + contract-gate.js (기존)    │                    │
│  │ + security-scan.js (기존)    │                    │
│  │ + task-sync.js (기존)        │                    │
│  └──────────┬───────────────────┘                    │
└─────────────┼────────────────────────────────────────┘
              │ HTTP POST
              ▼
┌─────────────────────────────────┐
│         Bun Server              │
│  ┌────────────┐  ┌───────────┐  │
│  │  SQLite DB  │  │ WebSocket │  │
│  │  (이벤트)   │  │ (실시간)  │  │
│  └────────────┘  └─────┬─────┘  │
└─────────────────────────┼───────┘
                          │
              ┌───────────▼───────────┐
              │   Vue.js 대시보드      │
              │  ┌─────────────────┐  │
              │  │ 모델별 호출 현황  │  │
              │  │ 에스컬레이션 히트  │  │
              │  │ 실패/fallback 로그│  │
              │  │ 비용 추정        │  │
              │  └─────────────────┘  │
              └───────────────────────┘
```

### 2.3 모니터링 이벤트

#### 기본 12종 (observability 저장소 제공)

| 이벤트 | 설명 | Maestro 활용 |
|--------|------|-------------|
| PreToolUse | 도구 실행 전 | Write/Edit 요청 → Codex 라우팅 확인 |
| PostToolUse | 도구 실행 후 | 실행 결과 로깅 |
| PostToolUseFailure | 도구 실패 | 모델별 실패율 추적 |
| PermissionRequest | 권한 요청 | 보안 이벤트 감시 |
| Stop | 응답 완료 | 세션 통계 집계 |
| SubagentStart | 서브에이전트 시작 | OMC 에이전트 위임 추적 |
| SubagentStop | 서브에이전트 종료 | 에이전트 실행 시간 |
| PreCompact | 컨텍스트 압축 | 토큰 사용량 모니터링 |
| UserPromptSubmit | 사용자 프롬프트 | 요청 패턴 분석 |
| SessionStart | 세션 시작 | 세션 메타데이터 |
| SessionEnd | 세션 종료 | 세션 요약 |
| Notification | 알림 | 중요 이벤트 전달 |

#### Maestro 전용 이벤트 4종 (신규 추가)

```python
# hooks/maestro-events.py
# ccproxy 라우팅 이벤트를 대시보드에 전송

import json
import os
import httplib

DASHBOARD_URL = os.environ.get("MAESTRO_DASHBOARD_URL", "http://localhost:3456")

MAESTRO_EVENTS = {
    "ModelRouted": {
        "fields": ["source_model", "target_model", "rule_matched", "token_count", "latency_ms"],
        "description": "ccproxy가 모델을 라우팅할 때 발생",
        "example": {
            "source_model": "glm-5",
            "target_model": "gpt-5.4-medium",
            "rule_matched": "code-work",
            "token_count": 1500,
            "latency_ms": 45
        }
    },
    "FallbackTriggered": {
        "fields": ["original_model", "fallback_model", "reason", "error_code"],
        "description": "Tailscale 끊김, 서버 다운 등으로 fallback 발생",
        "example": {
            "original_model": "qwen3-coder-30b",
            "fallback_model": "glm-5",
            "reason": "tailscale_disconnected",
            "error_code": "ETIMEDOUT"
        }
    },
    "CostEstimate": {
        "fields": ["model", "input_tokens", "output_tokens", "estimated_cost_usd"],
        "description": "모델별 비용 추정 (세션 종료 시 집계)",
        "example": {
            "model": "gpt-5.4-medium",
            "input_tokens": 12000,
            "output_tokens": 3000,
            "estimated_cost_usd": 0.00  # 구독 내
        }
    },
    "SelfHostedHealth": {
        "fields": ["server", "status", "gpu_usage_percent", "vram_free_mb", "response_time_ms"],
        "description": "nexus/cognit 서버 상태 (5분 주기)",
        "example": {
            "server": "cognit",
            "status": "healthy",
            "gpu_usage_percent": 95,
            "vram_free_mb": 600,
            "response_time_ms": 120
        }
    }
}
```

### 2.4 기존 hooks와 병합

```jsonc
// .claude/settings.json 수정안
// 기존 3개 hook + observability 6개 hook = 9개
{
  "hooks": {
    "PreToolUse": [
      // 기존: API 계약 검증
      { "matcher": "Write|Edit", "command": "node .claude/hooks/contract-gate.js" },
      // 신규: observability 이벤트 전송
      { "matcher": "*", "command": "python .claude/hooks/send-event.py PreToolUse" }
    ],
    "PostToolUse": [
      // 기존: 보안 스캔
      { "matcher": "Write|Edit", "command": "node .claude/hooks/security-scan.js" },
      // 신규: observability 이벤트 전송
      { "matcher": "*", "command": "python .claude/hooks/send-event.py PostToolUse" }
    ],
    "Stop": [
      // 기존: TASKS.md 동기화
      { "command": "node .claude/hooks/task-sync.js" },
      // 신규: 세션 통계 전송
      { "command": "python .claude/hooks/send-event.py Stop" }
    ],
    "SubagentStart": [
      { "command": "python .claude/hooks/send-event.py SubagentStart" }
    ],
    "SubagentStop": [
      { "command": "python .claude/hooks/send-event.py SubagentStop" }
    ],
    "PostToolUseFailure": [
      { "command": "python .claude/hooks/send-event.py PostToolUseFailure" }
    ]
  }
}
```

### 2.5 대시보드 커스터마이징

| 모델 | 컬러 코드 | 표시명 |
|------|----------|--------|
| GLM-5 | `#4CAF50` (초록) | 🟢 GLM-5 (기본) |
| Qwen3-Coder | `#2196F3` (파랑) | 🔵 Qwen-Coder (경량) |
| Qwen3.5 | `#9C27B0` (보라) | 🟣 Qwen3.5 (장문) |
| Gemini | `#FF9800` (주황) | 🟠 Gemini (디자인) |
| gpt-5.4-medium | `#F44336` (빨강) | 🔴 Codex (코드) |
| Claude | `#FFD700` (금색) | 🟡 Claude (추론) |

### 2.6 작업 목록 (상세)

| # | 작업 | 산출물 | 검증 방법 | 소요 |
|---|------|--------|----------|------|
| 2-1 | observability 저장소 클론 | `tools/observability/` | 디렉토리 존재 | 15분 |
| 2-2 | Bun + SQLite + Vue 의존성 설치 | `bun install` 성공 | 서버 시작 | 30분 |
| 2-3 | `send-event.py` 작성 | hook 이벤트 전송기 | curl로 이벤트 수신 | 2시간 |
| 2-4 | Maestro 전용 이벤트 4종 추가 | `maestro-events.py` | 대시보드에 표시 | 2시간 |
| 2-5 | settings.json hook 병합 | 9개 hook 등록 | hook 에러 없음 | 1시간 |
| 2-6 | 대시보드 모델 컬러 코딩 | Vue 컴포넌트 수정 | 6색 구분 표시 | 1시간 |
| 2-7 | ccproxy 라우팅 로그 → 대시보드 연결 | ModelRouted 이벤트 | 라우팅 실시간 표시 | 2시간 |
| 2-8 | 통합 테스트 | 6개 모델 이벤트 표시 | 대시보드 스크린샷 | 1시간 |

### 2.7 롤백 계획

```bash
# observability 제거 시:
# 1. settings.json에서 send-event.py 관련 hook만 제거
# 2. 기존 3개 hook (contract-gate, security-scan, task-sync)은 유지
# 3. Bun 서버 중지
```

---

## Phase 3: 크로스 도구 설정 동기화

> 출처: [EveryInc/compound-engineering-plugin](https://github.com/EveryInc/compound-engineering-plugin) (10K stars)
> 기간: 2일
> 난이도: 낮
> 의존성: 없음

### 3.1 문제

현재 6개 CLI 도구가 각각 독립된 설정을 가짐:

```
~/.claude/skills/       ← Claude Code 전용
~/.claude/commands/     ← Claude Code 전용
~/.claude/settings.json ← Claude Code MCP 설정

~/.codex/              ← Codex 별도 설정
~/.gemini/skills/      ← Gemini 별도 설정

# 결과: 같은 skill을 3군데에 수동 복사/관리
```

### 3.2 해결

compound-engineering의 `sync` 명령으로 Claude 설정을 **원본(source of truth)**으로, 나머지 도구에 심볼릭 링크:

```
~/.claude/skills/my-skill.md  (원본)
    ├── symlink → ~/.codex/skills/my-skill.md
    └── symlink → ~/.gemini/skills/my-skill.md
```

### 3.3 동기화 매트릭스

| 대상 | 동기화 항목 | 제외 항목 | 이유 |
|------|-----------|----------|------|
| **Codex** | skills/, commands/ | contract-gate hook | Codex는 자체 보안 모델 |
| **Gemini** | skills/, MCP 설정 | 코드 실행 commands | Gemini는 코드보다 디자인 |
| **Qwen CLI** | 해당 없음 | 전부 | OpenAI 호환 API만 사용, CLI 없음 |

### 3.4 자동 동기화 스크립트

```bash
#!/bin/bash
# scripts/sync-settings.sh
# Claude 설정을 Codex, Gemini에 동기화

echo "[sync] Claude → Codex, Gemini 설정 동기화"

# skills 동기화
bunx @every-env/compound-plugin sync \
  --source ~/.claude/skills/ \
  --targets codex,gemini \
  --exclude "contract-gate*,security-scan*,task-sync*"

# commands 동기화 (Codex만)
bunx @every-env/compound-plugin sync \
  --source ~/.claude/commands/ \
  --targets codex \
  --exclude "design*,localcode*"

# MCP 서버 동기화 (Gemini만)
bunx @every-env/compound-plugin sync \
  --mcp \
  --source ~/.claude/settings.json \
  --targets gemini

echo "[sync] 완료"
```

### 3.5 작업 목록

| # | 작업 | 산출물 | 검증 방법 | 소요 |
|---|------|--------|----------|------|
| 3-1 | compound-engineering 설치 | `bunx @every-env/compound-plugin --version` | 버전 출력 | 15분 |
| 3-2 | 동기화 대상/제외 목록 정의 | `config/sync-targets.yaml` | YAML 파싱 | 30분 |
| 3-3 | `scripts/sync-settings.sh` 작성 | 동기화 스크립트 | 심볼릭 링크 생성 확인 | 1시간 |
| 3-4 | `maestro.sh`에 세션 시작 시 동기화 추가 | 자동 동기화 | 세션마다 동기화 로그 | 30분 |
| 3-5 | Codex skills 동기화 테스트 | Codex에서 skill 사용 | `/skill` 명령 동작 | 1시간 |
| 3-6 | Gemini MCP 동기화 테스트 | Gemini에서 MCP 사용 | MCP 도구 호출 성공 | 1시간 |

### 3.6 롤백 계획

```bash
# 심볼릭 링크만 제거하면 원복:
find ~/.codex/skills -type l -delete
find ~/.gemini/skills -type l -delete
```

---

## Phase 4: 병렬 세션 관리 (선택)

> 출처: [smtg-ai/claude-squad](https://github.com/smtg-ai/claude-squad) (6.3K stars)
> 기간: 1일 (설치 + 설정)
> 난이도: 낮
> 의존성: 없음
> **선택적 적용** — 대규모 태스크에서만 필요

### 4.1 적용 시나리오

대규모 프로젝트에서 **3-4개 모델을 동시에 다른 파일에서 작업**:

```bash
# 프로젝트 초기화
cd ~/workspace/my-project

# 4개 모델 동시 실행 (각각 독립 git worktree)
cs new -n "architect" -p "claude"            --prompt "시스템 아키텍처 설계..."
cs new -n "backend"   -p "codex"             --prompt "API 구현..."
cs new -n "designer"  -p "gemini"            --prompt "UI 컴포넌트 설계..."
cs new -n "reviewer"  -p "./scripts/qwen35-cli.sh" --prompt "전체 코드 리뷰..."

# TUI에서 세션 전환, 결과 확인, merge
cs  # TUI 열기
```

### 4.2 모델별 세션 프리셋

```yaml
# ~/.claude-squad/config.yaml
presets:
  architect:
    program: "claude"
    worktree_prefix: "wt-arch"
    auto_approve: false     # 아키텍처는 사람 확인
    description: "전체 설계, CLAUDE.md 업데이트"

  backend:
    program: "codex"
    worktree_prefix: "wt-be"
    auto_approve: true      # Codex 구독, 자동 승인
    description: "src/ 구현, API 엔드포인트"

  designer:
    program: "gemini"
    worktree_prefix: "wt-design"
    auto_approve: false
    description: "components/, styles/ 디자인"

  reviewer:
    program: "./scripts/qwen35-cli.sh"
    worktree_prefix: "wt-review"
    auto_approve: false
    description: "전체 코드 리뷰 (400K ctx 활용)"

  coder:
    program: "./scripts/qwen-coder-cli.sh"
    worktree_prefix: "wt-code"
    auto_approve: true
    description: "경량 코드 생성, 스니펫"
```

### 4.3 git worktree 격리

```
my-project/
├── .git/                    # 메인 저장소
├── src/                     # 메인 브랜치
└── ..worktrees/
    ├── wt-arch-architect/   # architect 세션 (독립 브랜치)
    ├── wt-be-backend/       # backend 세션 (독립 브랜치)
    ├── wt-design-designer/  # designer 세션 (독립 브랜치)
    └── wt-review-reviewer/  # reviewer 세션 (독립 브랜치)
```

각 세션은 **독립 브랜치에서 작업** → 충돌 없음 → 완료 후 merge.

### 4.4 작업 목록

| # | 작업 | 산출물 | 검증 방법 | 소요 |
|---|------|--------|----------|------|
| 4-1 | Go 설치 확인 | `go version` | 1.21+ | 5분 |
| 4-2 | claude-squad 설치 | `go install github.com/smtg-ai/claude-squad@latest` | `cs --version` | 15분 |
| 4-3 | 프리셋 설정 작성 | `~/.claude-squad/config.yaml` | `cs list-presets` | 30분 |
| 4-4 | 멀티 세션 실행 테스트 | 3개 세션 동시 실행 | TUI에서 3세션 표시 | 1시간 |
| 4-5 | worktree merge 테스트 | 결과 merge | git log에서 merge 확인 | 1시간 |

### 4.5 제한사항

- **TUI 전용**: 프로그래매틱 API 없음 → 자동화 통합에 제약
- **터미널 필요**: tmux 기반이므로 SSH/원격에서만 사용
- **OMC와 별개**: OMC의 Agent tool과는 독립 실행 (OMC는 같은 프로세스 내 subagent)

---

## Phase 5: 참조 아키텍처 벤치마크

> 출처: [musistudio/claude-code-router](https://github.com/musistudio/claude-code-router) (29K stars)
> 기간: 2일 (분석 + 선택적 차용)
> 난이도: 중
> 의존성: Phase 1 (ccproxy 기반 위에 패턴 추가)

### 5.1 ccproxy vs claude-code-router

| 항목 | ccproxy (Phase 1 채택) | claude-code-router |
|------|----------------------|-------------------|
| 언어 | Python (LiteLLM) | Node.js |
| 라우팅 | Rule 기반 (4종) | Router 타입 (6종) + Custom JS |
| 자체 모델 | api_base 지정 | Provider 설정 |
| Subagent 라우팅 | 없음 | `<CCR-SUBAGENT-MODEL>` 태그 |
| 장점 | 유연한 rule chain, fallback | Subagent별 모델 지정 |
| Stars | 178 | 29K |

### 5.2 차용할 패턴: Subagent 모델 태그

claude-code-router의 **Subagent 모델 태그 패턴**은 ccproxy에 없는 기능:

```markdown
<!-- 프롬프트에 삽입하면 해당 subagent만 다른 모델 사용 -->
<CCR-SUBAGENT-MODEL>qwen3.5-122b</CCR-SUBAGENT-MODEL>
```

이 패턴을 ccproxy의 Custom Hook으로 구현하면 **OMC 에이전트별 최적 모델 자동 배정** 가능.

### 5.3 OMC 에이전트 ↔ 모델 매핑

```yaml
# config/agent-model-map.yaml
# OMC 28개 에이전트별 최적 모델 매핑

# ─── Opus 티어 → Claude 구독 또는 Qwen3.5 ───
opus_agents:
  architect:        "claude-sonnet-4-6"     # 아키텍처 = 최고 추론 필요
  analyst:          "qwen3.5-122b"          # 분석 = 장문 컨텍스트 활용
  critic:           "claude-sonnet-4-6"     # 리뷰 = 정밀 판단
  planner:          "glm-5"                 # 기획 = GLM-5로 충분
  deep-executor:    "gpt-5.4-medium"        # 구현 = Codex 구독
  scientist-high:   "qwen3.5-122b"          # 데이터 분석 = 장문

# ─── Sonnet 티어 → Codex 또는 GLM-5 ───
sonnet_agents:
  code-reviewer:    "gpt-5.4-medium"        # 코드 리뷰 = Codex
  designer:         "gemini-3.1-pro"        # 디자인 = Gemini
  executor:         "gpt-5.4-medium"        # 구현 = Codex 구독
  git-master:       "glm-5"                 # Git = GLM-5
  qa-tester:        "gpt-5.4-medium"        # 테스트 = Codex
  researcher:       "glm-5"                 # 조사 = GLM-5
  scientist:        "qwen3.5-122b"          # 분석 = 장문
  security-reviewer:"claude-sonnet-4-6"     # 보안 = 최고 정밀도
  writer:           "glm-5"                 # 문서 = GLM-5 (저비용)

# ─── Haiku 티어 → Qwen3-Coder 또는 GLM-5 ───
haiku_agents:
  architect-low:    "glm-5"                 # 간단 질문
  build-fixer-low:  "qwen3-coder-30b"       # 빌드 에러 = 경량 코드
  code-reviewer-low:"qwen3-coder-30b"       # 빠른 리뷰
  executor-low:     "qwen3-coder-30b"       # 단순 코드
  explore:          "glm-5"                 # 탐색
  designer-low:     "glm-5"                 # 간단 스타일링

# ─── 전문가 에이전트 ───
specialist_agents:
  backend-specialist:  "gpt-5.4-medium"     # 백엔드 = Codex
  frontend-specialist: "gemini-3.1-pro"     # 프론트엔드 = Gemini
  database-specialist: "gpt-5.4-medium"     # DB = Codex
  security-specialist: "claude-sonnet-4-6"  # 보안 = Claude
  test-specialist:     "gpt-5.4-medium"     # 테스트 = Codex
  docs-specialist:     "glm-5"              # 문서 = GLM-5
```

### 5.4 구현 방법: ccproxy Custom Hook

```python
# hooks/subagent-router.py
# SubagentStart hook에서 에이전트 이름을 감지하여
# ccproxy에 모델 오버라이드 요청

import json
import yaml
import os

AGENT_MODEL_MAP_PATH = os.path.join(
    os.path.dirname(__file__), '..', 'config', 'agent-model-map.yaml'
)

def get_model_for_agent(agent_name: str) -> str | None:
    """에이전트 이름으로 최적 모델 조회"""
    with open(AGENT_MODEL_MAP_PATH) as f:
        config = yaml.safe_load(f)

    for tier in config.values():
        if isinstance(tier, dict) and agent_name in tier:
            return tier[agent_name]
    return None  # 매핑 없으면 기본(GLM-5)

def on_subagent_start(event: dict):
    """SubagentStart hook에서 호출"""
    agent_name = event.get("agent_name", "")
    model = get_model_for_agent(agent_name)

    if model:
        # ccproxy에 다음 요청의 모델 오버라이드 설정
        # (ccproxy API 또는 환경변수 방식)
        print(json.dumps({
            "action": "route_override",
            "agent": agent_name,
            "model": model
        }))
```

### 5.5 작업 목록

| # | 작업 | 산출물 | 검증 방법 | 소요 |
|---|------|--------|----------|------|
| 5-1 | claude-code-router Custom Router JS 분석 | 설계 참고 문서 | 분석 문서 | 2시간 |
| 5-2 | `config/agent-model-map.yaml` 작성 | 28개 에이전트 매핑 | YAML 파싱 성공 | 1시간 |
| 5-3 | `hooks/subagent-router.py` 작성 | SubagentStart hook | 에이전트별 모델 확인 | 3시간 |
| 5-4 | ccproxy Custom Hook 연동 | 동적 모델 오버라이드 | 로그에서 라우팅 확인 | 3시간 |
| 5-5 | 통합 테스트: executor → Codex 라우팅 | OMC executor 호출 시 gpt-5.4-medium | 대시보드에서 확인 | 1시간 |
| 5-6 | 통합 테스트: designer → Gemini 라우팅 | OMC designer 호출 시 gemini | 대시보드에서 확인 | 1시간 |

---

## 전체 로드맵

```
Week 1                          Week 2                    Week 3
┌───────────────────────────┐  ┌──────────────────────┐  ┌──────────────────┐
│ Phase 1: ccproxy          │  │ Phase 2: 관찰성       │  │ Phase 4: Squad   │
│ ├─ 1-1~1-3: 설치/설정     │  │ ├─ 2-1~2-2: 설치     │  │ ├─ 설치/프리셋   │
│ ├─ 1-4~1-5: maestro.sh   │  │ ├─ 2-3~2-4: 이벤트   │  │ └─ 통합 테스트   │
│ ├─ 1-6~1-8: health/안전망 │  │ ├─ 2-5~2-6: hook병합 │  │                  │
│ └─ 1-9~1-11: 통합 테스트  │  │ └─ 2-7~2-8: 대시보드 │  │ Phase 5: CCR     │
│                           │  │                      │  │ ├─ 에이전트 매핑  │
│                           │  │ Phase 3: 동기화       │  │ └─ hook 구현     │
│                           │  │ ├─ 설치/설정          │  │                  │
│                           │  │ └─ 테스트             │  │ 문서 업데이트     │
└───────────────────────────┘  └──────────────────────┘  └──────────────────┘
```

### Phase별 예상 효과

| Phase | 개선 영역 | 정량적 기대 | 비용 영향 |
|-------|----------|------------|----------|
| 1. ccproxy | 라우팅 지능화 | 수동 `/code`, `/design` 호출 → 자동 분기 (사용자 개입 90%↓) | GLM-5 부담 70%→50%, Codex 25% 무료 활용 |
| 2. 관찰성 | 운영 가시성 | 모델별 호출·실패·비용 추적 (0% → 100%) | 병목 식별로 간접 비용 절감 |
| 3. 동기화 | 설정 관리 | 3개 도구 수동 동기화 → 자동 | 연간 수십 시간 절감 |
| 4. Squad | 병렬 실행 | 순차 → 3-4x 병렬 (대규모 한정) | 시간 절감 |
| 5. CCR 패턴 | 에이전트 라우팅 | 28개 에이전트별 최적 모델 자동 배정 | 모델별 강점 극대화 |

### 총 비용 구조 변화

| 항목 | 현재 | 적용 후 |
|------|------|--------|
| GLM-5 (ZAI) | $3/월 | $3/월 (고정, 부담↓) |
| Codex | 미사용 또는 수동 | 구독 내 25% 자동 활용 |
| 자체 서버 | 수동 스크립트 | ccproxy 자동 라우팅 |
| Claude 구독 | 미사용 | thinking 3%만 사용 |
| 추가 비용 | — | **$0** (모두 구독/무료) |

---

## 적용하지 않는 프로젝트와 사유

| 프로젝트 | Stars | 사유 |
|----------|-------|------|
| Symphony | — | Codex MCP 전용, 2개 모델만 지원, 큰 개선 아님 |
| obra/superpowers | 74K | 이미 OMC가 더 풍부한 기능 제공 |
| everything-claude-code | 68K | 이미 참조 중, 추가 적용 불필요 |
| plandex | 15K | 독립 에이전트, Maestro 아키텍처와 충돌 |
| mcp_agent_mail | 1.8K | OMC의 Agent tool이 이미 에이전트 간 통신 해결 |
| poml (MS) | 4.9K | 아직 초기 단계, 실용성 낮음 |
| cherry-studio | 41K | GUI 앱, CLI 기반 Maestro와 호환 불가 |
| claude-mem | 34K | 이미 OMC memory + auto-memory 사용 중 |

---

## 우선순위 권장

```
[필수] Phase 1 (ccproxy)     ← 가장 큰 ROI, 즉시 착수
[권장] Phase 2 (관찰성)       ← Phase 1 효과 검증에 필수
[유용] Phase 3 (동기화)       ← 낮은 난이도, 빠른 적용
[선택] Phase 4 (Squad)        ← 대규모 프로젝트에서만
[선택] Phase 5 (CCR 패턴)     ← Phase 1 안정화 후
```

**Phase 1만 적용해도** 6개 모델의 자동 라우팅이 가능해져,
사용자가 모델을 의식하지 않고 `claude-glm` 하나로 최적 모델을 자동 사용하게 됩니다.
