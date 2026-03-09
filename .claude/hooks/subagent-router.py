#!/usr/bin/env python3
"""
Maestro Observability - SubagentStart Hook 에이전트 라우터
계획서: Phase 5 (CCR 패턴 차용)

Claude Code가 SubagentStart 이벤트 발생 시 실행됨.
stdin으로 전달된 JSON에서 에이전트 이름을 파싱하여:
1. agent-model-map.yaml에서 최적 모델을 조회
2. LiteLLM Proxy에 다음 요청의 모델 힌트를 전달
3. 관찰성 대시보드에 에이전트 라우팅 이벤트 전송
"""

import sys
import json
import os
import urllib.request
import urllib.error

# 경로 설정 (hooks/ -> .claude/ -> project_root)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
CONFIG_PATH = os.path.join(PROJECT_DIR, "config", "agent-model-map.yaml")
DASHBOARD_URL = os.environ.get("MAESTRO_DASHBOARD_URL", "http://localhost:3456")
CCPROXY_PORT = os.environ.get("CCPROXY_PORT", "4000")

# ─── 모델 매핑 로드 ───

def load_agent_model_map():
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


def get_model_for_agent(agent_name: str, agent_map: dict) -> str | None:
    """에이전트 이름으로 최적 모델 조회"""
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


# ─── 이벤트 전송 ───

def send_routing_event(agent_name: str, model: str, source: str):
    """관찰성 대시보드에 에이전트 라우팅 이벤트 전송"""
    payload = {
        "event_type": "SubagentRouted",
        "tool_name": "SubagentStart",
        "model": model,
        "status": source,  # "mapped" or "default"
        "payload": json.dumps({"agent": agent_name, "routed_to": model})
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


def write_model_hint(agent_name: str, model: str):
    """
    다음 LiteLLM 요청에 적용할 모델 힌트를 임시 파일에 기록.
    LiteLLM custom callback (tools/litellm-callback.py)이 이를 읽어 사용.
    """
    hint_path = os.path.join(PROJECT_DIR, "logs", "ccproxy", ".agent-model-hint")
    try:
        os.makedirs(os.path.dirname(hint_path), exist_ok=True)
        with open(hint_path, "w") as f:
            json.dump({"agent": agent_name, "model": model}, f)
    except Exception:
        pass


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

    # 에이전트별 최적 모델 조회
    agent_map = load_agent_model_map()
    model = get_model_for_agent(agent_name, agent_map)

    if model:
        source = "mapped"
        # 모델 힌트 파일 기록 (LiteLLM callback이 읽음)
        write_model_hint(agent_name, model)
        # 관찰성 이벤트 전송
        send_routing_event(agent_name, model, source)
    else:
        # 매핑 없으면 기본(GLM-5) 유지
        source = "default"
        if agent_name:
            send_routing_event(agent_name, "glm-5", source)

    # hook은 항상 exit 0 (실패해도 Claude Code 동작 방해 안 함)
    sys.exit(0)


if __name__ == "__main__":
    main()
