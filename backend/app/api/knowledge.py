import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser, require_admin
from app.core.config import settings
from app.db.session import SessionLocal, get_db
from app.models.knowledge_document import KnowledgeDocument
from app.schemas.knowledge import DeleteDocumentResponse, KnowledgeDocumentPublic
from app.services.knowledge_service import KnowledgeService

router = APIRouter()
knowledge_service = KnowledgeService()

BACKEND_DIR = Path(__file__).resolve().parents[2]
SUPPORTED_FILE_TYPES = {".pdf", ".docx", ".md", ".txt"}


def _raw_storage_root() -> Path:
    configured_path = Path(settings.knowledge_raw_storage_dir)
    if configured_path.is_absolute():
        return configured_path
    return BACKEND_DIR / configured_path


RAW_STORAGE_ROOT = _raw_storage_root()
RAW_STORAGE_ROOT.mkdir(parents=True, exist_ok=True)


def _relative_storage_path(file_path: Path) -> str:
    try:
        return file_path.relative_to(BACKEND_DIR).as_posix()
    except ValueError:
        return file_path.as_posix()


def _resolve_storage_path(storage_path: str) -> Path:
    file_path = Path(storage_path)
    if not file_path.is_absolute():
        file_path = BACKEND_DIR / file_path
    return file_path


def _ensure_inside_raw_storage(path: Path) -> None:
    root = RAW_STORAGE_ROOT.resolve()
    target = path.resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise RuntimeError("文档存储路径不在知识库原始文件目录内") from exc


def _delete_source_file(document: KnowledgeDocument) -> None:
    file_path = _resolve_storage_path(document.storage_path)
    _ensure_inside_raw_storage(file_path)

    document_dir = file_path.parent.resolve()
    _ensure_inside_raw_storage(document_dir)
    if document_dir == RAW_STORAGE_ROOT.resolve():
        raise RuntimeError("拒绝删除知识库根存储目录")

    shutil.rmtree(document_dir, ignore_errors=True)


def _process_document_task(document_id: str) -> None:
    with SessionLocal() as db:
        document = db.get(KnowledgeDocument, document_id)
        if document is None or document.status == "deleted":
            return

        document.status = "processing"
        document.error_message = None
        db.commit()

        try:
            file_path = _resolve_storage_path(document.storage_path)
            _ensure_inside_raw_storage(file_path)

            chunk_count = knowledge_service.process_and_store(
                str(file_path),
                document_id=document.id,
                original_filename=document.original_filename,
                title=document.title,
                category=document.category,
                access_level=document.access_level,
            )

            db.refresh(document)
            if document.status == "deleted":
                knowledge_service.delete_document_chunks(document.id)
                _delete_source_file(document)
                document.chunk_count = 0
                document.error_message = None
                db.commit()
                return

            document.status = "completed"
            document.chunk_count = chunk_count
            document.error_message = None
            document.completed_at = datetime.now(timezone.utc)
            db.commit()
        except Exception as exc:
            db.rollback()
            document = db.get(KnowledgeDocument, document_id)
            if document is not None and document.status != "deleted":
                document.status = "failed"
                document.error_message = str(exc)[:2000]
                db.commit()


@router.post(
    "/upload",
    response_model=KnowledgeDocumentPublic,
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
    category: str = Form(default="general"),
    access_level: Literal["public", "student", "admin"] = Form(default="public"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="未提供文件名")

    original_name = Path(file.filename).name
    suffix = Path(original_name).suffix.lower()
    if suffix not in SUPPORTED_FILE_TYPES:
        raise HTTPException(status_code=400, detail=f"暂不支持的文件格式: {suffix}")

    document_id = uuid4().hex
    document_dir = RAW_STORAGE_ROOT / document_id
    document_dir.mkdir(parents=True, exist_ok=True)
    file_path = document_dir / original_name

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as exc:
        shutil.rmtree(document_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"文件保存失败: {str(exc)}") from exc

    document = KnowledgeDocument(
        id=document_id,
        title=title.strip() if title and title.strip() else Path(original_name).stem,
        original_filename=original_name,
        file_ext=suffix,
        file_size=file_path.stat().st_size,
        content_type=file.content_type,
        category=category.strip() if category.strip() else "general",
        access_level=access_level,
        storage_path=_relative_storage_path(file_path),
        status="pending",
        chunk_count=0,
        uploaded_by_id=current_user.id,
        uploaded_by_username=current_user.username,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    background_tasks.add_task(_process_document_task, document.id)
    return document


@router.get("/documents", response_model=list[KnowledgeDocumentPublic])
def list_documents(
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_admin),
):
    statement = (
        select(KnowledgeDocument)
        .where(KnowledgeDocument.status != "deleted")
        .order_by(KnowledgeDocument.created_at.desc())
    )
    return list(db.scalars(statement).all())


@router.get("/documents/{document_id}", response_model=KnowledgeDocumentPublic)
def get_document(
    document_id: str,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_admin),
):
    document = db.get(KnowledgeDocument, document_id)
    if document is None or document.status == "deleted":
        raise HTTPException(status_code=404, detail="文档不存在")
    return document


@router.delete("/documents/{document_id}", response_model=DeleteDocumentResponse)
def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_admin),
):
    document = db.get(KnowledgeDocument, document_id)
    if document is None or document.status == "deleted":
        raise HTTPException(status_code=404, detail="文档不存在")

    previous_status = document.status
    should_delete_vectors = document.chunk_count > 0 or previous_status in {"completed", "processing"}

    document.status = "deleted"
    db.commit()

    try:
        if should_delete_vectors:
            knowledge_service.delete_document_chunks(document.id)
        _delete_source_file(document)
        document.chunk_count = 0
        document.error_message = None
        db.commit()
    except Exception as exc:
        db.rollback()
        document = db.get(KnowledgeDocument, document_id)
        if document is not None:
            document.status = previous_status
            document.error_message = f"删除失败: {str(exc)}"[:2000]
            db.commit()
        raise HTTPException(status_code=500, detail=f"删除文档失败: {str(exc)}") from exc

    return DeleteDocumentResponse(document_id=document_id, message="文档已删除")
