#!/bin/bash
# Demo 3: 멀티 AI 라우팅 흐름 시각화
# asciinema로 녹화: asciinema rec --title "Maestro Multi-AI Routing" demos/multi-ai-routing.cast

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
echo " Maestro Claude Code - Multi-AI Routing Demo"
echo "═══════════════════════════════════════════════"
echo

# routing.config.yaml 확인
sleep 1
type_text "$ cat .claude/routing.config.yaml | head -30"
sleep 0.3
cat << 'YAML'
defaults:
  primary: claude
  fallback_enabled: true

roles:
  architect:
    primary: claude-opus
    description: "시스템 설계, 아키텍처 결정"

  code:
    primary: codex
    description: "코드 생성, 리뷰, 테스트"

  design:
    primary: gemini
    description: "UI/UX, 디자인, 멀티모달"

  large-context:
    primary: qwen35-cli.sh
    description: "대용량 컨텍스트 (400K)"

  code-local:
    primary: qwen-coder-cli.sh
    description: "경량 코드 생성 (20K)"
YAML
echo

# 라우팅 흐름 시각화
sleep 1
type_text "$ # 라우팅 흐름 예시"
sleep 0.5

echo
echo "  태스크 입력: '로그인 API 구현'"
sleep 0.5
echo "  ┌─────────────────────────────────────────┐"
echo "  │  routing.config.yaml 분석 중...         │"
echo "  │  task_type: code → primary: codex       │"
echo "  └─────────────────────────────────────────┘"
sleep 0.5
echo "  → gpt-5.3-codex 로 라우팅"
echo

sleep 1
echo "  태스크 입력: '대시보드 UI 디자인'"
sleep 0.5
echo "  ┌─────────────────────────────────────────┐"
echo "  │  routing.config.yaml 분석 중...         │"
echo "  │  task_type: design → primary: gemini    │"
echo "  └─────────────────────────────────────────┘"
sleep 0.5
echo "  → gemini-3.1-pro-preview 로 라우팅"
echo

sleep 1
echo "  태스크 입력: '400K 문서 분석'"
sleep 0.5
echo "  ┌─────────────────────────────────────────┐"
echo "  │  routing.config.yaml 분석 중...         │"
echo "  │  task_type: large-context               │"
echo "  │  primary: qwen35-cli.sh (nexus, 400K)   │"
echo "  └─────────────────────────────────────────┘"
sleep 0.5
echo "  → Qwen3.5-122B (nexus:8080) 로 라우팅"
echo

sleep 2
echo "═══════════════════════════════════════════════"
echo " 데모 완료 — 역할별 최적 AI 자동 라우팅"
echo "  claude / codex / gemini / qwen35 / qwen-coder"
echo "═══════════════════════════════════════════════"
