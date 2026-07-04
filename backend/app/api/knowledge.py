import shutil
from pathlib import Path
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from app.services.knowledge_service import KnowledgeService

router = APIRouter()
knowledge_service = KnowledgeService()

# 确保临时上传目录存在
UPLOAD_DIR = Path("temp_uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
    category: str = Form(default="general"),
    access_level: Literal["public", "student", "admin"] = Form(default="public"),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="未提供文件名")

    original_name = Path(file.filename).name
    suffix = Path(original_name).suffix.lower()
    if suffix not in {".pdf", ".docx", ".md", ".txt"}:
        raise HTTPException(status_code=400, detail=f"暂不支持的文件格式: {suffix}")

    file_path = UPLOAD_DIR / f"{uuid4().hex}{suffix}"

    # 1. 将接收到的文件流保存到本地
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")

    # 2. 调用服务进行解析、切分和向量化存储
    try:
        chunks_count = knowledge_service.process_and_store(
            str(file_path),
            title=title or Path(original_name).stem,
            category=category,
            access_level=access_level,
        )
    except Exception as e:
        # 发生错误时清理遗留文件
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"知识库处理失败: {str(e)}")

    # 3. 处理完毕后删除本地临时文件释放空间
    file_path.unlink(missing_ok=True)

    return {
        "status": "success",
        "message": f"文件 '{original_name}' 处理完成",
        "chunks_generated": chunks_count,
        "title": title or Path(original_name).stem,
        "category": category,
        "access_level": access_level,
    }
