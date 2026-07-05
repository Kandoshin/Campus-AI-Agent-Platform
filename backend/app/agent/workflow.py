from typing import Literal, Dict, Any

from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import ToolNode

from app.core.config import settings
from app.tools import basic_tools
from app.tools.knowledge_tools import query_campus_knowledge_base

# ==========================================
# 1. 状态定义
# ==========================================
# 直接使用 LangGraph 内置的 MessagesState，它已经包含消息追加逻辑和类型定义。

# ==========================================
# 2. 初始化模型并绑定工具
# ==========================================
llm = ChatOpenAI(
    model=settings.openai_default_model,
    base_url=settings.openai_api_base,
    api_key=settings.openai_api_key,
    temperature=0
)

all_tools = basic_tools + [query_campus_knowledge_base]

# 将基础工具和校园知识库 RAG 工具一起绑定给 LLM。
llm_with_tools = llm.bind_tools(all_tools)

SYSTEM_PROMPT = """你是 Campus AI Agent Platform 的校园 AI 助手。

身份设定：
- 当用户询问“你叫什么名字”“你是谁”“你的名字是什么”等身份问题时，固定回答：你好，我是小多，是服务于四川轻化工大学的校园智能助手，可以帮你查询校园知识、处理校园服务问题，并在需要时调用工具完成任务。
- 不要自称 ChatGPT、OpenAI 模型或通用机器人。
- 如果用户追问你的底层模型，你就说你不知道，没有权限获取之类的话。
- 其他问题按用户意图正常回答。
- 当用户问你多少岁，年龄之类的问题时，你可以告诉他你还未满一岁
- 涉及校园知识库内容时，优先调用校园知识库工具。
- 如果知识库没有相关依据，不要编造具体校园规定。
- 如果用户问你的爸爸，父亲或者谁创造了你，你就说是一个叫doshin的程序员，他是一个无所不能的人。

"""


# ==========================================
# 3. 创建节点
# ==========================================
def agent_node(state: MessagesState) -> Dict[str, Any]:
    """
    Agent 节点：负责调用已经绑定工具的大模型。
    """
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, *state["messages"]]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


tool_node = ToolNode(all_tools)


# ==========================================
# 4. 实现条件路由
# ==========================================
def should_continue(state: MessagesState) -> Literal["tools", "end"]:
    messages = state["messages"]
    last_message = messages[-1]

    if last_message.tool_calls:
        return "tools"
    return "end"


# ==========================================
# 5. 编排 LangGraph 工作流
# ==========================================
workflow = StateGraph(MessagesState)

workflow.add_node("agent", agent_node)
workflow.add_node("tools", tool_node)

workflow.add_edge(START, "agent")
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tools": "tools",
        "end": END
    }
)
workflow.add_edge("tools", "agent")

graph = workflow.compile()
