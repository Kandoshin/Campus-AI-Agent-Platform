from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.chat import router as chat_router
from app.api.knowledge import router as knowledge_router
from app.core.config import settings

app = FastAPI(title=settings.app_name, version=settings.app_version)

# 配置 CORS 允许前端跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # 开发环境下限制为前端开发服务器地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/api")

app.include_router(knowledge_router, prefix="/api/knowledge", tags=["Campus Knowledge Base"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
