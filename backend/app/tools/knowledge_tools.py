from contextvars import ContextVar, Token
from typing import Literal

from langchain_core.tools import tool
from langchain_community.vectorstores.milvus import Milvus

from app.core.config import settings
from app.services.zhipu_embeddings import ZhipuEmbeddings

_vector_store = None
_current_user_role: ContextVar[str] = ContextVar("current_user_role", default="guest")

ROLE_ACCESS_LEVELS = {
    "guest": ["public"],
    "student": ["public", "student"],
    "admin": ["public", "student", "admin"],
}


def _get_vector_store():
    """Lazy init keeps the FastAPI app importable when Milvus is offline."""
    global _vector_store
    if _vector_store is not None:
        return _vector_store

    embeddings = ZhipuEmbeddings(
        api_key=settings.zhipu_api_key,
        model=settings.embedding_model,
        dimensions=settings.embedding_dimensions,
        batch_size=settings.embedding_batch_size,
    )
    _vector_store = Milvus(
        embedding_function=embeddings,
        collection_name=settings.milvus_collection,
        connection_args={"uri": settings.milvus_uri},
    )
    return _vector_store


def _access_expr(role: str) -> str:
    levels = ROLE_ACCESS_LEVELS.get(role, ROLE_ACCESS_LEVELS["guest"])
    quoted_levels = ", ".join(f'"{level}"' for level in levels)
    return f"access_level in [{quoted_levels}]"


def set_current_user_role(role: str) -> Token[str]:
    return _current_user_role.set(role)


def reset_current_user_role(token: Token[str]) -> None:
    _current_user_role.reset(token)


@tool
def query_campus_knowledge_base(
    query: str,
    role: Literal["guest", "student", "admin"] = "guest",
) -> str:
    """
    当用户询问校园公开信息、学生手册、校规校纪、招生政策、校园服务等知识库内容时调用此工具。
    输入应该是提炼后的核心检索关键词或问题。
    role 用于权限过滤：guest 只能检索 public，student 可检索 public/student，admin 可检索全部。
    """
    effective_role = _current_user_role.get()
    try:
        docs = _get_vector_store().similarity_search(
            query,
            k=3,
            expr=_access_expr(effective_role),
        )
        if not docs:
            return "知识库中未找到相关内容。"

        formatted_results = []
        for i, doc in enumerate(docs):
            # 提取元数据用于溯源
            title = doc.metadata.get("title", "未知文档")
            page = doc.metadata.get("page", "未知页码")
            access_level = doc.metadata.get("access_level", "unknown")

            formatted_results.append(
                f"[来源 {i + 1}]: 《{title}》第 {page} 页，权限级别: {access_level}\n"
                f"相关内容: {doc.page_content}\n"
            )

        return "\n---\n".join(formatted_results)
    except Exception as e:
        return f"检索知识库时发生错误: {str(e)}"
