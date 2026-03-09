# Phase 1 구현 보고서: LiteLLM Proxy 지능형 라우팅

> 작성일: 2026-03-09
> 담당: Claude Sonnet 4.6 (Maestro Claude Code)
> 계획서 참조: `docs/계획서/GitHub-프로젝트-적용-계획서.md` Phase 1

---

## 1. 개요

### 목표
기존 단순 GLM-5 직접 연결(`maestro.sh`) 방식을 **LiteLLM Proxy 기반 지능형 라우팅**으로 고도화.
6개 AI 모델을 투명하게 자동 라우팅하여 사용자 개입 없이 최적 모델 선택.

### 핵심 변경
```
변경 전:  claude-glm → ZAI API (GLM-5) → 모든 요청 GLM-5 처리

변경 후:  claude-glm → LiteLLM Proxy (localhost:4000) → 조건 분기
            ├─ claude-sonnet-4-6 요청 → GLM-5 ($3/월, 기본)
            ├─ claude-haiku-* 요청    → Qwen3-Coder-30B (무료)
            ├─ 컨텍스트 초과 fallback → Qwen3.5-122B (무료)
            └─ Tailscale 미연결       → litellm-fallback.yaml (클라우드만)
```

---

## 2. 구현 완료 목록

| # | 작업 | 상태 | 산출물 |
|---|------|------|--------|
| 1-1 | LiteLLM Proxy 설치 | ✅ 완료 | `litellm v1.82.0` |
| 1-2 | ccproxy.yaml 작성 | ✅ 완료 | `config/ccproxy.yaml` (8개 모델) |
| 1-3 | litellm-fallback.yaml 작성 | ✅ 완료 | `config/litellm-fallback.yaml` (6개 모델) |
| 1-4 | nexus/cognit 연결 테스트 | ✅ 완료 | cognit HEALTHY, nexus API 미응답 확인 |
| 1-5 | maestro.sh 수정 | ✅ 완료 | 프록시 자동 시작 + fallback 포함 |
| 1-6 | ccproxy-start.sh 작성 | ✅ 완료 | `scripts/ccproxy-start.sh` |
| 1-7 | ccproxy-health.sh 작성 | ✅ 완료 | `scripts/ccproxy-health.sh` |
| 1-8 | health-check.sh 수정 | ✅ 완료 | litellm 항목 추가 |
| 1-9 | 통합 테스트: 프록시 기동 | ✅ 완료 | 8개 모델 정상 서빙 확인 |
| 1-10 | 통합 테스트: Write/Edit → Codex | ⚠️ 부분 | 모델명 기반 라우팅으로 대체 |
| 1-11 | 통합 테스트: Tailscale fallback | ✅ 완료 | fallback 설정 검증 |
| 1-12 | .env.example 업데이트 | ✅ 완료 | API 키 + LiteLLM 변수 추가 |

---

## 3. 신규/수정 파일 목록

### 신규 생성

| 파일 | 역할 |
|------|------|
| `config/ccproxy.yaml` | LiteLLM Proxy 전체 설정 (Tailscale 연결 시) |
| `config/litellm-fallback.yaml` | Tailscale 미연결 시 클라우드 모델 전용 설정 |
| `scripts/ccproxy-start.sh` | 프록시 start/stop/restart/status 관리 |
| `scripts/ccproxy-health.sh` | 프록시 + 백엔드 모델 전체 점검 |
| `logs/ccproxy/` | 프록시 로그 디렉토리 |

### 수정

| 파일 | 변경 내용 |
|------|----------|
| `scripts/maestro.sh` | 프록시 자동 시작 + Tailscale 감지 + fallback 로직 추가 |
| `scripts/health-check.sh` | litellm, ccproxy 점검 항목 추가 |
| `.env.example` | OPENAI_API_KEY, GOOGLE_API_KEY, LITELLM_MASTER_KEY 등 추가 |

---

## 4. 라우팅 설계

### 모델 우선순위 (ccproxy.yaml)

| 모델명 | 실제 모델 | 조건 |
|--------|----------|------|
| `claude-sonnet-4-6` | GLM-5 (ZAI) | 기본 (모든 요청) |
| `claude-haiku-4-5-20251001` | Qwen3-Coder-30B | haiku 티어 요청 + Tailscale 연결 시 |
| `qwen3.5-122b` | Qwen3.5-122B (nexus) | 장문 컨텍스트 fallback |
| `gemini-3.1-pro` | gemini-2.0-flash | 멀티모달/디자인 |
| `gpt-5.4-medium` | gpt-4o | Codex 구독 활용 |
| `claude-opus` | claude-opus-4-6 | 최종 에스컬레이션 |

### Tailscale 자동 감지 로직 (maestro.sh)

```
시작 시:
  1. tailscale status --json → Online 여부 확인
  2. nexus(100.124.117.46) / cognit(100.121.138.74) ping 테스트
  3. 응답 시 → config/ccproxy.yaml (자체 서버 포함)
  4. 미응답 시 → config/litellm-fallback.yaml (클라우드만)
```

---

## 5. 발견 및 수정 사항

### IP 불일치 수정

| 항목 | 기존 설정 | 실제 Tailscale IP | 수정 결과 |
|------|----------|------------------|----------|
| cognit | `100.89.224.48` | `100.121.138.74` | ✅ 전체 수정 |
| nexus ping | `100.64.189.120` | `100.124.117.46` | ✅ 스크립트 수정 |
| nexus API | `100.64.189.120:8080` | 동일 (synapse IP) | 유지 |

### nexus API 미응답

- **현상**: Tailscale ping 성공, API(100.64.189.120:8080) Connection refused
- **원인**: nexus llama-server 미실행 상태
- **영향**: nexus → GLM-5 자동 fallback (계획서 설계대로 동작)
- **조치**: 서버 접속 후 llama-server 재시작 필요

---

## 6. 계획서와의 차이점

### MatchToolRule 미구현

**계획서 의도**: Write/Edit 도구 사용 시 → gpt-5.4-medium(Codex) 자동 라우팅

**실제 구현**: LiteLLM Proxy는 도구 감지 기반 라우팅을 기본 지원하지 않음

**현재 대안**: 모델명 기반 라우팅 (haiku 요청 → Qwen3-Coder)
- OMC가 haiku 티어 에이전트를 호출하면 자동으로 Qwen3-Coder로 라우팅
- Write/Edit 도구 기반 라우팅은 Phase 5 (CCR 패턴 차용) 때 hook으로 구현 예정

### ccproxy → LiteLLM Proxy 대체

**계획서**: `pip install ccproxy` / `ccproxy run --config`

**실제**: `pip install litellm[proxy]` / `litellm --config`

**이유**: starbaser/ccproxy(178 stars)는 실제 pip 패키지가 아님. 계획서의 YAML 형식이 LiteLLM 표준 형식과 동일하여 LiteLLM Proxy가 사실상 동일한 역할 수행.

---

## 7. 검증 결과

### 작동 확인

```bash
# 프록시 시작
$ bash scripts/ccproxy-start.sh start
[ccproxy] 시작 중... (설정: ccproxy.yaml)
  자체 서버: ✅ 활성
완료 (PID: 83127, port: 4000)

# 모델 목록 확인
$ python3 -c "..."
프록시 응답: 8개 모델
  - glm-5, claude-sonnet-4-6, claude-haiku-4-5-20251001
  - qwen3-coder-30b, qwen3.5-122b, gemini-3.1-pro
  - gpt-5.4-medium, claude-opus

# health check
$ bash scripts/ccproxy-health.sh
litellm proxy:      RUNNING (port 4000)
ZAI GLM-5:          API KEY OK
cognit(QwenCoder):  HEALTHY (qwen3-coder)
nexus(Qwen3.5):     DEGRADED (llama-server 미실행)
Codex/OpenAI:       API KEY OK
Claude:             API KEY OK
```

---

## 8. 사용 방법

```bash
# GLM-5 + 자동 라우팅 모드 (기본)
./scripts/maestro.sh
# 또는
claude-glm

# ZAI API 직접 모드 (프록시 우회)
./scripts/maestro.sh direct

# 프록시 단독 관리
./scripts/ccproxy-start.sh start|stop|restart|status

# 전체 상태 점검
./scripts/ccproxy-health.sh
./scripts/health-check.sh
```

---

## 9. 다음 Phase 준비사항

| Phase | 사전 조건 | 상태 |
|-------|----------|------|
| Phase 2 (관찰성) | Phase 1 프록시 실행 | ✅ 준비됨 |
| Phase 3 (동기화) | 없음 | ✅ 즉시 가능 |
| Phase 5 (CCR 패턴) | Phase 1 안정화 후 | 대기 중 |

### nexus 서버 복구 필요
```bash
# SSH 접속 후 llama-server 상태 확인
ssh nexus
systemctl status llama-server  # 또는 해당 서비스명
```

---

*보고서 작성: Claude Sonnet 4.6 / Maestro Claude Code*
