"""
Streamlit 前端界面 — 中远海运散货 AI 助理「远航助手」
====================================================
基于 Streamlit 构建的聊天式 AI Agent 交互界面。
布局：左侧边栏（工具列表 + 设置）+ 右侧主区（聊天窗口）。
"""

import streamlit as st

# 导入本项目的核心模块
from tools import TOOL_NAMES, TOOL_DESCRIPTIONS
from agent_core import run_agent

# ============================================================
# 页面配置
# ============================================================
st.set_page_config(
    page_title="远航助手 - 中远海运散货 AI Agent",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# 左侧边栏
# ============================================================
with st.sidebar:
    # --- Logo & 标题 ---
    st.markdown("# 🚢 远航助手")
    st.markdown("*COSCO Shipping Bulk AI Agent*")
    st.divider()

    # --- 当前挂载工具列表 ---
    st.subheader("🔧 当前挂载工具")
    st.caption(f"共 {len(TOOL_NAMES)} 个工具可供 Agent 调用")

    for i, tool in enumerate(TOOL_DESCRIPTIONS, 1):
        tool_info = tool["function"]
        with st.expander(f"{tool_info['name']}", expanded=False):
            st.markdown(f"**功能：** {tool_info['description']}")
            # 提取参数信息
            params = tool_info.get("parameters", {}).get("properties", {})
            required = tool_info.get("parameters", {}).get("required", [])
            if params:
                st.markdown("**参数：**")
                for pname, pinfo in params.items():
                    req_mark = " *（必填）*" if pname in required else ""
                    st.caption(f"  • `{pname}` ({pinfo.get('type', 'any')}){req_mark}")

    st.divider()

    # --- 清空对话按钮 ---
    if st.button("🗑️ 清空对话", use_container_width=True, type="secondary"):
        st.session_state.messages = []
        st.rerun()

    # --- 底部信息 ---
    st.divider()
    st.caption("💡 Powered by DeepSeek + Streamlit")
    st.caption("🖥️ 适配 Apple Silicon (M系列)")
    st.caption(f"📦 Python 3 | macOS")

# ============================================================
# 右侧主区域 — 聊天窗口
# ============================================================

# 页面标题
st.title("🚢 远航助手")
st.markdown("中远海运散货运输 AI 智能助理 —— 支持船期查询、时间查询等功能")

# --- 初始化会话状态 ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    # 首次进入时显示欢迎消息
    st.session_state.messages.append({
        "role": "assistant",
        "content": (
            "👋 您好！我是**远航助手**，中远海运散货运输 AI 智能助理。\n\n"
            "我目前可以帮您：\n"
            "• 📅 查询当前日期和时间\n"
            "• 🚢 查询散货船期信息（支持：西澳-青岛、巴西-天津、印尼-湛江）\n\n"
            "请随时向我提问！"
        ),
    })

# --- 渲染历史消息 ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 聊天输入框 ---
# Streamlit 的 chat_input 组件提供了原生的聊天输入体验
user_input = st.chat_input(
    placeholder="请输入您的问题...",
)

# 输入框下方的提示语
st.caption(
    "💬 例如：*现在几点了？*  或  *查一下西澳-青岛的船期*  或  *巴西到天津的船什么时候到？*"
)

# --- 处理用户输入 ---
if user_input:
    # 1. 将用户消息追加到历史并显示
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # 2. 调用 Agent 核心引擎（传递历史消息上下文）
    with st.chat_message("assistant"):
        # 构建历史消息（不含 system prompt，agent_core 会自动添加）
        # 我们传递完整的 messages 作为上下文
        with st.spinner("🤔 正在思考中..."):
            try:
                # 传入当前对话历史（不含最新的 user 消息，它在 run_agent 内部会追加）
                history = st.session_state.messages[:-1]  # 去掉刚追加的 user 消息
                # 只取 user 和 assistant 的消息（过滤掉欢迎消息等）
                history_for_agent = [
                    {"role": m["role"], "content": m["content"]}
                    for m in history
                    if m["role"] in ("user", "assistant")
                ]

                response = run_agent(
                    user_query=user_input,
                    chat_history=history_for_agent if history_for_agent else None,
                )
                st.markdown(response)
                # 3. 将助手回复追加到历史
                st.session_state.messages.append({"role": "assistant", "content": response})

            except Exception as e:
                error_msg = f"❌ 系统错误：{str(e)}\n请检查 API Key 配置和网络连接。"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
