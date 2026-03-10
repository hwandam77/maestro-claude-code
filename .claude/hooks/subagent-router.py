#!/usr/bin/env python3
"""
Maestro Observability - SubagentStart Hook 에이전트 라우터
계획서: Phase 5 (CCR 패턴 차용) + 고급 기능 (v2)

Claude Code가 SubagentStart 이벤트 발생 시 실행됨.
stdin으로 전달된 JSON에서 에이전트 이름을 파싱하여:
1. agent-model-map.yaml에서 최적 모델을 조회
2. 환경변수 오버라이드 적용 (MAESTRO_SUBAGENT_MODEL, MAESTRO_MODEL_{AGENT})
3. 복잡도 휴리스틱으로 모델 에스컬레이션 결정
4. 제공자 장애 대비 Failover 체인 설정
5. LiteLLM Proxy에 풍부한 힌트 JSON 전달
6. 관찰성 대시보드에 에이전트 라우팅 이벤트 전송
"""

import sys
import json
import os
import time
import urllib.request
import urllib.error

# 경로 설정 (hooks/ -> .claude/ -> project_root)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
CONFIG_PATH = os.path.join(PROJECT_DIR, "config", "agent-model-map.yaml")
DASHBOARD_URL = os.environ.get("MAESTRO_DASHBOARD_URL", "http://localhost:3456")
CCPROXY_PORT = os.environ.get("CCPROXY_PORT", "4000")

# ─── Feature 2: 제공자 장애 대비 Failover 체인 ───
# 각 모델에 대해 순서대로 대체 모델 시도
FAILOVER_CHAINS: dict[str, list[str]] = {
    "gpt-5.4-medium":     ["glm-5", "qwen3-coder-30b"],
    "gemini-3.1-pro":     ["glm-5"],
    "qwen3.5-122b":       ["glm-5"],
    "qwen3-coder-30b":    ["glm-5"],
    "claude-sonnet-4-6":  ["glm-5"],
    "glm-5":              [],  # 최종 fallback, 더 이상 없음
}

# ─── Feature 3: 복잡도 에스컬레이션 티어 ───
# 복잡도 점수가 높을 때 저비용 모델을 상위 티어로 올림
TIER_ESCALATION: dict[str, str] = {
    "qwen3-coder-30b": "glm-5",
    "glm-5":           "gpt-5.4-medium",
}

# 복잡도 에스컬레이션 임계값
COMPLEXITY_ESCALATION_THRESHOLD = 5

# "저비용" 모델 목록 (에스컬레이션 대상)
CHEAP_MODELS = {"glm-5", "qwen3-coder-30b"}


# ─── 모델 매핑 로드 ───

def load_agent_model_map() -> dict:
    """agent-model-map.yaml 로드 (YAML 파서 없이 단순 파싱)"""
    if not os.path.exists(CONFIG_PATH):
        return {}

    agent_map = {}
    try:
        with open(CONFIG_PATH) as f:
            for line in f:
                line = line.strip()
                # "  agent-name: \"model-name\"" 패턴 파싱
                if ":" in line and not line.startswith("#") and not line.startswith("-"):
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        key = parts[0].strip()
                        raw_value = parts[1].strip()
                        # 인라인 주석 제거 (따옴표 밖의 # 이후)
                        if "#" in raw_value:
                            raw_value = raw_value[:raw_value.index("#")].strip()
                        value = raw_value.strip('"').strip("'").strip()
                        # 유효한 모델명인지 확인 (공백, 주석 제외)
                        if value and not value.startswith("#") and "/" not in value[:4]:
                            # 에이전트명 형식 (하이픈, 영문자)
                            if all(c.isalnum() or c in "-_." for c in key):
                                agent_map[key] = value
    except Exception:
        pass

    return agent_map


def get_model_from_yaml(agent_name: str, agent_map: dict) -> str | None:
    """YAML 맵에서 에이전트 이름으로 최적 모델 조회"""
    if not agent_name:
        return None

    # 정확한 매칭
    if agent_name in agent_map:
        return agent_map[agent_name]

    # 접두사 매칭 (oh-my-claudecode: 접두사 제거)
    clean_name = agent_name.replace("oh-my-claudecode:", "")
    if clean_name in agent_map:
        return agent_map[clean_name]

    return None


# ─── Feature 1: 환경변수 오버라이드 ───

def get_model_from_env(agent_name: str) -> tuple[str | None, str]:
    """
    환경변수에서 모델 오버라이드 조회.
    우선순위: 에이전트별 ENV > 전역 ENV

    Returns:
        (model, source) 튜플. 오버라이드 없으면 (None, "")
    """
    # 에이전트별 오버라이드: MAESTRO_MODEL_{AGENT_NAME_UPPER}
    # 예: MAESTRO_MODEL_EXECUTOR=gpt-5.4-medium
    if agent_name:
        clean_name = agent_name.replace("oh-my-claudecode:", "")
        # 하이픈과 점을 언더스코어로 변환 후 대문자화
        env_key = "MAESTRO_MODEL_" + clean_name.upper().replace("-", "_").replace(".", "_")
        per_agent_model = os.environ.get(env_key)
        if per_agent_model:
            return per_agent_model.strip(), "env_per_agent"

    # 전역 오버라이드: MAESTRO_SUBAGENT_MODEL (모든 서브에이전트에 강제 적용)
    global_model = os.environ.get("MAESTRO_SUBAGENT_MODEL")
    if global_model:
        return global_model.strip(), "env_global"

    return None, ""


# ─── Feature 3: 복잡도 휴리스틱 ───

def compute_complexity_score(hook_data: dict) -> int:
    """
    hook_data에서 복잡도 점수 계산.
    높을수록 더 강력한 모델이 필요한 복잡한 태스크.
    """
    # 분석할 텍스트 추출 (prompt, description, task 등 공통 필드)
    text_parts = []
    for field in ("prompt", "description", "task", "input", "message", "content"):
        value = hook_data.get(field)
        if isinstance(value, str):
            text_parts.append(value)
        elif isinstance(value, dict):
            # 중첩 딕셔너리에서 텍스트 재귀 추출 (1단계)
            for v in value.values():
                if isinstance(v, str):
                    text_parts.append(v)

    combined_text = " ".join(text_parts).lower()
    score = 0

    # 토큰 추정 (문자 수 기준): 2000자 초과 → +2
    if len(combined_text) > 2000:
        score += 2

    # 고복잡도 키워드: 보안, 아키텍처, 중요 작업 → +3
    high_complexity_keywords = ["security", "architecture", "critical", "보안", "아키텍처", "중요"]
    for kw in high_complexity_keywords:
        if kw in combined_text:
            score += 3
            break  # 중복 합산 방지

    # 중복잡도 키워드: 디버그, 분석, 리팩토링 → +2
    medium_complexity_keywords = ["debug", "analyze", "refactor", "디버그", "분석", "리팩토링"]
    for kw in medium_complexity_keywords:
        if kw in combined_text:
            score += 2
            break  # 중복 합산 방지

    # 저복잡도 키워드: 단순 수정, 오타, 형식 → -2
    low_complexity_keywords = ["simple", "rename", "typo", "format", "단순", "이름변경", "오타", "형식"]
    for kw in low_complexity_keywords:
        if kw in combined_text:
            score -= 2
            break  # 중복 합산 방지

    return score


def maybe_escalate_model(model: str, complexity_score: int) -> tuple[str, str]:
    """
    복잡도 점수가 임계값 이상이고 저비용 모델이면 상위 티어로 에스컬레이션.

    Returns:
        (final_model, source) 튜플
    """
    if complexity_score >= COMPLEXITY_ESCALATION_THRESHOLD and model in CHEAP_MODELS:
        escalated = TIER_ESCALATION.get(model)
        if escalated:
            return escalated, "complexity_escalation"
    return model, ""


# ─── 모델 결정 (우선순위 적용) ───

def resolve_model(agent_name: str, hook_data: dict, agent_map: dict) -> tuple[str, str, int]:
    """
    우선순위에 따라 최종 모델 결정:
    1. 에이전트별 ENV 오버라이드
    2. 전역 ENV 오버라이드
    3. YAML 맵 + 복잡도 에스컬레이션
    4. 기본값 (glm-5)

    Returns:
        (model, source, complexity_score) 튜플
    """
    complexity_score = compute_complexity_score(hook_data)

    # 1 & 2: 환경변수 오버라이드 (복잡도 에스컬레이션 적용 안 함 — 명시적 지정 존중)
    env_model, env_source = get_model_from_env(agent_name)
    if env_model:
        return env_model, env_source, complexity_score

    # 3: YAML 맵 조회 후 복잡도 에스컬레이션
    yaml_model = get_model_from_yaml(agent_name, agent_map)
    if yaml_model:
        final_model, escalation_source = maybe_escalate_model(yaml_model, complexity_score)
        source = escalation_source if escalation_source else "yaml_map"
        return final_model, source, complexity_score

    # 4: 기본값
    default_model = "glm-5"
    final_model, escalation_source = maybe_escalate_model(default_model, complexity_score)
    source = escalation_source if escalation_source else "default"
    return final_model, source, complexity_score


# ─── Feature 4: 풍부한 힌트 파일 기록 ───

def write_model_hint(agent_name: str, model: str, source: str,
                     complexity_score: int, failover_chain: list[str]):
    """
    다음 LiteLLM 요청에 적용할 풍부한 힌트 JSON을 임시 파일에 기록.
    LiteLLM custom callback (tools/litellm_callback.py)이 이를 읽어 사용.
    """
    hint_path = os.path.join(PROJECT_DIR, "logs", "ccproxy", ".agent-model-hint")
    hint_data = {
        "agent": agent_name,
        "model": model,
        "source": source,                     # 결정 근거
        "complexity_score": complexity_score,  # 복잡도 점수
        "failover_chain": failover_chain,      # 장애 시 대체 모델 목록
        "timestamp": int(time.time()),
    }
    try:
        os.makedirs(os.path.dirname(hint_path), exist_ok=True)
        with open(hint_path, "w") as f:
            json.dump(hint_data, f)
    except Exception:
        pass


# ─── 이벤트 전송 ───

def send_routing_event(agent_name: str, model: str, source: str,
                        complexity_score: int):
    """관찰성 대시보드에 에이전트 라우팅 이벤트 전송"""
    payload = {
        "event_type": "SubagentRouted",
        "tool_name": "SubagentStart",
        "model": model,
        "status": source,
        "payload": json.dumps({
            "agent": agent_name,
            "routed_to": model,
            "source": source,
            "complexity_score": complexity_score,
        })
    }
    try:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            f"{DASHBOARD_URL}/event",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=2) as r:
            pass
    except Exception:
        pass  # 대시보드 미실행 시 무시


# ─── 메인 ───

def main():
    # stdin에서 hook 데이터 읽기
    try:
        hook_data = json.load(sys.stdin)
    except Exception:
        hook_data = {}

    # 에이전트 이름 추출 (SubagentStart 이벤트 필드)
    agent_name = (
        hook_data.get("agent_name") or
        hook_data.get("subagent_type") or
        hook_data.get("type") or
        ""
    )

    # YAML 맵 로드
    agent_map = load_agent_model_map()

    # 우선순위에 따라 최종 모델 결정
    model, source, complexity_score = resolve_model(agent_name, hook_data, agent_map)

    # Feature 2: 해당 모델의 failover 체인 조회
    failover_chain = FAILOVER_CHAINS.get(model, [])

    # Feature 4: 풍부한 힌트 파일 기록 (LiteLLM callback이 읽음)
    write_model_hint(agent_name, model, source, complexity_score, failover_chain)

    # 관찰성 이벤트 전송
    if agent_name or model:
        send_routing_event(agent_name, model, source, complexity_score)

    # hook은 항상 exit 0 (실패해도 Claude Code 동작 방해 안 함)
    sys.exit(0)


if __name__ == "__main__":
    main()
