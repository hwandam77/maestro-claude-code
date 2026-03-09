# Phase 3 - 크로스 도구 설정 동기화 구현 보고서

**작성일**: 2026-03-09
**구현 방식**: 순수 bash 심볼릭 링크

---

## 동기화 경로 목록

| 방향 | 소스 | 대상 |
|------|------|------|
| Claude → Codex | `~/.claude/skills/` | `~/.codex/skills/` |
| Claude → Codex | `~/.claude/commands/` | `~/.codex/commands/` |
| Claude → Gemini | `~/.claude/skills/` | `~/.gemini/skills/` |

- Gemini commands: 동기화 없음 (Gemini CLI 미지원)
- Qwen CLI: OpenAI 호환 API만 사용, 별도 CLI 없으므로 제외

---

## 생성된 심볼릭 링크 수

| 대상 경로 | 링크 수 | 제외 수 |
|-----------|--------|---------|
| `~/.codex/skills/` | 101개 | 2개 |
| `~/.codex/commands/` | 37개 | 2개 |
| `~/.gemini/skills/` | 99개 | 4개 |

---

## 제외 항목 목록

### 공통 제외 (모든 대상)
- `contract-gate*` — Claude Code Hook 전용
- `security-scan*` — Claude Code Hook 전용
- `task-sync*` — Claude Code Hook 전용
- `brand-guidelines*` — Claude 전용 브랜드 설정

### Codex 추가 제외
- `design*` — 디자인 전용 (Gemini 담당)
- `localcode*` — Claude 로컬 전용

### Gemini 추가 제외
- `tdd*` — 코드 테스트 (Codex 담당)
- `build-fix*` — 빌드 수정 (Codex 담당)
- `code-review*` — 코드 리뷰 (Codex 담당)

---

## 사용 방법

```bash
# 전체 동기화 (Codex + Gemini)
./scripts/sync-settings.sh

# 개별 동기화
./scripts/sync-settings.sh codex
./scripts/sync-settings.sh gemini

# 상태 확인
./scripts/sync-settings.sh status

# 심볼릭 링크만 제거 (원본 유지)
./scripts/sync-settings.sh clean
```

---

## 생성 파일

| 파일 | 설명 |
|------|------|
| `config/sync-targets.yaml` | 동기화 대상/제외 설정 문서 |
| `scripts/sync-settings.sh` | bash 심볼릭 링크 동기화 스크립트 |

---

## 발견된 이슈 및 해결

| 이슈 | 원인 | 해결 |
|------|------|------|
| `rm: is a directory` 오류 | `~/.codex/skills/` 에 기존 실제 디렉토리 존재 | `rm -f` → `rm -rf` 로 변경 |

- `~/.codex/skills/algorithmic-art` 가 실제 디렉토리로 존재했음 (이전 설치본)
- `~/.codex/skills/` 및 `~/.gemini/skills/` 각 1개씩 로컬 파일 잔존 (동기화 제외 후 유지됨)

---

## 검증 결과

- `sync-settings.sh all` 실행: 오류 없음
- `~/.codex/skills/`: 101개 심볼릭 링크 생성 확인
- `~/.codex/commands/`: 37개 심볼릭 링크 생성 확인
- `~/.gemini/skills/`: 99개 심볼릭 링크 생성 확인
- 제외 파일(contract-gate 등): 링크 미생성 확인
- `sync-settings.sh clean` 후 원본 파일 유지 확인
- clean 후 재동기화 성공 확인
