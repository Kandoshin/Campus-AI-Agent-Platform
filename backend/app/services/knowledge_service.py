import os
from uuid import uuid4

from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores.milvus import Milvus

from app.core.config import settings
from app.services.zhipu_embeddings import ZhipuEmbeddings


class KnowledgeService:
    def __init__(self):
        self.embeddings = ZhipuEmbeddings(
            api_key=settings.zhipu_api_key,
            model=settings.embedding_model,
            dimensions=settings.embedding_dimensions,
            batch_size=settings.embedding_batch_size,
        )
        self.milvus_uri = settings.milvus_uri
        self.collection_name = settings.milvus_collection

    def _get_loader(self, file_path: str):
        """根据文件后缀匹配加载器"""
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".pdf":
            return PyPDFLoader(file_path)
        elif ext == ".docx":
            return Docx2txtLoader(file_path)
        elif ext in [".txt", ".md"]:
            return TextLoader(file_path, encoding="utf-8")
        else:
            raise ValueError(f"暂不支持的文件格式: {ext}")

    def load_and_split(self, file_path: str):
        """解析并切分文档"""
        loader = self._get_loader(file_path)
        documents = loader.load()

        # 采用递归字符切分，适合代码和自然语言混合的文档
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=100
        )
        return text_splitter.split_documents(documents)

    def process_and_store(
        self,
        file_path: str,
        title: str | None = None,
        category: str = "general",
        access_level: str = "public",
    ) -> int:
        """处理文件并持久化到 Milvus，返回切片数量"""
        chunks = self.load_and_split(file_path)

        file_name = os.path.basename(file_path)
        document_id = uuid4().hex
        document_title = title or os.path.splitext(file_name)[0]

        for index, chunk in enumerate(chunks):
            page = chunk.metadata.get("page", 0)
            chunk.metadata = {
                "document_id": document_id,
                "chunk_index": index,
                "source_file": file_name,
                "title": document_title,
                "page": page,
                "category": category,
                "access_level": access_level,
            }

        Milvus.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            collection_name=self.collection_name,
            connection_args={"uri": self.milvus_uri},
            drop_old=False  # 保留原有知识
        )
        return len(chunks)
