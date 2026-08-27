from __future__ import annotations

from typing import Any

from azure.cosmos import PartitionKey

from .azure_clients import build_cosmos_client
from .config import Settings


class CosmosVectorStore:
    def __init__(self, settings: Settings, create: bool = False) -> None:
        self.settings = settings
        client = build_cosmos_client(settings)
        if create:
            database = client.create_database_if_not_exists(settings.azure_cosmos_database)
            self.container = database.create_container_if_not_exists(
                id=settings.azure_cosmos_container,
                partition_key=PartitionKey(path="/document_id"),
                indexing_policy={
                    "automatic": True,
                    "indexingMode": "consistent",
                    "includedPaths": [{"path": "/*"}],
                    "excludedPaths": [
                        {"path": '/"_etag"/?'},
                        {"path": "/embedding/*"},
                    ],
                    "vectorIndexes": [
                        {"path": "/embedding", "type": settings.vector_index_type}
                    ],
                },
                vector_embedding_policy={
                    "vectorEmbeddings": [
                        {
                            "path": "/embedding",
                            "dataType": "float32",
                            "dimensions": settings.embedding_dimensions,
                            "distanceFunction": "cosine",
                        }
                    ]
                },
            )
        else:
            database = client.get_database_client(settings.azure_cosmos_database)
            self.container = database.get_container_client(settings.azure_cosmos_container)

    def upsert(self, item: dict[str, Any]) -> None:
        self.container.upsert_item(item)

    def search(self, embedding: list[float], top_k: int) -> list[dict[str, Any]]:
        safe_top_k = max(1, min(int(top_k), 20))
        query = f"""
            SELECT TOP {safe_top_k}
                c.id, c.document_id, c.title, c.section_id, c.issued_at,
                c.source_url, c.content,
                VectorDistance(c.embedding, @embedding) AS distance
            FROM c
            ORDER BY VectorDistance(c.embedding, @embedding)
        """
        return list(
            self.container.query_items(
                query=query,
                parameters=[{"name": "@embedding", "value": embedding}],
                enable_cross_partition_query=True,
            )
        )

