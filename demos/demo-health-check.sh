#!/bin/bash
# Demo 1: 헬스체크 - 서버 상태 확인
# asciinema로 녹화: asciinema rec --title "Maestro Health Check" demos/health-check.cast

set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# 타이핑 효과
type_text() {
    local text="$1"
    local delay="${2:-0.05}"
    for ((i=0; i<${#text}; i++)); do
        printf "%s" "${text:$i:1}"
        sleep "$delay"
    done
    echo
}

echo
echo "═══════════════════════════════════════════════"
echo " Maestro Claude Code - Health Check Demo"
echo "═══════════════════════════════════════════════"
echo
sleep 1

type_text "$ ./scripts/health-check.sh"
sleep 0.5

"$PROJECT_DIR/scripts/health-check.sh"

sleep 2
echo
echo "═══════════════════════════════════════════════"
echo " 데모 완료 — 전체 서버 상태 확인"
echo "═══════════════════════════════════════════════"
