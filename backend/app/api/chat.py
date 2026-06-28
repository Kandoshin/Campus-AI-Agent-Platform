# backend/app/api/chat.py
import json
from typing import List
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# 导入我们在上一步编排好的 LangGraph 实例
from app.agent.workflow import graph

router = APIRouter()


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
async def chat_stream_generator(messages: List[Message]):
    """
    异步生成器：运行 LangGraph 并捕获流式事件，转化为 SSE 格式
    """
    # 将前端传来的 Pydantic 模型列表转换为 LangChain 认识的字典列表格式
    formatted_messages = [{"role": msg.role, "content": msg.content} for msg in messages]

    # 构造 LangGraph 需要的初始 State (MessagesState)
    initial_state = {"messages": formatted_messages}

    try:
        # astream_events 是 LangGraph 提供的高级流式 API，version="v2" 是目前的标准推荐
        async for event in graph.astream_events(initial_state, version="v2"):
            kind = event["event"]

            # --- 核心事件 1：大模型正在输出文本 Token ---
            if kind == "on_chat_model_stream":
                # 提取模型生成的文本块
                chunk = event["data"]["chunk"]
                if chunk.content:
                    # 封装成 JSON 字符串，type 标记为 content
                    data = json.dumps({"type": "content", "content": chunk.content}, ensure_ascii=False)
                    # 严格按照 SSE 规范格式化： "data: {json}\n\n"
                    yield f"data: {data}\n\n"

            # --- 核心事件 2：Agent 决定调用工具 (Tool Calling) ---
            elif kind == "on_tool_start":
                tool_name = event["name"]
                tool_input = event["data"].get("input", {})
                # 告诉前端：Agent 正在使用什么工具，可以用来在 UI 上显示“正在思考/正在调用计算器...”
                data = json.dumps({
                    "type": "tool_start",
                    "tool_name": tool_name,
                    "tool_input": tool_input
                }, ensure_ascii=False)
                yield f"data: {data}\n\n"

            # --- 核心事件 3：工具执行完毕 ---
            elif kind == "on_tool_end":
                tool_name = event["name"]
                # 告诉前端：工具调用完毕
                data = json.dumps({"type": "tool_end", "tool_name": tool_name}, ensure_ascii=False)
                yield f"data: {data}\n\n"

        # 图流转彻底结束，向前端发送结束标识
        yield "data: [DONE]\n\n"

    except Exception as e:
        # 异常捕获并输出到流中，防止连接死锁
        error_data = json.dumps({"type": "error", "content": f"Agent 运行出错: {str(e)}"}, ensure_ascii=False)
        yield f"data: {error_data}\n\n"
        yield "data: [DONE]\n\n"


# ==========================================
# 3. 注册 FastAPI 路由
# ==========================================
@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    提供给前端调用的流式对话接口
    """
    # 必须使用 StreamingResponse，并指定 media_type 为 text/event-stream
    return StreamingResponse(
        chat_stream_generator(request.messages),
        media_type="text/event-stream"
    )