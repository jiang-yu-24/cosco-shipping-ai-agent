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

def _needs_cjk(text: str) -> bool:
    """
    判断文本是否包含 CJK、数学符号、特殊字符等 Helvetica 无法渲染的字符。
    DroidSansFallback 覆盖了 CJK + 数学符号 + 箭头 + 几何图形等 Unicode 区块。
    """
    for ch in text:
        cp = ord(ch)
        if (0x4E00 <= cp <= 0x9FFF or     # CJK 统一汉字
            0x3400 <= cp <= 0x4DBF or     # CJK 扩展 A
            0x20000 <= cp <= 0x2A6DF or   # CJK 扩展 B
            0xF900 <= cp <= 0xFAFF or     # CJK 兼容汉字
            0x3000 <= cp <= 0x303F or     # CJK 标点
            0xFF00 <= cp <= 0xFFEF or     # 全角字符
            0x2F800 <= cp <= 0x2FA1F or   # CJK 兼容补充
            0x2200 <= cp <= 0x22FF or     # 数学运算符 (∀ ∂ ∃ ∑ ∏ ∫ √ ∞ ≈ ≠ ≤ ≥)
            0x2190 <= cp <= 0x21FF or     # 箭头 (← → ↑ ↓ ↔ ↕)
            0x2300 <= cp <= 0x23FF or     # 杂项技术符号 (⌂ ⌃ ⌄)
            0x2500 <= cp <= 0x257F or     # 制表符
            0x25A0 <= cp <= 0x25FF or     # 几何图形 (■ □ ▲ △ ◆ ◇)
            0x2600 <= cp <= 0x26FF or     # 杂项符号 (☀ ☁ ☂ ★ ☆ ☎)
            0x0391 <= cp <= 0x03C9 or     # 希腊字母 (Α-Ω α-ω)
            0x2000 <= cp <= 0x206F or     # 通用标点 (— – … ‰)
            0x2100 <= cp <= 0x214F or     # 字母式符号 (ℂ ℇ ℈ ℉ ℗ ℘ ℙ)
            0x2150 <= cp <= 0x218F or     # 数字形式 (⅓ ⅔ ⅛ ⅜)
            0x2460 <= cp <= 0x24FF or     # 带圈数字 (① ② ③)
            0x2E80 <= cp <= 0x2EFF or     # CJK 部首补充
            0xFE30 <= cp <= 0xFE4F):       # CJK 兼容形式
            return True
    return False


def _wrap_cjk(text: str) -> str:
    """
    逐字符扫描文本，将 CJK 字符段用 <font face="CJK"> 包裹，
    非 CJK 字符（拉丁、数字、符号）保持 Helvetica 渲染。

    示例输入：  "预计 2026-08-15 到港"
    示例输出：  '<font face="CJK">预计 </font>2026-08-15<font face="CJK"> 到港</font>'
    """
    cjk_ok = "CJK" in pdfmetrics._fonts
    if not cjk_ok:
        return text

    result = []
    buf = []
    in_cjk = None  # None=初始, True=CJK缓冲区, False=拉丁缓冲区

    for ch in text:
        ch_is_cjk = _needs_cjk(ch)
        if in_cjk is None:
            in_cjk = ch_is_cjk
            buf.append(ch)
        elif ch_is_cjk == in_cjk:
            buf.append(ch)
        else:
            # 字体切换，flush 缓冲区
            segment = "".join(buf)
            if in_cjk:
                result.append(f'<font face="CJK">{segment}</font>')
            else:
                result.append(segment)
            buf = [ch]
            in_cjk = ch_is_cjk

    # flush 最后一段
    if buf:
        segment = "".join(buf)
        if in_cjk:
            result.append(f'<font face="CJK">{segment}</font>')
        else:
            result.append(segment)

    return "".join(result)


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


def _p(text: str, styles: dict, key: str = "body") -> Paragraph:
    """创建段落：自动 <br/> 换行 + CJK 字体混排。"""
    text = text.replace("\n", "<br/>")
    text = _wrap_cjk(text)
    return Paragraph(text, styles[key])


def _table(rows: list, col_widths: list, styles: dict) -> Table:
    """创建格式化表格。表内容经 _wrap_cjk 处理中文混排。"""
    formatted = []
    for i, row in enumerate(rows):
        sty = styles["cell_header"] if i == 0 else styles["cell"]
        formatted.append([Paragraph(_wrap_cjk(str(c)).replace("\n", "<br/>"), sty) for c in row])

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

    # --- 正文：按章节解析 ---
    sections = content.strip().split("\n#")
    for i, sec in enumerate(sections):
        sec = sec.strip()
        if not sec:
            continue

        # 第一个章节可能有 "# " 前缀，后续章节在 split 时去掉了 "#"
        if i == 0 and sec.startswith("# "):
            sec = sec[2:]
        elif i == 0 and sec.startswith("#"):
            sec = sec[1:]

        # 提取章节标题和正文
        lines = sec.split("\n", 1)
        heading = lines[0].strip()
        # 去掉可能的 "##" 前缀（二级标题）
        heading = heading.lstrip("#").strip()
        sec_body = lines[1].strip() if len(lines) > 1 else ""

        # 渲染章节标题
        story.append(Paragraph(_wrap_cjk(heading), section_h))
        story.append(_red_line(0.3, 4))

        # 渲染章节正文（按段落分割）
        for para in sec_body.split("\n"):
            para = para.strip()
            if para:
                # 检测表格行（包含 | 符号）
                if " | " in para and para.count("|") >= 2:
                    rows = []
                    for row_line in [para]:
                        cells = [c.strip() for c in row_line.split("|")]
                        if cells:
                            rows.append(cells)
                    if rows:
                        col_w = [(doc.width - 50) / len(rows[0])] * len(rows[0])
                        story.append(_table(rows, col_w, styles))
                        story.append(Spacer(1, 3 * mm))
                else:
                    story.append(_p(para, styles, "body"))
            else:
                story.append(Spacer(1, 2 * mm))

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
