"""
Governance document ingestion pipeline for Phase 9 RAG Engine.
Loads documents through DataLoader, chunks them deterministically,
generates embeddings, and upserts into ChromaDB idempotently.
"""
import logging
import time
from typing import List, Optional

from app.config.settings import settings
from app.rag.chunker import GovernanceChunker
from app.rag.embeddings import EmbeddingProvider, get_embedding_provider
from app.rag.vector_store import VectorStore, get_vector_store
from app.schemas.rag_models import DocumentChunk, IngestionReport
from app.services.data_loader import DataLoader

logger = logging.getLogger(__name__)


class GovernanceIngestionService:
    """
    Idempotent document ingestion service.
    Loads documents from the authoritative Phase 2 data store.
    """

    def __init__(
        self,
        data_loader: Optional[DataLoader] = None,
        chunker: Optional[GovernanceChunker] = None,
        embedding_provider: Optional[EmbeddingProvider] = None,
        vector_store: Optional[VectorStore] = None,
    ):
        self.data_loader = data_loader or DataLoader()
        self.chunker = chunker or GovernanceChunker()
        self.embedder = embedding_provider or get_embedding_provider()
        self.vector_store = vector_store or get_vector_store()
        self._last_ingestion_time: Optional[float] = None

    @property
    def last_ingestion_time(self) -> Optional[float]:
        return self._last_ingestion_time

    def ingest_all(self, force_clear: bool = False) -> IngestionReport:
        """
        Executes full ingestion pipeline over all governance documents.
        """
        start_time = time.time()
        errors: List[str] = []

        logger.info("Starting governance document ingestion pipeline...")

        if force_clear:
            logger.info("Clearing existing vector collection before re-indexing...")
            self.vector_store.clear()

        # 1. Load documents through DataLoader
        try:
            documents = self.data_loader.load_governance_documents()
        except Exception as exc:
            msg = f"Failed to load governance documents: {exc}"
            logger.error(msg)
            return IngestionReport(
                documents_discovered=0,
                documents_loaded=0,
                chunks_generated=0,
                chunks_upserted=0,
                collection_name=getattr(self.vector_store, "collection_name", "governance_documents"),
                elapsed_seconds=round(time.time() - start_time, 3),
                status="FAILED",
                errors=[msg],
            )

        # 2. Chunk documents deterministically
        all_chunks: List[DocumentChunk] = []
        for doc in documents:
            try:
                doc_chunks = self.chunker.chunk_document(doc)
                all_chunks.extend(doc_chunks)
            except Exception as exc:
                err = f"Failed to chunk doc '{doc.metadata.doc_id}': {exc}"
                logger.error(err)
                errors.append(err)

        if not all_chunks:
            return IngestionReport(
                documents_discovered=len(documents),
                documents_loaded=len(documents),
                chunks_generated=0,
                chunks_upserted=0,
                collection_name=getattr(self.vector_store, "collection_name", "governance_documents"),
                elapsed_seconds=round(time.time() - start_time, 3),
                status="EMPTY",
                errors=errors,
            )

        # 3. Generate embeddings
        chunk_texts = [c.text for c in all_chunks]
        try:
            embeddings = self.embedder.embed_documents(chunk_texts)
        except Exception as exc:
            err = f"Embedding generation failed: {exc}"
            logger.error(err)
            errors.append(err)
            return IngestionReport(
                documents_discovered=len(documents),
                documents_loaded=len(documents),
                chunks_generated=len(all_chunks),
                chunks_upserted=0,
                collection_name=getattr(self.vector_store, "collection_name", "governance_documents"),
                elapsed_seconds=round(time.time() - start_time, 3),
                status="FAILED",
                errors=errors,
            )

        # 4. Upsert into VectorStore idempotently
        try:
            upserted_count = self.vector_store.upsert_chunks(all_chunks, embeddings)
        except Exception as exc:
            err = f"Vector store upsert failed: {exc}"
            logger.error(err)
            errors.append(err)
            return IngestionReport(
                documents_discovered=len(documents),
                documents_loaded=len(documents),
                chunks_generated=len(all_chunks),
                chunks_upserted=0,
                collection_name=getattr(self.vector_store, "collection_name", "governance_documents"),
                elapsed_seconds=round(time.time() - start_time, 3),
                status="FAILED",
                errors=errors,
            )

        elapsed = round(time.time() - start_time, 3)
        self._last_ingestion_time = time.time()

        logger.info(
            "Governance ingestion complete: %d documents -> %d chunks stored in %.2fs",
            len(documents),
            upserted_count,
            elapsed,
        )

        return IngestionReport(
            documents_discovered=len(documents),
            documents_loaded=len(documents),
            chunks_generated=len(all_chunks),
            chunks_upserted=upserted_count,
            collection_name=getattr(self.vector_store, "collection_name", "governance_documents"),
            elapsed_seconds=elapsed,
            status="COMPLETED" if not errors else "COMPLETED_WITH_WARNINGS",
            errors=errors,
        )


# Global default ingestion service
default_ingestion_service: Optional[GovernanceIngestionService] = None


def get_ingestion_service() -> GovernanceIngestionService:
    global default_ingestion_service
    if default_ingestion_service is None:
        default_ingestion_service = GovernanceIngestionService()
    return default_ingestion_service
