from __future__ import annotations

from functools import lru_cache

from .azure_clients import build_openai_client
from .config import get_settings
from .rag import RagService
from .vector_store import CosmosVectorStore


@lru_cache
def get_rag_service() -> RagService:
    settings = get_settings()
    settings.validate_cloud_config()
    return RagService(
        settings=settings,
        openai_client=build_openai_client(settings),
        store=CosmosVectorStore(settings),
    )

