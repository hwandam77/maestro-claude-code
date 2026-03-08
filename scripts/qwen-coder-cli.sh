#!/bin/bash
# Qwen3-Coder-30B CLI wrapper (cognit:8000, vLLM)
#
# OpenAI 호환 API를 CLI처럼 호출하는 래퍼 스크립트
# stdin 또는 인자로 프롬프트를 받아 응답 텍스트를 stdout으로 출력
#
# 사용법:
#   echo "코드 생성 요청" | ./scripts/qwen-coder-cli.sh
#   ./scripts/qwen-coder-cli.sh "코드 생성 요청"
#   ./scripts/qwen-coder-cli.sh -s "시스템 프롬프트" "코드 생성 요청"
#
# 제약: context 16K tokens, 동시 요청 1개 권장

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# .env에서 서버 설정 로드
if [ -f "${PROJECT_DIR}/.env" ]; then
    set -a; source "${PROJECT_DIR}/.env"; set +a
fi

COGNIT_HOST="${COGNIT_HOST:-100.89.224.48}"
COGNIT_PORT="${COGNIT_PORT:-8000}"
COGNIT_URL="http://${COGNIT_HOST}:${COGNIT_PORT}/v1/chat/completions"
TIMEOUT="${QWEN_CODER_TIMEOUT:-120}"

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
        echo "사용법: echo '요청' | $0  또는  $0 '요청'" >&2
        exit 1
    fi
    PROMPT="$(cat)"
fi

# health check
if ! curl -sf --max-time 5 "http://${COGNIT_HOST}:${COGNIT_PORT}/v1/models" > /dev/null 2>&1; then
    echo "[qwen-coder-cli] cognit 서버 접근 불가 (${COGNIT_HOST}:${COGNIT_PORT})" >&2
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

# API 호출 (vLLM은 모델명을 그대로 전달)
RESPONSE=$(curl -sf --max-time "$TIMEOUT" "$COGNIT_URL" \
    -H "Content-Type: application/json" \
    -d "$(jq -n --argjson msgs "$MESSAGES" \
        '{model:"Qwen3-Coder-30B-A3B-Instruct",messages:$msgs,temperature:0.3,max_tokens:4096}')" \
    2>/dev/null)

if [ $? -ne 0 ] || [ -z "$RESPONSE" ]; then
    echo "[qwen-coder-cli] API 호출 실패" >&2
    exit 1
fi

# 응답 텍스트 추출
echo "$RESPONSE" | jq -r '.choices[0].message.content // empty'
