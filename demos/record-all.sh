#!/bin/bash
# 모든 데모를 asciinema로 녹화하는 마스터 스크립트
#
# 사용법:
#   ./demos/record-all.sh          # 전체 녹화
#   ./demos/record-all.sh health   # 헬스체크만
#   ./demos/record-all.sh mode     # 모드 전환만
#   ./demos/record-all.sh routing  # 라우팅만
#   ./demos/record-all.sh orch     # 오케스트레이션만

set -euo pipefail
DEMOS_DIR="$(cd "$(dirname "$0")" && pwd)"
CAST_DIR="$DEMOS_DIR/casts"
mkdir -p "$CAST_DIR"

chmod +x "$DEMOS_DIR"/demo-*.sh

record() {
    local name="$1"
    local title="$2"
    local script="$3"
    local cast="$CAST_DIR/${name}.cast"

    echo "🎬 녹화 시작: $title"
    asciinema rec \
        --title "$title" \
        --command "bash $script" \
        --idle-time-limit 2 \
        --overwrite \
        "$cast"
    echo "✓ 저장: $cast"
    echo
}

TARGET="${1:-all}"

case "$TARGET" in
    health|all)
        record "health-check" \
               "Maestro - Health Check" \
               "$DEMOS_DIR/demo-health-check.sh"
        ;;&
    mode|all)
        record "mode-switch" \
               "Maestro - Mode Switch (claude ↔ claude-glm)" \
               "$DEMOS_DIR/demo-mode-switch.sh"
        ;;&
    routing|all)
        record "multi-ai-routing" \
               "Maestro - Multi-AI Routing" \
               "$DEMOS_DIR/demo-multi-ai-routing.sh"
        ;;&
    orch|all)
        record "orchestrate" \
               "Maestro - Orchestration Wave" \
               "$DEMOS_DIR/demo-orchestrate.sh"
        ;;
esac

echo "═══════════════════════════════════════════════"
echo "  녹화 완료! cast 파일 위치: $CAST_DIR/"
echo
echo "  재생 방법:"
echo "    asciinema play demos/casts/health-check.cast"
echo "    asciinema play demos/casts/mode-switch.cast"
echo "    asciinema play demos/casts/multi-ai-routing.cast"
echo "    asciinema play demos/casts/orchestrate.cast"
echo
echo "  공유 방법:"
echo "    asciinema upload demos/casts/<name>.cast"
echo "    → asciinema.org 링크 생성됨"
echo "═══════════════════════════════════════════════"
