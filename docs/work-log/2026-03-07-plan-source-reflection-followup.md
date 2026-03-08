# 2026-03-07 Plan Source Reflection Follow-up

<!-- markdownlint-disable MD013 -->

- Task ID: `DOC-PLAN-2026-03-07-03`
- run_id: `run-20260307-plan-reflection-followup-01`
- Task:
  - 외부 3개 저장소의 기능이 `MAESTRO_UPGRADE_PLAN.md`에 충분히 반영됐는지 재점검하고, 누락된 기능군의 채택/보류 결정을 문서에 반영
- Input:
  - `/Users/hwandam/workspace/maestro-claude-code/docs/계획서/MAESTRO_UPGRADE_PLAN.md`
  - `https://github.com/spacedriveapp/spacebot?tab=readme-ov-file`
  - `https://github.com/team-attention/agent-council/tree/main`
  - `https://github.com/affaan-m/everything-claude-code`
  - `/Users/hwandam/workspace/maestro-claude-code/docs/리포트/reference_links_20260307.md`
- Expected Output:
  - 외부 기능군별 adopt/defer 판단이 명시된 계획서
  - Spacebot `skills/MCP/security`, Agent Council host UI progress contract, ECC session lifecycle/MCP audit 반영
- Attempt:
  - 계획서를 외부 저장소 README와 재대조
  - Spacebot의 확장/보안 기능군과 ECC의 lifecycle hook 범위를 누락 항목으로 분리
  - `Agent Council`의 `wait/status/results/clean` 외 checklist/cursor 계약을 Phase A로 연결
  - `config` 예시에 `securityPolicies` 스켈레톤 추가
- Outcome:
  - `MAESTRO_UPGRADE_PLAN.md`에 adopt/defer matrix, `securityPolicies`, session lifecycle, MCP audit, host checklist contract를 반영
  - `AGENTS.md`를 skills SSOT로 유지하고 Spacebot `skills.sh`는 비도입으로 명시
- Validation:
  - 문서 구조와 단계별 실행 계획의 연결성 검토
  - `npx --yes markdownlint-cli docs/계획서/MAESTRO_UPGRADE_PLAN.md docs/work-log/2026-03-07-plan-source-reflection-followup.md`
  - 외부 링크 `curl -L` 응답 `200` 확인
- Evidence:
  - Spacebot: `skills.sh`, MCP integration, layered security, readiness/warmup
  - Agent Council: host UI `wait`, checklist/status, runtime `missing_cli`
  - Everything Claude Code: session lifecycle hook, tool/MCP audit hook, `strategic-compact`, `verify`, `security-scan`
  - markdownlint 통과
  - GitHub 링크 3건 응답 `200`
- Next Step:
  - `config.template.json` 실제 스켈레톤 개편 여부 결정
  - council wrapper script에서 checklist/cursor 계약 구체화
  - hook runner에서 `minimal/standard/strict` 프로파일 분기 구현 여부 결정
