# 2026-03-07 참고 링크 리스트

<!-- markdownlint-disable MD013 -->

## 1. 외부 저장소

- Spacebot
  - [spacebot README](https://github.com/spacedriveapp/spacebot?tab=readme-ov-file)
- Agent Council
  - [agent-council repository](https://github.com/team-attention/agent-council/tree/main)
- Everything Claude Code
  - [everything-claude-code repository](https://github.com/affaan-m/everything-claude-code)

## 2. 이번 문서 작업에서 직접 참조한 로컬 문서

- `docs/계획서/MAESTRO_UPGRADE_PLAN.md`
- `docs/계획서/Nexus-vLLM-벤치마크-계획서.md`
- `docs/리포트/nexus_vllm_benchmark_20260205.md`
- `docs/리포트/cognit_vllm_benchmark_20260205.md`
- `docs/리포트/server_spec_report_20260204.md`
- `docs/work-log/2026-03-07-server-environment-alignment.md`
- `docs/work-log/2026-03-07-maestro-upgrade-plan-source-analysis.md`

## 3. 참조 목적

- Spacebot
  - Branch/Worker/Compactor/Cortex 설계 철학 및 운영 모델 확인
- Agent Council
  - 실제 `council.config.yaml` 스키마와 `start -> wait/status -> results -> clean` 실행 흐름 확인
- Everything Claude Code
  - hook profile, `strategic-compact`, `verify`, `orchestrate`, plugin 제약 확인
- 로컬 문서
  - 현재 서버 상태, 기존 벤치마크 결과, 계획서 개정 근거 대조
