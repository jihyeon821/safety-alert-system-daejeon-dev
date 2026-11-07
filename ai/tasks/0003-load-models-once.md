# 0003: load models once

- 날짜: 2026-11-07
- 상태: 완료
- 담당 에이전트: 오케스트레이터 (메인 Claude)

## 목표
`/predict` 요청마다 KCBERT와 Gemma를 새로 로드하던 문제를 고쳐서, 프로세스당 한 번만 로드하게 합니다.

## 범위
- 포함: `demo/backend/bert_llm.py`, `demo/backend/app.py`
- 제외: 예외 처리(맨 `except:`), tokenizer truncation, 응답 형식 → 각각 별도 KNOWN_ISSUES 항목
- API 계약 변경: 없음

## 완료 조건
- [x] 여러 요청에서 모델 로드 1회
- [x] 모델 파일이 없어도 서버가 시작됨 (기존처럼 /predict에서 오류 응답)
- [x] `python ai/harness.py check` error 0

## 계획
1. `bert_llm.get_analyzer()`: 모듈 수준 캐시 + 로드 lock. 실패하면 캐시하지 않고, 경로가 바뀌면 다시 로드
2. `main()`이 공유 인스턴스를 쓰고, `_run_lock`으로 분석을 직렬화 (llama.cpp 스레드 안전 문제)
3. `MemorySaver` checkpointer 제거: 인스턴스를 재사용하면 요청 상태가 메모리에 무한히 쌓이기 때문
4. `app.py`: 모델 경로를 모듈 상수로 옮기고, `lifespan`에서 사전 로드 (`PRELOAD_MODELS=0`이면 생략)

## 결과
- 경로는 기존과 같습니다 (`demo/backend/kcbert_local`, `best_kcbert_model.pt`, `gemma-3-1B-it-QAT-Q4_0.gguf`)
- 무거운 라이브러리를 가짜 모듈(stub)로 바꾼 테스트 6개 통과: 로드 실패는 캐시하지 않음 / 동시 20건 → 로드 1회, 동시 실행 최대 1 / 경로가 바뀌면 다시 로드 / lifespan에서 1회 로드 후 /predict 재사용 / 가중치가 없어도 startup이 죽지 않음 / 경로 동일
- `python ai/harness.py check --offline`: error 0 (5회 반복). 작업 도중 한 번 error 1이 나왔는데 출력을 남기지 못했고 재현되지 않았습니다.
- 실행하지 못한 것: 실제 모델 가중치로 uvicorn 구동 (가중치 없음, fastapi·torch 미설치)
- 동작 변화: 서버 시작이 모델 로드 시간만큼 느려지는 대신, 첫 요청부터 빨라집니다. 동시 요청은 순서대로 처리됩니다.
