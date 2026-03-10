#!/usr/bin/env python3
"""
Maestro Observability - Hook 이벤트 전송기
사용: python3 .claude/hooks/send-event.py <EventType>
stdin: Claude Code hook JSON 데이터
"""
import sys
import json
import urllib.request
import urllib.error
import os
import uuid
import time

DASHBOARD_URL = os.environ.get("MAESTRO_DASHBOARD_URL", "http://localhost:3456")
EVENT_TYPE = sys.argv[1] if len(sys.argv) > 1 else "Unknown"

# 프로젝트 루트 (hooks/ 기준 두 단계 상위)
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
HINT_PATH = os.path.join(PROJECT_DIR, "logs", "ccproxy", ".agent-model-hint")

# 힌트 파일 유효 시간 (초)
HINT_TTL = 30

# cost-tracker 선택적 임포트
try:
    sys.path.insert(0, os.path.join(PROJECT_DIR, "tools"))
    from cost_tracker import estimate_cost  # type: ignore
    COST_TRACKER_AVAILABLE = True
except Exception:
    COST_TRACKER_AVAILABLE = False


def get_session_id() -> str:
    """세션 ID 반환: 환경변수 > /tmp 파일 > 자동 생성"""
    # 1) 환경변수 우선
    env_id = os.environ.get("MAESTRO_SESSION_ID", "").strip()
    if env_id:
        return env_id

    # 2) /tmp 파일에서 읽기 (같은 세션 내 일관성 유지)
    tmp_path = "/tmp/maestro-session-id"
    try:
        if os.path.exists(tmp_path):
            with open(tmp_path) as f:
                stored = f.read().strip()
            if stored:
                return stored
    except Exception:
        pass

    # 3) 새 UUID 생성 후 저장
    new_id = str(uuid.uuid4())
    try:
        with open(tmp_path, "w") as f:
            f.write(new_id)
    except Exception:
        pass
    return new_id


def read_hint_file() -> dict:
    """subagent-router.py가 기록한 모델 힌트 읽기 (삭제하지 않음 - send-event는 읽기 전용)"""
    if not os.path.exists(HINT_PATH):
        return {}
    try:
        mtime = os.path.getmtime(HINT_PATH)
        if time.time() - mtime > HINT_TTL:
            return {}
        with open(HINT_PATH) as f:
            return json.load(f)
    except Exception:
        return {}


def extract_agent_context(hook_data: dict) -> dict:
    """hook_data 및 힌트 파일에서 에이전트 컨텍스트 추출"""
    ctx = {
        "agent_name": "",
        "model": hook_data.get("model", ""),
        "complexity_score": None,
        "routing_source": "",
        "input_tokens": None,
        "output_tokens": None,
    }

    # SubagentStart 이벤트에서 에이전트명 추출
    agent_name = (
        hook_data.get("agent_name", "")
        or hook_data.get("subagent_name", "")
        or hook_data.get("agent", "")
    )
    ctx["agent_name"] = agent_name

    # 응답 토큰 정보 추출
    usage = hook_data.get("usage", {}) or {}
    if usage:
        ctx["input_tokens"] = usage.get("input_tokens") or usage.get("prompt_tokens")
        ctx["output_tokens"] = usage.get("output_tokens") or usage.get("completion_tokens")

    # 힌트 파일에서 추가 정보
    hint = read_hint_file()
    if hint:
        if not ctx["agent_name"] and hint.get("agent"):
            ctx["agent_name"] = hint["agent"]
        if not ctx["model"] and hint.get("model"):
            ctx["model"] = hint["model"]
        ctx["complexity_score"] = hint.get("complexity_score")
        ctx["routing_source"] = hint.get("source", "")

    return ctx


def estimate_event_cost(input_tokens, output_tokens, model: str) -> float | None:
    """cost-tracker를 이용한 비용 추정 (없으면 None)"""
    if not COST_TRACKER_AVAILABLE:
        return None
    if not (input_tokens or output_tokens):
        return None
    try:
        return estimate_cost(
            model=model,
            input_tokens=input_tokens or 0,
            output_tokens=output_tokens or 0,
        )
    except Exception:
        return None


def send_event(payload: dict):
    """대시보드로 이벤트 전송 (실패 시 무시)"""
    try:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            f"{DASHBOARD_URL}/event",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=2) as r:
            pass  # 성공 시 무시
    except Exception:
        pass  # 대시보드 미실행 시에도 hook 실패 방지


def main():
    try:
        hook_data = json.load(sys.stdin)
    except Exception:
        hook_data = {}

    # 세션 ID 획득
    session_id = get_session_id()

    # 에이전트 컨텍스트 추출
    ctx = extract_agent_context(hook_data)

    # 비용 추정
    cost_usd = estimate_event_cost(
        ctx["input_tokens"],
        ctx["output_tokens"],
        ctx["model"],
    )

    # 확장된 이벤트 페이로드 구성
    payload = {
        "event_type": EVENT_TYPE,
        "session_id": session_id,
        "tool_name": hook_data.get("tool_name", hook_data.get("tool", "")),
        "model": ctx["model"],
        "agent_name": ctx["agent_name"],
        "complexity_score": ctx["complexity_score"],
        "routing_source": ctx["routing_source"],
        "input_tokens": ctx["input_tokens"],
        "output_tokens": ctx["output_tokens"],
        "cost_usd": cost_usd,
        "status": "ok",
        "payload": json.dumps(hook_data),
    }

    send_event(payload)


if __name__ == "__main__":
    main()
    sys.exit(0)
