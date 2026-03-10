#!/usr/bin/env python3
"""
Complexity Analyzer for Maestro Claude Code
NadirClaw/RouteLLM 패턴 차용 - 프롬프트 복잡도 분석으로 모델 자동 라우팅

점수 구간:
  0-2:  SIMPLE   → qwen3-coder-30b 또는 glm-5
  3-5:  MODERATE → glm-5 또는 gpt-5.4-medium
  6-8:  COMPLEX  → gpt-5.4-medium 또는 claude-sonnet-4-6
  9+:   CRITICAL → claude-sonnet-4-6 또는 claude-opus
"""

import re
import sys
from typing import Optional

# ── 복잡도 키워드 정의 ──────────────────────────────────────────────────────
CRITICAL_KEYWORDS = [
    "security audit", "vulnerability", "authentication", "encryption", "owasp",
    "penetration test", "sql injection", "xss", "csrf", "zero-day",
]

HIGH_KEYWORDS = [
    "architecture", "refactor entire", "design system", "migration strategy",
    "performance optimization", "distributed system", "microservice",
    "system design", "scalability",
]

MEDIUM_KEYWORDS = [
    "debug", "analyze", "implement", "integration", "database schema",
    "api design", "optimize", "refactor", "test suite", "ci/cd",
    "deployment", "containerize",
]

LOW_KEYWORDS = [
    "fix bug", "add feature", "update", "modify", "change", "create",
    "write", "generate", "extend",
]

SIMPLE_KEYWORDS = [
    "rename", "typo", "format", "comment", "log", "print", "echo",
    "hello world", "example", "snippet",
]

# ── 도메인 감지 패턴 ─────────────────────────────────────────────────────────
DOMAIN_PATTERNS = {
    "ui": [
        r"\bdesign\b", r"\bui\b", r"\bux\b", r"\bcss\b", r"\bcomponent\b",
        r"\blayout\b", r"\bstyle\b", r"\banimation\b", r"\bfigma\b",
        r"\btailwind\b", r"\bbootstrap\b",
    ],
    "analysis": [
        r"\banalyze\b", r"\blong document\b", r"\bsummariz\b", r"\b400k\b",
        r"\bdataset\b", r"\bstatistic\b", r"\breport\b", r"\binsight\b",
        r"\btranscript\b",
    ],
    "code": [
        r"\bfunction\b", r"\bclass\b", r"\bmethod\b", r"\btest\b",
        r"\bunit test\b", r"\bcode\b", r"\bscript\b", r"\bmodule\b",
    ],
    "security": [
        r"\bsecurity\b", r"\bvulnerabilit\b", r"\bauth\b", r"\bencrypt\b",
        r"\bowasp\b", r"\bpenetrat\b",
    ],
}

# ── 모델 매핑 ────────────────────────────────────────────────────────────────
TIER_MODELS = {
    "SIMPLE":   "qwen3-coder-30b",
    "MODERATE": "glm-5",
    "COMPLEX":  "gpt-5.4-medium",
    "CRITICAL": "claude-sonnet-4-6",
}

DOMAIN_OVERRIDES = {
    "ui":       "gemini-3.1-pro",
    "analysis": "qwen3.5-122b",
    "security": "claude-sonnet-4-6",
    # "code" 도메인은 점수 기반 라우팅 유지 (score >= 3 이면 gpt-5.4-medium)
}


def _detect_domain(text: str) -> Optional[str]:
    """텍스트에서 주요 도메인을 감지한다. 여러 도메인 중 가장 많이 매칭된 것 반환."""
    lower = text.lower()
    scores: dict[str, int] = {}
    for domain, patterns in DOMAIN_PATTERNS.items():
        count = sum(1 for p in patterns if re.search(p, lower))
        if count > 0:
            scores[domain] = count
    if not scores:
        return None
    return max(scores, key=lambda d: scores[d])


def analyze_complexity(text: str) -> dict:
    """
    프롬프트 복잡도를 분석하여 라우팅 정보를 반환한다.

    반환값:
        score (int): 총 복잡도 점수
        tier (str): SIMPLE / MODERATE / COMPLEX / CRITICAL
        factors (list[str]): 점수에 기여한 요소 목록
        recommended_model (str): 최적 모델명
        domain (str|None): 감지된 도메인
    """
    lower = text.lower()
    score = 0
    factors: list[str] = []

    # ── 1. 길이 점수 ─────────────────────────────────────────────────────────
    length = len(text)
    if length < 200:
        pass  # 0점
    elif length < 500:
        score += 1
        factors.append("길이 200-500자 (+1)")
    elif length < 2000:
        score += 2
        factors.append("길이 500-2000자 (+2)")
    elif length < 5000:
        score += 3
        factors.append("길이 2000-5000자 (+3)")
    else:
        score += 4
        factors.append("길이 5000자 초과 (+4)")

    # ── 2. 키워드 복잡도 ─────────────────────────────────────────────────────
    for kw in CRITICAL_KEYWORDS:
        if kw in lower:
            score += 4
            factors.append(f"치명 키워드 '{kw}' (+4)")

    for kw in HIGH_KEYWORDS:
        if kw in lower:
            score += 3
            factors.append(f"고복잡도 키워드 '{kw}' (+3)")

    for kw in MEDIUM_KEYWORDS:
        if kw in lower:
            score += 2
            factors.append(f"중복잡도 키워드 '{kw}' (+2)")
            break  # 중복 점수 방지: 첫 번째 매칭만 적용

    for kw in LOW_KEYWORDS:
        if kw in lower:
            score += 1
            factors.append(f"저복잡도 키워드 '{kw}' (+1)")
            break

    for kw in SIMPLE_KEYWORDS:
        if kw in lower:
            score -= 1
            factors.append(f"단순 키워드 '{kw}' (-1)")
            break

    # ── 3. 코드 지표 ─────────────────────────────────────────────────────────
    # 다중 파일 참조 (src/foo.ts, lib/bar.py 등)
    file_refs = re.findall(r'[\w./]+-[\w.]+\.\w{2,4}|[\w./]+/[\w.]+\.\w{2,4}', text)
    if len(file_refs) >= 2:
        score += 2
        factors.append(f"다중 파일 참조 {len(file_refs)}개 (+2)")

    # 코드 블록 포함 여부
    if "```" in text or re.search(r'\n    \S', text):
        score += 1
        factors.append("코드 블록 포함 (+1)")

    # 테스트 파일 참조
    if re.search(r'(test|spec|__tests__)', lower):
        score += 1
        factors.append("테스트 파일 참조 (+1)")

    # 설정/인프라 파일 참조
    if re.search(r'(dockerfile|docker-compose|\.yml|\.yaml|\.toml|nginx|k8s|kubernetes)', lower):
        score += 2
        factors.append("설정/인프라 파일 참조 (+2)")

    # ── 4. 도메인 지표 ───────────────────────────────────────────────────────
    domain = _detect_domain(text)
    if domain == "security":
        score += 3
        factors.append("보안 도메인 감지 (+3)")
    elif domain == "analysis":
        score += 1
        factors.append("데이터/분석 도메인 감지 (+1)")
    elif domain == "ui":
        score += 1
        factors.append("UI/디자인 도메인 감지 (+1)")

    # 음수 방지
    score = max(0, score)

    # ── 티어 결정 ────────────────────────────────────────────────────────────
    if score <= 2:
        tier = "SIMPLE"
    elif score <= 5:
        tier = "MODERATE"
    elif score <= 8:
        tier = "COMPLEX"
    else:
        tier = "CRITICAL"

    recommended_model = get_model_for_complexity(score, domain)

    return {
        "score": score,
        "tier": tier,
        "factors": factors,
        "recommended_model": recommended_model,
        "domain": domain,
    }


def get_model_for_complexity(score: int, domain: Optional[str] = None) -> str:
    """
    점수와 도메인을 기반으로 최적 모델명을 반환한다.

    도메인 오버라이드가 티어 기반 라우팅보다 우선한다.
    단, code 도메인은 점수 >= 3일 때만 gpt-5.4-medium으로 라우팅.
    """
    # 도메인 오버라이드 적용
    if domain in DOMAIN_OVERRIDES:
        return DOMAIN_OVERRIDES[domain]

    if domain == "code" and score >= 3:
        return "gpt-5.4-medium"

    # 티어 기반 기본 라우팅
    if score <= 2:
        return TIER_MODELS["SIMPLE"]
    elif score <= 5:
        return TIER_MODELS["MODERATE"]
    elif score <= 8:
        return TIER_MODELS["COMPLEX"]
    else:
        return TIER_MODELS["CRITICAL"]


# ── CLI 진입점 ───────────────────────────────────────────────────────────────
def main() -> None:
    """CLI: python3 complexity-analyzer.py "프롬프트 텍스트" 또는 stdin 입력"""
    if len(sys.argv) > 1:
        text = " ".join(sys.argv[1:])
    else:
        # stdin 입력 지원
        text = sys.stdin.read().strip()

    if not text:
        print("사용법: python3 complexity-analyzer.py \"프롬프트 텍스트\"")
        print("       echo \"프롬프트\" | python3 complexity-analyzer.py")
        sys.exit(1)

    result = analyze_complexity(text)

    print(f"═══════════════════════════════════════")
    print(f"  Maestro 복잡도 분석 결과")
    print(f"═══════════════════════════════════════")
    print(f"  점수:           {result['score']}")
    print(f"  티어:           {result['tier']}")
    print(f"  추천 모델:      {result['recommended_model']}")
    print(f"  감지된 도메인:  {result['domain'] or '없음'}")
    print(f"───────────────────────────────────────")
    if result["factors"]:
        print(f"  점수 요인:")
        for factor in result["factors"]:
            print(f"    • {factor}")
    else:
        print(f"  점수 요인: 없음 (기본 SIMPLE)")
    print(f"═══════════════════════════════════════")


if __name__ == "__main__":
    main()
