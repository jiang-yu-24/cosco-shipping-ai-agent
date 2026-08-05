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
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
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
# 字体注册（reportlab 需要在使用前注册 TTF 字体）
# ============================================================
_PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
_FONTS_DIR = os.path.join(_PROJECT_DIR, "fonts")
_FONT_REGISTERED = False

# 候选字体文件
_FONT_FILES = [
    os.path.join(_FONTS_DIR, "DroidSansFallback.ttf"),
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Light.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
    "C:/Windows/Fonts/msyh.ttc",
]


def _register_font():
    """注册中文字体到 reportlab，优先使用项目自带字体。"""
    global _FONT_REGISTERED
    if _FONT_REGISTERED:
        return
    _FONT_REGISTERED = True

    for font_path in _FONT_FILES:
        if os.path.isfile(font_path):
            try:
                pdfmetrics.registerFont(TTFont("CJK", font_path))
                pdfmetrics.registerFont(TTFont("CJK-Bold", font_path))  # reportlab 会合成粗体
                return
            except Exception:
                continue

    # 未找到字体时使用 Helvetica（中文将不正常显示）
    pass


# ============================================================
# PDF 生成核心
# ============================================================

def _build_document(
    title: str,
    doc_no: str,
    elements: list,
    recipient: str = "",
) -> bytes:
    """构建 PDF 文档，返回 bytes。"""
    _register_font()

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        topMargin=25 * mm,
        bottomMargin=20 * mm,
        leftMargin=22 * mm,
        rightMargin=22 * mm,
    )

    # 样式
    font_name = "CJK" if _FONT_REGISTERED else "Helvetica"

    styles = {
        "title": ParagraphStyle(
            "Title_CN", fontName=font_name, fontSize=18,
            alignment=TA_CENTER, spaceAfter=6, leading=28,
        ),
        "doc_no": ParagraphStyle(
            "DocNo", fontName=font_name, fontSize=10,
            alignment=TA_CENTER, textColor=HexColor("#888888"),
            spaceAfter=4,
        ),
        "recipient": ParagraphStyle(
            "Recipient", fontName=font_name, fontSize=11,
            alignment=TA_LEFT, spaceAfter=8, leading=18,
        ),
        "body": ParagraphStyle(
            "Body_CN", fontName=font_name, fontSize=11,
            alignment=TA_LEFT, spaceAfter=6, leading=22,
            firstLineIndent=22,  # 首行缩进
        ),
        "body_no_indent": ParagraphStyle(
            "BodyNoIndent", fontName=font_name, fontSize=11,
            alignment=TA_LEFT, spaceAfter=6, leading=22,
        ),
        "signature": ParagraphStyle(
            "Signature", fontName=font_name, fontSize=11,
            alignment=TA_RIGHT, spaceAfter=4, leading=18,
        ),
        "note": ParagraphStyle(
            "Note", fontName=font_name, fontSize=9,
            alignment=TA_LEFT, textColor=HexColor("#888888"),
            leading=16,
        ),
    }

    # 红色分隔线
    red_line = HRFlowable(
        width="100%", thickness=1, color=HexColor("#B40000"),
        spaceBefore=4, spaceAfter=4,
    )
    thin_red_line = HRFlowable(
        width="100%", thickness=0.4, color=HexColor("#B40000"),
        spaceBefore=2, spaceAfter=8,
    )

    # 组装文档
    story = []

    # 红头区域
    story.append(red_line)
    story.append(Paragraph(title, styles["title"]))
    if doc_no:
        story.append(Paragraph(doc_no, styles["doc_no"]))
    story.append(thin_red_line)

    # 主送
    if recipient:
        story.append(Paragraph(f"{recipient}：", styles["recipient"]))
        story.append(Spacer(1, 4 * mm))

    # 正文
    for elem in elements:
        story.append(elem)
        if isinstance(elem, Paragraph) and elem.style == styles["body"]:
            pass  # body style already has spaceAfter

    story.append(Spacer(1, 10 * mm))

    # 落款
    now = datetime.now(_CST)
    story.append(Paragraph("中远海运散货运输有限公司", styles["signature"]))
    story.append(Paragraph(now.strftime("%Y年%m月%d日"), styles["signature"]))

    doc.build(story)
    return buf.getvalue()


def _para(text: str, styles: dict, key: str = "body") -> Paragraph:
    """快捷创建段落，自动处理换行。"""
    return Paragraph(text.replace("\n", "<br/>"), styles[key])


def _build_table(rows: list, col_widths: list, styles: dict) -> Table:
    """创建格式化表格。"""
    font_name = "CJK" if _FONT_REGISTERED else "Helvetica"

    # 处理中文换行
    formatted_rows = []
    for row in rows:
        formatted_rows.append([Paragraph(str(c).replace("\n", "<br/>"),
                                          ParagraphStyle(
                                              "Cell", fontName=font_name, fontSize=10,
                                              leading=16,
                                          )) for c in row])

    t = Table(formatted_rows, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), font_name),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#CCCCCC")),
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#F0F0F0")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


# ============================================================
# 文档模板
# ============================================================

def generate_schedule_confirmation(
    route: str,
    vessel: str,
    departure: str,
    arrival: str,
    cargo: str,
    consignor: str = "待填写",
    consignee: str = "待填写",
) -> bytes:
    """生成船期确认函。"""
    _register_font()
    font_name = "CJK" if _FONT_REGISTERED else "Helvetica"

    styles = {
        "title": ParagraphStyle("T", fontName=font_name, fontSize=18, alignment=TA_CENTER, leading=28),
        "doc_no": ParagraphStyle("DN", fontName=font_name, fontSize=10, alignment=TA_CENTER, textColor=HexColor("#888888")),
        "recipient": ParagraphStyle("R", fontName=font_name, fontSize=11, alignment=TA_LEFT, leading=18),
        "body": ParagraphStyle("B", fontName=font_name, fontSize=11, alignment=TA_LEFT, leading=22, firstLineIndent=22),
        "signature": ParagraphStyle("S", fontName=font_name, fontSize=11, alignment=TA_RIGHT, leading=18),
    }

    now = datetime.now(_CST)
    doc_no = f"COSCO BULK 航确字〔{now.year}〕第{now.strftime('%m%d%H%M')}号"

    elements = [
        _para(f"致：{consignee}", styles, "recipient"),
        Spacer(1, 4 * mm),
        _para("根据贵我双方签署的运输合同，我司确认以下船期安排，现函告如下：", styles, "body"),
        Spacer(1, 4 * mm),
    ]

    # 船期信息表
    table_data = [
        ["项目", "内容"],
        ["航线", route],
        ["承运船舶", vessel],
        ["货种及货量", cargo],
        ["预计离港时间", departure],
        ["预计到港时间", arrival],
        ["托运人", consignor],
        ["收货人", consignee],
    ]
    col_w = [80, 300]
    elements.append(_build_table(table_data, col_w, styles))
    elements.append(Spacer(1, 6 * mm))

    elements.append(_para(
        "备注：以上船期为当前预计安排。如遇天气、港口拥堵等不可抗力因素，"
        "实际船期可能有所调整。我司将实时跟踪船舶动态，如有变更将第一时间通知贵方。",
        styles, "body",
    ))
    elements.append(_para("如有疑问，请联系我司客服中心。", styles, "body"))

    return _build_document("船 期 确 认 函", doc_no, elements, consignee)


def generate_shipping_report(
    title: str,
    content: str,
    author: str = "远航助手",
) -> bytes:
    """生成通用航运报告。"""
    _register_font()
    font_name = "CJK" if _FONT_REGISTERED else "Helvetica"

    styles = {
        "title": ParagraphStyle("T", fontName=font_name, fontSize=18, alignment=TA_CENTER, leading=28),
        "doc_no": ParagraphStyle("DN", fontName=font_name, fontSize=10, alignment=TA_CENTER, textColor=HexColor("#888888")),
        "body": ParagraphStyle("B", fontName=font_name, fontSize=11, alignment=TA_LEFT, leading=22, firstLineIndent=22),
        "meta": ParagraphStyle("M", fontName=font_name, fontSize=10, alignment=TA_RIGHT, textColor=HexColor("#888888")),
        "signature": ParagraphStyle("S", fontName=font_name, fontSize=11, alignment=TA_RIGHT, leading=18),
    }

    now = datetime.now(_CST)
    doc_no = f"COSCO BULK 报字〔{now.year}〕第{now.strftime('%m%d%H%M')}号"

    elements = [
        _para(f"编制：{author}    日期：{now.strftime('%Y-%m-%d')}", styles, "meta"),
        Spacer(1, 6 * mm),
    ]

    for para in content.strip().split("\n"):
        para = para.strip()
        if para:
            elements.append(_para(para, styles, "body"))
        else:
            elements.append(Spacer(1, 3 * mm))

    return _build_document(title, doc_no, elements)


def generate_official_document(
    title: str,
    content: str,
    recipient: str = "",
    doc_type: str = "通知",
) -> bytes:
    """生成央企通用公文。"""
    _register_font()
    font_name = "CJK" if _FONT_REGISTERED else "Helvetica"

    styles = {
        "title": ParagraphStyle("T", fontName=font_name, fontSize=18, alignment=TA_CENTER, leading=28),
        "doc_no": ParagraphStyle("DN", fontName=font_name, fontSize=10, alignment=TA_CENTER, textColor=HexColor("#888888")),
        "recipient": ParagraphStyle("R", fontName=font_name, fontSize=11, alignment=TA_LEFT, leading=18),
        "body": ParagraphStyle("B", fontName=font_name, fontSize=11, alignment=TA_LEFT, leading=22, firstLineIndent=22),
        "signature": ParagraphStyle("S", fontName=font_name, fontSize=11, alignment=TA_RIGHT, leading=18),
    }

    now = datetime.now(_CST)
    doc_no = f"COSCO BULK {doc_type}字〔{now.year}〕第{now.strftime('%m%d%H%M')}号"

    elements = []
    for para in content.strip().split("\n"):
        para = para.strip()
        if para:
            elements.append(_para(para, styles, "body"))
        else:
            elements.append(Spacer(1, 3 * mm))

    return _build_document(title, doc_no, elements, recipient)


# ============================================================
# 存储已生成的 PDF（供 app.py 下载）
# ============================================================

_generated_pdf: Optional[bytes] = None
_generated_pdf_name: str = ""


def store_pdf(pdf_bytes: bytes, filename: str) -> None:
    """存储生成的 PDF 供前端下载。"""
    global _generated_pdf, _generated_pdf_name
    _generated_pdf = bytes(pdf_bytes)
    _generated_pdf_name = filename


def get_pdf() -> Tuple[Optional[bytes], str]:
    """获取已生成的 PDF 数据及文件名，读取后清空。"""
    global _generated_pdf, _generated_pdf_name
    result = (_generated_pdf, _generated_pdf_name)
    _generated_pdf = None
    _generated_pdf_name = ""
    return result
