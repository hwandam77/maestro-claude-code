# /code - Codex로 코드 태스크 라우팅

codex (gpt-5.3-codex)에 코드 구현/리뷰/테스트 태스크를 위임합니다.

## 사용법
```
/code 로그인 API 구현
/code JWT 토큰 검증 함수 작성
/code 테스트 코드 작성
```

## 실행 방법

다음 bash 명령을 실행하세요:

```bash
cd /Users/hwandam/workspace/maestro-claude-code && ./scripts/maestro-route.sh --type code "$ARGUMENTS"
```

$ARGUMENTS 자리에 사용자가 입력한 태스크 설명을 그대로 넣으세요.
