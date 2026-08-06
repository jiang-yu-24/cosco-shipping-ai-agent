"""
Agent 核心引擎模块 — ReAct（推理-执行-观察）循环
================================================
本模块实现了 AI Agent 的核心决策闭环：

    ┌──────────┐     ┌──────────┐     ┌──────────┐
    │  Reason  │ ──▶ │   Act    │ ──▶ │ Observe  │
    │ (大模型)  │     │ (工具调用) │     │ (结果反馈) │
    └──────────┘     └──────────┘     └──────────┘
          ▲                                  │
          └──────────── 循环 ◀───────────────┘

工作流程：
  1. 用户输入问题
  2. Agent 将问题 + 工具列表发送给 DeepSeek 大模型（Reasoning）
  3. 大模型决定是否需要调用工具：
     - 需要 → 执行本地工具函数（Acting）→ 将结果反馈给大模型（Observation）→ 回到步骤2
     - 不需要 → 直接返回大模型的文本回答
  4. 最终将结果返回给用户

这种模式被称为 ReAct（Reasoning + Acting），是当前 AI Agent 架构的主流范式。
"""

import json
import os
from typing import Any, Dict, List, Optional

from openai import OpenAI
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

# 导入本项目的工具定义
from tools import TOOL_DESCRIPTIONS, TOOL_MAPPING

# ============================================================
# DeepSeek 客户端初始化
# ============================================================
# DeepSeek 兼容 OpenAI SDK，只需将 base_url 指向 DeepSeek API 地址即可
# API Key 从环境变量 DEEPSEEK_API_KEY 读取（请先在 .env 文件中配置）
_deepseek_client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)

# 使用的模型名称 — DeepSeek-V3 兼顾推理能力与响应速度
_MODEL_NAME = "deepseek-chat"

# 安全限制：Agent 最多连续调用工具的次数，防止无限循环或 Token 爆炸
_MAX_TOOL_CALL_ROUNDS = 5


# ============================================================
# 核心函数：run_agent
# ============================================================

def run_agent(user_query: str, chat_history: Optional[List[Dict[str, Any]]] = None) -> str:
    """
    Agent 主入口函数 — 驱动完整的 ReAct 循环。

    参数:
        user_query: str  - 用户输入的自然语言问题
        chat_history: list - 可选，历史对话消息列表（OpenAI messages 格式）

    返回:
        str - Agent 的最终回答文本
    """
    # ---------- 构建初始消息列表 ----------
    # 消息列表（messages）是 OpenAI Chat Completions API 的核心数据结构
    # 它承载了对话的全部上下文：系统指令、历史对话、工具调用与结果

    # 系统提示词（System Prompt）：定义 Agent 的角色、能力和行为边界
    system_prompt = {
        "role": "system",
        "content": (
            "你是「远航助手」，央国企数字化项目 AI 助理。"
            ""
            "PDF 类型：schedule=船期确认 report=报告 official=公文 generic=通用 proposal=项目方案。"
            "关键：用户提 PDF 关键词立刻调用 generate_document。需多份时依次多次调用，不可省略。"
            ""
            "proposal 规则（严格）："
            "- route 参数填项目名称，consignor 填申报单位（必须是企业/部门名，不能是人名）"
            "- content 必须按以下十章结构，不得省略、不得合并："
            "  一、项目概述（项目名称、申报单位、负责人、类型、周期、投资）"
            "  二、项目背景与必要性（政策依据、业务现状、必要性）"
            "  三、建设目标（总体目标、阶段目标、量化指标）"
            "  四、建设内容与方案（功能模块、业务流程、数据规划、基础设施）"
            "  五、技术方案（技术路线、系统架构、关键技术、安全方案、国产化）"
            "  六、实施计划（策略、进度、里程碑、人员组织）"
            "  七、投资估算（软件/硬件/实施/运维费用，表格呈现）"
            "  八、效益分析（经济/管理/社会效益、回收期）"
            "  九、风险分析与应对（风险类别|描述|影响|概率|措施 表格）"
            "  十、组织保障（领导小组、项目团队、沟通机制、质量保障）"
            "- 如果用户未提供足够信息（如申报单位、项目名称、投资估算等），填入「（待定）」或「（待补充）」，"
            "禁止编造虚假数据。生成 PDF 后必须明确提醒用户哪些字段需要手动补充。"
            "- 有上传文件时先 search_file_content 提取信息，再 generate_document"
            "所有回复用中文。"
        ),
    }

    # 组装 messages：系统指令 + 历史对话 + 当前用户问题
    messages = [system_prompt]
    if chat_history:
        messages.extend(chat_history)
    messages.append({"role": "user", "content": user_query})

    # ---------- ReAct 主循环 ----------
    # 记录当前已完成的工具调用轮数，用于安全保护
    tool_round = 0

    while tool_round < _MAX_TOOL_CALL_ROUNDS:
        # --------------------------------------------------------
        # 第1步：REASON（推理）—— Agent 的"大脑"决策点
        # --------------------------------------------------------
        # 将完整的 messages（包含历史对话、之前的工具调用和观察结果）
        # 发送给 DeepSeek 大模型。大模型会分析当前上下文，决定下一步：
        #   A. 调用某个工具 → 返回 tool_calls
        #   B. 直接生成文本回复 → 返回 content
        #
        # 这里不做任何预处理或规则判断——全部决策权交给大模型。
        # 这就是"大脑"的价值：理解上下文、判断是否需要外部信息、选择正确的工具。
        # --------------------------------------------------------
        try:
            response = _deepseek_client.chat.completions.create(
                model=_MODEL_NAME,
                messages=messages,
                tools=TOOL_DESCRIPTIONS,   # 将工具定义传给模型，模型据此判断是否调用工具
                temperature=0.3,           # 较低温度保证决策稳定性
            )
        except Exception as e:
            # 网络异常、API Key无效、额度不足等场景
            return f"❌ 服务暂时不可用，请稍后重试。"

        # 提取模型返回的 assistant 消息
        assistant_msg = response.choices[0].message

        # --------------------------------------------------------
        # 第2步：判断是否需要执行 ACT（执行）
        # --------------------------------------------------------
        # 检查模型中是否返回了 tool_calls。
        # tool_calls 是一个列表，每个元素包含：
        #   - id: 工具调用唯一标识（需要原样返回给模型）
        #   - function.name: 要调用的函数名
        #   - function.arguments: JSON 字符串形式的参数
        #
        # 如果 tool_calls 为空 → 模型已经生成了最终回答，循环结束。
        # --------------------------------------------------------
        if assistant_msg.tool_calls is None:
            # 模型没有请求工具调用，直接返回文本回答
            # 这是 ReAct 循环的"出口"——模型认为已有足够信息回答用户
            return assistant_msg.content or "（模型未返回有效内容，请重试）"

        # ---------- 有工具调用请求：进入 ACT + OBSERVE 阶段 ----------
        tool_round += 1

        # 将 assistant 消息加入 messages（含 tool_calls 定义）
        messages.append({
            "role": "assistant",
            "content": assistant_msg.content,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in assistant_msg.tool_calls
            ],
        })

        # 遍历本次请求中的所有工具调用（模型可能一次请求多个工具）
        for tool_call in assistant_msg.tool_calls:
            tool_name = tool_call.function.name
            tool_call_id = tool_call.id  # 必须原样返回给模型用于关联

            # 安全解析参数
            try:
                tool_args = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                tool_args = {}

            # --------------------------------------------------------
            # 第3步：ACT（执行）—— Agent 的"手脚"执行点
            # --------------------------------------------------------
            # 这是 Agent 从"思考"转向"行动"的关键环节。
            # Agent 通过 TOOL_MAPPING 字典找到对应的 Python 函数，
            # 并在本地执行它。这就好比 Agent 的"手"和"脚"——
            # 大模型（大脑）决定做什么，本地函数（手脚）实际去完成。
            #
            # 在真实业务场景中，这里的函数可能去调用：
            #   - 企业内部的 ERP/SAP 接口
            #   - 港口 AIS 船舶轨迹 API
            #   - 散货指数/运价数据库
            #   - 合同 OCR 解析微服务
            # --------------------------------------------------------
            print(f"[Agent Action] 调用工具: {tool_name}, 参数: {tool_args}")

            if tool_name in TOOL_MAPPING:
                try:
                    # 执行本地工具函数
                    tool_func = TOOL_MAPPING[tool_name]
                    if tool_args:
                        tool_result = tool_func(**tool_args)
                    else:
                        tool_result = tool_func()
                except Exception as e:
                    tool_result = f"工具执行出错：{str(e)}"
                    print(f"[Agent Error] 工具 {tool_name} 执行失败: {e}")
            else:
                tool_result = f"未知工具: {tool_name}，请检查 TOOL_MAPPING 注册表。"
                print(f"[Agent Warning] 模型请求了未注册的工具: {tool_name}")

            print(f"[Agent Observe] 工具返回: {tool_result[:200]}...")

            # --------------------------------------------------------
            # 第4步：OBSERVE（观察）—— Agent 的"反馈闭环"
            # --------------------------------------------------------
            # 工具执行结果以 "tool" 角色消息追加回 messages 列表。
            # 这是 ReAct 循环最关键的一环——"闭环反馈"：
            #
            #   大模型看到自己的 tool_call → 看到 tool 返回的结果 →
            #   基于结果继续推理 → 决定是再调工具还是给出最终回答。
            #
            # 没有这一步，模型就"失忆"了——它不知道工具执行了什么，
            # 也就无法基于真实数据生成准确回答。在商业场景中，这个闭环
            # 确保了 AI 的回答始终基于"最新鲜"的真实数据，而非幻觉。
            #
            # 注意：tool_call_id 必须和 assistant 消息中的 id 一致，
            # 这是 OpenAI API 协议要求的关联机制。
            # --------------------------------------------------------
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call_id,
                "content": str(tool_result),
            })

        # --------------------------------------------------------
        # 第5步：REFLECT（反思）—— Agent 的"自我审视"环节
        # --------------------------------------------------------
        # 工具执行完毕后，显式要求模型进行结构化自我审视：
        #   1. 工具返回的结果是否符合预期？
        #   2. 是否需要调整参数重试？
        #   3. 当前信息是否足够回答用户的原始问题？
        #
        # 这一步将"隐式反思"变为"显式反思"，显著提高回答准确性。
        # 模型在反思过程中如果发现信息不足，会继续调用工具；
        # 如果认为足够了，则给出最终回答。
        # --------------------------------------------------------
        messages.append({
            "role": "user",
            "content": "工具结果如上。如信息不足请继续调工具，否则直接回答。",
        })

        # 本轮所有工具调用处理完毕，回到 while 循环顶部
        # 模型将重新收到 tool 结果 + 反思提示，
        # 在反思中决定继续调工具还是给出最终回答

    # ---------- 达到最大轮数的兜底处理 ----------
    # 如果工具调用轮数用尽但模型仍请求工具，
    # 强行要求模型基于现有信息给出回答
    messages.append({
        "role": "user",
        "content": (
            "你已经调用了多次工具，请基于目前已获取的所有信息，"
            "直接给出最终回答，不要再请求新的工具调用。"
        ),
    })

    try:
        final_response = _deepseek_client.chat.completions.create(
            model=_MODEL_NAME,
            messages=messages,
            temperature=0.3,
        )
        return final_response.choices[0].message.content or "（无法生成有效回答，请重试）"
    except Exception as e:
        return f"❌ Agent 兜底调用失败：{str(e)}"
