#!/bin/bash
# Maestro Claude Code - ccproxy + 백엔드 모델 Health Check
#
# 사용법:
#   ./scripts/ccproxy-health.sh        → 전체 점검
#   ./scripts/ccproxy-health.sh proxy  → 프록시만 점검
#   ./scripts/ccproxy-health.sh models → 백엔드 모델만 점검

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CCPROXY_PORT="${CCPROXY_PORT:-4000}"

if [ -f "${PROJECT_DIR}/.env" ]; then
    set -a; source "${PROJECT_DIR}/.env"; set +a
fi

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

check_proxy() {
    printf "%-16s " "litellm proxy:"
    if lsof -ti:${CCPROXY_PORT} > /dev/null 2>&1; then
        printf "${GREEN}RUNNING${NC} (port ${CCPROXY_PORT})\n"
        return 0
    else
        printf "${RED}STOPPED${NC}\n"
        printf "  → 시작: ./scripts/ccproxy-start.sh start\n"
        return 1
    fi
}

check_zai() {
    printf "%-16s " "ZAI GLM-5:"
    if [ -z "${ZAI_API_KEY:-}" ]; then
        printf "${RED}NO API KEY${NC}\n"
        return 1
    fi
    printf "${GREEN}API KEY OK${NC}\n"
}

check_tailscale_server() {
    local name="$1"
    local ts_ip="$2"
    local api_host="$3"
    local api_port="$4"

    printf "%-16s " "${name}:"

    # Tailscale ping 테스트
    if ! tailscale ping --c 1 --timeout 3s "$ts_ip" > /dev/null 2>&1; then
        printf "${RED}UNREACHABLE${NC} (Tailscale ping 실패)\n"
        return 1
    fi

    # API 응답 테스트 (Python으로 curl 대체)
    local result
    result=$(python3 -c "
import urllib.request, json, sys
try:
    req = urllib.request.Request('http://${api_host}:${api_port}/v1/models', headers={'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=10) as r:
        data = json.load(r)
        models = [m['id'] for m in data.get('data', [])][:2]
        print('OK:' + ','.join(models))
except Exception as e:
    print('FAIL:' + str(e)[:50])
" 2>&1)

    if [[ "$result" == OK:* ]]; then
        local model_info="${result#OK:}"
        printf "${GREEN}HEALTHY${NC} (${model_info})\n"
    else
        local err="${result#FAIL:}"
        printf "${YELLOW}DEGRADED${NC} (ping OK, API 실패: ${err})\n"
    fi
}

check_cloud_key() {
    local name="$1"
    local key_var="$2"
    printf "%-16s " "${name}:"
    local key="${!key_var:-}"
    if [ -n "$key" ]; then
        printf "${GREEN}API KEY OK${NC}\n"
    else
        printf "${YELLOW}NO KEY${NC} (${key_var} 미설정)\n"
    fi
}

TARGET="${1:-all}"

echo "=================================="
echo "  Maestro ccproxy Health Check"
echo "=================================="
echo ""

if [ "$TARGET" = "all" ] || [ "$TARGET" = "proxy" ]; then
    echo "[프록시]"
    check_proxy
    check_zai
    echo ""
fi

if [ "$TARGET" = "all" ] || [ "$TARGET" = "models" ]; then
    echo "[자체 서버]"
    # nexus: Tailscale IP 100.124.117.46, API IP 100.64.189.120
    check_tailscale_server "nexus(Qwen3.5)" "100.124.117.46" "100.64.189.120" "8080"
    # cognit: Tailscale IP 100.121.138.74
    check_tailscale_server "cognit(QwenCoder)" "100.121.138.74" "100.121.138.74" "8000"
    echo ""

    echo "[클라우드 모델]"
    check_cloud_key "Gemini" "GOOGLE_API_KEY"
    check_cloud_key "Codex/OpenAI" "OPENAI_API_KEY"
    check_cloud_key "Claude" "ANTHROPIC_API_KEY"
    echo ""
fi

echo "=================================="
