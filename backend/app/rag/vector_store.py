"""
Vector Store abstraction and ChromaDB integration for Phase 9 RAG Engine.
Provides clean encapsulation over ChromaDB with idempotent upsert,
in-memory test support, and metadata sanitization.
"""
from abc import ABC, abstractmethod
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.config.settings import settings
from app.schemas.rag_models import DocumentChunk

logger = logging.getLogger(__name__)


class VectorStore(ABC):
    """
    Abstract vector store interface. Decoupled from agent and retrieval logic.
    """

    @abstractmethod
    def initialize(self) -> bool:
        pass

    @abstractmethod
    def upsert_chunks(
        self,
        chunks: List[DocumentChunk],
        embeddings: List[List[float]],
    ) -> int:
        pass

    @abstractmethod
    def query(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[DocumentChunk, float]]:
        """
        Returns list of (DocumentChunk, relevance_score) sorted by relevance descending.
        """
        pass

    @abstractmethod
    def count(self) -> int:
        pass

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def clear(self) -> bool:
        pass


class ChromaVectorStore(VectorStore):
    """
    ChromaDB implementation supporting both persistent directory storage
    and ephemeral in-memory storage for test isolation.
    """

    def __init__(
        self,
        collection_name: Optional[str] = None,
        persist_dir: Optional[str] = None,
        in_memory: bool = False,
    ):
        self.collection_name = collection_name or getattr(
            settings, "CHROMA_COLLECTION_NAME", "governance_documents"
        )
        self.persist_dir = persist_dir or getattr(
            settings, "CHROMA_PERSIST_DIRECTORY", "backend/data/chroma_db"
        )
        self.in_memory = in_memory
        self._client = None
        self._collection = None
        self._initialized = False

    def initialize(self) -> bool:
        if self._initialized and self._collection is not None:
            return True

        try:
            import chromadb

            if self.in_memory:
                self._client = chromadb.EphemeralClient()
                logger.info("ChromaVectorStore initialized with EphemeralClient (in-memory)")
            else:
                p_path = Path(self.persist_dir).resolve()
                p_path.mkdir(parents=True, exist_ok=True)
                self._client = chromadb.PersistentClient(path=str(p_path))
                logger.info("ChromaVectorStore initialized with PersistentClient at %s", p_path)

            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            self._initialized = True
            return True
        except Exception as exc:
            logger.error("ChromaDB initialization failed: %s", exc)
            self._initialized = False
            return False

    def upsert_chunks(
        self,
        chunks: List[DocumentChunk],
        embeddings: List[List[float]],
    ) -> int:
        if not self.initialize() or not chunks:
            return 0

        ids = [c.chunk_id for c in chunks]
        documents = [c.text for c in chunks]
        metadatas: List[Dict[str, Any]] = []

        for c in chunks:
            # Sanitize metadata for ChromaDB (must be str, int, float, or bool)
            meta: Dict[str, Any] = {
                "doc_id": str(c.doc_id),
                "title": str(c.title),
                "category": str(c.category),
                "section": str(c.section),
                "chunk_index": int(c.chunk_index),
                "content_hash": str(c.content_hash),
                "token_count": int(c.token_count),
                "tags": ",".join(c.relevance_tags),
            }
            metadatas.append(meta)

        try:
            self._collection.upsert(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
            )
            logger.info(
                "ChromaVectorStore successfully upserted %d chunks into collection '%s'",
                len(chunks),
                self.collection_name,
            )
            return len(chunks)
        except Exception as exc:
            logger.error("ChromaVectorStore upsert failed: %s", exc)
            raise

    def query(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[DocumentChunk, float]]:
        if not self.initialize() or self.count() == 0:
            return []

        # Clamp top_k to available items
        actual_k = min(max(1, top_k), self.count())

        where_clause = None
        if filters:
            # Support simple key-value filters e.g. {"category": "principles"} or {"doc_id": "ai_principles"}
            clean_filters = {k: v for k, v in filters.items() if v is not None}
            if len(clean_filters) == 1:
                k, v = next(iter(clean_filters.items()))
                where_clause = {k: v}
            elif len(clean_filters) > 1:
                where_clause = {"$and": [{k: v} for k, v in clean_filters.items()]}

        try:
            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=actual_k,
                where=where_clause,
                include=["documents", "metadatas", "distances"],
            )

            matched_chunks: List[Tuple[DocumentChunk, float]] = []

            ids = results.get("ids", [[]])[0]
            docs = results.get("documents", [[]])[0]
            metas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0]

            for c_id, text, meta, dist in zip(ids, docs, metas, distances):
                # Cosine similarity calculation: 1.0 - distance
                relevance = max(0.0, min(1.0, 1.0 - float(dist)))
                tags = meta.get("tags", "").split(",") if meta.get("tags") else []

                chunk = DocumentChunk(
                    chunk_id=c_id,
                    doc_id=meta.get("doc_id", "unknown"),
                    title=meta.get("title", ""),
                    category=meta.get("category", "principles"),
                    section=meta.get("section", ""),
                    chunk_index=int(meta.get("chunk_index", 0)),
                    text=text,
                    token_count=int(meta.get("token_count", 0)),
                    content_hash=meta.get("content_hash", ""),
                    relevance_tags=[t for t in tags if t],
                    metadata=meta,
                )
                matched_chunks.append((chunk, round(relevance, 4)))

            # Ensure sorted by relevance descending, with deterministic secondary sort by chunk_id
            matched_chunks.sort(key=lambda x: (-x[1], x[0].chunk_id))
            return matched_chunks

        except Exception as exc:
            logger.error("ChromaVectorStore query failed: %s", exc)
            return []

    def count(self) -> int:
        if not self.initialize() or self._collection is None:
            return 0
        try:
            return self._collection.count()
        except Exception:
            return 0

    def health_check(self) -> Dict[str, Any]:
        ready = self.initialize()
        cnt = self.count() if ready else 0
        return {
            "status": "ready" if ready else "unavailable",
            "collection_name": self.collection_name,
            "count": cnt,
            "in_memory": self.in_memory,
            "persist_directory": self.persist_dir if not self.in_memory else "in-memory",
        }

    def clear(self) -> bool:
        if not self.initialize():
            return False
        try:
            self._client.delete_collection(self.collection_name)
            self._collection = self._client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            return True
        except Exception as exc:
            logger.error("Failed to clear collection: %s", exc)
            return False


# Global default instance
default_vector_store: Optional[VectorStore] = None


def get_vector_store(
    in_memory: bool = False,
    force_new: bool = False,
) -> VectorStore:
    """
    Returns the vector store singleton instance.
    """
    global default_vector_store
    if default_vector_store is not None and not force_new and not in_memory:
        return default_vector_store

    store = ChromaVectorStore(
        collection_name=getattr(settings, "CHROMA_COLLECTION_NAME", "governance_documents"),
        persist_dir=getattr(settings, "CHROMA_PERSIST_DIRECTORY", "backend/data/chroma_db"),
        in_memory=in_memory,
    )
    store.initialize()

    if not in_memory:
        default_vector_store = store
    return store
