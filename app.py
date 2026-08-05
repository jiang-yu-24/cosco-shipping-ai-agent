"""
Streamlit 前端界面 — 中远海运散货 AI 助理「远航助手」
"""

import os
import streamlit as st

if "DEEPSEEK_API_KEY" in st.secrets:
    os.environ["DEEPSEEK_API_KEY"] = st.secrets["DEEPSEEK_API_KEY"]

from tools import (
    TOOL_NAMES, TOOL_DESCRIPTIONS, TOOL_DISPLAY_NAMES,
    parse_file_content, set_uploaded_file, get_uploaded_file_info,
)
from agent_core import run_agent

st.set_page_config(
    page_title="远航助手 - 中远海运散货运输智能助理",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"Get Help": None, "Report a bug": None, "About": None},
)

st.markdown("""
<style>
    footer {visibility: hidden;}
    .query-input textarea { font-size: 16px !important; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# 会话状态
# ============================================================
if "history" not in st.session_state:
    st.session_state.history = []
    st.session_state.file_loaded = False
    st.session_state.last_file_key = None
    st.session_state.widget_key = 0

# ============================================================
# 左侧边栏
# ============================================================
with st.sidebar:
    st.markdown("# 🚢 远航助手")
    st.markdown("*智能航运服务平台*")
    st.divider()

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

    st.subheader("🔧 服务能力")
    st.caption(f"共 {len(TOOL_NAMES)} 项服务")
    for tool in TOOL_DESCRIPTIONS:
        func_name = tool["function"]["name"]
        if func_name not in TOOL_DISPLAY_NAMES:
            continue
        with st.expander(TOOL_DISPLAY_NAMES[func_name], expanded=False):
            st.caption(tool["function"]["description"])

    st.divider()

    st.subheader("📜 历史记录")
    if st.session_state.history:
        for h in st.session_state.history[:10]:
            with st.expander(f"🔍 {h['query'][:30]}{'...' if len(h['query']) > 30 else ''}", expanded=False):
                st.markdown(h["response"])
    else:
        st.caption("暂无查询记录")

    st.divider()

    if st.button("🗑️ 清空历史", use_container_width=True, type="secondary"):
        st.session_state.history = []
        st.rerun()

    st.divider()
    st.caption("中远海运散货运输有限公司")

# ============================================================
# 右侧主区域 — 标题 + 状态占位
# ============================================================
st.title("🚢 远航助手")
st.caption("中远海运散货运输智能助理 · 船期查询 · 文件分析 · 实时信息")

status_placeholder = st.empty()

# ============================================================
# 第1区：结果面板（最先渲染 → 显示在上方）
# ============================================================
if st.session_state.history:
    latest = st.session_state.history[0]

    st.subheader("📋 查询结果")
    with st.container(border=True):
        st.caption(f"🔍 查询：{latest['query'][:100]}{'...' if len(latest['query']) > 100 else ''}")
        st.markdown(latest["response"])

    try:
        from pdf_utils import get_pdf
        pdf_data, pdf_name = get_pdf()
    except ImportError:
        pdf_data, pdf_name = None, ""
    if pdf_data is not None:
        st.download_button(
            label=f"📥 下载 {pdf_name}",
            data=pdf_data, file_name=pdf_name,
            mime="application/pdf", type="primary",
        )
else:
    st.info(
        "👋 欢迎使用远航助手！请在下方输入查询内容。\n\n"
        "**试试这些：**\n"
        "• 查一下西澳-青岛的船期\n"
        "• 上传一份提单 PDF，问：托运人是谁？\n"
        "• 帮我生成一份船期确认函"
    )

st.divider()

# ============================================================
# 第2区：查询栏（st.form —— Enter 直接提交）
# ============================================================
# 表单内：查询框 + 按钮（Enter 直接提交）
with st.form(key=f"query_form_{st.session_state.widget_key}", clear_on_submit=False):
    col_input, col_btn = st.columns([8, 1])
    with col_input:
        user_query = st.text_area(
            "查询内容",
            placeholder="Shift+Enter 换行，Enter 直接查询",
            label_visibility="collapsed",
            height=68,
            key=f"query_input_{st.session_state.widget_key}",
        )
    with col_btn:
        st.write("")
        submit = st.form_submit_button("查询", use_container_width=True, type="primary")

# 表单外：文件上传（独立于查询，选择文件即解析）
uploaded_file = st.file_uploader(
    "上传文件进行分析（支持 PDF / Excel / CSV / TXT）",
    type=["pdf", "xlsx", "xls", "csv", "txt"],
    help="上传后可在查询中对文件内容提问",
    label_visibility="visible",
    key=f"file_uploader_{st.session_state.widget_key}",
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

# ============================================================
# 第3区：查询处理逻辑
# ============================================================
if submit and user_query.strip():
    status_placeholder.info("🤔 正在分析中，请稍候...")

    try:
        history_for_agent = []
        for h in st.session_state.history:
            history_for_agent.append({"role": "user", "content": h["query"]})
            history_for_agent.append({"role": "assistant", "content": h["response"]})

        query = user_query.strip()
        if st.session_state.file_loaded:
            file_content, file_name = get_uploaded_file_info()
            if file_content:
                query = (
                    f"【用户已上传文件「{file_name}」，文件内容如下】\n\n"
                    f"{file_content}\n\n"
                    f"【文件内容结束。用户的问题是】\n{user_query.strip()}"
                )

        response = run_agent(
            user_query=query,
            chat_history=history_for_agent if history_for_agent else None,
        )

        st.session_state.history.insert(0, {
            "query": user_query.strip(),
            "response": response,
        })

        set_uploaded_file("", "")
        st.session_state.file_loaded = False
        st.session_state.last_file_key = None
        st.session_state.widget_key += 1
        status_placeholder.empty()
        st.rerun()

    except Exception:
        status_placeholder.error("❌ 系统繁忙，请稍后重试。")

elif submit and not user_query.strip():
    status_placeholder.warning("请输入查询内容")
