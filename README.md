# 🚢 远航助手 — 中远海运散货 AI Agent

基于 **DeepSeek + Streamlit** 构建的航运业务 AI 智能助理，实现完整的 **ReAct（推理-执行-观察）** Agent 闭环。

🌐 **线上 Demo**：[https://cosco-bulk-agent.streamlit.app](https://cosco-bulk-agent.streamlit.app)

## ✨ 功能特性

- 🧠 **ReAct 循环引擎**：大模型推理 → 本地工具调用 → 结果观察反馈，完整闭环
- 🔧 **可扩展工具框架**：符合 OpenAI Function Calling 规范，轻松接入新工具
- 📎 **文件分析**：上传 PDF / Excel / CSV / TXT，Agent 基于文件内容智能回答
- 📄 **PDF 文档生成**：自动生成船期确认函、航运报告、央企标准公文（红头格式）
- 🖥️ **跨平台兼容**：macOS (Apple Silicon) / Windows 均可运行
- 🎨 **Agent 应用风格 UI**：查询栏 + 结果面板 + 历史记录，非聊天对话模式

## 📁 项目结构

```
my_agent/
├── app.py                # Streamlit 前端界面（Agent应用风格）
├── agent_core.py         # Agent 核心引擎（ReAct 循环）
├── tools.py              # 工具函数定义 + 工具注册表
├── pdf_utils.py          # PDF 文档生成模块（央企公文模板）
├── requirements.txt      # Python 依赖清单
├── packages.txt          # Streamlit Cloud 系统依赖（CJK 字体）
├── git_push.sh           # 一键提交推送脚本（含自动重试）
├── setup_mac.sh          # 🍎 Mac 一键环境配置脚本
├── setup_windows.bat     # 🪟 Windows 一键环境配置脚本
├── .env.example          # 环境变量模板
├── .gitignore            # Git 忽略规则
└── README.md             # 本文件
```

## 🛠️ Agent 工具能力

| 工具 | 说明 | 前端可见 |
|------|------|---------|
| 🚢 散货船期查询 | 查询指定航线的船期、船名、货种等信息 | ✅ |
| 🔍 文件内容检索 | 在已上传文件中搜索关键词 | ✅ |
| ⏱️ 实时时间查询 | 获取当前北京时间 | ❌ 隐藏 |
| 📄 PDF 文档生成 | 生成船期确认函/航运报告/通用公文 | ❌ 隐藏 |

> 隐藏工具仅供 Agent 内部调用，不显示在侧边栏"服务能力"中。

---

## 🍎 MacBook (Apple Silicon) 快速启动

```bash
cd Agent4cosco/my_agent
chmod +x setup_mac.sh git_push.sh
./setup_mac.sh
```

然后：
```bash
source venv/bin/activate          # ⚠️ 每次新开终端都要执行
cp .env.example .env              # 创建环境变量文件
nano .env                         # 填入 DEEPSEEK_API_KEY
streamlit run app.py              # 启动！
```

---

## 🪟 Windows 快速启动

双击运行 `setup_windows.bat`，或在终端中：
```cmd
cd Agent4cosco\my_agent
setup_windows.bat
```

然后：
```cmd
venv\Scripts\activate.bat         REM ⚠️ 每次新开终端都要执行
copy .env.example .env            REM 创建环境变量文件
notepad .env                      REM 填入 DEEPSEEK_API_KEY
streamlit run app.py              REM 启动！
```

---

## 🔑 获取 API Key

前往 [DeepSeek 开放平台](https://platform.deepseek.com/api_keys) 注册并创建 API Key。

`.env` 文件内容：
```
DEEPSEEK_API_KEY=sk-your-api-key-here
```

---

## 🚀 一键提交推送

```bash
./git_push.sh "你的提交信息"
```

脚本会自动重试 5 次（间隔递增），网络不稳定时无需手动反复执行。如果开了 VPN 仍失败，考虑切换为 SSH：
```bash
git remote set-url origin git@github.com:jiang-yu-24/cosco-shipping-ai-agent.git
```

---

## 💬 使用示例

| 场景 | 输入示例 |
|------|---------|
| 船期查询 | `查一下西澳-青岛的船期` |
| 文件分析 | 上传提单 PDF → `这份提单的托运人是谁？` |
| PDF 生成 | `帮我生成一份西澳-青岛航线的船期确认函` |
| 报告生成 | `整理一份本周航运动态报告` |

---

## 🏗️ 技术架构

```
┌─────────────────────────────────────────────────┐
│              Streamlit 前端 (app.py)              │
│          Agent应用风格：查询栏 + 结果面板          │
└─────────────────────┬───────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│          Agent 核心引擎 (agent_core.py)            │
│                                                   │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│   │ Reason   │───▶│   Act    │───▶│ Observe  │  │
│   │(DeepSeek)│    │(tools.py)│    │ (反馈)    │  │
│   └──────────┘    └──────────┘    └──────────┘  │
│         ▲                              │          │
│         └────────  ReAct 循环 ◀────────┘          │
└─────────────────────────────────────────────────┘
```

---

## 📦 Streamlit Cloud 部署

已部署至：**[cosco-bulk-agent.streamlit.app](https://cosco-bulk-agent.streamlit.app)**

如需重新部署：
1. Push 到 GitHub → Streamlit Cloud 自动检测更新并重新部署
2. 或访问 [share.streamlit.io](https://share.streamlit.io) 手动 "Rerun"

**Cloud Secrets 配置：**
```
DEEPSEEK_API_KEY = "sk-你的密钥"
```

**注意：** 项目包含 `packages.txt`（安装 CJK 字体），首次部署或清除缓存后需等待字体安装完成（约多 1 分钟）。

---

## 🔧 扩展指南

### 添加新工具（前端可见）

1. 在 `tools.py` 中编写工具函数
2. 添加到 `TOOL_DESCRIPTIONS`、`TOOL_MAPPING`、`TOOL_DISPLAY_NAMES`
3. Agent 自动发现并使用

### 添加隐藏工具（仅 Agent 可用）

同上，但不添加到 `TOOL_DISPLAY_NAMES` 即可，侧边栏不显示。

### PDF 文档模板

在 `pdf_utils.py` 中添加新模板函数，然后在 `tools.py` 的 `generate_document` 中增加 `doc_type` 分支。

---

## 📋 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| 大模型 | DeepSeek (via OpenAI SDK) | `base_url=https://api.deepseek.com` |
| 前端 | Streamlit | Agent 应用风格 UI |
| PDF 生成 | fpdf2 | 央企公文红头格式 |
| 文件解析 | PyPDF2 + openpyxl | PDF / Excel / CSV / TXT |
| 环境管理 | python-dotenv | `.env` + Streamlit Secrets |

---

## 📄 License

MIT
