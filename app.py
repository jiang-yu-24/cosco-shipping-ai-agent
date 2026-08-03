"""
Streamlit 前端界面 — 中远海运散货 AI 助理「远航助手」
====================================================
布局：左侧边栏（服务列表 + 文件状态）+ 右侧主区（聊天窗口 + 上传 + 输入框）
"""

import os
import streamlit as st

# ============================================================
# 环境适配：Streamlit Cloud Secrets → os.environ
# ============================================================
if "DEEPSEEK_API_KEY" in st.secrets:
    os.environ["DEEPSEEK_API_KEY"] = st.secrets["DEEPSEEK_API_KEY"]

from tools import (
    TOOL_NAMES, TOOL_DESCRIPTIONS, TOOL_DISPLAY_NAMES,
    parse_file_content, set_uploaded_file, get_uploaded_file_info,
)
from agent_core import run_agent

# ============================================================
# 页面配置
# ============================================================
st.set_page_config(
    page_title="远航助手 - 中远海运散货运输智能助理",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"Get Help": None, "Report a bug": None, "About": None},
)

st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    /* 文件上传按钮紧凑样式 */
    div[data-testid="stFileUploader"] {width: 52px;}
    div[data-testid="stFileUploader"] section {padding: 0;}
</style>
""", unsafe_allow_html=True)

# ============================================================
# 会话状态初始化（必须在 sidebar 之前）
# ============================================================
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.file_loaded = False
    st.session_state.last_file_key = None
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

# ============================================================
# 左侧边栏
# ============================================================
with st.sidebar:
    st.markdown("# 🚢 远航助手")
    st.markdown("*智能航运服务平台*")
    st.divider()

    # 文件状态（仅在已加载时显示）
    if st.session_state.file_loaded:
        st.subheader("📎 已加载文件")
        _, file_name = get_uploaded_file_info()
        st.success(f"📄 {file_name}")
        if st.button("清除文件", use_container_width=True):
            set_uploaded_file("", "")
            st.session_state.file_loaded = False
            st.session_state.last_file_key = None
            st.rerun()
        st.divider()

    # 服务能力
    st.subheader("🔧 服务能力")
    st.caption(f"共 {len(TOOL_NAMES)} 项服务")
    for tool in TOOL_DESCRIPTIONS:
        func_name = tool["function"]["name"]
        display_name = TOOL_DISPLAY_NAMES.get(func_name, func_name)
        with st.expander(display_name, expanded=False):
            st.caption(tool["function"]["description"])

    st.divider()

    # 清空对话
    if st.button("🗑️ 清空对话", use_container_width=True, type="secondary"):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.caption("中远海运散货运输有限公司")

# ============================================================
# 右侧主区域
# ============================================================
st.title("🚢 远航助手")
st.markdown("中远海运散货运输智能助理，为您提供船期查询、航运信息等服务")

# 渲染历史消息
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 文件上传（紧凑一行，位于输入框上方）
uploaded_file = st.file_uploader(
    "📎 上传文件（支持 PDF / Excel / CSV / TXT）",
    type=["pdf", "xlsx", "xls", "csv", "txt"],
    help="上传后可在对话中对文件内容提问，例如「这份提单的托运人是谁？」",
    label_visibility="visible",
    key="file_uploader_main",
)

if uploaded_file is not None:
    file_key = f"{uploaded_file.name}_{uploaded_file.size}"
    if st.session_state.last_file_key != file_key:
        with st.spinner("正在解析文件..."):
            file_text = parse_file_content(uploaded_file.getvalue(), uploaded_file.name)
        set_uploaded_file(file_text, uploaded_file.name)
        st.session_state.last_file_key = file_key
        st.session_state.file_loaded = True
        st.rerun()

# 聊天输入框
user_input = st.chat_input(placeholder="请输入您的问题...")

st.caption("💬 例如：*现在几点了？*  |  *查一下西澳-青岛的船期*  |  *这份提单的托运人是谁？*")

# ============================================================
# 处理用户输入
# ============================================================
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("🤔 正在思考中..."):
            try:
                # 构建历史上下文
                history_for_agent = [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages[:-1]
                    if m["role"] in ("user", "assistant")
                ]

                # 注入文件内容
                query = user_input
                if st.session_state.file_loaded:
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
                st.session_state.messages.append({"role": "assistant", "content": response})

            except Exception:
                error_msg = "❌ 系统繁忙，请稍后重试。如持续出现此问题，请联系管理员。"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
