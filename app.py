"""
Streamlit 前端界面 — 中远海运散货 AI 助理「散运助手」
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
    page_title="散运助手 - 中远海运散货运输智能助理",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"Get Help": None, "Report a bug": None, "About": None},
)

st.markdown("""
<style>
    footer {visibility: hidden;}
    .query-input textarea { font-size: 16px !important; }
    /* 加载动画 */
    @keyframes dot-bounce {
        0%, 80%, 100% { opacity: 0; }
        40% { opacity: 1; }
    }
    .loading-dots span {
        animation: dot-bounce 1.4s infinite;
        font-size: 20px; font-weight: bold;
    }
    .loading-dots span:nth-child(1) { animation-delay: 0s; }
    .loading-dots span:nth-child(2) { animation-delay: 0.2s; }
    .loading-dots span:nth-child(3) { animation-delay: 0.4s; }
    /* 示例按钮不换行 */
    button { white-space: nowrap !important; }
    /* 加载启动画面：海浪图铺满html */
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
    st.markdown("# 🚢 散运助手")
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
    st.caption(f"共 {len(TOOL_DISPLAY_NAMES)} 项服务")
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
st.title("🚢 散运助手")
st.caption("中远海运散货运输智能助理 · 船期查询 · 文件分析 · 邮件生成 · 文件生成")

# ============================================================
# 第1区：对话历史 / 欢迎框（上方）
# ============================================================
# 对话历史
if st.session_state.history:
    for i, h in enumerate(reversed(st.session_state.history)):
        with st.chat_message("user"):
            st.code(h["query"], language="")
        with st.chat_message("assistant"):
            if h.get("response") == "__loading__":
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
    st.markdown("欢迎使用散运助手！请在下方框内输入指令。")

# PDF 下载（对话与示例之间）
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

# 示例按钮（始终显示）
st.caption("推荐依次输入下面几个示例：")
cols = st.columns(3)
examples = [
    "查一下西澳-青岛的船期",
    "帮我生成几内亚最近五班船期确认函",
    "帮我根据上述确认函内容生成邮件",
]
for i, text in enumerate(examples):
    with cols[i]:
        if st.button(text, key=f"ex_{i}", use_container_width=True):
            st.session_state._fill_input = text
            st.session_state.widget_key += 1
            st.rerun()

# 状态提示（对话区与输入框之间）
status_placeholder = st.empty()
st.divider()

# ============================================================
# 第2区：查询栏（下方）
# ============================================================
with st.form(key=f"query_form_{st.session_state.widget_key}", clear_on_submit=True):
    fill_val = st.session_state.pop("_fill_input", "") if st.session_state.get("_fill_input") else ""
    user_query = st.text_area(
        "查询内容",
        value=fill_val,
        placeholder="Shift+Enter 换行，Enter 直接发送",
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
# 阶段1：提交 → 存待处理，rerun
if submit and user_query.strip():
    st.session_state._pq = user_query.strip()
    if uploaded_file is not None:
        st.session_state._pf = uploaded_file.getvalue()
        st.session_state._pfn = uploaded_file.name
    else:
        st.session_state._pf = None
        st.session_state._pfn = None
    st.rerun()

# 阶段2：_pq 存在 → 插入占位 + 清除 _pq，rerun 到阶段3
if st.session_state.get("_pq"):
    st.session_state.history.insert(0, {
        "query": st.session_state._pq,
        "response": "__loading__",
        "file_name": None,
        "file_data": None,
        "emails": [],
    })
    st.session_state._pq = None  # 关键：清除标记，防止死循环
    st.session_state.widget_key += 1
    st.rerun()

# 阶段3：处理首个 __loading__ 条目
loading_entry = None
for h in st.session_state.history:
    if h.get("response") == "__loading__":
        loading_entry = h
        break

if loading_entry:
    try:
        query_text = loading_entry["query"]
        fb = st.session_state.get("_pf")
        fn = st.session_state.get("_pfn")

        # 处理上传文件
        if fb is not None:
            file_text = parse_file_content(fb, fn)
            set_uploaded_file(file_text, fn)
            st.session_state.file_loaded = True

        history_for_agent = []
        for h in st.session_state.history:
            if h.get("response") == "__loading__":
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

        entry_emails = []
        try:
            entry_emails = get_emails()
        except Exception:
            pass

        loading_entry["response"] = response
        loading_entry["emails"] = entry_emails
        if fb is not None:
            loading_entry["file_name"] = fn
            loading_entry["file_data"] = fb
            if not any(f["name"] == fn for f in st.session_state.file_vault):
                st.session_state.file_vault.append({
                    "name": fn, "data": fb, "type": "upload",
                })

        set_uploaded_file("", "")
        st.session_state.file_loaded = False
        st.session_state.last_file_key = None
        st.session_state._pf = None
        st.session_state._pfn = None
        st.rerun()

    except Exception:
        loading_entry["response"] = "❌ 系统繁忙，请稍后重试。"
        st.session_state._pf = None
        st.session_state._pfn = None
        st.rerun()

elif submit and not user_query.strip():
    status_placeholder.warning("请输入内容")
