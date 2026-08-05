"""
PDF 文档生成模块 — 央企规范化公文模板
=======================================
基于 reportlab 实现中文 PDF 文档生成。
支持：船期确认函、货运报告、通用公文。
仅供 Agent 后端调用，不在前端侧边栏展示。
"""

import io
import os
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
    - CJK: 使用项目自带或系统中文字体，覆盖中、日、韩及基础拉丁字符
    - 拉丁加粗回退到 Helvetica-Bold（reportlab 内置，无需外部文件）
    - CJK 加粗使用同一字体（reportlab 不支持合成粗体，改用字号/颜色区分）
    """
    global _DONE
    if _DONE:
        return
    _DONE = True

    # 1. 注册 CJK 字体（覆盖中文 + 基础拉丁）
    cjk_path = None
    for path in _CJK_CANDIDATES:
        if os.path.isfile(path):
            cjk_path = path
            break

    if cjk_path:
        pdfmetrics.registerFont(TTFont("CJK", cjk_path))

    # 2. Helvetica 作为拉丁粗体回退（reportlab 内置，无需注册）
    # Helvetica, Helvetica-Bold, Courier 均为 reportlab 内置字体


# ============================================================
# 样式工厂
# ============================================================

def _make_styles():
    """根据字体可用情况创建段落样式字典。"""
    _init_fonts()

    # CJK 可用时优先用 CJK（含拉丁），粗体回退到 Helvetica-Bold
    cjk_ok = "CJK" in pdfmetrics._fonts

    body_font = "CJK" if cjk_ok else "Helvetica"
    bold_font = "Helvetica-Bold"  # 拉丁加粗始终用 Helvetica-Bold（内置）
    meta_font = "Helvetica"       # 元数据（文号、日期等）用 Helvetica

    return {
        "title": ParagraphStyle(
            "s_title", fontName=body_font, fontSize=18,
            alignment=TA_CENTER, spaceAfter=6, leading=28,
        ),
        "doc_no": ParagraphStyle(
            "s_docno", fontName=body_font, fontSize=10,
            alignment=TA_CENTER, textColor=HexColor("#888888"), spaceAfter=4,
        ),
        "recipient": ParagraphStyle(
            "s_recip", fontName=body_font, fontSize=11,
            alignment=TA_LEFT, spaceAfter=8, leading=18,
        ),
        "body": ParagraphStyle(
            "s_body", fontName=body_font, fontSize=11,
            alignment=TA_LEFT, spaceAfter=6, leading=22,
            firstLineIndent=22,
        ),
        "signature": ParagraphStyle(
            "s_sign", fontName=body_font, fontSize=11,
            alignment=TA_RIGHT, spaceAfter=4, leading=18,
        ),
        "meta": ParagraphStyle(
            "s_meta", fontName=meta_font, fontSize=10,
            alignment=TA_RIGHT, textColor=HexColor("#888888"),
        ),
        "cell": ParagraphStyle(
            "s_cell", fontName=body_font, fontSize=10, leading=16,
        ),
        "cell_header": ParagraphStyle(
            "s_chdr", fontName=bold_font, fontSize=10, leading=16,
        ),
    }


def _p(text: str, styles: dict, key: str = "body") -> Paragraph:
    """创建段落，自动将换行符转为 <br/>。"""
    return Paragraph(text.replace("\n", "<br/>"), styles[key])


def _table(rows: list, col_widths: list, styles: dict) -> Table:
    """创建格式化表格。"""
    formatted = []
    for i, row in enumerate(rows):
        sty = styles["cell_header"] if i == 0 else styles["cell"]
        formatted.append([Paragraph(str(c).replace("\n", "<br/>"), sty) for c in row])

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
        _p(f"致：{consignee}", styles, "recipient"),
        Spacer(1, 4 * mm),
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
