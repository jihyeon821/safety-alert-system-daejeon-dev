"""Generate the 20 xlsx PM deliverables."""
from __future__ import annotations

from datetime import date, datetime, timedelta

from openpyxl.chart import LineChart, Reference
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import PatternFill
from openpyxl.utils import get_column_letter as L

import plan as P
from kit import (CENTER, FILL_SUB, cell, dropdown, new_book, note, sheet, status_colors, subtitle, table)

OUT = P.DOCS
FOLDER = {"1": "1_착수", "2": "2_계획", "3": "3_실행", "4": "4_감시통제", "5": "5_종료"}
DATE_FMT = "yyyy-mm-dd"
WON = '#,##0"원";-#,##0"원";"-"'


def dt(d) -> datetime:
    d = date.fromisoformat(d) if isinstance(d, str) else d
    return datetime(d.year, d.month, d.day)


def save(wb, group: str, name: str):
    path = OUT / FOLDER[group] / name
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)
    return path


def holidays_block(ws, top: int, col: int = 1) -> str:
    """Write holiday list and return absolute range string."""
    cell(ws, top, col, "공휴일", "head")
    for i, h in enumerate(P.HOLIDAYS, top + 1):
        cell(ws, i, col, dt(h), "input", DATE_FMT, CENTER)
    return f"${L(col)}${top + 1}:${L(col)}${top + len(P.HOLIDAYS)}"


# =========================================================================== 1 착수
def x02_stakeholders():
    wb = new_book()
    ws = sheet(wb, "이해관계자등록부", "02. 이해관계자 등록부", "착수·실행(이해관계자 관리)")
    cols = [("ID", 8, "c"), ("이해관계자", 26), ("프로젝트 내 역할", 20), ("관심사", 22), ("영향력(1-5)", 9, "c"),
            ("관심도(1-5)", 9, "c"), ("우선순위 점수", 9, "c"), ("관리 전략", 12, "c"), ("기대사항", 32), ("연락 채널", 18)]
    rows = []
    r0 = 5
    for i, s in enumerate(P.STAKEHOLDERS):
        r = r0 + i
        contact = (s[8], "base", "assume") if "확인 필요" in s[8] else s[8]
        rows.append([s[0], s[1], s[2], s[3], (s[4], "input"), (s[5], "input"), f"=E{r}*F{r}", s[7], s[6], contact])
    f, l = table(ws, 4, cols, rows)
    dropdown(ws, f"E{f}:F{l + 20}", ["1", "2", "3", "4", "5"])
    subtitle(ws, l + 2, "영향력·관심도 격자 (관리 전략 기준)")
    grid = [["구분", "관심도 낮음(1-3)", "관심도 높음(4-5)"],
            ["영향력 높음(4-5)", "만족 유지 (모니터링·요청 시 보고)", "긴밀 협의 (주요 의사결정 참여)"],
            ["영향력 낮음(1-3)", "모니터링", "정보 제공 (정기 공유)"]]
    for i, row in enumerate(grid, l + 3):
        for j, v in enumerate(row, 1):
            cell(ws, i, j + 1, v, "head" if i == l + 3 or j == 1 else "base")
    note(ws, l + 7, "노란 칸 = 저장소에서 확인할 수 없는 정보입니다. 실제 연락처로 채워 주세요. 점수 = 영향력 × 관심도")
    return save(wb, "1", "02_이해관계자등록부.xlsx")


def x03_team():
    wb = new_book()
    ws = sheet(wb, "팀 구성", "03. 프로젝트 팀 구성 및 역할 배정", "착수·실행(팀 개발·지원 획득·팀 관리)")
    cols = [("역할 코드", 9, "c"), ("역할", 18), ("구분", 11, "c"), ("담당", 28), ("책임", 60)]
    rows = [[r[0], r[1], r[2], (r[3], "base", "assume") if "확인" in r[3] else r[3], r[4]] for r in P.ROLES]
    f, l = table(ws, 4, cols, rows)
    note(ws, l + 2, "AI 에이전트 정의: ai/agents/*.md (.claude/agents로 동기화). 원 개발팀원 명단은 저장소에 없어 [확인 필요]로 표시했습니다.")

    ws2 = sheet(wb, "RACI", "역할 배정 매트릭스 (RACI)", "R 수행 · A 승인 · C 협의 · I 통보")
    codes = P.ROLE_CODES
    cols2 = [("활동 ID", 8, "c"), ("WBS", 7, "c"), ("활동", 30)] + [(c, 7, "c") for c in codes]
    rows2 = []
    for a in P.ACTIVITIES:
        roles = {c: "" for c in codes}
        roles["OWN"] = "A"
        roles[a[4]] = "R" if a[4] != "OWN" else "A/R"
        for c, h in a[7].items():
            if not roles[c] and h:
                roles[c] = "C" if c == "RV" else "R"
        if a[0] in ("A16", "A18", "A24", "A25"):
            roles["TM"] = "C"
        for c in codes:
            if not roles[c]:
                roles[c] = "I" if c in ("ORC",) else ""
        rows2.append([a[0], P.WP_CODE[a[0]], a[2]] + [roles[c] for c in codes])
    f2, l2 = table(ws2, 4, cols2, rows2)
    dropdown(ws2, f"D{f2}:{L(3 + len(codes))}{l2}", ["R", "A", "A/R", "C", "I"])
    subtitle(ws2, l2 + 2, "역할별 R(수행) 건수")
    for i, c in enumerate(codes):
        col = L(4 + i)
        cell(ws2, l2 + 3, 4 + i, c, "head")
        cell(ws2, l2 + 4, 4 + i, f'=COUNTIF({col}{f2}:{col}{l2},"R")+COUNTIF({col}{f2}:{col}{l2},"A/R")', "bold", None, CENTER)
    cell(ws2, l2 + 4, 3, "R 건수", "bold", fill="sub")

    ws3 = sheet(wb, "팀 관리 기록", "팀 개발·지원 획득·팀 관리 기록", "관례 산출물(표 공란)")
    note(ws3, 3, "실행 단계에서 팀 역량 개발, 자원 지원 요청, 팀 관리 활동을 기록하는 양식입니다. 날짜순으로 한 행씩 추가하세요.")
    table(ws3, 4, [("일자", 12, "c", DATE_FMT), ("프로세스", 14, "c"), ("내용", 50), ("대상", 18), ("결과·조치", 40), ("기록자", 12, "c")], [], 20)
    dropdown(ws3, "B5:B24", ["팀 개발", "지원 획득", "팀 관리"])
    return save(wb, "1", "03_프로젝트팀구성_역할배정.xlsx")


# =========================================================================== 2 계획
def x07_requirements():
    wb = new_book()
    ws = sheet(wb, "요구사항 수집", "07. 요구사항 수집서", "요구사항 44건 · 상세: docs/요구사항/요구사항정의서.xlsx")
    stake = {"데이터 분석": "SH-02", "라벨링": "SH-02", "모델": "SH-01, SH-03", "백엔드 API": "SH-01, SH-02",
             "데스크톱 UI": "SH-03", "알림": "SH-03, SH-04, SH-06", "성능": "SH-01, SH-03",
             "보안·개인정보": "SH-05, SH-07", "품질": "SH-03, SH-04", "운영·배포": "SH-01, SH-02", "가용성": "SH-03"}
    act_by_task = {}
    for a in P.ACTIVITIES:
        if a[3]:
            act_by_task.setdefault(a[3], []).append(a[0])
    cols = [("수집 ID", 9, "c"), ("요구사항 ID", 11, "c"), ("구분", 7, "c"), ("요구사항명", 22), ("이해관계자(출처)", 14, "c"),
            ("수집 방법", 11, "c"), ("근거 문서", 28), ("요구 내용", 44), ("수용 기준", 36), ("우선순위", 8, "c"),
            ("현재 상태", 9, "c"), ("추적: 작업 / 활동", 16, "c")]
    rows = []
    for i, q in enumerate(P.REQ["requirements"], 1):
        src = q["source"]
        method = "문서 분석" if src.startswith("README") else (
            "산출물 분석" if src.startswith(("notebooks", "results")) else "코드 분석")
        tasks = [t.strip() for t in q["tasks"].split(",") if t.strip()]
        acts = sorted({x for t in tasks for x in act_by_task.get(t, [])})
        trace = " / ".join(filter(None, [", ".join(tasks), ", ".join(acts)])) or "-"
        rows.append([f"RC-{i:02d}", q["id"], q["type"], q["name"], stake[q["category"]], method, src, q["desc"],
                     q["acceptance"], q["priority"], q["status"], trace])
    f, l = table(ws, 4, cols, rows)
    dropdown(ws, f"J{f}:J{l}", ["상", "중", "하"])
    ws.auto_filter.ref = f"A4:L{l}"
    subtitle(ws, l + 2, "수집 방법별 건수")
    for i, m in enumerate(["문서 분석", "산출물 분석", "코드 분석", "인터뷰"], l + 3):
        cell(ws, i, 1, m, "bold")
        cell(ws, i, 2, f'=COUNTIF($F${f}:$F${l},A{i})', "base", None, CENTER)
    note(ws, l + 8, "인터뷰(담당 공무원·보호자 대상)는 아직 실시하지 않았습니다. 인수 검토(A26) 전에 실시를 권장합니다.")
    return save(wb, "2", "07_요구사항수집서.xlsx")


def x09_wbs():
    wb = new_book()
    ws = sheet(wb, "WBS", "09. WBS (작업분류체계)", f"총 {len(P.ACTIVITIES)}개 작업 패키지")
    cols = [("WBS 코드", 10, "c"), ("수준", 6, "c"), ("요소명", 40), ("설명", 46), ("산출물", 28), ("담당", 16, "c")]
    rows = []
    for code, name, lvl, desc, deliv in P.WBS:
        rows.append([code, lvl, ("  " * (lvl - 1)) + name, desc, deliv, "OWN"])
        for a in P.ACTIVITIES:
            if a[1] == code:
                rows.append([P.WP_CODE[a[0]], lvl + 1, ("  " * lvl) + a[2], P.detail_of(a)[:80],
                             f"task {a[3]}" if a[3] else "-", a[4]])
    rows.sort(key=lambda r: [int(x) for x in str(r[0]).split(".")])
    f, l = table(ws, 4, cols, rows)
    for r in range(f, l + 1):
        if ws.cell(row=r, column=2).value == 1:
            for c in range(1, 7):
                ws.cell(row=r, column=c).fill = FILL_SUB

    ws2 = sheet(wb, "WBS 사전", "WBS 사전", "작업 패키지별 정의")
    cols2 = [("WBS 코드", 9, "c"), ("작업 패키지", 26), ("활동 ID", 8, "c"), ("작업 내용", 52), ("관련 요구사항", 20),
             ("인수 기준", 36), ("담당", 9, "c"), ("기간(일)", 8, "c"), ("선행", 14, "c")]
    rows2 = []
    for a in P.ACTIVITIES:
        reqs = [r.strip() for r in P.reqs_of(a).split(",") if r.strip() in P.REQS]
        acc = "; ".join(P.REQS[r]["acceptance"] for r in reqs) or "산출물 승인 / 하네스 검사 error 0"
        rows2.append([P.WP_CODE[a[0]], a[2], a[0], P.detail_of(a), P.reqs_of(a) or "-", acc, a[4],
                      P.SCHEDULE[a[0]]["dur"], ", ".join(a[6]) or "-"])
    table(ws2, 4, cols2, rows2)
    return save(wb, "2", "09_WBS_WBS사전.xlsx")


def x11_activities():
    wb = new_book()
    ws = sheet(wb, "활동목록", "11. 활동 목록표", "WBS 작업 패키지를 수행 활동으로 정의")
    cols = [("활동 ID", 8, "c"), ("WBS", 7, "c"), ("활동명", 28), ("활동 설명", 56), ("관련 작업", 9, "c"),
            ("관련 요구사항", 20), ("담당 역할", 14, "c"), ("선행 활동", 16, "c"), ("상태", 8, "c")]
    rows = [[a[0], P.WP_CODE[a[0]], a[2], P.detail_of(a), a[3] or "-", P.reqs_of(a) or "-",
             P.ROLE_NAME[a[4]], ", ".join(a[6]) or "-", "완료" if a[8] else "대기"] for a in P.ACTIVITIES]
    f, l = table(ws, 4, cols, rows)
    status_colors(ws, "I", f, l, ["완료", "대기", "진행중", "보류"])
    dropdown(ws, f"I{f}:I{l}", ["완료", "대기", "진행중", "보류"])
    subtitle(ws, l + 2, "마일스톤")
    ms = [[m[0], m[1], ", ".join(m[2]), m[3] or "계획"] for m in P.MILESTONES]
    table(ws, l + 3, [("ID", 8, "c"), ("마일스톤", 28), ("완료 기준 활동", 30), ("상태", 16, "c")], ms, freeze=False)
    return save(wb, "2", "11_활동목록표.xlsx")


def x12_network():
    wb = new_book()
    ws = sheet(wb, "공정표", "12. 프로젝트 공정표 (활동 순서·주공정)",
               "작업일 기준 전진·후진 계산 · 1단계 완료 활동(A01~A05)은 기간 0", assumptions=True)
    acts = P.ACTIVITIES
    idx = {a[0]: i for i, a in enumerate(acts)}
    top = 5
    first = top + 1
    cols = [("활동 ID", 8, "c"), ("활동명", 28), ("선행", 18, "c"), ("관계", 7, "c"), ("후행", 18, "c"),
            ("기간(일)", 8, "c"), ("ES", 6, "c"), ("EF", 6, "c"), ("LS", 6, "c"), ("LF", 6, "c"),
            ("총여유", 7, "c"), ("주공정", 8, "c")]
    rows = []
    last = first + len(acts) - 1
    for i, a in enumerate(acts):
        r = first + i
        preds, succs = a[6], P.SUCCESSORS[a[0]]
        dur = 0 if a[8] else P.SCHEDULE[a[0]]["dur"]
        es = "=0" if not preds else "=MAX(" + ",".join(f"H{first + idx[p]}" for p in preds) + ")"
        lf = f"=MAX($H${first}:$H${last})" if not succs else "=MIN(" + ",".join(f"I{first + idx[s]}" for s in succs) + ")"
        rows.append([a[0], a[2], ", ".join(preds) or "-", "FS", ", ".join(succs) or "-",
                     (dur, "input", None, "13_일정견적서의 적용 기간(PERT 올림)" if not a[8] else "완료 활동"),
                     es, f"=G{r}+F{r}", f"=J{r}-F{r}", lf, f"=I{r}-G{r}", f'=IF(K{r}=0,"주공정","")'])
    f, l = table(ws, top, cols, rows)
    ws.conditional_formatting.add(f"A{f}:L{l}", FormulaRule(formula=[f'$L{f}="주공정"'],
                                                             fill=PatternFill(fill_type="solid", start_color="FCE4D6", end_color="FCE4D6")))
    cell(ws, l + 2, 1, "총 공기(작업일)", "bold", fill="sub")
    cell(ws, l + 2, 3, f"=MAX(H{f}:H{l})", "bold", None, CENTER)
    cell(ws, l + 3, 1, "주공정 활동 수", "bold", fill="sub")
    cell(ws, l + 3, 3, f'=COUNTIF(L{f}:L{l},"주공정")', "bold", None, CENTER)
    note(ws, l + 5, "ES/EF/LS/LF는 착수일(작업일 0) 기준 작업일 수입니다. 관계는 모두 FS(종료-시작), 지연 0. 실제 날짜는 14_상세일정표 참고.")
    return save(wb, "2", "12_프로젝트공정표.xlsx")


def x13_estimates():
    wb = new_book()
    ws = sheet(wb, "일정견적", "13. 일정 견적서 (활동 기간 산정)", "3점 추정(PERT)", assumptions=True)
    cols = [("활동 ID", 8, "c"), ("활동명", 30), ("담당", 9, "c"), ("낙관(O)", 8, "c"), ("보통(M)", 8, "c"),
            ("비관(P)", 8, "c"), ("PERT 기대값", 10, "c", "0.00"), ("표준편차", 9, "c", "0.00"), ("적용 기간(일)", 10, "c"),
            ("산정 근거", 46)]
    basis = {"A16": "노트북 02·04, 백엔드 3곳 수정 + 라벨 재생성", "A18": "A100 GPU 5에포크 학습 + 실험 반복",
             "A21": "n8n 워크플로우 변경 포함", "A25": "모델·환경 준비 포함", "A20": "기관 협의 일정 불확실"}
    rows = []
    top = 5
    for i, a in enumerate([a for a in P.ACTIVITIES if not a[8]]):
        r = top + 1 + i
        o, m, p = a[5]
        rows.append([a[0], a[2], a[4], (o, "input", "assume"), (m, "input", "assume"), (p, "input", "assume"),
                     f"=(D{r}+4*E{r}+F{r})/6", f"=(F{r}-D{r})/6", f"=ROUNDUP(G{r},0)",
                     basis.get(a[0], "유사 작업(0001~0004) 실적 기반 추정")])
    f, l = table(ws, top, cols, rows)
    cell(ws, l + 2, 2, "합계 (활동 기간 단순 합, 병행 미반영)", "bold", fill="sub")
    for c in "GI":
        cell(ws, l + 2, " ABCDEFGHI".index(c), f"=SUM({c}{f}:{c}{l})", "bold", "0.0", CENTER)
    note(ws, l + 4, "단위: 작업일. 1단계 완료 활동(A01~A05)은 실적이 있어 제외했습니다(25_작업성과 참고). 적용 기간은 14_상세일정표에 반영됩니다.")
    return save(wb, "2", "13_일정견적서.xlsx")


def x14_schedule():
    wb = new_book()
    ws = sheet(wb, "상세일정", "14. 상세 일정표", "WORKDAY 수식 기반 · 간트 차트", assumptions=True)
    acts = P.ACTIVITIES
    idx = {a[0]: i for i, a in enumerate(acts)}
    top = 5
    first = top + 1
    last = first + len(acts) - 1
    hol_row = last + 6
    hol = holidays_block(ws, hol_row, 3)
    week0 = date(2026, 11, 2)
    weeks = [week0 + timedelta(weeks=k) for k in range(((P.PROJECT_FINISH - week0).days // 7) + 2)]
    base_cols = [("활동 ID", 8, "c"), ("WBS", 7, "c"), ("활동명", 28), ("담당", 7, "c"), ("선행", 14, "c"),
                 ("기간(일)", 7, "c"), ("시작", 11, "c", DATE_FMT), ("종료", 11, "c", DATE_FMT), ("상태", 7, "c")]
    cols = base_cols + [(w.strftime("%m/%d"), 6, "c") for w in weeks]
    rows = []
    for i, a in enumerate(acts):
        r = first + i
        s = P.SCHEDULE[a[0]]
        if a[8]:
            start = (dt(s["start"]), "input", None, "실적")
            finish = (dt(s["finish"]), "input", None, "실적")
        else:
            start = f"=WORKDAY(MAX(" + ",".join(f"H{first + idx[p]}" for p in a[6]) + f"),1,{hol})"
            finish = f"=WORKDAY(G{r},F{r}-1,{hol})"
        rows.append([a[0], P.WP_CODE[a[0]], a[2], a[4], ", ".join(a[6]) or "-",
                     (s["dur"], "input", None if a[8] else "assume"), start, finish,
                     "완료" if a[8] else "계획"] + [""] * len(weeks))
    f, l = table(ws, top, cols, rows)
    for k, w in enumerate(weeks):
        c = ws.cell(row=top, column=10 + k)
        c.value = dt(w)
        c.number_format = "mm/dd"
    g1, g2 = L(10), L(9 + len(weeks))
    rng = f"{g1}{f}:{g2}{l}"
    ws.conditional_formatting.add(rng, FormulaRule(
        formula=[f'AND($I{f}="완료",{g1}${top}<=$H{f},{g1}${top}+6>=$G{f})'], fill=PatternFill(fill_type="solid", start_color="70AD47", end_color="70AD47")))
    ws.conditional_formatting.add(rng, FormulaRule(
        formula=[f'AND({g1}${top}<=$H{f},{g1}${top}+6>=$G{f})'], fill=PatternFill(fill_type="solid", start_color="4472C4", end_color="4472C4")))
    status_colors(ws, "I", f, l, ["완료"])
    cell(ws, l + 2, 3, "프로젝트 종료일", "bold", fill="sub")
    cell(ws, l + 2, 8, f"=MAX(H{f}:H{l})", "bold", DATE_FMT, CENTER)
    cell(ws, l + 3, 3, "총 작업일 (착수~종료)", "bold", fill="sub")
    cell(ws, l + 3, 8, f"=NETWORKDAYS(G{f},H{l + 2},{hol})", "bold", None, CENTER)
    note(ws, hol_row - 1, "공휴일 목록 (WORKDAY 계산에서 제외). 필요하면 행을 추가하고 수식 범위를 넓히세요.", 3)
    note(ws, l + 4, "간트: 초록 = 완료, 파랑 = 계획. 주 시작일(월) 기준. 기간을 바꾸면 시작·종료일이 다시 계산됩니다.")
    return save(wb, "2", "14_상세일정표.xlsx")


def _rates_block(ws, top: int) -> dict:
    """Writes the assumption rate table, returns {key: absolute cell}."""
    subtitle(ws, top, "단가 (가정)")
    cell(ws, top + 1, 1, "항목", "head"); cell(ws, top + 1, 2, "단위", "head"); cell(ws, top + 1, 3, "단가", "head")
    refs = {}
    for i, (k, (name, unit, val)) in enumerate(P.RATES.items(), top + 2):
        cell(ws, i, 1, name, "bold")
        cell(ws, i, 2, unit, "base", None, CENTER)
        cell(ws, i, 3, val, "input", "0%" if unit == "비율" else WON, CENTER, "assume", "가정값: 실제 단가·요금으로 교체")
        refs[k] = f"$C${i}"
    return refs


def x16_cost():
    wb = new_book()
    ws = sheet(wb, "원가산정", "16. 원가 산정서", "활동별 상향식 산정", assumptions=True)
    ws.column_dimensions["A"].width = 28
    refs = _rates_block(ws, 5)
    top = 5 + len(P.RATES) + 4
    subtitle(ws, top - 1, "활동별 원가")
    cols = [("활동 ID", 28, "c"), ("활동명", 14), ("오너 시간(h)", 11, "c", "0.0"), ("인건비", 13, "c", WON),
            ("직접비(GPU 등)", 13, "c", WON), ("활동 원가", 13, "c", WON), ("비고", 34)]
    rows = []
    for i, a in enumerate(P.ACTIVITIES):
        r = top + 1 + i
        gpu = f"=2*{refs['GPU']}" if a[0] == "A18" else 0
        rows.append([a[0], a[2], (a[7].get("OWN", 0), "input", None, "19_자원소요계획서 오너 시간"),
                     f"=C{r}*{refs['OWN']}", gpu, f"=D{r}+E{r}",
                     "재학습 GPU 2회" if a[0] == "A18" else ("실적(1단계)" if a[8] else "")])
    f, l = table(ws, top, cols, rows, freeze=False)
    cell(ws, l + 1, 1, "활동 원가 소계", "bold", fill="sub")
    for c in "CDEF":
        cell(ws, l + 1, " ABCDEF".index(c), f"=SUM({c}{f}:{c}{l})", "bold", "0.0" if c == "C" else WON, CENTER, "sub")

    o0 = l + 4
    subtitle(ws, o0 - 1, "기간 비용·기타")
    cols2 = [("항목", 28), ("단위", 14, "c"), ("수량", 11, "c"), ("단가", 13, "c", WON), ("", 13), ("금액", 13, "c", WON), ("비고", 34)]
    rows2 = []
    for i, (name, unit, qty, rk, nt) in enumerate(P.OTHER_COSTS):
        r = o0 + 1 + i
        price = f"={refs[rk]}" if isinstance(rk, str) else (rk, "input")
        rows2.append([name, unit, (qty, "input", "assume"), price, "", f"=C{r}*D{r}", nt])
    of, ol = table(ws, o0, cols2, rows2, freeze=False)
    gpu_note_row = ol + 1
    cell(ws, gpu_note_row, 1, "기타 소계 (GPU는 활동 원가에 포함되어 제외)", "bold", fill="sub")
    gpu_row = next(o0 + 1 + i for i, c in enumerate(P.OTHER_COSTS) if c[3] == "GPU")
    cell(ws, gpu_note_row, 6, f"=SUM(F{of}:F{ol})-F{gpu_row}", "bold", WON, CENTER, "sub")

    s0 = gpu_note_row + 3
    subtitle(ws, s0 - 1, "원가 요약")
    summ = [("활동 원가 (A)", f"=F{l + 1}"), ("기간 비용·기타 (B)", f"=F{gpu_note_row}"),
            ("원가 기준선 (C = A + B)", f"=C{s0}+C{s0 + 1}"), ("관리 예비비 (D = C × 예비비율)", f"=C{s0 + 2}*{refs['RES']}"),
            ("총 예산 (C + D)", f"=C{s0 + 2}+C{s0 + 3}")]
    for i, (k, v) in enumerate(summ, s0):
        cell(ws, i, 1, k, "bold", fill="sub")
        cell(ws, i, 3, v, "bold", WON, CENTER)
    note(ws, s0 + 6, "AI 에이전트 작업 시간은 이용료(월정액)에 포함되어 시간당 원가를 따로 매기지 않습니다. 금액은 모두 가정값 기반입니다.")
    return save(wb, "2", "16_원가산정서.xlsx")


def x17_budget():
    wb = new_book()
    ws = sheet(wb, "예산서", "17. 예산서 및 S-Curve", "주별 계획 원가(PV) 누적", assumptions=True)
    top = 5
    acts = P.ACTIVITIES
    first, last = top + 1, top + len(acts)
    hol = holidays_block(ws, last + 20, 1)
    week0 = date(2026, 11, 2)
    weeks = [week0 + timedelta(weeks=k) for k in range(((P.PROJECT_FINISH - week0).days // 7) + 1)]
    cols = [("활동 ID", 9, "c"), ("활동명", 26), ("시작", 11, "c", DATE_FMT), ("종료", 11, "c", DATE_FMT),
            ("활동 원가", 12, "c", WON), ("일 원가", 11, "c", WON)] + [(w.strftime("주 %m/%d"), 11, "c", WON) for w in weeks]
    rows = []
    for i, a in enumerate(acts):
        r = first + i
        s = P.SCHEDULE[a[0]]
        row = [a[0], a[2], (dt(s["start"]), "input", None, "14_상세일정표"), (dt(s["finish"]), "input", None, "14_상세일정표"),
               (P.activity_cost(a), "input", None, "16_원가산정서"),
               f"=E{r}/MAX(1,NETWORKDAYS(C{r},D{r},{hol}))"]
        for k in range(len(weeks)):
            wc = L(7 + k)
            ws_, we = f"{wc}${last + 3}", f"{wc}${last + 4}"
            if a[8]:   # actual work on a Saturday -> book the whole cost in its week
                row.append(f"=IF(AND($C{r}>={ws_},$C{r}<={we}+1),$E{r},0)")
            else:
                row.append(f"=IF(AND($C{r}<={we},$D{r}>={ws_}),$F{r}*NETWORKDAYS(MAX($C{r},{ws_}),MIN($D{r},{we}),{hol}),0)")
        rows.append(row)
    f, l = table(ws, top, cols, rows)
    # week boundary rows + totals
    labels = [("주 시작", None), ("주 종료(금)", None), ("활동 원가 PV", None), ("기간 비용 배분", None), ("주별 PV 합계", None), ("누적 PV", None)]
    r_ws, r_we, r_act, r_per, r_tot, r_cum = last + 3, last + 4, last + 5, last + 6, last + 7, last + 8
    period_total = sum(c[2] * P.RATES[c[3]][2] for c in P.OTHER_COSTS if c[3] == "AI")
    cell(ws, r_per, 5, period_total, "input", WON, CENTER, "assume", "16_원가산정서 기간 비용(AI 도구 이용료), 주별 균등 배분")
    for i, (lab, _) in enumerate(labels):
        cell(ws, last + 3 + i, 2, lab, "bold", fill="sub")
    for k, w in enumerate(weeks):
        col = 7 + k
        c = L(col)
        cell(ws, r_ws, col, dt(w), "base", DATE_FMT, CENTER)
        cell(ws, r_we, col, dt(w + timedelta(days=4)), "base", DATE_FMT, CENTER)
        cell(ws, r_act, col, f"=SUM({c}{f}:{c}{l})", "base", WON, CENTER)
        cell(ws, r_per, col, f"=$E${r_per}/{len(weeks)}", "base", WON, CENTER)
        cell(ws, r_tot, col, f"={c}{r_act}+{c}{r_per}", "bold", WON, CENTER)
        cell(ws, r_cum, col, f"={c}{r_tot}" if k == 0 else f"={L(col - 1)}{r_cum}+{c}{r_tot}", "bold", WON, CENTER)
    end = L(6 + len(weeks))
    cell(ws, r_cum + 2, 2, "원가 기준선 (PV 합계)", "bold", fill="sub")
    cell(ws, r_cum + 2, 5, f"={end}{r_cum}", "bold", WON, CENTER)
    cell(ws, r_cum + 3, 2, "검산: 활동 원가 합계 + 기간 비용", "bold", fill="sub")
    cell(ws, r_cum + 3, 5, f"=SUM(E{f}:E{l})+E{r_per}", "bold", WON, CENTER)
    cell(ws, r_cum + 4, 2, "일치 여부", "bold", fill="sub")
    cell(ws, r_cum + 4, 5, f'=IF(ABS(E{r_cum + 2}-E{r_cum + 3})<1,"일치","불일치")', "bold", None, CENTER)
    cell(ws, r_cum + 5, 2, "관리 예비비 (기준선 × 10%, 16_원가산정서)", "bold", fill="sub")
    cell(ws, r_cum + 5, 5, f"=E{r_cum + 2}*{P.RATES['RES'][2]}", "bold", WON, CENTER)
    cell(ws, r_cum + 6, 2, "총 예산", "bold", fill="sub")
    cell(ws, r_cum + 6, 5, f"=E{r_cum + 2}+E{r_cum + 5}", "bold", WON, CENTER)

    chart = LineChart()
    chart.title = "S-Curve (누적 계획 원가)"
    chart.y_axis.title = "원"
    chart.x_axis.title = "주"
    chart.height, chart.width = 7.5, 18
    data = Reference(ws, min_col=7, max_col=6 + len(weeks), min_row=r_cum, max_row=r_cum)
    chart.add_data(data, from_rows=True, titles_from_data=False)
    chart.set_categories(Reference(ws, min_col=7, max_col=6 + len(weeks), min_row=r_ws, max_row=r_ws))
    chart.legend = None
    ws.add_chart(chart, f"H{r_cum + 2}")
    note(ws, last + 19, "공휴일 목록 (NETWORKDAYS 계산에서 제외)")
    note(ws, r_cum + 8, "1단계 실적(토요일 수행)은 해당 주에 전액 반영. 기간 비용은 주별로 균등 배분했습니다.")
    return save(wb, "2", "17_예산서_S-Curve.xlsx")


def x19_resources():
    wb = new_book()
    ws = sheet(wb, "자원소요", "19. 자원 소요 계획서", "활동별·역할별 소요 시간", assumptions=True)
    codes = [c for c in P.ROLE_CODES if c != "TM"]
    cols = [("활동 ID", 8, "c"), ("활동명", 28)] + [(f"{c}\n{P.ROLE_NAME[c]}", 11, "c", "0.0") for c in codes] + [("합계(h)", 9, "c", "0.0")]
    top = 5
    rows = []
    for i, a in enumerate(P.ACTIVITIES):
        r = top + 1 + i
        rows.append([a[0], a[2]] + [(a[7].get(c, 0), "input", None if a[8] else "assume") for c in codes]
                    + [f"=SUM(C{r}:{L(2 + len(codes))}{r})"])
    f, l = table(ws, top, cols, rows)
    cell(ws, l + 1, 2, "합계", "bold", fill="sub")
    for j in range(len(codes) + 1):
        c = L(3 + j)
        cell(ws, l + 1, 3 + j, f"=SUM({c}{f}:{c}{l})", "bold", "0.0", CENTER, "sub")
    cell(ws, l + 2, 2, "비중", "bold", fill="sub")
    tot = f"${L(3 + len(codes))}${l + 1}"
    for j in range(len(codes)):
        c = L(3 + j)
        cell(ws, l + 2, 3 + j, f"=IFERROR({c}{l + 1}/{tot},0)", "base", "0%", CENTER)

    ws2 = sheet(wb, "비인력 자원", "비인력 자원 소요", "")
    res = [["Python 3.10 가상환경", "개발·실행", "A07~A25", "필수", "PC에는 3.14 설치됨 → 3.10 별도 설치 필요"],
           ["Rust 툴체인 (cargo)", "Tauri 빌드", "A12~A15, A25", "필수", "미설치"],
           ["Node.js LTS", "Tauri CLI", "A12~A15", "필수", "v24 설치됨"],
           ["KCBERT 가중치·토크나이저", "추론·재학습", "A18, A19, A25", "필수", "저장소에 없음 → 원 팀원에게 인계 요청"],
           ["Gemma-3-1B GGUF", "설명 생성", "A25", "필수", "저장소에 없음"],
           ["원본·라벨링 데이터", "라벨 재생성·재학습", "A16, A18", "필수", "저장소에 없음, 개인정보"],
           ["클라우드 GPU (A100급)", "재학습", "A18", "필수", "16_원가산정서 GPU 비용"],
           ["n8n 인스턴스·카카오 개발자 계정", "알림", "A21, A25", "필수", "원 팀 워크플로우 확인 필요"],
           ["GitHub Private 저장소", "형상 관리", "전체", "필수", "준비됨"]]
    table(ws2, 4, [("자원", 30), ("용도", 16), ("필요 활동", 16, "c"), ("구분", 8, "c"), ("확보 현황", 40)], res)
    note(ws, l + 4, "OWN 시간은 사람의 투입(원가 산정 기준), AI 에이전트 시간은 작업량 지표(이용료에 포함)입니다. 1단계 실적은 추정 실적입니다.")
    return save(wb, "2", "19_자원소요계획서.xlsx")


def x21_risks():
    wb = new_book()
    ws = sheet(wb, "위기등록부", "21. 위기(리스크) 등록부", "계획·실행(위기 처리)·감시통제(위기 통제)")
    cols = [("ID", 7, "c"), ("분류", 10, "c"), ("위기", 24), ("원인", 30), ("영향", 28), ("발생 가능성(1-5)", 9, "c"),
            ("영향도(1-5)", 9, "c"), ("점수", 7, "c"), ("등급", 7, "c"), ("대응 유형", 9, "c"), ("대응 계획", 34),
            ("담당", 7, "c"), ("징후(트리거)", 22), ("상태", 13, "c")]
    top = 5
    rows = []
    for i, k in enumerate(P.RISKS):
        r = top + 1 + i
        rows.append([k[0], k[1], k[2], k[3], k[4], (k[5], "input"), (k[6], "input"), f"=F{r}*G{r}",
                     f'=IF(H{r}>=15,"높음",IF(H{r}>=8,"중간","낮음"))', k[7], k[8], k[9], k[10], k[11]])
    f, l = table(ws, top, cols, rows)
    status_colors(ws, "I", f, l, ["높음", "중간", "낮음"])
    dropdown(ws, f"F{f}:G{l + 20}", ["1", "2", "3", "4", "5"])
    dropdown(ws, f"J{f}:J{l + 20}", ["회피", "전가", "완화", "수용"])
    ws.auto_filter.ref = f"A{top}:N{l}"
    subtitle(ws, l + 2, "등급별 건수")
    for i, g in enumerate(["높음", "중간", "낮음"], l + 3):
        cell(ws, i, 2, g, "bold", None, CENTER)
        cell(ws, i, 3, f'=COUNTIF($I${f}:$I${l},B{i})', "base", None, CENTER)
    note(ws, l + 7, "점수 = 가능성 × 영향도. 등급: 15 이상 높음, 8~14 중간, 7 이하 낮음 (20_위기관리계획서 기준).")

    ws2 = sheet(wb, "처리 기록", "위기 처리·통제 기록", "실행·감시통제 단계에서 추가")
    hist = [["2026-11-07", "R-02", "식별", "코드 분석에서 print 발견, 작업 0011 등록", "ORC"],
            ["2026-11-07", "R-03", "식별", "노트북 02·04에서 같은 결함 확인, 작업 0007에 학습·추론 동시 수정으로 명시", "ORC"],
            ["2026-11-07", "R-01", "식별", "혼동 행렬 분석: emergency 재현율 45.0%", "ORC"]]
    table(ws2, 4, [("일자", 12, "c"), ("위기 ID", 9, "c"), ("활동", 10, "c"), ("내용", 60), ("기록자", 9, "c")],
          [[dt(h[0])] + h[1:] for h in hist], 15)
    for r in range(5, 5 + len(hist) + 15):
        ws2.cell(row=r, column=1).number_format = DATE_FMT
    dropdown(ws2, "C5:C30", ["식별", "평가", "대응", "종결", "재평가"])
    return save(wb, "2", "21_위기등록부.xlsx")


# =========================================================================== 3 실행
def _ev_table(ws, top: int, status_cell: str, hol: str, rate_note: str, freeze: bool = True) -> tuple[int, int]:
    cols = [("활동 ID", 8, "c"), ("활동명", 26), ("계획 시작", 11, "c", DATE_FMT), ("계획 종료", 11, "c", DATE_FMT),
            ("실제 시작", 11, "c", DATE_FMT), ("실제 종료", 11, "c", DATE_FMT), ("진척률", 8, "c", "0%"),
            ("BAC", 12, "c", WON), ("PV", 12, "c", WON), ("EV", 12, "c", WON), ("AC", 12, "c", WON), ("상태", 8, "c")]
    rows = []
    for i, a in enumerate(P.ACTIVITIES):
        r = top + 1 + i
        s = P.SCHEDULE[a[0]]
        done = bool(a[8])
        cost = P.activity_cost(a)
        pv = (f"=IF({status_cell}>=D{r},H{r},IF({status_cell}<C{r},0,"
              f"H{r}*NETWORKDAYS(C{r},{status_cell},{hol})/MAX(1,NETWORKDAYS(C{r},D{r},{hol}))))")
        rows.append([a[0], a[2], (dt(s["start"]), "input"), (dt(s["finish"]), "input"),
                     (dt(s["start"]), "input") if done else None, (dt(s["finish"]), "input") if done else None,
                     (1.0 if done else 0.0, "input"), (cost, "input", None, "16_원가산정서 활동 원가"), pv, f"=G{r}*H{r}",
                     (cost if done else 0, "input", "assume" if done else None, rate_note if done else None),
                     f'=IF(G{r}>=1,"완료",IF(G{r}>0,"진행중","대기"))'])
    f, l = table(ws, top, cols, rows, freeze=freeze)
    status_colors(ws, "L", f, l, ["완료", "진행중", "대기"])
    return f, l


def x25_performance():
    wb = new_book()
    ws = sheet(wb, "작업성과", "25. 작업 성과 · 진척 데이터", "활동별 진척률과 획득가치(EV)", assumptions=True)
    cell(ws, 4, 1, "기준일", "bold", fill="sub")
    cell(ws, 4, 2, dt(P.META["status_date"]), "input", DATE_FMT, CENTER, "assume", "진척 측정 기준일. 바꾸면 PV가 다시 계산됩니다.")
    top = 6
    hol = holidays_block(ws, top + len(P.ACTIVITIES) + 12, 1)
    f, l = _ev_table(ws, top, "$B$4", hol, "실적 원가 = 계획과 같다고 가정 (실제 투입 시간 기록 필요)")
    cell(ws, l + 1, 2, "합계", "bold", fill="sub")
    for c in "HIJK":
        cell(ws, l + 1, " ABCDEFGHIJK".index(c), f"=SUM({c}{f}:{c}{l})", "bold", WON, CENTER, "sub")
    cell(ws, l + 3, 2, "완료 활동 수", "bold", fill="sub")
    cell(ws, l + 3, 3, f'=COUNTIF(L{f}:L{l},"완료")&" / "&COUNTA(A{f}:A{l})', "bold", None, CENTER)
    cell(ws, l + 4, 2, "전체 진척률 (EV / BAC)", "bold", fill="sub")
    cell(ws, l + 4, 3, f"=IFERROR(J{l + 1}/H{l + 1},0)", "bold", "0.0%", CENTER)
    note(ws, l + 6, "진척률·실제 일자·AC를 갱신하면 32_프로젝트성과보고서 계산의 근거가 됩니다. 진척률 기준: 완료 100%, 진행 중은 담당자 판단.")
    note(ws, l + 11, "공휴일 목록")
    return save(wb, "3", "25_작업성과_진척데이터.xlsx")


def x26_issues():
    wb = new_book()
    ws = sheet(wb, "이슈관리대장", "26. 이슈 관리 대장", "실행(이해관계자 관리)")
    cols = [("ID", 7, "c"), ("등록일", 11, "c", DATE_FMT), ("제목", 24), ("내용", 36), ("우선순위", 8, "c"),
            ("관련 요구사항", 16, "c"), ("담당", 7, "c"), ("상태", 10, "c"), ("조치·해결", 36), ("종결일", 11, "c", DATE_FMT),
            ("경과일", 7, "c")]
    top = 5
    rows = []
    for i, s in enumerate(P.ISSUES):
        r = top + 1 + i
        rows.append([s[0], dt(s[1]), s[2], s[3], s[4], s[5], s[6], s[7], s[8], dt(s[9]) if s[9] else None,
                     f'=IF(J{r}="",TODAY()-B{r},J{r}-B{r})'])
    f, l = table(ws, top, cols, rows, 10)
    status_colors(ws, "H", f, l + 10, ["해결", "미해결", "부분 해결"])
    dropdown(ws, f"H{f}:H{l + 10}", ["미해결", "부분 해결", "해결"])
    dropdown(ws, f"E{f}:E{l + 10}", ["상", "중", "하"])
    subtitle(ws, l + 12, "상태별 건수")
    for i, st in enumerate(["미해결", "부분 해결", "해결"], l + 13):
        cell(ws, i, 2, st, "bold", None, CENTER)
        cell(ws, i, 3, f'=COUNTIF($H${f}:$H${l + 10},B{i})', "base", None, CENTER)
    note(ws, l + 17, "출처: ai/context/KNOWN_ISSUES.md, 작업 기록 ai/tasks/. 경과일은 미해결이면 오늘 기준으로 계산됩니다.")
    return save(wb, "3", "26_이슈관리대장.xlsx")


def x28_knowledge():
    wb = new_book()
    ws = sheet(wb, "지식관리대장", "28. 지식 관리 대장", "관례 산출물(표 공란)")
    note(ws, 3, "프로젝트 중 얻은 지식(기술 노하우, 결정 근거, 참고 자료)을 등록하는 양식입니다. 한 행에 한 건씩 기록하세요.")
    cols = [("ID", 8, "c"), ("등록일", 11, "c", DATE_FMT), ("분류", 12, "c"), ("제목", 26), ("내용 요약", 46),
            ("출처·위치", 26), ("관련 활동", 10, "c"), ("등록자", 10, "c"), ("공유 대상", 14, "c")]
    table(ws, 4, cols, [], 25)
    dropdown(ws, "C5:C29", ["기술", "도메인", "의사결정", "도구", "절차", "기타"])
    return save(wb, "3", "28_지식관리대장.xlsx")


def x29_qa():
    wb = new_book()
    ws = sheet(wb, "품질보증수행기록", "29. 품질 보증 수행 기록", "관례 산출물(표 공란)")
    note(ws, 3, "품질 보증 활동(하네스 검사, 코드 리뷰, 감사)을 기록하는 양식입니다. 기준은 22_품질관리계획서를 따릅니다.")
    cols = [("ID", 8, "c"), ("수행일", 11, "c", DATE_FMT), ("활동 유형", 12, "c"), ("대상", 22), ("기준", 26),
            ("결과", 9, "c"), ("발견 사항", 36), ("시정 조치", 30), ("수행자", 10, "c"), ("확인자", 10, "c")]
    table(ws, 4, cols, [], 25)
    dropdown(ws, "C5:C29", ["하네스 검사", "코드 리뷰", "테스트", "품질 감사", "문서 검토"])
    dropdown(ws, "F5:F29", ["적합", "부적합", "조건부"])
    return save(wb, "3", "29_품질보증수행기록.xlsx")


def x30_distribution():
    wb = new_book()
    ws = sheet(wb, "정보배포기록", "30. 정보 배포 기록", "24_의사소통관리계획서에 따른 배포 이력")
    cols = [("No", 6, "c"), ("배포일", 11, "c", DATE_FMT), ("정보", 34), ("형태", 10, "c"), ("발신", 12, "c"),
            ("수신", 18, "c"), ("채널", 14, "c"), ("참조(커밋·위치)", 28)]
    rows = [[i, dt(d[0])] + list(d[1:]) for i, d in enumerate(P.DISTRIBUTIONS, 1)]
    f, l = table(ws, 4, cols, rows, 15)
    note(ws, l + 2, "1단계 배포 이력은 git log 기준입니다. 이후 주간 보고·회의록 배포를 같은 형식으로 추가하세요.")
    return save(wb, "3", "30_정보배포기록.xlsx")


def x31_suppliers():
    wb = new_book()
    ws = sheet(wb, "공급자선정평가", "31. 공급자(외부 서비스·도구) 선정 평가서", "가중 점수 평가(안)", assumptions=True)
    subtitle(ws, 4, "평가 기준과 가중치")
    for i, (name, w) in enumerate(P.SUPPLIER_CRITERIA, 5):
        cell(ws, i, 1, name, "bold")
        cell(ws, i, 2, w, "input", "0%", CENTER, "assume")
    wl = 4 + len(P.SUPPLIER_CRITERIA)
    cell(ws, wl + 1, 1, "가중치 합계", "bold", fill="sub")
    cell(ws, wl + 1, 2, f"=SUM(B5:B{wl})", "bold", "0%", CENTER)
    cell(ws, wl + 1, 3, f'=IF(ABS(B{wl + 1}-1)<0.0001,"정상","합계가 100%가 아님")', "bold", None, CENTER)
    top = wl + 4
    subtitle(ws, top - 1, "후보 평가 (점수 1~5)")
    n = len(P.SUPPLIER_CRITERIA)
    cols = [("분야", 14, "c"), ("후보", 30)] + [(c[0], 11, "c") for c in P.SUPPLIER_CRITERIA] + \
           [("가중 점수", 10, "c", "0.00"), ("분야 내 순위", 10, "c"), ("선정", 8, "c"), ("비고", 36)]
    rows = []
    last = top + len(P.SUPPLIER_OPTIONS)
    sc = L(3 + n)
    for i, (cat, opt, scores, nt) in enumerate(P.SUPPLIER_OPTIONS):
        r = top + 1 + i
        rows.append([cat, opt] + [(s, "input", "assume") for s in scores] + [
            "=" + "+".join(f"{L(3 + j)}{r}*$B${5 + j}" for j in range(n)),
            f'=COUNTIFS($A${top + 1}:$A${last},A{r},${sc}${top + 1}:${sc}${last},">"&{sc}{r})+1',
            f'=IF({L(4 + n)}{r}=1,"선정","")', nt])
    f, l = table(ws, top, cols, rows, freeze=False)
    dropdown(ws, f"C{f}:{L(2 + n)}{l}", ["1", "2", "3", "4", "5"])
    ws.conditional_formatting.add(f"A{f}:{L(6 + n)}{l}", FormulaRule(formula=[f'${L(5 + n)}{f}="선정"'],
                                                                      fill=PatternFill(fill_type="solid", start_color="E2EFDA", end_color="E2EFDA")))
    note(ws, l + 2, "점수와 가중치는 평가(안)입니다. '설명 LLM - 외부 API'는 발화 데이터를 외부로 보내므로 개인정보 기준에서 낮게 평가했습니다.")
    return save(wb, "3", "31_공급자선정평가서.xlsx")


# =========================================================================== 4 감시·통제
def x27_changes():
    wb = new_book()
    ws = sheet(wb, "변경요청서", "27. 변경 요청서 (변경 관리 대장)", "통합 변경 통제 · 범위/일정/원가/자원/위기/품질/조달 통제")
    cols = [("CR ID", 8, "c"), ("요청일", 11, "c", DATE_FMT), ("요청자", 8, "c"), ("제목", 24), ("유형", 11, "c"),
            ("변경 내용", 34), ("사유", 22), ("영향 분석 (범위/일정/원가/품질)", 34), ("관련", 18), ("결정", 8, "c"),
            ("결정자", 10, "c"), ("결정일", 11, "c", DATE_FMT), ("상태", 8, "c")]
    rows = [[c[0], dt(c[1])] + list(c[2:9]) + [c[9], c[10] or None, dt(c[11]) if c[11] else None, c[12]] for c in P.CHANGES]
    f, l = table(ws, 4, cols, rows, 10)
    status_colors(ws, "J", f, l + 10, ["승인", "검토 중", "보류"])
    dropdown(ws, f"J{f}:J{l + 10}", ["검토 중", "승인", "반려", "보류"])
    dropdown(ws, f"E{f}:E{l + 10}", ["결함 수정", "설계 변경", "API 계약 변경", "범위 변경", "범위·품질 변경", "일정 변경", "원가 변경"])
    subtitle(ws, l + 12, "결정별 건수")
    for i, st in enumerate(["승인", "검토 중", "보류", "반려"], l + 13):
        cell(ws, i, 2, st, "bold", None, CENTER)
        cell(ws, i, 3, f'=COUNTIF($J${f}:$J${l + 10},B{i})', "base", None, CENTER)

    ws2 = sheet(wb, "변경요청 양식", "변경 요청서 (개별 양식)", "새 변경 요청 시 이 양식을 복사해 작성")
    fields = ["CR ID", "요청일", "요청자", "제목", "변경 유형", "현재 상태", "변경 내용", "변경 사유",
              "범위 영향", "일정 영향", "원가 영향", "품질 영향", "위기 영향", "관련 요구사항·작업", "대안", "결정 (승인/반려/보류)", "결정자 / 일자", "후속 조치"]
    ws2.column_dimensions["A"].width, ws2.column_dimensions["B"].width = 22, 80
    for i, k in enumerate(fields, 4):
        cell(ws2, i, 1, k, "bold", fill="sub")
        cell(ws2, i, 2, None)
    return save(wb, "4", "27_변경요청서.xlsx")


def x32_report():
    wb = new_book()
    ws = sheet(wb, "성과보고", "32. 프로젝트 성과 보고서", "획득가치(EVM) · 작업 통제 · 원가 통제", assumptions=True)
    cell(ws, 4, 1, "보고 기준일", "bold", fill="sub")
    cell(ws, 4, 2, dt(P.META["status_date"]), "input", DATE_FMT, CENTER, "assume")
    top = 22
    hol = holidays_block(ws, top + len(P.ACTIVITIES) + 4, 1)
    f, l = _ev_table(ws, top, "$B$4", hol, "실적 원가 = 계획과 같다고 가정", freeze=False)
    cell(ws, l + 1, 2, "합계", "bold", fill="sub")
    for c in "HIJK":
        cell(ws, l + 1, " ABCDEFGHIJK".index(c), f"=SUM({c}{f}:{c}{l})", "bold", WON, CENTER, "sub")
    t = l + 1
    subtitle(ws, 6, "획득가치 요약 (활동 원가 기준, 기간 비용 제외)")
    kpis = [("BAC (총 활동 예산)", f"=H{t}", WON, ""), ("PV (계획가치)", f"=I{t}", WON, ""), ("EV (획득가치)", f"=J{t}", WON, ""),
            ("AC (실제원가)", f"=K{t}", WON, ""), ("SV = EV - PV", "=B10-B9", WON, "0 이상이면 일정 정상"),
            ("CV = EV - AC", "=B10-B11", WON, "0 이상이면 원가 정상"), ("SPI = EV / PV", "=IFERROR(B10/B9,0)", "0.00", "1 이상 양호"),
            ("CPI = EV / AC", "=IFERROR(B10/B11,0)", "0.00", "1 이상 양호"), ("EAC = BAC / CPI", "=IFERROR(B8/B15,B8)", WON, "완료 시점 예상 원가"),
            ("ETC = EAC - AC", "=B16-B11", WON, "잔여 예상 원가"), ("VAC = BAC - EAC", "=B8-B16", WON, "예산 대비 차이"),
            ("진척률 (EV / BAC)", "=IFERROR(B10/B8,0)", "0.0%", "")]
    for i, (k, v, fmt, nt) in enumerate(kpis, 8):
        cell(ws, i, 1, k, "bold", fill="sub")
        cell(ws, i, 2, v, "bold", fmt, CENTER)
        cell(ws, i, 3, nt, "note")
    # KPI rows: B8 BAC, B9 PV, B10 EV, B11 AC, B12 SV, B13 CV, B14 SPI, B15 CPI, B16 EAC, B17 ETC, B18 VAC
    cell(ws, 8 + len(kpis), 1, "판정", "bold", fill="sub")
    cell(ws, 8 + len(kpis), 2, '=IF(AND(B14>=1,B15>=1),"정상",IF(OR(B14<0.9,B15<0.9),"위험","주의"))', "bold", None, CENTER)
    subtitle(ws, top - 1, "활동별 진척")
    ws.column_dimensions["A"].width = 22
    ws.column_dimensions["C"].width = 22

    ws2 = sheet(wb, "현황 요약", "현황 요약", f"기준일 {P.META['status_date']}")
    ms = []
    for m in P.MILESTONES:
        fin = max(P.SCHEDULE[x]["finish"] for x in m[2])
        ms.append([m[0], m[1], dt(fin), "달성" if m[3] else "계획"])
    f2, l2 = table(ws2, 4, [("ID", 7, "c"), ("마일스톤", 30), ("계획 일자", 12, "c", DATE_FMT), ("상태", 10, "c")], ms)
    subtitle(ws2, l2 + 2, "주요 현황")
    open_issues = sum(1 for i in P.ISSUES if i[7] != "해결")
    high_risks = sum(1 for k in P.RISKS if k[5] * k[6] >= 15)
    pend_cr = sum(1 for c in P.CHANGES if c[9] != "승인")
    items = [["이슈", f"미해결 {open_issues}건 / 전체 {len(P.ISSUES)}건", "26_이슈관리대장"],
             ["위기", f"높음 등급 {high_risks}건 / 전체 {len(P.RISKS)}건", "21_위기등록부"],
             ["변경 요청", f"결정 대기 {pend_cr}건 / 전체 {len(P.CHANGES)}건", "27_변경요청서"],
             ["다음 기간 계획", "A06 계획 기준선 승인 → 백엔드·프론트 결함 수정(A07~A15) 착수", "14_상세일정표"],
             ["의사결정 요청", "성능 목표값(A17), 알림 정책(A20), 원 팀원 자료 인계(R-04)", "21_위기등록부"]]
    table(ws2, l2 + 3, [("항목", 14, "c"), ("내용", 60), ("근거", 20, "c")], items, freeze=False)
    note(ws2, l2 + 10, "건수는 생성 시점 기준 값입니다. 최신 값은 각 대장의 집계 수식을 확인하세요.")
    return save(wb, "4", "32_프로젝트성과보고서.xlsx")


BUILDERS = [x02_stakeholders, x03_team, x07_requirements, x09_wbs, x11_activities, x12_network, x13_estimates,
            x14_schedule, x16_cost, x17_budget, x19_resources, x21_risks, x25_performance, x26_issues, x27_changes,
            x28_knowledge, x29_qa, x30_distribution, x31_suppliers, x32_report]


def build() -> list:
    return [b() for b in BUILDERS]


if __name__ == "__main__":
    for p in build():
        print(p.relative_to(P.ROOT).as_posix())
