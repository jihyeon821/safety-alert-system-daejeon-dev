"""Build docs/00_산출물목록.xlsx (the user's deliverable list + location, status, summary) and docs/README.md."""
from __future__ import annotations

import re

import openpyxl
from openpyxl.styles import Font

import plan as P
from kit import CENTER, cell, dropdown, new_book, note, sheet, table

SRC = P.DOCS / "_source" / "산출물목록_원본.xlsx"
GROUP_DIR = {"착수": "1_착수", "계획": "2_계획", "실행": "3_실행", "감시·통제": "4_감시통제", "종료": "5_종료"}
SUMMARY = {
    "01": "배경, 측정 가능한 목표, 범위, 마일스톤, 요약 예산, 상위 위기, PM 권한",
    "02": "이해관계자 10개 그룹, 영향력×관심도 점수, 관리 전략",
    "03": "역할 7종(사람·AI 에이전트), RACI 매트릭스, 팀 관리 기록 양식",
    "04": "단계 구성, 범위·일정·자원·예산 요약, 관리 계획 구성",
    "05": "테일러링, 기준선, 변경 통제 절차, 형상 관리, 성과 보고",
    "06": "요구사항 수집 방법, WBS 규칙, 범위 검증·통제, 추적 체계",
    "07": "요구사항 44건의 출처·수집 방법·수용 기준·추적",
    "08": "제품 범위, 포함·제외, 인수 기준, 산출물, 제약·가정",
    "09": "WBS 8개 영역·27개 작업 패키지, WBS 사전",
    "10": "PERT·CPM 방법, 일정 기준선, SPI 통제 기준",
    "11": "활동 27개 정의, 마일스톤 6개",
    "12": "선후행 관계, ES/EF/LS/LF 수식, 주공정",
    "13": "3점 추정(PERT) 수식, 적용 기간",
    "14": "WORKDAY 수식 일정, 간트 차트",
    "15": "원가 구성, EVM 규칙, CPI 통제 기준",
    "16": "단가(가정), 활동별 원가, 예비비, 총 예산 수식",
    "17": "주별 PV 배분 수식, 누적 S-Curve 차트",
    "18": "역할·조직, AI 에이전트 운영 규칙, 자원 확보·해제",
    "19": "활동×역할 소요 시간, 비인력 자원 확보 현황",
    "20": "위기 척도, P×I 등급 기준, 상위 위기",
    "21": "위기 12건, 점수·등급 수식, 처리 기록",
    "22": "품질 지표, 하네스 검사 항목, 품질 통제 시나리오",
    "23": "조달 대상, 선정 기준, 라이선스 관리",
    "24": "의사소통 매트릭스, 개인정보 공유 원칙, 에스컬레이션",
    "25": "활동별 진척률·PV·EV·AC 수식",
    "26": "실제 이슈 12건(해결 4), 상태 집계",
    "27": "변경 요청 6건(승인 3), 개별 CR 양식",
    "28": "지식 관리 양식 (표 공란)",
    "29": "품질 보증 기록 양식 (표 공란)",
    "30": "정보 배포 이력 8건 (git log 기준)",
    "31": "가중 점수 평가, 분야별 선정(안)",
    "32": "EVM 요약(SPI·CPI·EAC), 마일스톤·현황 요약",
    "33": "1단계 종료 보고, 목표 대비 결과, 인계 사항",
    "34": "교훈 10건, 잘된 점·개선할 점",
}


def locate(fname: str):
    hits = [p for p in P.DOCS.glob(f"*/{fname}") if p.parent.name != "_source"]
    return hits[0] if hits else None


def build():
    src = openpyxl.load_workbook(SRC)["산출물 목록"]
    rows_in = [r for r in src.iter_rows(min_row=2, values_only=True) if r[0]]
    wb = new_book()
    ws = sheet(wb, "산출물 목록", "산출물 목록", f"원본 목록 {len(rows_in)}행 · 고유 파일 {len(SUMMARY)}종 · 파일명을 누르면 열립니다")
    cols = [("그룹", 9, "c"), ("프로세스", 22), ("산출물 파일", 34), ("비고", 18), ("형식", 7, "c"), ("위치", 14, "c"),
            ("작성 상태", 11, "c"), ("내용 요약", 52)]
    body = []
    links = []
    for grp, proc, files, remark in rows_in:
        names = [f.strip() for f in str(files).split(",")]
        paths = [locate(n) for n in names]
        exts = sorted({n.rsplit(".", 1)[1] for n in names})
        num = re.match(r"(\d+)_", names[0]).group(1)
        status = "누락" if not all(paths) else ("양식(표 공란)" if remark and "공란" in str(remark) else "작성 완료")
        where = ", ".join(sorted({p.parent.name for p in paths if p}))
        summary = " / ".join(SUMMARY[re.match(r"(\d+)_", n).group(1)] for n in names)
        body.append([grp, proc, ", ".join(names), remark or "", "/".join(exts), where, status, summary])
        links.append(paths[0])
    f, l = table(ws, 4, cols, body)
    for i, p in enumerate(links):
        if p:
            c = ws.cell(row=f + i, column=3)
            c.hyperlink = p.relative_to(P.DOCS).as_posix()
            c.font = Font(name="맑은 고딕", size=10, color="0563C1", underline="single")
    dropdown(ws, f"G{f}:G{l}", ["작성 완료", "양식(표 공란)", "검토 중", "승인", "누락"])
    ws.auto_filter.ref = f"A4:H{l}"
    r = l + 2
    for i, st in enumerate(["작성 완료", "양식(표 공란)", "누락"]):
        cell(ws, r + i, 2, st, "bold", None, CENTER)
        cell(ws, r + i, 3, f'=COUNTIF($G${f}:$G${l},B{r + i})', "base", None, CENTER)
    note(ws, r + 4, "가정값(노란 칸)은 계획 기준선 승인(A06)에서 실제 값으로 확정합니다. 문서를 다시 만들려면 docs/_source/build_all.py를 실행하세요.")
    out = P.DOCS / "00_산출물목록.xlsx"
    wb.save(out)
    missing = [b[2] for b in body if b[6] == "누락"]
    return out, missing


if __name__ == "__main__":
    out, missing = build()
    print(out.relative_to(P.ROOT).as_posix(), "missing:", missing)
