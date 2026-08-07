# 远航助手 — 中远海运散货 AI Agent

基于 **DeepSeek + Streamlit** 构建的航运业务 AI 智能助理，实现完整的 **ReAct（推理-执行-观察-反思）** Agent 闭环。

🌐 **线上 Demo**：[https://cosco-bulk-agent.streamlit.app](https://cosco-bulk-agent.streamlit.app)

## 功能特性

- **ReAct + Reflect 循环引擎**：推理 → 工具调用 → 观察反馈 → 自我审视，每轮工具执行后强制反思
- **DeepSeek 风格对话流**：全部历史 Q&A 在主区域按序展示，侧边栏服务能力 + 文件暂存
- **100+ 散货船期数据库**：覆盖 7 大区域、多种货种的航线数据，支持关键词智能检索
- **文件分析**：上传 PDF / Excel / CSV / TXT，Agent 基于文件内容智能回答
- **PDF 文档生成**：船期确认函、航运报告、央企公文、通用格式四种模板
- **邮件编写**：自动生成邮件主题和正文，一键复制
- **跨平台**：macOS (Apple Silicon) / Windows 均可运行

## 项目结构

```
my_agent/
├── app.py                # Streamlit 前端界面
├── agent_core.py         # Agent 核心引擎（ReAct + Reflect 循环）
├── tools.py              # 工具函数定义 + 工具注册表
├── pdf_utils.py          # PDF 文档生成（reportlab 引擎）
├── data/
│   └── shipping_schedules.json  # 100+ 条散货船期数据
├── fonts/
│   └── DroidSansFallback.ttf    # 开源 CJK 字体
├── requirements.txt      # Python 依赖清单
├── packages.txt          # Streamlit Cloud 系统依赖
├── git_push.sh           # 一键提交推送脚本（自动重试）
├── setup_mac.sh          # Mac 一键环境配置脚本
├── setup_windows.bat     # Windows 一键环境配置脚本
├── .env.example          # 环境变量模板
└── .gitignore            # Git 忽略规则
```

## Agent 工具能力

| 工具 | 说明 | 侧边栏可见 |
|------|------|-----------|
| 读取文件内容 | 分析已上传文件，支持关键词检索 | ✅ |
| 生成 PDF 文件 | 船期确认函/报告/公文/通用格式 | ✅ |
| 编写邮件 | 生成可复制主题和正文 | ✅ |
| 散货船期查询 | 100+ 条航线数据智能检索 | ❌ 隐藏 |
| 实时时间查询 | 获取当前北京时间 | ❌ 隐藏 |

> 隐藏工具仅供 Agent 内部调用，不显示在侧边栏。

---

## Mac 快速启动

```bash
cd Agent4cosco/my_agent
chmod +x setup_mac.sh git_push.sh
./setup_mac.sh
```

然后：
```bash
source venv/bin/activate          # 每次新开终端都要执行
cp .env.example .env              # 创建环境变量文件
nano .env                         # 填入 DEEPSEEK_API_KEY
streamlit run app.py              # 启动
```

---

## Windows 快速启动

```cmd
cd Agent4cosco\my_agent
setup_windows.bat
```

然后：
```cmd
venv\Scripts\activate.bat
copy .env.example .env
notepad .env
streamlit run app.py
```

---

## 获取 API Key

前往 [DeepSeek 开放平台](https://platform.deepseek.com/api_keys) 注册并创建 API Key。

`.env` 文件内容：
```
DEEPSEEK_API_KEY=sk-your-api-key-here
```

---

## 一键提交推送

```bash
./git_push.sh "你的提交信息"
```

脚本自动重试 5 次（间隔递增），网络不稳定时无需手动反复执行。

---

## 使用示例

| 场景 | 输入示例 |
|------|---------|
| 船期查询 | `查一下西澳-青岛的铁矿石船期` |
| 文件分析 | 上传提单 PDF → `这份提单的托运人是谁？` |
| PDF 生成 | `帮我生成一份西澳-青岛航线的船期确认函` |
| 邮件编写 | `写一封邮件通知客户船期延迟` |
| 通用文档 | `帮我写一份新员工 Agent 开发手册` |

---

## 技术架构

```
┌─────────────────────────────────────────────────┐
│              Streamlit 前端 (app.py)              │
│        DeepSeek 风格对话流 + 侧边栏管理           │
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
│         │    ┌──────────┐              │          │
│         └────│ Reflect  │◀─────────────┘          │
│              │ (自我审视) │                        │
│              └──────────┘                        │
└─────────────────────────────────────────────────┘
```

## Streamlit Cloud 部署

已部署至：**[cosco-bulk-agent.streamlit.app](https://cosco-bulk-agent.streamlit.app)**

Push 到 GitHub 后 Cloud 自动检测更新并重新部署。

**Cloud Secrets 配置：**
```
DEEPSEEK_API_KEY = "sk-你的密钥"
```

---

## 扩展指南

### 添加新工具

1. 在 `tools.py` 中编写工具函数
2. 添加到 `TOOL_DESCRIPTIONS`、`TOOL_MAPPING`
3. 侧边栏可见则加到 `TOOL_DISPLAY_NAMES`，否则仅 Agent 内部可用

### 添加船期数据

编辑 `data/shipping_schedules.json`，按现有格式新增条目，Agent 自动纳入检索范围。

### PDF 文档模板

在 `pdf_utils.py` 中添加新模板函数，然后在 `tools.py` 的 `generate_document` 中增加 `doc_type` 分支。

---

## 技术栈

| 组件 | 技术 |
|------|------|
| 大模型 | DeepSeek (via OpenAI SDK) |
| 前端 | Streamlit |
| PDF 生成 | reportlab + DroidSansFallback CJK 字体 |
| 文件解析 | PyPDF2 + openpyxl |
| 数据存储 | JSON 文件 (100+ 船期记录) |
| 环境管理 | python-dotenv + Streamlit Secrets |
