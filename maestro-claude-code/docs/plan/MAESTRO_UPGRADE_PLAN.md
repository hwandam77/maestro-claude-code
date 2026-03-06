# Maestro Claude Code 고도화 종합계획서

작성자: hwandam77 / 작성일: 2026-03-06

## 목차
1. 개요
2. 목표 및 성공 기준
3. 범위
4. 현재 상태 요약
5. 아키텍처 설계 (요약)
6. 통합 대상 및 호환성
7. 단계별 작업 계획 (Phase A/B/C)
8. 검증 및 테스트 계획
9. 롤아웃 전략 및 롤백
10. 리스크 및 대응 방안
11. 인력·자원·권한
12. 산출물 체크리스트
13. 일정 및 예상 소요
14. 권장 우선순위
15. 다음 단계 및 요청사항

---

## 1. 개요

본 문서는 `Maestro Claude Code` 프로젝트(이하 '본 시스템')에 Spacebot의 핵심 철학(Branch/Worker/Compactor/Cortex)과 `insightflo/claude-imple-skills`(이하 'imple-skills')의 워크플로·훅 패키지를 통합하여, 멀티태스크 오케스트레이션, 컨텍스트 최적화 및 자동 검증 파이프라인을 적용하는 종합 계획서이다. Node.js 기반 라우터와 vLLM(Qwen3.5-122B)을 핵심 실행기로 유지하면서, Spacebot의 개념을 본 환경에 맞게 재해석하여 적용하는 것을 목표로 한다.

## 2. 목표 및 성공 기준

- 목표 1: Opus(설계, Maestro)와 Qwen3.5-122B(코딩, Soloist)의 역할 분담 자동화
  - 성공 기준: `@architect` 요청은 Opus로, `@coder`/`@file-manager` 요청은 Qwen3.5-122B로 라우팅되며, 샘플 시나리오 3개 이상의 E2E 통과

- 목표 2: 파일 편집 전후의 자동 훅(보안·품질) 적용
  - 성공 기준: `pre-edit-impact-check`, `security-scan` 훅이 실행되어 실패 시 경고 또는 차단이 동작(설정에 따름), 훅 동작에 대한 테스트 10건 통과

- 목표 3: 컨텍스트 최적화(Compress) 도입으로 장기 토큰 사용 절감
  - 성공 기준: 긴 세션(시뮬레이션, >50k 토큰) 진행 시 `compress` 스킬이 동작하여 토큰 소비 평균 30% 이상 절감

## 3. 범위

포함 항목:
- `impl-skills`(필수 스킬 일부)의 서브모듈 또는 복사 통합
- `config/config.json` 에 `contextStrategies` 및 skills/hooks 섹션 추가
- `config/custom-router.js` 에서 skill→agent 매핑, Branch/Worker spawn 로직 확장
- 파일 편집 파이프라인 훅 연결(사전/사후 검증)
- `compress` 스킬을 이용한 longContext 자동화
- 간단한 Cortex 수준의 모니터링(헬스/큐 메트릭)

제외 항목:
- 시스템 언어 전환(Rust로 재구성)
- 외부 CLI(예: gemini, codex) 의무 설치 — 옵션으로 둠

## 4. 현재 상태 요약

이미 수행된 변경(레포지토리 기준):
- `config/config.json` 일부 업데이트 (vllm-qwen35 provider 등)
- `config/custom-router.js` 에 `soloist` 티어 매핑 추가
- `.env` 파일에 Qwen3.5-122B 관련 환경 변수 추가
- `README.md` 에 5-Model Orchestra 설명 추가

(위 변경사항은 원격에 커밋되어 있음)

## 5. 아키텍처 설계 (요약)

핵심 개념의 Node.js 적응안:
- Channel: 사용자 상호작용 전담(기존 Claude Code/Opus 담당)
- Branch: Opus 가 독립적으로 사고(비동기 작업 분기)
- Worker: Qwen3.5-122B 를 역할별( `coder`, `file-manager`, `debugger`) 로 사용
- Compactor: `compress` 스킬을 통해 오래된 컨텍스트를 요약하여 컨텍스트 크기 관리
- Cortex: 라우터 레벨의 경량 모니터(작업 큐, 헬스, 실패율)

기본 흐름:
1. 사용자 요청 → `custom-router.js` 에서 에이전트/스킬 감지
2. Opus(설계) 실행 → 필요 시 Branch spawn
3. Branch → Worker(Qwen3.5-122B) 호출(비동기 작업 ID 발행)
4. 파일 수정 전 훅 실행(검증) → 수정 → post-hook
5. Compactor 주기/임계값에 따라 longContext 압축

## 6. 통합 대상 및 호환성

통합 대상: `insightflo/claude-imple-skills`
- 우선 적용 권장 스킬: `/workflow`, `/orchestrate-standalone`, `/compress`, `/agile`, `/tasks-init`, `/impact`, `/security-review`, `/quality-auditor`
- 훅 목록: `pre-edit-impact-check`, `security-scan`, `standards-validator`, `quality-gate`, `architecture-updater`, `changelog-recorder`

호환성 고려사항:
- imple-skills 는 Claude Code 환경(Claude system prompts)에 최적화되어 있으므로 프롬프트 템플릿을 Opus/Qwen3.5로 포팅 필요
- 일부 스킬은 외부 도구 의존(옵션) → 필요한 경우 옵션으로 활성화
- 훅은 파일 편집 파이프라인(Worker → commit)에 붙여야 하며, 훅 실패 시 동작 정책(경고/차단)을 설정해야 함
- 라이선스: imple-skills는 MIT 라이선스 — 통합 시 문제 없음(일반적 사용 조건 만족)

## 7. 단계별 작업 계획

### Phase A — 안전한 가져오기 & 빠른 가치 실현 (1–3일)
목표: imple-skills를 레포지토리에 통합하고 핵심 스킬을 즉시 사용 가능하게 설정

작업 항목:
- A1. 통합 방식 결정: `git submodule` 권장(또는 필요한 스킬만 `external/` 복사)
- A2. `scripts/install-claude-imple-skills.sh` 작성: 설치/초기화 자동화
- A3. `config/config.json` 에 `skills`/`hooks` 섹션 및 `contextStrategies` 추가
- A4. `custom-router.js` 에 skill → agent 매핑 및 Branch spawn 기본 로직 추가
- A5. 훅 래퍼 작성 및 파일 편집 파이프라인 연결
- A6. README/운영 매뉴얼 업데이트
- A7. 테스트 시나리오(E2E) 실행

산출물:
- `external/claude-imple-skills` (submodule 또는 복사)
- 설치 스크립트
- config 및 router 변경 커밋
- 테스트 결과 보고서

### Phase B — 적응·고도화 (1–2주)
목표: 프롬프트/스킬 포팅, Branch/Worker 관리, Compactor 자동화

작업 항목:
- B1. 스킬 system prompts 포팅(Claude → Opus/Soloist)
- B2. `compress` 스킬을 라우터와 연동하여 자동 트리거 구현
- B3. Branch 패턴 구현(비동기 작업 ID, 상태 조회 API)
- B4. Worker 장기 세션 관리(재연결/로그)
- B5. 훅 정책 세분화(경고/차단, 권한 예외)
- B6. Cortex 경량 모니터(메트릭 수집)

산출물:
- 포팅된 스킬 프롬프트 템플릿
- Branch/Worker 런타임 API
- Compactor 자동화 설정
- 운영 대시보드(간단)

### Phase C — 운영·확장(장기)
목표: TASKS/Kanban 연동, multi-AI review, 운영 최적화

작업 항목:
- TASKS.md / task-board 실시간 연동
- multi-ai-review 훅 통합(옵션)
- 모니터링/알림 및 자동 롤백 정책
- 성능 최적화 및 비용 모니터링

## 8. 검증 및 테스트 계획

- 단위 테스트: router 매핑, hook wrapper, skill 호출 래퍼
- 통합 테스트: Opus → Branch → Worker → Hook E2E 시나리오 5개
- 부하 테스트: 동시 작업 20~50 시나리오(동시성 체감)
- 보안 스캔: secrets 노출·권한 검증
- Acceptance 테스트: 운영자가 시나리오 3종을 직접 실습하여 워크플로 검증

## 9. 롤아웃 전략 및 롤백

- 단계적 롤아웃: staging → canary → production
- 롤백: 변경 전 커밋으로 되돌림, 훅 비활성화 플래그 제공
- 모니터링 임계치: 실패율 >5% 또는 훅 실패로 개발 차단 발생 시 롤백

## 10. 리스크 및 대응 방안

1. 프롬프트 포팅 실패(Claude 전용 문법 의존)
   - 대응: 템플릿화 및 검증, 초기에는 경량 스킬만 포팅
2. 훅 과도한 차단으로 개발 흐름 방해
   - 대응: 초기 `warn` 모드로 운영, 점진적 강화
3. vLLM 동시성 한계
   - 대응: 작업 큐, GLM 폴백, 작업 스로틀링
4. 토큰·비용 증가
   - 대응: Compactor 적용, 역할별 컨텍스트 분리

## 11. 인력·자원·권한

- 권장 인원: 1 Backend/Infra (Node.js), 1 DevOps, 1 QA
- 인프라: vLLM 서버(로컬 또는 클라우드), Claude Code Router 실행 환경, 경량 DB(상태 추적용)
- 권한: 레포지토리 쓰기 권한, vLLM/Cloud API 접근, .env 편집 권한

## 12. 산출물 체크리스트

- [ ] `external/claude-imple-skills` 추가(서브모듈 또는 복사)
- [ ] `scripts/install-claude-imple-skills.sh`
- [ ] `config/config.json` 변경 적용
- [ ] `config/custom-router.js` 에 매핑/branch 로직 추가
- [ ] Hook wrapper 구현 및 파이프라인 연결
- [ ] Compactor 자동화 트리거 설정
- [ ] 문서(README) 업데이트
- [ ] E2E 테스트 보고서

## 13. 일정 및 예상 소요

- Phase A: 1–3일
- Phase B: 1–2주
- Phase C: 2–6주 (요구사항에 따라 변화)

(한 명 기준 추정 — 병행 인력 투입 시 단축 가능)

## 14. 권장 우선순위

1. `insightflo/claude-imple-skills` 서브모듈 추가
2. 훅 래퍼 및 파일 편집 파이프라인 연결 (warn 모드로 시작)
3. `custom-router.js` 의 skill→agent 매핑 적용
4. `compress` 스킬 연동
5. Branch/Worker 비동기 패턴 구현

## 15. 다음 단계 및 요청사항

원하시는 작업 방식을 알려주세요:
- 옵션 1 (권장): `git submodule`로 `claude-imple-skills` 추가 후 Phase A 진행
- 옵션 2: 필요한 스킬(최대 6개)만 지정하여 복사 및 빠른 포팅
- 옵션 3: 우선 설계 문서(변경 파일 목록, 프롬프트 매핑 샘플) 제공

훅 동작 기본 정책 선택:
- A: 초기에는 `warn`(경고) 모드, 추후 `block`(차단) 적용
- B: 즉시 `block` 모드 적용

원하시는 옵션(예: "옵션 1, 훅은 warn 시작")을 알려주시면 바로 Phase A를 시작하겠습니다.
