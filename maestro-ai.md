# Maestro 멀티 AI 자동 라우팅

이 디렉토리에서 `claude-glm` 실행 시 태스크가 자동으로 최적 AI로 라우팅됩니다.

## AI 역할 분담 (2026-03-09 기준)

### 오케스트레이터
- **Claude** (`claude`): 전체 계획 수립, 아키텍처 설계, 에이전트 조율, 복잡한 의사결정, 보안 리뷰
- **GLM-5** (`claude-glm`): Claude 대체 오케스트레이터. 비용 절감 대화/질의, 문서 작성, 간단한 분석

### 위임 대상 (maestro-route로 라우팅)

| AI | 역할 | 언제 사용 |
|----|------|----------|
| **Qwen3-Coder-30B** (cognit) | 코드 구현 전문 | API 개발, 버그 수정, 테스트 작성, 리팩토링, 스니펫 |
| **Gemini** (Google) | UI/UX 디자인 | 컴포넌트 설계, CSS, 프론트엔드, 이미지 분석 |
| **Qwen3.5-122B** (nexus) | 대용량 분석 | 코드베이스 파악, 문서 요약, 400K 컨텍스트 처리 |

---

## 자동 라우팅 규칙 (CRITICAL)

**코드/디자인/분석 태스크는 직접 처리하지 말고 반드시 `maestro-route`로 위임하세요.**

```bash
maestro-route --type code "태스크"      # 코드 구현, 버그 수정, API, 테스트
maestro-route --type design "태스크"    # UI/UX, CSS, 컴포넌트, 프론트엔드
maestro-route --type analyze "태스크"   # 코드베이스 분석, 문서 요약, 대용량 처리
maestro-route --type localcode "태스크" # 간단한 함수, 스니펫
maestro-route "태스크"                  # 타입 자동 감지
```

### 판단 기준

| 태스크 | 타입 | 대상 AI |
|--------|------|---------|
| JWT 인증 API 구현 | `code` | Qwen3-Coder-30B |
| React 컴포넌트 디자인 | `design` | Gemini |
| 전체 코드베이스 분석 | `analyze` | Qwen3.5-122B |
| 정렬 함수 작성 | `localcode` | Qwen3-Coder-30B |
| 타입 불명확 | (없음) | 자동 감지 |

### 직접 처리 가능한 경우
- 아키텍처 설계, 기술 전략, 복잡한 의사결정
- 여러 AI 결과 통합 및 최종 검토
- 보안 리뷰, 코드 품질 판단

---

## 사용 예시

```
"JWT 인증 API 만들어줘"
→ maestro-route --type code "JWT 인증 미들웨어 구현"

"대시보드 UI 디자인해줘"
→ maestro-route --type design "대시보드 UI 컴포넌트 설계"

"이 프로젝트 구조 파악해줘"
→ maestro-route --type analyze "프로젝트 아키텍처 분석"

"배열 정렬 함수 짜줘"
→ maestro-route --type localcode "배열 정렬 함수 작성"
```
