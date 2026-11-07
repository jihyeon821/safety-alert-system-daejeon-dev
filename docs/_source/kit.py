"""Shared styling helpers for xlsx (openpyxl) and docx (python-docx) deliverables."""
from __future__ import annotations

from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

from plan import ASSUMPTION_NOTE, META

FONT = "맑은 고딕"
NAVY = "1F3864"

# =========================================================================== xlsx
XF = {
    "base": Font(name=FONT, size=10),
    "bold": Font(name=FONT, size=10, bold=True),
    "head": Font(name=FONT, size=10, bold=True, color="FFFFFF"),
    "title": Font(name=FONT, size=16, bold=True, color=NAVY),
    "sub": Font(name=FONT, size=11, bold=True, color=NAVY),
    "input": Font(name=FONT, size=10, color="0000FF"),
    "link": Font(name=FONT, size=10, color="008000"),
    "note": Font(name=FONT, size=9, italic=True, color="595959"),
}
FILL_HEAD = PatternFill("solid", fgColor=NAVY)
FILL_SUB = PatternFill("solid", fgColor="D9E1F2")
FILL_ASSUME = PatternFill("solid", fgColor="FFFF00")
_THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=_THIN, right=_THIN, top=_THIN, bottom=_THIN)
WRAP = Alignment(wrap_text=True, vertical="top")
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
STATUS_FILLS = {"완료": "E2EFDA", "해결": "E2EFDA", "승인": "E2EFDA", "진행중": "DDEBF7", "대응 중": "DDEBF7",
                "대기": "EDEDED", "미해결": "F8CBAD", "보류": "FFF2CC", "검토 중": "FFF2CC", "제출": "FFF2CC",
                "부분 해결": "FFF2CC", "높음": "F8CBAD", "중간": "FFF2CC", "낮음": "E2EFDA"}


def new_book() -> Workbook:
    wb = Workbook()
    wb.remove(wb.active)
    wb.calculation.fullCalcOnLoad = True
    return wb


def sheet(wb: Workbook, name: str, title: str, subtitle: str = "", assumptions: bool = False):
    ws = wb.create_sheet(name)
    ws["A1"] = title
    ws["A1"].font = XF["title"]
    ws["A2"] = f"{META['project']} · {META['version']} · {META['date']}" + (f" · {subtitle}" if subtitle else "")
    ws["A2"].font = XF["note"]
    if assumptions:
        ws["A3"] = ASSUMPTION_NOTE + " 파란 글자 = 입력값, 검은 글자 = 수식."
        ws["A3"].font = XF["note"]
    ws.sheet_view.showGridLines = False
    ws.page_setup.orientation = "landscape"
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.fitToWidth, ws.page_setup.fitToHeight = 1, 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_options.horizontalCentered = True
    ws.page_margins.left = ws.page_margins.right = 0.4
    return ws


def cell(ws, row, col, value, kind="base", fmt=None, align=None, fill=None, comment=None):
    c = ws.cell(row=row, column=col, value=value)
    c.font = XF.get(kind, XF["base"])
    c.border = BORDER
    c.alignment = align or (CENTER if kind in ("head",) else WRAP)
    if kind == "head":
        c.fill = FILL_HEAD
    if fill == "assume":
        c.fill = FILL_ASSUME
    elif fill == "sub":
        c.fill = FILL_SUB
    if fmt:
        c.number_format = fmt
    if comment:
        c.comment = Comment(comment, "PM")
    return c


def table(ws, top: int, columns: list[tuple], rows: list[list], blank_rows: int = 0, freeze: bool = True) -> tuple[int, int]:
    """columns: (header, width, align['c'|'l'], fmt or None). rows: list of values or (value, kind, fill).
    Returns (first_data_row, last_data_row)."""
    for j, (h, w, *_rest) in enumerate(columns, 1):
        cell(ws, top, j, h, "head")
        if w:
            ws.column_dimensions[get_column_letter(j)].width = w
    r = top + 1
    for row in rows:
        for j, v in enumerate(row, 1):
            spec = columns[j - 1]
            align = CENTER if (len(spec) > 2 and spec[2] == "c") else WRAP
            fmt = spec[3] if len(spec) > 3 else None
            kind, fill, comment = "base", None, None
            if isinstance(v, tuple):
                v, kind, *extra = v
                fill = extra[0] if extra else None
                comment = extra[1] if len(extra) > 1 else None
            elif isinstance(v, str) and v.startswith("="):
                kind = "base"
            cell(ws, r, j, v, kind, fmt, align, fill, comment)
        r += 1
    for _ in range(blank_rows):
        for j, spec in enumerate(columns, 1):
            align = CENTER if (len(spec) > 2 and spec[2] == "c") else WRAP
            cell(ws, r, j, None, "base", spec[3] if len(spec) > 3 else None, align)
        r += 1
    if freeze:
        ws.freeze_panes = ws.cell(row=top + 1, column=1)
    return top + 1, r - 1


def dropdown(ws, rng: str, values: list[str]) -> None:
    dv = DataValidation(type="list", formula1='"' + ",".join(values) + '"', allow_blank=True)
    ws.add_data_validation(dv)
    dv.add(rng)


def status_colors(ws, col: str, first: int, last: int, values: list[str] | None = None) -> None:
    for v in values or STATUS_FILLS:
        ws.conditional_formatting.add(f"{col}{first}:{col}{last}", FormulaRule(
            formula=[f'${col}{first}="{v}"'], fill=PatternFill(fill_type="solid", start_color=STATUS_FILLS[v], end_color=STATUS_FILLS[v])))


def note(ws, row: int, text: str, col: int = 1) -> None:
    c = ws.cell(row=row, column=col, value=text)
    c.font = XF["note"]


def subtitle(ws, row: int, text: str) -> None:
    ws.cell(row=row, column=1, value=text).font = XF["sub"]


# =========================================================================== docx
def _font(run_or_style, size=None, bold=None, color=None):
    f = run_or_style.font
    f.name = FONT
    rpr = run_or_style.element.get_or_add_rPr() if hasattr(run_or_style.element, "get_or_add_rPr") else run_or_style._element.get_or_add_rPr()
    fonts = rpr.find(qn("w:rFonts"))
    if fonts is None:
        fonts = OxmlElement("w:rFonts")
        rpr.append(fonts)
    for attr in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
        fonts.set(qn(attr), FONT)
    if size:
        f.size = Pt(size)
    if bold is not None:
        f.bold = bold
    if color:
        f.color.rgb = RGBColor.from_string(color)


def _shade(cell_, hex_color: str) -> None:
    tcpr = cell_._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcpr.append(shd)


def _page_number(paragraph) -> None:
    run = paragraph.add_run()
    for tag, text in (("begin", None), (None, "PAGE"), ("end", None)):
        if tag:
            el = OxmlElement("w:fldChar")
            el.set(qn("w:fldCharType"), tag)
        else:
            el = OxmlElement("w:instrText")
            el.set(qn("xml:space"), "preserve")
            el.text = text
        run._r.append(el)
    _font(run, 9)


class Doc:
    def __init__(self, doc_no: str, title: str, purpose: str, status: str = "초안", landscape: bool = False):
        self.d = Document()
        self.title = title
        sec = self.d.sections[0]
        sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
        if landscape:
            sec.orientation = WD_ORIENT.LANDSCAPE
            sec.page_width, sec.page_height = sec.page_height, sec.page_width
        for side in ("left_margin", "right_margin"):
            setattr(sec, side, Cm(2.0))
        sec.top_margin, sec.bottom_margin = Cm(2.0), Cm(1.8)
        self.width_cm = (sec.page_width - sec.left_margin - sec.right_margin) / 360000

        styles = self.d.styles
        _font(styles["Normal"], 10)
        styles["Normal"].paragraph_format.space_after = Pt(4)
        styles["Normal"].paragraph_format.line_spacing = 1.25
        for name, size, before, after in (("Title", 22, 0, 6), ("Heading 1", 14, 14, 6), ("Heading 2", 11.5, 10, 4)):
            st = styles[name]
            _font(st, size, True, NAVY)
            st.paragraph_format.space_before = Pt(before)
            st.paragraph_format.space_after = Pt(after)
            st.paragraph_format.keep_with_next = True
        for name in ("List Bullet", "List Number"):
            _font(styles[name], 10)

        header = sec.header.paragraphs[0]
        header.text = f"{META['project']}  |  {doc_no} {title}"
        header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        for r in header.runs:
            _font(r, 8, color="808080")
        footer = sec.footer.paragraphs[0]
        footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
        _page_number(footer)

        t = self.d.add_paragraph(style="Title")
        t.add_run(title)
        p = self.d.add_paragraph()
        r = p.add_run(META["project"])
        _font(r, 11, True, "595959")
        self.kv([("문서 번호", doc_no), ("문서명", title), ("프로젝트", f"{META['project']} ({META['project_en']})"),
                 ("버전 / 상태", f"{META['version']} / {status}"), ("작성일", META["date"]),
                 ("작성 / 승인", f"{META['owner']} (Claude Code 작성 지원) / [승인자 서명]"),
                 ("목적", purpose)])

    # ---------------------------------------------------------------- blocks
    def h1(self, text): self.d.add_heading(text, level=1)
    def h2(self, text): self.d.add_heading(text, level=2)

    def p(self, text, bold=False, italic=False, color=None, size=None):
        para = self.d.add_paragraph()
        r = para.add_run(text)
        _font(r, size, bold, color)
        r.italic = italic
        return para

    def note(self, text):
        return self.p(text, italic=True, color="595959", size=9)

    def bullets(self, items, numbered=False):
        for it in items:
            para = self.d.add_paragraph(style="List Number" if numbered else "List Bullet")
            if isinstance(it, tuple):
                r = para.add_run(it[0])
                _font(r, 10, True)
                r2 = para.add_run(" " + it[1])
                _font(r2, 10)
            else:
                _font(para.add_run(it), 10)

    def table(self, headers, rows, widths=None, font_size=9, highlight_col=None):
        n = len(headers)
        widths = widths or [self.width_cm / n] * n
        scale = self.width_cm / sum(widths)
        widths = [w * scale for w in widths]
        t = self.d.add_table(rows=1, cols=n)
        t.style = "Table Grid"
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        t.autofit = False
        for j, h in enumerate(headers):
            c = t.rows[0].cells[j]
            c.width = Cm(widths[j])
            c.text = ""
            r = c.paragraphs[0].add_run(str(h))
            _font(r, font_size, True, "FFFFFF")
            c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            _shade(c, NAVY)
        trpr = t.rows[0]._tr.get_or_add_trPr()
        hdr = OxmlElement("w:tblHeader")
        hdr.set(qn("w:val"), "true")
        trpr.append(hdr)
        for row in rows:
            cells = t.add_row().cells
            for j, v in enumerate(row):
                c = cells[j]
                c.width = Cm(widths[j])
                c.text = ""
                text = "" if v is None else str(v)
                assume = text.startswith("[가정]") or text.startswith("[확인 필요]")
                r = c.paragraphs[0].add_run(text)
                _font(r, font_size)
                if assume:
                    _shade(c, "FFFF00")
        self.d.add_paragraph()
        return t

    def kv(self, pairs, key_width=3.5):
        t = self.d.add_table(rows=0, cols=2)
        t.style = "Table Grid"
        t.autofit = False
        for k, v in pairs:
            cells = t.add_row().cells
            cells[0].width, cells[1].width = Cm(key_width), Cm(self.width_cm - key_width)
            cells[0].text, cells[1].text = "", ""
            _font(cells[0].paragraphs[0].add_run(k), 9.5, True)
            _shade(cells[0], "D9E1F2")
            text = str(v)
            _font(cells[1].paragraphs[0].add_run(text), 9.5)
            if text.startswith("[가정]") or text.startswith("[확인 필요]"):
                _shade(cells[1], "FFFF00")
        self.d.add_paragraph()

    def signoff(self):
        self.h1("승인")
        self.table(["구분", "이름", "역할", "서명", "일자"],
                   [["작성", META["owner"], "프로젝트 오너", "", META["date"]],
                    ["검토", "[확인 필요]", "원 개발팀 대표", "", ""],
                    ["승인", META["owner"], "후원자", "", ""]], [2, 3.5, 4, 3.5, 3])

    def save(self, path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.d.save(path)
