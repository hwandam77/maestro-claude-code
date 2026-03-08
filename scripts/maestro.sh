#!/bin/bash
# Maestro Claude Code - GLM-5 (ZAI) 모드 런처
#
# 사용법:
#   ./scripts/maestro.sh           → ZAI(GLM-5) 모드로 claude 실행
#   ./scripts/maestro.sh status    → 설정 확인
#
# Claude Code 구독 모드는 그냥 'claude' 실행

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# .env에서 ZAI_API_KEY 로드
if [ -f "${PROJECT_DIR}/.env" ]; then
    set -a; source "${PROJECT_DIR}/.env"; set +a
fi
: "${ZAI_API_KEY:?ZAI_API_KEY 미설정. .env 파일 확인}"

case "${1:-run}" in
    status)
        echo "Maestro Claude Code"
        echo "==================="
        echo "  GLM-5 모드:  ZAI Coding Plan"
        echo "  Endpoint:    https://api.z.ai/api/anthropic"
        echo "  비용:        ~\$3/월 (구독제)"
        echo ""
        echo "  실행: ./scripts/maestro.sh"
        echo "  구독: claude (환경변수 없이)"
        ;;
    *)
        echo "[maestro] GLM-5 (ZAI) 모드"
        ANTHROPIC_BASE_URL="https://api.z.ai/api/anthropic" \
        ANTHROPIC_AUTH_TOKEN="${ZAI_API_KEY}" \
        exec claude "$@"
        ;;
esac
