# Nexus 추론 런타임 운영 기준 및 재검증 계획서

<!-- markdownlint-disable MD013 -->

**작성일**: 2026-03-07  
**문서 상태**: Revised Draft v2  
**기준**: 2026-03-07 SSH 실측 + 2026-02-05 기존 벤치마크 리포트

## 0. Task Contract

- Task ID: `DOC-NEXUS-RUNTIME-2026-03-07-01`
- Input:
  - 기존 `Nexus-vLLM-벤치마크-계획서.md`
  - `docs/리포트/nexus_vllm_benchmark_20260205.md`
  - `docs/리포트/cognit_vllm_benchmark_20260205.md`
  - `docs/리포트/server_spec_report_20260204.md`
  - 2026-03-07 SSH 실측 결과 (`cognit`, `nexus`)
- Expected Output:
  - 현재 서버 환경에 맞는 운영 기준서
  - 과거 DeepSeek-R1 vLLM 벤치마크를 현재 기준선으로 재배치
  - 향후 서버/런타임 변화에 대응 가능한 재검증 절차
- Validation:
  - 현재 live runtime과 문서 내용이 모순되지 않을 것
  - `Nexus`/`Cognit`를 물리 서버로, `profile`을 역할 단위로 분리할 것
  - 향후 `vllm`, `ollama`, `llama_cpp` 전환이 inventory 수준 변경으로 흡수될 것
- Evidence:
  - SSH 명령 결과
  - 기존 벤치마크 리포트
  - 현재 계획서 개정 내용

## 1. 문서 목적

기존 문서는 `Nexus에서 DeepSeek-R1-Distill-Llama-70B-AWQ를 vLLM으로 벤치마크할 계획`을 다뤘다. 그러나 2026-03-07 현재 실서버 상태는 이미 다르다.

- `Nexus`는 현재 `vllm`이 아니라 `llama-server` 기반으로 대형 Qwen 모델을 서빙 중이다.
- `Cognit`는 현재 `vllm`이 아니라 `Ollama` 기반 로컬 추론 노드에 가깝다.
- 두 서버 모두 “물리 서버명”과 “모델 역할”이 더 이상 1:1 대응하지 않는다.

따라서 이 문서는 더 이상 “단일 vLLM 벤치마크 사전계획서”가 아니라:

1. 현재 서버 런타임 인벤토리 기록
2. `Nexus`와 `Cognit`의 운영 역할 정리
3. 과거 벤치마크를 아카이브 기준선으로 보존
4. 향후 런타임 교체 시 반복 가능한 재검증 절차 정의

를 목적으로 한다.

## 2. 현재 서버 환경 (2026-03-07 실측)

### 2.1 요약

| 항목 | Cognit | Nexus |
| ------ | ------ | ------ |
| SSH alias | `cognit` | `nexus` |
| 현재 해석 주소 | `100.121.138.74` | `100.124.117.46` |
| GPU | 2x RTX 3080 Ti | 3x RTX 3090 |
| 현재 추론 런타임 | `ollama serve` | `llama-server` |
| 활성 포트 | `11434` | `8080` |
| `vllm` 상태 | inactive / unit 미탐지 | inactive / unit disabled |
| GPU 부하 | 유휴 | `llama-server`가 3장 점유 |
| 현재 보이는 모델 | `qwen3:30b-a3b`, `qwen3.5:27b`, `qwen3:14b`, `exaone3.5:7.8b` 등 | `Qwen3.5-35B-A3B-AWQ-4bit`, `Qwen3-Coder-Next-*` 파일 + `Qwen3.5-122B-A10B` 로드 |

### 2.2 Cognit 현재 상태

- `nvidia-smi -L` 기준 2x RTX 3080 Ti
- `vllm` service는 현재 동작하지 않음
- `~/models` 디렉터리 가시 항목 없음
- `ollama serve`가 실행 중이며 `11434` 포트를 리슨
- `qwen3:30b-a3b`를 포함한 GGUF 모델이 설치되어 있음

현재 역할 해석:

- 빠른 로컬 coder/background
- 저비용 실험용 모델 교체
- `profile` 관점에서는 `coder_fast_local` 계열 후보

### 2.3 Nexus 현재 상태

- `nvidia-smi -L` 기준 3x RTX 3090
- `vllm.service`, `vllm-coder.service`는 disabled 상태
- 현재 활성 런타임은 `/home/hwandam/llama.cpp/build/bin/llama-server`
- `8080` 포트에서 health 응답 정상
- `props` 기준 현재 로드 모델 alias는 `Qwen3.5-122B-A10B-UD-Q3_K_XL-00001-of-00003.gguf`
- `~/models`에는 `Qwen3.5-35B-A3B-AWQ-4bit`, `Qwen3-Coder-Next-*` 계열 아티팩트가 존재

현재 역할 해석:

- 대형 로컬 모델
- 긴 컨텍스트/깊은 추론/대규모 코드 분석
- `profile` 관점에서는 `reasoner_large_local`, `coder_long_local` 계열 후보

## 3. 과거 벤치마크 기준선

과거 벤치마크는 폐기 대상이 아니라 “역사적 기준선”이다.

### 3.1 Nexus DeepSeek-R1 vLLM 기준선

`docs/리포트/nexus_vllm_benchmark_20260205.md` 기준:

- 모델: `DeepSeek-R1-Distill-Llama-70B-AWQ`
- 런타임: `vllm 0.15.0`
- 최적값:
  - `gpu-memory-utilization=0.96`
  - `max-model-len=16384`
  - `max-num-seqs=32`
- 특징:
  - 단일 TPS 약 `33.7 tok/s`
  - 동시 32요청 aggregate 약 `462 tok/s`
  - reasoning/analysis 용도로 강점

### 3.2 Cognit Qwen3 vLLM 기준선

`docs/리포트/cognit_vllm_benchmark_20260205.md` 기준:

- 모델: `Qwen3-Coder-30B-A3B-Instruct-W4A16-awq`
- 런타임: `vllm`
- 최적값:
  - `gpu-memory-utilization=0.93`
  - `max-model-len=16384`
  - `max-num-seqs=8`
- 특징:
  - 단일 TPS 약 `180 tok/s`
  - 동시 8요청 aggregate 약 `1080 tok/s`
  - 빠른 coding/background 용도로 강점

이 두 벤치마크는 지금 당장 live runtime을 설명하지는 않지만, `vllm`을 재도입하거나 비교 평가할 때 재사용할 수 있는 baseline이다.

## 4. 기존 계획이 더 이상 맞지 않는 이유

기존 문서의 주요 전제는 현재 기준으로 수정이 필요하다.

| 기존 전제 | 현재 상태 | 조치 |
| ------ | ------ | ------ |
| `Nexus = DeepSeek-R1 vLLM 서버` | 현재 `llama-server` 기반 Qwen3.5-122B 계열 사용 | `Nexus`를 물리 서버로만 다루고 역할은 profile로 분리 |
| `Cognit = Qwen3 vLLM 서버` | 현재 `Ollama` 기반 GGUF 운영 | `Cognit`를 `coder_fast_local` 후보로 재정의 |
| `GPU 2x RTX 3090` | 실측상 `Nexus`는 3x RTX 3090 | 서버 스펙과 capacity 문서 갱신 필요 |
| `단일 VLLM_ENDPOINT`로 표현 가능 | 현재 `ollama`와 `llama-server`가 공존 | endpoint를 runtime별로 분리 |
| 모델명과 서버명을 라우팅 키로 사용 | 서버·모델·엔진 변경 시 문서와 설정이 같이 깨짐 | `profile alias`와 adapter 계층 도입 |

## 5. 현재 Maestro에 적용할 서버 역할

현재 환경에 맞는 권장 역할은 다음과 같다.

| Profile alias | 현재 물리 서버 | 런타임 | 모델 | 용도 |
| ------ | ------ | ------ | ------ | ------ |
| `coder_fast_primary` | `cognit` | `ollama` | `qwen3:30b-a3b` | 빠른 background, 짧은 coding |
| `reasoner_large_primary` | `nexus` | `llama_cpp` | `Qwen3.5-122B-A10B-UD-Q3_K_XL` | 깊은 추론, 긴 컨텍스트, council 보조 |
| `cloud_default_primary` | cloud API | `openai-compatible` | `glm-4.7` | 기본 구현, 안정적 fallback |
| `cloud_longcontext_primary` | cloud API | `openai-compatible` | `gpt-5.2-codex` | 대규모 컨텍스트 |

핵심 원칙:

- profile 이름은 고정한다.
- 현재는 `coder_fast_primary -> Cognit/Ollama`지만, 나중에 `Nexus/vLLM` 또는 새 서버로 옮겨도 profile 이름은 유지한다.
- 라우터, council wrapper, 문서는 profile 이름을 기준으로 동작한다.

## 6. 유연한 방법: Server Inventory + Runtime Adapter

### 6.1 필요한 이유

현재처럼 `VLLM_ENDPOINT` 하나에 의존하면 다음 변화에 취약하다.

- 서버 교체
- IP 변경
- 런타임 변경 (`vllm` -> `ollama` -> `llama_cpp`)
- 모델 변경
- 역할 재배치 (`Nexus`가 coder, `Cognit`가 reasoner가 되는 경우)

### 6.2 권장 구조

```json
{
  "runtimeInventory": {
    "servers": {
      "cognit": {
        "sshHost": "cognit",
        "host": "100.121.138.74",
        "runtimes": {
          "ollama": "http://100.121.138.74:11434"
        }
      },
      "nexus": {
        "sshHost": "nexus",
        "host": "100.124.117.46",
        "runtimes": {
          "llama_cpp": "http://100.124.117.46:8080",
          "vllm": null
        }
      }
    },
    "profiles": {
      "coder_fast_primary": {
        "server": "cognit",
        "runtime": "ollama",
        "model": "qwen3:30b-a3b"
      },
      "reasoner_large_primary": {
        "server": "nexus",
        "runtime": "llama_cpp",
        "model": "Qwen3.5-122B-A10B-UD-Q3_K_XL"
      }
    }
  }
}
```

### 6.3 adapter 종류

- `openai-compatible`
  - Z.AI, OpenAI, future vLLM OpenAI API
- `vllm`
  - `/v1/models`, `/v1/chat/completions`
- `ollama`
  - `/api/tags`, `/api/chat`
- `llama_cpp`
  - `/health`, `/props`, OpenAI-compatible 여부 확인 후 선택

### 6.4 효과

- 문서와 설정에서 서버명을 직접 박아두지 않는다.
- 새 서버가 생겨도 `profiles`만 바꾸면 된다.
- `Agent Council` wrapper와 router가 같은 inventory를 참조하게 만들 수 있다.

## 7. 재검증 계획

### 7.1 Quick Check

다음은 서버 변경 시 가장 먼저 실행할 경량 점검이다.

1. `ssh alias` 접속 가능 여부
2. 포트 health
3. GPU inventory
4. 현재 로드 모델 확인
5. 1회 샘플 응답

예시:

- Cognit
  - `curl http://HOST:11434/api/tags`
- Nexus
  - `curl http://HOST:8080/health`
  - `curl http://HOST:8080/props`

### 7.2 Full Benchmark

다음 조건 중 하나라도 바뀌면 full benchmark를 다시 수행한다.

- GPU 수/종류 변경
- 드라이버/CUDA 변경
- 런타임 변경
- 모델 변경
- quantization 변경
- `max-model-len`, `gpu-memory-utilization`, `max-num-seqs` 변경

full benchmark 항목:

1. 단일 요청 레이턴시
2. 최대 throughput
3. 동시 요청 스케일링
4. prefix cache 또는 equivalent cache 효과
5. 컨텍스트 길이별 성능
6. 메모리 튜닝
7. GPU 온도/전력/VRAM

### 7.3 결과 저장 규칙

- live check 결과:
  - `docs/work-log/`
- full benchmark 결과:
  - `docs/리포트/<server>_<runtime>_<model>_<date>.md`

기존 `nexus_vllm_benchmark_20260205.md`는 아카이브로 유지하고 덮어쓰지 않는다.

## 8. vLLM 재도입 시 원칙

향후 `Nexus`나 `Cognit`에 `vllm`을 재도입하더라도 기존 문서처럼 “서버명이 곧 vLLM provider명”이 되면 안 된다.

권장 절차:

1. `runtimeInventory.servers.<server>.runtimes.vllm` 등록
2. 새 `profile alias` 생성
   - 예: `coder_fast_vllm_candidate`
3. quick check 수행
4. full benchmark 수행
5. 기존 profile과 비교 후 승격 여부 결정

예:

- `coder_fast_primary`
  - 현재 `cognit/ollama`
- `coder_fast_candidate`
  - 미래 `nexus/vllm`

비교 후 더 나은 쪽을 `primary`로 승격한다.

## 9. 권장 후속 조치

1. `MAESTRO_UPGRADE_PLAN.md`에 `runtimeInventory`와 `profile alias` 구조를 반영한다.
2. `.env.example`의 단일 `VLLM_ENDPOINT`는 장기적으로 분해한다.
   - `COGNIT_OLLAMA_ENDPOINT`
   - `NEXUS_LLAMA_ENDPOINT`
   - `COGNIT_VLLM_ENDPOINT`
   - `NEXUS_VLLM_ENDPOINT`
3. `scripts/status.sh`는 `vLLM - Cognit` 고정 문구를 제거하고 inventory 기반으로 출력한다.
4. `Agent Council` wrapper는 물리 서버명이 아니라 profile alias를 입력으로 받는다.

## 10. 산출물

- 현재 문서
- 과거 기준선 리포트
  - `docs/리포트/nexus_vllm_benchmark_20260205.md`
  - `docs/리포트/cognit_vllm_benchmark_20260205.md`
- 후속 작업 후보
  - inventory schema 초안
  - status script 개편안
  - profile alias 기반 council wrapper 설계

## 11. 결론

현재 기준으로 `Nexus`와 `Cognit`는 더 이상 “vLLM 서버 2대”가 아니다. `Cognit`은 `Ollama` 기반의 빠른 로컬 추론 노드, `Nexus`는 `llama-server` 기반의 대형 로컬 모델 노드로 보는 것이 맞다. 따라서 앞으로의 계획은 특정 서버와 특정 엔진을 고정하는 방식이 아니라, `server inventory -> runtime adapter -> profile alias` 구조로 바꿔야 한다.

이 방식이면 이후 서버가 바뀌거나, `vllm`이 돌아오거나, 새 GPU 노드가 추가돼도 문서와 라우팅 정책을 최소 수정으로 유지할 수 있다.
