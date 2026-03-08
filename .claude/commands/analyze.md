# /analyze - Qwen3.5-122B로 대용량 분석 라우팅

Qwen3.5-122B (nexus 서버, 400K context)에 대용량/장문 분석 태스크를 위임합니다.

## 사용법
```
/analyze 이 코드베이스의 아키텍처를 분석해줘
/analyze 이 문서 전체 요약
/analyze 성능 병목 분석
```

## 실행 방법

다음 bash 명령을 실행하세요:

```bash
cd /Users/hwandam/workspace/maestro-claude-code && ./scripts/maestro-route.sh --type analyze "$ARGUMENTS"
```

$ARGUMENTS 자리에 사용자가 입력한 태스크 설명을 그대로 넣으세요.
