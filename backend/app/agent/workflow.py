from typing import Literal, Dict, Any

from langchain_openai import ChatOpenAI
# 1. 引入内置的 MessagesState
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import ToolNode

from app.core.config import settings
# 导入我们的基础工具
from app.tools import basic_tools
# 导入校园知识库检索工具
from app.tools.knowledge_tools import query_campus_knowledge_base

# ==========================================
# 1. 状态定义
# ==========================================
# 我们不再需要手动定义 AgentState 及其 Annotated 逻辑。
# 直接使用官方提供的 MessagesState 即可，它已经包含了完美的类型注解。

# ==========================================
# 2. 初始化模型并绑定工具
# ==========================================
llm = ChatOpenAI(
    model=settings.openai_default_model,
    base_url=settings.openai_api_base,
    api_key=settings.openai_api_key,
    temperature=0
)

# 将基础工具和 RAG 工具合并成一个新的工具列表
all_tools = basic_tools + [query_campus_knowledge_base]

# 修改：将合并后的完整工具集绑定给 LLM
llm_with_tools = llm.bind_tools(all_tools)


# ==========================================
# 3. 创建 Nodes (核心执行节点)
# ==========================================
# 修复报错点 2：为函数添加显式的返回值类型注解 -> dict 或 -> Dict[str, Any]
def agent_node(state: MessagesState) -> Dict[str, Any]:
    """
    Agent 节点：负责调用绑定了工具的大模型。
    """
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}

# 修改：ToolNode 也需要接收完整的工具集
tool_node = ToolNode(all_tools)


# ==========================================
# 4. 实现 Agent Router (条件路由)
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
# 修复报错点 1：将 MessagesState 传给 StateGraph
workflow = StateGraph(MessagesState)

# 添加节点
workflow.add_node("agent", agent_node)
workflow.add_node("tools", tool_node)

# 设置边和条件路由
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

# 编译
graph = workflow.compile()
