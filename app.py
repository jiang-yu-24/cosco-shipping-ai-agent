"""
Streamlit 前端界面 — 中远海运散货 AI 助理「远航助手」
====================================================
Agent 应用风格布局：上方查询栏 + 下方结果面板 + 历史记录
"""

import os
import streamlit as st

# ============================================================
# 环境适配
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
    footer {visibility: hidden;}
    .query-input textarea { font-size: 16px !important; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# 会话状态初始化
# ============================================================
if "history" not in st.session_state:
    st.session_state.history = []          # [{query, response}]
    st.session_state.file_loaded = False
    st.session_state.last_file_key = None
    st.session_state.widget_key = 0        # 用于重置输入框和上传组件

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
            continue  # 不在展示列表中的工具（如内部工具）跳过
        with st.expander(TOOL_DISPLAY_NAMES[func_name], expanded=False):
            st.caption(tool["function"]["description"])

    st.divider()

    if st.button("🗑️ 清空历史", use_container_width=True, type="secondary"):
        st.session_state.history = []
        st.rerun()

    st.divider()
    st.caption("中远海运散货运输有限公司")

# ============================================================
# 右侧主区域
# ============================================================
st.title("🚢 远航助手")
st.caption("中远海运散货运输智能助理 · 船期查询 · 文件分析 · 实时信息")

# ============================================================
# 上方查询栏
# ============================================================
# 第一行：查询输入 + 查询按钮
col_input, col_btn = st.columns([8, 1])
with col_input:
    user_query = st.text_area(
        "查询内容",
        placeholder="请输入您的查询，例如：查一下西澳-青岛的船期，或 这份提单的托运人是谁？",
        label_visibility="collapsed",
        height=68,
        key=f"query_input_{st.session_state.widget_key}",
    )
with col_btn:
    st.write("")  # 对齐
    submit = st.button("查询", use_container_width=True, type="primary")

# 第二行：文件上传（占一整行）
uploaded_file = st.file_uploader(
    "上传文件进行分析（支持 PDF / Excel / CSV / TXT，上传后查询将基于文件内容回答）",
    type=["pdf", "xlsx", "xls", "csv", "txt"],
    help="上传后可在查询中对文件内容提问，例如「这份提单的托运人是谁？」",
    label_visibility="visible",
    key=f"file_uploader_{st.session_state.widget_key}",
)

# 处理文件上传
if uploaded_file is not None:
    file_key = f"{uploaded_file.name}_{uploaded_file.size}"
    if st.session_state.last_file_key != file_key:
        with st.spinner("正在解析文件..."):
            file_text = parse_file_content(uploaded_file.getvalue(), uploaded_file.name)
        set_uploaded_file(file_text, uploaded_file.name)
        st.session_state.last_file_key = file_key
        st.session_state.file_loaded = True
        st.rerun()

st.divider()

# ============================================================
# 执行查询
# ============================================================
if submit and user_query.strip():
    with st.spinner("🤔 正在分析中..."):
        try:
            # 构建历史上下文
            history_for_agent = []
            for h in st.session_state.history:
                history_for_agent.append({"role": "user", "content": h["query"]})
                history_for_agent.append({"role": "assistant", "content": h["response"]})

            # 注入文件内容
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

            # 存入历史
            st.session_state.history.insert(0, {
                "query": user_query.strip(),
                "response": response,
            })

            # 清空输入框和上传文件
            set_uploaded_file("", "")
            st.session_state.file_loaded = False
            st.session_state.last_file_key = None
            st.session_state.widget_key += 1
            st.rerun()

        except Exception:
            st.error("❌ 系统繁忙，请稍后重试。")

elif submit and not user_query.strip():
    st.warning("请输入查询内容")

# ============================================================
# 最新结果面板
# ============================================================
if st.session_state.history:
    latest = st.session_state.history[0]

    st.subheader("📋 查询结果")
    with st.container(border=True):
        st.caption(f"🔍 查询：{latest['query'][:100]}{'...' if len(latest['query']) > 100 else ''}")
        st.markdown(latest["response"])

    # ============================================================
    # 历史记录
    # ============================================================
    # PDF 下载按钮（Agent 生成文档后自动显示）
    try:
        from pdf_utils import get_pdf
        pdf_data, pdf_name = get_pdf()
    except ImportError:
        pdf_data, pdf_name = None, ""
    if pdf_data is not None:
        st.download_button(
            label=f"📥 下载 {pdf_name}",
            data=pdf_data,
            file_name=pdf_name,
            mime="application/pdf",
            type="primary",
        )

    if len(st.session_state.history) > 1:
        st.subheader("📜 历史记录")
        for i, h in enumerate(st.session_state.history[1:], 1):
            with st.expander(f"🔍 {h['query'][:60]}{'...' if len(h['query']) > 60 else ''}", expanded=False):
                st.markdown(h["response"])

# ============================================================
# 欢迎状态（无历史时的初始界面）
# ============================================================
else:
    st.info(
        "👋 欢迎使用远航助手！请在上方输入您的查询内容，点击「查询」按钮开始。\n\n"
        "**试试这些：**\n"
        "• 查一下西澳-青岛的船期\n"
        "• 上传一份提单 PDF，问：这份提单的托运人是谁？\n"
        "• 分析这份船期表中有没有去天津的船"
    )
