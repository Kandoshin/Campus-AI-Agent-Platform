from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Campus AI Agent Platform API"
    app_version: str = "0.9.0"

    openai_api_key: str = ""
    openai_api_base: str = "https://api.littlecold.cn/v1"
    openai_default_model: str = "gpt-5.5"

    zhipu_api_key: str = ""
    zhipu_embedding_base_url: str = "https://open.bigmodel.cn/api/paas/v4"
    zhipu_embedding_timeout: int = 60

    embedding_model: str = "embedding-3"
    embedding_dimensions: int = 1024
    embedding_batch_size: int = 16

    milvus_uri: str = "http://127.0.0.1:19530"
    milvus_collection: str = "campus_knowledge"

    database_url: str = "postgresql+psycopg://campus_ai:campus_ai_dev_password@127.0.0.1:5432/campus_ai"

    auth_secret_key: str = "campus-ai-dev-secret-change-me"
    auth_access_token_expire_minutes: int = 60 * 24
    default_admin_username: str = "admin"
    default_admin_password: str = "admin123456"
    default_admin_display_name: str = "系统管理员"

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
