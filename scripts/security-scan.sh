#!/bin/bash
# Maestro Claude Code - Security Scan (AgentShield 대응)
#
# CI/CD 파이프라인 또는 수동 실행용 보안 스캔 스크립트
# exit 0: 통과, exit 2: 보안 이슈 발견
#
# 사용법:
#   ./scripts/security-scan.sh              → 전체 스캔
#   ./scripts/security-scan.sh --quick      → 시크릿만 빠른 스캔

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ISSUES=0

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "================================"
echo "  Maestro Security Scan"
echo "================================"
echo ""

# 1. 시크릿 하드코딩 검사
echo "[1/4] 시크릿 하드코딩 검사..."
SECRET_PATTERNS=(
    "ANTHROPIC_API_KEY=sk-"
    "OPENAI_API_KEY=sk-"
    "ZAI_API_KEY=[a-zA-Z0-9]"
    "api_key.*=.*['\"][a-zA-Z0-9]{20}"
    "password.*=.*['\"][^'\"]{8}"
    "token.*=.*['\"][a-zA-Z0-9]{20}"
    "BEGIN.*PRIVATE KEY"
)

for pattern in "${SECRET_PATTERNS[@]}"; do
    matches=$(grep -rn --include="*.sh" --include="*.js" --include="*.ts" --include="*.py" --include="*.yaml" --include="*.yml" --include="*.json" \
        -E "$pattern" "$PROJECT_DIR" \
        --exclude-dir=node_modules --exclude-dir=.git --exclude="*.example" 2>/dev/null || true)
    if [ -n "$matches" ]; then
        printf "${RED}[FAIL]${NC} 시크릿 패턴 발견: %s\n" "$pattern"
        echo "$matches" | head -5
        ISSUES=$((ISSUES + 1))
    fi
done
[ $ISSUES -eq 0 ] && printf "${GREEN}[PASS]${NC} 시크릿 없음\n"

if [ "${1:-}" = "--quick" ]; then
    echo ""
    if [ $ISSUES -gt 0 ]; then
        printf "${RED}보안 이슈 %d건 발견${NC}\n" "$ISSUES"
        exit 2
    fi
    printf "${GREEN}빠른 스캔 통과${NC}\n"
    exit 0
fi

# 2. .env 파일 git 추적 검사
echo ""
echo "[2/4] .env 파일 git 추적 검사..."
ENV_TRACKED=$(git -C "$PROJECT_DIR" ls-files "*.env" ".env.*" 2>/dev/null | grep -v ".env.example" || true)
if [ -n "$ENV_TRACKED" ]; then
    printf "${RED}[FAIL]${NC} .env 파일이 git에 추적됨:\n"
    echo "$ENV_TRACKED"
    ISSUES=$((ISSUES + 1))
else
    printf "${GREEN}[PASS]${NC} .env 미추적\n"
fi

# 3. wrapper 스크립트 권한 검사
echo ""
echo "[3/4] 스크립트 권한 검사..."
for script in "$PROJECT_DIR"/scripts/*.sh; do
    if [ -f "$script" ]; then
        perms=$(stat -f "%Lp" "$script" 2>/dev/null || stat -c "%a" "$script" 2>/dev/null)
        if [[ "$perms" == *"7"* ]] && [[ "$perms" != "755" ]] && [[ "$perms" != "775" ]]; then
            printf "${YELLOW}[WARN]${NC} 과도한 권한: %s (%s)\n" "$(basename "$script")" "$perms"
        fi
    fi
done
printf "${GREEN}[PASS]${NC} 스크립트 권한 정상\n"

# 4. 민감 파일 존재 검사
echo ""
echo "[4/4] 민감 파일 검사..."
SENSITIVE_FILES=("credentials.json" "service-account.json" "*.pem" "*.key" "id_rsa")
for pattern in "${SENSITIVE_FILES[@]}"; do
    found=$(find "$PROJECT_DIR" -name "$pattern" -not -path "*/.git/*" -not -path "*/node_modules/*" 2>/dev/null || true)
    if [ -n "$found" ]; then
        printf "${RED}[FAIL]${NC} 민감 파일 발견: %s\n" "$found"
        ISSUES=$((ISSUES + 1))
    fi
done
[ $ISSUES -eq 0 ] && printf "${GREEN}[PASS]${NC} 민감 파일 없음\n" || true

# 결과
echo ""
echo "================================"
if [ $ISSUES -gt 0 ]; then
    printf "${RED}보안 이슈 %d건 발견${NC}\n" "$ISSUES"
    exit 2
fi
printf "${GREEN}모든 보안 검사 통과${NC}\n"
exit 0
