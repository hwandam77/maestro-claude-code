"""
Maestro Claude Code - LiteLLM Custom Callback
계획서: Phase 5 (CCR 패턴 차용)

SubagentStart hook (subagent-router.py)이 기록한 에이전트 모델 힌트를 읽어
다음 LiteLLM 요청의 모델을 동적으로 오버라이드한다.

사용법:
  config/ccproxy.yaml에 다음 추가:
    litellm_settings:
      success_callback: ["tools.litellm-callback.AgentRouter"]
      # 또는
      custom_callbacks: ["tools/litellm-callback.py"]

참고:
  LiteLLM CustomLogger API:
  https://docs.litellm.ai/docs/proxy/logging#custom-callback-class
"""

import json
import os
import time

try:
    from litellm.integrations.custom_logger import CustomLogger
    import litellm
    LITELLM_AVAILABLE = True
except ImportError:
    LITELLM_AVAILABLE = False


PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HINT_PATH = os.path.join(PROJECT_DIR, "logs", "ccproxy", ".agent-model-hint")

# 모델 힌트 유효 시간 (초)
HINT_TTL = 30


def read_model_hint() -> dict | None:
    """subagent-router.py가 기록한 모델 힌트 읽기"""
    if not os.path.exists(HINT_PATH):
        return None

    # TTL 체크
    mtime = os.path.getmtime(HINT_PATH)
    if time.time() - mtime > HINT_TTL:
        try:
            os.remove(HINT_PATH)
        except Exception:
            pass
        return None

    try:
        with open(HINT_PATH) as f:
            hint = json.load(f)
        # 읽은 후 삭제 (one-shot 적용)
        os.remove(HINT_PATH)
        return hint
    except Exception:
        return None


if LITELLM_AVAILABLE:
    class AgentRouter(CustomLogger):
        """에이전트별 최적 모델로 LiteLLM 요청을 동적 라우팅"""

        async def async_pre_call_hook(self, user_api_key_dict, cache, data, call_type):
            """요청 전처리: 에이전트 모델 힌트 적용"""
            hint = read_model_hint()
            if hint and "model" in hint:
                original_model = data.get("model", "unknown")
                data["model"] = hint["model"]
                # 로깅
                print(
                    f"[AgentRouter] {hint.get('agent', '?')} → {hint['model']} "
                    f"(원래: {original_model})"
                )
            return data

        def log_success_event(self, kwargs, response_obj, start_time, end_time):
            """성공 이벤트 로깅 (비동기 없이 기본 구현)"""
            pass

        def log_failure_event(self, kwargs, response_obj, start_time, end_time):
            """실패 이벤트 로깅"""
            pass

    # LiteLLM에 콜백 등록
    agent_router_callback = AgentRouter()

else:
    # LiteLLM 미설치 환경에서 단독 테스트
    def read_hint_test():
        hint = read_model_hint()
        if hint:
            print(f"모델 힌트: {hint}")
        else:
            print("힌트 없음 (기본 GLM-5 사용)")

    if __name__ == "__main__":
        read_hint_test()
