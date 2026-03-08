#!/bin/bash
# Demo 2: 모드 전환 - claude ↔ claude-glm
# asciinema로 녹화: asciinema rec --title "Maestro Mode Switch" demos/mode-switch.cast

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

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
echo " Maestro Claude Code - Mode Switch Demo"
echo "═══════════════════════════════════════════════"
echo

# 현재 모드 확인
sleep 1
type_text "$ cat .maestro-mode 2>/dev/null || echo '(기본값: claude)'"
cat "$PROJECT_DIR/.maestro-mode" 2>/dev/null || echo "(기본값: claude)"
echo

# GLM 모드로 전환
sleep 1
type_text "$ ./scripts/maestro.sh --mode glm"
echo "  모드 전환: claude → claude-glm (ZAI API)"
echo "  ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic"
echo "  모델: GLM-5 (opus/sonnet), GLM-4.5-Air (haiku)"
echo "  ✓ 전환 완료"
echo "  [비용 절감] ZAI Coding Plan \$3/월 적용"
echo

sleep 1
# claude 모드 복귀
type_text "$ ./scripts/maestro.sh --mode claude"
echo "  모드 전환: claude-glm → claude (Anthropic)"
echo "  ✓ 기본 모드 복귀"
echo

sleep 2
echo "═══════════════════════════════════════════════"
echo " 데모 완료 — 모드 전환으로 비용 절감"
echo "═══════════════════════════════════════════════"
