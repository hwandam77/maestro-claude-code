# 2026-03-07 Server Environment Alignment

<!-- markdownlint-disable MD013 -->

- Task ID: `DOC-SERVER-ALIGN-2026-03-07-01`
- run_id: `run-20260307-server-alignment-01`
- Task:
  - `Nexus`/`Cognit`의 현재 live 상태를 반영해 계획서를 수정
- Input:
  - `docs/계획서/MAESTRO_UPGRADE_PLAN.md`
  - `docs/계획서/Nexus-vLLM-벤치마크-계획서.md`
  - `docs/리포트/server_spec_report_20260204.md`
  - `docs/리포트/nexus_vllm_benchmark_20260205.md`
  - `docs/리포트/cognit_vllm_benchmark_20260205.md`
  - `docs/리포트/reference_links_20260307.md`
  - SSH 실측 결과 (`cognit`, `nexus`)
- Key Findings:
  - `Cognit`는 현재 `vllm`이 아니라 `Ollama` 기반 (`11434`)
  - `Nexus`는 현재 `vllm`이 아니라 `llama-server` 기반 (`8080`)
  - `Nexus` GPU는 현재 3x RTX 3090으로 확인됨
  - 기존 문서의 `Nexus=DeepSeek-R1 vLLM`, `Cognit=Qwen3 vLLM` 가정은 현재 live 상태와 다름
- Outcome:
  - `MAESTRO_UPGRADE_PLAN.md`에 `runtimeInventory`, `profile alias`, `runtime adapter` 구조 반영
  - `Nexus-vLLM-벤치마크-계획서.md`를 현재 운영 기준 + 재검증 계획 문서로 재작성
- Validation:
  - SSH alias `cognit`, `nexus` 실측
  - 문서 변경 후 markdownlint 예정
- Evidence:
  - `cognit`: `ollama serve`, `11434`, `qwen3:30b-a3b` 등 모델 확인
  - `nexus`: `llama-server`, `8080`, `Qwen3.5-122B-A10B...` 로드 확인
- Next Step:
  - inventory 기반 config/schema 문서화
  - `scripts/status.sh`와 `.env.example` 개편 여부 결정
  - 참고 링크 문서 유지
