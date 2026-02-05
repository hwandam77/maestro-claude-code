# Claude Code + vLLM 통합 테스트 리포트

**작성일**: 2026-02-03
**작성자**: AI Assistant + hwandam
**상태**: ✅ 통합 테스트 성공

---

## 1. 개요

### 목표

Nexus 서버 (2x RTX 3090, 48GB VRAM)에서 vLLM 추론 서버를 운영하고, Claude Code를 로컬 vLLM 서버와 연동하여 자체 호스팅 AI 코딩 어시스턴트를 구축한다.

### 최종 구성

```
Docker Container (claude-vllm:local)
  └─ Claude Code 2.1.29
       └─ ANTHROPIC_BASE_URL=http://host.docker.internal:8000
            └─ SSH Tunnel (localhost:8000 → 192.168.0.14:8000)
                 └─ vLLM 0.15.0 (Qwen3-Coder-30B-A3B AWQ)
                      └─ RTX 3090 x2 (Tensor Parallel, 48GB VRAM)
```

---

## 2. FP8 모델 호환성 문제 분석

### 문제 현상

- Qwen3-30B-A3B-FP8 모델 실행 시 CUDA device-side assert 크래시
- 42K 토큰 프롬프트에서 "!!!!" 가비지 출력 (vLLM issue #22881)
- 43K+ 토큰 + 4096 completion에서 서버 크래시 및 VPN 연쇄 장애

### 근본 원인

| 항목 | 설명 |
|------|------|
| GPU 아키텍처 | RTX 3090 = Ampere (compute capability 8.6) |
| FP8 요구사항 | compute capability > 8.9 (Ada Lovelace/Hopper) |
| Fallback 동작 | W8A16 via Marlin 커널 (불완전) |
| 핵심 비호환 | Block-wise FP8 + MoE 조합이 Ampere에서 미지원 |
| KV Cache | FP8 KV cache도 Ampere에서 미지원 |

### 결론

RTX 3090에서 FP8 + MoE 모델은 근본적 호환성 문제 존재. AWQ INT4 양자화로 전환 필요.

---

## 3. AWQ 모델 전환

### 선택 모델

| 항목 | 값 |
|------|-----|
| 모델명 | nm-testing/Qwen3-Coder-30B-A3B-Instruct-W4A16-awq |
| 크기 | 16GB (FP8 31GB 대비 절반) |
| 양자화 | compressed-tensors (W4A16 AWQ) |
| 구조 | MoE: 30B 총 파라미터, 3B 활성 파라미터 |
| 커널 | CompressedTensorsWNA16MarlinMoEMethod |
| 모델 로딩 메모리 | 7.84 GiB |

### vLLM 시작 설정

```bash
exec python -m vllm.entrypoints.openai.api_server \
  --model /home/hwandam/models/Qwen3-Coder-30B-A3B-Instruct-W4A16-awq \
  --served-model-name Qwen3-Coder-30B-A3B \
  --tensor-parallel-size 2 \
  --max-model-len 65536 \
  --max-num-seqs 32 \
  --max-num-batched-tokens 4096 \
  --gpu-memory-utilization 0.95 \
  --enable-prefix-caching \
  --enable-chunked-prefill \
  --disable-custom-all-reduce \
  --enable-auto-tool-choice \
  --tool-call-parser hermes \
  --trust-remote-code \
  --host 0.0.0.0 --port 8000
```

핵심 변경:
- `--enforce-eager` 제거 (AWQ는 CUDA graph 지원)
- `--quantization` 미지정 (compressed-tensors 자동 감지)

---

## 4. 스트레스 테스트 결과

### 성능 측정

| 테스트 | 프롬프트 토큰 | 완료 토큰 | 시간 | 속도 | 결과 |
|--------|-------------|----------|------|------|------|
| 기본 코딩 질문 | 24 | 107 | 0.73s | 146 tok/s | ✅ 성공 |
| 10K 토큰 | 10,514 | 200 | 3.2s | 63 tok/s | ✅ 성공 |
| 42K 토큰 (Claude Code 크기) | 42,558 | 2,048 | 20.8s | 98.6 tok/s | ✅ 성공 |

### GPU 상태 (테스트 후)

| GPU | 메모리 사용 | 온도 |
|-----|-----------|------|
| GPU 0 | 23,908 / 24,576 MiB (97.3%) | 53°C |
| GPU 1 | 23,908 / 24,576 MiB (97.3%) | 57°C |

### FP8 vs AWQ 비교

| 항목 | FP8 (이전) | AWQ (현재) |
|------|-----------|-----------|
| 모델 크기 | 31GB | 16GB |
| 기본 속도 | 134 tok/s | 63-99 tok/s |
| 43K 토큰 처리 | ❌ CUDA 크래시 | ✅ 성공 (20.8초) |
| 출력 품질 | "!!!!" 가비지 | 깨끗한 코드 |
| 장시간 안정성 | ❌ 반복 크래시 | ✅ 안정 |

---

## 5. 네트워크 구성

### VPN 불안정 문제

- vLLM 크래시 후 WireGuard VPN (10.5.5.0/24) 반복 끊김
- 해결: SSH Jump 방식으로 우회

### SSH 터널 구성

```bash
ssh -f -N -L 8000:192.168.0.14:8000 \
  -J trading@10.5.5.11 hwandam@192.168.0.14 \
  -o ServerAliveInterval=30 -o ServerAliveCountMax=3
```

```
Mac (localhost:8000)
  → SSH Jump (trading@10.5.5.11)
    → Nexus (192.168.0.14:8000)
```

### Docker 네트워크

- `host.docker.internal` → Mac 호스트 → SSH 터널 → vLLM
- `extra_hosts: host.docker.internal:host-gateway` 설정 필요

---

## 6. Claude Code + vLLM Docker 통합

### 핵심 발견

- **vLLM 0.15.0은 Anthropic Messages API (`/v1/messages`)를 네이티브 구현**
- LiteLLM 프록시 불필요 - vLLM이 직접 Anthropic 형식 요청/응답 처리
- Claude Code의 `ANTHROPIC_BASE_URL` 환경변수로 간단히 연동 가능

### Docker 환경 변수

```bash
ANTHROPIC_BASE_URL=http://host.docker.internal:8000
ANTHROPIC_API_KEY=dummy
ANTHROPIC_AUTH_TOKEN=dummy
ANTHROPIC_DEFAULT_OPUS_MODEL=Qwen3-Coder-30B-A3B
ANTHROPIC_DEFAULT_SONNET_MODEL=Qwen3-Coder-30B-A3B
ANTHROPIC_DEFAULT_HAIKU_MODEL=Qwen3-Coder-30B-A3B
```

### Dockerfile

```dockerfile
FROM node:22-slim
RUN apt-get update && apt-get install -y curl git python3 ripgrep && rm -rf /var/lib/apt/lists/*
RUN npm install -g @anthropic-ai/claude-code
RUN mkdir -p /workspace /root/.claude
WORKDIR /workspace
ENV ANTHROPIC_BASE_URL=http://host.docker.internal:8000
ENV ANTHROPIC_API_KEY=dummy
ENV ANTHROPIC_AUTH_TOKEN=dummy
ENV ANTHROPIC_DEFAULT_OPUS_MODEL=Qwen3-Coder-30B-A3B
ENV ANTHROPIC_DEFAULT_SONNET_MODEL=Qwen3-Coder-30B-A3B
ENV ANTHROPIC_DEFAULT_HAIKU_MODEL=Qwen3-Coder-30B-A3B
CMD ["claude"]
```

### 통합 테스트 결과

| 테스트 | 결과 |
|--------|------|
| Anthropic Messages API 호환성 | ✅ 성공 (깨끗한 코드 생성) |
| Claude Code `-p` 비대화형 모드 | ✅ 성공 (palindrome checker 생성) |
| 파일 작성 도구 호출 | ✅ 정상 동작 |

---

## 7. OpenClaw 에이전트 설정 업데이트

### 변경 사항 (openclaw.json)

| 항목 | 이전 | 현재 |
|------|------|------|
| provider baseUrl | `http://10.5.5.14:8000/v1` | `http://host.docker.internal:8000/v1` |
| model id | `Qwen2.5-Coder-32B-Instruct-AWQ` | `Qwen3-Coder-30B-A3B` |
| contextWindow | 32768 | 65536 |
| agent model | `local-vllm/Qwen2.5-Coder-32B-Instruct-AWQ` | `local-vllm/Qwen3-Coder-30B-A3B` |

### 미해결 이슈

- OpenClaw 게이트웨이 Docker 컨테이너 OOM-Killed 반복
- Docker Desktop 메모리 할당 증가 필요

---

## 8. 파일 위치 참조

### 로컬 (Mac)

| 파일 | 경로 |
|------|------|
| Docker 프로젝트 | `/Users/hwandam/system/Web_server/claude-vllm/` |
| OpenClaw 설정 | `~/.openclaw/openclaw.json` |

### 원격 서버 (Nexus, 192.168.0.14)

| 파일 | 경로 |
|------|------|
| vLLM 시작 스크립트 | `~/server_setting/vllm-start.sh` |
| 백업 (Qwen2.5-Coder) | `~/server_setting/vllm-start.sh.bak_qwen25` |
| 백업 (76800 버전) | `~/server_setting/vllm-start.sh.bak_76800` |
| 백업 (FP8 버전) | `~/server_setting/vllm-start.sh.bak_fp8` |
| 현재 모델 (AWQ) | `~/models/Qwen3-Coder-30B-A3B-Instruct-W4A16-awq/` (16GB) |
| 비활성 모델 (FP8) | `~/models/Qwen3-30B-A3B-FP8/` (31GB) |
| 비활성 모델 (Qwen2.5) | `~/models/Qwen2.5-Coder-32B-Instruct-AWQ/` (19GB) |
| 비활성 모델 (72B) | `~/models/Qwen2.5-72B-Instruct-AWQ/` (39GB) |
| vLLM 로그 | `~/vllm-server-new.log` |

---

## 9. 남은 작업

| 우선순위 | 작업 | 설명 |
|---------|------|------|
| 높음 | VPN 안정화 | WireGuard VPN이 vLLM 크래시 시 끊기는 문제 근본 해결 |
| 높음 | SSH 터널 자동화 | 부팅 시 자동 SSH 터널 생성 (launchd) |
| 중간 | OpenClaw OOM 해결 | Docker Desktop 메모리 증가 또는 경량화 |
| 중간 | Claude Code 대화형 테스트 | TTY 환경에서 실제 대화형 코딩 세션 테스트 |
| 낮음 | 성능 튜닝 | max-model-len, max-num-seqs 최적화 |
| 낮음 | systemd 버그 수정 | vllm.service ExecStop의 $MAINPID 버그 |

---

## 10. 결론

RTX 3090 x2 환경에서 FP8 모델의 근본적 호환성 문제를 진단하고, AWQ INT4 모델(Qwen3-Coder-30B-A3B)로 전환하여 43K+ 토큰 장문 프롬프트에서도 안정적으로 동작하는 것을 확인했다. vLLM 0.15.0의 네이티브 Anthropic Messages API 지원을 활용하여 별도 프록시 없이 Claude Code와 직접 연동에 성공했으며, Docker 기반 재현 가능한 환경을 구축했다.
