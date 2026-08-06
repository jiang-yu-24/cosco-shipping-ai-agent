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
    get_emails,
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
    /* 加载动画：三个点依次跳动 */
    @keyframes dot-bounce {
        0%, 80%, 100% { opacity: 0; }
        40% { opacity: 1; }
    }
    .loading-dots span {
        animation: dot-bounce 1.4s infinite;
        font-size: 20px;
        font-weight: bold;
    }
    .loading-dots span:nth-child(1) { animation-delay: 0s; }
    .loading-dots span:nth-child(2) { animation-delay: 0.2s; }
    .loading-dots span:nth-child(3) { animation-delay: 0.4s; }
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
    st.session_state.processing = False
if "file_vault" not in st.session_state:
    st.session_state.file_vault = []

# ============================================================
# 左侧边栏
# ============================================================
with st.sidebar:
    st.markdown("# 🚢 远航助手")
    st.markdown("*智能航运服务平台*")
    st.divider()

    # 文件暂存区
    st.subheader("📎 文件暂存区")
    if st.session_state.file_vault:
        for i, f in enumerate(st.session_state.file_vault):
            icon = "📄" if f["type"] == "upload" else "📑"
            st.download_button(
                label=f"{icon} {f['name']}",
                data=f["data"],
                file_name=f["name"],
                mime="application/octet-stream" if f["type"] == "upload" else "application/pdf",
                use_container_width=True,
                key=f"vault_dl_{i}",
            )
        if st.button("清空暂存区", use_container_width=True):
            st.session_state.file_vault = []
            st.rerun()
    else:
        st.caption("暂无文件，上传或生成PDF后将出现在此")
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

# ============================================================
# 第1区：对话历史 / 欢迎框（上方）
# ============================================================
# 对话历史
if st.session_state.history:
    for i, h in enumerate(reversed(st.session_state.history)):
        with st.chat_message("user"):
            st.code(h["query"], language="")
        with st.chat_message("assistant"):
            if h.get("_loading"):
                st.markdown(
                    '<div style="'
                    'background: linear-gradient(135deg, #e8f0fe 0%, #d4e4fc 100%);'
                    'border: 1px solid #a8c8f0; border-radius: 10px;'
                    'padding: 14px 20px; font-size: 15px; color: #2c5aa0;'
                    '">'
                    '正在分析中<span class="loading-dots">'
                    '<span>.</span><span>.</span><span>.</span>'
                    '</span></div>',
                    unsafe_allow_html=True,
                )
            else:
                st.code(h["response"], language="")
            if h.get("file_data"):
                st.download_button(
                    label=f"📥 下载 {h['file_name']}",
                    data=h["file_data"],
                    file_name=h["file_name"],
                    mime="application/octet-stream",
                    key=f"hist_dl_{i}",
                )
            # 该回复关联的邮件
            for subject, body, recipient in h.get("emails", []):
                with st.container(border=True):
                    if recipient:
                        st.caption(f"收件人：{recipient}")
                    st.code(subject, language="")
                    st.code(body, language="")
else:
    st.info(
        "欢迎使用远航助手！请在下方框内输入指令。\n\n"
        "试试这些：\n"
        "查一下西澳-青岛的船期\n"
        "上传一份提单 PDF，问：托运人是谁？\n"
        "帮我生成一份船期确认函"
    )

# PDF 下载（对话下方）
try:
    from pdf_utils import get_pdfs
    pdfs = get_pdfs()
except ImportError:
    pdfs = []
for j, (pdf_data, pdf_name) in enumerate(pdfs):
    st.download_button(
        label=f"📥 下载 {pdf_name}",
        data=pdf_data, file_name=pdf_name,
        mime="application/pdf", type="primary",
        key=f"pdf_dl_{j}_{st.session_state.widget_key}",
    )
    if not any(f["name"] == pdf_name and f["type"] == "pdf" for f in st.session_state.file_vault):
        st.session_state.file_vault.append({
            "name": pdf_name, "data": pdf_data, "type": "pdf",
        })

# 状态提示（对话区与输入框之间）
status_placeholder = st.empty()
st.divider()

# ============================================================
# 第2区：查询栏（下方）
# ============================================================
with st.form(key=f"query_form_{st.session_state.widget_key}", clear_on_submit=True):
    user_query = st.text_area(
        "查询内容",
        placeholder="Shift+Enter 换行，Enter 直接查询",
        label_visibility="collapsed",
        height=64,
        key=f"query_input_{st.session_state.widget_key}",
    )
    uploaded_file = st.file_uploader(
        "📎 上传文件（PDF / Excel / CSV / TXT）",
        type=["pdf", "xlsx", "xls", "csv", "txt"],
        label_visibility="visible",
        key=f"file_uploader_{st.session_state.widget_key}",
    )
    submit = st.form_submit_button("↑ 发送", use_container_width=True, type="primary")

# ============================================================
# 第3区：查询处理
# ============================================================
# 阶段1：用户提交 → 先展示提问+加载动画，标记待处理
if submit and user_query.strip():
    st.session_state._pending_query = user_query.strip()
    st.session_state._pending_file = uploaded_file.getvalue() if uploaded_file else None
    st.session_state._pending_filename = uploaded_file.name if uploaded_file else None
    st.rerun()

# 阶段2：处理待处理查询
if st.session_state.get("_pending_query"):
    query_text = st.session_state._pending_query
    file_bytes = st.session_state.get("_pending_file")
    file_name = st.session_state.get("_pending_filename")
    del st.session_state._pending_query
    st.session_state._pending_file = None
    st.session_state._pending_filename = None

    # 先插入用户提问（占位，让用户立刻看到）
    st.session_state.history.insert(0, {
        "query": query_text,
        "response": "正在分析中...",
        "file_name": None,
        "file_data": None,
        "emails": [],
        "_loading": True,
    })
    st.session_state.widget_key += 1
    st.rerun()

# 阶段3：处理标记为 _loading 的条目
loading_entry = None
for h in st.session_state.history:
    if h.get("_loading"):
        loading_entry = h
        break

if loading_entry:
    try:
        query_text = loading_entry["query"]

        # 处理上传文件
        if file_bytes is not None or (hasattr(st, 'session_state') and False):
            pass  # 文件已在阶段1获取
        # 重新获取文件（如果有）
        if loading_entry.get("_pending_file"):
            fb = loading_entry["_pending_file"]
            fn = loading_entry.get("_pending_filename", "")
            if fb:
                file_text = parse_file_content(fb, fn)
                set_uploaded_file(file_text, fn)
                st.session_state.file_loaded = True

        history_for_agent = []
        for h in st.session_state.history:
            if h.get("_loading"):
                continue
            history_for_agent.append({"role": "user", "content": h["query"]})
            history_for_agent.append({"role": "assistant", "content": h["response"]})

        query = query_text
        if st.session_state.file_loaded:
            file_content, fname = get_uploaded_file_info()
            if file_content:
                query = (
                    f"【用户已上传文件「{fname}」，文件内容如下】\n\n"
                    f"{file_content}\n\n"
                    f"【文件内容结束。用户的问题是】\n{query_text}"
                )

        response = run_agent(
            user_query=query,
            chat_history=history_for_agent if history_for_agent else None,
        )

        # 拉取邮件
        entry_emails = []
        try:
            entry_emails = get_emails()
        except Exception:
            pass

        # 更新占位条目
        loading_entry["response"] = response
        loading_entry["emails"] = entry_emails
        loading_entry["_loading"] = False
        if file_bytes:
            loading_entry["file_name"] = file_name
            loading_entry["file_data"] = file_bytes
            if not any(f["name"] == file_name and f["type"] == "upload" for f in st.session_state.file_vault):
                st.session_state.file_vault.append({
                    "name": file_name, "data": file_bytes, "type": "upload",
                })

        set_uploaded_file("", "")
        st.session_state.file_loaded = False
        st.session_state.last_file_key = None
        st.rerun()

    except Exception:
        loading_entry["response"] = "❌ 系统繁忙，请稍后重试。"
        loading_entry["_loading"] = False
        st.rerun()

elif submit and not user_query.strip():
    status_placeholder.warning("请输入查询内容")
