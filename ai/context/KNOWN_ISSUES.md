# 알려진 문제 (백로그)

> 하네스를 처음 만들 때 코드를 분석해서 찾은 문제들입니다. 고치면 `[x]`로 바꾸고 해결한 task 번호를 적습니다.
> 심각도: **H** 동작 실패나 데이터 위험 / **M** 잘못된 동작 / **L** 품질·정리

- [x] **H** `requirements.txt:23` `nbforma==4.2.0`: 존재하지 않는 패키지입니다(`nbformat`의 오타로 보임). `pip install -r requirements.txt`가 여기서 실패합니다. → harness `requirements` 검사가 잡습니다. → `nbformat==5.11.1`로 수정 (task 0002)
- [x] **H** `demo/backend/app.py` `/predict`: 요청이 올 때마다 `main()`이 KCBERT와 Gemma를 **새로 로드**합니다. 매 요청마다 수 초~수십 초가 걸리고 메모리 사용이 큽니다. 앱 시작 시 한 번만 로드하도록 바꿔야 합니다. → 서버 시작 시 1회 로드 + 공유 인스턴스로 수정 (task 0003)
- [ ] **H** `demo/backend/app.py` `/predict`: 맨 `except:`가 모든 예외를 삼키고 HTTP 200으로 `'오류가 발생했습니다'`를 돌려줍니다. 프론트는 `predicted_value`가 문자열이어도 성공으로 처리하고 표를 그리려 합니다. 적절한 HTTP 오류 코드와 메시지가 필요합니다.
- [ ] **H** `demo/backend/bert_llm.py` `node_mode_analysis`: `self.tokenizer(text, return_tensors="pt")`에 `truncation=True, max_length=300`이 없습니다. 병합한 대화 턴이 KCBERT 최대 길이(300 토큰)를 넘으면 예외가 나고, 위의 `except:`에 묻혀 "오류가 발생했습니다"만 보입니다.
- [ ] **M** `demo/backend/bert_llm.py` `node_file_analysis`: `groupby(["group", "min"])`이 각 턴의 첫 발화(`min=True`)와 나머지 발화(`min=False`)를 다른 그룹으로 나눕니다. 10분 이내 턴 병합이 의도대로 되지 않습니다(첫 그룹 제외). `groupby("group")`이어야 합니다. 정렬 없이 `diff()`를 쓰는 점도 확인이 필요합니다.
- [ ] **M** `demo/src/main.js`: `summary`의 초기값이 `"없음"`이라 카카오 전송 전에 하는 `if (!summary)` 검사가 항상 통과합니다. 분석하지 않아도 "없음"이 전송될 수 있습니다.
- [ ] **M** `demo/backend/app.py` `file_path`: 클라이언트가 보낸 임의의 경로를 그대로 엽니다. 로컬 데스크톱 용도라면 괜찮지만, 서버를 외부에 노출하면 위험합니다. CORS도 `*`입니다(개발용).
- [ ] **M** Python 버전: README는 3.10을 권장하는데 이 PC에는 3.14가 설치돼 있습니다. `torch==2.7.0`, `llama-cpp-python` 등은 3.14 wheel이 없을 수 있으니 3.10 가상환경을 쓰세요.
- [ ] **L** `README.md` 4.2: `scr_tauri` / `cargo clean` 줄이 잘못된 명령어입니다.
- [ ] **L** `README.md`는 `/analyze` 엔드포인트를 언급하지만, 실제 엔드포인트는 `/predict`와 `/run-workflow`입니다.
- [ ] **L** `demo/backend/app.py`: n8n URL이 하드코딩돼 있습니다. 환경변수(`N8N_WEBHOOK_URL`)로 빼는 게 좋습니다.

## 요구사항 분석(task 0004)에서 추가로 찾은 문제
- [ ] **H** `demo/src/main.js`: [입력] 버튼 클릭 핸들러 안에서 [분석실행] 클릭 리스너와 `setInterval(vis)`를 등록해서, [입력]을 누를 때마다 리스너가 하나씩 늘어납니다. 그러면 [분석실행] 1회 클릭에 /predict가 여러 번 호출됩니다. → task 0008
- [ ] **H** `demo/backend/app.py:63,70,80`, `bert_llm.py:177,238,254`: 발화 원문, 분석 표, 보고서를 콘솔에 `print`합니다(개인정보 규칙 위반). → task 0011
- [ ] **H** `notebooks/02`, `04`: 턴 병합 `groupby(["group","min"])` 결함이 노트북에도 있어서, 학습 라벨도 같은 방식으로 만들어졌습니다. 추론 코드만 고치면 학습과 서빙이 어긋납니다. → task 0007
- [ ] **M** `demo/src/index.html`: Grid.js와 Pretendard를 CDN(unpkg, jsdelivr)에서 불러와서, 오프라인이면 결과 표가 렌더링되지 않습니다. → task 0016
- [ ] **M** 모델 성능: emergency 재현율이 45.0%입니다(111건 중 50건). 목표값이 정해져 있지 않습니다. → task 0017
- [ ] **L** `demo/backend/app.py` `/run-workflow`: n8n이 4xx·5xx로 응답해도 "n8n 호출 성공"을 반환합니다. → task 0013
