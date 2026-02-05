# Maestro Claude Code — 멀티모델 Claude Code 에이전트 구성 계획서

> **Maestro Claude Code**: 거장/지휘자. 🎼Maestro(Opus) + 🎻Concertmaster(GLM) + 🎹Principal(GPT-5.2) + 🥁Ensemble(Qwen3) — 50개 전문 에이전트를 4개 백엔드 모델로 지휘하는 오케스트라 시스템.

**작성일**: 2026-02-05
**프로젝트명**: Maestro Claude Code
**상태**: 연구 완료, 최종 아키텍처 확정, oh-my-claudecode 50에이전트 통합 + 모델 페르소나(오케스트라) + 플러그인 가이드(OMC/Router/claude-mem) + Ultra-Thin 4계층 통신 아키텍처 + Signal Protocol v1.0 + claude-labs 채택(ADOPT 5 + MERGE 11) + Docker + MCP 공유 + 리스크 매트릭스 반영 완료, Phase 1-3 구현 준비 완료
**관련 리포트**: `docs/리포트/cognit_vllm_benchmark_20260205.md`
**프로젝트 루트**: `/Users/hwandam/workspace/maestro-claude-code/`

---

## 📑 목차

| # | 섹션 | 줄 | 핵심 내용 |
|---|------|-----|----------|
| **1** | [개요](#1-개요) | L12 | 목표, 핵심 컨셉, 설계 결정, 아키텍처, 모델 페르소나(오케스트라) |
| **2** | [모델별 벤치마크 비교](#2-모델별-벤치마크-비교) | L149 | 성능 매트릭스, Tool Calling, 컨텍스트, 강점/약점 |
| **3** | [개발 환경 및 인프라](#3-개발-환경-및-인프라) | L261 | Docker(Ubuntu 22.04), 서버 상태, vLLM 플래그, Cognit 벤치마크 |
| **4** | [기술 연구 결과](#4-기술-연구-결과) | L403 | LLM 연결 방식, 라우팅 비교, API 제공자, MCP 공유, 에이전트 통합(50개) |
| **5** | [최종 구성](#5-최종-구성) | L832 | config.json, Transformer, fallback, API 키 관리, 실행 방법 |
| **6** | [구현 계획](#6-구현-계획) | L1211 | Phase 1~4 단계별 실행 계획 |
| **7** | [비용 분석](#7-비용-분석) | L1307 | 현재 vs 하이브리드 비용, 절감 효과 |
| **8** | [제약 사항 및 주의사항](#8-제약-사항-및-주의사항) | L1354 | 16K 토큰 버짓 ⭐, Tool Calling, GLM 제약, 리스크 매트릭스, **Ultra-Thin 4계층 통신** ⭐⭐⭐, 폴백 |
| **9** | [모델별 최적 사용 시나리오](#9-모델별-최적-사용-시나리오) | L2292 | 작업 유형별 1순위, 라우터 매핑, 수동 전환 |
| **10** | [구현 Task 세분화](#10-구현-task-세분화) | L2329 | T1~T15 목록, 의존성 그래프, Phase별 일정 |
| **11** | [검증 체크리스트](#11-검증-체크리스트) | L2428 | Phase 0~4 완료 기준, OMC 통합 검증 |
| **12** | [참고 자료](#12-참고-자료) | L2522 | 공식 문서, 벤치마크, 커뮤니티, 플러그인 |
| **13** | [플러그인 설치 및 설정 가이드](#13-플러그인-설치-및-설정-가이드) | L2585 | OMC, Router, claude-mem, MCP, **claude-labs 채택** |

<details>
<summary><b>📋 세부 목차 펼치기 (전체 ~80개 소섹션)</b></summary>

### 1. 개요
- 1.1 목표 · 1.2 핵심 컨셉 · 1.3 주요 설계 결정
- 1.4 아키텍처 다이어그램 · 1.5 모델 페르소나 — 오케스트라 🎼

### 2. 모델별 벤치마크 비교
- 2.1 종합 성능 매트릭스 · 2.2 Tool Calling & 코드 리뷰 · 2.3 컨텍스트 & 속도
- 2.4 강점/약점: Opus 4.5 · GLM-4.7 · GPT-5.2 · Qwen3-Coder · DeepSeek-R1

### 3. 개발 환경 및 인프라
- 3.0 Docker 개발 환경 (Dockerfile, compose, 네트워크)
- 3.1 서버 상태 · 3.2 vLLM 실행 플래그 · 3.3 Cognit 벤치마크

### 4. 기술 연구 결과
- 4.1 LLM 연결 방식 (A: 직접 / B: LiteLLM / C: claude-code-router ⭐)
- 4.2 라우팅 상세 비교 · 4.3 API 제공자 (Z.AI, OpenAI, Anthropic)
- 4.4 Gemini 3 Pro 거부 이유 · 4.5 MCP 도구 공유 아키텍처
- 4.6 최종 라우팅 전략 + 트래픽 분배
- 4.7 oh-my-claudecode 멀티에이전트 통합 ⭐ (50개 에이전트-모델 매핑, 티어 조정, 실행 모드)

### 5. 최종 구성
- 5.1 config.json · 5.2 설정 설명 (Providers, Transformer, Router, fallback)
- 5.3 환경 변수 · 5.4 API 키 통합관리 (.env, 키 주입, 보안)
- 5.5 실행 방법 · 5.6 DeepSeek 추가 (선택)

### 6. 구현 계획
- Phase 1: Qwen3×2 + Opus · Phase 2: GLM-4.7 · Phase 3: 4모델 최종 · Phase 4: DeepSeek

### 7. 비용 분석
- 7.1 현재 · 7.2 하이브리드 후 · 7.3 절감 효과 · 7.4 세부 분석

### 8. 제약 사항 및 주의사항
- 8.1 Qwen3 16K 토큰 버짓 ⭐ (소진 시뮬레이션, 파일 크기별)
- 8.2 Tool Calling 호환성 · 8.3 네트워크 경로 · 8.4 GLM-4.7 제약
- 8.5 리스크 매트릭스 + **R3: 16K Task 분리** + **Ultra-Thin 4계층 통신** ⭐⭐⭐
  - Signal Protocol v1.0 · 에스컬레이션 · 모델별 통신 규칙 · 컨텍스트 절감(97%/99.2%)
  - run_in_background 상태 · 에이전트 라이프사이클 · 모드 선택 가이드
- 8.6 폴백 체인 · 8.7 served-model-name 규칙

### 9. 모델별 최적 사용 시나리오
- 9.1 작업 유형별 1순위 · 9.2 라우터 자동 매핑 · 9.3 수동 전환

### 10. 구현 Task 세분화
- 10.1 Task 목록 (T1~T15) · 10.2 의존성 그래프
- 10.3 상세: T13(티어 수정), T14(ecomode 보호), T15(ultrawork 검증) · 10.4 일정 추정

### 11. 검증 체크리스트
- 11.1~11.4 Phase 0~3 완료 기준
- 11.5 OMC 통합 (라우팅, 병렬, 실행모드, GLM concurrency, MCP, Fallback)
- 11.6 Phase 4 (선택)

### 12. 참고 자료
- 12.1 공식 문서 · 12.2 벤치마크 · 12.3 커뮤니티 · 12.4 플러그인

### 13. 플러그인 설치 및 설정 가이드
- 13.1 oh-my-claudecode (설치, 설정마법사, 모드, 티어, 스킬, HUD)
- 13.2 claude-code-router v2.0.0 (CLI, Custom Router, Preset, Subagent, Statusline, Transformer 16종)
- 13.3 claude-mem (아키텍처, 3-Layer 검색, 통합 전략)
- 13.4 MCP 서버 (Tavily, Context7, Playwright, Memory, 모델별 안전 매핑)
- **13.5 claude-labs 채택 항목** ⭐
  - 13.5.1 ADOPT (5): ultra-thin-orchestrate, systematic-debugging, guardrails, reasoning, reverse
  - 13.5.2 MERGE (11): TASKS.md 의존성, verification, evaluation, rag, deep-research, Hook, JSON 스키마, Constitution, Gemini 하이브리드, TDD, Defense-in-Depth
  - 13.5.3 SKIP 사유 (43개/72%)
  - 13.5.4 구현 태스크 매핑 (T16~T27)

</details>

---

## 1. 개요

### 1.1 목표

Claude Code CLI에서 **역할별로 다른 LLM 모델을 자동 라우팅**하여, 비용 효율과 성능을 동시에 최적화하는 하이브리드 에이전트 시스템 구축.

### 1.2 핵심 컨셉

```
🎼 Maestro (마에스트로)     — Claude Opus 4.5   — 지휘자       사용률: 10%
🎻 Concertmaster (콘서트마스터) — GLM-4.7       — 제1바이올린   사용률: 35%
🎹 Principal (프린치팔)     — GPT-5.2 Codex     — 수석 연주자   사용률: 5%
🥁 Ensemble (앙상블)        — Qwen3-Coder       — 섹션 단원     사용률: 50%
```

### 1.3 주요 설계 결정

**✅ 채택**:
- Opus: 계획 및 코드 리뷰 전용 (SWE-bench 80.9%, 0% tool error)
- GLM-4.7: 메인 코딩 엔진 (SWE-bench 73.8%, 비용 효율)
- GPT-5.2 Codex: 대규모 코드베이스 분석 (400K 컨텍스트, SWE-bench 80.0%)
- Qwen3-Coder: 빠른 백그라운드 작업 (180 tok/s, 로컬 무료)
- 모든 API는 **직접 연결** (Anthropic + Z.AI + OpenAI)

**❌ 거부**:
- Gemini 3 Pro: 85-88% 환각률, 컨텍스트 메모리 열화, tool calling 불안정
- OpenRouter: 사용자 요청에 따라 모든 API는 직접 연결 사용

### 1.4 아키텍처 다이어그램

```
┌─────────────────────────────────────────────────────────────────────┐
│  Docker Container (Ubuntu 22.04)                                     │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  oh-my-claudecode (오케스트레이션 레이어)                       │  │
│  │                                                               │  │
│  │  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐  │  │
│  │  │autopilot│ │ultrawork │ │  ralph   │ │  ecomode/swarm   │  │  │
│  │  └────┬────┘ └────┬─────┘ └────┬─────┘ └───────┬──────────┘  │  │
│  │       └───────────┼────────────┼────────────────┘             │  │
│  │                   ▼                                           │  │
│  │  ┌───────────────────────────────────────────────────────┐   │  │
│  │  │  50개 전문 에이전트                                     │   │  │
│  │  │  opus(16) → architect, planner, critic, analyst...     │   │  │
│  │  │  sonnet(20) → executor, researcher, designer...        │   │  │
│  │  │  haiku(14) → executor-low, writer, build-fixer-low...  │   │  │
│  │  └───────────────────────┬───────────────────────────────┘   │  │
│  └──────────────────────────┼────────────────────────────────────┘  │
│                             ▼                                       │
│  ┌───────────────┐  ┌────────────────────────────────────────┐     │
│  │  Claude Code  │  │  MCP Servers (공유)                     │     │
│  │   (CLI)       │──│  filesystem, git, memory, playwright,   │     │
│  │   model=X     │  │  context7, tavily, gemini, youtube      │     │
│  └──────┬────────┘  └────────────────────────────────────────┘     │
│         │                                                           │
│  ┌──────▼─────────────────────────────────────┐                    │
│  │  claude-code-router (:8081)                 │                    │
│  │  모델명 기반 자동 라우팅                      │                    │
│  │  opus→think | sonnet→default | haiku→bg     │                    │
│  └──┬──────┬──────┬──────────────┬────────────┘                    │
└─────┼──────┼──────┼──────────────┼──────────────────────────────────┘
      ▼      ▼      ▼              ▼
 ┌──────┐ ┌──────┐ ┌──────────┐ ┌────────┐
 ┌──────┐ ┌──────┐ ┌──────────┐ ┌────────┐
 │🎼Opus│ │🎻GLM │ │🎹GPT-5.2 │ │🥁Qwen3 │
 │Mstro │ │Cncrt │ │Principal │ │Ensembl │
 │16 agt│ │20 agt│ │auto 60K+ │ │14 agt  │
 │ 10%  │ │ 35%  │ │  5%      │ │ 50%    │
 └──────┘ └──────┘ └──────────┘ └────────┘
Anthropic  Z.AI     OpenAI      Cognit
  API      API       API       10.5.5.11
  (Internet)                  (VPN/Docker)
```

**핵심 설계**:
- **oh-my-claudecode**: 50개 에이전트 × 7개 실행 모드 × 37개 스킬로 병렬 오케스트레이션
- **claude-code-router**: 에이전트 티어(opus/sonnet/haiku)를 모델명으로 자동 라우팅
- **MCP 도구 공유**: Claude Code 클라이언트가 관리 → 어떤 백엔드 모델이든 동일한 MCP 도구 사용

### 1.5 모델 페르소나 — 오케스트라 🎼

> **Maestro Claude Code**라는 프로젝트명처럼, 4개 모델은 **교향악단**의 멤버로서 각자의 악기와 역할을 가진다. 지휘자(Maestro)가 전체 흐름을 설계하고, 콘서트마스터가 주선율을 이끌며, 수석 연주자가 특수 파트를 소화하고, 섹션 단원들이 대량의 리듬을 빠르게 채운다.

| 페르소나 | 모델 | 오케스트라 역할 | 태그라인 | 핵심 특성 |
|---------|------|---------------|---------|----------|
| 🎼 **Maestro** (마에스트로) | Claude Opus 4.5 | **Conductor** (지휘자) | "모든 음표가 완벽한 조화를 이루도록" | 전체 흐름 설계, 깊은 통찰, 완벽주의 |
| 🎻 **Concertmaster** (콘서트마스터) | GLM-4.7 | **First Violin** (제1바이올린) | "모든 멜로디의 중심" | 가장 많은 연주량, 다재다능, 신뢰의 중심축 |
| 🎹 **Principal** (프린치팔) | GPT-5.2 Codex | **Principal Player** (수석 연주자) | "깊이와 넓이를 아우르는 전문가" | 특수 솔로, 방대한 악보(400K), 희소 호출 |
| 🥁 **Ensemble** (앙상블) | Qwen3-Coder | **Section Players** (섹션 단원) | "빠르고 끊임없는 리듬" | 대량 병렬 처리, 최고 속도, 무료 투입 |

#### 페르소나별 상세

**🎼 Maestro (마에스트로) — Claude Opus 4.5**
- **상징**: 지휘봉, 악보 (완벽한 설계도)
- **역할**: 작전의 총지휘자. 계획 수립, 아키텍처 설계, 코드 리뷰, 완료 검증
- **성격**: 신중하고 완벽주의적. 빠르진 않지만 한 번의 지시로 정확한 방향을 제시
- **SWE-bench**: 80.9% (업계 1위), Tool Error: 0%, 보안 탐지: 100%
- **사용 패턴**: 세션당 1-2회만 호출되지만, 모든 작업의 품질을 결정하는 핵심

**🎻 Concertmaster (콘서트마스터) — GLM-4.7**
- **상징**: 바이올린 (주선율의 리더)
- **역할**: 오케스트라의 실질적 리더. 대부분의 코딩 작업을 소화하는 주역
- **성격**: 만능형. 코딩, UI 생성("Vibe Coding"), 리팩토링을 두루 소화
- **SWE-bench**: 73.8%, τ²-Bench(Tool Use): 87.4%, 비용: $0.60/$2.20 (Opus의 1/11)
- **사용 패턴**: 35%의 트래픽을 안정적으로 처리. 지휘자 다음으로 신뢰받는 존재

**🎹 Principal (프린치팔) — GPT-5.2 Codex**
- **상징**: 그랜드 피아노 (깊이 있는 솔로)
- **역할**: 특수한 상황에서 호출되는 수석 연주자. 방대한 악보(400K 컨텍스트)를 읽어내는 전문가
- **성격**: 과묵하지만 호출되면 압도적. 400K 토큰의 대규모 코드베이스를 한 번에 분석
- **SWE-bench**: 80.0%, SWE-bench Pro: 55.6% (SOTA), AIME 2025: 100%
- **사용 패턴**: 5%만 호출되지만, longContext(60K+) 자동 전환으로 빛을 발함

**🥁 Ensemble (앙상블) — Qwen3-Coder**
- **상징**: 타악기 섹션 (빠르고 끊임없는 리듬)
- **역할**: 대량의 반복 작업을 빠르게 처리하는 섹션 단원들
- **성격**: 빠르고 부지런함. 180 tok/s로 단순 작업을 순식간에 완료. 5명 동시 투입 가능
- **SWE-bench**: 50.3% (로컬 모델 중 우수), 속도: 180 tok/s, 비용: 무료 (로컬)
- **사용 패턴**: 50%의 트래픽. ultrawork 모드에서 5개 병렬 실행 시 ~750 tok/s 총 처리량

#### 오케스트라 협업 시나리오

```
🎼 Maestro: "이번 교향곡(프로젝트)의 구조를 설계한다" → architect, planner
     ↓
🎻 Concertmaster: "주선율(메인 코딩)을 이끈다" → executor, designer, researcher
     ↓
🥁 Ensemble ×5: "리듬 섹션(병렬 단순 작업)을 빠르게 채운다" → executor-low ×5
     ↓
🎹 Principal: "특수 솔로(대규모 분석)를 소화한다" → longContext 자동 전환
     ↓
🎼 Maestro: "최종 리허설(검증)을 지휘한다" → architect, code-reviewer, security-reviewer
```

---

## 2. 모델별 벤치마크 비교

### 2.1 종합 성능 매트릭스

| 벤치마크 | Claude Opus 4.5 (10%) | GLM-4.7 355B (35%) | GPT-5.2 Codex (5%) | Qwen3-Coder-30B (50%) | DeepSeek-R1-70B (<1%) |
|---------|----------------------|---------------------|---------------------|------------------------|------------------------|
| **SWE-bench Verified** | **80.9%** 🥇 | **73.8%** 🥉 | **80.0%** 🥈 | 50.3% | ~67% |
| **SWE-bench Pro** | - | - | **55.6%** (SOTA) | - | - |
| **LiveCodeBench** | - | **84.9%** | - | - | - |
| **τ²-Bench (Tool Use)** | 87.2% | **87.4%** | - | 49.0% | - |
| **Terminal-Bench 2.0** | **59.3%** | - | - | - | - |
| **AIME 2024** | - | 91.6% | - | 85.0% | **70%** |
| **AIME 2025** | - | 95.7% | **100%** 🥇 | - | - |
| **MATH-500** | - | - | - | - | **94.5%** |
| **GPQA Diamond** | - | **85.7%** | - | - | 82.4% |
| **HLE (with Tools)** | - | **42.8%** | - | - | 40.8% |
| **Codeforces Rating** | - | - | - | - | 1633 |

### 2.2 Tool Calling & 코드 리뷰 성능

| 모델 | 사용률 | Tool Error Rate | 코드 리뷰 속도 | 보안 버그 탐지율 |
|------|--------|----------------|---------------|----------------|
| **Claude Opus 4.5** | **10%** | **0%** 🥇 | **1분** 🥇 | **100%** 🥇 |
| GLM-4.7 | **35%** | ~13% (comparable to Claude 87.2% in τ²) | - | - |
| GPT-5.2 Codex | **5%** | 불안정 (OpenRouter), 직접 API 개선 예상 | - | - |
| Qwen3-Coder-30B | **50%** | 안정 (qwen3_coder parser) | - | - |
| DeepSeek-R1-70B | **<1%** | 불안정 (실험적) | - | - |

### 2.3 컨텍스트 윈도우 & 속도

| 모델 | 사용률 | 컨텍스트 윈도우 | 속도 (tok/s) | 비용 (Input/Output) |
|------|--------|----------------|--------------|-------------------|
| Claude Opus 4.5 | **10%** | 200K | 79 | $5/$25 per 1M |
| GLM-4.7 | **35%** | **200K** | API 지연 있음 | **$0.60/$2.20** per 1M |
| GPT-5.2 Codex | **5%** | **400K** 🥇 | 느림 | $1.75/$14.00 per 1M |
| Qwen3-Coder-30B | **50%** | 16K (VRAM 제한) | **180** 🥇 | 전기세만 (로컬) |
| DeepSeek-R1-70B | **<1%** | 16K (VRAM 제한) | 30-50 | 전기세만 (로컬) |

### 2.4 강점 & 약점 분석

#### Claude Opus 4.5
**강점**:
- SWE-bench 80.9% (업계 1위)
- Tool calling 에러율 0% (완벽한 안정성)
- 코드 리뷰: 1분 완료, 100% 보안 탐지
- Edge case 감지, 아키텍처 설계 최강

**약점**:
- 비용 매우 높음 ($5/$25)
- 속도 느림 (79 tok/s)
- Over-engineering 경향

**최적 역할**: 전략 계획, 아키텍처 설계, 코드 리뷰, 복잡한 디버깅

#### GLM-4.7 (355B MoE)
**강점**:
- SWE-bench 73.8% (오픈 모델 최강)
- LiveCodeBench 84.9%
- Tool use 87.4% (Claude 수준)
- UI 생성 우수 ("Vibe Coding")
- 비용 매우 저렴 ($0.60/$2.20, Opus 대비 1/11)
- 200K 컨텍스트

**약점**:
- Concurrency limit=1 (Claude Code는 순차 실행이라 문제 없음)
- 100K+ 컨텍스트에서 tool call 버그 보고 있음

**최적 역할**: 일상 코딩, 멀티파일 리팩토링, UI 생성, 에이전틱 작업

#### GPT-5.2 Codex
**강점**:
- SWE-bench 80.0% (2위), Pro 55.6% (SOTA)
- 400K 컨텍스트 (업계 최대)
- AIME 2025 100% (완벽한 수학 추론)
- 대규모 코드베이스 분석 최강

**약점**:
- OpenRouter 경유 시 tool calling 불안정 (직접 API 사용으로 개선 예상)
- 속도 느림
- 비용 높음 ($1.75/$14, 사용자는 비용 무관하다고 함)

**최적 역할**: 대규모 코드베이스 분석, 복잡한 코딩, 수학적 추론

#### Qwen3-Coder-30B
**강점**:
- 속도 180 tok/s (가장 빠름)
- 로컬 무료
- Tool calling 안정 (qwen3_coder parser)
- SWE-bench 50.3% (로컬 모델 중 우수)

**약점**:
- 16K 컨텍스트 제한 (VRAM)
- 복잡한 추론, 아키텍처 설계 약함

**최적 역할**: 빠른 코드 생성, 백그라운드 작업, 단일 파일 편집

#### DeepSeek-R1-70B (선택사항)
**강점**:
- AIME 2024 70%
- MATH-500 94.5%
- Chain-of-thought 추론 강력
- Codeforces 1633

**약점**:
- Tool calling 불안정 (실험적)
- 속도 느림 (30-50 tok/s)
- VRAM 35-40GB 필요 (RTX 3090 2개 필요)

**최적 역할**: 깊은 추론, 알고리즘 디버깅, 수학 문제 (tool calling 없이 수동 사용)

---

## 3. 개발 환경 및 인프라

### 3.0 Docker 개발 환경 (Ubuntu 22.04)

**설계 원칙**: Claude Code + 라우터 + MCP 서버를 단일 Docker 컨테이너에 패키징하여 재현 가능한 개발 환경 구축.

#### Dockerfile 구성

```dockerfile
FROM ubuntu:22.04

# 기본 패키지
RUN apt-get update && apt-get install -y \
    curl git wget sudo build-essential \
    python3 python3-pip \
    wireguard-tools iproute2 \
    && rm -rf /var/lib/apt/lists/*

# Node.js 20 LTS
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs

# Claude Code CLI + 라우터
RUN npm install -g @anthropic-ai/claude-code @musistudio/claude-code-router

# MCP 서버 설치
RUN npm install -g \
    @anthropic-ai/claude-code-mcp-server-filesystem \
    @anthropic-ai/claude-code-mcp-server-memory \
    @anthropic-ai/claude-code-mcp-server-git

# Playwright (웹 테스트용)
RUN npx playwright install --with-deps chromium

# 작업 디렉토리
WORKDIR /workspace
VOLUME ["/workspace", "/root/.claude", "/root/.claude-code-router"]

# 라우터 포트 (claude-code-router 기본 포트: 3456)
EXPOSE 3456

# 환경변수 (ccr activate가 자동 설정하지만, Docker 내부에서는 명시적 설정)
ENV ANTHROPIC_BASE_URL=http://localhost:3456/v1/messages
ENV ANTHROPIC_AUTH_TOKEN=dummy

CMD ["bash"]
```

#### docker-compose.yml

```yaml
version: '3.8'
services:
  claude-agent:
    build: .
    container_name: claude-multi-agent
    volumes:
      - ./workspace:/workspace
      - ./config/claude:/root/.claude
      - ./config/router:/root/.claude-code-router
      - /var/run/docker.sock:/var/run/docker.sock  # Docker-in-Docker (선택)
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - ZAI_API_KEY=${ZAI_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_BASE_URL=http://localhost:3456/v1/messages
      - ANTHROPIC_AUTH_TOKEN=dummy
    networks:
      - vllm-net
    dns:
      - 8.8.8.8
    ports:
      - "3456:3456"   # 라우터 (기본 포트)
    stdin_open: true
    tty: true

networks:
  vllm-net:
    driver: bridge
    # VPN 또는 host network로 vLLM 서버 접근
    # 대안: network_mode: "host" (VPN이 호스트에 있을 경우)
```

#### 네트워크 구성 옵션

| 옵션 | 방법 | vLLM 접근 | Cloud API | macOS 호환 |
|------|------|----------|-----------|-----------|
| ~~A: Host Network~~ | ~~`network_mode: host`~~ | ~~VPN 경유~~ | ~~✅ 직접~~ | ❌ **불가** |
| **B: Port Forward** ⭐ | 호스트에서 `ssh -L 8000:10.5.5.11:8000` | localhost:8000 | ✅ 직접 | ✅ |
| **C: WireGuard in Container** | 컨테이너 내 wg0 | VPN 직접 | ✅ 직접 | ✅ (복잡) |
| **D: 네이티브 실행** ⭐⭐ | Docker 없이 Mac에서 직접 실행 | VPN 경유 (호스트 wg0) | ✅ 직접 | ✅ (최적) |

> ⚠️ **Docker Desktop for Mac은 `network_mode: host`를 지원하지 않는다** (Linux 전용). 따라서 옵션 A는 macOS에서 사용 불가.

**권장 순위**:
1. **옵션 D (네이티브 실행)** — Mac에서 직접 `ccr code` 실행. 가장 간단하고 VPN/MCP 접근에 제약 없음. 단일 사용자 환경에 최적.
2. **옵션 B (Port Forward)** — Docker가 필요한 경우. 호스트에서 SSH 터널로 vLLM 접근.
3. **옵션 C (WireGuard in Container)** — 완전 격리가 필요한 경우. 설정 복잡.

> **참고**: Docker 공식 Claude Code 샌드박스 템플릿(`docker/sandbox-templates:claude-code`)도 존재하나, 우리 설정(라우터 + MCP + VPN)은 네이티브 실행 또는 커스텀 이미지가 더 적합.

### 3.1 서버 현황

### 3.1 서버 상태 (2026-02-05 확인)

| 서버 | IP | GPU | 현재 모델 | vLLM 상태 |
|------|-----|-----|----------|-----------|
| **Nexus** | 10.5.5.14 / 192.168.1.1 | 2x RTX 3090 (48GB) | Qwen3-Coder-30B-A3B | 실행 중 |
| **Cognit** | 10.5.5.11 / 192.168.1.2 | 2x RTX 3080 Ti (24GB) | Qwen3-Coder-30B-A3B | 실행 중 |

### 3.2 vLLM 실행 플래그 (공통)

```bash
python -m vllm.entrypoints.openai.api_server \
  --model /home/hwandam/models/Qwen3-Coder-30B-A3B-Instruct-W4A16-awq \
  --served-model-name Qwen3-Coder-30B-A3B \
  --tensor-parallel-size 2 \
  --max-model-len 16384 \
  --max-num-seqs 8 \
  --max-num-batched-tokens 2048 \
  --gpu-memory-utilization 0.93 \
  --enable-prefix-caching \
  --enable-chunked-prefill \
  --enable-auto-tool-choice \
  --tool-call-parser qwen3_coder \
  --host 0.0.0.0 --port 8000
```

**핵심**: `--enable-auto-tool-choice --tool-call-parser qwen3_coder` 이미 설정 완료 → Claude Code tool calling 지원 준비됨.

### 3.3 Cognit 벤치마크 결과 요약

| 지표 | 값 |
|------|-----|
| 단일 요청 TPS | ~180 tok/s |
| 8 동시 요청 Aggregate | 1,080 tok/s |
| 최대 컨텍스트 활용 | 16,256 tokens (98.2%) |
| GPU 온도 (피크) | 67°C / 62°C |
| 응답 일관성 | σ < 15ms |

---

## 4. 기술 연구 결과

### 4.1 Claude Code와 LLM 연결 방식

#### 방식 A: 직접 연결 (단일 모델)

vLLM은 **Anthropic Messages API를 직접 구현**하므로 환경변수만 설정하면 연결 가능.

**vLLM 공식 문서**: `docs.vllm.ai/en/latest/serving/integrations/claude_code/`

```bash
ANTHROPIC_BASE_URL=http://10.5.5.11:8000 \
ANTHROPIC_API_KEY=dummy \
ANTHROPIC_AUTH_TOKEN=dummy \
ANTHROPIC_DEFAULT_OPUS_MODEL=Qwen3-Coder-30B-A3B \
ANTHROPIC_DEFAULT_SONNET_MODEL=Qwen3-Coder-30B-A3B \
ANTHROPIC_DEFAULT_HAIKU_MODEL=Qwen3-Coder-30B-A3B \
claude
```

**한계**: 모든 티어가 동일 모델로 라우팅. 멀티모델 불가.

#### 방식 B: LiteLLM Proxy (멀티모델 라우팅)

LiteLLM이 중간에서 Anthropic API ↔ OpenAI API 포맷 변환 및 모델별 라우팅 수행.

**장점**: 안정적, 폴백 지원, 모니터링, 예산 제한
**단점**: Docker 필요, 별도 프로세스 관리

#### 방식 C: claude-code-router (작업 유형별 라우팅) ⭐ 최종 채택

npm 패키지로 **작업 유형(think/default/background/longContext)별 라우팅** 지원. Claude Code 전용 설계.

**장점**: 작업 유형별 라우팅, 설치 간편, `/model` 커맨드로 실시간 전환
**단점**: 서드파티 npm 패키지 (하지만 Claude Code 커뮤니티에서 널리 사용)

### 4.2 라우팅 솔루션 상세 비교

| 기능 | 직접 연결 | LiteLLM | claude-code-router |
|------|----------|---------|-------------------|
| 멀티모델 | ❌ | ✅ 모델명 기반 | ✅ 작업 유형 기반 |
| 라우팅 방식 | 없음 | Opus/Sonnet/Haiku 티어 | think/default/background/longContext/webSearch |
| 포맷 변환 | vLLM 자체 | 자동 (Anthropic↔OpenAI) | transformer 플러그인 (12종 내장) |
| 설치 | 환경변수만 | Docker | `npm install -g` |
| 로드밸런싱 | ❌ | ✅ | ❌ (수동 전환) |
| 폴백 | ❌ | ✅ | ✅ `fallback` config + Custom Router |
| 실시간 모델 전환 | ❌ | ❌ | ✅ (`/model` 커맨드, `ccr model`, `ccr ui`) |
| 커스텀 라우팅 | ❌ | ❌ | ✅ (`CUSTOM_ROUTER_PATH` JS 모듈) |
| 모니터링 | ❌ | Prometheus | 로그 + Statusline (beta) |
| Preset 관리 | ❌ | ❌ | ✅ (`ccr preset export/install`) |
| 오버헤드 | 0ms | ~5ms | ~5ms |
| 적합 시나리오 | 단일 모델 테스트 | 프로덕션, 다수 사용자 | 개인 개발자, 유연한 라우팅 |

**최종 선택**: claude-code-router (개인 사용, 유연한 라우팅, 간편한 설치)

### 4.3 API 제공자 분석

#### Z.AI (GLM-4.7)
- **API 엔드포인트**: `https://api.z.ai/api/anthropic`
- **호환성**: Anthropic Messages API 완전 호환
- **모델**: GLM-4.7 (355B MoE), GLM-4.5-Air
- **컨텍스트**: 200K tokens
- **비용**: $0.60/$2.20 per 1M tokens
- **특징**: Claude Code 공식 연동 지원, transformer 불필요

#### OpenAI (GPT-5.2 Codex)
- **API 엔드포인트**: `https://api.openai.com/v1/chat/completions`
- **모델**: GPT-5.2 Codex
- **컨텍스트**: 400K tokens
- **비용**: $1.75/$14.00 per 1M tokens (사용자는 비용 무관)
- **특징**: OpenAI API 포맷, transformer 필요 (`openai`, `maxcompletiontokens`)

#### Anthropic (Claude Opus 4.5)
- **API 엔드포인트**: `https://api.anthropic.com/v1/messages`
- **모델**: Claude Opus 4.5
- **컨텍스트**: 200K tokens
- **비용**: $5/$25 per 1M tokens
- **특징**: 네이티브 API, transformer 불필요

### 4.4 Gemini 3 Pro 거부 이유

사용자 피드백 및 벤치마크 분석 결과:

❌ **환각률 85-88%**: 신뢰할 수 없는 코드 생성
❌ **컨텍스트 메모리 열화**: 5-6 메시지 후 이전 컨텍스트 망각
❌ **Tool calling 불안정**: OpenRouter 경유 시 빈 응답 발생
❌ **코드 품질**: "Opus로 만든 코드를 망가뜨렸다"는 사용자 리포트
❌ **대안 존재**: GLM-4.7이 더 저렴하고 안정적

**결론**: Gemini 3 Pro는 아키텍처에서 완전 제외.

### 4.5 MCP 도구 공유 아키텍처

#### 핵심 원리

MCP(Model Context Protocol) 도구는 **Claude Code 클라이언트가 관리**한다. 백엔드 모델은 `tool_use` 요청만 생성하고, 실제 실행은 Claude Code가 담당.

```
모델(GLM/GPT/Qwen) → tool_use JSON 생성 → Claude Code 수신 → MCP 서버 실행 → 결과 반환
```

**따라서 어떤 백엔드 모델을 사용하든 동일한 MCP 도구에 접근 가능.**

#### MCP 도구 호환성 매트릭스

| MCP 서버 | Opus (10%) | GLM-4.7 (35%) | GPT-5.2 (5%) | Qwen3 (50%) | DeepSeek (<1%) |
|----------|-----------|---------------|--------------|-------------|----------------|
| filesystem | ✅ | ✅ | ✅ | ✅ | ⚠️ 수동 |
| git | ✅ | ✅ | ✅ | ✅ | ⚠️ 수동 |
| memory | ✅ | ✅ | ✅ | ✅ | ⚠️ 수동 |
| playwright | ✅ | ✅ | ✅ | ✅ | ❌ |
| context7 | ✅ | ✅ | ✅ | ✅ | ❌ |
| tavily | ✅ | ✅ | ✅ | ✅ | ❌ |
| gemini | ✅ | ✅ | ✅ | ✅ | ❌ |

**전제 조건**: 각 모델이 Anthropic `tool_use` 포맷으로 정확히 응답해야 함.
- Opus/GLM-4.7: 네이티브 Anthropic 포맷 → **그대로 동작**
- GPT-5.2: `openai` transformer가 변환 → **변환 후 동작**
- Qwen3-Coder: `tooluse` transformer가 변환 → **변환 후 동작**
- DeepSeek-R1: tool calling 불안정 → **MCP 의존 작업 비권장**

#### MCP 서버 Docker 설정

`~/.claude/claude_desktop_config.json` (Docker 내부):

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/claude-code-mcp-server-filesystem", "--dir", "/workspace"]
    },
    "memory": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/claude-code-mcp-server-memory"]
    },
    "context7": {
      "command": "npx",
      "args": ["-y", "@context7/mcp-server"]
    },
    "tavily": {
      "command": "npx",
      "args": ["-y", "tavily-mcp"],
      "env": { "TAVILY_API_KEY": "${TAVILY_API_KEY}" }
    },
    "playwright": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/claude-code-mcp-server-playwright"]
    }
  }
}
```

#### Qwen3-Coder 16K 컨텍스트와 MCP 도구 제약

Qwen3-Coder는 16K 컨텍스트 제한으로 인해 **MCP 도구 응답이 큰 경우 컨텍스트 오버플로우** 위험:

| MCP 도구 | 평균 응답 크기 | Qwen3-Coder 안전성 |
|----------|--------------|-------------------|
| filesystem (파일 읽기) | 1K~50K tokens | ⚠️ 큰 파일 위험 |
| git (diff/log) | 500~10K tokens | ✅ 보통 안전 |
| memory (검색) | 200~2K tokens | ✅ 안전 |
| playwright (스냅샷) | 2K~20K tokens | ⚠️ 큰 페이지 위험 |
| context7 (문서) | 1K~15K tokens | ⚠️ 위험 |
| tavily (검색) | 500~5K tokens | ✅ 보통 안전 |

**대응 전략**: Qwen3-Coder(background)에는 **단순 작업만 라우팅** — 단일 파일 편집, 짧은 코드 생성 등. 대규모 MCP 조회가 필요한 작업은 GLM-4.7(default) 또는 GPT-5.2(longContext)로 자동 전환.

### 4.6 최종 라우팅 전략

| 라우터 | 모델 | Provider | 사용률 | 사용 시나리오 |
|--------|------|----------|--------|--------------|
| **think** | Claude Opus 4.5 | Anthropic 직접 API | **10%** | 전략 계획, 아키텍처 설계, 코드 리뷰 |
| **default** | GLM-4.7 | Z.AI 직접 API | **35%** | 일상 코딩, 멀티파일 리팩토링, UI 생성 |
| **longContext** | GPT-5.2 Codex | OpenAI 직접 API | **5%** | 대규모 코드베이스 분석, 복잡한 코딩 |
| **background** | Qwen3-Coder-30B | Cognit vLLM (로컬) | **50%** | 빠른 코드 생성, 단일 파일 편집 |
| **(수동)** | DeepSeek-R1-70B | Nexus vLLM (선택사항) | **<1%** | 깊은 추론, 알고리즘 디버깅 (/model 전환) |

### 4.6.1 모델별 트래픽 분배 예상

| 모델 | 예상 트래픽 비율 | 일일 토큰 사용량 (추정) |
|------|----------------|----------------------|
| Qwen3-Coder (background) | **50%** | ~500K tokens |
| GLM-4.7 (default) | **35%** | ~350K tokens |
| Opus (think) | **10%** | ~100K tokens |
| GPT-5.2 Codex (longContext) | **5%** | ~50K tokens |
| DeepSeek-R1 (수동) | **<1%** | ~10K tokens |

**근거**:
- 백그라운드 작업 (빠른 코드 생성)이 가장 많음
- 메인 코딩은 GLM-4.7이 담당 (비용 효율)
- 계획/리뷰는 세션당 1-2회만 발생 (Opus)
- 대규모 분석은 가끔만 필요 (GPT-5.2)

### 4.7 oh-my-claudecode 멀티에이전트 통합 ⭐ 핵심 설계

#### 통합 원리

oh-my-claudecode(v3.10.3)는 Claude Code에 **50개 전문 에이전트 + 37개 스킬 + 7개 실행 모드**를 제공하는 오케스트레이션 플러그인이다. 각 에이전트는 `model: haiku/sonnet/opus` 티어를 가지며, `Task(model="haiku")` 형태로 호출 시 Claude Code가 해당 모델 API 요청을 생성한다.

**claude-code-router는 이 API 요청을 가로채서 모델명/요청 내용 기반으로 라우팅한다.**

```
oh-my-claudecode                claude-code-router 감지 로직      백엔드 모델
─────────────                   ─────────────────────────       ──────────
Task(model="opus")      →  claude-opus-4-5     →  think      →  Opus 4.5 (Anthropic)
  (감지: req.body.thinking 필드 존재)
Task(model="sonnet")    →  claude-sonnet-4-5   →  default    →  GLM-4.7 (Z.AI)
  (감지: 위 조건 모두 불일치 시 기본값)
Task(model="haiku")     →  claude-haiku-4-5    →  background →  Qwen3-Coder (vLLM)
  (감지: req.body.model에 "claude"+"haiku" 포함)
(any, 60K+ context)     →  자동 감지            →  longContext→  GPT-5.2 Codex (OpenAI)
  (감지: tokenCount > longContextThreshold 또는 이전 usage > threshold)
```

#### 라우팅 감지 우선순위 (claude-code-router v2.0.0)

| 우선순위 | 조건 | 라우팅 타입 |
|---------|------|-----------|
| 1 | 명시적 `provider,model` 지정 | 해당 모델 직접 |
| 2 | tokenCount > longContextThreshold (60K) | `longContext` |
| 3 | 서브에이전트 프롬프트에 `provider,model` 포함 | Subagent Routing |
| 4 | req.body.model에 "claude"+"haiku" 포함 | `background` |
| 5 | req.body.tools에 web_search 타입 존재 | `webSearch` |
| 6 | req.body.thinking 필드 존재 | `think` |
| 7 | 위 조건 모두 불일치 | `default` |

> **Subagent Routing**: 서브에이전트 프롬프트의 **시작 부분에 `provider,model`**을 포함하면 특정 모델로 직접 라우팅 가능. oh-my-claudecode의 에이전트별 커스텀 라우팅에 활용 가능.

**결과**: oh-my-claudecode가 `executor-low`(haiku)를 5개 병렬 실행하면 → **Qwen3-Coder가 180 tok/s로 5개 동시 처리**. `architect`(opus)가 검증하면 → **Opus 4.5가 처리**. 자동으로.

#### 전체 에이전트-모델 매핑 (50개)

##### opus → Opus 4.5 (Anthropic API, 10%) — 16개 에이전트

고품질 추론, 아키텍처 설계, 검증이 필요한 핵심 에이전트.

| 에이전트 | 역할 | 호출 빈도 |
|----------|------|----------|
| `architect` | 아키텍처 분석, 디버깅 조언, **완료 검증** | 매 작업 완료 시 |
| `planner` | 전략 계획, 인터뷰 워크플로우 | 세션 시작 시 |
| `critic` | 계획 품질 리뷰 | 계획 후 |
| `analyst` | 요구사항 분석 | 새 기능 시 |
| `orchestrator` | 작업 분해, 에이전트 조율 | 항상 (메인 루프) |
| `deep-executor` | 복잡한 멀티파일 구현 | 복잡한 작업 시 |
| `executor-high` | 고복잡도 구현 | 필요 시 |
| `code-reviewer` | 심층 코드 리뷰 (보안 포함) | 완료 전 |
| `security-reviewer` | OWASP 취약점 탐지 | 보안 관련 코드 |
| `security-specialist` | 보안 전문 검사 | 배포 전 |
| `backend-specialist` | 서버사이드 로직, DB | 백엔드 작업 |
| `designer-high` | 복잡한 UI 아키텍처 | 대규모 UI |
| `explore-high` | 전체 시스템 구조 분석 | 아키텍처 파악 |
| `qa-tester-high` | 프로덕션급 QA | 릴리스 전 |
| `scientist-high` | 복잡한 데이터 분석 | ML/통계 |
| `system-designer` | 시스템 설계 | 새 컴포넌트 |

##### sonnet → GLM-4.7 (Z.AI API, 35%) — 17개 에이전트

일상 코딩, 중간 복잡도 구현, UI 작업. GLM-4.7의 73.8% SWE-bench + "Vibe Coding" UI 생성 능력 활용.

| 에이전트 | 역할 | 호출 빈도 |
|----------|------|----------|
| `executor` | **메인 구현 에이전트** — 멀티파일 작업 | 매우 높음 |
| `researcher` | 외부 문서/API 리서치 | 새 라이브러리 사용 시 |
| `designer` | UI/UX 컴포넌트 디자인 | 프론트엔드 작업 |
| `architect-medium` | 중간 복잡도 아키텍처 분석 | 일반 분석 |
| `explore-medium` | 중간 깊이 코드베이스 탐색 | 코드 조사 |
| `scientist` | 데이터 분석 | 데이터 작업 |
| `qa-tester` | CLI/서비스 테스트 (tmux) | 테스트 |
| `build-fixer` | 빌드/타입 에러 수정 | 빌드 실패 시 |
| `git-master` | Git 작업 (커밋, 리베이스) | 커밋 시 |
| `tdd-guide` | TDD 워크플로우 | 테스트 우선 개발 |
| `vision` | 이미지/PDF 분석 | 시각 자료 |
| `3d-engine-specialist` | Three.js, BIM 작업 | 3D 작업 |
| `frontend-specialist` | 프론트엔드 전문 | 프론트 구현 |
| `api-designer` | API 계약 설계 | API 설계 |
| `requirements-analyst` | 요구사항 분해 | 기획 |
| `task-executor` | 개별 Task 자율 실행 | ultrawork 모드 |
| `task-planner` | Phase/Task 분해 | 태스크 분할 |

##### haiku → Qwen3-Coder (Local vLLM, 50%) — 17개 에이전트 (⚠️ 조정 필요)

빠른 단순 작업. **단, 16K 컨텍스트 제한으로 인해 일부 에이전트는 sonnet으로 승격 필요.**

| 에이전트 | 역할 | Qwen3 적합성 | 비고 |
|----------|------|-------------|------|
| `executor-low` | 단일 파일 편집 | ✅ 안전 | 핵심 작업말 |
| `build-fixer-low` | 간단한 빌드 에러 | ✅ 안전 | |
| `designer-low` | 간단한 스타일링 | ✅ 안전 | |
| `writer` | 문서 작성 | ✅ 안전 | 짧은 문서 |
| `code-reviewer-low` | 빠른 코드 체크 | ✅ 안전 | |
| `security-reviewer-low` | 빠른 보안 스캔 | ✅ 안전 | |
| `tdd-guide-low` | 간단한 테스트 제안 | ✅ 안전 | |
| `scientist-low` | 간단한 데이터 조회 | ✅ 안전 | |
| `researcher-low` | 빠른 문서 조회 | ✅ 안전 | |
| `dependency-resolver` | TASKS.md 파싱 | ✅ 안전 | 한 줄 응답 |
| `impact-analyzer` | 변경 영향 분석 | ✅ 안전 | 한 줄 응답 |
| `architect-low` | 간단한 코드 질문 | ⚠️ 주의 | 컨텍스트 모니터링 |
| `docs-specialist` | 문서 생성 | ⚠️ 주의 | 큰 문서는 GLM으로 |
| `database-specialist` | DB 스키마 설계 | ⚠️ 주의 | 복잡하면 GLM으로 |
| `explore` | 코드베이스 탐색 | ❌ **승격 필요** | 다수 파일 → 16K 초과 |
| `architecture-analyst` | 코드베이스 구조 분석 | ❌ **승격 필요** | 전체 분석 → 16K 초과 |
| `test-specialist` | 테스트 작성 | ❌ **승격 필요** | 복잡한 테스트 → 16K 초과 |

#### 티어 조정 (Qwen3-Coder 16K 대응)

**haiku → sonnet 승격 대상 (3개)**:

| 에이전트 | 현재 | 변경 | 이유 |
|----------|------|------|------|
| `explore` | haiku → Qwen3 | **sonnet → GLM-4.7** | 다수 파일 탐색 결과 누적 → 16K 즉시 초과. GLM-4.7의 200K로 안전 |
| `architecture-analyst` | haiku → Qwen3 | **sonnet → GLM-4.7** | 전체 코드베이스 구조 분석 → 16K 부족. 200K 필요 |
| `test-specialist` | haiku → Qwen3 | **sonnet → GLM-4.7** | Contract-First TDD로 계약 정의 + 테스트 작성 → 컨텍스트 소모 큼 |

**승격 방법**: `~/.claude/agents/` 디렉토리의 해당 `.md` 파일에서 `model: haiku` → `model: sonnet` 수정.

```yaml
# 변경 전 (explore.md)
---
name: explore
model: haiku
---

# 변경 후
---
name: explore
model: sonnet
---
```

> ⚠️ oh-my-claudecode 업데이트 시 에이전트 파일이 덮어씌워질 수 있음. `.claude/agents/` 변경사항을 별도 백업하거나, OMC config에서 오버라이드 방법 확인 필요.

#### 조정 후 최종 티어 분포

| 티어 | 백엔드 모델 | 에이전트 수 | 비율 |
|------|-----------|-----------|------|
| **opus** | Opus 4.5 (Anthropic) | 16개 | 10% 트래픽 |
| **sonnet** | GLM-4.7 (Z.AI) | **20개** (기존 17 + 승격 3) | 35% 트래픽 |
| **haiku** | Qwen3-Coder (로컬) | **14개** (기존 17 - 승격 3) | 50% 트래픽 |
| **longContext** | GPT-5.2 Codex (OpenAI) | 자동 (60K+) | 5% 트래픽 |

#### 실행 모드별 모델 사용 패턴

##### autopilot 모드 (전체 자율 실행)

```
Phase 0 (Expansion):   analyst(Opus) + architect(Opus)       → Opus 100%
Phase 1 (Planning):    architect(Opus) + critic(Opus)         → Opus 100%
Phase 2 (Execution):   executor-low(Qwen3) + executor(GLM)   → Qwen3 60% + GLM 40%
Phase 3 (QA):          build-fixer(GLM) + qa-tester(GLM)      → GLM 100%
Phase 4 (Validation):  architect(Opus) + security-reviewer(Opus) + code-reviewer(Opus) → Opus 100%
```

**비용 효과**: 전체 autopilot 중 Phase 2(구현)이 80% 시간 차지 → Qwen3+GLM이 대부분 처리 → 비용 최소화.

##### ultrawork 모드 (최대 병렬)

```
┌──────────────────────────────────────────────────────┐
│  병렬 실행 예시 (5개 동시)                              │
│                                                      │
│  executor-low(Qwen3) ─┐                              │
│  executor-low(Qwen3) ─┤                              │
│  executor-low(Qwen3) ─┼─→ 각 180 tok/s, 동시 5개     │
│  executor-low(Qwen3) ─┤    ≈ 총 ~750 tok/s 처리량    │
│  executor-low(Qwen3) ─┘                              │
│                                                      │
│  → 완료 후 architect(Opus) 검증                       │
└──────────────────────────────────────────────────────┘
```

##### ecomode (토큰 절약)

ecomode는 **공격적 하향 전략**을 사용하는 modifier:

| 기본 티어 | ecomode 동작 | 우리 모델 변화 |
|----------|-------------|--------------|
| opus | → sonnet (essential한 경우만 opus 유지) | Opus → **GLM-4.7** |
| sonnet | → **haiku 우선 시도**, 실패 시에만 sonnet 복귀 | GLM-4.7 → **Qwen3-Coder** (먼저 시도) |
| haiku | → haiku (변화 없음) | Qwen3 → Qwen3 |

> ⚠️ **주의**: ecomode의 sonnet→haiku 전환은 "항상 한 단계 낮춤"이 아니라 **"haiku를 먼저 시도하고, 실패하면 sonnet으로 업그레이드"** 패턴이다. 이는 승격된 3개 에이전트(explore, architecture-analyst, test-specialist)가 ecomode 활성화 시 **Qwen3-Coder(16K)로 강등될 가능성이 높음**을 의미한다.

**ecomode + 우리 시스템**: GLM-4.7($0.60/$2.20)이 Opus 역할을 대신하므로 **추가 비용 절감**. 그러나 승격된 3개 에이전트가 ecomode에서 haiku로 강등되면 16K 오버플로우 위험이 재발하므로, **반드시 에이전트 `.md` 파일에서 `model: sonnet`으로 고정하고, ecomode 스킬에 예외 에이전트 목록을 추가**해야 한다 (T14 참조).

#### 아키텍처 다이어그램 (통합)

```
┌─────────────────────────────────────────────────────────────────────┐
│  Docker Container (Ubuntu 22.04)                                     │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  oh-my-claudecode (오케스트레이션 레이어)                       │  │
│  │                                                               │  │
│  │  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐  │  │
│  │  │autopilot│ │ultrawork │ │  ralph   │ │  ecomode/swarm   │  │  │
│  │  └────┬────┘ └────┬─────┘ └────┬─────┘ └───────┬──────────┘  │  │
│  │       └───────────┼────────────┼────────────────┘             │  │
│  │                   ▼                                           │  │
│  │  ┌───────────────────────────────────────────────────────┐   │  │
│  │  │  50개 전문 에이전트                                     │   │  │
│  │  │  opus(16) → architect, planner, critic, analyst...     │   │  │
│  │  │  sonnet(20) → executor, researcher, designer...        │   │  │
│  │  │  haiku(14) → executor-low, writer, build-fixer-low...  │   │  │
│  │  └───────────────────────┬───────────────────────────────┘   │  │
│  └──────────────────────────┼────────────────────────────────────┘  │
│                             ▼                                       │
│  ┌───────────────┐  ┌────────────────────────────────────────┐     │
│  │  Claude Code  │  │  MCP Servers (공유)                     │     │
│  │   (CLI)       │──│  filesystem, git, memory, playwright,   │     │
│  │   model=X     │  │  context7, tavily, gemini, youtube      │     │
│  └──────┬────────┘  └────────────────────────────────────────┘     │
│         │                                                           │
│  ┌──────▼─────────────────────────────────────┐                    │
│  │  claude-code-router (:8081)                 │                    │
│  │  모델명 기반 자동 라우팅                      │                    │
│  │  opus→think | sonnet→default | haiku→bg     │                    │
│  └──┬──────┬──────┬──────────────┬────────────┘                    │
└─────┼──────┼──────┼──────────────┼──────────────────────────────────┘
      ▼      ▼      ▼              ▼
 ┌──────┐ ┌──────┐ ┌──────────┐ ┌────────┐
 │Opus  │ │GLM   │ │GPT-5.2   │ │Qwen3   │
 │4.5   │ │4.7   │ │Codex     │ │Coder   │
 │16 agt│ │20 agt│ │auto 60K+ │ │14 agt  │
 └──────┘ └──────┘ └──────────┘ └────────┘
```

---

## 5. 최종 구성

### 5.1 config.json (claude-code-router)

`~/.claude-code-router/config.json`:

```json
{
  "LOG": true,
  "LOG_LEVEL": "info",
  "API_TIMEOUT_MS": 600000,

  "Providers": [
    {
      "name": "anthropic",
      "api_base_url": "https://api.anthropic.com/v1/messages",
      "api_key": "$ANTHROPIC_API_KEY",
      "models": ["claude-opus-4-5-20251101"],
      "transformer": { "use": ["anthropic"] }
    },
    {
      "name": "zai",
      "api_base_url": "https://api.z.ai/api/anthropic",
      "api_key": "$ZAI_API_KEY",
      "models": ["glm-4.7"],
      "transformer": { "use": ["cleancache"] }
    },
    {
      "name": "openai",
      "api_base_url": "https://api.openai.com/v1/chat/completions",
      "api_key": "$OPENAI_API_KEY",
      "models": ["gpt-5.2-codex"],
      "transformer": { "use": ["cleancache"] }
    },
    {
      "name": "cognit",
      "api_base_url": "http://10.5.5.11:8000/v1/chat/completions",
      "api_key": "none",
      "models": ["Qwen3-Coder-30B-A3B"],
      "transformer": {
        "use": [
          "tooluse",
          "enhancetool",
          ["maxtoken", {"max_tokens": 15000}],
          "cleancache"
        ]
      }
    }
  ],

  "Router": {
    "default": "zai,glm-4.7",
    "think": "anthropic,claude-opus-4-5-20251101",
    "background": "cognit,Qwen3-Coder-30B-A3B",
    "longContext": "openai,gpt-5.2-codex",
    "longContextThreshold": 60000
  },

  "fallback": {
    "default": ["anthropic,claude-opus-4-5-20251101"],
    "background": ["zai,glm-4.7"],
    "think": ["zai,glm-4.7"],
    "longContext": ["anthropic,claude-opus-4-5-20251101"]
  }
}
```

### 5.2 설정 설명

#### Providers 섹션

**anthropic**:
- Anthropic Messages API 네이티브 포맷
- `transformer: { "use": ["anthropic"] }` → Bearer 인증 처리 (네이티브 API이므로 포맷 변환 없음)
- Opus 전용

**zai**:
- Anthropic Messages API 호환 (Z.AI가 프록시 제공)
- `transformer: { "use": ["cleancache"] }` → `cache_control` 필드 제거 (Z.AI 미지원 필드 방지)
- GLM-4.7 서빙

**openai**:
- OpenAI Chat Completions API 포맷
- `transformer: { "use": ["cleancache"] }` → `cache_control` 제거 + OpenAI 포맷 자동 변환
- GPT-5.2 Codex 서빙

**cognit**:
- vLLM OpenAI-compatible API 포맷
- `transformer: { "use": ["tooluse", "enhancetool", ["maxtoken", {"max_tokens": 15000}], "cleancache"] }`
  - `tooluse`: Anthropic tool format 변환 + ExitTool 자동 처리
  - `enhancetool`: tool call 파라미터 오류 허용 (안정성 향상)
  - `maxtoken`: 16K 컨텍스트에 맞춰 응답 토큰 제한
  - `cleancache`: `cache_control` 필드 제거
- Qwen3-Coder 로컬 서빙

#### 내장 Transformer 참조 (claude-code-router v2.0.0)

| Transformer | 용도 | 주요 Provider |
|-------------|------|-------------|
| `anthropic` | Anthropic API 직접 연결 (Bearer 인증) | anthropic |
| `cleancache` | 요청에서 `cache_control` 필드 제거 | 비-Anthropic 전체 |
| `tooluse` | tool calling 강제 + ExitTool 자동 처리 | vLLM, Ollama |
| `enhancetool` | tool call 파라미터 오류 허용 레이어 | vLLM, Ollama |
| `maxtoken` | 최대 응답 토큰 제한 (옵션: `max_tokens`) | VRAM 제한 모델 |
| `reasoning` | `reasoning_content` 필드 처리 | DeepSeek-R1 |
| `deepseek` | DeepSeek API 어댑터 | DeepSeek |
| `gemini` | Gemini API 어댑터 | Google |
| `openrouter` | OpenRouter API 어댑터 | OpenRouter |
| `sampling` | `temperature`, `top_p` 등 샘플링 파라미터 | 전체 |

> **Transformer 적용 순서**: `cleancache` → `tooluse` → `enhancetool` → `maxtoken` (순서 중요)
>
> **옵션 전달 방법**: `["transformer-name", {"option": "value"}]` (배열 형태)

#### Router 섹션

**default** (메인 코딩):
- GLM-4.7 (Z.AI API)
- 이유: SWE-bench 73.8%, 비용 효율, 200K 컨텍스트

**think** (계획/리뷰):
- Claude Opus 4.5 (Anthropic API)
- 이유: SWE-bench 80.9%, 0% tool error, 최고 품질

**background** (빠른 작업):
- Qwen3-Coder-30B (Cognit 로컬 vLLM)
- 이유: 180 tok/s 속도, 무료, 단일 파일 작업 충분

**longContext** (대규모 분석):
- GPT-5.2 Codex (OpenAI API)
- 이유: 400K 컨텍스트, SWE-bench 80.0%, 사용자 비용 무관
- `longContextThreshold: 60000` → 60K tokens 이상 시 자동 전환

#### fallback 섹션 (자동 폴백)

claude-code-router v2.0.0은 시나리오별 폴백 체인을 지원한다. 1차 모델 요청 실패 시 `fallback` 리스트의 다음 모델로 자동 전환.

| 시나리오 | 1차 모델 | 폴백 모델 | 상황 |
|---------|---------|----------|------|
| `default` | GLM-4.7 (Z.AI) | Opus 4.5 (Anthropic) | Z.AI API 장애 시 |
| `background` | Qwen3-Coder (로컬) | GLM-4.7 (Z.AI) | VPN 단절/vLLM 다운 시 |
| `think` | Opus 4.5 (Anthropic) | GLM-4.7 (Z.AI) | Anthropic API 장애 시 |
| `longContext` | GPT-5.2 (OpenAI) | Opus 4.5 (Anthropic) | OpenAI API 장애 시 |

### 5.3 환경 변수 설정

`~/.zshrc` 또는 `~/.bashrc`에 추가:

```bash
# Claude Code Router API Keys
export ANTHROPIC_API_KEY="sk-ant-api03-xxxxx"
export ZAI_API_KEY="your_zai_api_key"
export OPENAI_API_KEY="sk-proj-xxxxx"

# Claude Code Router 자동 설정 (ANTHROPIC_BASE_URL, ANTHROPIC_AUTH_TOKEN 등 자동 주입)
eval "$(ccr activate)"
```

> **참고**: `ccr activate`는 `ANTHROPIC_BASE_URL`, `ANTHROPIC_AUTH_TOKEN`, `NO_PROXY`, `DISABLE_TELEMETRY`, `DISABLE_COST_WARNINGS`, `API_TIMEOUT_MS`를 자동 설정한다. 수동 설정 불필요.
>
> claude-code-router 기본 포트는 **3456**이다. 변경이 필요하면 config.json에 `"PORT": 원하는_포트`를 추가.

### 5.4 API 키 통합관리 전략

#### 전체 키 매트릭스

| # | 키 이름 | 용도 | 발급처 | 비용 | 필수 |
|---|---------|------|--------|------|------|
| 1 | `ANTHROPIC_API_KEY` | Opus 4.5 (think 라우팅) | [console.anthropic.com](https://console.anthropic.com) | $5/$25 per 1M | ✅ |
| 2 | `ZAI_API_KEY` | GLM-4.7 (default 라우팅) | [open.z.ai](https://open.z.ai) | $0.60/$2.20 per 1M | ✅ |
| 3 | `OPENAI_API_KEY` | GPT-5.2 Codex (longContext) | [platform.openai.com](https://platform.openai.com) | $1.75/$14 per 1M | ✅ |
| 4 | `TAVILY_API_KEY` | 웹 검색/추출/크롤링 (MCP) | [app.tavily.com](https://app.tavily.com) | 무료 1,000크레딧/월 | ✅ |
| 5 | — | Context7 문서 조회 (MCP) | — | **무료, 키 불필요** | ✅ |
| 6 | — | claude-mem 메모리 (플러그인) | — | **로컬, 키 불필요** | 선택 |
| 7 | — | Qwen3-Coder (로컬 vLLM) | — | **로컬, 키 불필요** | ✅ |

> **키가 필요한 서비스: 4개** (Anthropic, Z.AI, OpenAI, Tavily). 나머지는 무료/로컬.

#### 통합 관리 — 단일 `.env` 파일

모든 API 키를 **하나의 `.env` 파일**에서 중앙 관리:

```bash
# ~/.claude-env/.env (중앙 API 키 저장소)
# ================================================
# LLM Provider Keys (claude-code-router용)
# ================================================
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
ZAI_API_KEY=your_zai_api_key_here
OPENAI_API_KEY=sk-proj-xxxxx

# ================================================
# MCP Server Keys
# ================================================
TAVILY_API_KEY=tvly-xxxxx

# ================================================
# 선택사항
# ================================================
# GITHUB_TOKEN=ghp_xxxxx              # GitHub MCP (선택)
# GEMINI_API_KEY=AIza-xxxxx            # Gemini MCP (선택)
```

#### 키 주입 흐름

```
~/.claude-env/.env (중앙 저장소)
    │
    ├──→ ~/.zshrc (source로 로드)
    │    └──→ shell 환경변수로 노출
    │         ├──→ claude-code-router config.json ($ANTHROPIC_API_KEY 참조)
    │         ├──→ ccr activate (ANTHROPIC_BASE_URL, AUTH_TOKEN 자동 설정)
    │         └──→ MCP 서버 env (TAVILY_API_KEY)
    │
    └──→ docker-compose.yml (env_file로 주입)
         └──→ 컨테이너 내 환경변수
```

**`~/.zshrc`에 추가**:
```bash
# API 키 중앙 로드
source ~/.claude-env/.env
export ANTHROPIC_API_KEY ZAI_API_KEY OPENAI_API_KEY TAVILY_API_KEY

# Claude Code Router 자동 설정
eval "$(ccr activate)"
```

**`docker-compose.yml`에서 참조**:
```yaml
services:
  claude-agent:
    env_file:
      - ~/.claude-env/.env    # 중앙 .env 파일 참조
```

#### 키 상태 확인 스크립트

```bash
#!/bin/bash
# check-api-keys.sh — API 키 상태 일괄 확인

echo "=== API Key Status Check ==="

# 1. Anthropic
if curl -s -o /dev/null -w "%{http_code}" \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  https://api.anthropic.com/v1/messages \
  -d '{"model":"claude-haiku-4-5-20251001","max_tokens":1,"messages":[{"role":"user","content":"hi"}]}' \
  | grep -q "200"; then
  echo "✅ ANTHROPIC_API_KEY: 유효"
else
  echo "❌ ANTHROPIC_API_KEY: 무효 또는 미설정"
fi

# 2. Z.AI
if [ -n "$ZAI_API_KEY" ]; then
  echo "✅ ZAI_API_KEY: 설정됨 (${ZAI_API_KEY:0:8}...)"
else
  echo "❌ ZAI_API_KEY: 미설정"
fi

# 3. OpenAI
if [ -n "$OPENAI_API_KEY" ]; then
  echo "✅ OPENAI_API_KEY: 설정됨 (${OPENAI_API_KEY:0:8}...)"
else
  echo "❌ OPENAI_API_KEY: 미설정"
fi

# 4. Tavily
if [ -n "$TAVILY_API_KEY" ]; then
  echo "✅ TAVILY_API_KEY: 설정됨 (${TAVILY_API_KEY:0:8}...)"
else
  echo "❌ TAVILY_API_KEY: 미설정"
fi

# 5. Cognit vLLM
if curl -s -o /dev/null -w "%{http_code}" http://10.5.5.11:8000/health | grep -q "200"; then
  echo "✅ Cognit vLLM: 정상"
else
  echo "❌ Cognit vLLM: 접근 불가"
fi

# 6. Context7 (키 불필요)
echo "✅ Context7: 무료, 키 불필요"
```

#### 보안 규칙

| 규칙 | 설명 |
|------|------|
| **단일 저장소** | 모든 키는 `~/.claude-env/.env`에만 저장 |
| **Git 차단** | `.gitignore`에 `.env`, `*.env`, `config.json` 등록 |
| **하드코딩 금지** | Docker 이미지, 소스코드에 키 삽입 금지 |
| **환경변수 참조** | config.json에서 `$ANTHROPIC_API_KEY` 형식만 사용 |
| **키 로테이션** | 분기 1회 또는 유출 의심 시 즉시 교체 |
| **최소 권한** | `.env` 파일 퍼미션 `600` (소유자만 읽기/쓰기) |
| **백업** | 키 발급 후 1Password/Bitwarden 등 비밀번호 매니저에 별도 보관 |

```bash
# .env 파일 보안 설정
chmod 600 ~/.claude-env/.env

# .gitignore 필수 항목
.env
*.env
.claude-env/
.claude-code-router/config.json
```

### 5.5 실행 방법

```bash
# 1. claude-code-router 설치
npm install -g @musistudio/claude-code-router

# 2. 환경변수 자동 설정 (~/.zshrc에 추가)
eval "$(ccr activate)"

# 3. 라우터 시작 + Claude Code 실행 (권장)
ccr code

# 4. 또는 라우터만 백그라운드 실행
ccr start  # http://localhost:3456 리슨 (기본 포트)
claude     # 별도 터미널에서 Claude Code 실행

# 5. 웹 UI로 설정 관리
ccr ui

# 6. Phase별 Preset 관리
ccr preset export phase1-opus-qwen
ccr preset export phase3-full-multimodel
ccr preset install phase1-opus-qwen  # Preset 전환
```

### 5.6 (선택사항) DeepSeek-R1-70B 추가

Phase 4에서 Nexus에 DeepSeek-R1-70B를 배포할 경우:

**config.json에 추가**:

```json
{
  "Providers": [
    ...existing providers...,
    {
      "name": "nexus",
      "api_base_url": "http://10.5.5.14:8000/v1/chat/completions",
      "api_key": "none",
      "models": ["deepseek-r1-70b"],
      "transformer": { "use": ["reasoning"] }
    }
  ],

  "Router": {
    ...existing routes...
    # DeepSeek-R1은 수동 전환만 (/model nexus,deepseek-r1-70b)
  }
}
```

**Nexus vLLM 실행**:

```bash
python -m vllm.entrypoints.openai.api_server \
  --model /home/hwandam/models/DeepSeek-R1-Distill-Llama-70B-AWQ \
  --served-model-name deepseek-r1-70b \
  --tensor-parallel-size 2 \
  --max-model-len 16384 \
  --gpu-memory-utilization 0.93 \
  --enable-auto-tool-choice \
  --tool-call-parser deepseek_v3 \
  --chat-template examples/tool_chat_template_deepseekr1.jinja \
  --host 0.0.0.0 --port 8000
```

---

## 6. 구현 계획

### Phase 1: Qwen3-Coder 2대 + Opus (즉시 가능)

**목표**: 기존 인프라 변경 없이 멀티모델 라우팅 테스트

**상태**: 이미 구성 가능 (Cognit + Nexus 모두 Qwen3-Coder 실행 중)

**작업**:
1. claude-code-router 설치: `npm install -g @musistudio/claude-code-router`
2. Phase 1 config.json 작성 (Opus + Qwen3-Coder 2대)
3. `ccr code` 실행하여 라우팅 동작 확인
4. 계획 모드 진입 시 Opus, 코드 작성 시 Qwen 호출 확인

**검증 방법**:
- `ccr ui` → 웹 기반 설정 확인
- Claude Code 내에서 `/model` → 현재 모델 확인 및 전환
- 로그 확인: `~/.claude-code-router/logs/`

### Phase 2: GLM-4.7 단독 사용 (서버 변경 없음)

**목표**: Z.AI GLM Coding Plan으로 Claude Code 전체를 GLM-4.7로 전환하여 성능 테스트

**공식 문서**: https://docs.z.ai/devpack/tool/claude

**작업**:
1. Z.AI API 키 발급 (https://open.z.ai)
2. `~/.claude/settings.json` 수정:
   ```json
   {
     "env": {
       "ANTHROPIC_AUTH_TOKEN": "your_zai_api_key",
       "ANTHROPIC_BASE_URL": "https://api.z.ai/api/anthropic",
       "API_TIMEOUT_MS": "3000000"
     }
   }
   ```
3. `claude` 실행하여 GLM-4.7 동작 확인
4. SWE-bench 스타일 작업으로 코딩 품질 평가

**검증 지표**:
- 멀티파일 리팩토링 정확도
- Tool calling 안정성
- UI 생성 품질
- 응답 속도

**한계**: Opus를 Anthropic API로 혼합 사용 불가 (모든 것이 GLM으로 감). Opus 혼합은 Phase 3에서.

### Phase 3: Opus + GLM-4.7 + GPT-5.2 Codex + Qwen3-Coder (최종 멀티모델)

**목표**: 작업 유형별로 4개 모델을 최적 라우팅

**작업**:
1. OpenAI API 키 발급 (GPT-5.2 Codex 접근)
2. Phase 2에서 GLM-4.7 단독 테스트 완료
3. claude-code-router에 최종 config.json 적용 (섹션 5.1 참조)
4. 환경 변수 설정 (섹션 5.3 참조)
5. `ccr code` 실행

**검증 시나리오**:
- **계획 모드** → Opus 호출 확인 (로그에서 anthropic provider)
- **일반 코딩** → GLM-4.7 호출 확인 (zai provider)
- **대규모 파일 분석** (60K+ tokens) → GPT-5.2 Codex 자동 전환 확인
- **백그라운드 작업** → Qwen3-Coder 로컬 호출 확인 (cognit provider)

**라우팅 전환 로그 예시**:
```
[Router] Routing 'think' request to anthropic,claude-opus-4-5-20251101
[Router] Routing 'default' request to zai,glm-4.7
[Router] Routing 'longContext' request to openai,gpt-5.2-codex (threshold: 65432 tokens)
[Router] Routing 'background' request to cognit,Qwen3-Coder-30B-A3B
```

### Phase 4: (선택사항) DeepSeek-R1-70B 추가

**목표**: Nexus에서 DeepSeek-R1-70B를 서빙하여 추론/디버깅 전용으로 활용

**전제 조건**: GLM-4.7이 API로 이동했으므로 Nexus GPU를 DeepSeek-R1 전용으로 전환 가능

**작업**:
1. Nexus vLLM 프로세스 중지: `ssh hwandam@10.5.5.14 "pkill -f vllm && sleep 5"`
2. DeepSeek-R1-70B 모델 다운로드 (HuggingFace AWQ 버전)
3. Nexus에서 DeepSeek-R1 서빙 시작 (섹션 5.5 참조)
4. config.json에 nexus provider 추가
5. `/model nexus,deepseek-r1-70b` 명령어로 수동 전환하여 사용

**사용 시나리오**:
- 복잡한 알고리즘 디버깅
- 수학 추론 (MATH-500 94.5%)
- Chain-of-thought가 필요한 문제
- Tool calling 없이 순수 추론만 필요한 작업

**주의**: DeepSeek-R1의 tool calling은 불안정하므로, Claude Code의 에이전틱 기능보다는 **수동 전환 + 순수 추론**용으로만 활용 권장.

---

## 7. 비용 분석

### 7.1 현재 (Opus/Sonnet 100% Anthropic API)

| 모델 | 비용 (1M tokens) | 일일 추정 사용량 | 일일 비용 |
|------|-----------------|----------------|---------|
| Opus | $5 input / $25 output | ~200K tokens | ~$3.0 |
| Sonnet | $3 input / $15 output | ~2M tokens | ~$18.0 |
| **합계** | | | **~$21.0/일** |

**월간**: ~$630

### 7.2 하이브리드 구성 후 (Phase 3)

| 모델 | 비용 (1M tokens) | 일일 추정 사용량 | 일일 비용 |
|------|-----------------|----------------|---------|
| Opus (think, 10%) | $5/$25 | ~100K tokens | ~$1.5 |
| GLM-4.7 (default, 35%) | $0.60/$2.20 | ~350K tokens | ~$0.56 |
| GPT-5.2 Codex (longContext, 5%) | $1.75/$14.00 | ~50K tokens | ~$0.39 |
| Qwen3-Coder (background, 50%) | 전기세만 | ~500K tokens | ~$0.15 |
| **합계** | | | **~$2.60/일** |

**월간**: ~$78

### 7.3 비용 절감 효과

| 항목 | 값 |
|------|-----|
| 현재 월간 비용 | ~$630 |
| 하이브리드 월간 비용 | ~$78 |
| **절감액** | **~$552/월** |
| **절감율** | **~88%** |

### 7.4 세부 비용 분석

**Opus**: 계획/리뷰만 10% → Input $0.50 + Output $2.50 = ~$1.5/일

**GLM-4.7**: 메인 코딩 35% → Input $0.21 + Output $0.77 = ~$0.56/일 (매우 저렴)

**GPT-5.2 Codex**: 대규모 분석 5% → Input $0.09 + Output $0.70 = ~$0.39/일 (사용자 비용 무관)

**Qwen3-Coder**: 백그라운드 50%, 로컬 무료 → 전기세만 (~$0.15/일, GPU 평균 350W 기준)

**핵심**: GLM-4.7이 메인 코딩의 35%를 담당하면서 비용을 $0.56/일로 억제 (Sonnet 대비 1/32).

---

## 8. 제약 사항 및 주의사항

### 8.1 Qwen3-Coder 16K 토큰 버짓 분석 ⭐ 최핵심 제약

> **이 섹션이 전체 시스템의 성패를 결정한다.** Qwen3-Coder는 전체 트래픽의 50%를 담당하지만 16,384 토큰만 사용할 수 있다. Task 분리를 제대로 하지 않으면 **절반의 작업이 실패**한다.

#### 모델별 컨텍스트 비교

| 모델 | max-model-len | 실사용 가능 | 여유도 |
|------|--------------|-----------|--------|
| **Qwen3-Coder-30B (로컬)** | **16,384** | **~8,000~11,000** | ⛔ 매우 부족 |
| GLM-4.7 (API) | 200,000 | ~180,000 | ✅ 충분 |
| GPT-5.2 Codex (API) | 400,000 | ~380,000 | ✅ 매우 충분 |
| Opus (Cloud) | 200,000 | ~180,000 | ✅ 충분 |

#### 16,384 토큰은 이렇게 소진된다

서브에이전트(Task)가 생성되면 16K 토큰이 다음과 같이 분배된다:

```
┌─────────────────────────────────────────────────────────┐
│           Qwen3-Coder 16,384 토큰 버짓                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  [고정 오버헤드] ─────────────────────── ~5,000~7,000    │
│  ├── Claude Code 시스템 프롬프트:       ~1,500~2,500    │
│  ├── 도구 정의 (Read, Edit, Bash 등):   ~2,000~3,000    │
│  ├── 에이전트 시스템 프롬프트 (.md):     ~500~1,000     │
│  └── 특수 토큰, 포맷 오버헤드:          ~200~500       │
│                                                         │
│  [Task 프롬프트] ──────────────────────── ~500~2,000    │
│  └── 사용자가 전달한 작업 지시문                         │
│                                                         │
│  [작업 가용 공간] ───────────── ⭐ ~8,000~11,000 남음   │
│  ├── 도구 호출 요청: ~200~500/회                        │
│  ├── 도구 응답: ~500~5,000/회 (파일 크기에 따라)        │
│  ├── 모델 텍스트 응답: ~200~1,000/회                    │
│  └── maxtoken(15000)이 응답 제한하지만                   │
│      input이 크면 output 공간 자체가 줄어듦              │
│                                                         │
│  [응답 예약] ──────────────────────────── ~1,000~2,000  │
│  └── 모델이 최종 답변을 생성할 여유                      │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

#### 도구 호출 횟수별 토큰 소진 시뮬레이션

| 시나리오 | 도구 호출 | 누적 토큰 | 남은 토큰 | 상태 |
|---------|----------|----------|----------|------|
| 시작 (고정 오버헤드 + 프롬프트) | 0 | ~6,000 | ~10,384 | ✅ 여유 |
| 파일 1개 Read (200줄) | 1 | ~7,500 | ~8,884 | ✅ 안전 |
| 파일 Edit (함수 수정) | 2 | ~8,500 | ~7,884 | ✅ 안전 |
| 파일 1개 더 Read (300줄) | 3 | ~10,500 | ~5,884 | ⚠️ 주의 |
| 또 다른 파일 Edit | 4 | ~11,500 | ~4,884 | ⚠️ 빡빡 |
| Grep 검색 결과 | 5 | ~12,500 | ~3,884 | 🔴 위험 |
| **컨텍스트 초과** | 6+ | ~14,000+ | ~2,384 | ⛔ 실패 |

> **결론**: Qwen3-Coder는 **도구 호출 3~4회가 안전 한계**이다. 즉, "파일 1개 읽고 → 수정하고 → 확인" 정도가 1 Task의 적정 크기.

#### 파일 크기별 토큰 소비

| 파일 유형 | 줄 수 | 토큰 (추정) | Qwen3 안전성 |
|----------|-------|-----------|-------------|
| 짧은 함수 | ~30줄 | ~200 | ✅ 안전 |
| 단일 컴포넌트 | ~100줄 | ~500~700 | ✅ 안전 |
| 중간 모듈 | ~200줄 | ~1,000~1,500 | ✅ 안전 (1개만) |
| 큰 파일 | ~500줄 | ~2,500~3,500 | ⚠️ 읽기만 가능, 수정 여유 적음 |
| 대형 파일 | ~1000줄 | ~5,000~7,000 | ❌ 읽기만으로 가용 공간 소진 |
| 매우 큰 파일 | ~2000줄+ | ~10,000+ | ⛔ 읽기조차 불가 |

> **핵심 규칙**: Qwen3-Coder에는 **500줄 이하 파일만** 전달. 500줄 초과 파일은 GLM-4.7(sonnet)로 에스컬레이션.

### 8.2 Tool Calling 호환성

| 모델 | 사용률 | Tool Calling | Parser | 안정성 |
|------|--------|-------------|--------|--------|
| Qwen3-Coder-30B | **50%** | ✅ 지원 | `qwen3_coder` | 안정 |
| GLM-4.7 (API) | **35%** | ✅ 지원 | 네이티브 (API 서버 측 처리) | **안정** (τ²-Bench 87.4%) |
| GPT-5.2 Codex (API) | **5%** | ✅ 지원 | 네이티브 | **안정** (직접 API 사용 시) |
| Opus (Cloud) | **10%** | ✅ 완벽 | 네이티브 | **완벽** (0% error) |
| DeepSeek-R1-70B | **<1%** | ⚠️ 실험적 | `deepseek_v3` | **불안정** |

**주의**: DeepSeek-R1은 tool calling이 불안정하므로 순수 추론 작업에만 수동 전환하여 사용.

### 8.3 네트워크 경로

```
Mac → VPN (10.5.5.x) → Cognit (Qwen3-Coder, 로컬)
     ↘ Internet → Anthropic API (Opus)
     ↘ Internet → Z.AI API (GLM-4.7)
     ↘ Internet → OpenAI API (GPT-5.2 Codex)
```

- **vLLM 요청**: VPN 경유 (지연 추가 ~5-10ms)
- **Cloud API 요청**: 인터넷 직접 연결
- **VPN 단절 시**: 로컬 모델 접근 불가 → Cloud API (GLM-4.7, Opus, GPT-5.2)로 자동 폴백
- **Z.AI API 장애 시**: Qwen3-Coder 로컬 또는 Opus로 수동 전환

### 8.4 GLM-4.7 제약 사항

**Concurrency limit=1**:
- GLM-4.7 API는 동시 요청 제한 있음
- Claude Code **기본** 동작은 순차 실행이므로 일반 사용에서는 문제 없음
- ⚠️ **ultrawork/swarm/ultrapilot 모드에서는 서브에이전트가 병렬 실행**된다. sonnet 티어(GLM-4.7) 에이전트 여러 개가 동시 호출되면 concurrency 제한에 걸림
- **대응**: 병렬 실행 시에는 **haiku(Qwen3-Coder) 에이전트만** 사용. sonnet(GLM-4.7) 에이전트는 순차 실행으로 제한. 예: `executor-low`(haiku) 5개 병렬 → OK, `executor`(sonnet) 2개 병렬 → ❌ concurrency 에러

**100K+ 컨텍스트에서 tool call 버그**:
- 일부 사용자 리포트에서 100K tokens 이상 시 tool calling 응답 누락
- `longContextThreshold: 60000` 설정으로 60K 이상 시 GPT-5.2 Codex로 자동 전환하여 우회

### 8.5 리스크 매트릭스

| # | 리스크 | 확률 | 영향도 | 종합 | 대응 전략 |
|---|--------|------|--------|------|----------|
| R1 | **GLM-4.7 API 장애** (Z.AI 서버 다운) | 중 | **높음** (35% 트래픽 중단) | 🔴 | `fallback` config로 **Opus 자동 전환**. 수동 전환 불필요. 비용 증가 감수 |
| R2 | **Z.AI 서비스 종료/정책 변경** | 낮음 | **매우 높음** (메인 모델 소실) | 🔴 | 대체: Opus(비용↑) 또는 GPT-5.2(default로 승격). LiteLLM 폴백 구성 준비 |
| R3 | **Qwen3-Coder 16K 컨텍스트 오버플로우** | **높음** | 중 (background 실패) | 🟡 | Task를 더 세분화하여 기획. 단일 파일 편집/짧은 코드 생성만 할당. 대형 작업은 GLM-4.7로 라우팅 |
| R4 | **VPN 단절** | 중 | 중 (로컬 모델만 불가) | 🟡 | Cloud API 3개(Opus/GLM/GPT) 정상 동작. Qwen3-Coder만 사용 불가. 자동 폴백 |
| R5 | **Cognit vLLM 다운** | 낮음 | 중 (background 50% 중단) | 🟢 | `fallback` config로 **GLM-4.7 자동 대행**. 비용 소폭 증가 (~$0.56/일 추가) |
| R6 | **claude-code-router 유지보수 중단** | 낮음 | 높음 (라우팅 불가) | 🟡 | LiteLLM Proxy로 대체 가능 (Section 4.1 방식 B). 마이그레이션 1일 소요 |
| R7 | **GPU 하드웨어 장애** (Cognit/Nexus) | 낮음 | 높음 | 🟡 | Cloud API로 전환. Nexus/Cognit 중 1대 장애 시 나머지 1대로 운영 |
| R8 | **OpenAI API 비용 폭증** | 낮음 | 낮음 (5% 트래픽) | 🟢 | longContext를 Opus로 대체 (200K 컨텍스트로도 대부분 커버) |

#### R3 대응: Qwen3-Coder 16K Task 분리 전략 ⭐⭐⭐

> **이 전략이 전체 시스템의 50% 성공률을 결정한다.** Section 8.1의 토큰 버짓 분석을 기반으로 한 실전 가이드.

##### 핵심 원칙: 1T1F — One Task, One File

```
모든 Qwen3-Coder Task는 반드시:
  ✅ 1 Task = 1 File (최대)
  ✅ 1 Task = 1 Function (권장)
  ✅ 도구 호출 3~4회 이내
  ✅ 대상 파일 500줄 이하
  ✅ 프롬프트 200단어 이하
  ✅ max_turns 5 이하
```

##### 분리 패턴 5종

**패턴 1: 수직 분리 (파일 단위)**

하나의 큰 작업을 파일별로 독립 Task로 분해.

```
❌ 잘못된 예:
Task(haiku): "src/auth.ts, src/middleware.ts, src/routes.ts에 JWT 인증 추가"

✅ 올바른 예:
Task(haiku): "src/auth.ts에 verifyToken() 함수 추가"
Task(haiku): "src/middleware.ts에 authMiddleware() 함수 추가"
Task(haiku): "src/routes.ts에 /login POST 엔드포인트 추가"
```

**패턴 2: 수평 분리 (함수 단위)**

하나의 파일 내에서도 함수별로 분해.

```
❌ 잘못된 예:
Task(haiku): "src/utils.ts를 리팩토링해줘 (800줄)"

✅ 올바른 예:
Task(haiku): "src/utils.ts의 parseDate() 함수 (30~65줄)를 dayjs로 교체"
Task(haiku): "src/utils.ts의 formatCurrency() 함수 (70~95줄)에 locale 파라미터 추가"
Task(haiku): "src/utils.ts의 validateEmail() 함수 (100~120줄) 정규식 수정"
```

**패턴 3: 컨텍스트 주입 분리 (읽기/쓰기 분리)**

파일이 클 때, 읽기와 쓰기를 다른 모델에게 분담.

```
✅ 2단계 전략:
1단계 — GLM-4.7(sonnet):  "src/bigFile.ts (1200줄)를 분석하고 수정 계획을 JSON으로 반환"
    → 결과: { "line_45": "old → new", "line_230": "old → new" }

2단계 — Qwen3(haiku) ×N:  "src/bigFile.ts의 45줄 부근 oldCode를 newCode로 수정"
                           "src/bigFile.ts의 230줄 부근 oldCode를 newCode로 수정"
```

> **핵심**: Qwen3에게는 "어디를 어떻게 수정할지"를 **구체적으로** 알려줘야 한다. 파일 전체를 읽고 판단하는 것은 GLM-4.7의 몫.

**패턴 4: 독립 생성 (새 파일/함수)**

기존 코드를 읽을 필요 없이 새로 생성하는 작업. Qwen3에 최적.

```
✅ 최고 효율 Task:
Task(haiku): "다음 인터페이스에 맞는 validateUser() 함수를 src/validators.ts에 작성:
  input: { email: string, password: string }
  output: { valid: boolean, errors: string[] }
  규칙: email은 @포함, password는 8자 이상 + 숫자 포함"
```

> 기존 파일을 Read할 필요 없으므로 도구 호출 1회(Write)로 완료 가능. **16K 내에서 가장 효율적.**

**패턴 5: 린트/포맷 일괄 (단순 반복)**

린트 에러, 타입 에러 등 기계적 수정은 Qwen3가 가장 잘한다.

```
✅ 에러별 1 Task:
Task(haiku): "src/api.ts:45 — 'response' is defined but never used. 사용하지 않는 변수 제거"
Task(haiku): "src/types.ts:12 — Missing return type. getUserById() 반환 타입 Promise<User> 추가"
Task(haiku): "src/config.ts:3 — 'fs' import unused. 사용하지 않는 import 제거"
```

##### 분리 판단 플로우차트

```
작업 수신
  │
  ├─ 대상 파일이 있는가?
  │   ├─ NO (새 파일 생성) → ✅ Qwen3 (패턴 4)
  │   └─ YES
  │       ├─ 파일 크기 확인
  │       │   ├─ ≤200줄 → ✅ Qwen3 (Read+Edit 안전)
  │       │   ├─ 201~500줄 → ⚠️ Qwen3 (Read+Edit 가능, 여유 적음)
  │       │   └─ >500줄 → ❌ GLM-4.7로 에스컬레이션
  │       │               또는 패턴 3 (읽기/쓰기 분리)
  │       │
  │       ├─ 수정 범위 확인
  │       │   ├─ 함수 1개 → ✅ Qwen3
  │       │   ├─ 함수 2~3개 (같은 파일) → ⚠️ Qwen3 (도구 호출 4~6회)
  │       │   ├─ 파일 2개 이상 → ❌ 파일별 분리 (패턴 1)
  │       │   └─ 전체 리팩토링 → ❌ GLM-4.7에 위임
  │       │
  │       └─ MCP 도구 필요?
  │           ├─ 단순 Read/Edit → ✅ Qwen3
  │           ├─ Grep (결과 작음) → ✅ Qwen3
  │           ├─ context7/playwright → ❌ GLM-4.7 (응답 크기 예측 불가)
  │           └─ git diff (큰 diff) → ❌ GLM-4.7
```

##### 구체적 Before/After 예시 5개

**예시 1: "모든 린트 에러 수정"**

```
❌ BEFORE (단일 Task):
Task(haiku): "프로젝트의 모든 ESLint 에러를 수정해줘"
→ Grep으로 에러 수집 → 여러 파일 Read → 여러 파일 Edit → ⛔ 16K 초과

✅ AFTER (분리):
1단계 — GLM-4.7(sonnet):  "ESLint 에러 목록을 파일별로 정리해줘"
    → 결과: { "src/api.ts": ["L45 unused var", "L89 missing type"],
              "src/utils.ts": ["L12 no-any", "L34 prefer-const"] }

2단계 — Qwen3(haiku) × 파일 수:
    Task(haiku): "src/api.ts L45의 unused var 제거, L89에 반환 타입 추가"
    Task(haiku): "src/utils.ts L12의 any를 구체적 타입으로 교체, L34의 let을 const로"
```

**예시 2: "React 컴포넌트에 폼 검증 추가"**

```
❌ BEFORE:
Task(haiku): "UserForm.tsx에 이메일, 비밀번호, 이름 검증 로직을 추가하고
             에러 메시지 표시 컴포넌트도 만들어줘"
→ 큰 컴포넌트 Read + 검증 로직 + UI 변경 = 도구 호출 6~8회 → ⛔ 초과

✅ AFTER:
Task(haiku): "src/validators/userForm.ts 새로 생성 — validateEmail, validatePassword,
             validateName 함수 3개. 각각 string→{valid, error} 반환"          [패턴 4]
Task(haiku): "src/components/ErrorMessage.tsx 새로 생성 — {message: string} props,
             빨간색 텍스트로 에러 표시하는 간단한 컴포넌트"                      [패턴 4]
Task(sonnet): "src/components/UserForm.tsx에 validators import하고 onSubmit에
              검증 로직 통합 + ErrorMessage 컴포넌트 연결"                     [GLM: 큰 파일]
```

**예시 3: "API 엔드포인트 5개 추가"**

```
❌ BEFORE:
Task(haiku): "REST API 엔드포인트 5개 추가: GET /users, POST /users,
             GET /users/:id, PUT /users/:id, DELETE /users/:id"
→ 라우터 파일 Read + 5개 핸들러 작성 + 타입 정의 → ⛔ 초과

✅ AFTER (5개 병렬):
Task(haiku): "src/routes/users.ts에 GET /users 핸들러 추가. DB에서 전체 유저 조회,
             Response: User[] 반환"
Task(haiku): "src/routes/users.ts에 POST /users 핸들러 추가. body: {name, email},
             새 유저 생성, Response: User 반환"
Task(haiku): "src/routes/users.ts에 GET /users/:id 핸들러 추가. params.id로 조회,
             없으면 404, Response: User"
Task(haiku): "src/routes/users.ts에 PUT /users/:id 핸들러 추가. body로 업데이트,
             Response: User"
Task(haiku): "src/routes/users.ts에 DELETE /users/:id 핸들러 추가. 삭제 후 204 반환"
```

> ⚠️ **같은 파일에 5개 병렬 쓰기** — 충돌 가능. 실제로는 순차 실행하거나, 각각 별도 파일로 분리 후 GLM이 통합.

**예시 4: "테스트 코드 작성"**

```
❌ BEFORE:
Task(haiku): "src/services/auth.ts의 모든 함수에 대한 Jest 테스트 작성"
→ 소스 파일 Read(500줄) + 테스트 파일 전체 Write → 도구 호출 많음

✅ AFTER:
Task(haiku): "src/__tests__/auth.login.test.ts 생성 — login() 함수 테스트 3개:
             성공 케이스, 잘못된 비밀번호, 존재하지 않는 유저"                  [패턴 4]
Task(haiku): "src/__tests__/auth.register.test.ts 생성 — register() 함수 테스트 3개:
             성공, 중복 이메일, 약한 비밀번호"                                 [패턴 4]
Task(haiku): "src/__tests__/auth.token.test.ts 생성 — verifyToken() 테스트 3개:
             유효한 토큰, 만료 토큰, 잘못된 서명"                              [패턴 4]
```

> **패턴 4 (독립 생성)가 테스트에 최적**: 기존 코드를 Read할 필요 없이 함수 시그니처와 예상 동작만 프롬프트에 전달.

**예시 5: "대규모 리팩토링"**

```
❌ BEFORE:
Task(haiku): "src/legacy/ 디렉토리의 모든 Class를 함수형으로 리팩토링"
→ ⛔ 절대 불가 (여러 파일 탐색 + 의존성 분석 + 대량 수정)

✅ AFTER (3단계):
1단계 — Opus(architect): "src/legacy/ 분석하여 리팩토링 계획 수립.
        파일별 Class→함수 변환 맵 작성"
    → 결과: 계획서 (어떤 클래스를 어떤 함수로 변환할지)

2단계 — GLM-4.7(executor) × 큰 파일:
    Task(sonnet): "src/legacy/UserService.ts (600줄) Class를 함수형으로 변환"
    Task(sonnet): "src/legacy/AuthProvider.ts (400줄) Class를 함수형으로 변환"

2단계 — Qwen3(executor-low) × 작은 파일:
    Task(haiku): "src/legacy/helpers.ts (80줄) formatDate Class를 순수 함수로 변환"
    Task(haiku): "src/legacy/constants.ts (40줄) ConfigClass를 const 객체로 변환"
    Task(haiku): "src/legacy/types.ts (60줄) interface 정리 및 export 추가"

3단계 — Opus(architect): "리팩토링 결과 검증"
```

##### 에스컬레이션 규칙 (Qwen3 → GLM/GPT 전환)

| 조건 | Qwen3 | GLM-4.7 | GPT-5.2 |
|------|-------|---------|---------|
| 파일 ≤200줄, 함수 1개 수정 | ✅ | | |
| 파일 201~500줄, 함수 1개 | ⚠️ 가능 | ✅ 권장 | |
| 파일 >500줄 | ❌ | ✅ | |
| 파일 2개 이상 동시 수정 | ❌ | ✅ | |
| MCP 응답 큰 도구 (playwright, context7) | ❌ | ✅ | |
| 전체 코드베이스 분석 | ❌ | ❌ | ✅ |
| 컨텍스트 60K+ 토큰 | ❌ | ❌ | ✅ (자동) |
| 새 파일 생성 (인터페이스 명확) | ✅ 최적 | | |
| 린트/타입 에러 단건 수정 | ✅ 최적 | | |
| 단순 코드 스니펫 생성 | ✅ 최적 | | |

##### 안티패턴 (절대 하지 말 것)

```
⛔ 안티패턴 1: "파일 전체를 이해한 후 수정해줘"
   → Qwen3는 큰 파일을 "이해"할 여유가 없다. 수정할 위치와 내용을 명시해야 한다.

⛔ 안티패턴 2: "여러 파일을 참조해서 수정해줘"
   → 파일 2개 Read만으로 가용 공간 소진. 파일별로 분리하거나 GLM에 위임.

⛔ 안티패턴 3: "Grep으로 먼저 찾고 수정해줘"
   → Grep 결과가 크면 그 자체로 수천 토큰. Grep은 GLM이 하고, 결과를 Qwen3 프롬프트에 포함.

⛔ 안티패턴 4: "context7로 문서 찾아보고 구현해줘"
   → context7 응답은 1K~15K 토큰. Qwen3에서 호출하면 즉시 오버플로우.

⛔ 안티패턴 5: "이전 대화 내용을 참고해서..."
   → 서브에이전트는 자기 Task 프롬프트만 본다. 컨텍스트 히스토리 없음.
   → 필요한 정보는 반드시 프롬프트에 포함해야 한다.

⛔ 안티패턴 6: max_turns를 10 이상으로 설정
   → 턴이 많을수록 대화 히스토리 누적 → 16K 소진. max_turns: 5 이하 권장.
```

##### oh-my-claudecode ultrawork 연동

ultrawork 모드에서 Qwen3-Coder(executor-low)를 병렬 실행할 때의 Task 분리 규칙:

```
ultrawork "5개 API 엔드포인트 구현" 실행 시:

┌── orchestrator(Opus) ─────────────────────────────────────┐
│                                                           │
│  "5개 엔드포인트를 각각 독립 Task로 분해"                    │
│                                                           │
│  ┌─ executor-low(Qwen3) ─┐  프롬프트: 짧고 구체적         │
│  │ "GET /users 핸들러     │  max_turns: 5                 │
│  │  Response: User[]"     │  대상: 1 파일, 1 함수          │
│  └────────────────────────┘                               │
│  ┌─ executor-low(Qwen3) ─┐                               │
│  │ "POST /users 핸들러    │                               │
│  │  body: {name, email}"  │  ← 5개 동시 실행              │
│  └────────────────────────┘    각 ~150 tok/s              │
│  ┌─ executor-low(Qwen3) ─┐    총 ~750 tok/s              │
│  │ "GET /users/:id"       │                               │
│  └────────────────────────┘                               │
│  ┌─ executor-low(Qwen3) ─┐                               │
│  │ "PUT /users/:id"       │                               │
│  └────────────────────────┘                               │
│  ┌─ executor-low(Qwen3) ─┐                               │
│  │ "DELETE /users/:id"    │                               │
│  └────────────────────────┘                               │
│                                                           │
│  → 모두 완료 후 architect(Opus) 검증                       │
└───────────────────────────────────────────────────────────┘
```

**Task 프롬프트 템플릿 (executor-low용)**:

```
[대상 파일]: src/routes/users.ts (120줄)
[수정 위치]: 파일 끝에 추가
[작업]: GET /users 핸들러 함수 작성
[인터페이스]:
  - Method: GET
  - Path: /users
  - Response: User[] (id, name, email)
  - Error: 500 → { error: string }
[제약]: express 라우터 사용, async/await 패턴
```

> **핵심**: 프롬프트에 "파일 읽고 분석해서 알아서 해줘"가 아니라, **파일명 + 수정 위치 + 구체적 인터페이스 + 제약 조건**을 명시. Qwen3가 Read 없이 바로 Write할 수 있게.

##### 모니터링 및 안전장치

**1. maxtoken transformer** (현재 설정):
```json
["maxtoken", {"max_tokens": 15000}]
```
- 응답 토큰을 15,000으로 제한하여 vLLM OOM 방지
- 하지만 input이 크면 output 공간이 자동으로 줄어듦

**2. vLLM 로그 모니터링**:
```bash
# 컨텍스트 초과 에러 감지
ssh hwandam@10.5.5.11 "grep 'exceeds max_model_len\|context length' ~/vllm-server-new.log | tail -5"
```

**3. Claude Code auto-compaction**:
- 서브에이전트 내에서도 컨텍스트 초과 시 auto-compaction 동작
- 하지만 16K에서 compaction이 동작하면 **이미 품질이 저하된 상태**
- compaction에 의존하지 말고, 애초에 16K 안에서 완료되도록 Task 설계

**4. max_turns 안전장치**:
```
Task(model="haiku", max_turns=5, prompt="...")
```
- `max_turns: 5` → 최대 5턴으로 제한 → 대화 누적 방지
- 5턴 안에 완료 못하면 → Task 실패 → orchestrator가 재분해 또는 GLM 에스컬레이션

##### VRAM 확보 시 max-model-len 증가 검토

| 서버 | GPU | 현재 max-model-len | 증가 가능? | 예상 |
|------|-----|-------------------|----------|------|
| Cognit | 2x RTX 3080 Ti (24GB) | 16,384 | ⚠️ 제한적 | 24K 가능성 (테스트 필요) |
| Nexus | 2x RTX 3090 (48GB) | 16,384 | ✅ 여유 | 32K~48K 가능 |

```bash
# 테스트: Nexus에서 32K로 증가
python -m vllm.entrypoints.openai.api_server \
  --model Qwen3-Coder-30B-A3B \
  --tensor-parallel-size 2 \
  --max-model-len 32768 \  # 16K → 32K
  --gpu-memory-utilization 0.95 \
  ...
```

> 32K로 증가하면 도구 호출 안전 한계가 3~4회 → **7~8회로 2배** 확장. Task 분리 부담 크게 감소. Phase 3 완료 후 우선 테스트 권장.

##### 클린 아키텍처 기반 Task 분리 — 의존성 최소화 원칙 ⭐

> **Maestro 오케스트라의 근본 철학**: 각 악기(에이전트)가 독립적으로 연주할 수 있어야 합주가 성공한다. 클린 아키텍처의 **의존성 역전**, **레이어 분리**, **단일 책임** 원칙이 Task 분리의 기본이다.

**왜 클린 아키텍처가 16K Task 분리의 핵심인가?**

```
의존성이 많은 코드:
  UserController → UserService → UserRepository → Database → Config → Logger → ...
  → 하나를 수정하려면 모든 의존성을 Read해야 함 → 16K 즉시 초과

의존성이 분리된 코드:
  UserController → IUserService (인터페이스)
  UserService → IUserRepository (인터페이스)
  → 인터페이스만 알면 독립적으로 수정 가능 → 16K 안에서 완결
```

**레이어별 Task 할당 전략 (의존성 흐름 = 바깥→안쪽)**

```
┌─────────────────────────────────────────────────────────────┐
│  레이어 4: Presentation (UI/API)                              │
│  ├── 컴포넌트, 라우터, 컨트롤러                                │
│  ├── 의존성: 인터페이스만 (구현체 모름)                         │
│  └── 🥁 Qwen3 적합 — 인터페이스 명세만으로 작성 가능            │
├─────────────────────────────────────────────────────────────┤
│  레이어 3: Application (Use Cases)                            │
│  ├── 서비스, 유스케이스, 비즈니스 로직                          │
│  ├── 의존성: Domain 인터페이스                                 │
│  └── 🎻 GLM-4.7 적합 — 비즈니스 로직 이해 필요                 │
├─────────────────────────────────────────────────────────────┤
│  레이어 2: Domain (Entities + Interfaces)                     │
│  ├── 엔티티, 값 객체, 인터페이스 정의                           │
│  ├── 의존성: 없음 (가장 안쪽)                                  │
│  └── 🥁 Qwen3 최적 — 의존성 제로, 독립 생성                    │
├─────────────────────────────────────────────────────────────┤
│  레이어 1: Infrastructure (DB, External)                      │
│  ├── Repository 구현체, 외부 API 클라이언트                     │
│  ├── 의존성: Domain 인터페이스 + 외부 라이브러리                 │
│  └── 🎻 GLM-4.7 적합 — 외부 라이브러리 API 이해 필요            │
└─────────────────────────────────────────────────────────────┘

의존성 방향: Presentation → Application → Domain ← Infrastructure
                                          ↑
                            모든 의존성이 Domain을 향한다
```

**인터페이스 우선 개발 (Interface-First) — 16K 최적화의 핵심**

```
┌── 1단계: 🎼 Maestro(Opus) ──────────────────────────────────┐
│                                                              │
│  "전체 아키텍처 설계 + 인터페이스 정의"                         │
│                                                              │
│  결과물:                                                     │
│  ├── src/domain/interfaces/IUserRepository.ts                │
│  ├── src/domain/interfaces/IAuthService.ts                   │
│  ├── src/domain/entities/User.ts                             │
│  └── src/domain/types.ts                                     │
│                                                              │
│  → 이 인터페이스들이 모든 후속 Task의 "계약서" 역할             │
└──────────────────────────────────────────────────────────────┘
         │
         ▼
┌── 2단계: 🥁 Ensemble(Qwen3) ×N 병렬 ─────────────────────────┐
│                                                               │
│  각 Task에 인터페이스를 프롬프트에 포함 → Read 불필요            │
│                                                               │
│  Task A: "IUserRepository를 구현하는 PrismaUserRepository 작성  │
│           interface IUserRepository {                          │
│             findById(id: string): Promise<User | null>         │
│             create(data: CreateUserDTO): Promise<User>         │
│           }"                                                  │
│                                                               │
│  Task B: "IAuthService를 구현하는 JwtAuthService 작성           │
│           interface IAuthService {                             │
│             login(email, password): Promise<Token>             │
│             verify(token): Promise<User>                      │
│           }"                                                  │
│                                                               │
│  Task C: "User 엔티티 기반 UserDTO 변환 함수 작성               │
│           class User { id, name, email, createdAt }"          │
│                                                               │
│  → 각 Task는 인터페이스만 보고 독립 작성 가능                    │
│  → 다른 파일 Read 불필요 → 도구 호출 최소                       │
└───────────────────────────────────────────────────────────────┘
         │
         ▼
┌── 3단계: 🎻 Concertmaster(GLM-4.7) ─────────────────────────┐
│                                                              │
│  "의존성 주입(DI) 설정 + 레이어 통합 + 통합 테스트"             │
│                                                              │
│  → 여러 파일 읽기 필요 → 200K 컨텍스트로 안전                  │
│  → 인터페이스-구현체 연결, 라우팅 설정, E2E 검증                │
└──────────────────────────────────────────────────────────────┘
         │
         ▼
┌── 4단계: 🎼 Maestro(Opus) ──────────────────────────────────┐
│  "최종 아키텍처 검증 — 의존성 방향 확인, SOLID 원칙 준수"       │
└──────────────────────────────────────────────────────────────┘
```

**의존성 최소화 Task 설계 규칙**

| # | 규칙 | 이유 | 예시 |
|---|------|------|------|
| 1 | **인터페이스를 프롬프트에 포함** | 다른 파일 Read 불필요 | `"IUserRepo 구현: findById(id): Promise<User>"` |
| 2 | **구현체는 인터페이스만 의존** | 구현체 간 의존 없음 → 병렬 가능 | Service는 IRepo만 알고, Repo 구현 모름 |
| 3 | **엔티티/DTO를 프롬프트에 인라인** | 타입 파일 Read 불필요 | `"User: {id, name, email}"` |
| 4 | **통합(DI/Wiring)은 GLM에게** | 여러 파일 조합 필요 → 16K 부족 | DI 컨테이너 설정은 sonnet |
| 5 | **테스트도 인터페이스 기반 Mock** | 구현체 Read 불필요 | `"IUserRepo를 Mock하는 유닛 테스트"` |
| 6 | **순환 의존 절대 금지** | A→B→A면 두 파일 다 읽어야 함 | 단방향 의존만 허용 |

**프로젝트 구조 템플릿 (클린 아키텍처)**

```
src/
├── domain/                    # 🥁 Qwen3 영역 — 의존성 제로
│   ├── entities/              # User, Order, Product...
│   ├── interfaces/            # IUserRepo, IAuthService...
│   ├── types.ts               # DTO, 공통 타입
│   └── errors.ts              # 도메인 에러 클래스
│
├── application/               # 🎻 GLM-4.7 영역 — Domain만 의존
│   ├── use-cases/             # CreateUser, LoginUser...
│   └── services/              # AuthService, NotificationService...
│
├── infrastructure/            # 🎻 GLM-4.7 영역 — Domain + 외부 라이브러리
│   ├── database/              # PrismaUserRepo, RedisCache...
│   ├── external/              # StripeClient, SendGridClient...
│   └── config/                # 환경 설정, DI 컨테이너
│
├── presentation/              # 🥁 Qwen3 영역 — 인터페이스 기반 작성 가능
│   ├── api/                   # Express 라우터, 컨트롤러
│   ├── components/            # React 컴포넌트
│   └── middleware/            # 인증, 로깅 미들웨어
│
└── main.ts                    # 🎻 GLM-4.7 — DI 조립, 앱 시작
```

> **핵심**: `domain/`과 `presentation/`은 독립적으로 작성 가능 → **Qwen3-Coder가 16K 안에서 완결**. `application/`과 `infrastructure/`는 여러 의존성 이해 필요 → **GLM-4.7이 담당**. 전체 설계와 통합 검증은 **Opus가 지휘**.

**실전 적용: "유저 CRUD API 구현" 전체 워크플로우**

```
🎼 Maestro(Opus): 아키텍처 설계 + 인터페이스 정의
  → domain/entities/User.ts
  → domain/interfaces/IUserRepository.ts
  → domain/interfaces/IUserService.ts

🥁 Ensemble(Qwen3) ×5 병렬:                         [16K 안전]
  Task 1: "domain/entities/User.ts 생성 — id,name,email,createdAt"
  Task 2: "infrastructure/database/PrismaUserRepo.ts —
           IUserRepository 구현, 인터페이스: findById, findAll, create, update, delete"
  Task 3: "presentation/api/userController.ts —
           GET/POST/PUT/DELETE 핸들러, IUserService 의존"
  Task 4: "presentation/api/userValidator.ts —
           createUser, updateUser 요청 검증 함수"
  Task 5: "domain/errors.ts — UserNotFoundError, ValidationError 클래스"

🎻 Concertmaster(GLM-4.7):                           [200K 안전]
  Task 6: "application/use-cases/CreateUser.ts —
           IUserRepo + INotificationService 조합한 유스케이스"
  Task 7: "infrastructure/config/container.ts —
           의존성 주입 설정, 모든 인터페이스-구현체 연결"
  Task 8: "main.ts 수정 — 새 라우터 등록 + 미들웨어 연결"

🎼 Maestro(Opus): 최종 검증
  → 의존성 방향 확인 (바깥→안쪽만)
  → SOLID 원칙 준수
  → 통합 테스트 확인
```

##### Ultra-Thin 통신 아키텍처 — 쪼갠 결과를 최소 컨텍스트로 주고받기 ⭐⭐⭐

> **1T1F로 쪼갠 Task의 결과를 어떻게 주고받는가?** 이 섹션은 R3 Task 분리 전략의 **실행 계층**을 정의한다.
> claude-labs Ultra-Thin 패턴을 Maestro 4모델 환경에 맞게 재설계.

###### 핵심 문제

```
일반 모드:
  Orchestrator가 50개 Task의 결과를 직접 수신 → ~150K 토큰 → 컨텍스트 오버플로우

Ultra-Thin 모드:
  Orchestrator는 교통정리만 → 서브에이전트가 모든 작업 처리
  결과는 1줄 시그널만 수신 → 200 Task도 ~16K 토큰 → ✅ 안전
```

###### 4계층 통신 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│              Maestro 최소 컨텍스트 통신 아키텍처                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Layer 4: Artifact (코드 파일)                                   │
│  ├── src/**/*.ts, *.py 등 실제 소스 코드                        │
│  ├── 모든 에이전트가 파일시스템으로 직접 접근                    │
│  └── 부모 컨텍스트 비용: 0                                       │
│                                                                 │
│  Layer 3: Contract (JSON 스키마)                                 │
│  ├── .claude/analysis/architecture.json                         │
│  ├── .claude/analysis/requirements.json                         │
│  ├── .claude/analysis/system-design.json                        │
│  ├── .claude/analysis/api-design.json                           │
│  └── 부모 컨텍스트 비용: 0 (쓸 때), 필요시만 Read               │
│                                                                 │
│  Layer 2: State (상태 조율)                                      │
│  ├── .claude/orchestrate-state.json                             │
│  ├── tasks: pending/ready/in_progress/completed/failed          │
│  └── 부모 컨텍스트 비용: ~200 tokens (갱신 시)                   │
│                                                                 │
│  Layer 1: Signal (1줄 프로토콜) ← 유일하게 부모 컨텍스트 사용     │
│  ├── READY:T1.3,T1.4        (~50 tokens)                        │
│  ├── DONE:T1.3               (~30 tokens)                        │
│  ├── FAIL:T1.3:reason        (~50 tokens)                        │
│  ├── PHASE_DONE:1            (~30 tokens)                        │
│  └── ALL_DONE                (~20 tokens)                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

###### Signal Protocol v1.0 — 1줄 시그널 명세

| Signal | Format | 용도 | Max Tokens |
|--------|--------|------|-----------|
| 실행가능 | `READY:T1.3,T1.4` | dependency-resolver → 오케스트레이터 | ~50 |
| 실행가능(그룹) | `READY:T1.3,T1.4\|T1.5` | `\|`로 그룹 구분, 첫 그룹만 즉시 실행 | ~60 |
| 완료 | `DONE:T1.3` | task-executor → 오케스트레이터 | ~30 |
| 실패 | `FAIL:T1.3:TypeError - msg` | 10회 재시도 후 실패 | ~50 |
| Phase 완료 | `PHASE_DONE:1` | dependency-resolver → 오케스트레이터 | ~30 |
| 전체 완료 | `ALL_DONE` | 유일한 종료 조건 | ~20 |
| 에러 | `ERROR:TASKS.md not found` | 시스템 에러 | ~40 |
| 에스컬레이션 | `ESCALATE:T1.3:context_overflow` | Qwen3 16K 초과 → 모델 승격 | ~50 |
| 아키텍처 | `ARCH_MAP:{stack}\|{structure}\|{pattern}` | architecture-analyst | ~80 |
| 요구사항 | `REQ_DONE:FR:{n}\|NFR:{n}\|RISK:{n}` | requirements-analyst | ~60 |
| 설계 | `DESIGN_DONE:{domain}:{n}svc,{n}api` | system-designer | ~80 |
| API | `API_DONE:endpoints:{n}\|schemas:{n}` | api-designer | ~60 |
| 태스크 | `PLAN_DONE:P0:{n},P1:{n}\|total:{n}` | task-planner | ~70 |
| 영향도 | `IMPACT:files:{n}\|tests:{n}\|risk:{level}` | impact-analyzer | ~60 |

**Protocol 규칙**: Delimiter — `:` (필드), `|` (그룹), `,` (리스트). 모든 시그널 ≤ 100 tokens.

###### 에스컬레이션 시그널 (Maestro 전용)

```
ESCALATE:T1.3:context_overflow    → Qwen3 16K 초과, GLM으로 승격
ESCALATE:T1.3:model_timeout       → 모델 응답 타임아웃
ESCALATE:T1.3:concurrency_limit   → GLM concurrency=1 초과

오케스트레이터 처리:
  context_overflow  → 동일 task를 sonnet(GLM-4.7)으로 재실행
  model_timeout     → 3회 재시도 후 FAIL 처리
  concurrency_limit → 큐에 넣고 다른 ready task 먼저 실행
```

###### 모델별 통신 규칙

| 모델 | 역할 | 최대 수신 | 최대 발신 | 파일 I/O |
|------|------|----------|----------|---------|
| 🎼 Opus (오케스트레이터) | 교통정리만 | 1줄 시그널만 | Task ID만 | state.json Read만 |
| 🎻 GLM-4.7 (task-executor) | 자율 실행 | Task ID (50 tok) | DONE/FAIL (30 tok) | 모든 파일 접근 |
| 🥁 Qwen3 (dependency-resolver) | 의존성 해석 | RESOLVE_NEXT (10 tok) | READY (50 tok) | TASKS.md + state.json만 |
| 🎹 GPT-5.2 (대형 컨텍스트) | 전체 문서 처리 | 제한 없음 | 제한 없음 | 모든 파일 접근 |

###### Ultra-Thin 실행 루프

```
┌─────────────────────────────────────────────────────────────────┐
│  ULTRA-THIN ORCHESTRATION LOOP (🎼 Maestro 내부)                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  LOOP:                                                          │
│  │                                                              │
│  ├── Step 1: dependency-resolver 호출                            │
│  │   Task(model="haiku", prompt="RESOLVE_NEXT")                 │
│  │   → "READY:T1.3,T1.4" 또는 "PHASE_DONE:1" 또는 "ALL_DONE"  │
│  │                                                              │
│  ├── Step 2: ALL_DONE이면 → 최종 보고 → EXIT (유일한 종료)      │
│  │                                                              │
│  ├── Step 3: PHASE_DONE이면 → 자동 병합 → GOTO LOOP             │
│  │                                                              │
│  ├── Step 4: READY이면 → task-executor 병렬 호출                 │
│  │   Task(model="sonnet", prompt="TASK_ID:T1.3")               │
│  │   Task(model="sonnet", prompt="TASK_ID:T1.4")               │
│  │   → "DONE:T1.3", "DONE:T1.4"                                │
│  │                                                              │
│  ├── Step 5: FAIL 수신 시 → failed_tasks에 추가, 계속 진행       │
│  │   ESCALATE 수신 시 → 모델 승격 후 재실행                     │
│  │                                                              │
│  └── GOTO LOOP                                                  │
│                                                                 │
│  ⚠️ GLM concurrency=1 제약:                                     │
│  task-executor 병렬 실행 시, 동시에 GLM으로 가는 요청이 1개만    │
│  가능. 나머지는 큐잉되거나 Qwen3로 내려감.                       │
│  → ultrawork 모드에서는 haiku(Qwen3) 에이전트만 병렬 사용       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

###### 컨텍스트 절감 비교

| 항목 | 일반 모드 | Ultra-Thin | 절감 |
|------|----------|------------|------|
| **Task당 오케스트레이터 비용** | ~3,000 tok | ~80 tok | 97% |
| **50 Task 총합** | ~150K tok | ~4K tok | 97% |
| **200 Task 총합** | ~600K tok (불가) | ~16K tok | 97% |
| **분석 파이프라인** | ~46K tok | ~350 tok | 99.2% |

###### 분석 파이프라인 데이터 흐름

분석 에이전트 간 상세 데이터는 Layer 3 (JSON 파일)로 전달. 오케스트레이터 컨텍스트 비용: 0.

```
architecture-analyst ──write──→ .claude/analysis/architecture.json
                                    │
requirements-analyst ──write──→ .claude/analysis/requirements.json
                                    │
              ┌─────── read ────────┘
              ▼
system-designer ──write──→ .claude/analysis/system-design.json
api-designer ───write──→ .claude/analysis/api-design.json
              │                     │
              └─── read ────────────┘
                    ▼
task-planner ──write──→ docs/planning/TASKS.md
                        .claude/orchestrate-state.json

오케스트레이터가 보는 것 (5단계 합계: ~350 tokens):
  Step 1: "ARCH_MAP:fastapi+react|monorepo|3-tier"
  Step 2: "REQ_DONE:FR:5|NFR:3|RISK:2"
  Step 3: "DESIGN_DONE:auth:3svc,5api|pattern:repo"
  Step 4: "API_DONE:endpoints:12|schemas:8"
  Step 5: "PLAN_DONE:P0:3,P1:5|total:8|parallel:6"
```

###### Qwen3-Coder dependency-resolver 토큰 예산

```
┌─── Qwen3-Coder 16,384 tokens ────────────────────────────────┐
│                                                               │
│  ■■■■■■■■ Agent Prompt (resolver 정의)         ~2,000        │
│  ■■■■■■■■■ System + CLAUDE.md context           ~3,000        │
│  ■■■■       입력: "RESOLVE_NEXT"                    ~10        │
│  ■■■■■■■■■■■■■ TASKS.md Read (50 tasks)        ~3,000        │
│  ■■■■■■ orchestrate-state.json Read              ~1,000        │
│  ■■■■ state.json Write                             ~500        │
│  ■■ 출력: "READY:T1.3,T1.4"                         ~50        │
│  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 여유            ~6,824        │
│                                                               │
│  총 사용: ~9,560 / 16,384 (58%) → ✅ 안전                     │
│                                                               │
│  ⚠️ 200+ Task 시 TASKS.md가 12K+ 토큰 → 16K 초과!             │
│  해결: RESOLVE_NEXT:PHASE:2 (현재 Phase만 파싱)                │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

###### 상태 파일 스키마 (orchestrate-state.json)

```json
{
  "version": "2.0",
  "mode": "ultra-thin",
  "project": "my-project",
  "execution": {
    "current_phase": 1,
    "worktree": "worktree/phase-1-feature",
    "started_at": "2026-01-21T09:00:00Z"
  },
  "tasks": {
    "pending": ["T1.5", "T1.6"],
    "ready": ["T1.3", "T1.4"],
    "in_progress": [],
    "completed": ["T0.5.1", "T1.1", "T1.2"],
    "failed": []
  },
  "dependencies": {
    "T1.3": ["T1.1", "T1.2"],
    "T1.4": ["T1.1"],
    "T1.5": ["T1.3", "T1.4"]
  },
  "checkpoints": {
    "phase_0": {
      "completed_at": "2026-01-21T09:30:00Z",
      "tasks": 3,
      "merged": true
    }
  }
}
```

###### run_in_background 현황 및 권장사항

| 기준 | 포그라운드 + 1줄 프로토콜 | 백그라운드 (run_in_background) |
|------|--------------------------|-------------------------------|
| 컨텍스트 절감 | 97%+ | 99% (이론상) |
| 신뢰성 | ✅ 안정 | ❌ 알려진 버그 (output_file 0바이트, JSONL 누출) |
| 병렬 실행 | Task 도구 병렬 호출 지원 | 별도 폴링 필요 |
| 에러 처리 | 즉시 FAIL 수신 | 폴링 지연 |

**결론**: 포그라운드 + 1줄 프로토콜을 기본 채택. `run_in_background` 버그 수정 후 마이그레이션 가능.

###### 에이전트 수명주기 규칙

| 조건 | 동작 |
|------|------|
| 컨텍스트 윈도우 > 85% | 즉시 종료, 결과 반환 |
| 3회 연속 잘못된 제안 | 종료, FAIL 반환 |
| 순환 편집 감지 | 종료, ESCALATE 반환 |
| 동일 에러 3회 반복 | systematic-debugging 발동 |
| 10회 재시도 초과 | FAIL 반환 (최종) |

###### 모드 선택 가이드

| Task 수 | 권장 모드 | 오케스트레이터 컨텍스트 |
|---------|----------|----------------------|
| 1-30개 | 일반 모드 (직접 관리) | ~90K (Opus 200K의 45%) |
| 30-50개 | 일반 + Phase별 /compact | ~150K (위험 수준) |
| **50-200개** | **Ultra-Thin** | **~16K (Opus 200K의 8%)** |
| 200개+ | Ultra-Thin + Phase 분할 | ~16K (Phase당) |

### 8.6 폴백 체인

```
┌─────────── 라우터별 폴백 경로 ───────────┐

think (계획/리뷰):
  Opus 4.5 ──장애──→ GLM-4.7 (수동 전환)
                      └──장애──→ GPT-5.2 Codex (수동)

default (메인 코딩):
  GLM-4.7 ──장애──→ Opus 4.5 (자동 전환) ⭐ 핵심 폴백
                     └──장애──→ Qwen3-Coder (수동, 16K 제한 주의)

background (빠른 작업):
  Qwen3-Coder ──VPN 단절──→ GLM-4.7 (수동 전환)
                              └──장애──→ Opus 4.5 (수동)

longContext (대규모 분석):
  GPT-5.2 Codex ──장애──→ Opus 4.5 (200K로도 대부분 커버)
                           └──장애──→ GLM-4.7 (200K, 100K 이하만)

└──────────────────────────────────────────┘
```

**자동 폴백 구현 (claude-code-router v2.0.0 지원)**:

claude-code-router v2.0.0은 `fallback` config를 네이티브 지원한다 (config.json 섹션 5.1 참조). 1차 모델 요청 실패 시 `fallback` 리스트의 다음 모델로 자동 전환된다.

- **R1 GLM-4.7 장애 → Opus 자동 전환**: `"fallback": { "default": ["anthropic,claude-opus-4-5-20251101"] }` 설정으로 **자동 폴백** 동작. config.json 핫스왑 불필요.
- **R4 VPN 단절 → Cloud API 유지**: VPN이 끊겨도 Internet 경유 Cloud API는 영향 없음. Qwen3-Coder만 불가 → `"fallback": { "background": ["zai,glm-4.7"] }`로 GLM-4.7이 자동 대행.
- **R5 Cognit vLLM 다운**: background 폴백이 자동으로 GLM-4.7으로 전환.

> **추가 대응 (선택)**: `CUSTOM_ROUTER_PATH`를 활용하여 health check 기반 동적 라우팅 구현 가능. 예: vLLM health check 실패 시 Cloud API로 선제 전환하는 Custom Router JS 모듈 작성.

### 8.7 served-model-name 규칙

- Claude Code는 모델명에 `/`를 허용하지 않음
- ❌ `Qwen/Qwen3-Coder-30B-A3B-Instruct` (HuggingFace 원본명)
- ✅ `Qwen3-Coder-30B-A3B` (현재 설정, 정상)
- ✅ `glm-4.7` (Z.AI API 모델명)
- ✅ `gpt-5.2-codex` (OpenAI API 모델명)
- ✅ `deepseek-r1-70b` (Phase 4에서 사용할 이름)

---

## 9. 모델별 최적 사용 시나리오

### 9.1 작업 유형별 1순위 모델

| 작업 유형 | 1순위 모델 (사용률) | 2순위 모델 | 근거 |
|----------|-------------------|-----------|------|
| **전략 계획/아키텍처** | Opus 4.5 (10%) | GLM-4.7 | SWE-bench 80.9%, 0% tool error, edge case 감지 |
| **코드 리뷰 (심층)** | Opus 4.5 (10%) | GLM-4.7 | 1분 완료, 100% 보안 탐지, async 버그 발견 |
| **멀티파일 리팩토링** | GLM-4.7 (35%) | Opus 4.5 | SWE-bench 73.8%, 비용 효율 |
| **빠른 단일 파일 코딩** | Qwen3-Coder (50%) | GLM-4.7 | 180 tok/s 속도 우위 |
| **UI/프론트엔드 생성** | GLM-4.7 (35%) | Opus 4.5 | "Vibe Coding" 능력 우수 |
| **Tool Use / 에이전틱** | GLM-4.7 (35%) | Opus 4.5 | τ²-Bench 87.4% |
| **대규모 코드베이스 분석** | GPT-5.2 Codex (5%) | Opus 4.5 | 400K 컨텍스트, SWE-bench Pro 55.6% |
| **수학/순수 추론** | GPT-5.2 Codex (5%) | DeepSeek-R1 | AIME 2025 100%, MATH-500 94.5% |
| **디버깅 (로직 분석)** | DeepSeek-R1 (<1%) | Opus 4.5 | Chain-of-thought, Codeforces 1633 |
| **백그라운드 단순 작업** | Qwen3-Coder (50%) | - | 속도 최우선 |

### 9.2 라우터별 자동 매핑

| 라우터 | 모델 | 사용률 | 자동 트리거 조건 |
|--------|------|--------|----------------|
| `think` | Opus 4.5 | **10%** | `/plan`, `/review`, `/analyze` 명령어 |
| `default` | GLM-4.7 | **35%** | 기본 코딩 요청 |
| `longContext` | GPT-5.2 Codex | **5%** | 컨텍스트 60K+ tokens 시 자동 전환 |
| `background` | Qwen3-Coder | **50%** | 단일 파일 편집, 빠른 생성 요청 |

### 9.3 수동 전환 권장 시나리오

| 시나리오 | 수동 명령어 | 이유 |
|---------|-----------|------|
| 복잡한 알고리즘 디버깅 | `/model nexus,deepseek-r1-70b` | Chain-of-thought 추론 |
| 매우 큰 파일 분석 (100K+ tokens) | `/model openai,gpt-5.2-codex` | 400K 컨텍스트 |
| 비용 무관한 최고 품질 코딩 | `/model anthropic,claude-opus-4-5-20251101` | SWE-bench 80.9% |
| 매우 빠른 프로토타이핑 | `/model cognit,Qwen3-Coder-30B-A3B` | 180 tok/s |

---

## 10. 구현 Task 세분화

기존 20개 task를 **실질적 작업 단위 12개**로 재구성. 과도한 세분화 제거, Phase 순서에 정확히 매핑.

### 10.1 Task 목록

| ID | Phase | Task | 복잡도 | 선행 | 산출물 |
|----|-------|------|--------|------|--------|
| **T1** | P0 | Docker 개발 환경 구축 (Ubuntu 22.04 컨테이너, Node.js, MCP 서버) | 4 | - | Dockerfile, docker-compose.yml |
| **T2** | P0 | API 키 수집 + `.env` 파일 구성 (Anthropic, Z.AI, OpenAI) | 2 | - | `.env` |
| **T3** | P1 | claude-code-router 설치 + config.json 전체 작성 (4 Providers + Router 한번에) | 3 | T1 | `config.json` |
| **T4** | P1 | Cognit vLLM 연결 확인 (VPN + health check + 단순 요청) | 3 | T1 | 연결 테스트 결과 |
| **T5** | P1 | `ccr code` 실행 → Opus think + Qwen background 라우팅 확인 | 4 | T2, T3, T4 | Phase 1 검증 로그 |
| **T6** | P2 | Z.AI API 키 발급 + GLM-4.7 단독 테스트 (tool calling, 리팩토링, 100K 컨텍스트) | 5 | T2 | GLM-4.7 성능 리포트 |
| **T7** | P3 | config.json에 Z.AI provider 추가 → default 라우팅 검증 | 3 | T5, T6 | 업데이트된 config.json |
| **T8** | P3 | OpenAI API 설정 + GPT-5.2 longContext 자동 전환 검증 (60K+ 토큰) | 6 | T2, T7 | longContext 테스트 결과 |
| **T9** | P3 | 4개 모델 통합 라우팅 E2E 테스트 (20+ 케이스) + MCP 도구 공유 검증 | 7 | T7, T8 | E2E 테스트 리포트 |
| **T10** | P3 | 폴백 시나리오 테스트 (GLM→Opus 자동 전환, VPN 단절) + 대응 문서화 | 5 | T9 | 폴백 테스트 결과, 런북 |
| **T11** | P3 | 비용 벤치마크 (토큰 사용량 집계, $78/월 목표 검증) + 모니터링 스크립트 | 4 | T9 | 비용 리포트, 모니터링 스크립트 |
| **T12** | P4 | (선택) DeepSeek-R1 Nexus 배포 + 수동 전환 테스트 | 7 | T9 | DeepSeek vLLM 실행, config 업데이트 |
| **T13** | P1 | oh-my-claudecode 에이전트 티어 수정 (explore, architecture-analyst, test-specialist: haiku→sonnet) | 2 | T1 | 수정된 `.md` 파일 3개, 백업 |
| **T14** | P3 | ecomode 보호 에이전트 설정 (승격 3개 에이전트가 ecomode에서도 sonnet 유지 확인) | 3 | T9, T13 | ecomode 테스트 결과 |
| **T15** | P3 | ultrawork 병렬 실행 검증 (executor-low×5 → Qwen3 동시 처리 + architect → Opus 검증) | 4 | T9, T13 | 병렬 실행 로그, 모델별 라우팅 확인 |

### 10.2 의존성 그래프

```
T1 (Docker) ──→ T3 (config.json) ──→ T5 (P1 검증) ──→ T7 (GLM 추가) ──→ T9 (E2E)
                                       ↑                  ↑                  ↑
T2 (API 키) ──→ T5                    T6 (GLM 단독)      T8 (GPT-5.2)      T10 (폴백)
              ──→ T6                                                         T11 (비용)
              ──→ T8                                                         T12 (선택)
T1 ──→ T4 (Cognit 연결) ──→ T5                                              T14 (ecomode)
T1 ──→ T13 (에이전트 티어) ──→ T14, T15                                       T15 (병렬)
```

### 10.3 oh-my-claudecode 통합 Task 상세

#### T13: 에이전트 티어 수정

**대상 파일** (`~/.claude/agents/`):
- `explore.md`: `model: haiku` → `model: sonnet`
- `architecture-analyst.md`: `model: haiku` → `model: sonnet`
- `test-specialist.md`: `model: haiku` → `model: sonnet`

**이유**: Qwen3-Coder 16K 컨텍스트에서 이 에이전트들은 다수 파일 탐색/분석으로 컨텍스트 초과 위험. GLM-4.7(200K)로 라우팅하여 안전 확보.

**영속성 보장 방법** (oh-my-claudecode 업데이트 시 파일 덮어씌워짐 대응):
1. **Git 관리**: `~/.claude/agents/` 디렉토리를 git으로 관리하여 업데이트 후 복원
2. **패치 스크립트**: 업데이트 후 자동으로 3개 파일의 `model: haiku`를 `model: sonnet`으로 변경하는 셸 스크립트 작성
3. **`.omc-config.json` 오버라이드**: oh-my-claudecode의 config 기반 에이전트 모델 오버라이드 가능 여부 확인 (확인 필요)

> ⚠️ 이전에 언급된 "`~/.claude/agents/custom/` 디렉토리"는 실제로 존재하지 않는 기능이다. 위 3가지 방법 중 선택하여 적용.

#### T14: ecomode 보호 에이전트 설정

ecomode는 **공격적 하향 전략** 사용: sonnet 에이전트를 "haiku 우선 시도 → 실패 시 sonnet 복귀" 패턴으로 처리. 승격된 3개 에이전트가 ecomode에서 haiku(Qwen3-Coder, 16K)로 강등되면 **16K 오버플로우 위험 재발**.

**검증 시나리오**:
1. `eco` 모드 활성화
2. `explore` 에이전트 호출 → 라우터 로그에서 `zai,glm-4.7` (sonnet 유지) 확인
3. `executor-low` 에이전트 호출 → 라우터 로그에서 `cognit,Qwen3-Coder` (haiku 유지) 확인
4. **실패 케이스 테스트**: `explore`가 `cognit,Qwen3-Coder`로 라우팅되면 보호 실패

**대응 방법 (우선순위순)**:
1. 에이전트 `.md` 파일에서 `model: sonnet`으로 고정 + ecomode 스킬에 예외 에이전트 목록 추가
2. ecomode SKILL.md 자체를 수정하여 `explore`, `architecture-analyst`, `test-specialist`를 sonnet 최소 보장으로 하드코딩
3. Custom Router에서 이 3개 에이전트의 요청을 감지하여 항상 GLM-4.7로 라우팅하는 로직 추가

#### T15: ultrawork 병렬 실행 검증

**테스트 시나리오**:
```
"ulw fix all lint errors" 실행 →
  executor-low ×5 (haiku) → Qwen3-Coder 개별 ~150 tok/s, aggregate ~750 tok/s
  → 완료 후 architect (opus) → Opus 4.5 검증
  → 라우터 로그에서 cognit×5 + anthropic×1 확인
```

**확인 사항**:
- [ ] Qwen3-Coder가 동시 5개 요청 처리 가능 (vLLM `--max-num-seqs 8` 설정)
- [ ] 라우터 로그에 `background` 5회 + `think` 1회 기록
- [ ] 전체 소요 시간이 순차 실행 대비 3배 이상 빠름
- [ ] 동시 5개 요청 시 개별 속도 ~150 tok/s, aggregate ~750 tok/s 확인 (단일 180 대비 감소 정상)
- [ ] sonnet(GLM-4.7) 에이전트 2개 동시 호출 시 concurrency 에러 발생 확인 → 병렬은 haiku만 사용 규칙 검증

### 10.4 Phase별 일정 추정

| Phase | Tasks | 소요 시간 | 비고 |
|-------|-------|----------|------|
| **P0** (환경 구축) | T1, T2 | 반나절 | Docker + API 키 |
| **P1** (기본 라우팅) | T3, T4, T5, **T13** | 반나절 | Opus + Qwen3 + 에이전트 티어 수정 |
| **P2** (GLM 단독) | T6 | 1일 | Z.AI 가입 + 테스트 |
| **P3** (통합) | T7~T11, **T14, T15** | 2~3일 | 4모델 통합 + omc 검증 |
| **P4** (선택) | T12 | 반나절 | DeepSeek 배포 |
| **총합** | | **4~5일** | |

---

## 11. 검증 체크리스트

### 11.1 Phase 0 완료 기준

- [ ] Docker 컨테이너 빌드 성공 (`docker-compose build`)
- [ ] 컨테이너 내 `claude --version` 실행 확인
- [ ] 컨테이너 내 `ccr --version` 실행 확인
- [ ] MCP 서버 5개 이상 정상 로드 확인
- [ ] `.env` 파일에 ANTHROPIC_API_KEY 설정 + 컨테이너 내 접근 확인
- [ ] `.gitignore`에 `.env`, `config.json` 등록 확인

### 11.2 Phase 1 완료 기준

- [ ] `ccr code` 실행 시 라우터 3456 포트 리슨 확인 (또는 config에서 설정한 포트)
- [ ] `ccr activate` 환경변수 자동 설정 확인 (`echo $ANTHROPIC_BASE_URL`)
- [ ] think 요청 → 로그에 `anthropic,claude-opus-4-5-20251101` 확인
- [ ] background 요청 → 로그에 `cognit,Qwen3-Coder-30B-A3B` 확인
- [ ] Qwen3-Coder `enhancetool` transformer가 tool calling 안정성을 개선하는지 확인
- [ ] Qwen3-Coder 응답 속도 150+ tok/s 확인
- [ ] MCP 도구 (filesystem, git) 정상 동작 확인 (Opus/Qwen 각각)
- [ ] `/model` 명령어로 수동 전환 동작 확인

### 11.3 Phase 2 완료 기준

- [ ] Z.AI API 키 발급 완료
- [ ] GLM-4.7 단독 모드에서 간단 코딩 작업 성공
- [ ] GLM-4.7 멀티파일 리팩토링 정확도 확인
- [ ] GLM-4.7 tool calling 안정성 확인 (3/3 성공)
- [ ] GLM-4.7 100K 토큰 컨텍스트 테스트 (tool call 버그 발생 여부 기록)
- [ ] MCP 도구 정상 동작 확인 (GLM-4.7 경유)

### 11.4 Phase 3 완료 기준 (최종 성공 기준)

- [ ] **라우팅 정확도**: 4/4 라우터 (think/default/background/longContext) 올바른 모델 호출 — 로그 증거
- [ ] **longContext 자동 전환**: 60K+ 토큰 시 GPT-5.2 Codex로 자동 전환 확인
- [ ] **MCP 도구 공유**: 4개 모델 모두 filesystem, git, memory MCP 도구 정상 사용
- [ ] **폴백 동작**: `fallback` config 기반 자동 폴백 확인 (GLM-4.7 장애 → Opus, Qwen3 다운 → GLM-4.7)
- [ ] **비용 목표**: 일일 비용 ~$2.60 이하 (월 ~$78, 88% 절감) 검증
- [ ] **품질 유지**: GLM-4.7 코딩 품질 체감 확인 (SWE-bench 73.8% 수준)
- [ ] **속도 목표**: Qwen3-Coder background 180 tok/s 확인
- [ ] **수동 전환**: `/model` 명령어로 4개 provider 전환 성공
- [ ] **Docker 재현성**: `docker-compose down && docker-compose up` 후 전체 기능 정상

### 11.5 oh-my-claudecode 통합 완료 기준

#### 에이전트 라우팅 검증
- [ ] `executor-low`(haiku) 호출 → 라우터 로그에 `cognit,Qwen3-Coder-30B-A3B` 확인
- [ ] `executor`(sonnet) 호출 → 라우터 로그에 `zai,glm-4.7` 확인
- [ ] `architect`(opus) 호출 → 라우터 로그에 `anthropic,claude-opus-4-5-20251101` 확인
- [ ] 승격 에이전트 `explore`(sonnet) → `zai,glm-4.7` 라우팅 확인 (haiku가 아님)
- [ ] 승격 에이전트 `architecture-analyst`(sonnet) → `zai,glm-4.7` 라우팅 확인
- [ ] 승격 에이전트 `test-specialist`(sonnet) → `zai,glm-4.7` 라우팅 확인

#### 병렬 실행 검증
- [ ] ultrawork 모드에서 `executor-low` 5개 병렬 → Qwen3-Coder 동시 5개 처리 성공
- [ ] 병렬 완료 후 `architect` 검증 → Opus 호출 확인
- [ ] Qwen3-Coder vLLM `--max-num-seqs 8`로 동시 요청 처리 확인
- [ ] 병렬 처리 시 순차 대비 3배 이상 속도 향상 확인

#### 실행 모드 검증
- [ ] autopilot Phase 0-1 → Opus 100% 사용 확인 (analyst, architect, critic)
- [ ] autopilot Phase 2 → Qwen3 + GLM 혼합 사용 확인 (executor-low, executor)
- [ ] autopilot Phase 4 → Opus 100% 검증 (architect, security-reviewer, code-reviewer)
- [ ] ecomode 활성화 → opus 에이전트가 sonnet(GLM-4.7)으로 라우팅 확인
- [ ] ecomode 활성화 → 승격된 3개 에이전트는 sonnet 유지 확인 (haiku로 강등 안됨)
- [ ] ecomode 활성화 → ecomode의 "haiku 우선 시도" 패턴에서 승격 에이전트가 보호되는지 확인
- [ ] ralph 모드에서 반복 루프 정상 동작 + 매 루프 architect(Opus) 검증 확인

#### GLM-4.7 Concurrency 검증
- [ ] sonnet(GLM-4.7) 에이전트 단일 호출 → 정상 동작 확인
- [ ] sonnet(GLM-4.7) 에이전트 2개 동시 호출 → concurrency 에러 발생 확인
- [ ] ultrawork 모드에서 haiku(Qwen3) 에이전트만 병렬 실행되고, sonnet은 순차 실행되는지 확인

#### MCP 도구 공유 검증 (모델별)
- [ ] Qwen3-Coder(haiku) → filesystem MCP 도구 정상 사용 (작은 파일)
- [ ] Qwen3-Coder(haiku) → `enhancetool` transformer로 tool calling 에러 복구 확인
- [ ] GLM-4.7(sonnet) → context7, tavily MCP 도구 정상 사용
- [ ] GLM-4.7(sonnet) → `cleancache` transformer로 cache_control 제거 정상 동작 확인
- [ ] Opus(think) → 모든 MCP 도구 정상 사용
- [ ] GPT-5.2(longContext) → 대용량 filesystem 읽기 정상 처리

#### Fallback 자동 전환 검증
- [ ] Cognit vLLM 중지 → background 요청이 `zai,glm-4.7`로 자동 폴백 확인
- [ ] Z.AI API 모의 장애 → default 요청이 `anthropic,claude-opus-4-5-20251101`로 자동 폴백 확인

### 11.6 Phase 4 완료 기준 (선택)

- [ ] Nexus에서 DeepSeek-R1-70B vLLM 서빙 성공 (health check 통과)
- [ ] `/model nexus,deepseek-r1-70b` 수동 전환 성공
- [ ] 순수 추론 작업 (수학, 알고리즘) 품질 확인
- [ ] Tool calling 없이 대화형 추론 동작 확인

---

## 12. 참고 자료

### 12.1 공식 문서

**Claude Code**:
- [vLLM - Claude Code Integration](https://docs.vllm.ai/en/latest/serving/integrations/claude_code/)
- [vLLM - Tool Calling](https://docs.vllm.ai/en/latest/features/tool_calling/)
- [Claude Code - Model Configuration](https://code.claude.com/docs/en/model-config)
- [Claude Code - LLM Gateway](https://code.claude.com/docs/en/llm-gateway)
- [Docker Docs - Claude Code Configuration](https://docs.docker.com/ai/sandboxes/claude-code/)
- [Claude Code Development Containers](https://code.claude.com/docs/en/devcontainer)

**라우팅 솔루션**:
- [claude-code-router (GitHub)](https://github.com/musistudio/claude-code-router)
- [LiteLLM - Claude Code Tutorial](https://docs.litellm.ai/docs/tutorials/claude_non_anthropic_models)
- [LiteLLM - vLLM Provider](https://docs.litellm.ai/docs/providers/vllm)

**모델 공식 문서**:
- [Qwen3-Coder 공식 블로그](https://qwenlm.github.io/blog/qwen3-coder/)
- [GLM-4.7 공식 블로그](https://z.ai/blog/glm-4.7)
- [Z.AI GLM Coding Plan - Claude Code 연동](https://docs.z.ai/devpack/tool/claude)
- [Z.AI API 플랫폼](https://open.z.ai)
- [DeepSeek-R1 HuggingFace](https://huggingface.co/deepseek-ai/DeepSeek-R1-Distill-Llama-70B)
- [GPT-5.2 Codex 공식 문서](https://platform.openai.com/docs/models/gpt-5-2-codex)

**Docker & MCP**:
- [Docker MCP Toolkit Documentation](https://docs.docker.com/ai/mcp-catalog-and-toolkit/get-started/)
- [Model Context Protocol Architecture](https://medium.com/@rajkundalia/understanding-model-context-protocol-mcp-beyond-the-hype-582ae84d459d)
- [GitHub - RchGrav/claudebox (Multi-instance Docker)](https://github.com/RchGrav/claudebox)

### 12.2 벤치마크 & 비교

- [GLM-4.7 vs DeepSeek-R1 비교 (Artificial Analysis)](https://artificialanalysis.ai/models/comparisons/glm-4-7-vs-deepseek-r1)
- [SWE-bench Verified Leaderboard](https://www.swebench.com/)
- [LiveCodeBench Leaderboard](https://livecodebench.github.io/leaderboard.html)
- [AIME 2025 Results](https://openai.com/research/aime-2025)

### 12.3 커뮤니티 & 튜토리얼

- [Run Claude Code for Free with Local Models (Towards Data Science)](https://towardsdatascience.com/run-claude-code-for-free-with-local-and-cloud-models-from-ollama/)
- [Claude Code with LiteLLM (Medium)](https://medium.com/@niklas-palm/claude-code-with-litellm-24b3fb115911)
- [Claude Code Usage Guide: Third-Party Models](https://www.kevnu.com/en/posts/claude-code-usage-guide-from-official-configuration-to-integrating-third-party-models)
- [Ollama - Claude Code Integration](https://docs.ollama.com/integrations/claude-code)
- [Docker WireGuard Networking Guide](https://cyberpanel.net/blog/wireguard-docker)
- [LinuxServer WireGuard Docker Docs](https://docs.linuxserver.io/images/docker-wireguard/)

### 12.4 플러그인 & 확장

**oh-my-claudecode**:
- [oh-my-claudecode GitHub](https://github.com/Yeachan-Heo/oh-my-claudecode) — 50에이전트 오케스트레이션 플러그인
- [oh-my-claudecode 공식 문서](https://yeachan-heo.github.io/oh-my-claudecode-website/docs.html)
- [REFERENCE.md (전체 레퍼런스)](https://github.com/Yeachan-Heo/oh-my-claudecode/blob/main/docs/REFERENCE.md)
- [ARCHITECTURE.md (아키텍처)](https://github.com/Yeachan-Heo/oh-my-claudecode/blob/main/docs/ARCHITECTURE.md)

**claude-code-router**:
- [claude-code-router GitHub](https://github.com/musistudio/claude-code-router) — 멀티모델 라우팅 프록시
- [Custom Router 예제](https://github.com/musistudio/claude-code-router/blob/main/custom-router.example.js)

**claude-mem**:
- [claude-mem GitHub](https://github.com/thedotmack/claude-mem) — 영구 메모리 압축 시스템

---

## 13. 플러그인 설치 및 설정 가이드

### 13.1 oh-my-claudecode 설치/설정

#### 개요

oh-my-claudecode(v3.10.3)는 Claude Code에 **50개 전문 에이전트 + 37개 스킬 + 7개 실행 모드 + 31개 훅**을 제공하는 오케스트레이션 플러그인이다. 우리 시스템의 핵심 레이어로, 작업 의도를 감지하여 적절한 에이전트를 선택하고, claude-code-router를 통해 최적의 백엔드 모델로 자동 라우팅한다.

#### 설치

```bash
# Step 1: 마켓플레이스 추가
/plugin marketplace add https://github.com/Yeachan-Heo/oh-my-claudecode

# Step 2: 플러그인 설치
/plugin install oh-my-claudecode
```

**요구사항**:
- Claude Code CLI (최신 버전)
- Node.js 18+
- 인증: Claude Max/Pro 구독 또는 `ANTHROPIC_API_KEY` 환경변수

> ⚠️ npm/bun/curl 직접 설치는 더 이상 지원되지 않음. 반드시 Claude Code 플러그인 시스템 사용.

#### 설정 마법사 (omc-setup)

```bash
/oh-my-claudecode:omc-setup
```

##### 설정 범위 선택

| 범위 | 파일 위치 | 영향 범위 | 권장 |
|------|----------|----------|------|
| **프로젝트별** | `./.claude/CLAUDE.md` | 현재 프로젝트만 | ✅ 안전 |
| **전역** | `~/.claude/CLAUDE.md` | 모든 프로젝트 | ⚠️ 기존 파일 덮어씀 |

**설정 우선순위**: `./.claude/CLAUDE.md` (프로젝트) > `~/.claude/CLAUDE.md` (전역)

##### 설정이 활성화하는 기능

| 기능 | 설정 전 | 설정 후 |
|------|--------|--------|
| 에이전트 위임 | 수동만 | 작업 기반 자동 위임 |
| 키워드 감지 | 비활성 | autopilot, ultrawork, eco 등 |
| 모델 라우팅 | 기본값 | 스마트 3-tier 선택 (haiku/sonnet/opus) |
| 완료 강제 | 없음 | 모든 task 완료 시까지 지속 |
| 스킬 조합 | 없음 | 자동 결합 (ralph = ultrawork + 지속성) |

#### 실행 모드 설정 (.omc-config.json)

```bash
# 위치
~/.claude/.omc-config.json
```

```json
{
  "defaultExecutionMode": "ultrawork"
}
```

| 옵션 | 값 | 설명 |
|------|-----|------|
| `defaultExecutionMode` | `"ultrawork"` | 최대 병렬 처리 (**기본값**) |
| `defaultExecutionMode` | `"ecomode"` | 토큰 효율적 병렬 처리 |

**우리 시스템 권장**: `"ultrawork"` — haiku(Qwen3-Coder) 에이전트 5개 병렬 실행으로 최대 속도. ecomode는 승격 에이전트 보호 이슈 있음 (T14 참조).

#### 에이전트 티어 설정

oh-my-claudecode의 50개 에이전트는 3-tier 구조:

| 티어 | model 파라미터 | 우리 백엔드 | 에이전트 수 |
|------|-------------|-----------|-----------|
| **opus** | `model: opus` | Opus 4.5 (Anthropic) | 16개 |
| **sonnet** | `model: sonnet` | GLM-4.7 (Z.AI) | 20개 (17 + 승격 3) |
| **haiku** | `model: haiku` | Qwen3-Coder (로컬 vLLM) | 14개 (17 - 승격 3) |

**에이전트 파일 수정** (`~/.claude/agents/`):

```yaml
# explore.md — haiku→sonnet 승격 예시
---
name: explore
model: sonnet    # haiku에서 변경 (Qwen3 16K → GLM-4.7 200K)
---
코드베이스 탐색 시스템 프롬프트...
```

**승격 대상 3개**: `explore`, `architecture-analyst`, `test-specialist` (Section 4.7 참조)

#### 핵심 스킬 목록

| 카테고리 | 스킬 | 트리거 | 설명 |
|---------|------|--------|------|
| **실행 모드** | `autopilot` | "build me", "I want a" | 완전 자율 실행 |
| | `ultrawork` | "ulw", "ultrawork" | 최대 병렬 처리 |
| | `ralph` | "ralph", "don't stop" | 완료까지 지속 (ultrawork 포함) |
| | `ecomode` | "eco", "ecomode" | 토큰 절약 모드 |
| | `ultrapilot` | "ultrapilot" | 병렬 autopilot (3-5x 빠름) |
| | `swarm` | "swarm" | N개 에이전트 조율 |
| | `pipeline` | "pipeline" | 순차 체이닝 |
| **검색** | `deepsearch` | "search", "find" | 코드베이스 심층 검색 |
| **분석** | `analyze` | "analyze", "debug" | 심층 분석/디버깅 |
| **계획** | `plan` | "plan this" | 인터뷰 기반 계획 |
| | `ralplan` | "ralplan" | 반복 합의 계획 |
| **유틸** | `cancel` | "cancelomc", "stopomc" | 진행 중 작업 취소 |
| | `doctor` | `/oh-my-claudecode:doctor` | 설치 진단 |
| | `help` | `/oh-my-claudecode:help` | 사용 가이드 |

#### 설치 후 검증

```bash
# 진단 실행
/oh-my-claudecode:doctor
```

**검사 항목**:
- ✅ 종속성 (Node.js, Git, 선택적 tmux/LSP/ast-grep)
- ✅ 설정 파일 (CLAUDE.md 주입 상태)
- ✅ 훅 설치 (31개 라이프사이클 훅)
- ✅ 에이전트 가용성 (50개 에이전트 등록)
- ✅ 스킬 등록 (37개 스킬)
- ✅ 플랫폼 호환성

#### HUD (상태선) 설정

```bash
# HUD 설치
/oh-my-claudecode:hud setup
```

**표시 항목**: 작업 디렉토리, Git 브랜치, 활성 모드, 에이전트 상태, 작업 진행률, 토큰 사용량

**프리셋**: `minimal` | `focused` (권장) | `full` | `analytics` | `opencode`

#### 상태 관리 파일 구조

```
.omc/
├── state/
│   ├── autopilot-state.json     # autopilot 상태
│   ├── ralph-state.json         # ralph 루프 상태
│   ├── ultrawork-state.json     # ultrawork 병렬 상태
│   ├── swarm.db                 # swarm 에이전트 풀
│   └── token-tracking.jsonl     # 토큰 사용 추적
├── notepad.md                   # 압축 방지 메모장
└── logs/
    └── delegation-audit.jsonl   # 위임 감사 로그
```

### 13.2 claude-code-router v2.0.0 기능 레퍼런스

#### 개요

claude-code-router(v2.0.0)는 Claude Code의 API 요청을 가로채서 작업 유형별로 다른 백엔드 모델로 라우팅하는 프록시 서버이다. Fastify/TypeScript 기반, 기본 포트 3456.

#### CLI 명령어 전체

| 명령어 | 설명 | 용도 |
|--------|------|------|
| `ccr start` | 라우터 서버 시작 | 백그라운드 실행 |
| `ccr stop` | 라우터 서버 정지 | 서버 종료 |
| `ccr restart` | 라우터 서버 재시작 | 설정 변경 후 |
| `ccr status` | 서버 상태 확인 | 헬스체크 |
| `ccr code` | 라우터 시작 + Claude Code 실행 | **권장 실행 방법** |
| `ccr model` | 대화형 모델 선택기 | 런타임 모델 전환 |
| `ccr activate` | 환경변수 자동 설정 | `eval "$(ccr activate)"` |
| `ccr ui` | 웹 UI 열기 (포트 3457) | 설정 관리/모니터링 |
| `ccr preset export` | 현재 설정을 프리셋으로 내보내기 | 설정 백업 |
| `ccr preset install` | 프리셋에서 설정 불러오기 | 설정 복원 |
| `ccr preset list` | 설치된 프리셋 목록 | 프리셋 관리 |
| `ccr preset info` | 프리셋 상세 정보 | 프리셋 확인 |
| `ccr preset delete` | 프리셋 삭제 | 정리 |
| `ccr version` | 버전 정보 출력 | 버전 확인 |

#### Custom Router (JavaScript 모듈)

Custom Router는 기본 라우팅 로직을 넘어서는 **고급 라우팅**을 JavaScript 모듈로 구현할 수 있게 한다.

**설정**:
```json
{
  "CUSTOM_ROUTER_PATH": "~/.claude-code-router/custom-router.js"
}
```

**API 인터페이스**:
```javascript
/**
 * @param {object} req - Claude Code 요청 객체
 *   - req.body.messages: 대화 메시지 배열
 *   - req.body: 전체 요청 바디
 * @param {object} config - 앱 설정 객체
 * @returns {Promise<string|null>} - "provider,model" 또는 null (기본 라우팅)
 */
module.exports = async function router(req, config) {
  // 예: 코드 설명 요청은 Opus로
  const userMessage = req.body.messages?.find(m => m.role === "user")?.content;
  if (userMessage?.includes("explain this code")) {
    return "anthropic,claude-opus-4-5-20251101";
  }
  return null;  // null → 기본 시나리오 라우팅으로 폴백
};
```

**우리 시스템 활용 예시**:
```javascript
// health check 기반 동적 라우팅
module.exports = async function router(req, config) {
  // Cognit vLLM 상태 체크
  try {
    const res = await fetch("http://10.5.5.11:8000/health", { signal: AbortSignal.timeout(2000) });
    if (!res.ok) return null;  // 실패 → 기본 라우팅 (fallback 동작)
  } catch {
    // vLLM 다운 → background 요청도 GLM으로 강제
    if (req.body.model?.includes("haiku")) return "zai,glm-4.7";
  }
  return null;
};
```

**활용 시나리오**: 동적 라우팅, A/B 테스트, 로드밸런싱, 비용 최적화, 사용자 티어별 라우팅

#### Preset 시스템

설정을 **프리셋**으로 저장/복원하여 Phase별 빠른 전환 지원.

```bash
# Phase 1 설정 저장 (Opus + Qwen3만)
ccr preset export phase1-opus-qwen --name "Phase 1: Opus + Qwen3" --tags "phase1,minimal"

# Phase 3 설정 저장 (4모델 전체)
ccr preset export phase3-full --name "Phase 3: Full Multi-Model" --tags "phase3,production"

# Phase 전환
ccr preset install phase1-opus-qwen

# 프리셋 목록
ccr preset list
```

**프리셋에 포함되는 내용**: Providers, Router, Transformer, fallback 설정 전체. API 키는 `{{ANTHROPIC_API_KEY}}` 플레이스홀더로 자동 치환 (보안).

**저장 위치**: `~/.claude-code-router/presets/<name>/manifest.json`

#### Subagent Routing (`provider,model` 태그)

서브에이전트 프롬프트의 **시작 부분에 `provider,model`**을 포함하면 해당 모델로 직접 라우팅.

```
# 서브에이전트 프롬프트 예시
zai,glm-4.7 이 파일을 분석하고 리팩토링 제안을 해줘...
```

**라우터 동작**: 프롬프트 첫 줄에서 `provider,model` 패턴 감지 → 해당 모델로 라우팅 → 프롬프트에서 태그 제거 후 모델에 전달

**oh-my-claudecode 연동**: 에이전트별 `.md` 파일의 시스템 프롬프트에 태그를 삽입하면 에이전트-모델 직접 바인딩 가능. 현재는 티어 기반 라우팅(haiku/sonnet/opus)으로 충분하므로 선택사항.

#### Statusline (웹 UI 모니터링)

```bash
ccr ui  # http://127.0.0.1:3457 에서 웹 UI 열기
```

**표시 항목**:

| 모듈 | 아이콘 | 표시 내용 |
|------|--------|----------|
| workDir | 󰉋 | 현재 작업 디렉토리 |
| gitBranch | 🌿 | Git 브랜치명 |
| model | 🤖 | 현재 활성 모델 |
| usage | 📊 | Input → Output 토큰 수 |

**설정** (config.json):
```json
{
  "StatusLine": {
    "enabled": true,
    "currentStyle": "default",
    "fontFamily": "Hack Nerd Font Mono"
  }
}
```

**스타일**: `default` (기본), `powerline` (파워라인). 모듈별 색상, 아이콘 커스터마이징 가능.

#### Image / webSearch 라우팅

**Image 라우팅**: 이미지 관련 작업을 비전 모델로 자동 라우팅
```json
{
  "Router": {
    "image": "gemini,gemini-2.5-flash"
  }
}
```

**webSearch 라우팅**: 웹 검색 도구 호출 시 검색 지원 모델로 라우팅
```json
{
  "Router": {
    "webSearch": "gemini,gemini-2.5-flash"
  }
}
```

> **우리 시스템**: 현재 Image/webSearch 라우팅은 미설정. 필요 시 Gemini 또는 `openrouter,model:online` 형태로 추가 가능.

#### Transformer 파이프라인 전체 (16종)

| # | Transformer | 용도 | 주요 Provider |
|---|-------------|------|-------------|
| 1 | `anthropic` | Anthropic API 직접 연결 (Bearer 인증) | Anthropic |
| 2 | `deepseek` | DeepSeek API 어댑터 | DeepSeek |
| 3 | `gemini` | Google Gemini API 어댑터 | Google |
| 4 | `openrouter` | OpenRouter API 어댑터 (provider 라우팅 지원) | OpenRouter |
| 5 | `groq` | Groq API 어댑터 | Groq |
| 6 | `maxtoken` | 최대 응답 토큰 제한 `["maxtoken", {"max_tokens": N}]` | VRAM 제한 모델 |
| 7 | `tooluse` | Anthropic tool format 변환 + ExitTool 자동 처리 | vLLM, Ollama |
| 8 | `enhancetool` | tool call 파라미터 오류 허용 (안정성 향상, non-streaming) | vLLM, Ollama |
| 9 | `cleancache` | 요청에서 `cache_control` 필드 제거 | 비-Anthropic 전체 |
| 10 | `reasoning` | `reasoning_content` 필드 처리 | DeepSeek-R1 |
| 11 | `sampling` | `temperature`, `top_p`, `top_k`, `repetition_penalty` 처리 | 전체 |
| 12 | `vertex-gemini` | Vertex AI 인증 (Gemini) | Google Cloud |
| 13 | `gemini-cli` | Gemini CLI 실험적 지원 | Google (실험적) |
| 14 | `chutes-glm` | GLM 4.5 모델 지원 (비공식) | Chutes |
| 15 | `qwen-cli` | Qwen3-coder-plus 실험적 지원 | Qwen (실험적) |
| 16 | `rovo-cli` | Atlassian Rovo Dev CLI (GPT-5) 실험적 지원 | Atlassian (실험적) |

**적용 순서**: `use` 배열 순서대로 적용. **순서가 중요하다.**

```json
// 예: Qwen3-Coder용 — tooluse → enhancetool → maxtoken → cleancache 순서
"transformer": {
  "use": [
    "tooluse",
    "enhancetool",
    ["maxtoken", {"max_tokens": 15000}],
    "cleancache"
  ]
}
```

**옵션 전달**: 단순 문자열 `"name"` 또는 배열 `["name", {"option": "value"}]`

#### 라우팅 감지 우선순위 (상세)

```
1. CUSTOM_ROUTER_PATH → Custom Router JS 모듈 (null 반환 시 다음으로)
2. tokenCount > longContextThreshold → longContext
3. 서브에이전트 프롬프트 "provider,model" → Subagent Routing
4. req.body.model에 "claude"+"haiku" → background
5. req.body.tools에 web_search → webSearch
6. req.body 이미지 콘텐츠 감지 → image
7. req.body.thinking 존재 → think
8. 위 조건 모두 불일치 → default
```

### 13.3 claude-mem 영구 메모리 플러그인

#### 개요

claude-mem은 Claude Code를 위한 **영구 메모리 압축 시스템**이다. 세션 중 모든 도구 사용과 관찰 내용을 자동 캡처하여 AI 기반 의미론적 요약본으로 압축하고, 이후 세션에서 관련 컨텍스트를 자동 재주입한다.

**핵심 가치**: 상태 없는(stateless) AI 어시스턴트를 **시간이 지나며 지식을 축적하는 영구적인 개발 파트너**로 변환. 수동 컨텍스트 관리 대비 **~10배 토큰 효율**.

#### 설치

```bash
# Claude Code 터미널에서
/plugin marketplace add thedotmack/claude-mem
/plugin install claude-mem
```

Claude Code 재시작 후 자동 작동. 별도 설정 불필요.

**시스템 요구사항**: Node.js 18+, Bun (자동 설치), SQLite3 (번들), uv (벡터 검색용, 자동 설치)

#### 아키텍처

claude-mem은 3가지 통합 메커니즘으로 Claude Code와 연결된다:

##### A. Lifecycle Hooks (5개)

| 훅 | 시점 | 동작 |
|----|------|------|
| `SessionStart` | 세션 시작 | 이전 메모리 컨텍스트 자동 주입 |
| `UserPromptSubmit` | 사용자 프롬프트 제출 | 프롬프트 관련 메모리 검색 |
| `PostToolUse` | 도구 사용 후 | 관찰 내용 캡처 및 저장 |
| `Stop` | 작업 중단 | 중간 상태 저장 |
| `SessionEnd` | 세션 종료 | 최종 메모리 압축 |

##### B. MCP Tools (4개)

| 도구 | 용도 | 토큰 비용 |
|------|------|----------|
| `search` | 메모리 인덱스 검색 | ~50-100 토큰/결과 |
| `timeline` | 시간순 컨텍스트 조회 | ~100-200 토큰/결과 |
| `get_observations` | ID로 전체 관찰 내용 조회 | ~500-1,000 토큰/결과 |
| `__IMPORTANT` | 워크플로우 문서 (항상 노출) | 최소 |

##### C. Worker Service

- HTTP API 서버: `http://localhost:37777`
- 웹 뷰어 UI: 실시간 메모리 스트림, 검색, 설정 관리
- Bun 프로세스 관리 (자동 시작/재시작)

#### 3-Layer 검색 워크플로우

```
1단계: search(query, type, limit)
       → 간결한 인덱스 반환 (ID 포함, ~50-100 토큰/결과)

2단계: timeline(observation_id)
       → 관심 결과 주변의 시간순 컨텍스트

3단계: get_observations(ids: [123, 456])
       → 필터링된 ID에 대해서만 전체 상세 정보
```

**Progressive Disclosure**: 계층적으로 토큰 비용을 최적화. 1단계에서 대부분 걸러지므로 3단계까지 도달하는 메모리는 소수.

#### 설정

**파일 위치**: `~/.claude-mem/settings.json`

```json
{
  "model": "claude-opus-4-5-20251101",
  "workerPort": 37777,
  "dataDirectory": "~/.claude-mem",
  "logLevel": "info",
  "contextObservations": 50,
  "enableContextInjection": true
}
```

| 설정 | 기본값 | 설명 |
|------|--------|------|
| `model` | `claude-opus-4-5-20251101` | 메모리 압축에 사용할 AI 모델 |
| `workerPort` | `37777` | Worker 서비스 포트 |
| `contextObservations` | `50` | 세션 시작 시 주입할 관찰 수 |
| `enableContextInjection` | `true` | 자동 컨텍스트 주입 활성화 |

**환경변수 튜닝**:
```bash
export CLAUDE_MEM_CONTEXT_OBSERVATIONS=10   # 줄이기 (토큰 절약)
export CLAUDE_MEM_CONTEXT_OBSERVATIONS=100  # 늘리기 (컨텍스트 풍부)
```

#### 저장 방식

```
~/.claude-mem/
├── memory.db          # SQLite 데이터베이스 (세션, 관찰, 요약)
├── settings.json      # 설정 파일
├── chroma/            # Chroma 벡터 데이터베이스 (의미론적 검색)
└── logs/              # 로그 파일
```

- **SQLite**: 구조화된 데이터 저장, FTS5 전문 검색
- **Chroma**: 벡터 임베딩 기반 의미론적 유사도 검색
- **하이브리드 검색**: 키워드(FTS5) + 의미론적(Chroma) 결합

#### 우리 시스템과의 통합 전략

##### claude-mem + claude-code-router + oh-my-claudecode 3중 스택

```
┌─────────────────────────────────────────────────────┐
│  claude-mem (영구 메모리)                              │
│  ├── SessionStart: 이전 프로젝트 지식 자동 주입         │
│  ├── PostToolUse: 모든 에이전트 작업 결과 캡처          │
│  └── SessionEnd: 세션 지식 압축/저장                   │
├─────────────────────────────────────────────────────┤
│  oh-my-claudecode (50개 에이전트 오케스트레이션)         │
│  ├── 작업 의도 감지 → 에이전트 선택                     │
│  └── 티어 기반 라우팅 (opus/sonnet/haiku)              │
├─────────────────────────────────────────────────────┤
│  claude-code-router (멀티모델 라우팅)                   │
│  ├── think → Opus 4.5 🎼 Maestro                     │
│  ├── default → GLM-4.7 🎻 Concertmaster              │
│  ├── background → Qwen3-Coder 🥁 Ensemble            │
│  └── longContext → GPT-5.2 Codex 🎹 Principal        │
├─────────────────────────────────────────────────────┤
│  Claude Code CLI                                      │
└─────────────────────────────────────────────────────┘
```

##### 통합 시 고려사항

| 항목 | 고려 사항 | 권장 대응 |
|------|----------|----------|
| **메모리 모델** | claude-mem의 압축 모델 설정 | 비용 고려하여 `glm-4.7` 또는 `claude-sonnet-4-5` 사용 |
| **토큰 오버헤드** | SessionStart 시 메모리 주입으로 초기 토큰 증가 | `contextObservations: 30`으로 줄여 Qwen3-Coder 16K 부담 최소화 |
| **Qwen3-Coder 호환** | 16K 컨텍스트에서 메모리 주입 + 시스템 프롬프트 = 여유 감소 | background 에이전트에는 메모리 주입 최소화 |
| **oh-my-claudecode 훅 충돌** | 두 플러그인 모두 `SessionStart`, `PostToolUse` 훅 사용 | Claude Code가 훅 순서를 관리하므로 충돌 없음 (플러그인 설치 순서대로 실행) |
| **Worker 포트** | claude-mem(37777) vs claude-code-router(3456) | 포트 충돌 없음, 공존 가능 |

##### 프라이버시 제어

```xml
<!-- 민감한 데이터 저장 방지 -->
<no-store>
API 키: sk-ant-api03-xxxxx
서버 비밀번호: xxx
</no-store>
```

`<no-store>` 태그 안의 내용은 claude-mem 저장소에서 제외.

##### 알려진 이슈 (v9.0.5 기준)

- **빈 CLAUDE.md 파일 생성**: 일부 프로젝트에 빈 `CLAUDE.md` 파일이 자동 생성되는 버그
  - 임시 해결: `.gitignore`에 불필요한 CLAUDE.md 패턴 추가
  - 추후 릴리스에서 수정 예정

### 13.4 MCP 서버 상세 가이드

#### 개요

MCP(Model Context Protocol) 서버는 Claude Code에 외부 도구 기능을 제공한다. **어떤 백엔드 모델(Opus/GLM/GPT/Qwen3)을 사용하든 동일한 MCP 도구에 접근** 가능하다 (Section 4.5 참조).

#### MCP 서버 전체 매트릭스

| # | MCP 서버 | 도구 수 | API 키 | 비용 | 주요 용도 | 업데이트 |
|---|---------|--------|--------|------|----------|---------|
| 1 | **Tavily** | 5 | ✅ `TAVILY_API_KEY` | 무료 1,000/월 | 웹 검색, 추출, 크롤링, 리서치 | 상시 |
| 2 | **Context7** | 2 | ❌ 불필요 | **완전 무료** | 라이브러리 최신 문서/코드 예제 | ~2주 주기 |
| 3 | **Playwright** | 15+ | ❌ 불필요 | 무료 | 브라우저 자동화, 스크린샷, 테스트 | 상시 |
| 4 | **Memory** | 10+ | ❌ 불필요 | 무료 (로컬) | 영구 메모리, 벡터 검색 | 로컬 |
| 5 | **YouTube** | 1 | ❌ 불필요 | 무료 | YouTube 자막 다운로드 | 상시 |
| 6 | **Gemini** | 3 | ✅ (선택) | 무료 티어 | Gemini 모델 직접 호출, 브레인스토밍 | 상시 |

#### Tavily MCP — 웹 검색/추출/리서치

**역할**: 우리 시스템의 **인터넷 접근 창구**. 모든 웹 검색은 Tavily를 통해 수행.

**도구 5개**:

| 도구 | 기능 | 크레딧 소비 | Qwen3 안전성 |
|------|------|-----------|-------------|
| `tavily_search` | 실시간 웹 검색 | 1 (basic) / 2 (advanced) | ⚠️ 결과 크기에 따라 |
| `tavily_extract` | URL에서 구조화된 데이터 추출 | 0.2/URL | ⚠️ 페이지 크기 |
| `tavily_crawl` | 사이트 병렬 크롤링 | 페이지당 과금 | ❌ 결과 대량 |
| `tavily_map` | 사이트 구조 맵 생성 | 페이지당 과금 | ⚠️ 사이트 크기 |
| `tavily_research` | 종합 리서치 (다중 검색+분석) | 다수 크레딧 | ❌ 결과 대량 |

**설치**:
```bash
# 원격 서버 방식 (권장 — 로컬 설치 불필요)
claude mcp add --scope user --transport http tavily \
  "https://mcp.tavily.com/mcp/?tavilyApiKey=${TAVILY_API_KEY}"

# 또는 NPX 로컬 방식
# settings.json에 직접 추가
```

**Claude Code settings.json 설정**:
```json
{
  "mcpServers": {
    "tavily-mcp": {
      "command": "npx",
      "args": ["-y", "tavily-mcp@latest"],
      "env": {
        "TAVILY_API_KEY": "${TAVILY_API_KEY}"
      }
    }
  }
}
```

**비용 관리**:

| 플랜 | 월 크레딧 | 비용 | 권장 |
|------|----------|------|------|
| **Free** | 1,000 | $0 | ✅ 일반 사용 충분 |
| Pay-as-you-go | 무제한 | $0.008/크레딧 | 대량 사용 시 |
| Subscription | 볼륨별 | $0.005~0.0075 | 프로덕션 |

> **월 1,000 크레딧으로 충분한 이유**: 일일 ~33회 검색 가능. 코딩 작업 중 웹 검색은 세션당 5~10회 정도. 크레딧 이월 불가(월말 소멸).

**Qwen3-Coder와의 호환성**:
- `tavily_search` 결과는 보통 500~5K 토큰 → Qwen3에서 **간단한 검색만** 안전
- `tavily_research`, `tavily_crawl` → **GLM-4.7 또는 Opus에서만** 사용 (결과 크기 예측 불가)
- **권장**: 웹 검색이 필요한 작업은 `researcher`(sonnet) 에이전트에 위임

#### Context7 MCP — 라이브러리 최신 문서

**역할**: SDK/프레임워크/라이브러리의 **최신 공식 문서와 코드 예제**를 실시간으로 제공. LLM의 학습 데이터 cutoff 문제를 해결.

**도구 2개**:

| 도구 | 기능 | 사용 순서 |
|------|------|----------|
| `resolve-library-id` | 라이브러리 이름 → Context7 ID 변환 | 1단계 (먼저) |
| `query-docs` | 라이브러리 ID로 최신 문서/코드 조회 | 2단계 (이후) |

**사용 워크플로우**:
```
"React useEffect 최신 사용법"
    ↓
resolve-library-id("react", query="useEffect usage")
    → "/facebook/react"
    ↓
query-docs(libraryId="/facebook/react", query="useEffect cleanup examples")
    → 최신 문서 + 코드 스니펫 반환
```

**설치**:
```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"]
    }
  }
}
```

> **API 키 불필요. 완전 무료. 사용량 제한 없음.**

**핵심 특징**:

| 특징 | 설명 |
|------|------|
| **실시간 최신** | 공식 문서에서 직접 가져옴 (학습 데이터 cutoff 무관) |
| **~2주 주기 업데이트** | 라이브러리 인덱스 정기 갱신 |
| **시맨틱 검색** | 독자적 랭킹 알고리즘으로 관련성 높은 결과 |
| **버전별 문서** | `/org/project/version` 형식으로 특정 버전 조회 가능 |
| **Redis 캐싱** | 동일 쿼리 재요청 시 빠른 응답 |

**Qwen3-Coder와의 호환성**:
- Context7 응답은 **1K~15K 토큰**으로 매우 가변적
- ⚠️ **Qwen3-Coder에서 직접 호출하면 16K 오버플로우 위험**
- **권장**: Context7 조회는 `researcher`(sonnet) 또는 `explore-medium`(sonnet)에서 수행. 결과 요약본을 Qwen3 Task 프롬프트에 포함.

```
❌ 위험:
Task(haiku): "Context7에서 Next.js 라우팅 문서 찾아서 구현해줘"
→ context7 응답 ~10K 토큰 + 시스템 프롬프트 = ⛔ 초과

✅ 안전:
Task(sonnet): "Context7에서 Next.js App Router 문서 조회하여 핵심 패턴 정리"
→ 결과 요약: "App Router는 app/ 디렉토리 사용, layout.tsx + page.tsx 구조..."

Task(haiku): "src/app/users/page.tsx 생성.
  Next.js App Router 규칙: app/ 디렉토리의 page.tsx = 라우트.
  Server Component로 작성. getUserList() 호출하여 유저 목록 표시."
→ 필요한 정보가 프롬프트에 이미 포함 → context7 호출 불필요 → 16K 안전
```

#### MCP 서버 통합 설정 (settings.json)

모든 MCP 서버를 하나의 `~/.claude/settings.json`에서 통합 관리:

```json
{
  "mcpServers": {
    "tavily-mcp": {
      "command": "npx",
      "args": ["-y", "tavily-mcp@latest"],
      "env": {
        "TAVILY_API_KEY": "${TAVILY_API_KEY}"
      }
    },
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"]
    },
    "playwright": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/claude-code-mcp-server-playwright"]
    },
    "memory": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/claude-code-mcp-server-memory"]
    },
    "youtube": {
      "command": "npx",
      "args": ["-y", "youtube-mcp"]
    }
  }
}
```

#### MCP 도구 — 모델별 안전 매핑

> **핵심**: 어떤 MCP 도구를 호출하느냐에 따라 적합한 모델이 달라진다.

| MCP 도구 | 응답 크기 (토큰) | 🥁 Qwen3 | 🎻 GLM | 🎼 Opus | 비고 |
|----------|----------------|---------|--------|---------|------|
| **tavily_search** (basic) | 500~3K | ⚠️ 작은 결과만 | ✅ | ✅ | max_results=3 이하 |
| **tavily_search** (advanced) | 2K~8K | ❌ | ✅ | ✅ | |
| **tavily_extract** | 1K~20K | ❌ | ✅ | ✅ | 페이지 크기 따라 |
| **tavily_crawl** | 5K~50K+ | ❌ | ⚠️ | ✅ | 대량 결과 |
| **tavily_research** | 5K~30K+ | ❌ | ✅ | ✅ | 종합 리서치 |
| **context7 resolve** | ~200 | ✅ | ✅ | ✅ | ID만 반환 |
| **context7 query** | 1K~15K | ❌ | ✅ | ✅ | 문서 크기 가변 |
| **playwright snapshot** | 2K~20K | ❌ | ✅ | ✅ | 페이지 복잡도 |
| **playwright screenshot** | 이미지 | ❌ | ✅ | ✅ | 바이너리 |
| **memory search** | 200~2K | ✅ | ✅ | ✅ | 안전 |
| **Read (파일)** | 500~5K+ | ⚠️ 500줄 이하 | ✅ | ✅ | 파일 크기 |
| **Grep** | 200~5K | ⚠️ 결과 적을 때 | ✅ | ✅ | head_limit 사용 |
| **Edit** | ~200 | ✅ | ✅ | ✅ | 안전 |

**규칙 요약**:
- 🥁 **Qwen3**: Read(작은 파일), Edit, Grep(제한), memory — **응답 예측 가능한 도구만**
- 🎻 **GLM-4.7**: tavily_search, context7, playwright — **중간 크기 응답 도구**
- 🎼 **Opus**: tavily_research, tavily_crawl — **대량 결과 도구 + 분석**
- 🎹 **GPT-5.2**: 60K+ 컨텍스트 누적 시 자동 전환

---

### 13.5 claude-labs 채택 항목 — 스킬 & 통합 기법

> claude-labs v1.8.2에서 분석한 67개 항목(에이전트 19 + 스킬 35 + Constitution 13) 중
> Maestro 시스템에 통합할 가치가 있는 항목을 **ADOPT(5)** / **MERGE(11)** 로 분류.

#### 13.5.1 ADOPT — 완전 채택 스킬 (5개)

##### ① ultra-thin-orchestrate (→ 8.5절에 이미 반영)

- **역할**: 200+ 태스크도 오토 컴팩팅 없이 처리하는 초슬림 오케스트레이션
- **핵심 메커니즘**: `run_in_background` + DONE/FAIL 1줄 프로토콜
- **컨텍스트 절감**: 76% (일반 Task 대비)
- **하위 에이전트**: dependency-resolver (TASKS.md 파싱) + task-executor (자율 실행)
- **Maestro 반영**: 8.5절 "Ultra-Thin 4계층 통신 아키텍처"로 확장 반영 완료

##### ② systematic-debugging — 4단계 근본 원인 분석

```
┌─────────────────────────────────────────────────────────┐
│            Systematic Debugging Pipeline                 │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Phase 1: INVESTIGATE (증거 수집)                        │
│  ├── 에러 메시지/스택 트레이스 수집                       │
│  ├── 코드 흐름 추적 (Grep/Read)                          │
│  └── 환경 정보 확인 (버전, 설정)                          │
│           │                                             │
│  Phase 2: PATTERN (패턴 인식)                            │
│  ├── 비슷한 버그 검색 (git log, 메모리)                   │
│  ├── 영향 범위 파악 (의존성 그래프)                       │
│  └── 재현 조건 식별                                      │
│           │                                             │
│  Phase 3: HYPOTHESIS (가설 수립 & 검증)                  │
│  ├── 최소 3개 가설 수립                                   │
│  ├── 각 가설에 대한 검증 실험 설계                        │
│  └── 실험 실행 → 결과 기반 가설 선택                      │
│           │                                             │
│  Phase 4: IMPLEMENT (수정 & 검증)                        │
│  ├── 근본 원인에 대한 최소 수정                           │
│  ├── 회귀 테스트 실행                                     │
│  └── 수정 후 전체 빌드/테스트 확인                        │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Iron Law**: 근본 원인 미확인 시 수정 금지

**3-Strike 에스컬레이션**:
| 시도 | 행동 |
|------|------|
| 1~3회 | 단순 수정 시도 (🥁 Qwen3-Coder) |
| 4~6회 | 코드 분석 병행 (🎻 GLM-4.7 승격) |
| 7~9회 | systematic-debugging 풀 파이프라인 (🎻 GLM-4.7) |
| 10회 | FAIL 시그널 → 🎼 Opus architect 에스컬레이션 |

**Anti-Rationalization 테이블** (금지 표현):
| 금지 표현 | 대신 해야 할 행동 |
|-----------|-------------------|
| "아마 이게 원인일 거야" | 가설을 세우고 검증 실험 실행 |
| "이건 환경 문제야" | 환경 차이를 구체적으로 확인 |
| "재현이 안 돼" | 재현 조건을 체계적으로 탐색 |
| "다른 곳에서 고쳐야 해" | 영향 범위를 코드로 증명 |
| "테스트가 불안정해서" | flaky test 원인 분석 |
| "시간이 없어서 임시로" | 근본 원인 수정 후 진행 |
| "리팩토링이 필요해서" | 현재 버그와 리팩토링 분리 |
| "이전에도 이랬어" | 이전 발생 이력 조사 후 근본 원인 추적 |

##### ③ guardrails — 코드 생성 전후 안전성 검증

```
┌────────────────────────────────────────────────────┐
│              Guardrails 3-Layer Defense              │
├────────────────────────────────────────────────────┤
│                                                    │
│  Layer 1: INPUT GUARDS (코드 생성 전)               │
│  ├── 위험 패턴 차단:                                │
│  │   rm -rf /, DROP DATABASE, chmod 777,           │
│  │   eval(), exec(), __import__                    │
│  ├── 경고 패턴 감지:                                │
│  │   sudo, force push, --no-verify                 │
│  └── 사용자 확인 요구:                              │
│      파괴적 작업은 반드시 확인 후 실행               │
│                                                    │
│  Layer 2: OUTPUT GUARDS (코드 생성 후)              │
│  ├── SQL Injection 검사 (f-string in query)        │
│  ├── XSS 검사 (innerHTML, dangerouslySetHTML)      │
│  ├── Secret 스캔 (API 키, 비밀번호 하드코딩)        │
│  ├── 경로 조작 검사 (path traversal)                │
│  └── 안전하지 않은 역직렬화 검사                     │
│                                                    │
│  Layer 3: BEHAVIOR GUARDS (실행 중)                 │
│  ├── 파일 시스템 제한 (프로젝트 외부 쓰기 금지)      │
│  ├── 명령어 제한 (허용 목록 기반)                    │
│  └── 네트워크 제한 (알려진 호스트만)                 │
│                                                    │
└────────────────────────────────────────────────────┘
```

**Maestro 통합**: security-specialist 에이전트(🎻 sonnet)와 연동하여 모든 executor 출력에 자동 적용

##### ④ reasoning — CoT/ToT/ReAct 추론 기법

| 기법 | 언제 사용 | 구조 |
|------|----------|------|
| **Chain of Thought (CoT)** | 순차적 논리 문제 | Step 1→2→3→결론 |
| **Tree of Thought (ToT)** | 다중 옵션 비교 | N개 후보 → 가중 평가 → 최적 선택 |
| **ReAct** | 반복 탐색 + 행동 | Thought→Action→Observation→반복 |

**CoT 템플릿** (단순 분석):
```
1. 문제 정의: [구체적 문제]
2. 알려진 사실: [확인된 정보]
3. 추론 단계:
   Step 1: [첫 번째 논리 단계]
   Step 2: [두 번째 논리 단계]
   ...
4. 결론: [도출된 결론]
```

**ToT 템플릿** (아키텍처 결정):
```
후보 A: [방안 A]
  - 장점: [...]  단점: [...]
  - 점수: 성능(0.3) × 8 + 유지보수(0.3) × 7 + 복잡도(0.2) × 6 + 보안(0.2) × 9 = 7.5

후보 B: [방안 B]
  - 장점: [...]  단점: [...]
  - 점수: 성능(0.3) × 6 + 유지보수(0.3) × 9 + 복잡도(0.2) × 8 + 보안(0.2) × 7 = 7.5

→ 동점 시 유지보수 가중치 우선
```

**ReAct 템플릿** (탐색 + 수정):
```
Thought 1: [현재 이해 / 가설]
Action 1: [실행할 도구 호출]
Observation 1: [결과]
Thought 2: [관찰 기반 새로운 이해]
Action 2: [다음 행동]
...반복...
Final: [최종 결론 + 행동]
```

**자동 트리거 규칙**:
| 상황 | 자동 활성화 기법 |
|------|----------------|
| 버그 분석 중 원인 추적 | CoT |
| 아키텍처 방안 비교 | ToT |
| 코드베이스 탐색 + 수정 | ReAct |
| 테스트 실패 원인 분석 | CoT → (실패 시) ReAct |

##### ⑤ reverse — 레거시 코드베이스 역추출

```
┌─────────────────────────────────────────────────┐
│         Reverse Engineering Pipeline             │
├─────────────────────────────────────────────────┤
│                                                 │
│  /reverse scan                                  │
│  ├── 디렉토리 구조 분석                          │
│  ├── 기술 스택 감지 (package.json, pyproject.toml)│
│  └── 코드베이스 규모 측정 (LOC, 모듈 수)          │
│           │                                     │
│  /reverse extract                               │
│  ├── 도메인 리소스 (ORM → resources.yaml)        │
│  ├── API 계약 (Routes → api/*.yaml)             │
│  └── 화면 명세 (Components → screens/*.yaml)     │
│           │                                     │
│  /reverse review                                │
│  ├── 추출 신뢰도 검증 (0.9+: 자동, 0.7~: 리뷰)  │
│  └── 수동 보완 포인트 식별                        │
│           │                                     │
│  /reverse finalize                              │
│  ├── 명세 확정 (_reverse_meta 제거)              │
│  ├── 갭 분석 (누락/불일치/기술부채)               │
│  └── TASKS.md 자동 생성 (→ auto-orchestrate)     │
│                                                 │
└─────────────────────────────────────────────────┘
```

**신뢰도 계산 요소**:
| 요소 | 가중치 | 설명 |
|------|--------|------|
| 타입 어노테이션 | 0.3 | TypeScript, Python 타입 힌트 |
| 테스트 커버리지 | 0.2 | 테스트가 동작 증명 |
| 문서화 | 0.2 | docstring, 주석 |
| 일관된 패턴 | 0.2 | 코드 패턴 일관성 |
| 명시적 계약 | 0.1 | OpenAPI, TypeScript interface |

**Maestro 통합**: explore-high(🎼 Opus)가 scan/extract, architect(🎼 Opus)가 review/finalize 담당

---

#### 13.5.2 MERGE — 기존 시스템에 통합할 기법 (11개)

##### ① TASKS.md 의존성 그래프 + Git Worktree (from auto-orchestrate)

```yaml
# TASKS.md Phase 구조
phases:
  - id: P1
    name: "기반 구축"
    git_worktree: "worktree/p1-foundation"   # Phase별 독립 브랜치
    tasks:
      - id: T1.1
        depends_on: []          # 의존성 없음 → 즉시 실행 가능
      - id: T1.2
        depends_on: [T1.1]     # T1.1 완료 후 실행
      - id: T1.3
        depends_on: [T1.1]     # T1.1과 T1.2 병렬 가능

# dependency-resolver 출력 예시
# READY:T1.1        (즉시)
# READY:T1.2|T1.3   (T1.1 완료 후 병렬)
```

**Git Worktree 규칙**:
- Phase마다 독립 worktree 생성 → 충돌 없는 병렬 작업
- Phase 완료 시 메인 브랜치에 merge
- Qwen3-Coder(🥁)는 worktree 생성 금지 (git 명령 제한) → GLM-4.7(🎻) 이상만

##### ② verification-before-completion (Anti-Rationalization)

**Iron Law**: "수정했습니다", "통과했습니다" 주장 전 반드시 검증 명령 실행 + 출력 확인

```
금지 패턴 → 필수 행동:
"should work"        → 실제 실행하고 결과 확인
"probably fixed"     → 테스트 실행하고 PASS 확인
"seems to pass"      → 빌드 로그 출력 첨부
"I believe it's..."  → 증거(로그, 스크린샷) 제시
"tests are green"    → 실제 테스트 출력 라인 인용
```

모든 에이전트 tier에 적용 (🥁🎻🎼🎹 공통)

##### ③ evaluation — 정량적 품질 메트릭

| 메트릭 | 측정 방법 | 기준 |
|--------|----------|------|
| 테스트 커버리지 | `pytest --cov` / `vitest --coverage` | ≥70% |
| 코드 복잡도 | `radon cc` / ESLint complexity | ≤15 cyclomatic |
| Lint 점수 | `ruff check` / `eslint` | 0 errors |
| 타입 안전성 | `mypy` / `tsc --noEmit` | 0 errors |
| 보안 | `bandit` / `npm audit` | 0 critical/high |

Phase 완료 시 evaluation 스킬이 자동 실행 → 기준 미달 시 Phase 재실행

##### ④ rag — Context7 MCP 자동 트리거

```
자동 트리거 규칙:
- 에이전트가 미지의 라이브러리 API 사용 시 → resolve-library-id → query-docs
- import 문에 새로운 패키지 등장 시 → 자동 문서 조회
- 에러 메시지에 라이브러리명 포함 시 → 해당 라이브러리 문서 검색

적용 에이전트: 🎻 GLM-4.7 이상 (Context7 응답 크기 1K~15K → 🥁 Qwen3 부적합)
```

##### ⑤ deep-research — 멀티 API 병렬 리서치

```
5개 검색 소스 병렬 실행:
├── Tavily Search (일반 웹)
├── Tavily Research (종합 리서치)
├── Context7 (라이브러리 문서)
├── WebSearch (최신 정보)
└── WebFetch (특정 URL 분석)

결과 통합: researcher(🎻 sonnet)가 5개 소스 결과를 종합 → 단일 리포트
```

##### ⑥ PostToolUse 자동 포맷 Hook

```json
// settings.json PostToolUse hook
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Write|Edit",
      "command": "auto-format based on file extension",
      "rules": {
        "*.py": "ruff format --quiet",
        "*.ts|*.tsx|*.js|*.jsx": "prettier --write",
        "*.go": "gofmt -w",
        "*.rs": "rustfmt"
      }
    }]
  }
}
```

Write/Edit 도구 실행 후 자동 포맷팅 → 코드 스타일 일관성 보장

##### ⑦ 구조화된 JSON 분석 스키마 (5종)

| 스키마 | 용도 | 핵심 필드 |
|--------|------|----------|
| `architecture.json` | 코드베이스 구조 분석 | layers, dependencies, patterns |
| `requirements.json` | 요구사항 분석 | functional, non_functional, constraints |
| `system-design.json` | 시스템/컴포넌트 설계 | components, interfaces, data_flow |
| `api-design.json` | API 계약 설계 | endpoints, schemas, auth |
| `impact.json` | 변경 영향도 분석 | affected_files, risk_level, test_plan |

Ultra-Thin 파이프라인에서 `.claude/analysis/*.json`으로 에이전트 간 릴레이

##### ⑧ Constitution 거버넌스 패턴 (MUST/SHOULD/NEVER)

```yaml
# 에이전트 행동 규칙 3단계 계층
governance:
  MUST:    # 반드시 준수 (위반 시 FAIL)
    - "수정 전 근본 원인 확인"
    - "완료 주장 전 검증 실행"
    - "보안 취약점 발견 시 즉시 보고"

  SHOULD:  # 권장 (위반 시 경고)
    - "3개 이상 가설 수립 후 수정"
    - "관련 테스트 추가"
    - "문서 업데이트"

  NEVER:   # 절대 금지 (위반 시 즉시 중단)
    - "사용자 확인 없이 파괴적 작업 실행"
    - "근거 없는 완료 주장"
    - "보안 검사 우회"
```

모든 에이전트 프롬프트에 Constitution 규칙 주입

##### ⑨ frontend-specialist Gemini 하이브리드 패턴

```
Model A (Gemini) → 디자인 코드 생성
     │
     ▼
Model B (Claude) → 통합/TDD/품질 검증

작동 방식:
1. Gemini MCP(mcp__gemini__ask-gemini)로 UI 코드 생성 (디자인 감각 활용)
2. Claude(executor)가 생성된 코드를 프로젝트에 통합
3. test-specialist(🎻)가 TDD 검증
4. security-specialist(🎻)가 보안 검사
```

**Maestro 적용**: frontend-specialist 에이전트가 Gemini MCP를 자동 호출

##### ⑩ test-specialist TDD Iron Law

```
RED → GREEN → REFACTOR (절대 순서 위반 금지)

Iron Law:
1. 실패하는 테스트를 먼저 작성 (RED)
2. 테스트를 통과하는 최소 코드 작성 (GREEN)
3. 코드 품질 개선 (REFACTOR)
4. 테스트 없는 코드 작성 금지

12가지 Anti-Rationalization:
"시간이 없어서"           → 테스트 없이 더 오래 걸림
"너무 간단해서"           → 간단하면 테스트도 간단
"나중에 쓸게"             → '나중에'는 안 옴
"프로토타입이라서"        → 프로토타입이 프로덕션 됨
"프레임워크가 테스트함"    → 당신의 로직은 테스트 안 함
"리팩토링 중이라서"       → 리팩토링에 테스트 필수
"UI는 테스트 어려워서"    → 컴포넌트 테스트 가능
"DB 테스트가 느려서"      → 인메모리 DB 사용
"외부 API라서"            → Mock 사용
"확실히 동작하니까"       → 확신은 버그의 어머니
"리뷰어가 확인할 거야"    → 리뷰어는 테스트 안 씀
"CI에서 돌아가니까"       → CI 실패는 이미 늦음
```

##### ⑪ security-specialist Defense-in-Depth 4계층

```
┌──────────────────────────────────────────┐
│     Defense-in-Depth 4 Layers            │
├──────────────────────────────────────────┤
│                                          │
│  L1: INPUT VALIDATION                    │
│  └── 모든 외부 입력 검증 + 새니타이즈     │
│                                          │
│  L2: AUTHENTICATION & AUTHORIZATION      │
│  └── 인증/인가 로직 검증                  │
│                                          │
│  L3: SECURE CODING                       │
│  └── OWASP Top 10 패턴 검사             │
│                                          │
│  L4: DEPENDENCY AUDIT                    │
│  └── 의존성 취약점 스캔 (npm audit 등)    │
│                                          │
└──────────────────────────────────────────┘
```

---

#### 13.5.3 SKIP 사유 요약

67개 분석 항목 중 **43개(72%) SKIP** — 사유 분류:

| 사유 | 해당 수 | 예시 |
|------|---------|------|
| Maestro에 이미 동등/상위 기능 존재 | 15 | autopilot, ralph, ultrawork, plan, deepsearch |
| claude-labs 프로젝트 전용 (Electron/FastAPI) | 12 | electron-main-specialist, api-handler |
| 🥁 Qwen3-Coder 16K 초과 우려 | 8 | 대형 Constitution, 복잡한 에이전트 프롬프트 |
| 범용성 부족 | 5 | screen-spec, socrates (프로젝트 특화) |
| 기타 | 3 | 중복 기능, 실험적 기능 |

---

#### 13.5.4 채택 항목 구현 태스크 매핑

| 채택 항목 | 구현 태스크 | 난이도 | 우선순위 |
|-----------|------------|--------|---------|
| systematic-debugging | T16: 디버깅 스킬 통합 | 중 | P1 |
| guardrails | T17: 안전성 검증 레이어 구축 | 중 | P1 |
| reasoning (CoT/ToT/ReAct) | T18: 추론 템플릿 에이전트 프롬프트 주입 | 하 | P2 |
| reverse | T19: 역추출 파이프라인 구축 | 상 | P3 |
| TASKS.md 의존성 + Worktree | T5에 통합 (auto-orchestrate 확장) | 중 | P1 |
| verification-before-completion | T20: 전 에이전트 검증 규칙 주입 | 하 | P1 |
| evaluation 메트릭 | T21: Phase 완료 품질 게이트 | 중 | P2 |
| Context7 자동 트리거 | T22: rag 스킬 에이전트 연동 | 하 | P2 |
| PostToolUse 포맷 Hook | T23: settings.json Hook 설정 | 하 | P1 |
| JSON 분석 스키마 | T8에 통합 (Ultra-Thin 파이프라인) | 중 | P1 |
| Constitution 거버넌스 | T24: MUST/SHOULD/NEVER 규칙 체계 | 하 | P2 |
| Gemini 하이브리드 | T25: frontend-specialist Gemini MCP 연동 | 상 | P3 |
| TDD Iron Law | T26: test-specialist TDD 규칙 강화 | 하 | P2 |
| Defense-in-Depth | T27: security-specialist 4계층 검사 | 중 | P2 |

> **신규 태스크**: T16~T27 (12개), 기존 태스크 확장: T5, T8 (2개)
> **Phase 매핑**: P1(즉시) 6개, P2(안정화 후) 5개, P3(확장) 3개
