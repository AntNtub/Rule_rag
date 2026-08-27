from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_env: str = "development"
    cors_origins: str = "http://localhost:5173"

    azure_openai_endpoint: str = ""
    azure_openai_api_version: str = "2024-10-21"
    azure_openai_chat_deployment: str = ""
    azure_openai_embedding_deployment: str = ""
    azure_openai_api_key: str = ""

    azure_cosmos_endpoint: str = ""
    azure_cosmos_database: str = "campus-policy"
    azure_cosmos_container: str = "regulation-chunks"
    azure_cosmos_key: str = ""

    embedding_dimensions: int = 1536
    vector_index_type: Literal["flat", "quantizedFlat", "diskANN"] = "quantizedFlat"
    retrieval_top_k: int = 6
    max_vector_distance: float | None = None
    chunk_size_chars: int = 1200
    chunk_overlap_chars: int = 180
    generation_temperature: float = 0.0

    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    def validate_cloud_config(self) -> None:
        missing = [
            name
            for name, value in {
                "AZURE_OPENAI_ENDPOINT": self.azure_openai_endpoint,
                "AZURE_OPENAI_CHAT_DEPLOYMENT": self.azure_openai_chat_deployment,
                "AZURE_OPENAI_EMBEDDING_DEPLOYMENT": self.azure_openai_embedding_deployment,
                "AZURE_COSMOS_ENDPOINT": self.azure_cosmos_endpoint,
            }.items()
            if not value
        ]
        if missing:
            raise RuntimeError("Missing cloud configuration: " + ", ".join(missing))
        if self.chunk_overlap_chars >= self.chunk_size_chars:
            raise RuntimeError("CHUNK_OVERLAP_CHARS must be smaller than CHUNK_SIZE_CHARS")


@lru_cache
def get_settings() -> Settings:
    return Settings()
