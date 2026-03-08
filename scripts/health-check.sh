#!/bin/bash
# Maestro Claude Code - 서버 Health Check
#
# nexus/cognit 서버 상태를 점검하고 결과를 출력
#
# 사용법:
#   ./scripts/health-check.sh          → 전체 점검
#   ./scripts/health-check.sh nexus    → nexus만 점검
#   ./scripts/health-check.sh cognit   → cognit만 점검

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# .env 로드
if [ -f "${PROJECT_DIR}/.env" ]; then
    set -a; source "${PROJECT_DIR}/.env"; set +a
fi

NEXUS_HOST="${NEXUS_HOST:-100.64.189.120}"
NEXUS_PORT="${NEXUS_PORT:-8080}"
COGNIT_HOST="${COGNIT_HOST:-100.89.224.48}"
COGNIT_PORT="${COGNIT_PORT:-8000}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

check_server() {
    local name="$1"
    local host="$2"
    local port="$3"
    local url="http://${host}:${port}/v1/models"

    printf "%-12s " "${name}:"

    # ping 체크
    if ! ping -c 1 -W 2 "$host" > /dev/null 2>&1; then
        printf "${RED}UNREACHABLE${NC} (ping failed - VPN 확인)\n"
        return 1
    fi

    # API 체크
    local response
    response=$(curl -sf --max-time 10 "$url" 2>/dev/null) || {
        printf "${YELLOW}DEGRADED${NC} (ping OK, API 응답 없음 - 서비스 확인)\n"
        return 1
    }

    # 모델 정보 추출
    local model_id
    model_id=$(echo "$response" | jq -r '.data[0].id // "unknown"' 2>/dev/null)

    printf "${GREEN}HEALTHY${NC} (model: ${model_id})\n"
    return 0
}

check_cli() {
    local name="$1"
    local cmd="$2"

    printf "%-12s " "${name}:"

    if command -v "$cmd" > /dev/null 2>&1; then
        local path
        path=$(command -v "$cmd")
        printf "${GREEN}OK${NC} (${path})\n"
    else
        printf "${RED}NOT FOUND${NC}\n"
    fi
}

echo "================================"
echo "  Maestro Health Check"
echo "================================"
echo ""

TARGET="${1:-all}"

if [ "$TARGET" = "all" ] || [ "$TARGET" = "cli" ]; then
    echo "[CLI Tools]"
    check_cli "claude" "claude"
    check_cli "codex" "codex"
    check_cli "gemini" "gemini"
    check_cli "claude-glm" "claude-glm"
    echo ""
fi

if [ "$TARGET" = "all" ] || [ "$TARGET" = "nexus" ]; then
    echo "[Self-hosted Servers]"
    check_server "nexus" "$NEXUS_HOST" "$NEXUS_PORT"
fi

if [ "$TARGET" = "all" ] || [ "$TARGET" = "cognit" ]; then
    [ "$TARGET" = "cognit" ] && echo "[Self-hosted Servers]"
    check_server "cognit" "$COGNIT_HOST" "$COGNIT_PORT"
fi

echo ""
echo "================================"
