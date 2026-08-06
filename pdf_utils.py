"""
PDF 文档生成模块 — 央企规范化公文模板
=======================================
基于 reportlab 实现中文 PDF 文档生成。
支持：船期确认函、货运报告、通用公文。
仅供 Agent 后端调用，不在前端侧边栏展示。
"""

import io
import os
import re as _re
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# 北京时间
_CST = timezone(timedelta(hours=8), name="Asia/Shanghai")

# ============================================================
# 字体注册
# ============================================================
_PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
_FONTS_DIR = os.path.join(_PROJECT_DIR, "fonts")
_DONE = False

# 中文字体候选路径
_CJK_CANDIDATES = [
    os.path.join(_FONTS_DIR, "DroidSansFallback.ttf"),
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Light.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
    "C:/Windows/Fonts/msyh.ttc",
]


def _init_fonts():
    """
    注册字体策略：
    - Helvetica 作为基准字体（拉丁/数字完美支持，reportlab 内置）
    - CJK 字体仅用于中文渲染，通过 XML <font> 标签按需混排
    """
    global _DONE
    if _DONE:
        return
    _DONE = True

    cjk_path = None
    for path in _CJK_CANDIDATES:
        if os.path.isfile(path):
            cjk_path = path
            break

    if cjk_path:
        pdfmetrics.registerFont(TTFont("CJK", cjk_path))


# ============================================================
# 文本混排：拉丁用 Helvetica，中文用 CJK
# ============================================================

# CJK 字符正则（覆盖汉字、数学符号、希腊字母、箭头、几何图形等）
_CJK_RE = _re.compile(
    r'[一-鿿㐀-䶿豈-﫿'
    r'　-〿＀-￯︰-﹏'
    r'∀-⋿←-⇿⌀-⏿'
    r'─-╿■-◿☀-⛿'
    r'Α-ω -⁯℀-⅏'
    r'⅐-↏①-⓿⺀-⻿]+'
)


def _wrap_cjk(text: str) -> str:
    """
    用正则匹配 CJK 连续字符段，包裹 <font face="CJK">，
    非 CJK 字符保持 Helvetica。单次替换，O(n)。
    """
    cjk_ok = "CJK" in pdfmetrics._fonts
    if not cjk_ok:
        return text
    return _CJK_RE.sub(r'<font face="CJK">\g<0></font>', text)


def _make_styles():
    """创建段落样式字典。基准字体 Helvetica，CJK 通过 XML 注入。"""
    _init_fonts()

    return {
        "title": ParagraphStyle(
            "s_title", fontName="Helvetica", fontSize=18,
            alignment=TA_CENTER, spaceAfter=6, leading=28,
        ),
        "doc_no": ParagraphStyle(
            "s_docno", fontName="Helvetica", fontSize=10,
            alignment=TA_CENTER, textColor=HexColor("#888888"), spaceAfter=4,
        ),
        "recipient": ParagraphStyle(
            "s_recip", fontName="Helvetica", fontSize=11,
            alignment=TA_LEFT, spaceAfter=8, leading=18,
        ),
        "body": ParagraphStyle(
            "s_body", fontName="Helvetica", fontSize=11,
            alignment=TA_LEFT, spaceAfter=6, leading=22,
            firstLineIndent=22,
        ),
        "signature": ParagraphStyle(
            "s_sign", fontName="Helvetica", fontSize=11,
            alignment=TA_RIGHT, spaceAfter=4, leading=18,
        ),
        "meta": ParagraphStyle(
            "s_meta", fontName="Helvetica", fontSize=10,
            alignment=TA_RIGHT, textColor=HexColor("#888888"),
        ),
        "cell": ParagraphStyle(
            "s_cell", fontName="Helvetica", fontSize=10, leading=16,
        ),
        "cell_header": ParagraphStyle(
            "s_chdr", fontName="Helvetica-Bold", fontSize=10, leading=16,
        ),
    }


# CJK 禁则——用正则单次替换，避免逐字符遍历
_KINSOKU_PATTERN = _re.compile(
    r'([^\s\n ‍])([，。、》」』】！？％…—～：）］"'+"'"+r'″′〉,.;:!?%)}]'+"'"+r'"])'
)


def _fix_kinsoku(text: str) -> str:
    """
    用 ‍ (ZWJ) 连接 CJK 标点与前一字，防止标点断到行首。
    正则单次替换，O(n) 复杂度，对长文本无性能影响。
    """
    return _KINSOKU_PATTERN.sub(r'\1‍\2', text)


def _p(text: str, styles: dict, key: str = "body") -> Paragraph:
    """创建段落：禁则处理 + <br/> 换行 + CJK 字体混排。"""
    text = _fix_kinsoku(text)
    text = text.replace("\n", "<br/>")
    text = _wrap_cjk(text)
    return Paragraph(text, styles[key])


def _table(rows: list, col_widths: list, styles: dict) -> Table:
    """创建格式化表格。表内容经 _wrap_cjk 处理中文混排。"""
    formatted = []
    for i, row in enumerate(rows):
        sty = styles["cell_header"] if i == 0 else styles["cell"]
        formatted.append([Paragraph(_wrap_cjk(_fix_kinsoku(str(c))).replace("\n", "<br/>"), sty) for c in row])

    t = Table(formatted, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#CCCCCC")),
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#EEEEEE")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


# ============================================================
# 文档构建
# ============================================================

def _red_line(thickness: float = 1, space_after: float = 4) -> HRFlowable:
    return HRFlowable(
        width="100%", thickness=thickness,
        color=HexColor("#B40000"),
        spaceBefore=4, spaceAfter=space_after,
    )


def _build(title: str, doc_no: str, elements: list, recipient: str = "") -> bytes:
    """组装 PDF 文档，返回 bytes。"""
    _init_fonts()
    styles = _make_styles()

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=25 * mm, bottomMargin=20 * mm,
        leftMargin=22 * mm, rightMargin=22 * mm,
    )

    story = []
    # 红头
    story.append(_red_line(1.0, 4))
    story.append(_p(title, styles, "title"))
    if doc_no:
        story.append(_p(doc_no, styles, "doc_no"))
    story.append(_red_line(0.4, 8))

    # 主送
    if recipient:
        story.append(_p(f"致：{recipient}", styles, "recipient"))
        story.append(Spacer(1, 4 * mm))

    # 正文元素
    for elem in elements:
        story.append(elem)

    story.append(Spacer(1, 12 * mm))

    # 落款
    now = datetime.now(_CST)
    story.append(_p("中远海运散货运输有限公司", styles, "signature"))
    story.append(_p(now.strftime("%Y年%m月%d日"), styles, "signature"))

    doc.build(story)
    return buf.getvalue()


# ============================================================
# 文档模板
# ============================================================

def generate_schedule_confirmation(
    route: str, vessel: str, departure: str, arrival: str, cargo: str,
    consignor: str = "待填写", consignee: str = "待填写",
) -> bytes:
    _init_fonts()
    styles = _make_styles()
    now = datetime.now(_CST)
    doc_no = f"COSCO BULK 航确字〔{now.year}〕第{now.strftime('%m%d%H%M')}号"

    elements = [
        _p("根据贵我双方签署的运输合同，我司确认以下船期安排，现函告如下：", styles, "body"),
        Spacer(1, 4 * mm),
    ]

    data = [
        ["项目", "内容"],
        ["航线", route],
        ["承运船舶", vessel],
        ["货种及货量", cargo],
        ["预计离港时间", departure],
        ["预计到港时间", arrival],
        ["托运人", consignor],
        ["收货人", consignee],
    ]
    elements.append(_table(data, [80, 300], styles))
    elements.append(Spacer(1, 6 * mm))
    elements.append(_p(
        "备注：以上船期为当前预计安排。如遇天气、港口拥堵等不可抗力因素，"
        "实际船期可能有所调整。我司将实时跟踪船舶动态，如有变更将第一时间通知贵方。",
        styles, "body",
    ))

    return _build("船 期 确 认 函", doc_no, elements, consignee)


def generate_shipping_report(title: str, content: str, author: str = "远航助手") -> bytes:
    _init_fonts()
    styles = _make_styles()
    now = datetime.now(_CST)
    doc_no = f"COSCO BULK 报字〔{now.year}〕第{now.strftime('%m%d%H%M')}号"

    elements = [
        _p(f"编制：{author}    日期：{now.strftime('%Y-%m-%d')}", styles, "meta"),
        Spacer(1, 6 * mm),
    ]
    for para in content.strip().split("\n"):
        para = para.strip()
        if para:
            elements.append(_p(para, styles, "body"))
        else:
            elements.append(Spacer(1, 3 * mm))

    return _build(title, doc_no, elements)


def generate_official_document(
    title: str, content: str, recipient: str = "", doc_type: str = "通知",
) -> bytes:
    _init_fonts()
    styles = _make_styles()
    now = datetime.now(_CST)
    doc_no = f"COSCO BULK {doc_type}字〔{now.year}〕第{now.strftime('%m%d%H%M')}号"

    elements = []
    for para in content.strip().split("\n"):
        para = para.strip()
        if para:
            elements.append(_p(para, styles, "body"))
        else:
            elements.append(Spacer(1, 3 * mm))

    return _build(title, doc_no, elements, recipient)


def _build_generic(title: str, elements: list) -> bytes:
    """构建无公文格式的通用 PDF（无红头、无文号、无落款）。"""
    _init_fonts()
    styles = _make_styles()

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=20 * mm, bottomMargin=15 * mm,
        leftMargin=22 * mm, rightMargin=22 * mm,
    )

    story = []
    # 简洁标题
    story.append(Spacer(1, 10 * mm))
    story.append(_p(title, styles, "title"))
    story.append(Spacer(1, 8 * mm))

    for elem in elements:
        story.append(elem)

    doc.build(story)
    return buf.getvalue()


def generate_generic_pdf(title: str, content: str) -> bytes:
    """生成无公文格式的通用 PDF（简洁排版，适合非正式场景）。"""
    _init_fonts()
    styles = _make_styles()

    elements = []
    for para in content.strip().split("\n"):
        para = para.strip()
        if para:
            elements.append(_p(para, styles, "body"))
        else:
            elements.append(Spacer(1, 3 * mm))

    return _build_generic(title, elements)


def generate_proposal(
    title: str,
    project_name: str = "",
    department: str = "",
    content: str = "",
) -> bytes:
    """
    生成央企数字化项目方案 PDF。

    参数:
        title: 方案标题
        project_name: 项目名称
        department: 申报单位
        content: 方案正文（按模板章节组织，以 # 号标注章节标题）
    """
    _init_fonts()
    styles = _make_styles()

    # 封面样式
    cover_title = ParagraphStyle(
        "cover_title", fontName="Helvetica", fontSize=24,
        alignment=TA_CENTER, leading=36, spaceAfter=20,
    )
    cover_sub = ParagraphStyle(
        "cover_sub", fontName="Helvetica", fontSize=14,
        alignment=TA_CENTER, leading=22, textColor=HexColor("#555555"),
    )
    # 章节标题样式
    section_h = ParagraphStyle(
        "section_h", fontName="Helvetica", fontSize=14,
        alignment=TA_LEFT, leading=22, spaceBefore=10, spaceAfter=6,
    )
    body = styles["body"]

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=22 * mm, bottomMargin=18 * mm,
        leftMargin=25 * mm, rightMargin=25 * mm,
    )

    story = []

    # --- 封面 ---
    story.append(Spacer(1, 40 * mm))
    story.append(Paragraph(_wrap_cjk("数字化项目方案"), cover_title))
    story.append(Spacer(1, 10 * mm))
    story.append(Paragraph(_wrap_cjk(title), cover_title))
    story.append(Spacer(1, 15 * mm))
    if project_name:
        story.append(Paragraph(_wrap_cjk(f"项目名称：{project_name}"), cover_sub))
    if department:
        story.append(Paragraph(_wrap_cjk(f"申报单位：{department}"), cover_sub))
    now = datetime.now(_CST)
    story.append(Paragraph(_wrap_cjk(f"编制日期：{now.strftime('%Y年%m月%d日')}"), cover_sub))
    story.append(Spacer(1, 10 * mm))

    # 封面分隔线
    story.append(_red_line(1.0, 8))

    # --- 正文：按章节解析（支持「一、」「二、」格式和「#」格式） ---
    # 按中文序号标题分割：一、二、三、... 或 # 开头
    sections = _re.split(r"\n(?=[一二三四五六七八九十]、|\d+、|# )", content.strip())
    if len(sections) <= 1:
        # 无章节分割，整个内容作为正文
        sections = [content.strip()]

    for sec in sections:
        sec = sec.strip()
        if not sec:
            continue

        # 提取章节标题和正文
        lines = sec.split("\n", 1)
        heading = lines[0].strip()
        # 清理标题前缀（# 或 中文序号）
        heading = re.sub(r'^[#\s]+', '', heading)
        # 保留原标题格式（如"一、项目概述"）
        sec_body = lines[1].strip() if len(lines) > 1 else ""

        # 渲染章节标题
        story.append(Paragraph(_wrap_cjk(heading), section_h))
        story.append(_red_line(0.3, 4))

        # 渲染章节正文（按段落分割，连续 | 行自动合并为表格）
        para_lines = sec_body.split("\n")
        i = 0
        while i < len(para_lines):
            para = para_lines[i].strip()

            # 跳过空行
            if not para:
                story.append(Spacer(1, 2 * mm))
                i += 1
                continue

            # 检测表格行（包含 | 且至少2个分隔符）
            if "|" in para and para.count("|") >= 2:
                rows = []
                while i < len(para_lines) and "|" in para_lines[i] and para_lines[i].count("|") >= 2:
                    cells = [c.strip() for c in para_lines[i].strip().split("|")]
                    # 去掉首尾可能的空串
                    if cells and cells[0] == "":
                        cells = cells[1:]
                    if cells and cells[-1] == "":
                        cells = cells[:-1]
                    if cells:
                        rows.append(cells)
                    i += 1
                if rows:
                    col_w = [(doc.width - 50) / len(rows[0])] * len(rows[0])
                    story.append(_table(rows, col_w, styles))
                    story.append(Spacer(1, 3 * mm))
            else:
                story.append(_p(para, styles, "body"))
                i += 1

        story.append(Spacer(1, 4 * mm))

    # --- 尾页 ---
    story.append(Spacer(1, 15 * mm))
    story.append(_p("编制单位审核意见：", styles, "body"))
    story.append(Spacer(1, 20 * mm))
    story.append(_p(f"编制人：________    审核人：________    批准人：________", styles, "body"))
    story.append(_p(f"日期：________    日期：________    日期：________", styles, "body"))

    doc.build(story)
    return buf.getvalue()


# ============================================================
# 存储已生成的 PDF（供 app.py 下载）
# ============================================================

_generated_pdf: Optional[bytes] = None
_generated_pdf_name: str = ""


def store_pdf(pdf_bytes: bytes, filename: str) -> None:
    global _generated_pdf, _generated_pdf_name
    _generated_pdf = bytes(pdf_bytes)
    _generated_pdf_name = filename


def get_pdf() -> Tuple[Optional[bytes], str]:
    global _generated_pdf, _generated_pdf_name
    result = (_generated_pdf, _generated_pdf_name)
    _generated_pdf = None
    _generated_pdf_name = ""
    return result
