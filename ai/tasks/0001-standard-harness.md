# 0001: standard harness

- 날짜: 2026-11-07
- 상태: 완료
- 담당 에이전트: 오케스트레이터 (메인 Claude)

## 목표
프로젝트를 분석해서, AI 에이전트가 일관된 방식으로 검증을 거쳐 작업할 수 있는 **재사용 가능한 하네스**를 `ai/`에 만들고 실행합니다.

## 범위
- 포함: `ai/` 폴더 전체, 루트 `CLAUDE.md`, 에이전트 원본을 `ai/agents`로 이동하고 `.claude/agents`와 동기화
- 제외: 애플리케이션 코드 수정 (발견한 문제는 `KNOWN_ISSUES.md`에 기록만 함)

## 완료 조건
- [x] 프로젝트 컨텍스트 문서 (`ai/context/PROJECT.md`)
- [x] 일반 CLI + 프로젝트 설정 분리 (`harness.py` / `harness.json`)
- [x] 표준 작업 루프와 작업 템플릿
- [x] 하네스 실행 및 검사 동작 확인
- [ ] `python ai/harness.py check` error 0 → **기존 코드의 `requirements.txt` 문제 1건 때문에 미충족** (아래 참고)

## 계획
README, 노트북 목록, `app.py`, `bert_llm.py`, `main.js`, Tauri 설정, `requirements.txt`를 분석했습니다. 검사 항목은 이 프로젝트에서 실제로 위험한 것 위주로 골랐습니다: 모델 가중치·개인정보 커밋, 프론트·백엔드 API 불일치, 설치 실패.

## 결과
**`python ai/harness.py check` (온라인):** 10개 검사, error 1, skip 1
- FAIL `requirements`: `requirements.txt:23 nbforma==4.2.0`은 PyPI에 없는 패키지입니다. 기존 버그이고 KNOWN_ISSUES에 H로 기록했습니다.
- SKIP `rust-check`: 이 PC에 `cargo`가 없습니다.
- 나머지 8개는 PASS입니다. API 계약 결과: 클라이언트 `/predict`, `/run-workflow` ⊆ 서버 `/`, `/predict`, `/run-workflow`

**음성 테스트 (일부러 문제를 넣고 감지되는지 확인):** 5개 모두 감지했습니다.
- 가짜 `.gguf` 파일 → `forbidden-files` FAIL
- `api_key = "..."` → `secrets` FAIL
- 문법 오류가 있는 `.py` → `python-syntax` FAIL
- 백엔드에 없는 `/missing` 호출 → `api-contract` FAIL
- `.claude/agents` 직접 수정 → `agents-sync` FAIL

임시 파일을 지운 뒤 `--offline` 검사는 error 0으로 돌아왔습니다.

**실행하지 못한 것:** 백엔드 서버와 Tauri 앱 실제 구동 (모델 가중치 없음, Rust 미설치), `reviewer` 서브에이전트 리뷰 (에이전트 정의가 이번 세션 시작 후에 추가돼서 로드되지 않음)

**분석으로 찾은 문제:** `ai/context/KNOWN_ISSUES.md`에 11건 (H 4 / M 4 / L 3)
