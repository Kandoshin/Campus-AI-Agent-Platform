from datetime import datetime
from typing import Literal

from pydantic import BaseModel


AccessLevel = Literal["public", "student", "admin"]
DocumentStatus = Literal["pending", "processing", "completed", "failed", "deleted"]


class KnowledgeDocumentPublic(BaseModel):
    id: str
    title: str
    original_filename: str
    file_ext: str
    file_size: int
    content_type: str | None = None
    category: str
    access_level: AccessLevel
    storage_path: str
    status: DocumentStatus
    chunk_count: int
    uploaded_by_id: int | None = None
    uploaded_by_username: str
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}


class DeleteDocumentResponse(BaseModel):
    status: str = "success"
    document_id: str
    message: str
