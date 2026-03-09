#!/bin/bash
# Maestro Claude Code - LiteLLM Proxy 독립 시작/종료/상태
#
# 사용법:
#   ./scripts/ccproxy-start.sh start   → 프록시 시작
#   ./scripts/ccproxy-start.sh stop    → 프록시 종료
#   ./scripts/ccproxy-start.sh status  → 상태 확인
#   ./scripts/ccproxy-start.sh restart → 재시작

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CCPROXY_PORT="${CCPROXY_PORT:-4000}"
PID_FILE="${PROJECT_DIR}/logs/ccproxy/proxy.pid"
LOG_FILE="${PROJECT_DIR}/logs/ccproxy/proxy.log"
CONFIG_FULL="${PROJECT_DIR}/config/ccproxy.yaml"
CONFIG_FALLBACK="${PROJECT_DIR}/config/litellm-fallback.yaml"

# .env 로드
if [ -f "${PROJECT_DIR}/.env" ]; then
    set -a; source "${PROJECT_DIR}/.env"; set +a
fi

# LITELLM_MASTER_KEY: 설정 시 DB 인증 강제 → localhost 전용이므로 비활성화
unset LITELLM_MASTER_KEY

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

is_running() {
    if [ -f "$PID_FILE" ]; then
        local pid
        pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            return 0
        fi
    fi
    # PID 파일 없어도 포트로 확인
    lsof -ti:${CCPROXY_PORT} > /dev/null 2>&1
}

detect_config() {
    # Tailscale 연결 + 서버 도달 가능 여부 확인
    if tailscale status --json 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); exit(0 if d.get('Self',{}).get('Online') else 1)" 2>/dev/null; then
        # nexus ping 테스트 (Tailscale IP)
        if tailscale ping --c 1 --timeout 3s 100.124.117.46 > /dev/null 2>&1; then
            echo "$CONFIG_FULL"
            return 0
        fi
        # cognit ping 테스트
        if tailscale ping --c 1 --timeout 3s 100.121.138.74 > /dev/null 2>&1; then
            echo "$CONFIG_FULL"
            return 0
        fi
    fi
    echo "$CONFIG_FALLBACK"
}

do_start() {
    if is_running; then
        printf "${GREEN}이미 실행 중${NC} (port ${CCPROXY_PORT})\n"
        return 0
    fi

    mkdir -p "$(dirname "$LOG_FILE")"

    local config_file
    config_file=$(detect_config)
    local config_name
    config_name=$(basename "$config_file")

    printf "[ccproxy] 시작 중... (설정: ${YELLOW}${config_name}${NC})\n"

    if [ "$config_file" = "$CONFIG_FULL" ]; then
        printf "  자체 서버: ${GREEN}활성${NC}\n"
    else
        printf "  자체 서버: ${YELLOW}비활성${NC} (Tailscale 미연결 또는 서버 미응답)\n"
    fi

    # 대시보드 시작 (선택, --with-dashboard 플래그 또는 WITH_DASHBOARD=true)
    if [[ "${WITH_DASHBOARD:-}" == "true" ]]; then
        cd "${PROJECT_DIR}/tools/observability" && bun run start >> "${PROJECT_DIR}/logs/dashboard.log" 2>&1 &
        printf "  대시보드: ${GREEN}시작됨${NC} (port 3456, http://localhost:3456)\n"
        cd "${PROJECT_DIR}"
    fi

    # LiteLLM Proxy 시작 (PYTHONPATH: tools.litellm_callback import용)
    export PYTHONPATH="${PROJECT_DIR}:${PYTHONPATH:-}"
    nohup litellm --config "$config_file" \
                  --port ${CCPROXY_PORT} \
                  --detailed_debug \
                  > "$LOG_FILE" 2>&1 &
    local pid=$!
    echo $pid > "$PID_FILE"

    # 준비 대기 (최대 15초)
    printf "  준비 대기 중"
    for i in $(seq 1 15); do
        sleep 1
        printf "."
        if lsof -ti:${CCPROXY_PORT} > /dev/null 2>&1; then
            printf "\n${GREEN}완료${NC} (PID: ${pid}, port: ${CCPROXY_PORT})\n"
            return 0
        fi
    done
    printf "\n${RED}경고: 15초 내 시작 실패. 로그 확인: ${LOG_FILE}${NC}\n"
    return 1
}

do_stop() {
    if ! is_running; then
        printf "${YELLOW}실행 중이 아님${NC}\n"
        return 0
    fi

    # PID 파일로 종료
    if [ -f "$PID_FILE" ]; then
        local pid
        pid=$(cat "$PID_FILE")
        kill "$pid" 2>/dev/null && printf "${GREEN}종료됨${NC} (PID: ${pid})\n"
        rm -f "$PID_FILE"
    fi

    # 포트 점유 프로세스 강제 종료
    local port_pid
    port_pid=$(lsof -ti:${CCPROXY_PORT} 2>/dev/null) || true
    if [ -n "$port_pid" ]; then
        kill -9 $port_pid 2>/dev/null || true
    fi
}

do_status() {
    echo "================================"
    echo "  ccproxy (LiteLLM Proxy) 상태"
    echo "================================"
    echo ""

    if is_running; then
        local pid=""
        [ -f "$PID_FILE" ] && pid=$(cat "$PID_FILE")
        printf "  상태:   ${GREEN}실행 중${NC}"
        [ -n "$pid" ] && printf " (PID: ${pid})"
        printf "\n"
        printf "  포트:   ${CCPROXY_PORT}\n"
        printf "  로그:   ${LOG_FILE}\n"
    else
        printf "  상태:   ${RED}중지됨${NC}\n"
        printf "  시작:   ./scripts/ccproxy-start.sh start\n"
    fi

    echo ""

    # Tailscale 상태
    if tailscale status --json 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); exit(0 if d.get('Self',{}).get('Online') else 1)" 2>/dev/null; then
        printf "  Tailscale: ${GREEN}연결됨${NC}\n"
        tailscale ping --c 1 --timeout 3s 100.124.117.46 > /dev/null 2>&1 \
            && printf "  nexus:     ${GREEN}✅ 응답${NC} (100.124.117.46:8080)\n" \
            || printf "  nexus:     ${RED}❌ 미응답${NC}\n"
        tailscale ping --c 1 --timeout 3s 100.121.138.74 > /dev/null 2>&1 \
            && printf "  cognit:    ${GREEN}✅ 응답${NC} (100.121.138.74:8000)\n" \
            || printf "  cognit:    ${RED}❌ 미응답${NC}\n"
    else
        printf "  Tailscale: ${RED}미연결${NC}\n"
        printf "  hint:      'tailscale up' 으로 연결\n"
    fi

    echo ""
}

case "${1:-status}" in
    start)   do_start ;;
    stop)    do_stop ;;
    restart) do_stop; sleep 1; do_start ;;
    status)  do_status ;;
    *)
        echo "사용법: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac
