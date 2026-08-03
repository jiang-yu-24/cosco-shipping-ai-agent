"""
工具函数定义模块 — 业务逻辑占位层
=====================================
此文件为业务逻辑占位，后续可替换为：
  - 合同/提单智能解析（OCR + NLP）
  - 散货船期/运价数据中台 API 调用
  - 港口拥堵指数、AIS 船舶轨迹查询
  - 企业内部 RAG 知识库检索
当前版本仅提供两个演示工具用于跑通 Agent 的 ReAct 闭环。
"""

import csv
import io
import json
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

# ============================================================
# 时区配置
# ============================================================
# 北京时间（东八区）— Streamlit Cloud 服务器使用 UTC 时区，
# 因此必须显式指定时区，否则 datetime.now() 会慢 8 小时
_CST = timezone(timedelta(hours=8), name="Asia/Shanghai")

# ============================================================
# 上传文件内容暂存区
# ============================================================
# app.py 在上传文件后将解析后的文本存储于此，
# Agent 工具 search_file_content 可检索该内容
_uploaded_file_content: str = ""
_uploaded_file_name: str = ""


def set_uploaded_file(content: str, filename: str) -> None:
    """供 app.py 调用，将已解析的文件内容存入模块全局变量。"""
    global _uploaded_file_content, _uploaded_file_name
    _uploaded_file_content = content
    _uploaded_file_name = filename


def get_uploaded_file_info() -> tuple:
    """返回 (content, filename) 供 app.py 读取。"""
    return _uploaded_file_content, _uploaded_file_name


# ============================================================
# 文件解析函数
# ============================================================

def parse_file_content(file_bytes: bytes, filename: str, max_chars: int = 8000) -> str:
    """
    根据文件扩展名选择解析器，提取文本内容。

    支持格式：PDF、Excel(.xlsx)、CSV、TXT
    超过 max_chars 时截断并追加提示。
    """
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""

    try:
        if ext == "pdf":
            text = _parse_pdf(file_bytes)
        elif ext in ("xlsx", "xls"):
            text = _parse_excel(file_bytes)
        elif ext == "csv":
            text = _parse_csv(file_bytes)
        elif ext == "txt":
            text = file_bytes.decode("utf-8", errors="replace")
        else:
            return f"❌ 暂不支持 .{ext} 文件格式，请上传 PDF、Excel、CSV 或 TXT 文件。"

        if not text.strip():
            return "⚠️ 文件中未提取到可读文本内容。"

        if len(text) > max_chars:
            text = text[:max_chars] + f"\n\n... (文件内容已截断，共 {len(text)} 字符，仅展示前 {max_chars} 字符)"

        return text

    except Exception as e:
        return f"❌ 文件解析失败：{str(e)}"


def _parse_pdf(file_bytes: bytes) -> str:
    """从 PDF 二进制数据中提取文本。"""
    from PyPDF2 import PdfReader
    reader = PdfReader(io.BytesIO(file_bytes))
    parts = []
    for i, page in enumerate(reader.pages):
        page_text = page.extract_text()
        if page_text:
            parts.append(f"--- 第{i+1}页 ---\n{page_text}")
    return "\n\n".join(parts)


def _parse_excel(file_bytes: bytes) -> str:
    """从 Excel 二进制数据中提取所有工作表的文本。"""
    from openpyxl import load_workbook
    wb = load_workbook(io.BytesIO(file_bytes), data_only=True)
    parts = []
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        parts.append(f"--- 工作表: {sheet_name} ---")
        for row in ws.iter_rows(values_only=True):
            row_vals = [str(v) if v is not None else "" for v in row]
            if any(v for v in row_vals):
                parts.append(" | ".join(row_vals))
    return "\n".join(parts)


def _parse_csv(file_bytes: bytes) -> str:
    """从 CSV 二进制数据中提取文本。"""
    text = file_bytes.decode("utf-8", errors="replace")
    reader = csv.reader(io.StringIO(text))
    parts = []
    for row in reader:
        parts.append(" | ".join(row))
    return "\n".join(parts)


# ============================================================
# 工具函数定义区
# ============================================================

def get_current_time() -> str:
    """
    获取当前北京时间（东八区）。
    返回格式化的日期时间字符串，用于演示 Agent 调用本地工具的能力。
    """
    now = datetime.now(_CST)
    # 使用中文友好的日期时间格式
    return now.strftime("%Y年%m月%d日 %H:%M:%S (星期%w) 北京时间")


def query_shipping_schedule(route: str) -> str:
    """
    模拟查询散货船期信息。

    参数:
        route: str - 航运路线描述，例如 "西澳-青岛"、"巴西-天津"、"印尼-湛江"

    返回:
        str - 虚构但业务逻辑通顺的船期信息（含船名、预计离港/到港时间、货种等）
    """
    # --- 模拟船期数据库 ---
    # 在实际项目中，这里应调用中远海运数据中台 API 或内部调度系统
    mock_schedule_db = {
        "西澳-青岛": {
            "vessel": "COSCO SHIPPING BULK - 致远号 (ZHI YUAN)",
            "cargo": "铁矿石 (Iron Ore)",
            "departure": "2026-08-15 (澳大利亚 黑德兰港)",
            "arrival": "2026-08-28 (中国 青岛前湾港)",
            "duration": "约13天",
            "status": "在港待装 (Waiting for Loading)",
            "remark": "受NW季风影响，预计有0.5天延迟",
        },
        "巴西-天津": {
            "vessel": "COSCO SHIPPING BULK - 远望号 (YUAN WANG)",
            "cargo": "大豆 (Soybean)",
            "departure": "2026-08-05 (巴西 桑托斯港)",
            "arrival": "2026-09-20 (中国 天津港)",
            "duration": "约46天",
            "status": "航行中 (Underway)",
            "remark": "经好望角航线，当前航速12.5节",
        },
        "印尼-湛江": {
            "vessel": "COSCO SHIPPING BULK - 远航号 (YUAN HANG)",
            "cargo": "动力煤 (Thermal Coal)",
            "departure": "2026-08-10 (印度尼西亚 塔巴尼奥港)",
            "arrival": "2026-08-18 (中国 湛江港)",
            "duration": "约8天",
            "status": "装货中 (Loading)",
            "remark": "天气良好，预计准时发运",
        },
    }

    # 尝试精确匹配
    if route in mock_schedule_db:
        info = mock_schedule_db[route]
        return (
            f"📍 航线：{route}\n"
            f"🚢 船名：{info['vessel']}\n"
            f"📦 货种：{info['cargo']}\n"
            f"⚓ 预计离港：{info['departure']}\n"
            f"🏁 预计到港：{info['arrival']}\n"
            f"⏱️ 预计航程：{info['duration']}\n"
            f"📡 船舶状态：{info['status']}\n"
            f"📝 备注：{info['remark']}"
        )

    # 未匹配到航线时的兜底返回
    supported_routes = "、".join(mock_schedule_db.keys())
    return (
        f"⚠️ 暂未收录航线「{route}」的船期数据。\n"
        f"当前支持的航线：{supported_routes}\n"
        f"（实际项目中此接口将对接实时调度数据库）"
    )


def search_file_content(keyword: str) -> str:
    """
    在用户上传的文件中搜索关键词，返回匹配的段落。

    适用于用户上传了提单、合同、船期表等文件后，
    需要从文件中提取特定信息（如托运人、货量、港口等）。

    参数:
        keyword: str - 要搜索的关键词或短语
    """
    content, filename = get_uploaded_file_info()

    if not content:
        return "⚠️ 当前没有已上传的文件。请先在左侧上传一份文件（PDF/Excel/CSV/TXT）。"

    if not keyword.strip():
        return "⚠️ 请输入要搜索的关键词。"

    # 将内容按行拆分，搜索包含关键词的行及上下文
    lines = content.split("\n")
    matched_blocks = []
    kw_lower = keyword.lower()

    for i, line in enumerate(lines):
        if kw_lower in line.lower():
            # 取匹配行及上下各1行作为上下文
            start = max(0, i - 1)
            end = min(len(lines), i + 2)
            block = "\n".join(lines[start:end])
            matched_blocks.append(block)

    if not matched_blocks:
        return (
            f"📄 在文件「{filename}」中未找到与「{keyword}」相关的内容。\n"
            f"建议尝试其他关键词，或直接询问我关于文件内容的概括性问题。"
        )

    # 最多返回前5个匹配块
    result = f"📄 在文件「{filename}」中找到 {len(matched_blocks)} 处「{keyword}」相关匹配：\n\n"
    for j, block in enumerate(matched_blocks[:5], 1):
        result += f"【匹配 {j}】\n{block}\n\n"

    if len(matched_blocks) > 5:
        result += f"... (还有 {len(matched_blocks) - 5} 处匹配未展示，建议缩小搜索范围)"

    return result


# ============================================================
# 工具注册表 — 供 agent_core.py 和 app.py 使用
# ============================================================

# TOOL_DESCRIPTIONS: 符合 OpenAI Function Calling 规范的工具定义列表
# 每个工具包含 name（函数名）、description（功能说明）、parameters（参数JSON Schema）
TOOL_DESCRIPTIONS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "获取当前系统日期和时间。当用户询问'现在几点'、'今天几号'、'当前时间'时调用此工具。",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_shipping_schedule",
            "description": (
                "查询中远海运散货船期信息。"
                "当用户询问特定航线的船期、船名、到港时间等信息时调用此工具。"
                "支持的航线包括：西澳-青岛（铁矿石）、巴西-天津（大豆）、印尼-湛江（动力煤）。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "route": {
                        "type": "string",
                        "description": "航运路线，例如 '西澳-青岛'、'巴西-天津'、'印尼-湛江'",
                    },
                },
                "required": ["route"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_file_content",
            "description": (
                "在用户已上传的文件中搜索指定关键词或短语，返回匹配段落的上下文。"
                "当用户询问关于已上传文件的细节（如'托运人是谁'、'装货港在哪'、"
                "'船期表中有没有去天津的船'）时调用此工具。"
                "支持的文件格式：PDF、Excel、CSV、TXT。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "要搜索的关键词或短语，例如'托运人'、'装货港'、'天津'",
                    },
                },
                "required": ["keyword"],
            },
        },
    },
]

# TOOL_MAPPING: 工具名 -> 实际Python函数的映射字典
# agent_core.py 通过此字典查找并执行本地函数
TOOL_MAPPING: Dict[str, Any] = {
    "get_current_time": get_current_time,
    "query_shipping_schedule": query_shipping_schedule,
    "search_file_content": search_file_content,
}

# TOOL_NAMES: 工具名称列表，供 app.py 侧边栏展示
TOOL_NAMES: List[str] = [t["function"]["name"] for t in TOOL_DESCRIPTIONS]

# TOOL_DISPLAY_NAMES: 工具函数名 -> 自然语言展示名
# app.py 侧边栏使用此映射展示服务能力，对用户隐藏内部函数名
TOOL_DISPLAY_NAMES: Dict[str, str] = {
    "get_current_time": "📅 实时时间查询",
    "query_shipping_schedule": "🚢 散货船期查询",
    "search_file_content": "🔍 文件内容检索",
}
