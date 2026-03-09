#!/bin/bash
# Maestro Claude Code - GLM-5 (ZAI) 모드 런처
#
# 변경 전: claude-glm → ZAI API 직접
# 변경 후: claude-glm → LiteLLM Proxy → ZAI API (+ 조건부 에스컬레이션)
#
# 사용법:
#   ./scripts/maestro.sh           → 프록시 경유 GLM-5 모드 (기본)
#   ./scripts/maestro.sh direct    → ZAI API 직접 (프록시 우회)
#   ./scripts/maestro.sh status    → 설정 및 프록시 상태 확인

set -euo pipefail

# 심볼릭 링크를 따라 실제 스크립트 경로 해석 (claude-glm symlink 지원)
REAL_SCRIPT="$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$0")"
SCRIPT_DIR="$(cd "$(dirname "$REAL_SCRIPT")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CCPROXY_PORT="${CCPROXY_PORT:-4000}"
CONFIG_FULL="${PROJECT_DIR}/config/ccproxy.yaml"
CONFIG_FALLBACK="${PROJECT_DIR}/config/litellm-fallback.yaml"
PID_FILE="${PROJECT_DIR}/logs/ccproxy/proxy.pid"
LOG_FILE="${PROJECT_DIR}/logs/ccproxy/proxy.log"

# .env에서 API 키 로드
if [ -f "${PROJECT_DIR}/.env" ]; then
    set -a; source "${PROJECT_DIR}/.env"; set +a
fi
: "${ZAI_API_KEY:?ZAI_API_KEY 미설정. .env 파일 확인}"

export LITELLM_MASTER_KEY="${LITELLM_MASTER_KEY:-maestro-local-key}"

# ─── 함수 정의 ───

proxy_is_running() {
    lsof -ti:${CCPROXY_PORT} > /dev/null 2>&1
}

detect_config() {
    # Tailscale 연결 + 자체 서버 도달 가능 여부 확인
    if tailscale status --json 2>/dev/null | python3 -c "
import sys, json
d = json.load(sys.stdin)
exit(0 if d.get('Self', {}).get('Online') else 1)
" 2>/dev/null; then
        # nexus 또는 cognit 응답 확인
        if tailscale ping --c 1 --timeout 3s 100.124.117.46 > /dev/null 2>&1 || \
           tailscale ping --c 1 --timeout 3s 100.121.138.74 > /dev/null 2>&1; then
            echo "full"
            return 0
        fi
        echo "fallback"
        return 0
    fi
    echo "fallback"
}

start_proxy() {
    if proxy_is_running; then
        echo "[maestro] 프록시 이미 실행 중 (port ${CCPROXY_PORT})"
        return 0
    fi

    mkdir -p "$(dirname "$LOG_FILE")"

    local mode
    mode=$(detect_config)

    local config_file
    if [ "$mode" = "full" ]; then
        config_file="$CONFIG_FULL"
        echo "[maestro] Tailscale 연결 → 자체 서버 포함 전체 라우팅"
    else
        config_file="$CONFIG_FALLBACK"
        echo "[maestro] Tailscale 미연결 → 클라우드 모델만 사용"
        echo "  hint: 'tailscale up' 으로 연결하면 자체 서버 활성화"
    fi

    nohup litellm --config "$config_file" \
                  --port ${CCPROXY_PORT} \
                  > "$LOG_FILE" 2>&1 &
    local pid=$!
    echo $pid > "$PID_FILE"

    # 준비 대기 (최대 15초)
    for i in $(seq 1 15); do
        sleep 1
        if proxy_is_running; then
            echo "[maestro] 프록시 준비 완료 (PID: ${pid}, port: ${CCPROXY_PORT})"
            return 0
        fi
    done

    echo "[maestro] 경고: 프록시 시작 실패, ZAI API 직접 연결로 fallback"
    rm -f "$PID_FILE"
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
    echo "  진입점:    claude-glm (ZAI Coding Plan)"
    echo "  비용:      ~\$3/월 (구독제)"
    echo ""

    if proxy_is_running; then
        local pid=""
        [ -f "$PID_FILE" ] && pid=" (PID: $(cat "$PID_FILE"))"
        echo "  프록시:    ✅ 실행 중${pid} (port ${CCPROXY_PORT})"
    else
        echo "  프록시:    ❌ 미실행"
        echo "  시작:      ./scripts/ccproxy-start.sh start"
    fi

    if tailscale status --json 2>/dev/null | python3 -c "
import sys, json
d = json.load(sys.stdin)
exit(0 if d.get('Self', {}).get('Online') else 1)
" 2>/dev/null; then
        echo "  Tailscale: ✅ 연결됨"
        tailscale ping --c 1 --timeout 3s 100.124.117.46 > /dev/null 2>&1 \
            && echo "  nexus:     ✅ 응답 (Qwen3.5-122B)" \
            || echo "  nexus:     ❌ 미응답"
        tailscale ping --c 1 --timeout 3s 100.121.138.74 > /dev/null 2>&1 \
            && echo "  cognit:    ✅ 응답 (Qwen3-Coder-30B)" \
            || echo "  cognit:    ❌ 미응답"
    else
        echo "  Tailscale: ❌ 미연결 (자체 모델 비활성)"
    fi

    echo ""
    echo "  명령어:"
    echo "    ./scripts/maestro.sh           → 프록시 모드 실행"
    echo "    ./scripts/maestro.sh direct    → ZAI API 직접 연결"
    echo "    ./scripts/ccproxy-start.sh start/stop/status"
    echo "    ./scripts/ccproxy-health.sh    → 프록시 + 백엔드 점검"
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
        if start_proxy; then
            run_with_proxy "$@"
        else
            echo "[maestro] 프록시 fallback → ZAI API 직접 연결"
            run_direct "$@"
        fi
        ;;
esac
