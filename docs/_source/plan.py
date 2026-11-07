"""Single source of project-management data for all deliverables in docs/.

Facts come from the repository (requirements.json, ai/tasks, KNOWN_ISSUES, git log).
Anything that cannot be derived from the repo (dates of planned work, rates, budgets)
is an ASSUMPTION and is marked as such in every generated document.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
REQ = json.loads((DOCS / "요구사항" / "requirements.json").read_text(encoding="utf-8"))

META = {
    "project": "투윤백 안전 알림 시스템 고도화",
    "project_en": "safety-alert-system-daejeon-dev",
    "org": "투윤백 팀",
    "owner": "jihyeon821",
    "version": "v0.1",
    "date": "2026-11-07",
    "status_date": "2026-11-07",
    "start": "2026-11-07",
    "plan_start": "2026-11-09",
    "repo": "https://github.com/jihyeon821/safety-alert-system-daejeon-dev",
    "basis": "저장소 main 브랜치 분석 (requirements.json, ai/tasks 0001~0020, ai/context/KNOWN_ISSUES.md, git log)",
}
ASSUMPTION_NOTE = ("노란 배경 = 저장소에서 확인할 수 없는 가정값·계획(안)입니다. "
                   "실제 값으로 바꾸면 수식이 자동으로 다시 계산됩니다.")
HOLIDAYS = ["2026-12-25", "2027-01-01"]

# --------------------------------------------------------------------------- people / roles
# Real people beyond the repository owner are not recorded in the repo -> placeholders.
ROLES = [
    # code, name, kind, who, responsibility
    ("OWN", "프로젝트 오너(PM)", "사람", "jihyeon821", "범위·우선순위 결정, 산출물 승인, 의사결정(성능 목표, 알림 정책), 실제 환경 검증"),
    ("ORC", "오케스트레이터", "AI 에이전트", "Claude Code (메인)", "작업 분해·배정, 하네스 검증, 문서화, 커밋"),
    ("BE", "백엔드 담당", "AI 에이전트", "backend 서브에이전트", "FastAPI·모델 파이프라인 구현"),
    ("FE", "프론트엔드 담당", "AI 에이전트", "frontend 서브에이전트", "Tauri UI 구현"),
    ("DA", "데이터·모델 담당", "AI 에이전트", "data-analyst 서브에이전트", "노트북, 라벨링, 학습·평가"),
    ("RV", "리뷰 담당", "AI 에이전트", "reviewer 서브에이전트(읽기 전용)", "변경 검토, 계약·보안 점검"),
    ("TM", "원 개발팀원", "사람", "[확인 필요]", "기존 모델·데이터·n8n 워크플로우 보유자. 자료 인계, 도메인 자문"),
]
ROLE_CODES = [r[0] for r in ROLES]

# --------------------------------------------------------------------------- WBS
WBS = [
    # code, name, level, description, deliverable
    ("1", "프로젝트 관리", 1, "착수·계획·감시통제·종료 관리", "PM 산출물 01~34"),
    ("1.1", "착수", 2, "헌장, 이해관계자, 팀 구성", "01, 02, 03"),
    ("1.2", "계획", 2, "관리 계획서와 기준선(범위·일정·원가)", "04~24"),
    ("1.3", "감시·통제", 2, "성과 보고, 변경 통제, 이슈·위기 관리", "25~32"),
    ("1.4", "종료", 2, "단계 종료, 교훈", "33, 34"),
    ("2", "분석·기반 구축 (1단계)", 1, "작업 하네스, 긴급 결함 수정, 요구사항 정의", "ai/, 요구사항정의서"),
    ("2.1", "AI 작업 하네스 구축", 2, "검증 CLI, 에이전트, 작업 루프 (task 0001)", "ai/harness.py 외"),
    ("2.2", "의존성 오류 수정", 2, "requirements.txt 오타 수정 (task 0002)", "requirements.txt"),
    ("2.3", "모델 1회 로드", 2, "요청마다 모델을 다시 로드하던 문제 수정 (task 0003)", "demo/backend"),
    ("2.4", "요구사항 정의", 2, "요구사항 44건, 작업 19건 도출 (task 0004)", "요구사항정의서.xlsx"),
    ("3", "백엔드 안정화", 1, "API 오류 처리, 입력 처리, 개인정보 로그, 보안 설정", "demo/backend"),
    ("4", "프론트엔드 개선", 1, "중복 호출, 알림 가드, 진행·오류 표시, 오프라인", "demo/src"),
    ("5", "모델 품질 개선", 1, "턴 병합 일치, 성능 목표, 재학습", "notebooks, 모델 가중치"),
    ("6", "알림 고도화", 1, "등급 기반 자동·단계 알림", "backend, n8n"),
    ("7", "운영·문서", 1, "하네스 보강, README, 모델 준비 절차", "ai/, README"),
    ("8", "통합 검증·종료", 1, "실제 모델 E2E 테스트, 인수, 종료", "테스트 기록, 종료 보고서"),
]

# Activities. dur = (optimistic, most likely, pessimistic) workdays.
# hours = estimated effort per role (OWN hours are human hours and drive labour cost).
# actual = (start, finish, % complete) for work already done.
ACTIVITIES = [
    # id, wbs, name, task, owner_role, (O,M,P), preds, {role: hours}, actual
    ("A01", "2.1", "AI 작업 하네스 구축", "0001", "ORC", (1, 1, 1), [], {"OWN": 1, "ORC": 4}, ("2026-11-07", "2026-11-07", 1.0)),
    ("A02", "2.2", "requirements 오타 수정", "0002", "ORC", (1, 1, 1), ["A01"], {"OWN": 0.5, "ORC": 0.5}, ("2026-11-07", "2026-11-07", 1.0)),
    ("A03", "2.3", "모델 1회 로드", "0003", "BE", (1, 1, 1), ["A01"], {"OWN": 0.5, "BE": 2, "RV": 0.5}, ("2026-11-07", "2026-11-07", 1.0)),
    ("A04", "2.4", "요구사항 정의", "0004", "ORC", (1, 1, 1), ["A01"], {"OWN": 1, "ORC": 3}, ("2026-11-07", "2026-11-07", 1.0)),
    ("A05", "1.1", "PM 산출물(착수·계획) 작성", "0020", "ORC", (1, 1, 1), ["A04"], {"OWN": 1, "ORC": 4}, ("2026-11-07", "2026-11-07", 1.0)),
    ("A06", "1.2", "계획 기준선 검토·승인", "", "OWN", (1, 1, 2), ["A05"], {"OWN": 3}, None),
    ("A07", "3", "/predict 오류 응답 개선", "0005", "BE", (1, 2, 3), ["A06"], {"OWN": 1, "BE": 4, "RV": 1}, None),
    ("A08", "3", "KCBERT 입력 truncation", "0006", "BE", (1, 1, 2), ["A06"], {"OWN": 0.5, "BE": 1, "RV": 0.5}, None),
    ("A09", "3", "로그에서 발화 원문 제거", "0011", "BE", (1, 1, 2), ["A06"], {"OWN": 0.5, "BE": 2, "RV": 0.5}, None),
    ("A10", "3", "파일 경로·CORS 제한", "0012", "BE", (1, 2, 3), ["A07"], {"OWN": 1, "BE": 3, "RV": 1}, None),
    ("A11", "3", "n8n URL 환경변수화", "0013", "BE", (1, 1, 2), ["A06"], {"OWN": 0.5, "BE": 1, "RV": 0.5}, None),
    ("A12", "4", "분석 버튼 중복 리스너 제거", "0008", "FE", (1, 1, 2), ["A06"], {"OWN": 0.5, "FE": 2, "RV": 0.5}, None),
    ("A13", "4", "알림 전송 가드 수정", "0009", "FE", (1, 1, 1), ["A12"], {"OWN": 0.5, "FE": 1, "RV": 0.5}, None),
    ("A14", "4", "분석 진행·오류 UI", "0010", "FE", (1, 2, 3), ["A07", "A12"], {"OWN": 1, "FE": 3, "RV": 1}, None),
    ("A15", "4", "UI 라이브러리 로컬 번들", "0016", "FE", (1, 1, 2), ["A06"], {"OWN": 0.5, "FE": 1, "RV": 0.5}, None),
    ("A16", "5", "턴 병합 수정·라벨 재생성", "0007", "DA", (2, 3, 5), ["A06"], {"OWN": 2, "DA": 6, "BE": 1, "RV": 1}, None),
    ("A17", "5", "성능 목표 확정", "0017", "OWN", (1, 1, 2), ["A06"], {"OWN": 2}, None),
    ("A18", "5", "KCBERT 재학습·평가", "0017", "DA", (3, 5, 8), ["A16", "A17"], {"OWN": 4, "DA": 8, "RV": 1}, None),
    ("A19", "5", "신규 모델 백엔드 반영", "0007", "BE", (1, 1, 2), ["A18", "A08"], {"OWN": 1, "BE": 2, "RV": 0.5}, None),
    ("A20", "6", "알림 정책 확정", "0018", "OWN", (1, 2, 4), ["A06"], {"OWN": 4}, None),
    ("A21", "6", "자동·단계 알림 구현", "0018", "BE", (3, 4, 6), ["A20", "A07"], {"OWN": 3, "BE": 6, "RV": 1}, None),
    ("A22", "7", "하네스 데이터 파일 차단", "0014", "ORC", (1, 1, 1), ["A06"], {"OWN": 0.5, "ORC": 1}, None),
    ("A23", "7", "README 정정", "0015", "ORC", (1, 1, 1), ["A06"], {"OWN": 0.5, "ORC": 1}, None),
    ("A24", "7", "모델·데이터 준비 절차 문서화", "0019", "ORC", (1, 2, 3), ["A19"], {"OWN": 1, "ORC": 2}, None),
    ("A25", "8", "통합 테스트 (실제 모델 E2E)", "", "OWN", (2, 3, 5),
     ["A09", "A10", "A11", "A13", "A14", "A15", "A19", "A21", "A22", "A23"], {"OWN": 8, "ORC": 2, "RV": 2}, None),
    ("A26", "8", "사용자 인수 검토", "", "OWN", (1, 1, 2), ["A25", "A24"], {"OWN": 3}, None),
    ("A27", "1.4", "종료 보고·교훈 정리", "", "ORC", (1, 1, 2), ["A26"], {"OWN": 1, "ORC": 2}, None),
]
MILESTONES = [
    ("M1", "1단계(분석·기반 구축) 완료", ["A05"], "2026-11-07 달성"),
    ("M2", "계획 기준선 승인", ["A06"], ""),
    ("M3", "백엔드·프론트 결함 수정 완료", ["A10", "A11", "A13", "A14", "A15", "A09"], ""),
    ("M4", "개선 모델 반영", ["A19"], ""),
    ("M5", "통합 테스트 완료", ["A25"], ""),
    ("M6", "프로젝트 종료", ["A27"], ""),
]

# --------------------------------------------------------------------------- cost assumptions
RATES = {  # KRW, all ASSUMPTIONS
    "OWN": ("프로젝트 오너 인건비", "원/시간", 20000),
    "AI": ("AI 코딩 도구 이용료", "원/월", 100000),
    "GPU": ("클라우드 GPU 이용료 (재학습)", "원/회", 50000),
    "RES": ("관리 예비비", "비율", 0.10),
}
OTHER_COSTS = [  # name, unit, qty, rate key or unit price, note
    ("AI 코딩 도구 이용료", "월", 2, "AI", "11월·12월 2개월분 결제 (가정)"),
    ("클라우드 GPU 이용료", "회", 2, "GPU", "A18 재학습 2회분 (가정)"),
    ("오픈소스 소프트웨어", "식", 1, 0, "FastAPI, Tauri, transformers, n8n(셀프 호스팅) 등 무료"),
    ("메신저 알림(카카오) 연동", "식", 1, 0, "개발자 계정 기준 비용 없음으로 가정 (확인 필요)"),
]

# --------------------------------------------------------------------------- stakeholders
STAKEHOLDERS = [
    # id, name/group, role in project, interest, influence(1-5), interest(1-5), expectation, strategy, contact
    ("SH-01", "프로젝트 오너 (jihyeon821)", "후원자·PM", "고도화 완료, 결함 해소", 5, 5, "범위 내 결함 수정과 품질 개선", "주도", "GitHub"),
    ("SH-02", "원 개발팀 (투윤백 팀원)", "기존 개발자·자문", "기존 성과 보존, 재사용", 3, 4, "모델·데이터·n8n 자료 인계, 변경 공유", "긴밀 협의", "[확인 필요]"),
    ("SH-03", "대전 중구 담당 공무원", "1차 알림 수신자·최종 사용자", "위험 대상자 조기 파악", 4, 4, "정확한 위험 알림, 오경보 최소화", "긴밀 협의", "[확인 필요]"),
    ("SH-04", "보호자", "2차 알림 수신자", "가족 안전", 2, 5, "긴급 상황 즉시 통보", "정보 제공", "[확인 필요]"),
    ("SH-05", "어르신 (돌봄 인형 사용자)", "데이터 주체", "개인정보 보호, 안전", 2, 5, "발화 데이터의 안전한 처리", "보호·정보 제공", "-"),
    ("SH-06", "긴급 기관 (119/112)", "긴급 통보 대상(계획)", "정확한 출동 정보", 4, 2, "정책에 맞는 연계 방식", "협의 후 결정", "[확인 필요]"),
    ("SH-07", "데이터 제공 기관 (대회 주최·대전시)", "데이터 제공자", "데이터 이용 조건 준수", 4, 2, "제공 목적 내 사용, 재배포 금지", "조건 준수 보고", "data/데이터 출처.txt"),
    ("SH-08", "외부 서비스 (카카오, n8n)", "알림 채널 제공자", "이용 약관 준수", 3, 1, "API 인증·약관 준수", "모니터링", "개발자 센터"),
    ("SH-09", "모델 라이선스 제공자 (Google Gemma, KcBERT)", "모델 제공자", "라이선스 준수", 3, 1, "Gemma Terms, Apache-2.0 준수", "모니터링", "라이선스 문서"),
    ("SH-10", "AI 개발 에이전트 (Claude Code)", "개발 수행 자원", "-", 2, 3, "명확한 작업 정의, 하네스 규칙", "작업 배정", "ai/"),
]

# --------------------------------------------------------------------------- risks
RISKS = [
    # id, category, risk, cause, effect, P(1-5), I(1-5), response type, response, owner, trigger, status
    ("R-01", "품질", "긴급 위험 발화 미탐지", "emergency 재현율 45.0% (111건 중 50건)", "긴급 상황 알림 누락으로 인명 피해 가능", 4, 5, "완화", "성능 목표 확정, 재학습·임계값 조정, 사람 검토 병행", "DA", "재학습 후 재현율 목표 미달", "대응 중 (A17, A18)"),
    ("R-02", "개인정보", "발화 원문 로그 노출", "서버가 발화·보고서를 콘솔에 print", "민감정보 유출", 4, 4, "회피", "로그에서 원문 제거, 건수·단계만 기록", "BE", "로그에 문장 출력 발견", "대응 예정 (A09)"),
    ("R-03", "기술", "학습·추론 데이터 처리 불일치", "턴 병합 결함이 노트북과 백엔드에 모두 있음", "추론만 고치면 모델 성능 저하", 4, 4, "완화", "학습·추론 동시 수정 후 재학습", "DA", "병합 규칙이 서로 다름", "대응 예정 (A16)"),
    ("R-04", "자원", "모델 가중치·원본 데이터 확보 실패", "가중치·데이터가 저장소에 없음, 원 팀원 연락 미확보", "실제 E2E 테스트·재학습 불가", 3, 5, "완화", "원 팀원에게 인계 요청, 준비 절차 문서화", "OWN", "A25 시작 시점까지 미확보", "미해결"),
    ("R-05", "기술", "로컬 실행 환경 불일치", "PC Python 3.14, Rust 미설치 (권장 3.10)", "설치 실패, 앱 빌드 불가", 4, 3, "완화", "Python 3.10 가상환경, Rust 설치", "OWN", "pip/cargo 실패", "미해결"),
    ("R-06", "자원", "GPU 접근 불가", "파인튜닝에 A100급 GPU 필요", "재학습 지연", 3, 4, "전가", "클라우드 GPU(Colab 등) 사용", "DA", "GPU 할당 실패", "미해결"),
    ("R-07", "외부", "메신저 API 승인·약관 제약", "카카오 개발자 권한 필요", "알림 기능 지연", 3, 3, "완화", "대체 채널(텔레그램 등 n8n 노드) 준비", "OWN", "인증 실패", "미해결"),
    ("R-08", "정책", "긴급 기관 자동 통보 정책 미확정", "119/112 연계에 기관 협의 필요", "자동 알림 범위 축소", 4, 3, "수용", "1차: 공무원·보호자 알림까지만 구현", "OWN", "정책 결정 지연", "미해결"),
    ("R-09", "품질", "LLM 근거 설명의 사실 왜곡", "1B 소형 LLM 생성", "잘못된 근거로 사용자가 오판", 3, 3, "완화", "근거는 참고용임을 UI에 표시, 리뷰 샘플링", "DA", "부적절한 근거 사례 발견", "미해결"),
    ("R-10", "운영", "UI 오프라인 미동작", "Grid.js·폰트 CDN 의존", "야간·폐쇄망에서 결과 표 미표시", 2, 3, "회피", "라이브러리 로컬 번들", "FE", "네트워크 차단 환경", "대응 예정 (A15)"),
    ("R-11", "법·라이선스", "모델 라이선스 위반", "Gemma 금지 용도 정책, 재배포 조건", "배포 제한", 2, 4, "회피", "라이선스 검토 후 배포 문서에 명시", "OWN", "배포 직전 검토 누락", "미해결"),
    ("R-12", "일정", "의사결정 지연", "성능 목표·알림 정책은 오너 결정 사항", "A18, A21 착수 지연", 3, 3, "완화", "결정 항목을 주간 보고에 상정, 기한 지정", "OWN", "결정 기한 초과", "미해결"),
]

# --------------------------------------------------------------------------- issues (actual, from this repo)
ISSUES = [
    # id, date, title, description, priority, related, owner, status, resolution, closed
    ("I-01", "2026-11-07", "웹 업로드 100개 제한", "demo 폴더(120개 파일) 웹 업로드 실패, node_modules 93개 포함", "중", "-", "ORC", "해결", "node_modules·__pycache__ 제외 후 git push, .gitignore 추가", "2026-11-07"),
    ("I-02", "2026-11-07", "git 사용자 정보 미설정", "커밋 실패 (Author identity unknown)", "하", "-", "ORC", "해결", "저장소 단위 user.name/email 설정", "2026-11-07"),
    ("I-03", "2026-11-07", "requirements.txt 설치 실패", "존재하지 않는 패키지 nbforma==4.2.0", "상", "NFR-OP-01", "ORC", "해결", "nbformat==5.11.1 (task 0002)", "2026-11-07"),
    ("I-04", "2026-11-07", "요청마다 모델 재로드", "/predict마다 KCBERT·Gemma 로드", "상", "NFR-PF-01", "BE", "해결", "프로세스당 1회 로드 (task 0003)", "2026-11-07"),
    ("I-05", "2026-11-07", "오류를 성공(200)으로 반환", "맨 except:가 예외를 삼킴", "상", "FR-API-04", "BE", "미해결", "task 0005", ""),
    ("I-06", "2026-11-07", "긴 입력 시 분석 실패", "tokenizer truncation 없음", "상", "FR-API-06", "BE", "미해결", "task 0006", ""),
    ("I-07", "2026-11-07", "턴 병합 결함 (학습·추론)", "groupby([group,min])가 첫 발화 분리", "상", "FR-LB-02, FR-API-02", "DA", "미해결", "task 0007", ""),
    ("I-08", "2026-11-07", "분석 요청 중복 호출", "[입력] 클릭마다 리스너 추가", "상", "FR-UI-05", "FE", "미해결", "task 0008", ""),
    ("I-09", "2026-11-07", "발화 원문 로그 출력", "print로 원문·보고서 출력", "상", "NFR-SC-03", "BE", "미해결", "task 0011", ""),
    ("I-10", "2026-11-07", "분석 전 알림 전송 가능", "summary 초기값 '없음'", "중", "FR-UI-06", "FE", "미해결", "task 0009", ""),
    ("I-11", "2026-11-07", "원 팀원 연락처·자료 미확보", "가중치, 원본 데이터, n8n 워크플로우 위치 불명", "상", "NFR-OP-02", "OWN", "미해결", "원 팀원 인계 요청", ""),
    ("I-12", "2026-11-07", "로컬 검증 도구 부재", "LibreOffice·Rust·fastapi 미설치로 일부 검증 불가", "중", "-", "ORC", "부분 해결", "대체 검증 (formulas, stub 테스트)", ""),
]

# --------------------------------------------------------------------------- change requests
CHANGES = [
    # id, date, requester, title, type, description, reason, impact scope/schedule/cost/quality, related, decision, decided_by, decided_on, status
    ("CR-001", "2026-11-07", "ORC", "requirements.txt 의존성 수정", "결함 수정", "nbforma==4.2.0 → nbformat==5.11.1", "설치 실패", "범위 영향 없음 / 일정 0.1일 / 원가 무시 / 품질 향상", "I-03, task 0002", "승인", "jihyeon821", "2026-11-07", "완료"),
    ("CR-002", "2026-11-07", "ORC", "모델 1회 로드 구조 변경", "결함 수정", "get_analyzer 캐시, 실행 lock, lifespan 사전 로드", "응답 지연·메모리 과다", "API 계약 영향 없음 / 일정 0.5일 / 품질·성능 향상", "I-04, task 0003", "승인", "jihyeon821", "2026-11-07", "완료"),
    ("CR-003", "2026-11-07", "ORC", "LangGraph checkpointer 제거", "설계 변경", "MemorySaver 제거, 요청 상태 비보존", "인스턴스 재사용 시 개인정보 누적", "기능 영향 없음 / 개인정보 보호 강화", "task 0003, NFR-SC-02", "승인", "jihyeon821", "2026-11-07", "완료"),
    ("CR-004", "2026-11-07", "ORC", "/predict 오류 응답 형식 변경", "API 계약 변경", "오류 시 200 + 문자열 → 4xx/5xx + 메시지", "오류 원인 파악 불가", "프론트 수정 필요(A14) / 일정 +1일", "I-05, task 0005", "검토 중", "", "", "제출"),
    ("CR-005", "2026-11-07", "DA", "턴 병합 규칙 수정 및 재학습", "범위·품질 변경", "학습·추론 병합 규칙 수정, 라벨 재생성, 재학습", "결함 + 학습·추론 일치", "일정 +8~13일 / GPU 비용 발생 / 성능 변동", "I-07, task 0007, R-03", "검토 중", "", "", "제출"),
    ("CR-006", "2026-11-07", "OWN", "자동·단계 알림 범위 결정", "범위 변경", "등급 기반 자동 알림, 1·2차 대상, 긴급 기관 연계 여부", "README 설계 목표 반영", "범위 확대 / 일정 +5~8일 / 정책 협의 필요", "task 0018, R-08", "보류", "", "", "보류"),
]

# --------------------------------------------------------------------------- information distribution (actual records)
DISTRIBUTIONS = [
    # date, info, form, from, to, channel, ref
    ("2026-11-07", "demo 앱 소스 업로드", "코드", "jihyeon821", "원본 저장소", "GitHub push", "39c2817"),
    ("2026-11-07", "고도화 저장소 생성(Private, 이력 포함)", "저장소", "jihyeon821", "고도화 저장소", "GitHub", "safety-alert-system-daejeon-dev"),
    ("2026-11-07", "AI 서브에이전트 구성", "설정", "ORC", "프로젝트 팀(에이전트)", "GitHub push", "4e11285"),
    ("2026-11-07", "AI 작업 하네스·프로젝트 분석 문서", "문서·코드", "ORC", "프로젝트 팀", "GitHub push", "99c7f02"),
    ("2026-11-07", "의존성 오류 수정", "코드", "ORC", "프로젝트 팀", "GitHub push", "3df4d56"),
    ("2026-11-07", "모델 1회 로드 개선", "코드", "BE", "프로젝트 팀", "GitHub push", "c39690c"),
    ("2026-11-07", "요구사항정의서·작업 목록", "문서", "ORC", "프로젝트 오너", "GitHub push", "4f79588"),
    ("2026-11-07", "PM 산출물 34종", "문서", "ORC", "프로젝트 오너", "GitHub push", "task 0020"),
]

# --------------------------------------------------------------------------- supplier / option evaluation
SUPPLIER_CRITERIA = [("기능 적합성", 0.30), ("비용", 0.20), ("개인정보·보안", 0.25), ("운영 용이성", 0.15), ("라이선스·약관", 0.10)]
SUPPLIER_OPTIONS = [
    # category, option, scores per criterion (1-5), note
    ("알림 채널", "카카오톡 (n8n 연동)", [5, 4, 3, 3, 3], "보호자 접근성 높음, 개발자 권한 필요"),
    ("알림 채널", "텔레그램 (n8n 노드)", [3, 5, 3, 4, 4], "연동 쉬움, 보호자 가입·사용률 낮음"),
    ("알림 채널", "문자(SMS) 게이트웨이", [4, 2, 4, 4, 4], "유료, 도달률 높음"),
    ("재학습 GPU", "Google Colab (A100)", [5, 4, 3, 5, 4], "기존 학습 환경과 같음"),
    ("재학습 GPU", "로컬 GPU", [3, 5, 5, 2, 5], "장비 미보유 (가정)"),
    ("설명 LLM", "Gemma-3-1B GGUF (현행)", [3, 5, 5, 5, 3], "CPU 동작, 품질 한계"),
    ("설명 LLM", "더 큰 로컬 LLM (예: 4B급 GGUF)", [4, 5, 5, 2, 3], "메모리·속도 부담, 저사양 PC 실행 어려움"),
    ("설명 LLM", "외부 LLM API", [5, 2, 1, 4, 3], "발화 데이터 외부 전송 → 개인정보 위험"),
]


# =========================================================================== derived schedule
import math
from datetime import date, timedelta

_HOL = {date.fromisoformat(h) for h in HOLIDAYS}
TASKS = {t["id"]: t for t in REQ["tasks"]}
REQS = {q["id"]: q for q in REQ["requirements"]}


def is_workday(d: date) -> bool:
    return d.weekday() < 5 and d not in _HOL


def workday(d: date, n: int) -> date:
    """Excel WORKDAY semantics (n >= 0)."""
    step = 0
    while step < n:
        d += timedelta(days=1)
        if is_workday(d):
            step += 1
    return d


def networkdays(a: date, b: date) -> int:
    return sum(1 for i in range((b - a).days + 1) if is_workday(a + timedelta(days=i)))


def pert(o, m, p) -> float:
    return (o + 4 * m + p) / 6


SCHEDULE = {}   # id -> dict(start, finish, dur, done)
for a in ACTIVITIES:
    aid, _, _, _, _, (o, m, p), preds, _, actual = a
    if actual:
        s, f, _pct = actual
        SCHEDULE[aid] = {"start": date.fromisoformat(s), "finish": date.fromisoformat(f), "dur": 1, "done": True}
    else:
        dur = math.ceil(round(pert(o, m, p), 6))
        prev = max(SCHEDULE[x]["finish"] for x in preds)
        start = workday(prev, 1)
        SCHEDULE[aid] = {"start": start, "finish": workday(start, dur - 1), "dur": dur, "done": False}
PROJECT_FINISH = max(v["finish"] for v in SCHEDULE.values())

# WBS work-package codes for activities (e.g. "3" -> 3.1, 3.2 ...)
WP_CODE = {}
_counter: dict[str, int] = {}
for a in ACTIVITIES:
    parent = a[1]
    _counter[parent] = _counter.get(parent, 0) + 1
    WP_CODE[a[0]] = f"{parent}.{_counter[parent]}"

SUCCESSORS = {a[0]: [b[0] for b in ACTIVITIES if a[0] in b[6]] for a in ACTIVITIES}
ROLE_NAME = {r[0]: r[1] for r in ROLES}


def activity_cost(a) -> float:
    """Planned cost of one activity: owner labour + GPU for retraining (assumptions)."""
    own = a[7].get("OWN", 0) * RATES["OWN"][2]
    gpu = 2 * RATES["GPU"][2] if a[0] == "A18" else 0
    return own + gpu


def reqs_of(a) -> str:
    t = TASKS.get(a[3])
    return t["reqs"] if t else ""


def detail_of(a) -> str:
    t = TASKS.get(a[3])
    if t:
        return t["detail"]
    return {
        "A06": "계획 산출물(범위·일정·원가 기준선)을 검토하고 승인합니다. 가정값을 실제 값으로 확정합니다.",
        "A25": "실제 모델 가중치와 Python 3.10·Rust 환경에서 파일 선택→분석→표→알림까지 E2E 시나리오를 실행합니다.",
        "A26": "담당 공무원·보호자 관점 시나리오로 결과를 검토하고 인수 여부를 결정합니다.",
        "A27": "단계·프로젝트 종료 보고서와 교훈을 정리하고 저장소를 인계 가능한 상태로 정리합니다.",
    }.get(a[0], "")
