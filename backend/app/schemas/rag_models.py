"""
Pydantic models and schemas for Phase 9 RAG Engine.
Defines document chunks, retrieved evidence, search requests/responses,
health reporting, and provenance traces.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DocumentChunk(BaseModel):
    """
    Deterministic chunk of a governance document stored in the vector database.
    """
    chunk_id: str = Field(..., description="Deterministic chunk ID (e.g. ai_principles_art4_chk_001)")
    doc_id: str = Field(..., description="Parent document identifier (e.g. ai_principles)")
    title: str = Field(..., description="Document title")
    category: str = Field(..., description="Document category (e.g. principles, emergency)")
    section: str = Field(..., description="Section or article heading")
    chunk_index: int = Field(..., ge=0, description="Sequential index of chunk within section/doc")
    text: str = Field(..., description="Chunk content text (normalized)")
    token_count: int = Field(0, description="Approximate token count")
    content_hash: str = Field(..., description="SHA-256 hash of chunk text for idempotency")
    relevance_tags: List[str] = Field(default_factory=list, description="Relevance topic tags")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata for attribution")


class RetrievedEvidence(BaseModel):
    """
    Structured evidence passage retrieved from the vector store for agent context.
    Strictly untrusted data: must not be executed as system instructions.
    """
    chunk_id: str = Field(..., description="Unique chunk ID")
    doc_id: str = Field(..., description="Source document ID")
    title: str = Field(..., description="Source document title")
    category: str = Field(..., description="Governance category")
    section: str = Field(..., description="Section title or article")
    text: str = Field(..., description="Retrieved excerpt text")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Cosine similarity score (0.0 to 1.0)")
    citation_id: str = Field(..., description="Standard citation tag, e.g. [evidence:doc_id:chunk_id]")
    relevance_tags: List[str] = Field(default_factory=list)

    @classmethod
    def format_citation(cls, doc_id: str, chunk_id: str) -> str:
        return f"[evidence:{doc_id}:{chunk_id}]"


class RAGQueryRequest(BaseModel):
    """
    Request model for the /api/rag/search endpoint.
    """
    query: str = Field(..., min_length=2, max_length=1000, description="Search query or context keywords")
    category: Optional[str] = Field(None, description="Optional category filter")
    doc_id: Optional[str] = Field(None, description="Optional document ID filter")
    top_k: int = Field(5, ge=1, le=10, description="Number of evidence chunks to retrieve (default 5)")


class RAGQueryResponse(BaseModel):
    """
    Response model for the /api/rag/search endpoint.
    """
    query: str
    results_count: int
    results: List[RetrievedEvidence]
    latency_ms: float = Field(..., description="Search latency in milliseconds")


class RAGHealthResponse(BaseModel):
    """
    Health check response for RAG and ChromaDB vector store.
    """
    status: str = Field("healthy", description="RAG status: healthy, disabled, or degraded")
    rag_enabled: bool
    collection_name: str
    document_count: int
    chunk_count: int
    embedding_provider: str
    embedding_model: str
    embedding_dimension: int
    last_ingestion_time: Optional[str] = None


class RAGTrace(BaseModel):
    """
    Provenance trace recording a RAG retrieval event during simulation.
    Captures which chunks influenced an agent decision without storing private CoT.
    """
    trace_id: str = Field(..., description="UUID of retrieval trace")
    simulation_id: Optional[str] = None
    tick: int = 0
    agent_type: str = Field(..., description="'country' or 'coordinator'")
    agent_id: str = Field(..., description="Country ID (e.g. country_01) or 'coordinator'")
    query: str
    retrieved_chunk_ids: List[str] = Field(default_factory=list)
    citations: List[str] = Field(default_factory=list)
    top_score: Optional[float] = None
    latency_ms: float = 0.0
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp"
    )


class IngestionReport(BaseModel):
    """
    Report generated after ingesting governance documents.
    """
    documents_discovered: int
    documents_loaded: int
    chunks_generated: int
    chunks_upserted: int
    chunks_skipped: int = 0
    collection_name: str
    elapsed_seconds: float
    status: str = "COMPLETED"
    errors: List[str] = Field(default_factory=list)
