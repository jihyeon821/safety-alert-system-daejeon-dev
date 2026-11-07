#!/usr/bin/env python3
"""Build a requirements-specification workbook (and harness task files) from JSON.

Reusable: point it at another project's requirements.json with the same schema.

Usage:
    python ai/tools/build_requirements.py docs/요구사항/requirements.json docs/요구사항/요구사항정의서.xlsx [--sync-tasks]

--sync-tasks creates ai/tasks/NNNN-*.md for every task in the JSON that has no file yet.
Requires openpyxl.
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

ROOT = Path(__file__).resolve().parents[2]
FONT = "맑은 고딕"
NAVY = "1F3864"
F_BASE = Font(name=FONT, size=10)
F_BOLD = Font(name=FONT, size=10, bold=True)
F_HEAD = Font(name=FONT, size=10, bold=True, color="FFFFFF")
F_TITLE = Font(name=FONT, size=16, bold=True, color=NAVY)
F_SUB = Font(name=FONT, size=11, bold=True, color=NAVY)
F_INPUT = Font(name=FONT, size=10, color="0000FF")      # hardcoded inputs
F_LINK = Font(name=FONT, size=10, color="008000")       # cross-sheet links
F_NOTE = Font(name=FONT, size=9, italic=True, color="595959")
FILL_HEAD = PatternFill("solid", fgColor=NAVY)
FILL_SUB = PatternFill("solid", fgColor="D9E1F2")
FILL_ASSUME = PatternFill("solid", fgColor="FFFF00")
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
WRAP = Alignment(wrap_text=True, vertical="top")
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)

STATUS_FILL = {"구현완료": "E2EFDA", "부분구현": "FFF2CC", "미구현": "EDEDED", "결함": "F8CBAD",
               "완료": "E2EFDA", "대기": "EDEDED", "진행중": "DDEBF7", "보류": "FFF2CC"}

REQ_SHEET, TASK_SHEET = "요구사항 목록", "작업 목록"
REQ_FIRST, REQ_LAST = 5, 300        # formula ranges cover blank rows so new entries count
TASK_FIRST, TASK_LAST = 5, 300


def header_row(ws, row: int, headers: list[str], widths: list[int] | None = None) -> None:
    for c, h in enumerate(headers, 1):
        cell = ws.cell(row=row, column=c, value=h)
        cell.font, cell.fill, cell.alignment, cell.border = F_HEAD, FILL_HEAD, CENTER, BORDER
        if widths:
            ws.column_dimensions[get_column_letter(c)].width = widths[c - 1]


def body_cell(ws, row: int, col: int, value, font=F_BASE, align=WRAP, fmt: str | None = None):
    cell = ws.cell(row=row, column=col, value=value)
    cell.font, cell.alignment, cell.border = font, align, BORDER
    if fmt:
        cell.number_format = fmt
    return cell


def title(ws, text: str, sub: str) -> None:
    ws["A1"] = text
    ws["A1"].font = F_TITLE
    ws["A2"] = sub
    ws["A2"].font = F_NOTE


def status_colors(ws, col_letter: str, first: int, last: int, values: list[str]) -> None:
    rng = f"{col_letter}{first}:{col_letter}{last}"
    for v in values:
        ws.conditional_formatting.add(rng, FormulaRule(
            formula=[f'${col_letter}{first}="{v}"'], fill=PatternFill(fill_type="solid", start_color=STATUS_FILL[v], end_color=STATUS_FILL[v])))


def dropdown(ws, col_letter: str, first: int, last: int, values: list[str]) -> None:
    dv = DataValidation(type="list", formula1='"' + ",".join(values) + '"', allow_blank=True)
    dv.error, dv.errorTitle = "목록에서 선택하세요: " + ", ".join(values), "입력 값 오류"
    ws.add_data_validation(dv)
    dv.add(f"{col_letter}{first}:{col_letter}{last}")


# --------------------------------------------------------------------------- sheets

def sheet_cover(wb: Workbook, spec: dict) -> None:
    ws = wb.active
    ws.title = "표지"
    m = spec["meta"]
    ws.column_dimensions["A"].width, ws.column_dimensions["B"].width = 18, 95
    title(ws, m["document"], m["project"])
    rows = [("문서명", m["document"]), ("프로젝트", m["project"]), ("버전", m["version"]),
            ("작성일", m["date"]), ("작성자", m["author"]), ("저장소", m["repository"]),
            ("분석 기준", m["basis"]), ("유의사항", m["note"])]
    for i, (k, v) in enumerate(rows, 4):
        body_cell(ws, i, 1, k, F_BOLD).fill = FILL_SUB
        body_cell(ws, i, 2, v)

    r = len(rows) + 6
    ws.cell(row=r, column=1, value="시트 구성").font = F_SUB
    sheets = [("요약", "분류·상태·우선순위별 집계 (수식, 자동 갱신)"),
              (REQ_SHEET, "기능·비기능 요구사항, 수용 기준, 구현 상태, 관련 작업"),
              (TASK_SHEET, "요구사항을 수행 작업으로 분해한 목록 (ai/tasks/NNNN-*.md와 같은 번호)"),
              ("모델 성능", "혼동 행렬 기반 클래스별 정밀도·재현율·F1과 목표 대비 달성 여부")]
    for i, (k, v) in enumerate(sheets, r + 1):
        body_cell(ws, i, 1, k, F_BOLD)
        body_cell(ws, i, 2, v)

    r += len(sheets) + 2
    ws.cell(row=r, column=1, value="범례").font = F_SUB
    legend = [("ID 규칙", "FR-분류-번호 = 기능, NFR-분류-번호 = 비기능 (DA 데이터분석, LB 라벨링, ML 모델, API 백엔드, UI 화면, NT 알림, PF 성능, SC 보안, QA 품질, OP 운영, AV/PT 가용성)"),
              ("우선순위", "상: 안전·동작에 직결 / 중: 기능 품질 / 하: 개선"),
              ("구현 상태", "구현완료 / 부분구현 / 미구현 / 결함(구현은 됐지만 요구대로 동작하지 않음)"),
              ("작업 상태", "완료 / 대기 / 진행중 / 보류(의사결정 필요)"),
              ("편집 방법", "'요구사항 목록'·'작업 목록'의 우선순위·상태 열은 드롭다운으로 수정합니다. 요약 시트는 수식이라 자동으로 갱신됩니다. 원본 데이터는 docs/요구사항/requirements.json이고, 다시 생성하면 덮어씁니다."),
              ("글자색", "파란색 = 직접 입력한 값(원본 CSV 등) / 초록색 = 다른 시트 참조 / 노란 배경 = 확정이 필요한 가정값")]
    for i, (k, v) in enumerate(legend, r + 1):
        body_cell(ws, i, 1, k, F_BOLD)
        body_cell(ws, i, 2, v)


def sheet_requirements(wb: Workbook, spec: dict) -> None:
    ws = wb.create_sheet(REQ_SHEET)
    title(ws, "요구사항 목록", "구현 상태는 코드 분석 결과입니다. 관련 작업 번호는 '작업 목록' 시트와 ai/tasks/ 파일을 가리킵니다.")
    headers = ["요구사항 ID", "구분", "분류", "요구사항명", "상세 설명", "수용 기준", "우선순위",
               "출처(근거)", "구현 상태", "관련 작업", "비고"]
    header_row(ws, 4, headers, [12, 7, 13, 22, 48, 40, 8, 30, 10, 10, 40])
    for i, q in enumerate(spec["requirements"], REQ_FIRST):
        vals = [q["id"], q["type"], q["category"], q["name"], q["desc"], q["acceptance"],
                q["priority"], q["source"], q["status"], q["tasks"], q["note"]]
        for c, v in enumerate(vals, 1):
            body_cell(ws, i, c, v, align=CENTER if c in (1, 2, 3, 7, 9, 10) else WRAP)
    status_colors(ws, "I", REQ_FIRST, REQ_LAST, spec["statuses"])
    dropdown(ws, "G", REQ_FIRST, REQ_LAST, spec["priorities"])
    dropdown(ws, "I", REQ_FIRST, REQ_LAST, spec["statuses"])
    ws.freeze_panes = "B5"
    ws.auto_filter.ref = f"A4:K{REQ_FIRST + len(spec['requirements']) - 1}"


def sheet_tasks(wb: Workbook, spec: dict) -> None:
    ws = wb.create_sheet(TASK_SHEET)
    title(ws, "작업 목록", "미완료 요구사항을 작업으로 나눈 목록입니다. 작업 ID = ai/tasks/ 파일 번호. 선행 작업이 끝나야 시작할 수 있습니다.")
    headers = ["작업 ID", "작업명", "관련 요구사항", "담당 에이전트", "우선순위", "상태", "선행 작업", "작업 내용"]
    header_row(ws, 4, headers, [9, 30, 22, 18, 8, 9, 10, 80])
    for i, t in enumerate(spec["tasks"], TASK_FIRST):
        vals = [t["id"], t["title"], t["reqs"], t["agent"], t["priority"], t["status"], t["depends"], t["detail"]]
        for c, v in enumerate(vals, 1):
            body_cell(ws, i, c, v, align=CENTER if c in (1, 4, 5, 6, 7) else WRAP)
    status_colors(ws, "F", TASK_FIRST, TASK_LAST, spec["task_statuses"])
    dropdown(ws, "E", TASK_FIRST, TASK_LAST, spec["priorities"])
    dropdown(ws, "F", TASK_FIRST, TASK_LAST, spec["task_statuses"])
    ws.freeze_panes = "C5"
    ws.auto_filter.ref = f"A4:H{TASK_FIRST + len(spec['tasks']) - 1}"


def sheet_summary(wb: Workbook, spec: dict) -> None:
    ws = wb.create_sheet("요약", 1)
    title(ws, "요약", "모든 값은 '요구사항 목록'·'작업 목록' 시트를 참조하는 수식입니다.")
    R = f"'{REQ_SHEET}'!"
    cat_rng, stat_rng, pri_rng, type_rng = (f"{R}${c}${REQ_FIRST}:${c}${REQ_LAST}" for c in "CIGB")
    statuses = spec["statuses"]
    categories = list(dict.fromkeys(q["category"] for q in spec["requirements"]))

    # 1) category x status
    ws["A4"] = "분류별 구현 상태"
    ws["A4"].font = F_SUB
    header_row(ws, 5, ["분류", *statuses, "합계", "완료율"], [16, 11, 11, 11, 11, 10, 10])
    first = 6
    for i, cat in enumerate(categories, first):
        body_cell(ws, i, 1, cat, F_BOLD)
        for j, _ in enumerate(statuses, 2):
            col = get_column_letter(j)
            body_cell(ws, i, j, f'=COUNTIFS({cat_rng},$A{i},{stat_rng},{col}$5)', F_LINK, CENTER)
        tot = get_column_letter(len(statuses) + 2)
        body_cell(ws, i, len(statuses) + 2, f"=SUM(B{i}:{get_column_letter(len(statuses) + 1)}{i})", F_BOLD, CENTER)
        body_cell(ws, i, len(statuses) + 3, f"=IFERROR(B{i}/{tot}{i},0)", F_BASE, CENTER, "0%")
    last = first + len(categories) - 1
    t = last + 1
    body_cell(ws, t, 1, "합계", F_BOLD).fill = FILL_SUB
    for j in range(2, len(statuses) + 3):
        col = get_column_letter(j)
        body_cell(ws, t, j, f"=SUM({col}{first}:{col}{last})", F_BOLD, CENTER).fill = FILL_SUB
    tot = get_column_letter(len(statuses) + 2)
    body_cell(ws, t, len(statuses) + 3, f"=IFERROR(B{t}/{tot}{t},0)", F_BOLD, CENTER, "0%").fill = FILL_SUB
    check = t + 1
    body_cell(ws, check, 1, "검산", F_NOTE)
    body_cell(ws, check, 2, f'=IF({tot}{t}=COUNTA({R}$A${REQ_FIRST}:$A${REQ_LAST}),"일치","불일치: 상태 값 확인")',
              F_NOTE, CENTER)
    ws.merge_cells(start_row=check, start_column=2, end_row=check, end_column=len(statuses) + 3)

    # 2) priority x status (open items)
    p0 = check + 2
    ws.cell(row=p0, column=1, value="우선순위별 현황").font = F_SUB
    header_row(ws, p0 + 1, ["우선순위", *statuses, "합계", "미완료"])
    for i, pri in enumerate(spec["priorities"], p0 + 2):
        body_cell(ws, i, 1, pri, F_BOLD, CENTER)
        for j, _ in enumerate(statuses, 2):
            col = get_column_letter(j)
            body_cell(ws, i, j, f'=COUNTIFS({pri_rng},$A{i},{stat_rng},{col}${p0 + 1})', F_LINK, CENTER)
        body_cell(ws, i, len(statuses) + 2, f"=SUM(B{i}:{get_column_letter(len(statuses) + 1)}{i})", F_BOLD, CENTER)
        body_cell(ws, i, len(statuses) + 3, f"={tot}{i}-B{i}", F_BOLD, CENTER)

    # 3) type
    k0 = p0 + 2 + len(spec["priorities"]) + 1
    ws.cell(row=k0, column=1, value="구분별 건수").font = F_SUB
    header_row(ws, k0 + 1, ["구분", "건수"])
    for i, typ in enumerate(["기능", "비기능"], k0 + 2):
        body_cell(ws, i, 1, typ, F_BOLD, CENTER)
        body_cell(ws, i, 2, f'=COUNTIF({type_rng},$A{i})', F_LINK, CENTER)

    # 4) tasks
    T = f"'{TASK_SHEET}'!"
    tstat = f"{T}$F${TASK_FIRST}:$F${TASK_LAST}"
    s0 = k0 + 5
    ws.cell(row=s0, column=1, value="작업 진행 현황").font = F_SUB
    header_row(ws, s0 + 1, ["상태", "작업 수"])
    for i, st in enumerate(spec["task_statuses"], s0 + 2):
        body_cell(ws, i, 1, st, F_BOLD, CENTER)
        body_cell(ws, i, 2, f'=COUNTIF({tstat},$A{i})', F_LINK, CENTER)
    e = s0 + 2 + len(spec["task_statuses"])
    body_cell(ws, e, 1, "진행률", F_BOLD, CENTER).fill = FILL_SUB
    body_cell(ws, e, 2, f"=IFERROR(B{s0 + 2}/SUM(B{s0 + 2}:B{e - 1}),0)", F_BOLD, CENTER, "0%").fill = FILL_SUB


def sheet_performance(wb: Workbook, spec: dict) -> None:
    perf = spec.get("performance")
    if not perf:
        return
    ws = wb.create_sheet("모델 성능")
    title(ws, "모델 성능", "NFR-QA-01/02 판정 근거입니다. 파란 숫자는 results/*.csv 원본 값이고, 나머지는 수식입니다.")
    with (ROOT / perf["confusion_matrix_csv"]).open(encoding="utf-8-sig") as f:
        cm = list(csv.reader(f))
    labels = [h.replace("Pred ", "") for h in cm[0][1:]]
    n = len(labels)

    ws["A4"] = "혼동 행렬 (행 = 실제, 열 = 예측)"
    ws["A4"].font = F_SUB
    header_row(ws, 5, ["실제 \\ 예측", *labels, "실제 합계"], [22, 13, 13, 13, 13, 13, 13])
    r0 = 6
    for i, row in enumerate(cm[1:], r0):
        body_cell(ws, i, 1, labels[i - r0], F_BOLD, CENTER)
        for j, v in enumerate(row[1:], 2):
            body_cell(ws, i, j, int(v), F_INPUT, CENTER, "#,##0")
        body_cell(ws, i, n + 2, f"=SUM(B{i}:{get_column_letter(n + 1)}{i})", F_BOLD, CENTER, "#,##0")
    rl = r0 + n - 1
    body_cell(ws, rl + 1, 1, "예측 합계", F_BOLD, CENTER).fill = FILL_SUB
    for j in range(2, n + 3):
        col = get_column_letter(j)
        body_cell(ws, rl + 1, j, f"=SUM({col}{r0}:{col}{rl})", F_BOLD, CENTER, "#,##0").fill = FILL_SUB
    ws.cell(row=r0, column=1).comment = Comment(f"출처: {perf['confusion_matrix_csv']} (평가 세트 혼동 행렬)", "harness")

    m0 = rl + 3
    ws.cell(row=m0, column=1, value="클래스별 지표").font = F_SUB
    header_row(ws, m0 + 1, ["클래스", "정밀도", "재현율", "F1", "지원 수(실제)"])
    for k in range(n):
        i, rr = m0 + 2 + k, r0 + k
        diag = f"{get_column_letter(k + 2)}{rr}"
        body_cell(ws, i, 1, labels[k], F_BOLD, CENTER)
        body_cell(ws, i, 2, f"=IFERROR({diag}/{get_column_letter(k + 2)}{rl + 1},0)", F_BASE, CENTER, "0.0%")
        body_cell(ws, i, 3, f"=IFERROR({diag}/{get_column_letter(n + 2)}{rr},0)", F_BASE, CENTER, "0.0%")
        body_cell(ws, i, 4, f"=IFERROR(2*B{i}*C{i}/(B{i}+C{i}),0)", F_BASE, CENTER, "0.000")
        body_cell(ws, i, 5, f"={get_column_letter(n + 2)}{rr}", F_BASE, CENTER, "#,##0")
    ml = m0 + 1 + n
    diag_sum = "+".join(f"{get_column_letter(k + 2)}{r0 + k}" for k in range(n))
    a = ml + 1
    body_cell(ws, a, 1, "정확도", F_BOLD, CENTER).fill = FILL_SUB
    body_cell(ws, a, 2, f"=IFERROR(({diag_sum})/{get_column_letter(n + 2)}{rl + 1},0)", F_BOLD, CENTER, "0.0%")
    body_cell(ws, a + 1, 1, "macro F1", F_BOLD, CENTER).fill = FILL_SUB
    body_cell(ws, a + 1, 2, f"=AVERAGE(D{m0 + 2}:D{ml})", F_BOLD, CENTER, "0.000")

    g0 = a + 3
    ws.cell(row=g0, column=1, value="목표 대비 판정").font = F_SUB
    header_row(ws, g0 + 1, ["지표", "현재값", "목표값(가정)", "차이", "판정", "관련 요구사항"])
    emer = labels.index("emergency") if "emergency" in labels else n - 1
    goals = [("macro F1", f"=B{a + 1}", perf["targets"]["macro_f1"], "0.000", "NFR-QA-01"),
             ("emergency 재현율", f"=C{m0 + 2 + emer}", perf["targets"]["emergency_recall"], "0.0%", "NFR-QA-02")]
    for i, (name, cur, tgt, fmt, req) in enumerate(goals, g0 + 2):
        body_cell(ws, i, 1, name, F_BOLD, CENTER)
        body_cell(ws, i, 2, cur, F_BASE, CENTER, fmt)
        c = body_cell(ws, i, 3, tgt, F_INPUT, CENTER, fmt)
        c.fill = FILL_ASSUME
        c.comment = Comment(perf["targets_note"], "harness")
        body_cell(ws, i, 4, f"=B{i}-C{i}", F_BASE, CENTER, fmt)
        body_cell(ws, i, 5, f'=IF(B{i}>=C{i},"달성","미달")', F_BOLD, CENTER)
        body_cell(ws, i, 6, req, F_BASE, CENTER)
    ws.conditional_formatting.add(f"E{g0 + 2}:E{g0 + 3}", FormulaRule(
        formula=[f'$E{g0 + 2}="미달"'], fill=PatternFill(fill_type="solid", start_color=STATUS_FILL["결함"], end_color=STATUS_FILL["결함"])))
    ws.conditional_formatting.add(f"E{g0 + 2}:E{g0 + 3}", FormulaRule(
        formula=[f'$E{g0 + 2}="달성"'], fill=PatternFill(fill_type="solid", start_color=STATUS_FILL["구현완료"], end_color=STATUS_FILL["구현완료"])))
    note = ws.cell(row=g0 + 4, column=1, value="※ 노란 칸의 목표값은 제안값(가정)입니다. 확정하면 판정이 자동으로 바뀝니다.")
    note.font = F_NOTE

    # training history
    with (ROOT / perf["training_history_csv"]).open(encoding="utf-8-sig") as f:
        hist = list(csv.DictReader(f))
    h0 = g0 + 6
    ws.cell(row=h0, column=1, value="학습 이력 (검증 세트)").font = F_SUB
    header_row(ws, h0 + 1, ["epoch", "train loss", "train acc", "val F1 (macro)", "val F1 (weighted)"])
    for i, h in enumerate(hist, h0 + 2):
        body_cell(ws, i, 1, int(h["epoch"]), F_INPUT, CENTER)
        body_cell(ws, i, 2, float(h["train_loss"]), F_INPUT, CENTER, "0.000")
        body_cell(ws, i, 3, float(h["train_acc"]), F_INPUT, CENTER, "0.0%")
        body_cell(ws, i, 4, float(h["val_f1_macro"]), F_INPUT, CENTER, "0.000")
        body_cell(ws, i, 5, float(h["val_f1_weighted"]), F_INPUT, CENTER, "0.000")
    hl = h0 + 1 + len(hist)
    ws.cell(row=h0 + 2, column=1).comment = Comment(f"출처: {perf['training_history_csv']}", "harness")
    b = hl + 1
    body_cell(ws, b, 1, "최고 val F1", F_BOLD, CENTER).fill = FILL_SUB
    body_cell(ws, b, 4, f"=MAX(D{h0 + 2}:D{hl})", F_BOLD, CENTER, "0.000")
    body_cell(ws, b + 1, 1, "최고 epoch", F_BOLD, CENTER).fill = FILL_SUB
    body_cell(ws, b + 1, 4, f"=INDEX(A{h0 + 2}:A{hl},MATCH(D{b},D{h0 + 2}:D{hl},0))", F_BOLD, CENTER)


# --------------------------------------------------------------------------- tasks

def sync_tasks(spec: dict) -> list[str]:
    tasks_dir = ROOT / "ai" / "tasks"
    template = (ROOT / "ai" / "templates" / "task.md").read_text(encoding="utf-8")
    req_by_id = {q["id"]: q for q in spec["requirements"]}
    created = []
    for t in spec["tasks"]:
        if list(tasks_dir.glob(f"{t['id']}-*.md")):
            continue
        slug = re.sub(r"[^\w]+", "-", t["title"].lower(), flags=re.UNICODE).strip("-")
        reqs = [r.strip() for r in t["reqs"].split(",") if r.strip() in req_by_id]
        body = template.replace("{{ID}}", t["id"]).replace("{{TITLE}}", t["title"]) \
                       .replace("{{DATE}}", spec["meta"]["date"])
        body = body.replace("- 상태: 진행중", f"- 상태: {t['status']}")
        body = body.replace("- 담당 에이전트:", f"- 담당 에이전트: {t['agent']}\n- 우선순위: {t['priority']}"
                            + (f"\n- 선행 작업: {t['depends']}" if t["depends"] else ""))
        goal = "\n".join(f"- **{r}** {req_by_id[r]['name']}: {req_by_id[r]['desc']}" for r in reqs)
        accept = "\n".join(f"- [ ] {r}: {req_by_id[r]['acceptance']}" for r in reqs)
        body = body.replace("<!-- 무엇을 왜 하는가 -->", goal or t["title"])
        body = body.replace("- [ ] `python ai/harness.py check` error 0\n- [ ]",
                            f"- [ ] `python ai/harness.py check` error 0\n{accept}")
        body = body.replace("<!-- 수정할 파일, API 계약 영향 여부 -->", t["detail"])
        path = tasks_dir / f"{t['id']}-{slug}.md"
        path.write_text(body, encoding="utf-8")
        created.append(path.relative_to(ROOT).as_posix())
    return created


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 2:
        print(__doc__)
        return 2
    spec = json.loads((ROOT / args[0]).read_text(encoding="utf-8"))
    wb = Workbook()
    sheet_cover(wb, spec)
    sheet_requirements(wb, spec)
    sheet_tasks(wb, spec)
    sheet_summary(wb, spec)
    sheet_performance(wb, spec)
    wb.calculation.fullCalcOnLoad = True
    out = ROOT / args[1]
    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)
    print(f"wrote {out.relative_to(ROOT).as_posix()} "
          f"({len(spec['requirements'])} requirements, {len(spec['tasks'])} tasks)")
    if "--sync-tasks" in sys.argv:
        for p in sync_tasks(spec):
            print(f"created {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
