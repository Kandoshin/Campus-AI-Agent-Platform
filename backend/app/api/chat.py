import os
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

# 检查必要的环境变量，遵循 fail-fast 原则
api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL")
model_name = os.getenv("MODEL_NAME", "deepseek-chat") # 默认回退到 deepseek-chat

if not api_key:
    raise ValueError("环境变量 OPENAI_API_KEY 未设置")

client = AsyncOpenAI(
    api_key=api_key,
    base_url=base_url
)

class ChatRequest(BaseModel):
    message: str

async def generate_chat_stream(message: str):
    """生成流式对话响应"""
    try:
        response = await client.chat.completions.create(
            model=model_name,  # <--- 修改这里，使用环境变量
            messages=[{"role": "user", "content": message}],
            stream=True,
        )
        async for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                yield f"data: {content}\n\n"
        yield "data: [DONE]\n\n"
    except Exception as e:
        yield f"data: Error: {str(e)}\n\n"

@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    return StreamingResponse(
        generate_chat_stream(request.message),
        media_type="text/event-stream"
    )