# 2026-03-07 Maestro Upgrade Plan Source Analysis

<!-- markdownlint-disable MD013 -->

- Task ID: `DOC-PLAN-2026-03-07-01`
- run_id: `run-20260307-maestro-upgrade-plan-01`
- Task:
  - `MAESTRO_UPGRADE_PLAN.md`를 외부 3개 저장소의 최신 내용 기준으로 재검토하고 보강
- Input:
  - `/Users/hwandam/workspace/maestro-claude-code/docs/계획서/MAESTRO_UPGRADE_PLAN.md`
  - `https://github.com/spacedriveapp/spacebot?tab=readme-ov-file`
  - `https://github.com/team-attention/agent-council/tree/main`
  - `https://github.com/affaan-m/everything-claude-code`
  - 로컬 파일 `config/custom-router.js`, `config/config.template.json`, `scripts/start.sh`
- Expected Output:
  - 사실 기반 통합 계획서
  - 실현 가능한 Phase A/B/C
  - Task Contract, Quality Gates, 증적 기록
- Attempt:
  - 외부 저장소를 각각 문서와 핵심 설정/스크립트 단위로 비교
  - 로컬 라우터 구조와 맞지 않는 가정 제거
  - `Agent Council`의 실제 스키마와 실행 모델로 계획서 수정
  - `Everything Claude Code`는 선택 도입 기준으로 정리
  - `Spacebot`은 운영 모델 reference로 재정의
- Outcome:
  - 기존 계획서의 과장된 council 스키마와 포괄적 import 가정 제거
  - `MAESTRO_UPGRADE_PLAN.md`를 source-based 설계 문서로 재작성
  - `docs/work-log/` 디렉터리와 작업 기록 추가
- Validation:
  - 외부 저장소 README, config, hook, command 문서와 계획서 내용 대조
  - 로컬 `config/custom-router.js`, `config/config.template.json`, `scripts/start.sh` 기반 적합성 검토
- Evidence:
  - Spacebot: process model, compactor threshold, security, metrics
  - Agent Council: `members/chairman/settings`, `start -> wait/status -> results -> clean`, Node.js requirement
  - Everything Claude Code: hook profiles, strategic compact, verify order, plugin/rules 제약, Node `>=18`, 일부 Python3 요구
- Next Step:
  - `config/council.config.yaml` 초안 작성
  - `contextPolicies` / `observability` 스켈레톤을 `config.template.json`에 반영 여부 결정
