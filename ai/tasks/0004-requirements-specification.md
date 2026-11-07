# 0004: requirements specification

- 날짜: 2026-11-07
- 상태: 완료
- 담당 에이전트: 오케스트레이터 (메인 Claude)

## 목표
프로젝트를 분석해서 요구사항정의서(엑셀)를 만들고, 미완료 요구사항을 하네스 작업(ai/tasks)으로 등록합니다.

## 범위
- 포함: `docs/requirements.json`(원본 데이터), `docs/요구사항정의서.xlsx`, `ai/tools/build_requirements.py`(재사용 생성기), 작업 0005~0019 등록
- 제외: 등록한 작업의 구현

## 완료 조건
- [x] 기능·비기능 요구사항마다 수용 기준, 출처, 구현 상태, 관련 작업이 있음
- [x] 모든 미완료 요구사항이 작업에 연결됨 (끊긴 참조 0)
- [x] 엑셀 수식 오류 0, 집계값이 독립 계산과 일치
- [x] `python ai/harness.py check` error 0

## 계획
README, 노트북 4개, backend, frontend, Tauri 설정, results CSV를 분석해서 요구사항을 역으로 도출합니다. JSON 하나를 원본으로 두고, 엑셀과 작업 파일을 모두 거기서 생성합니다.

## 결과
- 요구사항 44건 (기능 28 / 비기능 16): 구현완료 24, 부분구현 9, 미구현 5, 결함 6
- 작업 19건: 완료 4 (0001~0004), 대기 13, 보류 2 (0017 성능 목표, 0018 자동 알림은 사용자 결정 필요)
- 엑셀 시트: 표지, 요약(COUNTIFS 수식), 요구사항 목록, 작업 목록, 모델 성능(혼동 행렬 → 정밀도·재현율·F1 수식)
- 검증: LibreOffice가 없어서 xlsx 스킬의 recalc.py는 실행하지 못했습니다. 대신 `formulas` 패키지로 수식 919개를 계산했고 오류 0이었습니다. 요약 집계 44칸, 우선순위·구분·작업 집계, 성능 지표(정확도 0.768, macro F1 0.602, emergency 재현율 0.450, 최고 val F1 0.639 @ epoch 5)를 Python 독립 계산과 대조해 모두 일치했습니다. 화면 렌더링(서식이 어떻게 보이는지)은 확인하지 못했습니다.
- 가정: 목표값 macro F1 0.70, emergency 재현율 0.80은 제안값입니다(엑셀 노란 칸). `confusion_matrix.csv`는 평가(test) 세트로 추정합니다.
- 다시 생성: `python ai/tools/build_requirements.py docs/requirements.json docs/요구사항정의서.xlsx --sync-tasks`
