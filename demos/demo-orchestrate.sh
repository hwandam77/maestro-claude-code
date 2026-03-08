#!/bin/bash
# Demo 4: 오케스트레이션 wave 실행 흐름
# asciinema로 녹화: asciinema rec --title "Maestro Orchestration" demos/orchestrate.cast

type_text() {
    local text="$1"
    local delay="${2:-0.05}"
    for ((i=0; i<${#text}; i++)); do
        printf "%s" "${text:$i:1}"
        sleep "$delay"
    done
    echo
}

progress_bar() {
    local label="$1"
    local total=20
    printf "  %-30s [" "$label"
    for ((i=0; i<total; i++)); do
        printf "█"
        sleep 0.05
    done
    printf "] ✓\n"
}

echo
echo "═══════════════════════════════════════════════"
echo " Maestro Claude Code - Orchestration Demo"
echo "═══════════════════════════════════════════════"
echo

sleep 1
type_text "$ /orchestrate-standalone --mode=standard"
echo
echo "  ┌─────────────────────────────────────────┐"
echo "  │  Orchestrate Standalone - Standard Mode │"
echo "  │  훅 프로파일: standard (6 hooks)        │"
echo "  │  Wave 크기: 20-40 tasks                 │"
echo "  └─────────────────────────────────────────┘"
echo
sleep 1

echo "  [Phase 1] Pre-flight Gate"
progress_bar "contract-gate"
progress_bar "quality-gate"
echo

sleep 0.5
echo "  [Wave 1/3] 병렬 실행 중..."
echo "  ├─ Agent: BackendSpecialist  → codex"
progress_bar "  API 엔드포인트 구현"
echo "  ├─ Agent: FrontendSpecialist → gemini"
progress_bar "  UI 컴포넌트 생성"
echo "  └─ Agent: SecuritySpecialist → claude"
progress_bar "  보안 검토"
echo

sleep 0.5
echo "  [Phase 2] Cross-Review Gate"
progress_bar "agents 상호 검토"
echo

sleep 0.5
echo "  [Wave 2/3] 병렬 실행 중..."
echo "  ├─ Agent: QAManager         → qwen-coder"
progress_bar "  테스트 작성"
echo "  └─ Agent: ChiefArchitect    → claude-opus"
progress_bar "  아키텍처 검증"
echo

sleep 0.5
echo "  [Phase 3] Quality Gate"
progress_bar "security-scan"
progress_bar "task-sync"
echo

sleep 1
echo "  ┌─────────────────────────────────────────┐"
echo "  │  ✓ 오케스트레이션 완료                  │"
echo "  │  Wave: 3/3  Tasks: 완료  Gate: 통과     │"
echo "  │  결과물: artifacts/runs/ 저장됨         │"
echo "  └─────────────────────────────────────────┘"
echo

sleep 2
echo "═══════════════════════════════════════════════"
echo " 데모 완료 — Hybrid Wave 멀티 에이전트 실행"
echo "═══════════════════════════════════════════════"
