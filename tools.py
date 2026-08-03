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

import json
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List


# ============================================================
# 时区配置
# ============================================================
# 北京时间（东八区）— Streamlit Cloud 服务器使用 UTC 时区，
# 因此必须显式指定时区，否则 datetime.now() 会慢 8 小时
_CST = timezone(timedelta(hours=8), name="Asia/Shanghai")


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
]

# TOOL_MAPPING: 工具名 -> 实际Python函数的映射字典
# agent_core.py 通过此字典查找并执行本地函数
TOOL_MAPPING: Dict[str, Any] = {
    "get_current_time": get_current_time,
    "query_shipping_schedule": query_shipping_schedule,
}

# TOOL_NAMES: 工具名称列表，供 app.py 侧边栏展示
TOOL_NAMES: List[str] = [t["function"]["name"] for t in TOOL_DESCRIPTIONS]

# TOOL_DISPLAY_NAMES: 工具函数名 -> 自然语言展示名
# app.py 侧边栏使用此映射展示服务能力，对用户隐藏内部函数名
TOOL_DISPLAY_NAMES: Dict[str, str] = {
    "get_current_time": "📅 实时时间查询",
    "query_shipping_schedule": "🚢 散货船期查询",
}
