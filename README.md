# 🚢 远航助手 — 中远海运散货 AI Agent

基于 **DeepSeek + Streamlit** 构建的航运业务 AI 智能助理，实现完整的 **ReAct（推理-执行-观察）** Agent 闭环。

## ✨ 功能特性

- 🧠 **ReAct 循环引擎**：大模型推理 → 本地工具调用 → 结果观察反馈，完整闭环
- 🔧 **可扩展工具框架**：符合 OpenAI Function Calling 规范，轻松接入新工具
- 💬 **多轮对话**：基于 Streamlit 的聊天界面，支持历史上下文记忆
- 🖥️ **跨平台兼容**：macOS (Apple Silicon) / Windows 均可运行

## 📁 项目结构

```
my_agent/
├── app.py                # Streamlit 前端界面
├── agent_core.py         # Agent 核心引擎（ReAct 循环）
├── tools.py              # 工具函数定义（业务逻辑占位）
├── requirements.txt      # Python 依赖清单
├── setup_mac.sh          # 🍎 Mac 一键环境配置脚本
├── setup_windows.bat     # 🪟 Windows 一键环境配置脚本
├── .env.example          # 环境变量模板
├── .gitignore            # Git 忽略规则
└── README.md             # 本文件
```

---

## 🍎 MacBook (Apple Silicon) 快速启动

```bash
cd Agent4cosco/my_agent
chmod +x setup_mac.sh
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

## 💬 使用示例

| 示例问题 | 调用的工具 |
|---------|-----------|
| `现在几点了？` | `get_current_time` |
| `查一下西澳-青岛的船期` | `query_shipping_schedule` |
| `巴西到天津的船什么时候到？` | `query_shipping_schedule` |
| `印尼-湛江航线是哪条船？` | `query_shipping_schedule` |

---

## 🏗️ 技术架构

```
┌─────────────────────────────────────────────────┐
│                   Streamlit 前端                  │
│              (app.py — 聊天界面)                   │
└─────────────────────┬───────────────────────────┘
                      │ 用户输入
                      ▼
┌─────────────────────────────────────────────────┐
│            Agent 核心引擎 (agent_core.py)          │
│                                                   │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│   │ Reason   │───▶│   Act    │───▶│ Observe  │  │
│   │ (DeepSeek)│    │(tools.py)│    │ (反馈)    │  │
│   └──────────┘    └──────────┘    └──────────┘  │
│         ▲                              │          │
│         └────────  ReAct 循环 ◀────────┘          │
└─────────────────────────────────────────────────┘
```

---

## 📦 提交清单

演示提交前逐项检查：

- [ ] `.env` 文件已加入 `.gitignore`（API Key 绝对不能泄露）
- [ ] `requirements.txt` 依赖完整可复现
- [ ] 代码在 macOS 和 Windows 上均可 `pip install -r requirements.txt` 后直接运行
- [ ] README 中包含清晰的启动步骤
- [ ] 准备至少 3 个可演示的业务场景（对应不同的工具调用）
- [ ] （加分项）部署到 Streamlit Cloud，提供线上 Demo 链接

### Streamlit Cloud 部署（2 分钟搞定）

1. 把项目 push 到 GitHub **公开仓库**
2. 打开 [share.streamlit.io](https://share.streamlit.io)，用 GitHub 登录
3. 点 "New app" → 选择仓库 → 主文件路径填 `my_agent/app.py`
4. 在 Advanced Settings 中添加 Secret：`DEEPSEEK_API_KEY = sk-xxx`
5. 点 Deploy，2 分钟后得到 `https://xxx.streamlit.app` 链接

> 💡 线上链接让评委**即点即用**，省去本地环境配置环节，体验完全不同。

---

## 🔧 扩展指南

### 添加新工具

1. 在 `tools.py` 中编写工具函数
2. 在 `TOOL_DESCRIPTIONS` 列表中添加函数定义（OpenAI Function Calling 格式）
3. 在 `TOOL_MAPPING` 字典中注册函数映射

Agent 会自动发现并使用新工具，无需修改 `agent_core.py`。

### 替换为真实业务接口

`tools.py` 顶部已标注为"业务逻辑占位"。实际项目中，将工具函数体替换为：
- 企业数据中台 API 调用
- 合同/提单 OCR 解析
- AIS 船舶轨迹查询
- 散货运价指数接口
- 内部 RAG 知识库检索

---

## 📋 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| 大模型 | DeepSeek (via OpenAI SDK) | `base_url=https://api.deepseek.com` |
| 前端 | Streamlit | 纯 Python，无需前端代码 |
| 环境管理 | python-dotenv | `.env` 文件管理敏感配置 |
| 平台 | macOS / Windows | Apple Silicon & x86 均可 |

---

## 📄 License

MIT
