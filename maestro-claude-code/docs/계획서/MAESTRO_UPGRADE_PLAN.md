# Maestro Claude Code 고도화 종합계획서

작성자: hwandam77  
작성일: 2026-03-06  
버전: v2.0 (agent-council 통합)

## 목차
1. 개요
2. 목표 및 성공 기준
3. 범위
4. 현재 상태 요약
5. 아키텍처 설계
6. 통합 대상 및 호환성
7. 단계별 작업 계획
8. 검증 및 테스트
9. 롤아웃 전략
10. 리스크 및 대응
11. 인력·자원·권한
12. 산출물 체크리스트
13. 일정
14. 권장 우선순위
15. 다음 단계

---

## 1. 개요

본 문서는 `Maestro Claude Code` 프로젝트(이하 '본 시스템')에 다음 세 가지 핵심 리소스를 통합하여 고도화하는 종합 계획서이다:

### 통합 대상 리소스
1. **Spacebot** (spacedriveapp/spacebot) - Rust 기반 멀티 에이전트 철학
   - Branch/Worker/Compactor/Cortex 아키텍처
   - 멀티유저 지원 (Discord/Slack/Telegram/Twitch)
   - 타입드 메모리 시스템 (SQLite + LanceDB)

2. **claude-imple-skills** (insightflo/claude-imple-skills) - 워크플로·검증 스킬 패키지
   - 20개 스킬, 10개 에이전트, 17개 훅
   - 프로젝트 팀 시스템 (PM, Architect, Designer, QA, DBA 등)
   - Long Context 최적화 (H2O, Compressive Context)

3. **agent-council** (team-attention/agent-council) - 다중 AI 협업 시스템 ⭐ NEW
   - 여러 AI CLI (Claude, Codex, Gemini) 의견 수렴
   - Karpathy의 LLM Council에서 영감을 받음
   - 추가 API 비용 없음 (설치된 CLI 활용)
   - 3단계 프로세스: Opinions → Collection → Synthesis

### 핵심 접근 방식
- **Spacebot 철학 재해석**: Rust 기반을 Node.js 환경에 맞게 적응
- **스킬 시스템 포팅**: Claude 전용 → Opus/Qwen3.5 맞게 변환
- **다중 AI 협업**: Council 시스템으로 다양한 관점 확보

---

## 2. 목표 및 성공 기준

### 목표 1: 역할 분담 자동화
**Opus(설계, Maestro)와 Qwen3.5-122B(코딩, Soloist)의 역할 분담 자동화**
- 성공 기준:
  - `@architect` 요청 → Opus/Claude 라우팅
  - `@coder`/`@file-manager` 요청 → Qwen3.5-122B 라우팅;
  - 샘플 시나리오 3종 이상 E2E 통과

### 목표 2: 자동 검증 파이프라인
**파일 편집 전후의 자동 훅(보안·품질) 적용**
- 성공 기준:
  - `pre-edit-impact-check`, `security-scan` 훅 동작;
  - 훅 테스트 10건 통과;
  - 보안 취약점 자동 탐지율 > 90%.

### 목표 3: 컨텍스트 최적화
**장기 컨텍스트 최적화(Compress)로 토큰 비용 절감**
- 성공 기준:
  - 시뮬레이션(>50k 토큰)에서 `compress` 동작;
  - 토큰 소비 평균 30% 이상 절감;
  - 컨텍스트 품질 유지 (정보 손실 < 10%).

### 목표 4: 다중 AI 협업 (Council) ⭐ NEW
**여러 AI 모델의 의견을 수렴하여 합의 도출**
- 성공 기준:
  - 3개 이상 모델이 참여하는 council 정상 작동;
  - Chairman(Opus)가 종합 결론 도출;
  - Council 시나리오 3종 이상 통과 (아키텍처 설계, 기술 선택, 코드 리뷰).

---

## 3. 범위

### 포함 항목
1. **스킬 시스템 통합**
   - `claude-imple-skills`의 핵심 스킬 8개 통합
   - `/workflow`, `/orchestrate-standalone`, `/compress`, `/agile`, `/tasks-init`, `/impact`, `/security-review`, `/quality-auditor`

2. **다중 AI 협업 (Council) 시스템** ⭐ NEW
   - `agent-council` 통합
   - Council 멤버: Opus, GLM-4.7, Qwen3.5-122B, GPT-5.2
   - 3단계 프로세스: Opinions → Collection → Synthesis
   - Chairman: Opus (기본) 또는 사용자 지정

3. **아키텍처 확장**
   - `config/config.json`에 `contextStrategies`, `council` 섹션 추가
   - `config/custom-router.js`에 skill→agent 매핑 및 Branch/Worker spawn 로직
   - `config/council.config.yaml` 생성 (멤버 설정).

4. **훅 시스템**
   - 파일 편집 훅(사전·사후) 17개 구현
   - 훅 래퍼(미들웨어) 구현.
   - 보안·품질·아키텍처 자동 검증.

5. **컨텍스트 관리**
   - `compress` 스킬을 이용한 longContext 자동화.
   - 역할별 컨텍스트 분리 (architect/coder/haiku).
   - H2O (Heavy-Hitter Oracle) 패턴 적용.

6. **모니터링 시스템**
   - 에이전트 헬스 체크.
   - 작업 큐 모니터링.
   - Council 진행 상황 추적.

### 제외 항목
- 시스템 전체를 Rust로 전환 (대규모 리라이팅).
- 외부 CLI(예: gemini, codex) 강제 의존 — 옵션으로만 사용.
- 실시간 멀티유저 지원 (Spacebot의 Discord/Slack 연동) — Phase C 에서 검토.

---

## 4. 현재 상태 요약

### 완료된 작업
- ✅ `config/config.json`에 vllm-qwen35 provider 항목 추가.
- ✅ `config/custom-router.js`에 `soloist` 티어 정의 및 에이전트 매핑.
- ✅ `.env`에 Qwen3.5 관련 환경변수 설정.
- ✅ README에 5-Model Orchestra 설명 추가.

### 진행 중인 작업
- 🔄 GitHub 동기화 (로컬 푸시 대기 중).
- 🔄 계획서 문서화 (본 문서).

### 대기 중인 작업
- ⏳ `claude-imple-skills` 통합.
- ⏳ `agent-council` 통합.
- ⏳ 훅 시스템 구현.
- ⏳ Council 시스템 구현.

---

## 5. 아키텍처 설계

### 5.1 핵심 아키텍처 (Spacebot 철학 재해석)

#### Channel (사용자 인터페이스)
- **역할**: 사용자 대화 담당 (Opus/Claude).
- **책임**: 요청 수신, 응답 생성, Branch/Worker 관리.
- **특징**: 항상 응답 가능 (블로킹 없음).

#### Branch (독립 사고)
- **역할**: Opus가 별도 작업(독립 사고)을 생성하는 논리 단위.
- **책임**: 독립적인 분석, 계획 수립, Worker 호출.
- **특징**: 비동기 작업 ID 발행, 상태 추적 가능.

#### Worker (작업 실행)
- **역할**: Qwen3.5-122B 기반 역할별 작업자.
- **유형**:
  - `coder`: 코드 작성 및 수정.
  - `file-manager`: 파일 시스템 작업.
  - `debugger`: 에러 분석 및 수정.
  - `tester`: 테스트 코드 작성.
- **특징**: 작업 전용 시스템 프롬프트, 도구 제한.

#### Compactor (컨텍스트 관리)
- **역할**: 오래된 컨텍스트 요약.
- **도구**: `compress` 스킬.
- **트리거**: 임계값(80%/85%/95%) 또는 주기적 실행.
- **특징**: 비동기 실행, Channel 블로킹 없음.

#### Cortex (시스템 감독)
- **역할**: 라우터 수준 경량 모니터.
- **책임**: 헬스 체크, 큐 길이, 실패율 수집, Council 진행 상황 추적.
- **특징**: 모든 에이전트 상태 통합 관리.

### 5.2 다중 AI 협업 (Council) 아키텍처 ⭐ NEW

#### Council 구조
```
┌─────────────────────────────────────────┐
│         Chairman (Opus/Claude)           │
│  - 의견 종합                              │
│  - 최종 결론 도출                         │
│  - 합의 규칙 적용                         │
└─────────────────────────────────────────┘
            ↓ Synthesis
┌─────────────────────────────────────────┐
│      Council Members (다양한 모델)       │
│  - Opus (Claude): 설계 관점              │
│  - GLM-4.7: 비용 효율적 구현 관점        │
│  - Qwen3.5-122B: 코딩 전문 관점          │
│  - GPT-5.2: 대규모 컨텍스트 관점         │
└─────────────────────────────────────────┘
```

#### Council 프로세스 (3단계)
1. **Stage 1: Initial Opinions**
   - 각 Council Member가 독립적으로 의견 제시.
   - 병렬 실행 (동시성 보장).
   - 타임아웃: 각 멤버 30초.

2. **Stage 2: Response Collection**
   - 각 멤버의 응답 수집.
   - 포맷팅 및 구조화.
   - 중복 의견 식별.

3. **Stage 3: Chairman Synthesis**
   - Chairman(Opus)가 모든 의견 종합.
   - 최종 추천 도출.
   - 합의 규칙 적용 (다수결 vs 전문가 의견).

#### Council 활용 시나리오
- **아키텍처 설계**: Opus + GLM-4.7 + GPT-5.2 의견 수렴.
- **기술 선택**: React vs Vue 등 다양한 관점 확보.
- **코드 품질 검토**: 여러 모델의 교차 검증.
- **성능 최적화**: 각 모델의 전문 분야 활용.

### 5.3 데이터 흐름

```
사용자 요청
    ↓
custom-router.js (에이전트/스킬 감지)
    ↓
┌─────────────┬─────────────┬─────────────┐
│   Opus      │   Council   │   Worker    │
│  (설계)     │  (협업)     │  (실행)     │
└─────────────┴─────────────┴─────────────┘
    ↓              ↓              ↓
  Branch      Chairman        Qwen3.5
    ↓         Synthesis         ↓
  Worker      ↓              File Edit
    ↓      Final Decision      ↓
 Hooks ← ← ← ← ← ← ← ← ← ← ← Hooks
    ↓                         ↓
Compactor                  Compactor
```

---

## 6. 통합 대상 및 호환성

### 6.1 claude-imple-skills 통합

#### 통합 스킬 (8개)
1. `/workflow` - 메타 허브 (상태 분석, 다음 스킬 추천).
2. `/orchestrate-standalone` - 대규모 오케스트레이션 (50-200 tasks).
3. `/compress` - Long Context 최적화 (H2O 패턴).
4. `/agile` - 레이어드 스프린트 (Skeleton → Muscles → Skin).
5. `/tasks-init` - TASKS.md 생성.
6. `/impact` - 변경 영향도 분석.
7. `/security-review` - OWASP TOP 10, CVE, secrets 탐지.
8. `/quality-auditor` - 배포 전 종합 감사.

#### 통합 훅 (17개)
**Permission (2개)**:
- `permission-checker` - 권한 검증.
- `domain-boundary-enforcer` - 도메인 경계 강제.

**Safety (3개)**:
- `pre-edit-impact-check` - 편집 전 영향도 분석.
- `risk-area-warning` - 위험 영역 경고.
- `security-scan` - 보안 스캔.

**Quality (4개)**:
- `standards-validator` - 코딩 표준 검증.
- `design-validator` - 디자인 시스템 일관성.
- `interface-validator` - 인터페이스 호환성.
- `quality-gate` - 품질 게이트.

**Gates (4개)**:
- `policy-gate` - 정책 준수.
- `contract-gate` - 계약 준수.
- `risk-gate` - 위험 관리.
- `docs-gate` - 문서화 완료.

**Sync (4개)**:
- `architecture-updater` - 아키텍처 업데이트.
- `changelog-recorder` - 변경 이력 기록.
- `cross-domain-notifier` - 도메인 간 알림.
- `task-sync` - 작업 동기화.

#### 호환성 고려사항
- **프롬프트 포팅**: Claude 전용 → Opus/Qwen3.5 맞게 변환.
- **외부 도구 의존**: 일부 스킬이 외부 툴에 의존 → 옵션화 또는 대체 구현.
- **훅 정책**: 파일 편집 파이프라인에 연결, 정책(경고/차단) 설정.

### 6.2 agent-council 통합 ⭐ NEW

#### 통합 내용
- **Council 멤버**: Opus, GLM-4.7, Qwen3.5-122B, GPT-5.2.
- **Chairman**: Opus (기본) 또는 사용자 지정.
- **합의 프로세스**: 3단계 (Opinions → Collection → Synthesis).
- **활용 시나리오**: 아키텍처 설계, 기술 선택, 코드 리뷰, 품질 검증.

#### 호환성 고려사항
- **응답 속도 차이**: 각 모델의 응답 시간 다름 → 타임아웃 설정 (30초).
- **비용 관리**: 다중 모델 호출 → 선택적 활성화 (중요한 결정에만).
- **의견 충돌**: 모델 간 의견 불일치 → Chairman이 명확한 합의 규칙 적용.

#### Council 설정 파일
```yaml
# config/council.config.yaml
council:
  chairman:
    model: opus
    role: synthesis
    
  members:
    - id: opus
      model: claude-opus-4.5
      role: architecture
      timeout: 30
      
    - id: glm
      model: glm-4.7
      role: implementation
      timeout: 30
      
    - id: qwen
      model: qwen3.5-122b
      role: coding
      timeout: 30
      
    - id: gpt
      model: gpt-5.2-codex
      role: longcontext
      timeout: 30
  
  synthesis:
    strategy: weighted_consensus  # 다수결 vs 전문가 의견
    timeout: 60
```

### 6.3 Spacebot 철학 적용

#### 적용 내용
- **Branch/Worker 패턴**: Node.js 환경에 맞게 적응.
- **Compactor**: `compress` 스킬로 구현.
- **Cortex**: 경량 모니터링 시스템.
- **타입드 메모리**: SQLite + JSON 스키마 (간소화).

#### 호환성 고려사항
- **Rust → Node.js**: 프로세스 기반 → 이벤트 루프 기반.
- **실시간 DB**: SQLite/LanceDB → 파일 기반 + 메모리 캐시.
- **멀티유저**: 단일 사용자 → 향후 확장 (Phase C).

---

## 7. 단계별 작업 계획

### Phase A — 안전 통합 & 빠른 가치 실현 (1–3일)

#### 목표
`claude-imple-skills`와 `agent-council`을 안전하게 레포지토리에 추가하고 핵심 스킬을 즉시 활용 가능하게 설정.

#### 작업 항목

**A1. 통합 방식 결정**
- `git submodule`로 두 리소스 추가.
- 대안: 필요한 파일만 복사.

**A2. 스킬 설치 스크립트 작성**
- `scripts/install-claude-imple-skills.sh`.
- `scripts/install-agent-council.sh` ⭐ NEW.

**A3. Council 설정 생성** ⭐ NEW
- `config/council.config.yaml` 생성.
- 멤버 설정: Opus, GLM, Qwen, GPT.
- Chairman 설정: Opus (기본).

**A4. Router 확장**
- `config/config.json`에 `skills`/`hooks`/`council` 섹션 추가.
- `config/custom-router.js`에 skill→agent 매핑 및 council 호출 로직 추가.

**A5. 훅 래퍼 구현**
- 파일 편집 미들웨어 구현.
- 사전/사후 훅 연결.
- 초기 정책: `warn` 모드 (경고만).

**A6. 문서 업데이트**
- README/운영 가이드 업데이트.
- Council 사용법 문서화.

**A7. E2E 테스트**
- 시나리오 1: tasks-init → orchestrate → coder 작업.
- 시나리오 2: council 소집 → 의견 수렴 → synthesis ⭐ NEW.
- 시나리오 3: security-review → 훅 동작 → 차단.

#### 산출물
- `external/claude-imple-skills` (서브모듈 또는 복사).
- `external/agent-council` (서브모듈 또는 복사) ⭐ NEW.
- 설치 스크립트 2개.
- `config/council.config.yaml` ⭐ NEW.
- config/router 변경 커밋.
- E2E 테스트 결과 (3개 시나리오).

### Phase B — 포팅 및 고도화 (1–2주)

#### 목표
스킬 프롬프트 포팅, Branch/Worker 런타임 안정화, Council 시스템 고도화, Compactor 자동화.

#### 작업 항목

**B1. 프롬프트 포팅**
- Claude 전용 → Opus/Soloist 맞게 변환.
- 템플릿화 및 검증 루틴 도입.

**B2. Council 시스템 고도화** ⭐ NEW
- 응답 속도 차이 해결 (타임아웃, 비동기 수집).
- 비용 관리 (선택적 활성화).
- 의견 충돌 해결 (합의 규칙 강화).

**B3. Compactor 자동화**
- `compress` 스킬과 라우터 연동.
- 토큰 임계값 트리거 (80%/85%/95%).

**B4. Branch/Worker 런타임**
- 작업 ID, 상태 조회, 취소 기능.
- Worker 세션 관리 (재연결, 로그).

**B5. 훅 정책 세분화**
- 경고/차단 정책 튜닝.
- 역할 기반 예외 처리.

**B6. Cortex 모니터 확장** ⭐ NEW
- Council 진행 상황 추적.
- 멤버별 응답 시간 모니터링.
- 합의 성공률 측정.

#### 산출물
- 포팅된 스킬 프롬프트 템플릿.
- Council 런타임 API ⭐ NEW.
- Branch/Worker 실행 API.
- Compactor 자동화 설정.
- 운영 대시보드 (Council 포함) ⭐ NEW.

### Phase C — 운영·확장 (2–6주)

#### 목표
TASKS.md/Task-board 연동, multi-AI review 옵션, 운영 최적화, 멀티유저 검토.

#### 작업 항목

**C1. 작업 관리 연동**
- TASKS.md/kanban 보드 실시간 연동.
- Council 결과를 작업에 반영 ⭐ NEW.

**C2. multi-ai-review 훅 통합** (옵션)
- 외부 CLI (gemini, codex) 통합.
- Council과 multi-ai-review 연동.

**C3. 모니터링·알림 완비**
- 자동 롤백 정책.
- Council 실패 시 알림 ⭐ NEW.
- 성능 메트릭 대시보드.

**C4. 성능 최적화**
- vLLM 동시성 튜닝.
- Council 호출 최적화 (캐싱, 배치) ⭐ NEW.
- 비용 모니터링.

**C5. 멀티유저 검토** (Spacebot 기능)
- Discord/Slack 연동 가능성 검토.
- Council 멀티유저 시나리오 설계 ⭐ NEW.

---

## 8. 검증 및 테스트

### 8.1 단위 테스트
- Router 매핑 로직.
- Hook wrapper.
- Skill 호출 래퍼.
- Council 멤버 호출 ⭐ NEW.
- Chairman synthesis 로직 ⭐ NEW.

### 8.2 통합 테스트
- Opus → Branch → Worker → Hook E2E (5개 시나리오).
- Council 소집 → 의견 수렴 → Synthesis (3개 시나리오) ⭐ NEW.
- 보안 스캔 → 훅 차단 → 롤백.

### 8.3 부하 테스트
- 동시 작업 20~50 시나리오.
- Council 병렬 호출 10개 동시 실행 ⭐ NEW.
- 응답 시간 측정 (각 멤버 30초 이내).

### 8.4 보안 점검
- 비밀값 노출 검증.
- 권한 검증.
- 훅 정상 동작 확인.
- Council 멤버 간 데이터 격리 ⭐ NEW.

### 8.5 운영 수용 테스트
- 운영자가 3개 시나리오를 실습하여 워크플로 검증.
- Council 사용 시나리오 (아키텍처 설계, 기술 선택) ⭐ NEW.

---

## 9. 롤아웃 전략

### 9.1 단계적 롤아웃
1. **staging**: 내부 테스트 환경.
2. **canary**: 소수 팀 (3-5명) 파일럿.
3. **production**: 전체 사용자.

### 9.2 훅 정책 진화
- **초기**: `warn` 모드 (경고만).
- **중기**: 중요한 파일에만 `block` 적용.
- **후기**: 전체 `block` 적용 (예외 허용).

### 9.3 Council 도입 순서 ⭐ NEW
1. **Phase A**: 수동 Council (사용자가 명시적으로 호출).
2. **Phase B**: 자동 Council (특정 시나리오에 자동 소집).
3. **Phase C**: 지능형 Council (시스템이 필요시 자동 판단).

### 9.4 롤백 계획
- **즉시 롤백**: 이전 커밋으로 되돌림.
- **훅 비활성화**: 플래그로 즉시 비활성화.
- **Council 비활성화**: 설정에서 Council 멤버 제거 ⭐ NEW.

### 9.5 모니터링 임계치
- 훅 실패율 > 5% → 경고.
- Council 실패율 > 10% → 경고 ⭐ NEW.
- 작업 실패율 > 5% → 자동 롤백.

---

## 10. 리스크 및 대응

### 10.1 프롬프트 포팅 실패
- **리스크**: Claude 전용 표현 의존.
- **대응**: 템플릿화 및 검증 루틴 도입, 단계적 포팅.

### 10.2 훅 과도한 차단
- **리스크**: 개발 흐름 방해.
- **대응**: 초기 경고 모드로 운영, 정책 튜닝, 역할 기반 예외.

### 10.3 vLLM 동시성 한계
- **리스크**: 동시 요청 처리 실패.
- **대응**: 작업 큐, GLM 폴백, 작업 스로틀링.

### 10.4 토큰·비용 증가
- **리스크**: 장기 세션 비용 폭증.
- **대응**: Compactor 자동화, 역할별 컨텍스트 분리, Council 선택적 활성화 ⭐ NEW.

### 10.5 Council 모델 간 응답 속도 차이 ⭐ NEW
- **리스크**: 느린 모델로 인한 전체 지연.
- **대응**: 타임아웃 설정 (각 멤버 30초), 비동기 수집, 결과 없는 멤버는 제외.

### 10.6 Council 비용 증가 ⭐ NEW
- **리스크**: 다중 모델 호출로 비용 증가.
- **대응**: 선택적 활성화 (중요한 결정에만 Council 사용), 캐싱, 배치 처리.

### 10.7 모델 간 의견 충돌 ⭐ NEW
- **리스크**: 모델 간 상반된 의견으로 합의 실패.
- **대응**: Chairman(Opus)이 명확한 합의 규칙 적용 (다수결 vs 전문가 의견), 가중치 기반 합의.

---

## 11. 인력·자원·권한

### 11.1 권장 인원
- **Backend/Infra** (1명): Node.js, 라우터, Worker 구현.
- **DevOps** (1명): 배포, vLLM, 모니터링.
- **QA** (1명): 테스트 시나리오, 검증.
- **Council 전담** (0.5명): Council 시스템 구현, 프롬프트 튜닝 ⭐ NEW.

### 11.2 인프라
- **vLLM 서버**: 로컬 또는 클라우드 (Qwen3.5-122B 실행).
- **Claude Code Router**: 실행 환경.
- **상태 추적용 DB**: SQLite 또는 Redis.
- **Council 런타임**: 각 모델 API 접근 ⭐ NEW.

### 11.3 권한
- **레포지토리**: 쓰기 권한.
- **vLLM/Cloud API**: 접근 권한.
- **.env 편집**: API 키 설정 권한.
- **Council 멤버 API**: 각 모델 API 키 (Opus, GLM, Qwen, GPT) ⭐ NEW.

---

## 12. 산출물 체크리스트

### Phase A 산출물
- [ ] `external/claude-imple-skills` 추가.
- [ ] `external/agent-council` 추가 ⭐ NEW.
- [ ] `scripts/install-claude-imple-skills.sh`.
- [ ] `scripts/install-agent-council.sh` ⭐ NEW.
- [ ] `config/council.config.yaml` ⭐ NEW.
- [ ] `config/config.json` (`contextStrategies`, `skills`/`hooks`/`council`) 변경.
- [ ] `config/custom-router.js`에 매핑/branch/council 로직 추가 ⭐ NEW.
- [ ] Hook wrapper 구현.
- [ ] Council 런타임 기본 구현 ⭐ NEW.
- [ ] 문서(README/운영 매뉴얼) 업데이트.
- [ ] E2E 테스트 결과 (3개 시나리오, Council 포함) ⭐ NEW.

### Phase B 산출물
- [ ] 포팅된 스킬 프롬프트 템플릿.
- [ ] Council 고도화 (응답 속도, 비용, 충돌 해결) ⭐ NEW.
- [ ] Compactor 자동화 설정.
- [ ] Branch/Worker 실행 API.
- [ ] Cortex 모니터 (Council 포함) ⭐ NEW.
- [ ] 운영 대시보드 (Council 포함) ⭐ NEW.

### Phase C 산출물
- [ ] TASKS.md/kanban 연동.
- [ ] multi-ai-review 훅 통합.
- [ ] 모니터링·알림·자동 롤백.
- [ ] 성능 최적화 (vLLM, Council) ⭐ NEW.
- [ ] 멀티유저 검토 보고서 ⭐ NEW.

---

## 13. 일정 및 예상 소요

### 13.1 Phase A (1–3일)
- **Day 1**: 서브모듈 추가, 설치 스크립트, Council 설정 ⭐ NEW.
- **Day 2**: Router 확장, 훅 래퍼, Council 런타임 ⭐ NEW.
- **Day 3**: E2E 테스트, 문서화.

### 13.2 Phase B (1–2주)
- **Week 1**: 프롬프트 포팅, Council 고도화, Compactor 자동화 ⭐ NEW.
- **Week 2**: Branch/Worker 런타임, Cortex 모니터, 대시보드.

### 13.3 Phase C (2–6주)
- **Week 3-4**: 작업 관리 연동, multi-ai-review, 모니터링.
- **Week 5-6**: 성능 최적화, 멀티유저 검토, Council 확장 ⭐ NEW.

### 13.4 총 소요 (한 명 기준)
- **Phase A**: 1–3일 (빠른 통합).
- **Phase B**: 1–2주 (고도화).
- **Phase C**: 2–6주 (운영·확장).
- **총계**: 4–9주 (동시 인력 투입 시 단축 가능).

---

## 14. 권장 우선순위

### 14.1 즉시 착수 (Phase A)
1. `claude-imple-skills` 서브모듈 추가.
2. `agent-council` 서브모듈 추가 ⭐ NEW.
3. Council 설정 파일 생성 (`council.config.yaml`) ⭐ NEW.
4. 훅 래퍼 및 파일 편집 파이프라인 연결 (초기엔 warn 모드).
5. custom-router의 skill→agent 매핑 적용.

### 14.2 단기 목표 (Phase B)
1. `compress` 스킬 연동 (장기 컨텍스트 최적화).
2. Branch/Worker 비동기 패턴 구현.
3. Council 시스템 고도화 (응답 속도, 비용, 충돌 해결) ⭐ NEW.
4. Cortex 모니터 (Council 진행 상황 포함) ⭐ NEW.

### 14.3 장기 목표 (Phase C)
1. TASKS.md/Task-board 실시간 연동.
2. multi-ai-review 훅 통합 (옵션).
3. 멀티유저 지원 검토 (Spacebot 기능).
4. Council 지능형 자동 소집 ⭐ NEW.

---

## 15. 다음 단계 및 요청사항

### 15.1 진행 옵션
- **옵션 1** (권장): `git submodule`로 두 리소스(`claude-imple-skills`, `agent-council`) 추가 후 Phase A 진행 ⭐ NEW.
- **옵션 2**: 필요한 스킬(최대 6개)과 Council 기능만 빠르게 복사·포팅 ⭐ NEW.
- **옵션 3**: 먼저 상세 설계(변경 파일 목록, 프롬프트 매핑 샘플, Council 시나리오) 제공 ⭐ NEW.

### 15.2 훅 동작 기본 정책
- **A**: 초기 `warn` 모드 (권장).
- **B**: 즉시 `block` 모드.

### 15.3 Council 기본 설정 ⭐ NEW
- **Chairman**: Opus (기본) 또는 사용자 지정.
- **멤버 수**: 3-4개 (Opus, GLM, Qwen, GPT).
- **활성화 시점**: Phase A (수동 호출) → Phase B (자동 소집).

### 15.4 요청 예시
```
"옵션 1, 훅은 warn으로 시작, Council은 Opus를 Chairman으로, 
멤버는 Opus, GLM, Qwen 3개만 활성화"
```

---

**이 계획서는 세 가지 핵심 리소스(Spacebot, claude-imple-skills, agent-council)를 모두 균형 있게 반영하여 작성되었습니다.** ⭐

**다음 단계**: 원하시는 옵션을 선택해 주시면 Phase A 작업을 시작하겠습니다.