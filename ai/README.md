# AI 작업 하네스

AI 에이전트(Claude Code)가 이 저장소에서 **같은 방식으로, 검증을 거쳐** 작업하도록 만든 표준 틀입니다.
다른 프로젝트에 옮겨 쓸 수 있게 **일반 부분**과 **프로젝트 전용 부분**을 나눠 두었습니다.

## 구조
```
ai/
├── harness.py            # [일반] 검증·동기화·작업기록 CLI (표준 라이브러리만 사용)
├── harness.json          # [전용] 프로젝트 프로필 + 검사 목록
├── context/
│   ├── PROJECT.md        # [전용] 아키텍처, 데이터 흐름, API 계약, 도메인 규칙
│   └── KNOWN_ISSUES.md   # [전용] 분석으로 찾은 문제 백로그
├── agents/               # [전용] 에이전트 정의 원본 → .claude/agents로 동기화
├── workflows/
│   └── standard-loop.md  # [일반] 기록 → 계획 → 구현 → 검증 → 리뷰 5단계
├── templates/
│   └── task.md           # [일반] 작업 기록 양식
└── tasks/                # 작업 기록 (NNNN-제목.md)
```
루트의 `CLAUDE.md`가 이 폴더를 가리키기 때문에, Claude Code를 시작하면 자동으로 이 규칙을 따릅니다.

## 명령어
```bash
python ai/harness.py check               # 전체 검사 (error가 있으면 exit 1)
python ai/harness.py check --offline     # PyPI 확인 같은 네트워크 검사 생략
python ai/harness.py check --only secrets,api-contract
python ai/harness.py sync-agents         # ai/agents → .claude/agents 복사
python ai/harness.py new-task "제목"     # ai/tasks/NNNN-제목.md 생성
```

## 검사 종류 (`harness.json`의 `type`)
| type | 하는 일 |
|---|---|
| `forbidden_tracked` | 커밋하면 안 되는 파일(모델 가중치, node_modules, .env 등) 감지 |
| `max_file_size` | 큰 파일 감지 (GitHub 경고 기준 50MB) |
| `secret_scan` | API 키나 토큰 패턴 감지 |
| `python_compile` | Python 문법 검사 |
| `json_valid` | JSON과 노트북 파일 파싱 |
| `api_contract` | 프론트가 호출하는 경로가 백엔드에 정의돼 있는지 확인 |
| `requirements` | 버전 고정 여부, PyPI에 실제 있는 버전인지 확인 |
| `dir_sync` | 두 폴더 내용이 같은지 확인 (에이전트 원본과 사본) |
| `command` | 임의의 명령 실행 (도구가 없으면 `optional`로 건너뜀) |

`level`이 `error`면 실패 시 커밋하지 않습니다. `warn`은 기록만 합니다.

## 다른 프로젝트에 재사용하기
1. `ai/` 폴더를 통째로 복사합니다.
2. `harness.json`을 고칩니다: 경로 glob, API 정규식, requirements 경로, 명령어 검사
3. `context/PROJECT.md`, `KNOWN_ISSUES.md`를 그 프로젝트 내용으로 다시 씁니다.
4. `agents/`의 역할과 범위를 맞추고 `python ai/harness.py sync-agents`를 실행합니다.
5. 루트에 `CLAUDE.md`를 복사합니다.
6. `python ai/harness.py check`가 통과하는지 확인합니다.

`harness.py`, `workflows/`, `templates/`는 고치지 않고 그대로 씁니다. 새 검사 종류가 필요하면 `harness.py`의 `CHECKS`에 함수를 추가하세요.
