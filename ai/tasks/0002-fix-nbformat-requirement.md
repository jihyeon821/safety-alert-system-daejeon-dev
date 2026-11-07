# 0002: fix nbformat requirement

- 날짜: 2026-11-07
- 상태: 완료
- 담당 에이전트: 오케스트레이터 (메인 Claude)

## 목표
`requirements.txt`의 오타 `nbforma==4.2.0`(PyPI에 없는 패키지) 때문에 `pip install -r requirements.txt`가 실패하는 문제를 고칩니다.

## 범위
- 포함: `requirements.txt` 23번째 줄, KNOWN_ISSUES 체크
- 제외: 다른 의존성 버전 변경

## 완료 조건
- [x] `python ai/harness.py check` error 0

## 계획
`nbformat`의 최신 버전 5.11.1을 사용합니다(requires_python >=3.10, 프로젝트 권장 3.10과 호환). 4.2.0은 2016년 버전이라 `ipykernel==7.1.0` 등 최신 Jupyter 스택과 맞지 않습니다.

## 결과
- `requirements.txt:23` `nbforma==4.2.0` → `nbformat==5.11.1`
- `python ai/harness.py check`: 10개 검사, error 0 (`requirements` PASS, `rust-check`는 cargo가 없어 SKIP)
- 실행하지 않은 것: 실제 `pip install -r requirements.txt` (이 PC는 Python 3.14라 torch 등 다른 패키지 설치가 별도로 실패할 수 있음. KNOWN_ISSUES 참고)
