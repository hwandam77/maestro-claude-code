# 5대 GitHub 저장소 분석 — Maestro 6-Model 오케스트레이션 통합 관점

## 1. musistudio/claude-code-router (CCR)

### 아키텍처
- 로컬 프록시 서버 (port 3456)가 Claude Code 요청을 가로채 다른 모델로 라우팅
- `ANTHROPIC_BASE_URL`을 로컬 프록시로 설정하여 투명하게 동작
- `eval "$(ccr activate)"`로 환경변수 자동 설정

### 라우팅 방식
- **6가지 라우터 타입**: default, background, think, longContext, webSearch, image
- **config.json** 기반 Provider 설정 (API base URL + API key + models + transformer)
- **Custom Router**: JS 모듈 export → 요청 내용 분석 후 `"provider,model"` 반환, null이면 기본 라우터 fallback
- **Subagent 라우팅**: 프롬프트에 `<CCR-SUBAGENT-MODEL>provider,model</CCR-SUBAGENT-MODEL>` 태그 삽입

### Fallback
- Custom router가 null 반환 시 기본 라우터로 fallback
- Preset 시스템으로 설정 저장/공유 가능

### Maestro 통합 가치
- **높음**: 6개 모델을 요청 타입별로 자동 라우팅하는 핵심 인프라로 활용 가능
- longContext → Qwen3.5-122B (400K ctx), background → GLM-5, think → Claude 구독
- Custom Router로 역할별 라우팅 로직 구현 가능

---

## 2. starbaser/ccproxy

### 아키텍처
- **LiteLLM Proxy Server** 기반 Python 프록시 (v1.2.0)
- Claude Code 요청을 가로채 OpenAI, Gemini, Perplexity 등으로 라우팅
- `ccproxy run claude` 또는 환경변수 설정으로 투명 프록시

### 라우팅 방식
- **Rule 기반 라우팅** (ccproxy.yaml):
  - `MatchModelRule`: 모델명 매칭
  - `ThinkingRule`: thinking 필드 존재 시 라우팅
  - `TokenCountRule`: 토큰 수 임계값 초과 시 대용량 모델로 라우팅
  - `MatchToolRule`: 도구 사용 기반 (예: WebSearch → Perplexity)
- **Hook 체인**: rule_evaluator → model_router → forward_oauth → custom hooks
- **config.yaml** (LiteLLM 표준)로 model_list 정의

### 자체 호스팅 모델 지원
- **가능**: LiteLLM이 OpenAI 호환 API를 지원하므로 vLLM/Ollama 엔드포인트 설정 가능
- `api_base` 필드에 `http://10.5.5.x:8080/v1` 형태로 지정

### Maestro 통합 가치
- **매우 높음**: CCR보다 유연한 rule 기반 라우팅
- TokenCountRule로 긴 컨텍스트 → Qwen3.5 자동 라우팅
- MatchToolRule로 WebSearch → Gemini 라우팅
- LangFuse 연동으로 비용/성능 추적 가능
- OAuth 포워딩으로 Claude 구독 토큰 재사용

---

## 3. smtg-ai/claude-squad

### 아키텍처
- **tmux** 기반 격리된 터미널 세션으로 복수 에이전트 병렬 실행
- **git worktree**로 코드베이스 격리 (각 세션이 독립 브랜치)
- Go 기반 TUI 인터페이스로 세션 관리

### 멀티 CLI 지원
- `-p` 플래그로 프로그램 지정:
  - `cs -p "codex"` → Codex CLI
  - `cs -p "aider --model ollama_chat/gemma3:1b"` → Aider + Ollama
  - `cs -p "gemini"` → Gemini CLI
- `-y` 플래그로 자동 승인 (experimental)
- 설정 파일로 기본 프로그램 변경 가능

### Maestro 통합 가치
- **중간**: 병렬 에이전트 세션 관리에 유용
- Codex, Gemini, Claude를 동시에 다른 태스크에 할당 가능
- git worktree 격리로 충돌 없는 병렬 작업
- 단, 프로그래매틱 API가 아닌 TUI 기반이라 자동화 통합에 제약

---

## 4. EveryInc/compound-engineering-plugin

### 아키텍처
- Claude Code 플러그인 마켓플레이스 시스템
- `bunx @every-env/compound-plugin` CLI로 설치/동기화
- 11개 타겟 지원: OpenCode, Codex, Droid, Pi, Gemini, Copilot, Kiro, Windsurf, OpenClaw, Qwen

### 동기화 기능
- `~/.claude/skills/` → 심볼릭 링크로 타 도구에 동기화
- `~/.claude/commands/` → provider별 형식으로 변환 (prompts, workflows, skills)
- `~/.claude/settings.json` MCP 서버 → 타겟별 MCP 설정으로 변환
- `sync` 명령으로 전체 또는 특정 타겟 동기화

### Maestro 통합 가치
- **중간-높음**: 멀티 CLI 간 설정 일관성 유지
- Claude Code의 skills/commands를 Codex, Gemini에 자동 동기화
- MCP 서버 설정을 cross-tool로 공유
- 6개 모델 환경에서 일관된 프롬프트/스킬 관리

---

## 5. disler/claude-code-hooks-multi-agent-observability

### 아키텍처
```
Claude Agents → Hook Scripts (Python/uv) → HTTP POST → Bun Server → SQLite → WebSocket → Vue Client
```

### 모니터링 이벤트 (12종)
| 이벤트 | 설명 |
|--------|------|
| PreToolUse / PostToolUse | 도구 실행 전/후 |
| PostToolUseFailure | 도구 실패 |
| PermissionRequest | 권한 요청 |
| Stop | 응답 완료 |
| SubagentStart / SubagentStop | 서브에이전트 시작/종료 |
| PreCompact | 컨텍스트 압축 |
| UserPromptSubmit | 사용자 프롬프트 |
| SessionStart / SessionEnd | 세션 시작/종료 |
| Notification | 알림 |

### 대시보드
- Vue.js 실시간 클라이언트 (WebSocket)
- 세션별 컬러 코딩, 이벤트 필터링
- `--source-app` 파라미터로 프로젝트별 구분
- 에이전트 팀 구성 및 `/plan_w_team` 슬래시 커맨드

### Maestro 통합 가치
- **높음**: 6개 모델의 동시 실행 상태를 실시간 모니터링
- Hook 기반이라 기존 Maestro hook 시스템과 병합 가능
- SubagentStart/Stop으로 OMC 에이전트 위임 추적
- 비용/성능 분석을 위한 이벤트 로그 수집

---

## 통합 전략 요약

### 우선순위별 통합 로드맵

| 순위 | 저장소 | 통합 방식 | 기대 효과 |
|------|--------|----------|----------|
| 1 | **ccproxy** | LiteLLM 프록시로 6개 모델 rule-based 라우팅 | TokenCount→Qwen3.5, WebSearch→Gemini, Think→Claude 자동 분기 |
| 2 | **hooks-observability** | 기존 hook 시스템에 send_event.py 추가 | 6개 모델 실시간 모니터링 대시보드 |
| 3 | **compound-engineering** | `sync` 명령으로 skills/MCP 통합 | Claude↔Codex↔Gemini 설정 일관성 |
| 4 | **claude-code-router** | ccproxy 대안 또는 Custom Router JS 참고 | Subagent 라우팅 패턴 차용 |
| 5 | **claude-squad** | 병렬 세션 관리 도구로 선택적 사용 | Codex+Gemini+Claude 동시 실행 |

### Maestro 6-Model에 특화된 라우팅 설계

```yaml
# ccproxy 기반 권장 라우팅 규칙
rules:
  - TokenCountRule (>60K tokens) → nexus:8080 (Qwen3.5-122B, 400K ctx)
  - MatchToolRule (WebSearch) → Gemini 3.1 Pro
  - ThinkingRule (deep reasoning) → Claude 구독
  - MatchModelRule (background) → GLM-5 (ZAI, 저비용)
  - MatchToolRule (code generation) → Codex (gpt-5.3-codex)
  - Default → cognit:8000 (Qwen3-Coder-30B, 단순 코드)
```
