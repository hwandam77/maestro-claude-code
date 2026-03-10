"""
Maestro Claude Code - LiteLLM Custom Callback
계획서: Phase 5 (CCR 패턴 차용)

SubagentStart hook (subagent-router.py)이 기록한 에이전트 모델 힌트를 읽어
다음 LiteLLM 요청의 모델을 동적으로 오버라이드한다.
failover_chain 지원: 주 모델 실패 시 체인 내 다음 모델로 자동 에스컬레이션.

사용법:
  config/ccproxy.yaml에 다음 추가:
    litellm_settings:
      callbacks: ["tools.litellm_callback.AgentRouter"]

참고:
  LiteLLM CustomLogger API:
  https://docs.litellm.ai/docs/proxy/logging#custom-callback-class

힌트 파일 형식 (JSON):
  {
    "agent": "executor",
    "model": "gpt-5.4-medium",
    "source": "yaml_map",
    "complexity_score": 3,
    "failover_chain": ["glm-5", "qwen3-coder-30b"],
    "timestamp": 1234567890
  }
"""

import json
import os
import time
from collections import defaultdict

try:
    from litellm.integrations.custom_logger import CustomLogger
    import litellm
    LITELLM_AVAILABLE = True
except ImportError:
    LITELLM_AVAILABLE = False

# cost-tracker 선택적 임포트
try:
    _THIS_DIR = os.path.dirname(os.path.abspath(__file__))
    import sys as _sys
    if _THIS_DIR not in _sys.path:
        _sys.path.insert(0, _THIS_DIR)
    from cost_tracker import estimate_cost  # type: ignore
    COST_TRACKER_AVAILABLE = True
except Exception:
    COST_TRACKER_AVAILABLE = False


PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HINT_PATH = os.path.join(PROJECT_DIR, "logs", "ccproxy", ".agent-model-hint")

# 모델 힌트 유효 시간 (초)
HINT_TTL = 30

# 인메모리 메트릭 (성공/실패 카운트, 프로세스 생애 동안 유지)
_metrics: dict[str, dict[str, int]] = defaultdict(lambda: {"success": 0, "failure": 0})


def read_model_hint() -> dict | None:
    """subagent-router.py가 기록한 모델 힌트 읽기 (읽은 후 삭제 - one-shot)"""
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


def log_cost(model: str, input_tokens: int, output_tokens: int, agent: str = ""):
    """cost-tracker를 이용한 비용 로깅 (없으면 무시)"""
    if not COST_TRACKER_AVAILABLE:
        return
    try:
        cost = estimate_cost(
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
        print(
            f"[AgentRouter] 비용 추정 | 에이전트={agent or '?'} | 모델={model} "
            f"| 입력={input_tokens} | 출력={output_tokens} | ${cost:.6f}"
        )
    except Exception:
        pass


def get_usage_from_response(response_obj) -> tuple[int, int]:
    """응답 객체에서 토큰 사용량 추출"""
    try:
        usage = getattr(response_obj, "usage", None) or {}
        if hasattr(usage, "prompt_tokens"):
            return usage.prompt_tokens or 0, usage.completion_tokens or 0
        if isinstance(usage, dict):
            return usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)
    except Exception:
        pass
    return 0, 0


if LITELLM_AVAILABLE:
    class AgentRouter(CustomLogger):
        """에이전트별 최적 모델로 LiteLLM 요청을 동적 라우팅 + failover 지원"""

        # 요청별 failover 체인 저장 (request_id → {chain, model, agent, ...})
        _pending: dict[str, dict] = {}

        async def async_pre_call_hook(self, user_api_key_dict, cache, data, call_type):
            """요청 전처리: 에이전트 모델 힌트 적용 및 failover 체인 저장"""
            hint = read_model_hint()
            if not hint or "model" not in hint:
                return data

            original_model = data.get("model", "unknown")
            data["model"] = hint["model"]

            # 요청 ID 추출 (없으면 타임스탬프 기반)
            request_id = data.get("litellm_call_id", str(time.time()))

            # failover 체인 저장
            self._pending[request_id] = {
                "agent": hint.get("agent", ""),
                "original_model": original_model,
                "model": hint["model"],
                "failover_chain": hint.get("failover_chain", []),
                "failover_index": 0,
                "complexity_score": hint.get("complexity_score"),
                "routing_source": hint.get("source", ""),
            }

            print(
                f"[AgentRouter] {hint.get('agent', '?')} → {hint['model']} "
                f"(원래: {original_model}, complexity={hint.get('complexity_score', '?')}, "
                f"source={hint.get('source', '?')}, "
                f"failover={hint.get('failover_chain', [])})"
            )
            return data

        def log_success_event(self, kwargs, response_obj, start_time, end_time):
            """성공 이벤트: 메트릭 업데이트 + 비용 로깅"""
            model = kwargs.get("model", "unknown")
            _metrics[model]["success"] += 1

            # 요청 컨텍스트 조회
            request_id = kwargs.get("litellm_call_id", "")
            ctx = self._pending.pop(request_id, {})
            agent = ctx.get("agent", "")

            # 비용 로깅
            input_t, output_t = get_usage_from_response(response_obj)
            if input_t or output_t:
                log_cost(model, input_t, output_t, agent)

            print(
                f"[AgentRouter] 성공 | 모델={model} | 에이전트={agent or '?'} "
                f"| 성공합계={_metrics[model]['success']}"
            )

        def log_failure_event(self, kwargs, response_obj, start_time, end_time):
            """실패 이벤트: 메트릭 업데이트 + failover 에스컬레이션 시도"""
            model = kwargs.get("model", "unknown")
            _metrics[model]["failure"] += 1

            request_id = kwargs.get("litellm_call_id", "")
            ctx = self._pending.get(request_id, {})
            agent = ctx.get("agent", "")
            chain = ctx.get("failover_chain", [])
            idx = ctx.get("failover_index", 0)

            print(
                f"[AgentRouter] 실패 | 모델={model} | 에이전트={agent or '?'} "
                f"| 실패합계={_metrics[model]['failure']}"
            )

            # failover 체인에 남은 모델이 있으면 에스컬레이션 로깅
            if idx < len(chain):
                next_model = chain[idx]
                ctx["failover_index"] = idx + 1
                self._pending[request_id] = ctx
                print(
                    f"[AgentRouter] Failover 에스컬레이션: {model} → {next_model} "
                    f"(에이전트={agent or '?'}, 체인 {idx + 1}/{len(chain)})"
                )
            else:
                # 체인 소진 - 정리
                self._pending.pop(request_id, None)
                print(
                    f"[AgentRouter] Failover 체인 소진 | 에이전트={agent or '?'} "
                    f"| 최종 모델={model}"
                )

        def get_metrics(self) -> dict:
            """현재 인메모리 메트릭 반환"""
            return dict(_metrics)

    # LiteLLM에 콜백 등록
    agent_router_callback = AgentRouter()

else:
    # LiteLLM 미설치 환경에서 단독 테스트
    def read_hint_test():
        hint = read_model_hint()
        if hint:
            print(f"모델 힌트: {hint}")
            print(f"  에이전트: {hint.get('agent', '?')}")
            print(f"  모델: {hint.get('model', '?')}")
            print(f"  complexity: {hint.get('complexity_score', '?')}")
            print(f"  failover: {hint.get('failover_chain', [])}")
        else:
            print("힌트 없음 (기본 GLM-5 사용)")

    if __name__ == "__main__":
        read_hint_test()
