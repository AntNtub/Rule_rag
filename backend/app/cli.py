from __future__ import annotations

import argparse
import json
from pathlib import Path

from .azure_clients import build_openai_client
from .chunking import split_into_spans, stable_id
from .config import get_settings
from .loaders import discover_documents, load_document
from .vector_store import CosmosVectorStore


def build_items(root: Path, include_embeddings: bool) -> list[dict]:
    settings = get_settings()
    client = build_openai_client(settings) if include_embeddings else None
    items: list[dict] = []
    for path in discover_documents(root):
        document = load_document(path)
        document_id = stable_id(document.title, document.version, document.source_url or str(path))
        spans = split_into_spans(
            document.text, settings.chunk_size_chars, settings.chunk_overlap_chars
        )
        for span in spans:
            chunk_id = stable_id(document_id, str(span.ordinal), span.content)
            item = {
                "id": chunk_id,
                "document_id": document_id,
                "title": document.title,
                "category": document.category,
                "issued_at": document.issued_at,
                "source_url": document.source_url,
                "version": document.version,
                "section_id": span.section_id,
                "ordinal": span.ordinal,
                "content": span.content,
            }
            if client:
                response = client.embeddings.create(
                    model=settings.azure_openai_embedding_deployment,
                    input=span.content,
                )
                item["embedding"] = response.data[0].embedding
            items.append(item)
    return items


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the regulation knowledge base")
    parser.add_argument("command", choices=["preview", "ingest"])
    parser.add_argument("path", type=Path)
    args = parser.parse_args()

    settings = get_settings()
    if args.command == "preview":
        items = build_items(args.path, include_embeddings=False)
        print(json.dumps(items, ensure_ascii=False, indent=2))
        print(f"\nPrepared {len(items)} chunks from {args.path}")
        return

    settings.validate_cloud_config()
    store = CosmosVectorStore(settings, create=True)
    items = build_items(args.path, include_embeddings=True)
    for item in items:
        store.upsert(item)
    print(f"Upserted {len(items)} chunks into {settings.azure_cosmos_container}")


if __name__ == "__main__":
    main()

