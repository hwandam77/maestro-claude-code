#!/bin/bash
# Maestro Claude Code - 크로스 도구 설정 동기화
# Claude skills/commands를 Codex, Gemini에 심볼릭 링크로 동기화
#
# 사용법:
#   ./scripts/sync-settings.sh          → 전체 동기화
#   ./scripts/sync-settings.sh codex    → Codex만
#   ./scripts/sync-settings.sh gemini   → Gemini만
#   ./scripts/sync-settings.sh status   → 현재 동기화 상태 확인
#   ./scripts/sync-settings.sh clean    → 심볼릭 링크만 제거 (원본 유지)

set -euo pipefail

CLAUDE_SKILLS="${HOME}/.claude/skills"
CLAUDE_COMMANDS="${HOME}/.claude/commands"

# Codex 설정 경로
CODEX_SKILLS="${HOME}/.codex/skills"
CODEX_COMMANDS="${HOME}/.codex/commands"

# Gemini 설정 경로
GEMINI_SKILLS="${HOME}/.gemini/skills"

# Claude 전용 제외 목록 (패턴)
EXCLUDE_ALWAYS=("contract-gate*" "security-scan*" "task-sync*" "brand-guidelines*")

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 제외 여부 확인
should_exclude() {
    local filename="$1"
    shift
    local patterns=("$@")
    for pattern in "${patterns[@]}"; do
        # shellcheck disable=SC2254
        case "$filename" in
            $pattern) return 0 ;;
        esac
    done
    return 1
}

# 디렉토리 심볼릭 링크 동기화
sync_dir() {
    local src_dir="$1"
    local dst_dir="$2"
    local label="$3"
    shift 3
    local excludes=("$@")

    if [ ! -d "$src_dir" ]; then
        printf "  ${YELLOW}소스 없음: %s${NC}\n" "$src_dir"
        return 1
    fi
    mkdir -p "$dst_dir"

    local count=0
    local skipped=0

    for src_file in "$src_dir"/*; do
        [ -e "$src_file" ] || continue
        local filename
        filename=$(basename "$src_file")

        # 제외 패턴 체크
        if should_exclude "$filename" "${excludes[@]}"; then
            skipped=$((skipped + 1))
            continue
        fi

        local dst_file="${dst_dir}/${filename}"

        # 이미 올바른 심볼릭 링크면 스킵
        if [ -L "$dst_file" ] && [ "$(readlink "$dst_file")" = "$src_file" ]; then
            continue
        fi

        # 기존 파일/링크/디렉토리 제거 후 심볼릭 링크 생성
        if [ -e "$dst_file" ] || [ -L "$dst_file" ]; then
            rm -rf "$dst_file"
        fi
        ln -s "$src_file" "$dst_file"
        count=$((count + 1))
    done

    printf "  %-10s ${GREEN}%d개 링크 생성${NC}" "$label" "$count"
    [ "$skipped" -gt 0 ] && printf " (${YELLOW}%d개 제외${NC})" "$skipped"
    printf "\n"
}

sync_codex() {
    echo "[동기화] Claude → Codex"
    local codex_excludes=("${EXCLUDE_ALWAYS[@]}" "design*" "localcode*")
    sync_dir "$CLAUDE_SKILLS"   "$CODEX_SKILLS"   "skills"   "${codex_excludes[@]}"
    sync_dir "$CLAUDE_COMMANDS" "$CODEX_COMMANDS" "commands" "${codex_excludes[@]}"
}

sync_gemini() {
    echo "[동기화] Claude → Gemini"
    local gemini_excludes=("${EXCLUDE_ALWAYS[@]}" "tdd*" "build-fix*" "code-review*")
    sync_dir "$CLAUDE_SKILLS" "$GEMINI_SKILLS" "skills" "${gemini_excludes[@]}"
    # Gemini는 commands 동기화 없음
}

show_status() {
    echo "================================"
    echo "  동기화 상태"
    echo "================================"
    echo ""

    for dir in "$CODEX_SKILLS" "$CODEX_COMMANDS" "$GEMINI_SKILLS"; do
        local link_count=0
        local real_count=0
        if [ ! -d "$dir" ]; then
            printf "  ${YELLOW}%-40s (디렉토리 없음)${NC}\n" "$dir"
            continue
        fi

        for f in "$dir"/*; do
            [ -e "$f" ] || [ -L "$f" ] || continue
            if [ -L "$f" ]; then
                link_count=$((link_count + 1))
            else
                real_count=$((real_count + 1))
            fi
        done

        echo "  $dir"
        printf "    심볼릭 링크: ${GREEN}%d개${NC}\n" "$link_count"
        [ "$real_count" -gt 0 ] && printf "    로컬 파일: ${YELLOW}%d개 (동기화 제외)${NC}\n" "$real_count"
    done
    echo ""
}

clean_links() {
    echo "[정리] 심볼릭 링크 제거 (원본 유지)"
    for dir in "$CODEX_SKILLS" "$CODEX_COMMANDS" "$GEMINI_SKILLS"; do
        [ -d "$dir" ] || continue
        local removed=0
        for f in "$dir"/*; do
            [ -L "$f" ] || continue
            rm -f "$f"
            removed=$((removed + 1))
        done
        [ "$removed" -gt 0 ] && printf "  %s: ${GREEN}%d개 링크 제거${NC}\n" "$dir" "$removed"
    done
    echo "  완료 (원본 파일은 유지됨)"
}

TARGET="${1:-all}"
case "$TARGET" in
    codex)   sync_codex ;;
    gemini)  sync_gemini ;;
    status)  show_status ;;
    clean)   clean_links ;;
    all)
        sync_codex
        echo ""
        sync_gemini
        echo ""
        echo "[완료] 동기화 완료"
        ;;
    *)
        echo "사용법: $0 {all|codex|gemini|status|clean}"
        exit 1
        ;;
esac
