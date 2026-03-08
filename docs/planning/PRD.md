# PRD: Maestro Claude Code

## 문서 정보

- **프로젝트명**: Maestro Claude Code
- **작성일**: 2026-02-06
- **상태**: Draft v1.0
- **작성자**: Claude (orchestrator)
- **마지막 업데이트**: 2026-02-06

---

## 1. 프로젝트 개요

### 1.1 프로젝트명

**Maestro Claude Code** — 오케스트라 협업 기반 하이브리드 LLM 에이전트 시스템

### 1.2 배경 및 동기

**현재 상황:**
- Claude Code CLI를 100% Anthropic API (Opus 4.5, Sonnet 4.5)로 운영 중
- 월 평균 API 비용: **$630** (Opus $450 + Sonnet $180)
- 50개 전문 에이전트(oh-my-claudecode) 모두 Anthropic 의존
- 비용 대비 활용도: 단순 작업에도 Opus/Sonnet 소비 → 리소스 낭비

**문제점:**
1. **비용 비효율성**: haiku 14개 에이전트 → 단순 파일 조작에도 Sonnet 사용 → 월 $120 불필요 소비
2. **속도 병목**: Anthropic API 동시 요청 제한 (5 req/s) → ultrawork 병렬 실행 시 대기 발생
3. **단일 공급자 의존성**: Anthropic 장애 시 전체 시스템 마비
4. **과잉 품질 투자**: 50% 작업이 단순 반복 (CRUD, 파일 복사, 리포트 생성) → Opus 불필요

**비전:**
> "4개의 전문 LLM이 오케스트라처럼 협업하여, 각 악기가 최적의 악절을 연주하듯, 각 모델이 최적의 작업을 수행하는 하이브리드 에이전트 시스템"

**오케스트라 비유:**
- 🎼 **Maestro (Claude Opus 4.5)** — 지휘자, 전략 수립 및 품질 검증, 10% 사용률
- 🎻 **Concertmaster (GLM-4.7)** — 제1바이올린, 핵심 코드 구현, 35% 사용률
- 🎹 **Principal (GPT-5.2 Codex)** — 수석 연주자, 대규모 컨텍스트 처리, 5% 사용률
- 🥁 **Ensemble (Qwen3-Coder-30B)** — 섹션 단원, 반복 작업 및 배경 실행, 50% 사용률

**목표:**
- 월 API 비용: **$630 → $78** (88% 절감)
- 품질 유지: SWE-bench 73.8%+ (GLM-4.7 기준)
- 속도 향상: Qwen3-Coder 로컬 실행 150+ tok/s → ultrawork 5 병렬 시 ~750 tok/s
- 안정성 강화: 4모델 자동 폴백 → 99%+ 가용성

---

## 2. 목표 및 성공 지표

### 2.1 비즈니스 목표

| 목표 | 현재 | 목표 | 측정 방법 |
|------|------|------|-----------|
| **비용 절감** | $630/월 | $78/월 (88% ↓) | 월별 API 청구서 |
| **처리량 향상** | ~200 tok/s | ~750 tok/s (3.75배) | benchmark 평균 속도 |
| **가용성** | 단일 공급자 99.5% | 4모델 폴백 99.9% | 월별 장애 시간 |
| **품질 유지** | SWE-bench 80.9% (Opus) | 73.8%+ (GLM-4.7) | 주간 E2E 테스트 |

### 2.2 성공 지표 (KPIs)

#### 핵심 지표 (P0)

1. **월 API 비용 ≤ $78**
   - 측정: 월말 Anthropic + Z.AI + OpenAI 청구 합산
   - 기준: 연속 3개월 $78 이하

2. **품질 기준선: SWE-bench 73.8%+**
   - 측정: 주간 20개 샘플 작업 자동 평가
   - 기준: GLM-4.7 에이전트 73.8% 이상 (현재 Opus 80.9% 대비 체감 품질 유지)

3. **ultrawork 병렬 처리량 ≥ 750 tok/s**
   - 측정: 5개 haiku 에이전트 동시 실행 시 aggregate throughput
   - 기준: Qwen3-Coder 로컬 150 tok/s × 5 = 750 tok/s

4. **가용성 99.9%**
   - 측정: 월별 uptime (vLLM + 3 Cloud APIs 폴백)
   - 기준: 월 43.2분 이하 장애

#### 보조 지표 (P1)

5. **Qwen3-Coder 작업 성공률 ≥ 92%**
   - 측정: haiku 에이전트 작업 완료 / 총 할당 작업
   - 기준: 16K 제약 내 92% 완료, 8% GLM-4.7 에스컬레이션

6. **GLM-4.7 에스컬레이션율 ≤ 8%**
   - 측정: Qwen3 → GLM-4.7 에스컬레이션 횟수 / 총 haiku 작업
   - 기준: 16K 오버플로우 8% 이하

7. **평균 응답 시간 (P95) ≤ 3초**
   - 측정: 사용자 요청 → 첫 모델 응답 시간
   - 기준: VPN 지연 포함 3초 이하

### 2.3 비기능 목표

- **유지보수성**: config.json 핫스왑으로 모델 변경 가능
- **확장성**: Phase 4 DeepSeek-R1-70B 선택 추가 시 1일 내 통합
- **보안**: API 키 암호화 저장, guardrails 3-layer defense
- **관측성**: 실시간 모델 라우팅 로그, 비용 대시보드

---

## 3. 사용자 및 이해관계자

### 3.1 주 사용자

**개인 개발자 (hwandam)**
- **역할**: 풀스택 개발자, AI 에이전트 오케스트레이터
- **사용 환경**: Mac (Apple Silicon) + VPN → GPU 서버 클러스터 (Cognit, Nexus)
- **주 작업**: 웹앱 프로토타이핑, API 개발, 데이터 분석, 문서 생성
- **통증점**:
  - 현재 Anthropic API 월 $630 부담
  - ultrawork 병렬 실행 시 Anthropic rate limit 대기
  - 단순 작업에도 Opus/Sonnet 소비 → 과잉 투자

**사용 시나리오:**
1. **autopilot 프로젝트 구축**: "autopilot: FastAPI CRUD 앱 생성"
   - Opus: 아키텍처 설계 (10%)
   - GLM-4.7: 핵심 API 구현 (35%)
   - Qwen3-Coder: 테스트, DB 마이그레이션, 문서 생성 (50%)
   - GPT-5.2: OpenAPI spec 60K 라인 분석 (5%)

2. **ralph 대규모 리팩토링**: "ralph: 20개 파일 타입 안전성 추가"
   - Opus: 리팩토링 전략 수립
   - GLM-4.7: 핵심 비즈니스 로직 변환
   - Qwen3-Coder: 반복 타입 주석 추가 (병렬 20개 파일)

3. **ultrawork 멀티파일 수정**: "ulw: 전체 에러 메시지 한국어 번역"
   - Qwen3-Coder: 50개 파일 동시 번역 (5 병렬 × 10 라운드)

### 3.2 이해관계자

| 역할 | 이해관계 | 관심 지표 |
|------|----------|-----------|
| **시스템 아키텍트 (hwandam)** | 안정성, 확장성 | 가용성 99.9%, Phase 4 확장 가능성 |
| **비용 관리자 (hwandam)** | 예산 절감 | 월 $78 이하, 88% 절감 |
| **품질 관리자 (hwandam)** | 코드 품질 유지 | SWE-bench 73.8%+, Opus 검증 |
| **GPU 서버 관리자 (hwandam)** | 리소스 효율 | vLLM 메모리 32GB 이하, GPU 활용률 80%+ |

---

## 4. 기능 요구사항 (Functional Requirements)

### FR-1: 멀티모델 자동 라우팅

**설명**: claude-code-router가 작업 유형 및 복잡도를 분석하여 최적 모델로 자동 라우팅

**우선순위**: P0 (필수)

**라우팅 규칙:**

| 작업 유형 | 감지 키워드/조건 | 모델 | 이유 |
|-----------|------------------|------|------|
| **think** | "design", "architecture", "strategy" | Opus 4.5 | 전략적 사고, 품질 검증 |
| **default** | 일반 코드 구현 | GLM-4.7 | SWE-bench 73.8%, 비용 효율 |
| **background** | "test", "migrate", "refactor", 파일 조작 | Qwen3-Coder | 로컬 150 tok/s, 무료 |
| **longContext** | 입력 토큰 ≥ 60K | GPT-5.2 Codex | 128K 컨텍스트, OpenAPI 분석 |

**세부 로직:**

1. **컨텍스트 크기 감지** (최우선 조건)
   ```python
   if context_tokens >= 60000:
       return "longContext"  # GPT-5.2
   ```

2. **작업 유형 분류**
   ```python
   if any(keyword in prompt for keyword in ["architecture", "design", "review"]):
       return "think"  # Opus
   elif any(keyword in prompt for keyword in ["test", "migrate", "background"]):
       return "background"  # Qwen3-Coder
   else:
       return "default"  # GLM-4.7
   ```

3. **에이전트 → 모델 매핑**
   ```python
   AGENT_MODEL_MAP = {
       "architect": "think",           # Opus
       "executor": "default",          # GLM-4.7
       "executor-low": "background",   # Qwen3-Coder
       "architect-low": "default",     # GLM-4.7 (haiku → sonnet 승격)
       "explore": "default",           # GLM-4.7 (haiku → sonnet 승격)
       # ... 나머지 50개 에이전트
   }
   ```

**입력:**
- 사용자 프롬프트
- 에이전트 이름
- 현재 컨텍스트 크기

**출력:**
- 선택된 모델 엔드포인트
- 라우팅 사유 (로그)

**예외 처리:**
- 알 수 없는 에이전트 → `default` (GLM-4.7)
- 라우팅 실패 → Opus 폴백

---

### FR-2: 50개 에이전트-모델 매핑

**설명**: oh-my-claudecode 50개 에이전트를 4개 모델에 최적 매핑

**우선순위**: P0 (필수)

**매핑 전략:**

#### 🎼 Maestro (Opus 4.5) — 16개 에이전트

**역할**: 전략 수립, 아키텍처 설계, 최종 품질 검증

| 에이전트 | 작업 예시 | 이유 |
|----------|-----------|------|
| architect | 시스템 설계, 리팩토링 전략 | 깊은 사고 필요 |
| architect-high | 대규모 아키텍처 결정 | 복잡도 최상 |
| planner | 프로젝트 기획, 로드맵 | 전략적 판단 |
| reviewer | 코드 리뷰, 보안 검증 | 품질 기준 엄격 |
| strategist | 비즈니스 로직 설계 | 도메인 지식 |
| analyst | 데이터 분석, 인사이트 도출 | 분석 깊이 |
| designer | UI/UX 설계 전략 | 창의성 |
| writer | 기술 문서 작성 | 표현력 |
| scientist-high | 복잡한 알고리즘 설계 | 수학적 사고 |
| legal-advisor | 라이선스 검토 | 법적 판단 |
| security-expert | 취약점 분석 | 보안 전문성 |
| devops | CI/CD 전략 | 인프라 설계 |
| data-engineer | ETL 파이프라인 설계 | 대규모 데이터 처리 |
| ml-engineer | 모델 아키텍처 설계 | ML 전문성 |
| frontend-architect | 프론트엔드 구조 설계 | SPA 아키텍처 |
| backend-architect | 백엔드 API 설계 | 마이크로서비스 패턴 |

**사용률**: 10% (월 $18, Opus $0.015/1K in + $0.075/1K out)

---

#### 🎻 Concertmaster (GLM-4.7) — 20개 에이전트

**역할**: 핵심 코드 구현, 비즈니스 로직

| 에이전트 | 작업 예시 | 이유 |
|----------|-----------|------|
| executor | 일반 코드 구현 | SWE-bench 73.8% |
| executor-medium | 중복잡도 구현 | 품질 균형 |
| architect-medium | 중규모 설계 | 비용 효율 |
| architect-low | 소규모 설계 (승격) | haiku → sonnet 품질 향상 |
| explore | 코드베이스 분석 (승격) | haiku → sonnet 정확도 |
| explore-medium | 중규모 탐색 | 컨텍스트 이해 |
| debugger | 버그 수정 | 논리 추론 |
| optimizer | 성능 최적화 | 알고리즘 개선 |
| tester | 테스트 코드 작성 (승격) | haiku → sonnet 커버리지 |
| documenter | 코드 주석 추가 | 가독성 |
| refactor | 코드 정리 | 구조 개선 |
| integrator | 외부 API 연동 | 프로토콜 이해 |
| migrator | 데이터 마이그레이션 | 스키마 변환 |
| api-designer | REST API 설계 | OpenAPI spec |
| database-designer | DB 스키마 설계 | 정규화 |
| frontend-developer | React/Vue 구현 | 컴포넌트 로직 |
| backend-developer | FastAPI/Express 구현 | 라우팅 로직 |
| mobile-developer | Flutter/React Native | 모바일 UI |
| devops-engineer | Docker/K8s 설정 | 컨테이너화 |
| qa-engineer | 자동화 테스트 | E2E 시나리오 |

**사용률**: 35% (월 $35, Z.AI API $0.001/1K in + $0.001/1K out)

---

#### 🥁 Ensemble (Qwen3-Coder-30B) — 14개 에이전트

**역할**: 반복 작업, 파일 조작, 배경 실행

| 에이전트 | 작업 예시 | 이유 |
|----------|-----------|------|
| executor-low | 단순 CRUD 생성 | 보일러플레이트 |
| writer-low | 리포트 생성 | 템플릿 작성 |
| tester-low | 단위 테스트 생성 (원래 haiku) | 반복 패턴 |
| documenter-low | README 작성 | 마크다운 |
| refactor-low | 변수명 일괄 변경 | 기계적 작업 |
| migrator-low | SQL 마이그레이션 | 스키마 복사 |
| formatter | 코드 포매팅 | Prettier/Black |
| linter | 린트 에러 수정 | 규칙 기반 |
| translator | 다국어 번역 | 문자열 치환 |
| generator | 코드 생성기 | 템플릿 확장 |
| copier | 파일 복사/이동 | 파일 시스템 |
| renamer | 파일명 일괄 변경 | 배치 작업 |
| deleter | 불필요 코드 제거 | 안전 삭제 |
| indexer | 코드 인덱싱 | 검색 DB 구축 |

**사용률**: 50% (월 $0, 로컬 vLLM 무료)

---

#### 🎹 Principal (GPT-5.2 Codex) — 선택적 사용

**역할**: 대규모 컨텍스트 처리 (60K+ 토큰)

| 상황 | 작업 예시 | 이유 |
|------|-----------|------|
| longContext 자동 전환 | OpenAPI spec 80K 라인 분석 | 128K 컨텍스트 |
| 수동 지정 | 전체 코드베이스 리뷰 | 사용자 명시 |
| Opus 폴백 | Opus 장애 시 대체 | 200K 컨텍스트 |

**사용률**: 5% (월 $25, OpenAI $0.005/1K in + $0.015/1K out)

---

**에이전트 승격 (haiku → sonnet):**

3개 에이전트를 GLM-4.7로 승격하여 품질 향상:
1. **architect-low**: 소규모 설계도 정확도 필요
2. **explore**: 코드베이스 탐색 시 컨텍스트 이해 중요
3. **tester**: 테스트 커버리지 품질 영향 큼

---

### FR-3: Ultra-Thin 4계층 통신 프로토콜

**설명**: 컨텍스트 97% 절감을 위한 최소 통신 프로토콜

**우선순위**: P1 (중요)

**4계층 구조:**

#### Layer 1: Signal (1줄 프로토콜)

**목적**: 에이전트 상태를 1줄 키워드로 전달

**신호 유형:**
- `READY` — 에이전트 초기화 완료
- `WORKING` — 작업 진행 중
- `DONE` — 작업 완료, 결과물 Layer 4 확인
- `FAIL` — 에러 발생, Layer 2 상태 확인
- `ESCALATE` — 상위 모델 요청 (Qwen3 → GLM-4.7 → Opus)

**예시:**
```
executor-low: DONE
```

#### Layer 2: State (orchestrate-state.json)

**목적**: 에이전트 진행 상황 및 메타데이터

**파일 위치**: `.claude/orchestrate-state.json`

**스키마:**
```json
{
  "agents": [
    {
      "id": "executor-low-1",
      "model": "qwen3-coder",
      "status": "DONE",
      "task": "Generate user.py CRUD",
      "startTime": "2026-02-06T10:00:00Z",
      "endTime": "2026-02-06T10:02:30Z",
      "tokensUsed": 1250,
      "artifacts": ["src/user.py"]
    }
  ],
  "totalCost": 0.003,
  "progressPercent": 75
}
```

#### Layer 3: Contract (분석 결과)

**목적**: 구조화된 분석 결과물 (JSON)

**파일 위치**: `.claude/analysis/[agent-id]-contract.json`

**예시**: architect가 생성한 설계 계약서
```json
{
  "architecture": {
    "pattern": "layered",
    "layers": ["controller", "service", "repository"],
    "database": "PostgreSQL",
    "orm": "SQLAlchemy"
  },
  "apiEndpoints": [
    {"method": "GET", "path": "/users", "handler": "UserController.list"}
  ]
}
```

#### Layer 4: Artifact (소스 코드)

**목적**: 실제 작업 결과물 (코드, 문서)

**파일 위치**: 프로젝트 디렉토리 (`src/`, `tests/`)

**예시**: `src/user.py` (executor-low가 생성)

---

**컨텍스트 절감 효과:**

| 통신 방식 | 에이전트 간 전달 내용 | 예상 토큰 |
|-----------|----------------------|-----------|
| **기존 (Full context)** | 전체 대화 이력 + 코드 | ~15,000 tokens |
| **Ultra-Thin** | Signal(1줄) + State(200 tokens) + Contract(500 tokens) | ~700 tokens |
| **절감률** | | **95%** |

---

### FR-4: 4모델 자동 폴백 체인

**설명**: 1차 모델 장애 시 자동으로 대체 모델 전환

**우선순위**: P0 (필수)

**폴백 체인:**

#### 1. GLM-4.7 (default) 장애 → Opus 폴백

**트리거 조건:**
- Z.AI API HTTP 5xx 에러
- 응답 시간 > 30초
- Rate limit 초과 (concurrency=1 위반)

**폴백 로직:**
```python
try:
    response = glm_api.complete(prompt)
except (APIError, Timeout):
    logger.warning("GLM-4.7 down, fallback to Opus")
    response = anthropic_api.complete(prompt, model="opus-4.5")
```

**예상 비용 증가**: 월 $35 → $180 (5배, 단 가용성 99.9% 보장)

---

#### 2. Qwen3-Coder (background) 다운 → GLM-4.7 대행

**트리거 조건:**
- vLLM 서버 unresponsive (ping 실패)
- VPN 단절 (10.5.5.12 unreachable)
- OOM 에러 (GPU 메모리 부족)

**폴백 로직:**
```python
try:
    response = vllm_client.generate(prompt, max_tokens=16000)
except (ConnectionError, TimeoutError):
    logger.warning("Qwen3-Coder down, fallback to GLM-4.7")
    response = glm_api.complete(prompt)
```

**주의사항**:
- GLM-4.7 concurrency=1 → 순차 처리로 전환
- ultrawork 병렬 실행 중단, 순차로 재실행

---

#### 3. GPT-5.2 (longContext) 장애 → Opus 200K 대체

**트리거 조건:**
- OpenAI API HTTP 5xx 에러
- 128K 컨텍스트 초과 에러
- Rate limit 초과

**폴백 로직:**
```python
try:
    response = openai_api.complete(prompt, model="gpt-5.2-codex")
except (APIError, ContextLengthExceeded):
    logger.warning("GPT-5.2 down, fallback to Opus 200K")
    response = anthropic_api.complete(prompt, model="opus-4.5")
```

**Opus 컨텍스트 한계**: 200K → GPT-5.2 128K 커버, 초과 시 청크 분할

---

#### 4. 전체 Cloud API 장애 → 로컬 Qwen3-Coder만 사용

**극단적 상황**:
- Anthropic, Z.AI, OpenAI 모두 장애
- VPN 연결 정상 → Qwen3-Coder만 가동

**제한 사항**:
- 16K 토큰 제한 → 1T1F 원칙 엄격 적용
- 복잡한 작업 불가 → 단순 작업만 처리
- 사용자에게 "제한 모드" 경고

---

**폴백 우선순위 요약:**

```
default(GLM-4.7) 장애
  ↓
  Opus (최고 품질, 비용 5배)

background(Qwen3-Coder) 다운
  ↓
  GLM-4.7 (순차 처리, 속도 50% ↓)

longContext(GPT-5.2) 장애
  ↓
  Opus 200K (128K 커버)

전체 Cloud API 장애
  ↓
  Qwen3-Coder만 (제한 모드)
```

---

### FR-5: MCP 도구 공유 및 안전 매핑

**설명**: 4개 모델이 동일한 MCP 서버를 공유하되, 모델별로 안전한 도구만 노출

**우선순위**: P1 (중요)

**공유 MCP 서버:**

| MCP 서버 | 기능 | 모든 모델 접근 가능 |
|----------|------|-------------------|
| **filesystem** | 파일 읽기/쓰기 | ✅ |
| **git** | Git 명령 실행 | ✅ |
| **memory** | 세션 컨텍스트 저장 | ✅ |
| **playwright** | 브라우저 자동화 | ✅ |
| **context7** | 라이브러리 문서 검색 | ✅ |
| **tavily** | 웹 검색 | ✅ |
| **youtube** | 자막 추출 | ✅ |

---

**모델별 안전 매핑:**

#### Opus 4.5: 전체 도구 접근

**이유**: 최고 품질 모델 → 모든 도구 신뢰 가능

**허용 도구**: 전체 (제한 없음)

---

#### GLM-4.7: 일반 개발 도구

**제한**: 파괴적 작업 금지

**허용 도구**:
- ✅ filesystem: read, write, list
- ✅ git: status, diff, log, add, commit
- ❌ git: reset --hard, push --force, branch -D
- ✅ memory: search, store
- ✅ playwright: navigate, screenshot
- ✅ context7: resolve, query-docs
- ✅ tavily: search, extract

**금지 도구**:
- ❌ filesystem: delete (대량 삭제 위험)
- ❌ git: 파괴적 명령어
- ❌ shell: arbitrary command execution

---

#### Qwen3-Coder: 예측 가능한 도구만

**제한**: 16K 제약 + 안정성 우선

**허용 도구**:
- ✅ filesystem: read (단일 파일 ≤ 500줄), write (단일 파일)
- ✅ git: status, diff (단일 파일)
- ❌ git: commit (다중 파일 금지)
- ✅ memory: search (단순 검색)
- ❌ playwright: (복잡한 브라우저 작업 금지)
- ✅ context7: query-docs (단순 문서 검색)
- ❌ tavily: (웹 검색 결과 컨텍스트 초과 위험)

**이유**:
- Qwen3-Coder 16K 제약 → 응답 예측 가능한 도구만
- playwright 자동화 → 다단계 상호작용 → 컨텍스트 오버플로우 위험
- tavily 검색 → 결과 10개 × 1K tokens = 10K → 안전 한계 초과

---

#### GPT-5.2 Codex: 읽기 전용 분석

**제한**: 대규모 컨텍스트 분석 전용

**허용 도구**:
- ✅ filesystem: read (다중 파일, 100K+ 라인)
- ✅ git: log, diff, blame (전체 히스토리)
- ✅ memory: search (대규모 검색)
- ✅ context7: query-docs
- ✅ tavily: search (대량 검색)
- ❌ filesystem: write (분석 전용, 수정 금지)
- ❌ git: commit, push (읽기 전용)

**이유**: GPT-5.2는 주로 분석 용도 → 수정 작업은 GLM-4.7/Opus 위임

---

**도구 접근 매트릭스:**

| 도구 | Opus | GLM-4.7 | Qwen3 | GPT-5.2 |
|------|------|---------|-------|---------|
| filesystem read | ✅ | ✅ | ✅ (≤500줄) | ✅ |
| filesystem write | ✅ | ✅ | ✅ (1파일) | ❌ |
| filesystem delete | ✅ | ❌ | ❌ | ❌ |
| git commit | ✅ | ✅ | ❌ | ❌ |
| git reset --hard | ✅ | ❌ | ❌ | ❌ |
| playwright | ✅ | ✅ | ❌ | ❌ |
| tavily search | ✅ | ✅ | ❌ | ✅ |
| memory store | ✅ | ✅ | ✅ | ✅ |

---

### FR-6: Docker 재현 가능한 개발 환경

**설명**: 모든 의존성을 포함한 Docker 컨테이너로 환경 통일

**우선순위**: P0 (필수)

**컨테이너 구성:**

```yaml
# docker-compose.yml
version: '3.8'

services:
  claude-code:
    image: maestro-claude-code:latest
    build:
      context: .
      dockerfile: Dockerfile
    volumes:
      - ./workspace:/workspace
      - ./config:/root/.config/claude-code
      - ./.env:/root/.env:ro
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - ZAI_API_KEY=${ZAI_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - TAVILY_API_KEY=${TAVILY_API_KEY}
      - VLLM_ENDPOINT=http://10.5.5.12:8000
    network_mode: host  # VPN 접근 위해 host 네트워크
    working_dir: /workspace
    command: claude-code-router start
```

**Dockerfile:**

```dockerfile
FROM ubuntu:22.04

# 기본 패키지
RUN apt-get update && apt-get install -y \
    curl git build-essential python3.12 python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Node.js 20 설치
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs

# Claude Code CLI 설치
RUN npm install -g @anthropic-ai/claude-code-cli

# claude-code-router 설치
RUN npm install -g claude-code-router@2.0.0

# MCP 서버 설치
RUN npm install -g \
    @modelcontextprotocol/server-filesystem \
    @modelcontextprotocol/server-git \
    @modelcontextprotocol/server-memory

# Python MCP 서버 (playwright, context7)
RUN pip3 install \
    playwright \
    context7-mcp \
    tavily-python

# oh-my-claudecode 설치
RUN curl -fsSL https://raw.githubusercontent.com/oh-my-claudecode/install.sh | bash

WORKDIR /workspace

CMD ["bash"]
```

---

**로컬 개발 vs. Docker 비교:**

| 항목 | 로컬 개발 | Docker |
|------|-----------|--------|
| **Node.js 버전** | v25.5.0 (최신) | v20.x LTS (안정) |
| **Python 버전** | 3.12.5 (pyenv) | 3.12 (시스템) |
| **MCP 서버** | `~/Library/Application Support/Claude/` | `/root/.config/claude-code/` |
| **API 키** | `~/.zshrc` 환경변수 | `.env` 파일 마운트 |
| **vLLM 접근** | VPN (10.5.5.12) | host 네트워크 공유 |
| **재현성** | 낮음 (환경 의존) | 높음 (Dockerfile 고정) |

---

**Docker 사용 시나리오:**

1. **CI/CD 파이프라인**: GitHub Actions에서 동일 환경 테스트
2. **팀 협업**: 다른 개발자와 환경 통일
3. **버전 관리**: Dockerfile Git 추적 → 환경 변화 이력 관리

---

### FR-7: API 키 통합 관리 및 보안

**설명**: 4개 API 키를 단일 `.env` 파일에서 중앙 관리, 보안 규칙 적용

**우선순위**: P0 (필수)

**`.env` 파일 구조:**

```bash
# Anthropic API (Opus 4.5)
ANTHROPIC_API_KEY=sk-ant-xxxxx
ANTHROPIC_BASE_URL=https://api.anthropic.com

# Z.AI API (GLM-4.7)
ZAI_API_KEY=zai-xxxxx
ZAI_BASE_URL=https://api.z.ai/v1

# OpenAI API (GPT-5.2 Codex)
OPENAI_API_KEY=sk-xxxxx
OPENAI_BASE_URL=https://api.openai.com/v1

# Tavily Search API
TAVILY_API_KEY=tvly-xxxxx

# vLLM Endpoint (Qwen3-Coder)
VLLM_ENDPOINT=http://10.5.5.12:8000

# 라우터 설정
ROUTER_LOG_LEVEL=info
ROUTER_COST_TRACKING=true
```

---

**보안 규칙:**

#### 1. 파일 권한

```bash
chmod 600 /Users/hwandam/workspace/maestro-claude-code/.env
```

**이유**: owner만 읽기/쓰기 가능, 다른 사용자/프로세스 접근 금지

---

#### 2. .gitignore 필수 등록

```bash
# .gitignore
.env
.env.*
*.key
credentials.json
```

**검증**:
```bash
git status | grep ".env"  # 출력 없어야 함
```

---

#### 3. 코드 내 하드코딩 금지

**❌ 잘못된 예시:**
```python
api_key = "sk-ant-xxxxx"  # 절대 금지!
```

**✅ 올바른 예시:**
```python
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("ANTHROPIC_API_KEY")

if not api_key:
    raise ValueError("ANTHROPIC_API_KEY not found in .env")
```

---

#### 4. Docker 시크릿 마운트

```yaml
# docker-compose.yml
services:
  claude-code:
    volumes:
      - ./.env:/root/.env:ro  # read-only 마운트
```

**이유**: 컨테이너 내 수정 방지

---

#### 5. 환경별 .env 파일 분리

```bash
.env              # 로컬 개발
.env.production   # 프로덕션 (CI/CD)
.env.test         # 테스트 환경
```

**로드 우선순위**:
```python
from dotenv import load_dotenv

load_dotenv(f".env.{os.getenv('ENV', 'development')}")
```

---

#### 6. API 키 로테이션 (90일마다)

**체크리스트**:
- [ ] Anthropic 대시보드에서 새 키 발급
- [ ] Z.AI 콘솔에서 새 키 발급
- [ ] OpenAI 대시보드에서 새 키 발급
- [ ] Tavily 대시보드에서 새 키 발급
- [ ] .env 파일 업데이트
- [ ] Docker 컨테이너 재시작
- [ ] 구 키 폐기

---

**API 키 노출 시 대응:**

1. **즉시 폐기**: 각 대시보드에서 키 삭제
2. **새 키 발급**: 동일 프로젝트에 새 키 생성
3. **Git 이력 제거** (노출 시):
   ```bash
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch .env" \
     --prune-empty --tag-name-filter cat -- --all
   ```
4. **비용 모니터링**: 노출 키로 과금 발생 여부 확인

---

## 5. 비기능 요구사항 (Non-Functional Requirements)

### NFR-1: 성능

**목표**: 로컬 vLLM 150+ tok/s, ultrawork 5 병렬 시 ~750 tok/s

#### 5.1.1 Qwen3-Coder 단일 요청 성능

**벤치마크 조건**:
- GPU: 2× RTX 3090 (24GB VRAM)
- 모델: Qwen/Qwen3-Coder-30B-Instruct-GPTQ-Int4
- vLLM 버전: v0.15.0
- 입력: 2000 tokens (일반 코드 구현 프롬프트)
- 출력: 500 tokens (생성 코드)

**목표 성능**:
| 지표 | 목표 | 측정 방법 |
|------|------|-----------|
| **처리량** | 150+ tok/s | `benchmark/qwen3_single.py` |
| **지연** | <1초 (TTFT) | Time To First Token |
| **GPU 메모리** | ≤32GB (2× 3090) | nvidia-smi |
| **동시 요청** | 5 병렬 | vLLM engine concurrency |

---

#### 5.1.2 ultrawork 5 병렬 처리량

**시나리오**: 5개 haiku 에이전트 동시 실행 (20개 파일 리팩토링)

**목표**:
| 지표 | 목표 | 이유 |
|------|------|------|
| **Aggregate 처리량** | ~750 tok/s | 150 tok/s × 5 |
| **완료 시간** | 20개 파일 ≤ 5분 | 기존 Sonnet API 15분 대비 3배 빠름 |
| **에스컬레이션율** | ≤8% | 16K 오버플로우 1-2개 파일 |

**벤치마크**:
```bash
python benchmark/ultrawork_parallel.py \
  --agents 5 \
  --tasks 20 \
  --model qwen3-coder
```

**예상 결과**:
```
Total tasks: 20
Parallel agents: 5
Avg throughput: 742 tok/s
Total time: 4m 32s
Escalations: 1 (5%)
```

---

#### 5.1.3 GLM-4.7 API 응답 시간

**목표**: P95 지연 ≤3초 (VPN 포함)

**측정**:
```python
import time
import requests

start = time.time()
response = requests.post(
    "https://api.z.ai/v1/completions",
    headers={"Authorization": f"Bearer {zai_api_key}"},
    json={"model": "glm-4.7", "prompt": "...", "max_tokens": 500}
)
latency = time.time() - start

assert latency < 3.0  # P95 목표
```

**네트워크 분해**:
- Mac → VPN → Internet: ~50ms
- Z.AI API 처리: ~2.5초 (추정)
- VPN → Mac: ~50ms
- **총합**: ~2.6초 (목표 3초 이하)

---

#### 5.1.4 longContext 자동 전환 속도

**목표**: 60K 토큰 감지 → GPT-5.2 전환 ≤5초

**로직**:
```python
def estimate_tokens(text):
    return len(text) / 4  # 대략적 추정

if estimate_tokens(context) >= 60000:
    logger.info("longContext detected, switching to GPT-5.2")
    model = "gpt-5.2-codex"
    # 전환 시간 < 5초 (토큰 카운팅 + 모델 선택)
```

**벤치마크**:
- 100K 텍스트 토큰 카운팅: ~0.5초
- GPT-5.2 첫 API 호출: ~1초 (cold start)
- **총합**: ~1.5초 (목표 5초 이하)

---

### NFR-2: 보안

**목표**: API 키 암호화 저장, guardrails 3-layer defense, OWASP Top 10 자동 검사

#### 5.2.1 API 키 암호화 저장

**방법**: Python `cryptography` 라이브러리 Fernet 대칭 암호화

**구현**:
```python
from cryptography.fernet import Fernet

# 1회성 마스터 키 생성 (초기 설정)
master_key = Fernet.generate_key()
with open(".master.key", "wb") as f:
    f.write(master_key)
os.chmod(".master.key", 0o600)

# API 키 암호화
cipher = Fernet(master_key)
encrypted_api_key = cipher.encrypt(b"sk-ant-xxxxx")

# 암호화된 키 저장
with open(".env.encrypted", "wb") as f:
    f.write(encrypted_api_key)

# 런타임 복호화
with open(".master.key", "rb") as f:
    master_key = f.read()
cipher = Fernet(master_key)
with open(".env.encrypted", "rb") as f:
    api_key = cipher.decrypt(f.read()).decode()
```

**보안 체크리스트**:
- [ ] `.master.key` 파일 권한 600
- [ ] `.master.key` .gitignore 등록
- [ ] `.env.encrypted` Git 추적 가능 (암호화됨)
- [ ] 마스터 키 별도 보관 (1Password 등)

---

#### 5.2.2 Guardrails 3-Layer Defense

**목적**: 악의적 프롬프트 차단, 민감 정보 출력 방지

**3계층 구조**:

##### Layer 1: Input Validation

**검사 항목**:
- 프롬프트 길이 제한: ≤100K 문자
- SQL injection 패턴: `'; DROP TABLE`, `UNION SELECT`
- 명령어 injection: `; rm -rf /`, `| curl`
- API 키 노출: `sk-ant-`, `sk-proj-`

**구현**:
```python
def validate_input(prompt: str) -> bool:
    # 길이 검사
    if len(prompt) > 100000:
        raise ValueError("Prompt too long")

    # SQL injection 패턴
    sql_patterns = [r";\s*DROP\s+TABLE", r"UNION\s+SELECT"]
    for pattern in sql_patterns:
        if re.search(pattern, prompt, re.IGNORECASE):
            raise SecurityError("SQL injection detected")

    # API 키 노출
    if re.search(r"sk-(ant|proj)-[a-zA-Z0-9]{20,}", prompt):
        raise SecurityError("API key in prompt")

    return True
```

---

##### Layer 2: Output Filtering

**검사 항목**:
- API 키 마스킹: `sk-ant-xxxxx` → `sk-ant-***REDACTED***`
- 개인정보 마스킹: 이메일, 전화번호, 주민번호
- 절대 경로 마스킹: `/Users/hwandam/` → `$HOME/`

**구현**:
```python
def filter_output(response: str) -> str:
    # API 키 마스킹
    response = re.sub(
        r"(sk-(ant|proj)-)[a-zA-Z0-9]{20,}",
        r"\1***REDACTED***",
        response
    )

    # 이메일 마스킹
    response = re.sub(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "***EMAIL***",
        response
    )

    # 절대 경로 마스킹
    response = response.replace("/Users/hwandam/", "$HOME/")

    return response
```

---

##### Layer 3: Behavior Monitoring

**목적**: 비정상 행동 패턴 감지

**모니터링 항목**:
| 행동 | 임계값 | 대응 |
|------|--------|------|
| API 호출 급증 | >100 req/min | Rate limiting |
| 대량 파일 읽기 | >50 files/min | 경고 + 로그 |
| Git 파괴적 명령 | `reset --hard`, `push --force` | 차단 + 알림 |
| 외부 네트워크 요청 | curl 비허용 도메인 | 차단 |

**구현**:
```python
class BehaviorMonitor:
    def __init__(self):
        self.api_calls = []
        self.file_reads = []

    def check_rate_limit(self):
        recent_calls = [
            t for t in self.api_calls
            if time.time() - t < 60
        ]
        if len(recent_calls) > 100:
            raise RateLimitError("Too many API calls")

    def check_file_access(self, path: str):
        if path.startswith("/etc/") or path.startswith("/sys/"):
            raise SecurityError("System file access denied")
```

---

#### 5.2.3 OWASP Top 10 자동 검사

**도구**: `bandit` (Python), `semgrep` (다국어)

**CI/CD 통합**:
```yaml
# .github/workflows/security.yml
name: Security Scan

on: [push, pull_request]

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Run Bandit
        run: |
          pip install bandit
          bandit -r src/ -f json -o bandit-report.json

      - name: Run Semgrep
        uses: returntocorp/semgrep-action@v1
        with:
          config: p/owasp-top-ten

      - name: Check vulnerabilities
        run: |
          if jq '.results | length > 0' bandit-report.json; then
            echo "Vulnerabilities found!"
            exit 1
          fi
```

**검사 항목** (OWASP Top 10 2021):
1. A01: Broken Access Control → 권한 검증 누락
2. A02: Cryptographic Failures → 암호화 미사용
3. A03: Injection → SQL/Command injection
4. A07: Identification and Authentication Failures → API 키 하드코딩
5. A08: Software and Data Integrity Failures → 의존성 취약점

---

### NFR-3: 안정성

**목표**: VPN 단절 폴백, vLLM 다운 대행, 에이전트 수명주기 관리

#### 5.3.1 VPN 단절 시 Cloud API 자동 폴백

**감지 로직**:
```python
import socket

def check_vpn_connection():
    try:
        socket.create_connection(("10.5.5.12", 8000), timeout=2)
        return True
    except (socket.timeout, OSError):
        return False

# vLLM 요청 전 VPN 체크
if not check_vpn_connection():
    logger.warning("VPN down, fallback to GLM-4.7 Cloud API")
    model = "glm-4.7"
else:
    model = "qwen3-coder"
```

**폴백 순서**:
1. VPN 3회 재시도 (각 2초 timeout)
2. 실패 시 GLM-4.7 Cloud API 전환
3. VPN 복구 시 자동으로 Qwen3-Coder 재사용

---

#### 5.3.2 vLLM 다운 자동 대행

**헬스체크**:
```python
def check_vllm_health():
    try:
        response = requests.get(
            "http://10.5.5.12:8000/health",
            timeout=5
        )
        return response.status_code == 200
    except requests.RequestException:
        return False

# 주기적 헬스체크 (30초마다)
if not check_vllm_health():
    logger.error("vLLM down, all background tasks → GLM-4.7")
    for agent in background_agents:
        agent.model = "glm-4.7"
```

**자동 복구**:
- vLLM 재시작 감지 → 5분 후 Qwen3-Coder 재활성화
- 복구 확인: 3회 연속 헬스체크 성공

---

#### 5.3.3 에이전트 수명주기 관리

**문제**: 장시간 실행 에이전트 → 컨텍스트 누적 → 메모리 부족

**수명주기 규칙**:

| 모델 | 컨텍스트 한계 | 자동 종료 임계값 | 재시작 방법 |
|------|--------------|----------------|------------|
| Opus 4.5 | 200K | 170K (85%) | 상태 저장 + 새 세션 |
| GLM-4.7 | 128K | 110K (85%) | 상태 저장 + 새 세션 |
| Qwen3-Coder | 16K | 14K (87%) | 에스컬레이션 |
| GPT-5.2 | 128K | 110K (85%) | 청크 분할 |

**구현**:
```python
class AgentLifecycle:
    def __init__(self, agent_id, model, context_limit):
        self.agent_id = agent_id
        self.model = model
        self.context_limit = context_limit
        self.current_context = 0

    def check_context_overflow(self):
        if self.current_context > self.context_limit * 0.85:
            logger.warning(f"{self.agent_id} context 85%, restarting")
            self.save_state()
            self.restart()

    def save_state(self):
        # Ultra-Thin Layer 2: State 저장
        state = {
            "agent_id": self.agent_id,
            "progress": self.get_progress(),
            "artifacts": self.get_artifacts()
        }
        with open(f".claude/state/{self.agent_id}.json", "w") as f:
            json.dump(state, f)

    def restart(self):
        # 새 세션 시작, 이전 상태 로드
        with open(f".claude/state/{self.agent_id}.json") as f:
            state = json.load(f)
        self.restore_state(state)
        self.current_context = 0
```

---

### NFR-4: 확장성

**목표**: Phase 4 DeepSeek-R1-70B 추가 1일 내 통합, config.json 핫스왑, Preset 시스템

#### 5.4.1 Phase 4: DeepSeek-R1-70B 선택적 추가

**요구 사항**:
- GPU: 4× RTX 3090 (96GB VRAM) 또는 2× A6000 (96GB)
- vLLM 버전: v0.15.0+
- 모델 크기: 140GB (INT4 양자화)

**통합 시간 목표**: 1일 (8시간)

**단계별 작업**:
| 단계 | 작업 | 예상 시간 |
|------|------|-----------|
| 1 | 모델 다운로드 + 양자화 | 2시간 |
| 2 | vLLM 서버 설정 (포트 8001) | 1시간 |
| 3 | router config 업데이트 | 30분 |
| 4 | 에이전트 매핑 (scientistHigh → DeepSeek) | 1시간 |
| 5 | 벤치마크 + 검증 | 2시간 |
| 6 | 문서 업데이트 | 1.5시간 |

**router config 변경**:
```json
{
  "models": {
    "deepseek-r1": {
      "endpoint": "http://10.5.5.12:8001/v1/completions",
      "contextWindow": 32000,
      "costPer1kIn": 0,
      "costPer1kOut": 0
    }
  },
  "routing": {
    "reasoning": "deepseek-r1"  // 새 카테고리 추가
  },
  "agentMap": {
    "scientist-high": "reasoning"
  }
}
```

---

#### 5.4.2 config.json 핫스왑

**목적**: 서버 재시작 없이 모델 설정 변경

**구현**:
```python
import json
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ConfigWatcher(FileSystemEventHandler):
    def __init__(self, router):
        self.router = router

    def on_modified(self, event):
        if event.src_path.endswith("config.json"):
            logger.info("Config changed, reloading...")
            self.router.reload_config()

# 파일 감시 시작
observer = Observer()
observer.schedule(
    ConfigWatcher(router),
    path="/root/.config/claude-code/",
    recursive=False
)
observer.start()
```

**핫스왑 가능 항목**:
- ✅ 모델 엔드포인트
- ✅ 에이전트-모델 매핑
- ✅ 라우팅 규칙
- ✅ 비용 추적 설정
- ❌ MCP 서버 (재시작 필요)

---

#### 5.4.3 Preset 시스템

**목적**: Phase별 설정을 빠르게 전환

**Preset 파일 구조**:
```bash
config/
├── preset-phase1.json  # Opus + Qwen3
├── preset-phase2.json  # GLM-4.7 단독
├── preset-phase3.json  # 4모델 통합
├── preset-phase4.json  # + DeepSeek-R1
└── preset-emergency.json  # Opus only (Cloud API 장애 시)
```

**Preset 전환 명령어**:
```bash
# Phase 3으로 전환
claude-code-router preset load phase3

# 긴급 모드 (Opus only)
claude-code-router preset load emergency
```

**Preset 내용 예시** (phase3):
```json
{
  "name": "Phase 3: 4-Model Integration",
  "models": {
    "opus": {...},
    "glm-4.7": {...},
    "qwen3-coder": {...},
    "gpt-5.2": {...}
  },
  "routing": {
    "think": "opus",
    "default": "glm-4.7",
    "background": "qwen3-coder",
    "longContext": "gpt-5.2"
  },
  "agentMap": {...}
}
```

---

## 6. 기술 스택

### 6.1 핵심 컴포넌트

| 계층 | 기술 | 버전 | 역할 |
|------|------|------|------|
| **CLI** | Claude Code CLI | latest | 사용자 인터페이스 |
| **라우터** | claude-code-router | v2.0.0 | 멀티모델 라우팅 |
| **오케스트레이터** | oh-my-claudecode | v3.10.3 | 50개 에이전트 관리 |
| **메모리** | claude-mem | v1.2.0 | 영구 메모리 압축 |
| **컨테이너** | Docker | 24.0+ | 재현 가능 환경 |
| **vLLM** | vLLM | v0.15.0 | 로컬 LLM 서빙 |

---

### 6.2 LLM 모델

#### 6.2.1 Anthropic Claude Opus 4.5

**용도**: Maestro (지휘자), 10% 사용률

**스펙**:
- 컨텍스트: 200K tokens
- SWE-bench: 80.9%
- API: Anthropic API (https://api.anthropic.com)
- 비용: $0.015/1K in, $0.075/1K out

**강점**:
- 전략적 사고, 아키텍처 설계
- 코드 리뷰 정확도 최고
- 복잡한 버그 디버깅

**제약**:
- 비용 최고 (Sonnet 대비 5배)
- API rate limit: 5 req/s

---

#### 6.2.2 Z.AI GLM-4.7

**용도**: Concertmaster (제1바이올린), 35% 사용률

**스펙**:
- 컨텍스트: 128K tokens
- SWE-bench: 73.8%
- API: Z.AI API (https://api.z.ai/v1)
- 비용: $0.001/1K in, $0.001/1K out (Opus 대비 15배 저렴)

**강점**:
- 코드 구현 품질 우수 (Sonnet 4.5와 동등)
- API 안정성 높음
- 비용 효율 탁월

**제약**:
- Concurrency limit = 1 (순차 처리만 가능)
- 창의적 작업은 Opus 대비 약함

---

#### 6.2.3 Qwen/Qwen3-Coder-30B-Instruct-GPTQ-Int4

**용도**: Ensemble (섹션 단원), 50% 사용률

**스펙**:
- 컨텍스트: 16K tokens (최대 제약)
- SWE-bench: ~60% (추정)
- 배포: 로컬 vLLM (Cognit 서버, 2× RTX 3090)
- 비용: $0 (자가 호스팅)

**강점**:
- 로컬 실행 → 무제한 사용
- 150+ tok/s (빠른 속도)
- 반복 작업 자동화 최적

**제약**:
- 16K 제약 → 1T1F 원칙 필수
- 복잡한 추론 약함 → 에스컬레이션 필요
- VPN 의존성

---

#### 6.2.4 OpenAI GPT-5.2 Codex (선택적)

**용도**: Principal (수석 연주자), 5% 사용률

**스펙**:
- 컨텍스트: 128K tokens
- Code generation: 우수
- API: OpenAI API (https://api.openai.com/v1)
- 비용: $0.005/1K in, $0.015/1K out

**강점**:
- 대규모 코드베이스 분석
- OpenAPI spec 60K+ 라인 처리
- Opus 폴백 대체

**제약**:
- 실시간 코드 실행 불가
- Opus 대비 추론 약함

---

### 6.3 GPU 서버 인프라

| 서버 | GPU | VRAM | 역할 | 모델 |
|------|-----|------|------|------|
| **Cognit** | 2× RTX 3080 Ti | 24GB × 2 = 48GB | 주 vLLM 서버 | Qwen3-Coder-30B |
| **Nexus** | 2× RTX 3090 | 24GB × 2 = 48GB | 백업 vLLM + Phase 4 | Qwen3-Coder + DeepSeek-R1 |

**네트워크**:
- Mac → VPN (10.5.5.x) → 서버
- vLLM 포트: 8000 (Qwen3), 8001 (DeepSeek-R1)

---

### 6.4 MCP 서버

| MCP 서버 | 설치 방법 | 용도 |
|----------|-----------|------|
| **filesystem** | `npm install @modelcontextprotocol/server-filesystem` | 파일 읽기/쓰기 |
| **git** | `npm install @modelcontextprotocol/server-git` | Git 명령 |
| **memory** | `npm install @modelcontextprotocol/server-memory` | 세션 컨텍스트 |
| **playwright** | `pip install playwright` | 브라우저 자동화 |
| **context7** | `pip install context7-mcp` | 문서 검색 |
| **tavily** | `pip install tavily-python` | 웹 검색 |
| **youtube** | Built-in | 자막 추출 |

---

## 7. 제약 사항

### C-1: Qwen3-Coder 16K 토큰 제한 (최핵심 제약)

**문제**: Qwen3-Coder는 최대 16K 토큰 컨텍스트 → 복잡한 작업 불가

**영향**:
- 500줄 이상 파일 처리 불가
- 다중 파일 동시 수정 불가
- 도구 호출 3-4회 초과 시 컨텍스트 오버플로우

**대응 전략**: 1T1F 원칙 (One Task, One File)

#### 7.1.1 1T1F 원칙 세부 규칙

**할당 가능 작업**:
- ✅ 단일 파일 생성 (≤500줄)
- ✅ 단일 파일 수정 (변경 범위 ≤200줄)
- ✅ 단위 테스트 생성 (1개 모듈)
- ✅ 문서 생성 (README, 리포트)
- ✅ SQL 마이그레이션 (1개 테이블)

**할당 불가 작업**:
- ❌ 다중 파일 리팩토링 (5개 파일 → 에스컬레이션)
- ❌ 500줄 이상 파일 수정 (GLM-4.7로 재할당)
- ❌ 복잡한 아키텍처 설계 (Opus로 직접 할당)
- ❌ 대규모 데이터 분석 (GPT-5.2 또는 Opus)

---

#### 7.1.2 자동 에스컬레이션

**트리거 조건**:
1. 파일 크기 > 500줄
2. 도구 호출 횟수 > 4회
3. 컨텍스트 사용량 > 14K tokens (87%)
4. 에러 발생 후 재시도 3회 실패

**에스컬레이션 체인**:
```
Qwen3-Coder (haiku) → GLM-4.7 (sonnet) → Opus
```

**구현**:
```python
def execute_agent(agent, task):
    if agent.tier == "haiku":
        # 사전 검증
        if task.file_lines > 500:
            logger.info(f"Task too large for haiku, escalate to sonnet")
            agent = get_agent(tier="sonnet")

        try:
            result = agent.run(task)
        except ContextOverflowError:
            logger.warning("Qwen3-Coder overflow, escalate to GLM-4.7")
            agent = get_agent(tier="sonnet")
            result = agent.run(task)

    return result
```

---

#### 7.1.3 에스컬레이션 성공률 목표

**목표**: 에스컬레이션율 ≤8%

**측정**:
```python
escalation_rate = (escalations / total_haiku_tasks) * 100
assert escalation_rate <= 8.0
```

**최적화 방법**:
1. 작업 분할 정확도 향상 → 1T1F 준수율 95%+
2. 파일 크기 사전 검증 → 500줄 초과 자동 재할당
3. 에이전트 학습 → 실패 패턴 분석 및 재발 방지

---

### C-2: GLM-4.7 Concurrency limit=1

**문제**: Z.AI API는 동시 요청 1개만 허용 (순차 처리 강제)

**영향**:
- ultrawork 병렬 실행 시 sonnet 에이전트 순차 대기
- 20개 sonnet 에이전트 작업 → 순차 20회 → 시간 20배

**대응 전략**:

#### 7.2.1 haiku 에이전트 우선 병렬 실행

**원칙**: ultrawork는 주로 haiku (Qwen3-Coder) 에이전트 병렬 실행

**예시**:
```bash
# 올바른 사용 (병렬 가능)
ulw: 50개 파일 변수명 변경  # executor-low × 5 병렬

# 비효율적 사용 (순차 처리)
ulw: 20개 파일 비즈니스 로직 리팩토링  # executor × 20 순차
```

---

#### 7.2.2 혼합 병렬 전략

**시나리오**: haiku 10개 + sonnet 5개 작업

**전략**:
1. haiku 10개 → 5 병렬 실행 (2 라운드)
2. sonnet 5개 → 순차 실행 (5 라운드)
3. **총 시간**: haiku 2분 + sonnet 10분 = 12분

**기존 (Sonnet API만)**:
- sonnet 15개 → 순차 실행 → 30분

**절감**: 60% 시간 단축

---

#### 7.2.3 GLM-4.7 요청 큐

**구현**: 순차 처리 보장을 위한 요청 큐

```python
import queue
import threading

class GLMRequestQueue:
    def __init__(self):
        self.queue = queue.Queue()
        self.worker = threading.Thread(target=self._process_queue)
        self.worker.start()

    def submit(self, prompt, callback):
        self.queue.put((prompt, callback))

    def _process_queue(self):
        while True:
            prompt, callback = self.queue.get()
            try:
                response = glm_api.complete(prompt)
                callback(response)
            except Exception as e:
                callback(error=e)
            finally:
                self.queue.task_done()

# 사용
glm_queue = GLMRequestQueue()

for task in sonnet_tasks:
    glm_queue.submit(task.prompt, task.on_complete)
```

---

### C-3: 네트워크 의존성

**문제**: Mac → VPN (10.5.5.x) → vLLM 서버 경로 필수

**영향**:
- VPN 단절 시 Qwen3-Coder 접근 불가
- 지연 +5-10ms (VPN 오버헤드)
- 불안정한 Wi-Fi → 간헐적 타임아웃

**대응 전략**:

#### 7.3.1 VPN 헬스체크 + 자동 폴백

**구현**: 앞서 NFR-3.1 참조

**폴백 체인**:
```
VPN 연결 → Qwen3-Coder (로컬)
VPN 단절 → GLM-4.7 (Cloud API)
```

---

#### 7.3.2 Cloud API 우선 모드 (외출 시)

**시나리오**: 외부에서 작업 시 VPN 불안정

**설정**:
```bash
# .env
FORCE_CLOUD_API=true  # Qwen3 비활성화, GLM-4.7만 사용
```

**비용 영향**:
- 월 $78 → $113 (45% 증가, 단 일시적)

---

#### 7.3.3 네트워크 재시도 정책

**설정**:
```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

retry_strategy = Retry(
    total=3,
    status_forcelist=[429, 500, 502, 503, 504],
    backoff_factor=1  # 1s, 2s, 4s
)
adapter = HTTPAdapter(max_retries=retry_strategy)
http = requests.Session()
http.mount("http://", adapter)
http.mount("https://", adapter)

# vLLM 요청
response = http.post(
    "http://10.5.5.12:8000/v1/completions",
    json={"prompt": "...", "max_tokens": 500},
    timeout=30
)
```

---

## 8. 리스크 매트릭스

| # | 리스크 | 확률 | 영향도 | 대응 전략 | 소유자 |
|---|--------|------|--------|----------|--------|
| **R1** | GLM-4.7 API 장애 (Z.AI 서비스 불안정) | 중 (20%) | 높음 (비용 5배) | fallback → Opus 자동 전환, 24시간 내 복구 대기 | hwandam |
| **R2** | Z.AI 서비스 종료 (장기 공급자 리스크) | 낮음 (5%) | 매우 높음 (대체 모델 필요) | Opus 또는 GPT-5.2 장기 대체, DeepSeek-R1 고려 | hwandam |
| **R3** | Qwen3-Coder 16K 오버플로우 빈발 | 높음 (30%) | 중 (에스컬레이션 증가) | 1T1F 작업 분할 정확도 95%+, 파일 크기 사전 검증 | hwandam |
| **R4** | VPN 단절 (Wi-Fi 불안정) | 중 (15%) | 중 (Cloud API 폴백 비용) | 자동 폴백 + 외출 시 Cloud 우선 모드 | hwandam |
| **R5** | Cognit vLLM 서버 다운 (GPU 오류, OOM) | 낮음 (10%) | 중 (GLM-4.7 순차 처리) | Nexus 백업 vLLM + 자동 헬스체크 | hwandam |
| **R6** | Opus API rate limit 초과 (think 작업 급증) | 중 (20%) | 낮음 (일시적 대기) | think 작업 우선순위 큐 + GPT-5.2 분산 | hwandam |
| **R7** | API 키 노출 (Git 실수 커밋) | 낮음 (5%) | 높음 (비용 폭증) | .gitignore 검증 + pre-commit hook + 암호화 저장 | hwandam |
| **R8** | Docker 환경 빌드 실패 (의존성 충돌) | 낮음 (10%) | 중 (로컬 개발 복귀) | Dockerfile 버전 고정 + 주간 빌드 테스트 | hwandam |
| **R9** | Qwen3-Coder 품질 저하 (60% 성공률) | 중 (25%) | 중 (에스컬레이션 증가) | 성공률 모니터링 + 임계값 92% 미만 시 GLM-4.7로 대체 | hwandam |
| **R10** | 월 비용 목표 초과 ($78 → $120) | 중 (20%) | 중 (예산 초과) | 비용 대시보드 + 주간 리뷰 + Opus 사용률 10% 엄격 준수 | hwandam |

---

### 리스크 대응 우선순위

**P0 (즉시 대응 필요)**:
- R2: Z.AI 서비스 종료 → 대체 모델 사전 준비 (DeepSeek-R1 Phase 4 진행)
- R7: API 키 노출 → pre-commit hook 설치 + 암호화 저장

**P1 (1주일 내 대응)**:
- R3: Qwen3 오버플로우 → 1T1F 작업 분할 로직 개선
- R9: Qwen3 품질 저하 → 성공률 모니터링 대시보드 구축

**P2 (1개월 내 대응)**:
- R1: GLM-4.7 장애 → Opus 폴백 테스트 자동화
- R10: 비용 초과 → 비용 추적 대시보드 구축

---

## 9. 구현 Phase 요약

### Phase 0: 환경 준비 (반나절, 4시간)

**목표**: Docker 환경 + API 키 수집

**작업**:
1. [ ] Docker 설치 확인 (`docker --version`)
2. [ ] Dockerfile 작성 (Ubuntu 22.04 + Node.js 20 + Python 3.12)
3. [ ] docker-compose.yml 작성 (네트워크, 볼륨 설정)
4. [ ] API 키 수집:
   - [ ] Anthropic API 키 (https://console.anthropic.com)
   - [ ] Z.AI API 키 (https://z.ai 대시보드)
   - [ ] OpenAI API 키 (https://platform.openai.com)
   - [ ] Tavily API 키 (https://tavily.com)
5. [ ] .env 파일 생성 + 권한 600
6. [ ] .gitignore 검증 (`.env` 포함 확인)
7. [ ] VPN 연결 테스트 (`ping 10.5.5.12`)
8. [ ] vLLM 서버 접근 테스트 (`curl http://10.5.5.12:8000/health`)

**검증**:
```bash
docker-compose up -d
docker exec -it claude-code bash
claude-code --version
```

---

### Phase 1: Opus + Qwen3 기본 라우팅 (반나절, 4시간)

**목표**: 2모델 라우팅 검증 (think → Opus, background → Qwen3)

**작업**:
1. [ ] claude-code-router 설치 (`npm install -g claude-code-router@2.0.0`)
2. [ ] config.json 작성:
   ```json
   {
     "models": {
       "opus": {
         "endpoint": "https://api.anthropic.com",
         "apiKey": "${ANTHROPIC_API_KEY}",
         "model": "claude-opus-4.5"
       },
       "qwen3-coder": {
         "endpoint": "http://10.5.5.12:8000/v1/completions",
         "model": "Qwen3-Coder-30B-Instruct"
       }
     },
     "routing": {
       "think": "opus",
       "background": "qwen3-coder"
     }
   }
   ```
3. [ ] 에이전트 매핑 (16개 opus, 14개 qwen3)
4. [ ] 라우팅 테스트:
   ```bash
   claude-code-router test --prompt "Design API architecture"  # → opus
   claude-code-router test --prompt "Generate CRUD code"  # → qwen3
   ```
5. [ ] Qwen3 16K 제한 테스트 (500줄 파일 에스컬레이션)
6. [ ] VPN 폴백 테스트 (VPN 끊고 Opus 폴백 확인)

**검증**:
- [ ] think 작업 → Opus 응답 (로그 확인)
- [ ] background 작업 → Qwen3 응답 (150+ tok/s)
- [ ] 에스컬레이션 동작 (500줄 파일 → Opus)

---

### Phase 2: GLM-4.7 단독 테스트 (1일, 8시간)

**목표**: GLM-4.7 API 안정성 + 품질 검증

**작업**:
1. [ ] Z.AI API 키 활성화 확인
2. [ ] config.json에 GLM-4.7 추가:
   ```json
   {
     "models": {
       "glm-4.7": {
         "endpoint": "https://api.z.ai/v1/completions",
         "apiKey": "${ZAI_API_KEY}",
         "model": "glm-4.7"
       }
     },
     "routing": {
       "default": "glm-4.7"
     }
   }
   ```
3. [ ] 20개 sonnet 에이전트 → GLM-4.7 매핑
4. [ ] SWE-bench 샘플 20개 테스트 (품질 73.8%+ 확인)
5. [ ] Concurrency=1 제약 테스트 (순차 처리 확인)
6. [ ] 응답 시간 벤치마크 (P95 ≤3초)
7. [ ] Opus 폴백 테스트 (Z.AI 장애 시나리오)

**검증**:
- [ ] SWE-bench 73.8%+ 달성
- [ ] P95 지연 ≤3초
- [ ] 순차 처리 로그 확인 (큐 대기)
- [ ] Opus 폴백 동작 (API 에러 주입)

---

### Phase 3: 4모델 통합 + E2E 검증 (2-3일, 16-24시간)

**목표**: Opus + GLM-4.7 + Qwen3 + GPT-5.2 완전 통합

**작업**:
1. [ ] GPT-5.2 API 키 활성화 확인
2. [ ] config.json 완성 (4모델 전체 설정)
3. [ ] longContext 자동 전환 로직 구현:
   ```python
   if context_tokens >= 60000:
       model = "gpt-5.2"
   ```
4. [ ] Ultra-Thin 4계층 프로토콜 구현:
   - [ ] Layer 1: Signal (READY, DONE, FAIL, ESCALATE)
   - [ ] Layer 2: State (orchestrate-state.json)
   - [ ] Layer 3: Contract (.claude/analysis/*.json)
   - [ ] Layer 4: Artifact (소스 코드)
5. [ ] 50개 에이전트 전체 매핑 검증
6. [ ] 폴백 체인 E2E 테스트:
   - [ ] GLM-4.7 다운 → Opus
   - [ ] Qwen3 다운 → GLM-4.7
   - [ ] GPT-5.2 다운 → Opus 200K
   - [ ] 전체 Cloud API 다운 → Qwen3 제한 모드
7. [ ] MCP 도구 안전 매핑 검증 (모델별 제한)
8. [ ] Guardrails 3-layer defense 통합
9. [ ] 비용 추적 대시보드 구축 (실시간 모니터링)
10. [ ] autopilot 종단간 테스트 (프로젝트 구축 시나리오)

**검증**:
- [ ] autopilot 프로젝트 구축 완료 (FastAPI CRUD 앱)
- [ ] 비용 ≤$78/월 (시뮬레이션)
- [ ] 모든 폴백 체인 동작 확인
- [ ] Ultra-Thin 프로토콜 컨텍스트 97% 절감 확인

---

### Phase 4: DeepSeek-R1-70B 선택 추가 (반나절, 4시간)

**목표**: 고급 추론 작업용 5번째 모델 추가

**작업**:
1. [ ] DeepSeek-R1-70B 모델 다운로드 (140GB INT4)
2. [ ] Nexus 서버에 vLLM 설치 (포트 8001)
3. [ ] vLLM 설정 최적화 (2× RTX 3090, tensor parallelism)
4. [ ] config.json에 DeepSeek-R1 추가:
   ```json
   {
     "models": {
       "deepseek-r1": {
         "endpoint": "http://10.5.5.12:8001/v1/completions",
         "model": "DeepSeek-R1-70B"
       }
     },
     "routing": {
       "reasoning": "deepseek-r1"
     }
   }
   ```
5. [ ] scientist-high 에이전트 → DeepSeek-R1 매핑
6. [ ] 복잡한 알고리즘 설계 테스트 (동적 프로그래밍, 그래프 알고리즘)
7. [ ] 벤치마크 (수학 문제 풀이, 논리 추론)

**검증**:
- [ ] scientist-high 작업 → DeepSeek-R1 라우팅
- [ ] 추론 정확도 Opus 동등 수준 확인
- [ ] 비용 여전히 ≤$78/월 (로컬 실행)

---

## 10. 비용 분석

### 10.1 현재 비용 (Baseline)

**Anthropic API 100% 사용**:

| 모델 | 월 사용량 | 비용/1K in | 비용/1K out | 월 비용 |
|------|-----------|-----------|------------|---------|
| Opus 4.5 | 30M tokens in, 10M tokens out | $0.015 | $0.075 | $450 + $750 = $450 |
| Sonnet 4.5 | 60M tokens in, 20M tokens out | $0.003 | $0.015 | $180 + $300 = $180 |
| **총합** | | | | **$630/월** |

---

### 10.2 목표 비용 (하이브리드)

**4모델 혼합 사용**:

| 모델 | 사용률 | 월 사용량 | 비용/1K | 월 비용 |
|------|--------|-----------|---------|---------|
| **Opus 4.5** | 10% | 9M in, 3M out | $0.015 / $0.075 | $13.5 + $22.5 = $18 |
| **GLM-4.7** | 35% | 31.5M in, 10.5M out | $0.001 / $0.001 | $31.5 + $10.5 = $35 |
| **Qwen3-Coder** | 50% | 45M in, 15M out | $0 (로컬) | $0 |
| **GPT-5.2** | 5% | 4.5M in, 1.5M out | $0.005 / $0.015 | $22.5 + $22.5 = $25 |
| **총합** | 100% | 90M in, 30M out | | **$78/월** |

---

### 10.3 절감 분석

| 항목 | 현재 | 목표 | 절감액 | 절감률 |
|------|------|------|--------|--------|
| 월 비용 | $630 | $78 | $552 | **88%** |
| 연 비용 | $7,560 | $936 | $6,624 | **88%** |

**투자 회수 기간 (ROI)**:
- 초기 투자: $0 (기존 GPU 서버 활용)
- 월 절감액: $552
- ROI: **즉시** (추가 비용 없음)

---

### 10.4 비용 변동 시나리오

#### 10.4.1 최악의 경우 (모든 폴백 발동)

**가정**: GLM-4.7 + Qwen3 완전 장애 → Opus 100% 대체

| 모델 | 사용률 | 월 비용 |
|------|--------|---------|
| Opus 4.5 | 50% (think + default + background) | $315 |
| GPT-5.2 | 5% | $25 |
| **총합** | 55% | **$340/월** |

**절감**: 현재 $630 대비 46% 절감 (여전히 이득)

---

#### 10.4.2 최선의 경우 (모든 로컬 모델 정상)

**가정**: Qwen3 100% 가동 + DeepSeek-R1 추가

| 모델 | 사용률 | 월 비용 |
|------|--------|---------|
| Opus 4.5 | 5% (think만) | $9 |
| GLM-4.7 | 25% | $25 |
| Qwen3-Coder | 60% | $0 |
| DeepSeek-R1 | 5% | $0 |
| GPT-5.2 | 5% | $25 |
| **총합** | 100% | **$59/월** |

**절감**: 현재 $630 대비 91% 절감

---

### 10.5 비용 모니터링 대시보드

**실시간 추적 지표**:
- 시간별 모델 사용률 (파이 차트)
- 누적 월 비용 (목표 $78 대비 진행률)
- 에스컬레이션율 (Qwen3 → GLM-4.7)
- 폴백 발동 횟수

**알림 임계값**:
- 월 비용 $60 초과 시 경고
- 월 비용 $80 초과 시 긴급 알림
- 에스컬레이션율 10% 초과 시 검토

---

## 11. 참고 문서

### 11.1 내부 문서

| 문서명 | 경로 | 설명 |
|--------|------|------|
| **멀티모델-Claude-Code-에이전트-계획서.md** | `docs/` | 4모델 오케스트라 전략 |
| **Nexus-vLLM-벤치마크-계획서.md** | `docs/` | GPU 서버 성능 측정 |
| **[리포트] claude-code-router 분석.md** | `docs/리포트/` | 라우터 아키텍처 상세 |
| **[리포트] oh-my-claudecode 구조 분석.md** | `docs/리포트/` | 50개 에이전트 매핑 |
| **[리포트] OMC 에이전트별 파이프 조사.md** | `docs/리포트/` | 에이전트 작업 유형 분류 |
| **[리포트] 설치 스크립트 분석.md** | `docs/리포트/` | Docker 환경 구성 |
| **[리포트] ultrawork 동작 분석.md** | `docs/리포트/` | 병렬 실행 메커니즘 |

---

### 11.2 외부 문서

| 문서 | URL | 용도 |
|------|-----|------|
| **claude-code-router GitHub** | https://github.com/anthropics/claude-code-router | 라우터 API 레퍼런스 |
| **oh-my-claudecode 공식 문서** | https://ohmyclaudecode.dev | 에이전트 가이드 |
| **vLLM 문서** | https://docs.vllm.ai | vLLM 설정 및 최적화 |
| **Qwen3-Coder 모델 카드** | https://huggingface.co/Qwen/Qwen3-Coder-30B-Instruct | 모델 스펙 |
| **Z.AI API 문서** | https://docs.z.ai | GLM-4.7 API 레퍼런스 |
| **Anthropic API 문서** | https://docs.anthropic.com | Opus 4.5 API 레퍼런스 |
| **OpenAI API 문서** | https://platform.openai.com/docs | GPT-5.2 API 레퍼런스 |

---

### 11.3 관련 표준 및 규격

| 표준 | 버전 | 적용 범위 |
|------|------|-----------|
| **OWASP Top 10** | 2021 | 보안 검사 기준 |
| **Semantic Versioning** | 2.0.0 | 버전 관리 (router, OMC) |
| **Docker Compose Spec** | 3.8 | 컨테이너 오케스트레이션 |
| **JSON Schema** | Draft 2020-12 | config.json 검증 |
| **Markdown Spec** | CommonMark 0.30 | 문서 포맷 |

---

## 12. 변경 이력

| 버전 | 날짜 | 작성자 | 변경 내용 |
|------|------|--------|-----------|
| v1.0 | 2026-02-06 | Claude (orchestrator) | 초안 작성 |

---

## 13. 승인

| 역할 | 이름 | 서명 | 날짜 |
|------|------|------|------|
| **프로젝트 오너** | hwandam | | 2026-02-06 |
| **시스템 아키텍트** | hwandam | | 2026-02-06 |
| **비용 관리자** | hwandam | | 2026-02-06 |

---

**문서 끝**
