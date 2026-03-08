#!/bin/bash
# Maestro Router - 모델 독립적 AI 라우터
#
# 사용법:
#   ./scripts/maestro-route.sh --type code "로그인 API 구현"
#   ./scripts/maestro-route.sh --type design "대시보드 UI 컴포넌트"
#   ./scripts/maestro-route.sh --type analyze "400K 문서 분석"
#   ./scripts/maestro-route.sh --type localcode "간단한 함수 작성"
#   ./scripts/maestro-route.sh "자유 태스크"  # auto-detect
#
# 타입:
#   code       → codex -q (gpt-5.3-codex), 실패 시 qwen-coder fallback
#   design     → gemini (gemini-3.1-pro-preview)
#   analyze    → qwen35 (nexus, 400K context)
#   localcode  → qwen-coder (cognit, 20K context)
#   arch       → claude (Anthropic 구독)
#   (없으면)   → auto-detect 키워드 분석
#
# codex 요구사항:
#   - 공식 OpenAI API 키 (sk-proj-... 또는 sk-...) 필요
#   - OpenRouter 키 (sk-or-v1-...) 는 /v1/responses 미지원으로 불가
#   - OPENAI_API_KEY 환경변수 또는 ~/.config/codex/ 설정

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# .env 로드
if [ -f "${PROJECT_DIR}/.env" ]; then
    set -a; source "${PROJECT_DIR}/.env"; set +a
fi

# codex 사용 가능 여부 확인
# ChatGPT OAuth 로그인 또는 공식 OpenAI 키(sk-proj-...) 필요
codex_available() {
    if ! command -v codex &>/dev/null; then
        echo "[maestro-route] ⚠️  codex CLI 미설치" >&2
        return 1
    fi
    # ChatGPT OAuth 로그인 상태 확인
    local login_status
    login_status=$(env -u OPENAI_API_KEY -u OPENAI_BASE_URL codex login status 2>&1 || true)
    if echo "$login_status" | grep -qi "logged in"; then
        return 0  # OAuth 로그인 완료
    fi
    # API 키 방식: 공식 OpenAI 키인지 확인
    local key="${OPENAI_API_KEY:-}"
    if [[ -n "$key" && "$key" != sk-or-v1-* ]]; then
        return 0  # 공식 OpenAI 키 사용
    fi
    echo "[maestro-route] ⚠️  codex 인증 없음 (OAuth 미로그인, 공식 키 미설정)" >&2
    echo "[maestro-route]    'codex login' 또는 OPENAI_API_KEY=sk-proj-... 설정 필요" >&2
    return 1
}

# codex 실행 (claude-imple-skills 패턴: codex -q "...")
# OPENAI_API_KEY/OPENAI_BASE_URL 언셋 → ChatGPT OAuth 사용
run_codex() {
    local task="$1"
    env -u OPENAI_API_KEY -u OPENAI_BASE_URL codex --yolo "$task"
}

# qwen-coder fallback 실행
run_qwen_coder() {
    local task="$1"
    echo "[maestro-route] ⚡ qwen-coder fallback (cognit, 20K)" >&2
    "${SCRIPT_DIR}/qwen-coder-cli.sh" "$task"
}

# 인자 파싱
TYPE=""
TASK=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --type|-t)
            TYPE="$2"
            shift 2
            ;;
        --help|-h)
            sed -n '3,20p' "$0"
            exit 0
            ;;
        *)
            TASK="${TASK:+$TASK }$1"
            shift
            ;;
    esac
done

if [ -z "$TASK" ]; then
    echo "사용법: $0 [--type TYPE] \"태스크 설명\"" >&2
    exit 1
fi

# Auto-detect: 타입 미지정 시 키워드로 판단
if [ -z "$TYPE" ]; then
    TASK_LOWER=$(echo "$TASK" | tr '[:upper:]' '[:lower:]')
    if echo "$TASK_LOWER" | grep -qE "ui|디자인|design|화면|컴포넌트|component|css|style|frontend|프론트|레이아웃|layout"; then
        TYPE="design"
    elif echo "$TASK_LOWER" | grep -qE "아키텍처|architecture|설계|시스템|system|구조|전략|strategy|계획|planning"; then
        TYPE="arch"
    elif echo "$TASK_LOWER" | grep -qE "분석|analyze|문서|400k|대용량|large|long|요약|summary"; then
        TYPE="analyze"
    elif echo "$TASK_LOWER" | grep -qE "간단|simple|quick|짧은|함수|function|snippet|작은"; then
        TYPE="localcode"
    else
        TYPE="code"
    fi
    echo "[maestro-route] auto-detect: --type $TYPE" >&2
fi

# 라우팅 실행
case "$TYPE" in
    code|codex)
        # codex exec: Codex 구독 필요 (현재 미구독)
        # codex --yolo: TTY 필요 (비인터랙티브 불가)
        # → qwen-coder로 처리 (cognit, 20K context)
        echo "[maestro-route] ⚡ qwen-coder (cognit) 로 라우팅 [codex 구독 시 전환 가능]" >&2
        run_qwen_coder "$TASK"
        ;;
    design|gemini)
        echo "[maestro-route] 💎 gemini (gemini-3.1-pro-preview) 로 라우팅" >&2
        echo "$TASK" | gemini --output-format text
        ;;
    analyze|qwen35|large)
        echo "[maestro-route] 🔮 Qwen3.5-122B (nexus, 400K) 로 라우팅" >&2
        "${SCRIPT_DIR}/qwen35-cli.sh" "$TASK"
        ;;
    localcode|qwen-coder|local)
        echo "[maestro-route] ⚡ Qwen3-Coder-30B (cognit, 20K) 로 라우팅" >&2
        "${SCRIPT_DIR}/qwen-coder-cli.sh" "$TASK"
        ;;
    arch|claude|anthropic)
        echo "[maestro-route] 🧠 Claude (Anthropic 구독) 로 라우팅" >&2
        echo "  [참고] 현재 claude-glm 세션 내에서 claude 직접 실행은 불가합니다." >&2
        echo "  claude 구독 창을 별도로 열어 실행하세요." >&2
        exit 1
        ;;
    glm|claude-glm)
        echo "[maestro-route] 🌐 GLM-5 (ZAI) - 현재 세션에서 직접 처리" >&2
        echo "$TASK"
        ;;
    *)
        echo "[maestro-route] 알 수 없는 타입: $TYPE" >&2
        echo "  사용 가능: code, design, analyze, localcode, arch" >&2
        exit 1
        ;;
esac
