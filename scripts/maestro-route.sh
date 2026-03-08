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
#   code       → codex (gpt-5.3-codex)
#   design     → gemini (gemini-3.1-pro-preview)
#   analyze    → qwen35 (nexus, 400K context)
#   localcode  → qwen-coder (cognit, 20K context)
#   arch       → claude (Anthropic 구독)
#   (없으면)   → auto-detect 키워드 분석

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# .env 로드
if [ -f "${PROJECT_DIR}/.env" ]; then
    set -a; source "${PROJECT_DIR}/.env"; set +a
fi

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
        echo "[maestro-route] 🤖 codex (gpt-5.3-codex) 로 라우팅" >&2
        codex exec "$TASK"
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
