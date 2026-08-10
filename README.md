# 散运助手 — 中远海运散货 AI Agent

基于 **DeepSeek + Streamlit** 构建的航运业务 AI 智能助理，实现完整的 **ReAct（推理-执行-观察-反思）** Agent 闭环。

🌐 **线上 Demo**：[https://cosco-bulk-agent.streamlit.app](https://cosco-bulk-agent.streamlit.app)

## 功能特性

- **ReAct + Reflect 循环引擎**：推理 → 工具调用 → 观察反馈 → 自我审视
- **100+ 散货船期数据库**：7 大区域多货种航线，关键词智能检索
- **文件分析**：上传 PDF / Excel / CSV / TXT，Agent 基于内容回答
- **PDF 文档生成**：船期确认函、航运报告、央企公文、项目方案、通用文档
- **邮件编写**：自动生成邮件，代码块形式一键复制
- **数据质量控制**：上传数据文件的完整性/重复/异常/敏感信息检测
- **会议纪要生成**：央企公文格式会议纪要 PDF
- **localhost 本地网页**：深海风格精美前端，双击启动
- **行业看板**：BDI/BCI/BPI/BSI 四大航运指数折线图

## 项目结构

```
├── app.py                # Streamlit 前端界面
├── agent_core.py         # Agent 核心引擎（ReAct + Reflect 循环）
├── tools.py              # 工具函数定义 + 工具注册表
├── pdf_utils.py          # PDF 文档生成（reportlab 引擎）
├── localhost_server.py   # 本地 Flask API 服务器
├── localhost/            # 精美 HTML 前端 + 一键启动脚本
│   ├── index.html        # 深海风全功能前端
│   └── 启动散运助手.command # 双击启动
├── data/
│   └── shipping_schedules.json  # 100+ 条散货船期数据
├── examples/             # 测试提示词 + 样例文件
│   ├── 测试提示词.md
│   ├── 测试报告.md
│   ├── 提单样例.txt
│   └── 船期数据样例.csv
├── fonts/
│   └── DroidSansFallback.ttf    # 开源 CJK 字体
├── requirements.txt
├── packages.txt
├── setup_mac.sh / setup_windows.bat
└── git_push.sh
```

## Agent 工具能力

| 工具 | 说明 | 侧边栏可见 |
|------|------|:--:|
| 读取文件内容 | 分析已上传文件，支持关键词检索 | ✅ |
| 散货船期查询 | 100+ 航线数据智能检索 | ✅ |
| 编写邮件 | 生成可复制主题和正文 | ✅ |
| 生成 PDF 文件 | 五种文档类型自动匹配 | ✅ |
| 数据质量控制 | 完整性/重复/异常/敏感信息检测 | ✅ |
| 会议纪要生成 | 央企公文格式会议纪要 PDF | ✅ |
| 实时时间查询 | 获取当前北京时间 | ❌ |

> 隐藏工具仅供 Agent 内部调用。

---

## 快速启动

### Streamlit Cloud（线上）

直接访问 **[cosco-bulk-agent.streamlit.app](https://cosco-bulk-agent.streamlit.app)**

### Mac 本地（终端）

```bash
source venv/bin/activate
cp .env.example .env && nano .env   # 填入 DEEPSEEK_API_KEY
streamlit run app.py
```

### Mac 本地网页（双击）

双击 `localhost/启动散运助手.command`，自动启动服务 + 打开浏览器。

### Windows 本地

```cmd
venv\Scripts\activate.bat
copy .env.example .env
notepad .env
streamlit run app.py
```

---

## 使用示例

| 场景 | 输入示例 |
|------|---------|
| 船期查询 | `查一下西澳-青岛的铁矿石船期` |
| 文件分析 | 上传提单 PDF → `这份提单的托运人是谁？` |
| PDF 生成 | `帮我生成西澳-青岛航线的船期确认函` |
| 邮件编写 | `写一封邮件通知客户船期延迟` |
| 项目方案 | `帮我写一份散货船调度平台项目方案` |
| 数据质控 | 上传数据文件 → `检查数据质量` |
| 会议纪要 | `生成启动会会议纪要` |
| 通用文档 | `帮我写一份新员工 Agent 开发手册` |

---

## 技术栈

| 组件 | 技术 |
|------|------|
| 大模型 | DeepSeek (via OpenAI SDK) |
| 前端 | Streamlit / localhost HTML+CSS+JS |
| PDF 生成 | reportlab + DroidSansFallback CJK 字体 |
| 文件解析 | PyPDF2 + openpyxl |
| 数据存储 | JSON 文件 |
| 本地服务 | Flask + Chart.js |
