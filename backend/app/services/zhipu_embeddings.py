from typing import List

import requests
from langchain_core.embeddings import Embeddings

from app.core.config import settings


class ZhipuEmbeddings(Embeddings):
    """LangChain embedding adapter for Zhipu's official embeddings API."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        dimensions: int | None = None,
        batch_size: int | None = None,
        base_url: str | None = None,
        timeout: int | None = None,
    ):
        self.api_key = api_key or settings.zhipu_api_key
        self.model = model or settings.embedding_model
        self.dimensions = dimensions or settings.embedding_dimensions
        self.batch_size = batch_size or settings.embedding_batch_size
        self.base_url = (base_url or settings.zhipu_embedding_base_url).rstrip("/")
        self.timeout = timeout or settings.zhipu_embedding_timeout

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        embeddings: List[List[float]] = []
        for start in range(0, len(texts), self.batch_size):
            batch = texts[start:start + self.batch_size]
            embeddings.extend(self._embed_batch(batch))
        return embeddings

    def embed_query(self, text: str) -> List[float]:
        return self._embed_batch([text])[0]

    def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        if not self.api_key:
            raise ValueError("ZHIPU_API_KEY 未配置，无法调用智谱 embedding 接口")

        response = requests.post(
            f"{self.base_url}/embeddings",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "input": texts,
                "dimensions": self.dimensions,
            },
            timeout=self.timeout,
        )

        if response.status_code >= 400:
            raise RuntimeError(f"智谱 embedding 调用失败: {response.status_code} {response.text}")

        payload = response.json()
        data = payload.get("data")
        if not isinstance(data, list):
            raise RuntimeError(f"智谱 embedding 响应格式异常: {payload}")

        data.sort(key=lambda item: item.get("index", 0))
        return [item["embedding"] for item in data]
