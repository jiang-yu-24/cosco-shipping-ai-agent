"""
Streamlit 前端界面 — 中远海运散货 AI 助理「远航助手」
====================================================
基于 Streamlit 构建的聊天式 AI Agent 交互界面。
布局：左侧边栏（工具列表 + 设置）+ 右侧主区（聊天窗口）。

环境适配说明：
  - 本地开发：从 .env 文件读取 DEEPSEEK_API_KEY（通过 python-dotenv）
  - Streamlit Cloud：从 st.secrets 读取 DEEPSEEK_API_KEY（在 Cloud 控制台配置）
    app.py 会在导入 agent_core 前将 st.secrets 桥接到 os.environ，
    这样 agent_core.py 不需要感知运行环境差异。
"""

import os
import streamlit as st

# ============================================================
# 环境适配：将 Streamlit Cloud Secrets 桥接到 os.environ
# ============================================================
# Streamlit Cloud 的 Secrets 不会自动注入到环境变量中，
# 因此需要在导入 agent_core 之前手动完成这个映射。
# 如果 st.secrets 中不存在该 key（本地开发场景），则跳过，
# agent_core 内部的 python-dotenv 会从 .env 文件中加载。
if "DEEPSEEK_API_KEY" in st.secrets:
    os.environ["DEEPSEEK_API_KEY"] = st.secrets["DEEPSEEK_API_KEY"]

# 导入本项目的核心模块
from tools import TOOL_NAMES, TOOL_DESCRIPTIONS, TOOL_DISPLAY_NAMES, parse_file_content, set_uploaded_file, get_uploaded_file_info
from agent_core import run_agent

# ============================================================
# 页面配置
# ============================================================
st.set_page_config(
    page_title="远航助手 - 中远海运散货运输智能助理",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": None,
    },
)

# 隐藏 Streamlit 默认页脚与工具栏
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ============================================================
# 左侧边栏
# ============================================================
with st.sidebar:
    # --- Logo & 标题 ---
    st.markdown("# 🚢 远航助手")
    st.markdown("*智能航运服务平台*")
    st.divider()

    # --- 文件状态 ---
    if st.session_state.get("file_loaded"):
        st.subheader("📎 已加载文件")
        _, file_name = get_uploaded_file_info()
        st.success(f"📄 {file_name}")
        st.caption("💡 可在对话框中对文件内容提问")
        if st.button("清除文件", use_container_width=True):
            set_uploaded_file("", "")
            st.session_state.file_loaded = False
            st.session_state.last_file_key = None
            st.rerun()
        st.divider()

    # --- 当前挂载工具列表 ---
    st.subheader("🔧 服务能力")
    st.caption(f"共 {len(TOOL_NAMES)} 项服务")

    for tool in TOOL_DESCRIPTIONS:
        tool_info = tool["function"]
        func_name = tool_info["name"]
        display_name = TOOL_DISPLAY_NAMES.get(func_name, func_name)
        with st.expander(display_name, expanded=False):
            st.caption(tool_info["description"])

    st.divider()

    # --- 清空对话按钮 ---
    if st.button("🗑️ 清空对话", use_container_width=True, type="secondary"):
        st.session_state.messages = []
        st.rerun()

    # --- 底部信息 ---
    st.divider()
    st.caption("中远海运散货运输有限公司")

# ============================================================
# 右侧主区域 — 聊天窗口
# ============================================================

# 页面标题
st.title("🚢 远航助手")
st.markdown("中远海运散货运输智能助理，为您提供船期查询、航运信息等服务")

# --- 初始化会话状态 ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.file_loaded = False
    st.session_state.last_file_key = None
    # 首次进入时显示欢迎消息
    st.session_state.messages.append({
        "role": "assistant",
        "content": (
            "👋 您好！我是**远航助手**，您的智能航运服务助理。\n\n"
            "我目前可以帮您：\n"
            "• 📅 查询当前日期和时间\n"
            "• 🚢 查询散货船期信息（支持：西澳-青岛、巴西-天津、印尼-湛江）\n"
            "• 📎 分析上传的文件（支持 PDF / Excel / CSV / TXT）\n\n"
            "请上传文件或直接向我提问！"
        ),
    })

# --- 渲染历史消息 ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 聊天输入区（输入框 + 右侧上传按钮） ---
col_input, col_upload = st.columns([20, 1])
with col_input:
    user_input = st.chat_input(
        placeholder="请输入您的问题，或点击右侧 📎 上传文件后提问...",
    )
with col_upload:
    # 弹窗式上传，点击 📎 按钮展开文件选择
    with st.popover("📎", use_container_width=True):
        uploaded_file = st.file_uploader(
            "上传文件",
            type=["pdf", "xlsx", "xls", "csv", "txt"],
            help="支持 PDF、Excel、CSV、TXT。上传后可在对话中对文件内容提问。",
            label_visibility="collapsed",
            key="file_uploader_main",
        )

        # 处理文件上传（在 popover 内完成解析+状态更新）
        if uploaded_file is not None:
            file_key = f"{uploaded_file.name}_{uploaded_file.size}"
            if "last_file_key" not in st.session_state or st.session_state.last_file_key != file_key:
                with st.spinner("正在解析..."):
                    file_text = parse_file_content(uploaded_file.getvalue(), uploaded_file.name)
                set_uploaded_file(file_text, uploaded_file.name)
                st.session_state.last_file_key = file_key
                st.session_state.file_loaded = True
                st.success(f"✅ 已加载")
                st.rerun()

# 输入框下方的提示语
st.caption(
    "💬 例如：*现在几点了？*  |  *查一下西澳-青岛的船期*  |  *这份提单的托运人是谁？*"
)

# --- 处理用户输入 ---
if user_input:
    # 1. 将用户消息追加到历史并显示
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # 2. 调用 Agent 核心引擎（传递历史消息上下文）
    with st.chat_message("assistant"):
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

                # 如果用户已上传文件，将文件内容作为上下文注入到用户问题中
                query = user_input
                if st.session_state.get("file_loaded"):
                    file_content, file_name = get_uploaded_file_info()
                    if file_content:
                        query = (
                            f"【用户已上传文件「{file_name}」，文件内容如下】\n\n"
                            f"{file_content}\n\n"
                            f"【文件内容结束。用户的问题是】\n{user_input}"
                        )

                response = run_agent(
                    user_query=query,
                    chat_history=history_for_agent if history_for_agent else None,
                )
                st.markdown(response)
                # 3. 将助手回复追加到历史
                st.session_state.messages.append({"role": "assistant", "content": response})

            except Exception as e:
                error_msg = f"❌ 系统繁忙，请稍后重试。如持续出现此问题，请联系管理员。"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
