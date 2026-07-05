# backend/app/api/chat.py
import json
import re
from typing import List
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# 导入我们在上一步编排好的 LangGraph 实例
from app.agent.workflow import graph
from app.core.auth import CurrentUser, get_optional_current_user
from app.tools.knowledge_tools import reset_current_user_role, set_current_user_role

router = APIRouter()


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


def _tool_display_name(tool_name: str) -> str:
    tool_names = {
        "query_campus_knowledge_base": "校园知识库",
        "get_current_time": "时间工具",
        "simple_calculator": "计算器",
    }
    return tool_names.get(tool_name, tool_name)


def _stringify_tool_output(output) -> str:
    if output is None:
        return ""
    content = getattr(output, "content", None)
    if content is not None:
        return str(content)
    return str(output)


def _summarize_text(text: str, limit: int = 96) -> str:
    normalized = re.sub(r"\s+", " ", text).strip()
    if len(normalized) <= limit:
        return normalized
    return f"{normalized[:limit]}..."


def _extract_knowledge_sources(output: str) -> list[dict[str, str]]:
    pattern = re.compile(
        r"\[来源\s+\d+\]:\s+《(?P<title>.*?)》第\s+(?P<page>.*?)\s+页，"
        r"分类:\s+(?P<category>.*?)，权限级别:\s+(?P<access>.*?)\n"
        r"相关内容:\s+(?P<content>.*?)(?=\n---\n|\Z)",
        re.S,
    )
    sources = []
    for match in pattern.finditer(output):
        sources.append(
            {
                "title": match.group("title").strip(),
                "category": match.group("category").strip(),
                "page": match.group("page").strip(),
                "summary": _summarize_text(match.group("content")),
            }
        )
    return sources


# ==========================================
# 1. 定义请求数据模型
# ==========================================
class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]


# ==========================================
# 2. SSE 流式生成器核心逻辑
# ==========================================
async def chat_stream_generator(messages: List[Message], current_user: CurrentUser):
    """
    异步生成器：运行 LangGraph 并捕获流式事件，转化为 SSE 格式
    """
    # 将前端传来的 Pydantic 模型列表转换为 LangChain 认识的字典列表格式
    formatted_messages = [{"role": msg.role, "content": msg.content} for msg in messages]
    formatted_messages.insert(
        0,
        {
            "role": "system",
            "content": (
                f"当前登录用户: {current_user.display_name}。"
                f"当前用户角色: {current_user.role}。"
                "当你调用 query_campus_knowledge_base 时，必须把 role 参数设置为当前用户角色。"
                "不要尝试访问超过该角色权限范围的知识库内容。"
            ),
        },
    )

    # 构造 LangGraph 需要的初始 State (MessagesState)
    initial_state = {"messages": formatted_messages}

    try:
        yield _sse({"type": "trace", "message": "正在理解问题"})

        role_token = set_current_user_role(current_user.role)
        is_answering = False
        # astream_events 是 LangGraph 提供的高级流式 API，version="v2" 是目前的标准推荐
        try:
            async for event in graph.astream_events(initial_state, version="v2"):
                kind = event["event"]

                # --- 核心事件 1：大模型正在输出文本 Token ---
                if kind == "on_chat_model_stream":
                    # 提取模型生成的文本块
                    chunk = event["data"]["chunk"]
                    if chunk.content:
                        if not is_answering:
                            yield _sse({"type": "trace", "message": "正在整理回答"})
                            is_answering = True
                        # 封装成 JSON 字符串，type 标记为 content
                        # 严格按照 SSE 规范格式化： "data: {json}\n\n"
                        yield _sse({"type": "content", "content": chunk.content})

                # --- 核心事件 2：Agent 决定调用工具 (Tool Calling) ---
                elif kind == "on_tool_start":
                    tool_name = event["name"]
                    tool_input = event["data"].get("input", {})
                    display_name = _tool_display_name(tool_name)
                    if tool_name == "query_campus_knowledge_base":
                        yield _sse({"type": "trace", "message": "正在检索校园知识库"})
                    yield _sse({"type": "trace", "message": f"调用工具：{display_name}"})
                    # 告诉前端：Agent 正在使用什么工具，可以用来在 UI 上显示“正在思考/正在调用计算器...”
                    yield _sse({
                        "type": "tool_start",
                        "tool_name": tool_name,
                        "tool_input": tool_input
                    })

                # --- 核心事件 3：工具执行完毕 ---
                elif kind == "on_tool_end":
                    tool_name = event["name"]
                    if tool_name == "query_campus_knowledge_base":
                        output = _stringify_tool_output(event["data"].get("output"))
                        sources = _extract_knowledge_sources(output)
                        yield _sse({"type": "trace", "message": f"找到相关资料：{len(sources)} 条"})
                        if sources:
                            yield _sse({
                                "type": "trace",
                                "message": "回答依据来源",
                                "sources": sources,
                            })
                    # 告诉前端：工具调用完毕
                    yield _sse({"type": "tool_end", "tool_name": tool_name})
        finally:
            reset_current_user_role(role_token)

        # 图流转彻底结束，向前端发送结束标识
        yield "data: [DONE]\n\n"

    except Exception as e:
        # 异常捕获并输出到流中，防止连接死锁
        yield _sse({"type": "error", "content": f"Agent 运行出错: {str(e)}"})
        yield "data: [DONE]\n\n"


# ==========================================
# 3. 注册 FastAPI 路由
# ==========================================
@router.post("/chat")
async def chat_endpoint(
    request: ChatRequest,
    current_user: CurrentUser = Depends(get_optional_current_user),
):
    """
    提供给前端调用的流式对话接口
    """
    # 必须使用 StreamingResponse，并指定 media_type 为 text/event-stream
    return StreamingResponse(
        chat_stream_generator(request.messages, current_user),
        media_type="text/event-stream"
    )
