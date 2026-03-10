#!/usr/bin/env python3
"""
Maestro Session Learner - Stop Hook
everything-claude-code의 evaluate-session.js 패턴 차용

세션 종료 시 실행되어:
1. 라우팅 힌트 로그에서 세션의 모델 라우팅 이력 수집
2. 비용 로그에서 세션 비용 집계
3. 에스컬레이션/failover 빈도 분석
4. 학습 패턴을 logs/learnings/YYYY-MM-DD.jsonl에 기록
5. 자주 에스컬레이션되는 에이전트 → agent-model-map.yaml 업데이트 제안

stdin: Claude Code Stop hook JSON (may contain transcript_path, session_id)
stdout: JSON { hookSpecificOutput: { additionalContext: "..." } }
"""

import sys
import json
import os
from datetime import datetime, timezone

# 경로 설정
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
COSTS_DIR = os.path.join(PROJECT_DIR, "logs", "costs")
LEARNINGS_DIR = os.path.join(PROJECT_DIR, "logs", "learnings")
EVENTS_LOG = os.path.join(PROJECT_DIR, "logs", "ccproxy", "routing-events.jsonl")
AGENT_MAP_PATH = os.path.join(PROJECT_DIR, "config", "agent-model-map.yaml")

# ─── 세션 이벤트 수집 ───

def get_session_id():
    """현재 세션 ID 조회"""
    # ENV에서 먼저
    sid = os.environ.get("MAESTRO_SESSION_ID", "")
    if sid:
        return sid
    # /tmp 파일에서
    try:
        with open("/tmp/maestro-session-id") as f:
            return f.read().strip()
    except Exception:
        return "unknown"


def collect_routing_events(session_id: str) -> list:
    """세션의 라우팅 이벤트 수집 (routing-events.jsonl에서)"""
    events = []
    if not os.path.exists(EVENTS_LOG):
        return events
    try:
        with open(EVENTS_LOG) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    evt = json.loads(line)
                    if evt.get("session_id") == session_id or session_id == "unknown":
                        events.append(evt)
                except json.JSONDecodeError:
                    continue
    except Exception:
        pass
    return events


def collect_today_costs() -> dict:
    """오늘의 비용 로그 집계"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    cost_file = os.path.join(COSTS_DIR, f"{today}.jsonl")
    summary = {"total_cost": 0.0, "total_calls": 0, "by_model": {}, "by_agent": {}}

    if not os.path.exists(cost_file):
        return summary

    try:
        with open(cost_file) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    cost = entry.get("cost", 0.0)
                    model = entry.get("model", "unknown")
                    agent = entry.get("agent", "unknown")

                    summary["total_cost"] += cost
                    summary["total_calls"] += 1

                    if model not in summary["by_model"]:
                        summary["by_model"][model] = {"calls": 0, "cost": 0.0}
                    summary["by_model"][model]["calls"] += 1
                    summary["by_model"][model]["cost"] += cost

                    if agent not in summary["by_agent"]:
                        summary["by_agent"][agent] = {"calls": 0, "cost": 0.0}
                    summary["by_agent"][agent]["calls"] += 1
                    summary["by_agent"][agent]["cost"] += cost
                except json.JSONDecodeError:
                    continue
    except Exception:
        pass

    return summary


# ─── 패턴 분석 ───

def analyze_escalation_patterns(events: list) -> dict:
    """에스컬레이션 패턴 분석"""
    patterns = {
        "escalation_count": 0,
        "escalated_agents": {},  # agent → {from_model, to_model, count}
        "failover_count": 0,
        "env_override_count": 0,
        "complexity_escalation_count": 0,
    }

    for evt in events:
        source = evt.get("routing_source", evt.get("source", ""))

        if source == "complexity_escalation":
            patterns["escalation_count"] += 1
            patterns["complexity_escalation_count"] += 1
            agent = evt.get("agent", evt.get("agent_name", "unknown"))
            model = evt.get("model", "unknown")
            if agent not in patterns["escalated_agents"]:
                patterns["escalated_agents"][agent] = {"to_model": model, "count": 0}
            patterns["escalated_agents"][agent]["count"] += 1

        elif source.startswith("env_"):
            patterns["env_override_count"] += 1

        elif source == "failover":
            patterns["failover_count"] += 1

    return patterns


def generate_recommendations(patterns: dict) -> list:
    """라우팅 개선 추천 생성"""
    recommendations = []

    # 자주 에스컬레이션되는 에이전트 → YAML 매핑 업데이트 제안
    for agent, data in patterns.get("escalated_agents", {}).items():
        if data["count"] >= 3:
            recommendations.append({
                "type": "upgrade_mapping",
                "agent": agent,
                "suggested_model": data["to_model"],
                "reason": f"에이전트 '{agent}'가 {data['count']}회 에스컬레이션됨 → YAML 매핑을 '{data['to_model']}'로 상향 권장",
                "priority": "high" if data["count"] >= 5 else "medium",
            })

    # 높은 failover 비율 → 서버 안정성 점검 권장
    if patterns.get("failover_count", 0) >= 5:
        recommendations.append({
            "type": "infra_check",
            "reason": f"Failover {patterns['failover_count']}회 발생 → Tailscale/서버 연결 점검 권장",
            "priority": "high",
        })

    return recommendations


# ─── 학습 기록 ───

def save_learning(session_id: str, patterns: dict, costs: dict, recommendations: list):
    """학습 결과를 JSONL 파일에 기록"""
    os.makedirs(LEARNINGS_DIR, exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    learning_file = os.path.join(LEARNINGS_DIR, f"{today}.jsonl")

    learning = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "session_id": session_id,
        "escalation_count": patterns.get("escalation_count", 0),
        "complexity_escalation_count": patterns.get("complexity_escalation_count", 0),
        "failover_count": patterns.get("failover_count", 0),
        "env_override_count": patterns.get("env_override_count", 0),
        "escalated_agents": patterns.get("escalated_agents", {}),
        "total_cost": costs.get("total_cost", 0.0),
        "total_calls": costs.get("total_calls", 0),
        "recommendations": recommendations,
    }

    try:
        with open(learning_file, "a") as f:
            f.write(json.dumps(learning, ensure_ascii=False) + "\n")
    except Exception:
        pass


# ─── 메인 ───

def main():
    try:
        hook_data = json.load(sys.stdin)
    except Exception:
        hook_data = {}

    session_id = get_session_id()

    # 라우팅 이벤트 수집
    events = collect_routing_events(session_id)

    # 오늘 비용 집계
    costs = collect_today_costs()

    # 패턴 분석
    patterns = analyze_escalation_patterns(events)

    # 추천 생성
    recommendations = generate_recommendations(patterns)

    # 학습 기록 저장
    save_learning(session_id, patterns, costs, recommendations)

    # 의미 있는 패턴이 있으면 Claude에게 알림
    context_parts = []

    if patterns["escalation_count"] > 0:
        context_parts.append(
            f"[Session Learner] 복잡도 에스컬레이션 {patterns['complexity_escalation_count']}회 발생"
        )

    if patterns["failover_count"] > 0:
        context_parts.append(
            f"[Session Learner] Failover {patterns['failover_count']}회 발생 - 서버 연결 점검 권장"
        )

    for rec in recommendations:
        if rec["priority"] == "high":
            context_parts.append(f"[Session Learner] 추천: {rec['reason']}")

    if costs["total_cost"] > 0:
        context_parts.append(
            f"[Session Learner] 세션 비용: ${costs['total_cost']:.4f} ({costs['total_calls']}회 호출)"
        )

    if context_parts:
        output = {
            "hookSpecificOutput": {
                "additionalContext": "\n".join(context_parts)
            }
        }
        sys.stdout.write(json.dumps(output))

    sys.exit(0)


if __name__ == "__main__":
    main()
