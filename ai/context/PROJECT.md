# 프로젝트 컨텍스트: 투윤백 (safety-alert-system-daejeon)

> AI 에이전트가 작업 전에 반드시 읽는 문서입니다. 코드가 바뀌면 이 문서도 같이 고칩니다.

## 1. 한 줄 요약
대전 중구 어르신 돌봄 인형(`doll_id`)의 발화 데이터를 **KCBERT로 위험도 4단계 분류**하고, **Gemma LLM이 분류 근거를 설명**한 뒤, Tauri 데스크톱 앱에서 결과를 보고 **n8n → 카카오톡**으로 알림을 보내는 시스템입니다.

## 2. 구성 요소

| 영역 | 위치 | 기술 | 비고 |
|---|---|---|---|
| 분석·학습 | `notebooks/01~04` | pandas, BERTopic, soynlp/kiwipiepy, transformers | 03은 Colab A100 전용 |
| AI 백엔드 | `demo/backend/app.py`, `bert_llm.py` | FastAPI, PyTorch, llama-cpp-python, LangGraph | 포트 8000 |
| 데스크톱 앱 | `demo/src` (UI), `demo/src-tauri` (Rust) | Tauri v2, vanilla JS, plugin-dialog | 번들러 없음 |
| 알림 | 외부 n8n (`localhost:5678/webhook/tauri`) | n8n 노코드 워크플로우 | 저장소에 없음 |
| 산출물 | `results/`, `figures/`, `reports/` | CSV, PNG, PDF, MP4 | |

## 3. 데이터 흐름
```
[Tauri UI] 엑셀 파일 선택 + doll_id 입력
   │ POST /predict {file_path, doll_id, kakao_message}
   ▼
[FastAPI] main() → BertLlm (LangGraph)
   node_file_analysis   : pd.read_excel → doll_id 필터 → 10분 이내 발화 턴 병합
   node_mode_analysis   : KCBERT 분류 (positive/danger/critical/emergency) + Gemma 근거 생성
   node_summary_report  : 요약 보고서 생성
   │ {predicted_value: <detail_dataframe JSON>, summary1: <summary_report>}
   ▼
[Tauri UI] 표(발화문/발화시간/등급/추론이유) 렌더링 → [카카오 전송] 버튼
   │ POST /run-workflow {..., kakao_message: summary}
   ▼
[FastAPI] → n8n webhook → 카카오톡/기타 메신저
```

## 4. API 계약 (프론트 ↔ 백엔드)
- 요청 바디(두 엔드포인트 공통 `InputData`): `file_path: str`, `doll_id: int`, `kakao_message: str`
- `POST /predict` 응답: `{"predicted_value": <dict 또는 오류 문자열>, "summary1": <str>}`
- `POST /run-workflow` 응답: `{"status": "n8n 호출 성공"|"n8n 호출 실패", ...}`. 프론트는 이 **한국어 문자열을 그대로 비교**합니다.
- 계약을 바꿀 때는 `demo/src/main.js`와 `demo/backend/app.py`를 **같은 작업에서** 함께 고칩니다. `harness check`의 `api-contract` 검사가 경로 불일치를 잡습니다.

## 5. 도메인 규칙
- 위험 등급 라벨은 4개이고 순서가 고정입니다: `positive` < `danger` < `critical` < `emergency`. KCBERT `num_labels=4`
- LLM은 **새로 판단하지 않고**, KCBERT가 내린 등급의 근거만 설명합니다.
- 클래스 불균형이 큽니다(대부분 positive). 평가 지표는 정확도가 아니라 F1(소수 클래스)을 봅니다.
- 발화 데이터는 어르신의 **개인정보·민감정보**입니다. 원본이나 발화 원문을 커밋하거나, 로그·예시에 실제 문장을 넣지 않습니다.

## 6. 저장소에 없는 것 (실행 전에 따로 준비)
- `demo/backend/kcbert_local/` (토크나이저와 설정), `best_kcbert_model.pt`, `gemma-3-1B-it-QAT-Q4_0.gguf`
- 원본 데이터와 라벨링 엑셀 (`data/데이터 출처.txt` 참고)
- n8n 워크플로우와 카카오 개발자 인증
- `demo/node_modules` → `cd demo && npm install`

## 7. 실행
```bash
pip install -r requirements.txt            # Python 3.10 권장
cd demo/backend && uvicorn app:app --reload   # 터미널 1
cd demo && npm install && npm run tauri dev   # 터미널 2 (Rust 필요)
```

## 8. 검증
```bash
python ai/harness.py check            # 전체 검사
python ai/harness.py check --offline  # 네트워크 없이 (PyPI 확인 생략)
```
