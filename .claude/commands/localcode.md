# /localcode - Qwen3-Coder-30B로 경량 코드 생성

Qwen3-Coder-30B (cognit 서버, 20K context)에 간단한 코드 생성 태스크를 위임합니다.

## 사용법
```
/localcode 피보나치 함수 작성
/localcode 간단한 정렬 알고리즘
/localcode JSON 파싱 유틸리티
```

## 실행 방법

다음 bash 명령을 실행하세요:

```bash
cd /Users/hwandam/workspace/maestro-claude-code && ./scripts/maestro-route.sh --type localcode "$ARGUMENTS"
```

$ARGUMENTS 자리에 사용자가 입력한 태스크 설명을 그대로 넣으세요.
