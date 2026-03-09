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

DASHBOARD_URL = os.environ.get("MAESTRO_DASHBOARD_URL", "http://localhost:3456")
EVENT_TYPE = sys.argv[1] if len(sys.argv) > 1 else "Unknown"


def send_event(payload: dict):
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

    # 이벤트 타입별 정보 추출
    payload = {
        "event_type": EVENT_TYPE,
        "session_id": hook_data.get("session_id", ""),
        "tool_name": hook_data.get("tool_name", hook_data.get("tool", "")),
        "model": hook_data.get("model", ""),
        "status": "ok",
        "payload": json.dumps(hook_data)
    }

    send_event(payload)


if __name__ == "__main__":
    main()
