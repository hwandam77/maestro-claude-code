#!/usr/bin/env python3
"""
Maestro Claude Code - 비용 추적 모듈
MassGen LiteLLM 비용 추적 방식에서 영감을 받아 구현
외부 의존성 없음 (stdlib만 사용)
"""

import json
import os
import sys
from datetime import datetime, date, timezone
from pathlib import Path
from typing import Optional

# ─────────────────────────────────────────────
# 모델별 1K 토큰당 비용 (USD)
# ─────────────────────────────────────────────
MODEL_PRICING = {
    # ZAI Coding Plan - 월정액 $3, 토큰 비용 없음
    "glm-5": {"input": 0.0, "output": 0.0},
    "glm-4.5-air": {"input": 0.0, "output": 0.0},

    # OpenAI Codex - 구독 포함
    "gpt-5.4-medium": {"input": 0.0, "output": 0.0},
    "gpt-5.3-codex": {"input": 0.0, "output": 0.0},

    # Google Gemini - 무료 티어
    "gemini-3.1-pro": {"input": 0.0, "output": 0.0},
    "gemini-3.1-pro-preview": {"input": 0.0, "output": 0.0},

    # 자체 호스팅 Qwen - 전기세만 발생 (월 고정비로 처리)
    "qwen3.5-122b": {"input": 0.0, "output": 0.0},
    "qwen3-coder-30b": {"input": 0.0, "output": 0.0},

    # Anthropic Claude - 구독이지만 기회비용 추적용
    "claude-sonnet-4-6": {"input": 0.003, "output": 0.015},
    "claude-sonnet-4-5": {"input": 0.003, "output": 0.015},
    "claude-opus-4": {"input": 0.015, "output": 0.075},
    "claude-haiku-4-5": {"input": 0.0008, "output": 0.004},

    # 기본값 (알 수 없는 모델)
    "unknown": {"input": 0.0, "output": 0.0},
}

# ─────────────────────────────────────────────
# 월정액 고정 비용 (USD/월)
# ─────────────────────────────────────────────
MONTHLY_FIXED_COSTS = {
    "glm-5 (ZAI Coding Plan)": 3.0,
    "gpt-5.4-medium (OpenAI 구독)": 0.0,   # 구독에 포함
    "gemini-3.1-pro (무료 티어)": 0.0,
    "자체 호스팅 서버 전기세 추정": 50.0,  # nexus(RTX 3090x3) + cognit(RTX 3080Ti x2)
}

# ─────────────────────────────────────────────
# 로그 디렉토리
# ─────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
LOGS_DIR = PROJECT_DIR / "logs" / "costs"


def _get_log_path(target_date: Optional[date] = None) -> Path:
    """날짜별 JSONL 로그 파일 경로 반환"""
    if target_date is None:
        target_date = date.today()
    return LOGS_DIR / f"{target_date.isoformat()}.jsonl"


def _normalize_model(model: str) -> str:
    """모델명을 pricing 딕셔너리 키로 정규화"""
    model_lower = model.lower()
    for key in MODEL_PRICING:
        if key in model_lower:
            return key
    return "unknown"


# ─────────────────────────────────────────────
# 비용 계산
# ─────────────────────────────────────────────
def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> dict:
    """
    모델과 토큰 수로 예상 비용 계산

    Returns:
        dict: model, input_tokens, output_tokens, input_cost, output_cost, total_cost, currency
    """
    norm_model = _normalize_model(model)
    pricing = MODEL_PRICING.get(norm_model, MODEL_PRICING["unknown"])

    input_cost = (input_tokens / 1000.0) * pricing["input"]
    output_cost = (output_tokens / 1000.0) * pricing["output"]
    total_cost = input_cost + output_cost

    return {
        "model": model,
        "normalized_model": norm_model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "input_cost": round(input_cost, 8),
        "output_cost": round(output_cost, 8),
        "total_cost": round(total_cost, 8),
        "currency": "USD",
    }


# ─────────────────────────────────────────────
# 비용 로깅
# ─────────────────────────────────────────────
def log_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
    agent_name: str = "",
    session_id: str = "",
) -> dict:
    """
    비용을 JSONL 파일에 기록

    Args:
        model: 모델명
        input_tokens: 입력 토큰 수
        output_tokens: 출력 토큰 수
        agent_name: OMC 에이전트명 (선택)
        session_id: 세션 ID (선택)

    Returns:
        기록된 비용 정보 dict
    """
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    cost_info = estimate_cost(model, input_tokens, output_tokens)
    record = {
        "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "model": model,
        "normalized_model": cost_info["normalized_model"],
        "agent": agent_name,
        "session_id": session_id,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost": cost_info["total_cost"],
        "input_cost": cost_info["input_cost"],
        "output_cost": cost_info["output_cost"],
        "currency": "USD",
    }

    log_path = _get_log_path()
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    return record


# ─────────────────────────────────────────────
# 일별 요약
# ─────────────────────────────────────────────
def get_daily_summary(target_date: Optional[str] = None) -> dict:
    """
    특정 날짜의 비용 요약 반환

    Args:
        target_date: 'YYYY-MM-DD' 형식 문자열 (None이면 오늘)

    Returns:
        dict: total_cost, by_model, by_agent, total_calls, total_tokens
    """
    if target_date is None:
        log_path = _get_log_path()
        target_date = date.today().isoformat()
    else:
        log_path = _get_log_path(date.fromisoformat(target_date))

    summary = {
        "date": target_date,
        "total_cost": 0.0,
        "total_calls": 0,
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "by_model": {},
        "by_agent": {},
    }

    if not log_path.exists():
        return summary

    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue

            model = record.get("normalized_model", record.get("model", "unknown"))
            agent = record.get("agent", "") or "unknown"
            cost = record.get("cost", 0.0)
            in_tok = record.get("input_tokens", 0)
            out_tok = record.get("output_tokens", 0)

            summary["total_cost"] += cost
            summary["total_calls"] += 1
            summary["total_input_tokens"] += in_tok
            summary["total_output_tokens"] += out_tok

            # 모델별 집계
            if model not in summary["by_model"]:
                summary["by_model"][model] = {"calls": 0, "input_tokens": 0, "output_tokens": 0, "cost": 0.0}
            summary["by_model"][model]["calls"] += 1
            summary["by_model"][model]["input_tokens"] += in_tok
            summary["by_model"][model]["output_tokens"] += out_tok
            summary["by_model"][model]["cost"] += cost

            # 에이전트별 집계
            if agent not in summary["by_agent"]:
                summary["by_agent"][agent] = {"calls": 0, "cost": 0.0}
            summary["by_agent"][agent]["calls"] += 1
            summary["by_agent"][agent]["cost"] += cost

    summary["total_cost"] = round(summary["total_cost"], 8)
    return summary


# ─────────────────────────────────────────────
# 월별 요약
# ─────────────────────────────────────────────
def get_monthly_summary(year_month: Optional[str] = None) -> dict:
    """
    특정 월의 비용 요약 (고정비 포함)

    Args:
        year_month: 'YYYY-MM' 형식 문자열 (None이면 이번 달)

    Returns:
        dict: total_variable, total_fixed, total_cost, by_model, by_agent, days_active
    """
    if year_month is None:
        year_month = date.today().strftime("%Y-%m")

    summary = {
        "year_month": year_month,
        "total_variable": 0.0,
        "total_fixed": sum(MONTHLY_FIXED_COSTS.values()),
        "total_cost": 0.0,
        "total_calls": 0,
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "by_model": {},
        "by_agent": {},
        "days_active": 0,
        "fixed_costs": MONTHLY_FIXED_COSTS,
    }

    if not LOGS_DIR.exists():
        summary["total_cost"] = summary["total_fixed"]
        return summary

    # 해당 월의 모든 JSONL 파일 처리
    for log_file in sorted(LOGS_DIR.glob(f"{year_month}-*.jsonl")):
        day_summary = get_daily_summary(log_file.stem)
        if day_summary["total_calls"] > 0:
            summary["days_active"] += 1

        summary["total_variable"] += day_summary["total_cost"]
        summary["total_calls"] += day_summary["total_calls"]
        summary["total_input_tokens"] += day_summary["total_input_tokens"]
        summary["total_output_tokens"] += day_summary["total_output_tokens"]

        # 모델별 누적
        for model, stats in day_summary["by_model"].items():
            if model not in summary["by_model"]:
                summary["by_model"][model] = {"calls": 0, "input_tokens": 0, "output_tokens": 0, "cost": 0.0}
            summary["by_model"][model]["calls"] += stats["calls"]
            summary["by_model"][model]["input_tokens"] += stats["input_tokens"]
            summary["by_model"][model]["output_tokens"] += stats["output_tokens"]
            summary["by_model"][model]["cost"] += stats["cost"]

        # 에이전트별 누적
        for agent, stats in day_summary["by_agent"].items():
            if agent not in summary["by_agent"]:
                summary["by_agent"][agent] = {"calls": 0, "cost": 0.0}
            summary["by_agent"][agent]["calls"] += stats["calls"]
            summary["by_agent"][agent]["cost"] += stats["cost"]

    summary["total_variable"] = round(summary["total_variable"], 8)
    summary["total_cost"] = round(summary["total_variable"] + summary["total_fixed"], 8)
    return summary


# ─────────────────────────────────────────────
# CLI 인터페이스
# ─────────────────────────────────────────────
def _print_daily(target_date: Optional[str] = None):
    summary = get_daily_summary(target_date)
    print(f"\n{'='*50}")
    print(f"  일별 비용 요약: {summary['date']}")
    print(f"{'='*50}")
    print(f"  총 비용:        ${summary['total_cost']:.6f}")
    print(f"  총 호출 수:     {summary['total_calls']}")
    print(f"  입력 토큰:      {summary['total_input_tokens']:,}")
    print(f"  출력 토큰:      {summary['total_output_tokens']:,}")

    if summary["by_model"]:
        print(f"\n  [모델별]")
        for model, stats in sorted(summary["by_model"].items()):
            print(f"    {model}: {stats['calls']}회, ${stats['cost']:.6f}")

    if summary["by_agent"]:
        print(f"\n  [에이전트별]")
        for agent, stats in sorted(summary["by_agent"].items()):
            print(f"    {agent}: {stats['calls']}회, ${stats['cost']:.6f}")
    print()


def _print_monthly(year_month: Optional[str] = None):
    summary = get_monthly_summary(year_month)
    print(f"\n{'='*50}")
    print(f"  월별 비용 요약: {summary['year_month']}")
    print(f"{'='*50}")
    print(f"  변동 비용:      ${summary['total_variable']:.6f}")
    print(f"  고정 비용:      ${summary['total_fixed']:.2f}")
    print(f"  총 비용:        ${summary['total_cost']:.2f}")
    print(f"  활성 일수:      {summary['days_active']}일")
    print(f"  총 호출 수:     {summary['total_calls']}")

    print(f"\n  [고정 비용 항목]")
    for name, cost in summary["fixed_costs"].items():
        print(f"    {name}: ${cost:.2f}/월")

    if summary["by_model"]:
        print(f"\n  [모델별]")
        for model, stats in sorted(summary["by_model"].items()):
            print(f"    {model}: {stats['calls']}회, ${stats['cost']:.6f}")
    print()


def _print_estimate(model: str, tokens_str: str):
    try:
        tokens = int(tokens_str)
    except ValueError:
        print(f"오류: 토큰 수는 정수여야 합니다: {tokens_str}")
        sys.exit(1)

    # 입력:출력 = 3:1 비율 가정
    input_tokens = int(tokens * 0.75)
    output_tokens = int(tokens * 0.25)
    result = estimate_cost(model, input_tokens, output_tokens)

    print(f"\n  모델: {model} (→ {result['normalized_model']})")
    print(f"  총 토큰: {tokens:,} (입력 {input_tokens:,} / 출력 {output_tokens:,})")
    print(f"  예상 비용: ${result['total_cost']:.6f} USD\n")


def main():
    args = sys.argv[1:]

    if not args or args[0] == "daily":
        date_arg = args[1] if len(args) > 1 else None
        _print_daily(date_arg)

    elif args[0] == "monthly":
        ym_arg = args[1] if len(args) > 1 else None
        _print_monthly(ym_arg)

    elif args[0] == "estimate":
        if len(args) < 3:
            print("사용법: cost-tracker.py estimate <MODEL> <TOTAL_TOKENS>")
            sys.exit(1)
        _print_estimate(args[1], args[2])

    elif args[0] == "log":
        # 테스트용: cost-tracker.py log <model> <in_tok> <out_tok> [agent] [session]
        if len(args) < 4:
            print("사용법: cost-tracker.py log <MODEL> <INPUT_TOKENS> <OUTPUT_TOKENS> [AGENT] [SESSION]")
            sys.exit(1)
        record = log_cost(
            model=args[1],
            input_tokens=int(args[2]),
            output_tokens=int(args[3]),
            agent_name=args[4] if len(args) > 4 else "",
            session_id=args[5] if len(args) > 5 else "",
        )
        print(f"기록 완료: {json.dumps(record, ensure_ascii=False)}")

    else:
        print("사용법: cost-tracker.py [daily [YYYY-MM-DD] | monthly [YYYY-MM] | estimate MODEL TOKENS | log MODEL IN_TOK OUT_TOK]")
        sys.exit(1)


if __name__ == "__main__":
    main()
