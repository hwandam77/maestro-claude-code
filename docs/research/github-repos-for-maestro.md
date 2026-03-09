# Maestro Claude Code - GitHub 레포지토리 리서치 결과

> 검색일: 2026-03-09 (2차 업데이트)
> 목적: 멀티 LLM 오케스트레이션 프로젝트 강화를 위한 참조 레포지토리 발굴
> 방법: gh search repos (10개 쿼리) + Tavily 웹 검색 (3개 쿼리)

---

## 1. Claude Code 플러그인 / 워크플로우 (최우선)

| # | 레포지토리 | Stars | 설명 | Maestro 활용 |
|---|-----------|-------|------|-------------|
| 1 | [obra/superpowers](https://github.com/obra/superpowers) | 73,975 | Claude Code plan-mode 확장, 가장 인기 있는 CC 플러그인 | 계획 수립 강화, think-before-code 패턴 |
| 2 | [affaan-m/everything-claude-code](https://github.com/affaan-m/everything-claude-code) | 67,512 | 에이전트 하네스 최적화 (skills, memory, security, research-first) | 이미 참조 중, hook/verify 패턴 심화 |
| 3 | [CherryHQ/cherry-studio](https://github.com/CherryHQ/cherry-studio) | 41,030 | AI 생산성 스튜디오, 300+ 어시스턴트, 통합 LLM 접근 | 멀티 LLM 통합 UI 참고 |
| 4 | [code-yeongyu/oh-my-openagent](https://github.com/code-yeongyu/oh-my-openagent) | 38,125 | 에이전트 하네스 (구 oh-my-opencode) | OMC 대안/보완 에이전트 하네스 |
| 5 | [thedotmack/claude-mem](https://github.com/thedotmack/claude-mem) | 33,506 | 세션 자동 캡처 + AI 압축 + 컨텍스트 재주입 플러그인 | 세션 간 컨텍스트 유지 강화 |
| 6 | [wshobson/agents](https://github.com/wshobson/agents) | 30,697 | 73 플러그인, 112 에이전트, 146 스킬, 79 개발도구 | 에이전트/스킬 대규모 컬렉션 확장 소스 |
| 7 | [EveryInc/compound-engineering-plugin](https://github.com/EveryInc/compound-engineering-plugin) | 10,077 | 공식 compound engineering 플러그인 (크로스 도구 동기화) | CC/Codex/Gemini 간 설정 동기화 |
| 8 | [parcadei/Continuous-Claude-v3](https://github.com/parcadei/Continuous-Claude-v3) | 3,593 | Hooks 기반 상태 관리 (ledger/handoff), MCP 컨텍스트 격리 | 에이전트 컨텍스트 격리 및 핸드오프 패턴 |
| 9 | [disler/claude-code-hooks-mastery](https://github.com/disler/claude-code-hooks-mastery) | 3,244 | Claude Code Hooks 마스터 가이드 | Hook 고급 패턴 학습 자료 |

## 2. 모델 라우팅 / 프록시 (핵심)

| # | 레포지토리 | Stars | 설명 | Maestro 활용 |
|---|-----------|-------|------|-------------|
| 10 | [musistudio/claude-code-router](https://github.com/musistudio/claude-code-router) | 29,212 | CC 기반 코딩 인프라, 커스텀 모델 라우팅 | **직접 관련** - Maestro와 동일 컨셉, 포크/참조 |
| 11 | [starbaser/ccproxy](https://github.com/starbaser/ccproxy) | 178 | CC 요청 Hook/수정, /model 커스텀 모델, 지능형 라우팅 | **핵심** - 프록시 기반 모델 라우팅 로직 |
| 12 | [steipete/claude-code-mcp](https://github.com/steipete/claude-code-mcp) | 1,167 | Claude Code를 원샷 MCP 서버로 사용 (agent-in-agent) | 에이전트 중첩 패턴 참고 |

## 3. AI 코딩 에이전트 / 터미널 도구

| # | 레포지토리 | Stars | 설명 | Maestro 활용 |
|---|-----------|-------|------|-------------|
| 13 | [plandex-ai/plandex](https://github.com/plandex-ai/plandex) | 15,062 | 대규모 프로젝트용 오픈소스 AI 코딩 에이전트 | 장기 태스크 오케스트레이션 패턴 |
| 14 | [humanlayer/humanlayer](https://github.com/humanlayer/humanlayer) | 9,734 | 복잡한 코드베이스에서 AI 에이전트 문제 해결 지원 | human-in-the-loop 패턴 |
| 15 | [smtg-ai/claude-squad](https://github.com/smtg-ai/claude-squad) | 6,264 | 터미널 멀티플렉서로 다수 AI 에이전트 병렬 실행/관리 | **직접 통합** - 병렬 에이전트 관리 |
| 16 | [moazbuilds/CodeMachine-CLI](https://github.com/moazbuilds/CodeMachine-CLI) | 2,366 | AI 코딩 에이전트를 반복 가능한 장기 워크플로우로 오케스트레이션 | 워크플로우 자동화 패턴 |
| 17 | [can1357/oh-my-pi](https://github.com/can1357/oh-my-pi) | 1,782 | 터미널 AI 에이전트 (hash-anchored edits, LSP, 서브에이전트) | 해시 앵커 편집 참고 |
| 18 | [asheshgoplani/agent-deck](https://github.com/asheshgoplani/agent-deck) | 1,402 | Claude/Gemini/Codex/OpenCode 통합 터미널 세션 관리자 TUI | **직접 관련** - 멀티 CLI 통합 관리 |

## 4. 에이전트 협업 / 통신

| # | 레포지토리 | Stars | 설명 | Maestro 활용 |
|---|-----------|-------|------|-------------|
| 19 | [Dicklesworthstone/mcp_agent_mail](https://github.com/Dicklesworthstone/mcp_agent_mail) | 1,780 | AI 에이전트 간 비동기 통신 (인박스, 스레드, 파일 잠금) | 멀티 에이전트 간 비동기 조율 |
| 20 | [disler/claude-code-hooks-multi-agent-observability](https://github.com/disler/claude-code-hooks-multi-agent-observability) | - | 멀티에이전트 실시간 모니터링 (Hook 이벤트 트래킹) | **직접 관련** - 오케스트레이션 관찰성 |

## 5. 프롬프트 오케스트레이션

| # | 레포지토리 | Stars | 설명 | Maestro 활용 |
|---|-----------|-------|------|-------------|
| 21 | [microsoft/poml](https://github.com/microsoft/poml) | 4,863 | Prompt Orchestration Markup Language (Microsoft 공식) | 프롬프트 오케스트레이션 표준화 |

## 6. 큐레이션 리스트 / 리소스 허브

| # | 레포지토리 | Stars | 설명 | Maestro 활용 |
|---|-----------|-------|------|-------------|
| 22 | [hesreallyhim/awesome-claude-code](https://github.com/hesreallyhim/awesome-claude-code) | 26,918 | skills, hooks, 슬래시커맨드, 플러그인 큐레이션 | 도구 디스커버리 허브 |
| 23 | [VoltAgent/awesome-claude-code-subagents](https://github.com/VoltAgent/awesome-claude-code-subagents) | 12,921 | 100+ 전문 서브에이전트 컬렉션 | 에이전트 확장 소스 |
| 24 | [rohitg00/awesome-claude-code-toolkit](https://github.com/rohitg00/awesome-claude-code-toolkit) | 658 | 135 에이전트, 35 스킬, 42 커맨드, 120 플러그인, 19 hooks | 종합 툴킷 참고 |
| 25 | [ccplugins/awesome-claude-code-plugins](https://github.com/ccplugins/awesome-claude-code-plugins) | - | 슬래시커맨드, 서브에이전트, MCP, hooks 큐레이션 | 플러그인 디스커버리 |
| 26 | [VoltAgent/awesome-agent-skills](https://github.com/VoltAgent/awesome-agent-skills) | - | 500+ 에이전트 스킬 (CC, Codex, Gemini 호환) | 크로스 도구 스킬 확장 |
| 27 | [subinium/awesome-claude-code](https://github.com/subinium/awesome-claude-code) | 64 | MCP, 스킬, 플러그인 큐레이션 (한국인 관리) | 한국어 커뮤니티 연결 |

## 7. vLLM / 셀프호스팅

| # | 레포지토리 | Stars | 설명 | Maestro 활용 |
|---|-----------|-------|------|-------------|
| 28 | [amirrouh/vllm-manager](https://github.com/amirrouh/vllm-manager) | 3 | 터미널 기반 vLLM 관리 UI | cognit/nexus 서버 관리 참고 (소규모) |

---

## 통합 우선순위 TOP 10

| 순위 | 레포지토리 | Stars | 핵심 가치 |
|------|-----------|-------|----------|
| 1 | **musistudio/claude-code-router** | 29,212 | Maestro와 동일 컨셉, CC 기반 모델 라우팅 인프라 |
| 2 | **smtg-ai/claude-squad** | 6,264 | 다수 AI 에이전트 병렬 실행/관리 터미널 멀티플렉서 |
| 3 | **starbaser/ccproxy** | 178 | CC 요청 Hook + 커스텀 모델 라우팅 프록시 |
| 4 | **EveryInc/compound-engineering-plugin** | 10,077 | CC/Codex/Gemini 크로스 도구 설정 동기화 |
| 5 | **asheshgoplani/agent-deck** | 1,402 | Claude/Gemini/Codex 통합 TUI 세션 관리 |
| 6 | **thedotmack/claude-mem** | 33,506 | 세션 간 컨텍스트 자동 캡처/압축/주입 |
| 7 | **disler/hooks-multi-agent-observability** | - | 멀티에이전트 Hook 기반 실시간 모니터링 |
| 8 | **parcadei/Continuous-Claude-v3** | 3,593 | 에이전트 컨텍스트 격리 + 핸드오프 패턴 |
| 9 | **Dicklesworthstone/mcp_agent_mail** | 1,780 | 에이전트 간 비동기 메시징 레이어 |
| 10 | **microsoft/poml** | 4,863 | 프롬프트 오케스트레이션 마크업 표준화 |

---

## Sources
- gh search repos: 10개 카테고리 (claude-code-hooks, llm-routing, ai-coding-agent, claude-code, prompt-orchestration, vllm-management, multi-agent-framework, llm-orchestration, model-router, awesome-claude-code)
- Tavily: "claude code plugins 2026", "multi-agent AI coding framework 2026", "awesome claude code 2026"
