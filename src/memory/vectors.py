"""OpenEcho Memory Vectors — atom 7.2.

ChromaDB-backed vector storage for semantic search.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class MemoryVectors:
    """Vector storage using ChromaDB."""

    def __init__(self, collection_name: str = "openecho_memory") -> None:
        self._collection_name = collection_name
        self._collection: Any = None

    def connect(self) -> None:
        try:
            import chromadb
            client = chromadb.Client()
            self._collection = client.get_or_create_collection(self._collection_name)
        except Exception as e:
            logger.error("ChromaDB connection failed: %s", e)
            raise

    def add(self, doc_id: str, text: str, metadata: dict[str, Any] | None = None) -> None:
        assert self._collection
        self._collection.upsert(
            ids=[doc_id],
            documents=[text],
            metadatas=[metadata or {}],
        )

    def search(self, query: str, n_results: int = 5, where: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        assert self._collection
        kwargs: dict[str, Any] = {"query_texts": [query], "n_results": n_results}
        if where:
            kwargs["where"] = where
        results = self._collection.query(**kwargs)
        items = []
        for i in range(len(results["ids"][0])):
            items.append({
                "id": results["ids"][0][i],
                "text": results["documents"][0][i] if results["documents"] else "",
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                "distance": results["distances"][0][i] if results.get("distances") else 0,
            })
        return items

    def get(self, doc_id: str) -> dict[str, Any] | None:
        assert self._collection
        result = self._collection.get(ids=[doc_id])
        if not result["ids"]:
            return None
        return {
            "id": result["ids"][0],
            "text": result["documents"][0] if result["documents"] else "",
            "metadata": result["metadatas"][0] if result["metadatas"] else {},
        }
