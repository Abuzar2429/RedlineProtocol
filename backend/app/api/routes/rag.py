"""
FastAPI route endpoints for Phase 9 RAG Engine.
Provides health monitoring, controlled semantic retrieval, and ingestion status.
"""
import logging
import time
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status

from app.rag.engine import get_rag_engine
from app.rag.ingestion import get_ingestion_service
from app.schemas.rag_models import (
    IngestionReport,
    RAGHealthResponse,
    RAGQueryRequest,
    RAGQueryResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/rag", tags=["RAG"])


@router.get("/health", response_model=RAGHealthResponse)
async def rag_health() -> RAGHealthResponse:
    """
    Returns real-time health and status information for the RAG engine and vector store.
    """
    engine = get_rag_engine()
    return engine.get_health()


@router.post("/search", response_model=RAGQueryResponse)
async def rag_search(request: RAGQueryRequest) -> RAGQueryResponse:
    """
    Executes controlled semantic search over the governance vector store.
    Enforces maximum query length and clamps top_k to at most 10 (default 5).
    """
    start_time = time.time()
    engine = get_rag_engine()

    filters = {}
    if request.category:
        filters["category"] = request.category
    if request.doc_id:
        filters["doc_id"] = request.doc_id

    results = engine.retrieve(
        query=request.query,
        top_k=request.top_k,
        filters=filters if filters else None,
        agent_type="api_search",
        agent_id="user",
    )

    elapsed_ms = round((time.time() - start_time) * 1000.0, 2)

    return RAGQueryResponse(
        query=request.query,
        results_count=len(results),
        results=results,
        latency_ms=elapsed_ms,
    )


@router.post("/ingest", response_model=IngestionReport)
async def trigger_ingestion(
    force_clear: bool = Query(False, description="Clear existing collection before re-indexing"),
) -> IngestionReport:
    """
    Triggers idempotent ingestion of Phase 2 governance documents into ChromaDB.
    """
    service = get_ingestion_service()
    report = service.ingest_all(force_clear=force_clear)
    if report.status == "FAILED":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {'; '.join(report.errors)}",
        )
    return report
