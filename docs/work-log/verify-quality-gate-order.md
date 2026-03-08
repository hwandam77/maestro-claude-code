# Verify / Quality Gate 순서 (B4)

## 게이트 실행 순서

모든 태스크 완료 후, 아래 순서로 품질 게이트를 통과해야 한다.

### 1. Pre-Dispatch Gate (태스크 실행 전)

```
policy-gate.js    → 권한 + 코딩 표준 확인
risk-gate.js      → 영향도 + 위험도 평가
```

### 2. Post-Task Gate (태스크 완료 후)

```
contract-gate.js  → API 계약 준수 검증
quality-gate.js   → 빌드/타입/린트/테스트 통과
security-scan.js  → 보안 취약점 스캔
task-sync.js      → TASKS.md 상태 업데이트
```

### 3. Phase/Layer Barrier Gate (Phase 전환 시)

```
build             → 프로젝트 컴파일
types             → 타입 체커 (mypy/tsc)
lint              → 린팅 위반 없음
test              → 전체 테스트 통과, coverage >= 80%
security          → 시크릿 하드코딩 없음
console-cleanup   → console.log / print() 제거
```

### 4. Final Gate (PR/완료 선언 전)

```
/quality-auditor  → 종합 품질 감사
/multi-ai-review  → 멀티 AI 코드 리뷰 (council)
architect 검증     → 아키텍처 정합성 최종 확인
```

## Hook 프로파일 매핑

| 프로파일 | 게이트 | 용도 |
|----------|--------|------|
| lite     | policy + quality | 단순 변경, 핫픽스 |
| standard | policy + risk + quality + security + task-sync | 일반 개발 (기본값) |
| full     | 전체 게이트 체인 | 대규모 기능, 배포 전 |

## 현재 설정: standard (7 agents + 4 hooks)

적용 hooks: `contract-gate`, `quality-gate`, `security-scan`, `task-sync`
