# Nexus vLLM 종합 성능평가 벤치마크 계획서

**작성일**: 2026-02-05
**대상 서버**: Nexus (10.5.5.14 / 192.168.1.1)

---

## 1. 서버 스펙

| 항목 | Nexus | Cognit (비교 대상) |
|------|-------|-------------------|
| CPU | Intel Xeon Platinum 8173M (112T) | AMD Ryzen 7 5700X3D (16T) |
| RAM | 128GB | 64GB |
| GPU | 2x RTX 3090 (**24GB** each) | 2x RTX 3080 Ti (**12GB** each) |
| 총 VRAM | **48GB** | 24GB |
| CUDA | 13.1 | 13.0 |
| Driver | 590.48.01 | 580.105.08 |
| vLLM | 0.15.0 (venv) | 0.15.0 (venv) |

---

## 2. 현재 상태

| 항목 | 상태 |
|------|------|
| vLLM 서비스 | **중지됨** (systemd failed - 모델 경로 없음) |
| GPU 메모리 | 비어있음 (1 MiB / 24,576 MiB) |
| 사용 가능 모델 | DeepSeek-R1-Distill-Llama-70B-AWQ (26GB, ~/models/) |
| 기존 모델 | Qwen3-Coder-30B-A3B (경로 없음), Qwen2.5-72B (경로 없음) |

### 시작 스크립트 현황

| 스크립트 | 모델 | max-model-len | gpu-mem | max-num-seqs |
|----------|------|---------------|---------|--------------|
| vllm-start.sh (systemd) | Qwen3-Coder-30B-A3B | 65536 | 0.95 | 32 |
| vllm-optimized.sh | Qwen2.5-72B-AWQ | 8192 | 0.92 | 128 |
| vllm-coder.sh | Qwen2.5-Coder-32B-AWQ | 32768 | 0.92 | 128 |

**참고**: 위 모델들은 현재 디스크에 없음. DeepSeek-R1-70B-AWQ만 사용 가능.

---

## 3. 벤치마크 대상 모델

### 3.1 DeepSeek-R1-Distill-Llama-70B-AWQ

| 항목 | 값 |
|------|-----|
| 크기 | ~26GB (AWQ 4bit) |
| 아키텍처 | Llama 기반 (dense, MoE 아님) |
| 특성 | 추론/reasoning 특화 |
| VRAM 요구 | ~36GB 예상 (2x 3090에 적합) |

---

## 4. 테스트 계획

Cognit 벤치마크와 동일한 7+1 단계 구성.

### Phase 0: 서버 기동 및 설정 탐색

1. DeepSeek-R1-70B-AWQ용 시작 스크립트 작성
2. 초기 설정값 결정:
   - `--tensor-parallel-size 2`
   - `--max-model-len`: 모델 지원 최대값 확인 후 결정 (8192~32768)
   - `--gpu-memory-utilization`: **0.92** 시작 (RTX 3090은 24GB로 여유 충분)
   - `--max-num-seqs`: 32~128 (VRAM 여유에 따라)
   - `--max-num-batched-tokens`: 4096
   - `--enable-prefix-caching`
   - `--enable-chunked-prefill`
3. 서버 기동 및 KV 캐시 할당 정보 기록
4. GPU 메모리 사용량, 온도 기록

### Phase 1: 단일 요청 레이턴시 (3단계)

Cognit과 동일한 프롬프트 사용, 각 5회 반복.

| 테스트 | 프롬프트 | max_tokens |
|--------|---------|------------|
| 짧은 출력 | "1+1=?" | 32 |
| 중간 출력 | Python 퀵소트 설명 | 256 |
| 긴 출력 | FastAPI CRUD 코드 | 1024 |

**측정 지표**: TTFT, Total time, Completion tokens, TPS

### Phase 2: 최대 Throughput

| 테스트 | max_tokens | 반복 |
|--------|-----------|------|
| 2048 tokens | 2048 | 2회 |
| 4096 tokens | 4096 | 2회 |

### Phase 3: 동시 요청 처리

Cognit과 동일 구성 (각 128 tokens 출력).

| 동시 요청 수 | 비고 |
|-------------|------|
| 1 | 기준 |
| 2 | |
| 4 | |
| 8 | |
| 16 | Nexus는 max-num-seqs가 크므로 추가 |
| 32 | Nexus 추가 (VRAM 여유 활용) |

### Phase 4: Prefix Caching 효과

동일 system prompt 3회 반복, TTFT 비교.

### Phase 5: 컨텍스트 길이별 성능 변화

max_model_len 기준 100%→10% (10단계).
100%는 `max_model_len - prompt_tokens - 1`로 설정.

| 비율 | 비고 |
|------|------|
| 100% | 전량 소화 테스트 |
| 90% ~ 10% | 10% 단위 축소 |

### Phase 6: gpu-memory-utilization 튜닝

RTX 3090 (24GB)에서 최적값 탐색.

| 테스트 값 | 예상 |
|----------|------|
| 0.92 (시작) | 안정적 |
| 0.93 | |
| 0.94 | |
| 0.95 | vllm-start.sh 기존 설정, 테스트 필요 |
| 0.96 | OOM 경계 탐색 |

RTX 3090은 24GB로 Cognit(12GB) 대비 여유가 많으므로 0.95 이상도 가능할 수 있음.

### Phase 7: GPU 상태 최종 기록

nvidia-smi 전체 출력, 온도/전력/VRAM/utilization 기록.

---

## 5. Cognit 대비 비교 포인트

| 비교 항목 | Cognit | Nexus 예상 | 비고 |
|-----------|--------|-----------|------|
| 모델 | Qwen3-Coder-30B-A3B (MoE, AWQ) | DeepSeek-R1-70B (Dense, AWQ) | 70B dense vs 30B MoE |
| 단일 TPS | ~180 tok/s | 낮을 것 (70B dense) | 모델 크기 2배 이상 |
| VRAM 활용 | 24GB (91.7%) | 48GB | 여유 훨씬 큼 |
| max_model_len | 16,384 | 8,192~32,768 | VRAM에 따라 |
| 동시 처리 | max 8 (KV 제한) | 32+ 가능 | KV 캐시 대폭 증가 |
| GPU 온도 | 피크 67°C | TBD | 3090은 발열 더 높을 수 있음 |

---

## 6. 사전 확인 필요사항

- [ ] DeepSeek-R1-Distill-Llama-70B-AWQ 모델 파일 무결성 확인
- [ ] 모델의 max_position_embeddings (지원 최대 컨텍스트) 확인
- [ ] vLLM 0.15.0에서 DeepSeek-R1 호환성 확인
- [ ] tool_call_parser 설정 (DeepSeek-R1은 reasoning 모델이므로 별도 설정 필요할 수 있음)
- [ ] Cognit에서 다운로드 중인 모델(ssh 프로세스 확인됨) 완료 여부

---

## 7. 예상 소요 시간

| Phase | 예상 |
|-------|------|
| Phase 0 (기동) | 모델 로드 + 컴파일 |
| Phase 1~4 (레이턴시/동시/캐시) | 70B 모델이므로 Cognit보다 길어짐 |
| Phase 5 (컨텍스트별) | max_model_len에 비례 |
| Phase 6 (메모리 튜닝) | 서버 재시작 포함 반복 |
| **전체** | 모델 로드 시간 포함 상당 소요 |

---

## 8. 출력물

1. `Docs/리포트/nexus_vllm_benchmark_20260205.md` - 종합 성능평가 리포트
2. Cognit vs Nexus 비교 섹션 포함
3. gpu-memory-utilization 최적값 도출 및 start script 반영

---

*작성: AI Assistant*
