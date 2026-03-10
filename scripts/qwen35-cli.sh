#!/bin/bash
# Qwen3.5-122B CLI wrapper (nexus:8080, llama-server)
#
# OpenAI 호환 API를 CLI처럼 호출하는 래퍼 스크립트
# stdin 또는 인자로 프롬프트를 받아 응답 텍스트를 stdout으로 출력
#
# 사용법:
#   echo "질문" | ./scripts/qwen35-cli.sh
#   ./scripts/qwen35-cli.sh "질문"
#   ./scripts/qwen35-cli.sh -s "시스템 프롬프트" "질문"

set -euo pipefail

# 심볼릭 링크를 따라 실제 스크립트 경로 해석
REAL_SCRIPT="$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$0")"
SCRIPT_DIR="$(cd "$(dirname "$REAL_SCRIPT")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# .env에서 서버 설정 로드
if [ -f "${PROJECT_DIR}/.env" ]; then
    set -a; source "${PROJECT_DIR}/.env"; set +a
fi

NEXUS_HOST="${NEXUS_HOST:-100.124.117.46}"
NEXUS_PORT="${NEXUS_PORT:-8080}"
NEXUS_URL="http://${NEXUS_HOST}:${NEXUS_PORT}/v1/chat/completions"
TIMEOUT="${QWEN35_TIMEOUT:-120}"

# 인자 파싱
SYSTEM_PROMPT=""
PROMPT=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        -s|--system)
            SYSTEM_PROMPT="$2"
            shift 2
            ;;
        *)
            PROMPT="$1"
            shift
            ;;
    esac
done

# stdin에서 프롬프트 읽기 (인자가 없을 때)
if [ -z "$PROMPT" ]; then
    if [ -t 0 ]; then
        echo "사용법: echo '질문' | $0  또는  $0 '질문'" >&2
        exit 1
    fi
    PROMPT="$(cat)"
fi

# health check
if ! curl -sf --max-time 5 "http://${NEXUS_HOST}:${NEXUS_PORT}/v1/models" > /dev/null 2>&1; then
    echo "[qwen35-cli] nexus 서버 접근 불가 (${NEXUS_HOST}:${NEXUS_PORT})" >&2
    exit 1
fi

# 메시지 구성
if [ -n "$SYSTEM_PROMPT" ]; then
    MESSAGES=$(jq -n --arg sys "$SYSTEM_PROMPT" --arg usr "$PROMPT" \
        '[{"role":"system","content":$sys},{"role":"user","content":$usr}]')
else
    MESSAGES=$(jq -n --arg usr "$PROMPT" \
        '[{"role":"user","content":$usr}]')
fi

# API 호출
RESPONSE=$(curl -sf --max-time "$TIMEOUT" "$NEXUS_URL" \
    -H "Content-Type: application/json" \
    -d "$(jq -n --argjson msgs "$MESSAGES" \
        '{model:"Qwen3.5-122B",messages:$msgs,temperature:0.7,max_tokens:4096}')" \
    2>/dev/null)

if [ $? -ne 0 ] || [ -z "$RESPONSE" ]; then
    echo "[qwen35-cli] API 호출 실패" >&2
    exit 1
fi

# 응답 텍스트 추출
echo "$RESPONSE" | jq -r '.choices[0].message.content // empty'
