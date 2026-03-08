#!/bin/bash
# Maestro Claude Code - 상태 확인 스크립트

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# .env 로드
if [ -f "${PROJECT_DIR}/.env" ]; then
    set -a
    source "${PROJECT_DIR}/.env"
    set +a
fi

echo "=========================================="
echo "  Maestro Claude Code - System Status"
echo "=========================================="

# 1. Router 상태
echo -e "\n[Router]"
if curl -sf "http://127.0.0.1:3456/health" > /dev/null 2>&1; then
    echo "  claude-code-router: 🟢 Running (port 3456)"
else
    echo "  claude-code-router: 🔴 Stopped"
fi

# 2. vLLM 상태 (Cognit)
echo -e "\n[vLLM - Cognit]"
VLLM="${VLLM_ENDPOINT:?VLLM_ENDPOINT 미설정 - .env 확인}"
if curl -sf "${VLLM}/v1/models" > /dev/null 2>&1; then
    MODELS=$(curl -sf "${VLLM}/v1/models" 2>/dev/null | jq -r '.data[]? | "  Model: \(.id)"' 2>/dev/null)
    echo "  vLLM Server: 🟢 Running"
    echo "$MODELS"
else
    echo "  vLLM Server: 🔴 Unreachable (VPN 확인)"
fi

# 3. API 키 상태
echo -e "\n[API Keys]"
echo "  Anthropic: 🟢 Claude Code Auth (API 키 불필요)"
[ -n "${ZAI_API_KEY:-}" ] && echo "  Z.AI:      🟢 Set" || echo "  Z.AI:      🔴 Missing"
[ -n "${OPENAI_API_KEY:-}" ] && echo "  OpenAI:    🟢 Set" || echo "  OpenAI:    🔴 Missing"
[ -n "${TAVILY_API_KEY:-}" ] && echo "  Tavily:    🟢 Set" || echo "  Tavily:    🔴 Missing"

# 4. Docker 상태
echo -e "\n[Docker]"
if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "maestro-claude-code"; then
    echo "  Container: 🟢 Running"
else
    echo "  Container: ⚪ Not running (로컬 모드)"
fi

echo -e "\n=========================================="
