# /route - 자동 AI 라우팅

태스크를 분석하여 최적의 AI CLI로 자동 라우팅합니다.

| 타입 | 라우팅 대상 |
|------|------------|
| 코드 구현/리뷰/테스트 | codex |
| UI/디자인/프론트엔드 | gemini |
| 대용량 분석 (400K) | qwen35 (nexus) |
| 간단한 코드 생성 | qwen-coder (cognit) |

## 사용법
```
/route 로그인 API 구현해줘
/route 대시보드 UI 만들어줘
/route 이 코드베이스 전체 분석
```

## 실행 방법

다음 bash 명령을 실행하세요 (타입 자동 감지):

```bash
cd /Users/hwandam/workspace/maestro-claude-code && ./scripts/maestro-route.sh "$ARGUMENTS"
```

$ARGUMENTS 자리에 사용자가 입력한 태스크 설명을 그대로 넣으세요.
