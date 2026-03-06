# 🎼 Maestro Claude Code - Overture Setup

## 5-Model Orchestra System

**Maestro Claude Code**는 5 개의 LLM 모델을 오케스트라처럼 협업시키는 하이브리드 에이전트 라우팅 시스템입니다.

### 🎻 모델 구성

| 역할 | 모델 | 용도 | 사용률 |
|------|------|------|--------|
| 🎼 **Maestro** | Claude Opus 4.5 | 전략 수립, 아키텍처 설계, 품질 검증 | 10% |
| 🎻 **Concertmaster** | GLM-4.7 (Z.AI) | 핵심 코드 구현, 비즈니스 로직 | 30% |
| 🎹 **Principal** | GPT-5.2 Codex | 대규모 컨텍스트 처리 (60K+ tokens) | 5% |
| 🥁 **Ensemble** | Qwen3-Coder-30B (vLLM) | 반복 작업, 파일 조작, 배경 실행 | 25% |
| 🎺 **Soloist** | **Qwen3.5-122B (vLLM)** | **고급 코딩, 복잡한 로직, 빠른 응답** | **30%** |

---

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 환경 변수 파일 생성
cp .env.example .env

# .env 파일에서 API 키 설정
# - ANTHROPIC_API_KEY: Claude Opus 용 (선택사항, claude login 사용시 불필요)
# - ZAI_API_KEY: GLM-4.7 용
# - OPENAI_API_KEY: GPT-5.2 용
# - VLLM_ENDPOINT: Qwen3-Coder-30B 서버 엔드포인트
# - VLLM_QWEN35_ENDPOINT: Qwen3.5-122B 서버 엔드포인트
```

### 2. 라우터 시작

```bash
# 라우터 + Claude Code 시작
./scripts/start.sh

# 또는 수동으로:
source .env
ccr start --config config/config.json &
eval "$(ccr activate)" && claude
```

### 3. Zed 에서 사용

Zed 터미널에서:
```bash
# 라우터 시작
cd maestro-claude-code
source .env
./scripts/start.sh
```

그 후 Zed 의 채팅 인터페이스에서 에이전트 태그 사용:
```
@architect 새로운 REST API 아키텍처를 설계해줘.
@coder src/api/handler.ts 파일을 구현해줘.
@orchestrator 전체적인 프로젝트 구조를 만들어줘.
```

---

## 📋 에이전트 태그 가이드

### Opus (Maestro) - 전략/설계 에이전트

**사용 예시**:
```
@architect 새로운 마이크로서비스 아키텍처 설계
@planner 프로젝트 마일스톤 계획 수립
@critic 기존 코드베이스 리팩토링 검토
@analyst 성능 병목 지점 분석
@designer UI/UX 디자인 시스템 설계
@orchestrator 복잡한 워크플로우 오케스트레이션
@security-reviewer 보안 취약점 분석
@code-reviewer 코드 리뷰 및 개선 제안
```

**모델**: Claude Opus 4.5 (또는 ZAI 의 GLM-4.7)  
**용도**: 고차원적 사고가 필요한 작업, 전략 수립, 설계, 검토

---

### Concertmaster (Sonnet) - 핵심 구현 에이전트

**사용 예시**:
```
@executor 주요 기능 구현
@researcher 기술 스택 조사 및 추천
@frontend-specialist React/Vue 컴포넌트 개발
@backend-specialist REST API, 마이크로서비스 구현
@database-specialist DB 스키마 설계 및 쿼리 최적화
@tdd-guide TDD 방식으로 테스트 코드 작성
@build-fixer 빌드 에러 수정
```

**모델**: GLM-4.7 (Z.AI)  
**용도**: 복잡한 비즈니스 로직, 핵심 기능 구현

---

### Soloist (Qwen3.5-122B) - 고급 코딩 에이전트 ⭐ NEW

**사용 예시**:
```
@coder 복잡한 알고리즘 구현
@codexpert 대규모 리팩토링
@code-builder 빌드 스크립트 작성
@implementation-specialist 세부 구현 최적화
@refactor-specialist 코드 리팩토링
@debug-specialist 디버깅 및 에러 수정
@test-creator 단위/통합 테스트 작성
@api-creator API 엔드포인트 생성
@file-manager 파일 시스템 작업
@code-modifier 코드 수정 및 개선
```

**모델**: Qwen3.5-122B (vLLM)  
**용도**: 고급 코딩 작업, 복잡한 로직 구현, 빠른 응답이 필요한 작업

**특징**:
- **122B 파라미터**로 높은 코딩 능력
- **32K 토큰 컨텍스트** 지원
- **빠른 응답 속도** (vLLM 최적화)
- **복잡한 알고리즘** 구현에 최적

---

### Haiku (Ensemble) - 반복 작업 에이전트

**사용 예시**:
```
@executor-low 간단한 파일 수정
@researcher-low 빠른 정보 검색
@task-executor 단일 작업 수행
@dependency-resolver 의존성 해결
@impact-analyzer 변경 사항 영향 분석
```

**모델**: Qwen3-Coder-30B (vLLM)  
**용도**: 반복 작업, 빠른 응답이 필요한 간단한 작업

---

## 🔧 아키텍처

### 라우팅 흐름

```
사용자 요청 → claude-code-router (port 3456)
                    ↓
            custom-router.js (에이전트 감지)
                    ↓
    ┌───────────────┼───────────────┬───────────────┐
    ↓               ↓               ↓               ↓
  opus          sonnet        soloist         haiku
(Opus 4.5)    (GLM-4.7)    (Qwen3.5-122B)  (Qwen3-Coder)
  10%           30%             30%            25%
```

### 폴백 체인

```
Soloist (Qwen3.5-122B) 장애 → Concertmaster (GLM-4.7) 대행
Haiku (Qwen3-Coder) 장애 → Concertmaster (GLM-4.7) 대행
Concertmaster (GLM-4.7) 장애 → Maestro (Opus) 폴백
Principal (GPT-5.2) 장애 → Maestro (Opus) 200K 대체
```

---

## 📝 사용 예제

### 시나리오 1: 새로운 REST API 개발

```
# 1. Opus 가 아키텍처 설계
@architect 새로운 사용자 관리 REST API 아키텍처를 설계해줘.
- 기술 스택: Node.js, Express, PostgreSQL
- 요구사항: JWT 인증, RBAC, OpenAPI 문서

# 2. Opus 가 Qwen3.5-122B 에 구현 위임
@coder 아래 아키텍처대로 src/api/users.ts 구현해줘.
[Opus 가 생성한 아키텍처 내용...]

# 3. Opus 가 코드 검증
@critic @coder 가 구현한 src/api/users.ts 코드 리뷰해줘.
```

### 시나리오 2: 대규모 리팩토링

```
# 1. Opus 가 전략 수립
@planner 레거시 모놀리식 앱을 마이크로서비스로 전환하는 계획 수립

# 2. Soloist 가 개별 서비스 구현
@codexpert src/service-a 폴더의 비즈니스 로직을 분리해서 micro-service-a 로 변환

# 3. Ensemble 이 파일 정리
@file-manager 리팩토링 후 사용되지 않는 import 정리

# 4. Opus 가 최종 검증
@security-reviewer 새 마이크로서비스 보안 검토
```

---

## 🔍 진단 및 모니터링

### 헬스체크

```bash
# 라우터 헬스체크
curl http://127.0.0.1:3456/health

# vLLM 서버 상태 확인
curl http://127.0.0.1:8000/v1/models
```

### 로그 확인

```bash
# 라우터 로그
tail -f ~/.claude-code-router/logs/router.log

# vLLM 로그
tail -f /path/to/vllm/logs/server.log
```

---

## ⚠️ 주의사항

### Qwen3.5-122B 제약 사항

- **32K 토큰 제한**: 32,000 토큰 초과 시 자동 에스컬레이션
- **1T1F 원칙**: One Task, One File (대규모 파일은 분할 처리)
- **vLLM 의존성**: vLLM 서버 가동 필요 (VPN 접속 필요할 수 있음)

### GLM-4.7 동시성 제한

- `GLM_MAX_CONCURRENCY = 1` (순차 처리 강제)
- 병렬 작업 시 Soloist(Quwen3.5-122B) 또는 Ensemble(Qwen3-Coder) 우선 사용

---

## 📚 추가 리소스

- [claude-code-router GitHub](https://github.com/musistudio/claude-code-router)
- [vLLM 문서](https://docs.vllm.ai)
- [Qwen3.5 모델 카드](https://huggingface.co/Qwen/Qwen3.5-122B-Instruct)
- [GLM-4.7 API 문서](https://docs.z.ai)

---

## 🤝 기여 방법

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

**Made with ❤️ by hwandam77**