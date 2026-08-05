"""
PDF 文档生成模块 — 央企规范化公文模板
=======================================
基于 fpdf2 实现中文 PDF 文档生成。
支持：船期确认函、货运报告、通用公文。
仅供 Agent 后端调用，不在前端侧边栏展示。

中文字体加载策略：
  1. 遍历候选路径列表
  2. glob 通配搜索常见字体目录
  3. 调用 fc-list 命令查询系统可用中文字体
  4. 以上均失败则使用 Helvetica（中文将显示为空白）
"""

import glob
import io
import os
import subprocess
import base64
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple

from fpdf import FPDF

# 北京时间
_CST = timezone(timedelta(hours=8), name="Asia/Shanghai")

# 中文字体候选路径（支持 glob 通配符）
_FONT_GLOBS = [
    # macOS
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti*.ttc",
    "/System/Library/Fonts/Hiragino*.ttc",
    "/Library/Fonts/Arial Unicode.ttf",
    # Debian/Ubuntu (Streamlit Cloud) — fonts-noto-cjk 安装路径
    "/usr/share/fonts/opentype/noto/NotoSansCJK-*.ttc",
    "/usr/share/fonts/opentype/noto/NotoSerifCJK-*.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-*.ttc",
    "/usr/share/fonts/truetype/noto/NotoSerifCJK-*.ttc",
    "/usr/share/fonts/noto-cjk/*.ttc",
    "/usr/share/fonts/truetype/droid/DroidSans*.ttf",
    "/usr/share/fonts/truetype/wqy/*.ttc",
    "/usr/share/fonts/truetype/wqy/*.ttf",
    # 通用 Linux
    "/usr/share/fonts/**/*CJK*.ttc",
    "/usr/share/fonts/**/*CJK*.ttf",
    # Windows
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/msyh.ttf",
    "C:/Windows/Fonts/simsun.ttc",
]

# 全局字体路径缓存
_FONT_PATH: Optional[str] = None
_FONT_SEARCHED: bool = False


def _find_chinese_font() -> Optional[str]:
    """扫描系统，返回第一个可用的中文字体路径。"""
    global _FONT_PATH, _FONT_SEARCHED
    if _FONT_SEARCHED:
        return _FONT_PATH
    _FONT_SEARCHED = True

    # 1. glob 匹配候选路径
    for pattern in _FONT_GLOBS:
        matches = glob.glob(pattern, recursive=True)
        for path in matches:
            if os.path.isfile(path):
                _FONT_PATH = path
                return _FONT_PATH

    # 2. fc-list 命令查询（Linux 最可靠的方式）
    try:
        result = subprocess.run(
            ["fc-list", ":lang=zh", "file"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            # 取第一个结果的文件路径（格式：/path/to/font.ttf: Font Name）
            first_line = result.stdout.strip().split("\n")[0]
            font_path = first_line.split(":")[0].strip()
            if os.path.isfile(font_path):
                _FONT_PATH = font_path
                return _FONT_PATH
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass

    return None


# ============================================================
# PDF 生成核心
# ============================================================

class ShippingPDF(FPDF):
    """航运业务 PDF 文档基类，封装中文字体加载和公文格式。"""

    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=20)
        self._font_loaded = False
        self._init_font()

    def _init_font(self):
        font_path = _find_chinese_font()
        if font_path:
            self.add_font("cjk", "", font_path, uni=True)
            self.add_font("cjk", "B", font_path, uni=True)
            self._font_loaded = True
        else:
            # 无可用的中文字体，使用内置 Helvetica
            self._font_loaded = False

    def _font(self, bold: bool = False):
        """返回当前可用字体名。"""
        if self._font_loaded:
            return "cjk" if not bold else "cjk"
        return "Helvetica"

    def header_block(self, title: str, doc_no: str = ""):
        """公文红头标题区域。"""
        self.add_page()
        # 红色分隔线
        self.set_draw_color(180, 0, 0)
        self.set_line_width(0.8)
        self.line(15, 25, self.w - 15, 25)
        # 标题
        self.set_font(self._font(bold=True), "", 18)
        self.set_y(32)
        self.cell(0, 12, title, align="C")
        self.ln(14)
        # 文号
        if doc_no:
            self.set_font(self._font(), "", 10)
            self.set_text_color(100, 100, 100)
            self.cell(0, 8, doc_no, align="C")
            self.ln(10)
            self.set_text_color(0, 0, 0)
        # 红色分隔线
        self.set_draw_color(180, 0, 0)
        self.set_line_width(0.4)
        self.line(15, self.get_y(), self.w - 15, self.get_y())
        self.ln(10)

    def body_text(self, text: str, size: int = 11, indent: bool = True):
        """正文段落，首行缩进两字符。"""
        self.set_font(self._font(), "", size)
        if indent:
            self.cell(2 * size, 8, "")  # 缩进
        self.multi_cell(0, 7, text, align="L")
        self.ln(2)

    def body_table(self, rows: list, col_widths: list = None):
        """简单表格。"""
        if not rows:
            return
        if col_widths is None:
            col_widths = [self.w / len(rows[0]) - 2] * len(rows[0])
        self.set_font(self._font(), "", 10)
        for i, row in enumerate(rows):
            if i == 0:
                self.set_font(self._font(bold=True), "", 10)
            else:
                self.set_font(self._font(), "", 10)
            for j, cell in enumerate(row):
                w = col_widths[j] if j < len(col_widths) else 30
                self.cell(w, 8, str(cell), border=1, align="C")
            self.ln()
        self.ln(4)

    def signature_block(self, company: str = "中远海运散货运输有限公司"):
        """落款区域。"""
        self.set_font(self._font(), "", 11)
        self.ln(10)
        self.cell(0, 8, company, align="R")
        self.ln(8)
        now = datetime.now(_CST)
        date_str = now.strftime("%Y年%m月%d日")
        self.cell(0, 8, date_str, align="R")

    def footer(self):
        self.set_y(-15)
        self.set_font(self._font(), "", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"第 {self.page_no()} 页", align="C")


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
    """
    生成船期确认函。

    参数:
        route: 航线，如"西澳-青岛"
        vessel: 船名
        departure: 预计离港时间
        arrival: 预计到港时间
        cargo: 货种及货量
        consignor: 托运人
        consignee: 收货人
    """
    pdf = ShippingPDF()

    now = datetime.now(_CST)
    doc_no = f"COSCO BULK 航确字〔{now.year}〕第{now.strftime('%m%d%H%M')}号"

    pdf.header_block("船 期 确 认 函", doc_no)

    # 收件方
    pdf.set_font(pdf._font(bold=True), "", 11)
    pdf.cell(0, 8, f"致：{consignee}", align="L")
    pdf.ln(12)

    # 正文
    pdf.body_text(
        f"根据贵我双方签署的运输合同，我司确认以下船期安排，现函告如下："
    )
    pdf.ln(4)

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
    col_w = [(pdf.w - 30) * 0.3, (pdf.w - 30) * 0.7]
    pdf.body_table(table_data, col_w)

    # 备注
    pdf.body_text(
        "备注：以上船期为当前预计安排。如遇天气、港口拥堵等不可抗力因素，"
        "实际船期可能有所调整。我司将实时跟踪船舶动态，如有变更将第一时间通知贵方。"
    )

    # 联系方式
    pdf.ln(4)
    pdf.set_font(pdf._font(), "", 10)
    pdf.cell(0, 8, "如有疑问，请联系我司客服中心：400-XXX-XXXX", align="L")
    pdf.ln(8)

    pdf.signature_block()

    return pdf.output()


def generate_shipping_report(
    title: str,
    content: str,
    author: str = "远航助手",
) -> bytes:
    """
    生成通用航运报告。

    参数:
        title: 报告标题
        content: 报告正文（支持换行符分段）
        author: 编制人/部门
    """
    pdf = ShippingPDF()

    now = datetime.now(_CST)
    doc_no = f"COSCO BULK 报字〔{now.year}〕第{now.strftime('%m%d%H%M')}号"

    pdf.header_block(title, doc_no)

    # 编制信息
    pdf.set_font(pdf._font(), "", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, f"编制：{author}    日期：{now.strftime('%Y-%m-%d')}", align="R")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(12)

    # 正文（按段落处理）
    paragraphs = content.strip().split("\n")
    for para in paragraphs:
        para = para.strip()
        if para:
            pdf.body_text(para)
        else:
            pdf.ln(4)

    pdf.ln(6)
    pdf.signature_block()

    return pdf.output()


def generate_official_document(
    title: str,
    content: str,
    recipient: str = "",
    doc_type: str = "通知",
) -> bytes:
    """
    生成央企通用公文。

    参数:
        title: 公文标题
        content: 公文正文
        recipient: 主送单位
        doc_type: 公文类型（通知/函/报告/请示）
    """
    pdf = ShippingPDF()

    now = datetime.now(_CST)
    doc_no = f"COSCO BULK {doc_type}字〔{now.year}〕第{now.strftime('%m%d%H%M')}号"

    pdf.header_block(title, doc_no)

    # 主送单位
    if recipient:
        pdf.set_font(pdf._font(bold=True), "", 11)
        pdf.cell(0, 8, f"{recipient}：", align="L")
        pdf.ln(12)

    # 公文正文
    paragraphs = content.strip().split("\n")
    for para in paragraphs:
        para = para.strip()
        if para:
            pdf.body_text(para)
        else:
            pdf.ln(4)

    pdf.ln(6)
    pdf.signature_block()

    return pdf.output()


# ============================================================
# 存储已生成的 PDF（供 app.py 下载）
# ============================================================

_generated_pdf: Optional[bytes] = None
_generated_pdf_name: str = ""


def store_pdf(pdf_bytes: bytes, filename: str) -> None:
    """存储生成的 PDF 供前端下载。"""
    global _generated_pdf, _generated_pdf_name
    _generated_pdf = pdf_bytes
    _generated_pdf_name = filename


def get_pdf() -> Tuple[Optional[bytes], str]:
    """获取已生成的 PDF 数据及文件名，读取后清空。"""
    global _generated_pdf, _generated_pdf_name
    result = (_generated_pdf, _generated_pdf_name)
    _generated_pdf = None
    _generated_pdf_name = ""
    return result
