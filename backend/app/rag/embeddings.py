"""
Embedding provider abstraction for Phase 9 RAG Engine.
Includes MockEmbeddingProvider (deterministic, fast, zero-dependency)
and extensible provider factory.
"""
from abc import ABC, abstractmethod
import hashlib
import logging
import math
import re
from typing import List, Optional

from app.config.settings import settings

logger = logging.getLogger(__name__)


class EmbeddingProvider(ABC):
    """
    Abstract Base Class for embedding providers.
    Decoupled from LLMProvider and VectorStore.
    """

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding vector for a single query text."""
        pass

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embedding vectors for multiple document chunks."""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Embedding vector dimension."""
        pass


class MockEmbeddingProvider(EmbeddingProvider):
    """
    Deterministic, zero-dependency embedding provider for development and testing.
    Uses SHA-256 token hashing and n-gram projection with L2 normalization.
    Guarantees:
    - 100% deterministic (same text -> identical vector)
    - Words with shared tokens produce high cosine similarity
    - Sub-millisecond execution without external API calls or network requests
    """

    def __init__(self, dimension: int = 384):
        self._dim = dimension

    @property
    def dimension(self) -> int:
        return self._dim

    def embed_text(self, text: str) -> List[float]:
        return self._compute_vector(text)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._compute_vector(t) for t in texts]

    def _compute_vector(self, text: str) -> List[float]:
        vec = [0.0] * self._dim
        if not text or not text.strip():
            # Return uniform normalized vector for empty text
            val = 1.0 / math.sqrt(self._dim)
            return [val] * self._dim

        # Tokenize into words and n-grams
        tokens = re.findall(r"\b[a-zA-Z0-9_\-]+\b", text.lower())
        if not tokens:
            tokens = [text.strip().lower()]

        # Generate projections
        for token in tokens:
            # Word-level hash
            token_hash = int(hashlib.sha256(token.encode("utf-8")).hexdigest(), 16)
            idx = token_hash % self._dim
            sign = 1.0 if ((token_hash >> 8) & 1) == 0 else -1.0
            vec[idx] += sign * 1.5

            # Bi-gram sub-tokens for prefix/suffix matching
            for i in range(len(token) - 2):
                tri = token[i : i + 3]
                tri_hash = int(hashlib.sha256(tri.encode("utf-8")).hexdigest(), 16)
                t_idx = tri_hash % self._dim
                t_sign = 1.0 if ((tri_hash >> 8) & 1) == 0 else -1.0
                vec[t_idx] += t_sign * 0.5

        # L2 normalize
        norm_sq = sum(v * v for v in vec)
        if norm_sq <= 1e-12:
            val = 1.0 / math.sqrt(self._dim)
            return [val] * self._dim

        norm = math.sqrt(norm_sq)
        return [round(v / norm, 6) for v in vec]


class ExternalEmbeddingProvider(EmbeddingProvider):
    """
    Adapter for external or local embedding libraries (e.g. sentence-transformers, OpenAI).
    Falls back gracefully to MockEmbeddingProvider if external library is missing or fails.
    """

    def __init__(
        self,
        provider_name: str,
        model_name: str,
        api_key: Optional[str] = None,
        dimension: int = 384,
    ):
        self.provider_name = provider_name
        self.model_name = model_name
        self.api_key = api_key
        self._dim = dimension
        self._fallback = MockEmbeddingProvider(dimension=dimension)
        self._model_instance = None
        self._init_external_model()

    def _init_external_model(self):
        if self.provider_name == "sentence_transformers":
            try:
                from sentence_transformers import SentenceTransformer
                self._model_instance = SentenceTransformer(self.model_name)
                logger.info("Loaded SentenceTransformer model: %s", self.model_name)
            except Exception as exc:
                logger.warning(
                    "sentence_transformers unavailable (%s); falling back to MockEmbeddingProvider",
                    exc,
                )
        elif self.provider_name == "openai":
            # Requires openai package and API key
            try:
                import openai
                if not self.api_key:
                    logger.warning("No EMBEDDING_API_KEY provided for OpenAI; falling back to MockEmbeddingProvider")
                else:
                    self._model_instance = openai.OpenAI(api_key=self.api_key)
            except Exception as exc:
                logger.warning("OpenAI client initialization failed (%s); falling back to MockEmbeddingProvider", exc)

    @property
    def dimension(self) -> int:
        return self._dim

    def embed_text(self, text: str) -> List[float]:
        if self._model_instance is None:
            return self._fallback.embed_text(text)
        try:
            if self.provider_name == "sentence_transformers":
                arr = self._model_instance.encode(text, normalize_embeddings=True)
                return [round(float(x), 6) for x in arr]
            elif self.provider_name == "openai":
                resp = self._model_instance.embeddings.create(input=[text], model=self.model_name)
                return resp.data[0].embedding
        except Exception as exc:
            logger.warning("External embedding failed: %s; using deterministic fallback", exc)
            return self._fallback.embed_text(text)
        return self._fallback.embed_text(text)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if self._model_instance is None:
            return self._fallback.embed_documents(texts)
        try:
            if self.provider_name == "sentence_transformers":
                arr = self._model_instance.encode(texts, normalize_embeddings=True)
                return [[round(float(x), 6) for x in row] for row in arr]
            elif self.provider_name == "openai":
                resp = self._model_instance.embeddings.create(input=texts, model=self.model_name)
                return [item.embedding for item in resp.data]
        except Exception as exc:
            logger.warning("External batch embedding failed: %s; using deterministic fallback", exc)
            return self._fallback.embed_documents(texts)
        return self._fallback.embed_documents(texts)


# Singleton factory
_embedding_provider_instance: Optional[EmbeddingProvider] = None


def get_embedding_provider(
    provider_name: Optional[str] = None,
    force_new: bool = False,
) -> EmbeddingProvider:
    """
    Returns the configured embedding provider singleton.
    Defaults to MockEmbeddingProvider if provider_name is 'mock' or not specified.
    """
    global _embedding_provider_instance
    if _embedding_provider_instance is not None and not force_new:
        return _embedding_provider_instance

    p_name = (provider_name or getattr(settings, "EMBEDDING_PROVIDER", "mock")).lower()

    if p_name in ("mock", "test", "deterministic"):
        _embedding_provider_instance = MockEmbeddingProvider(dimension=384)
    elif p_name in ("sentence_transformers", "openai"):
        _embedding_provider_instance = ExternalEmbeddingProvider(
            provider_name=p_name,
            model_name=getattr(settings, "EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
            api_key=getattr(settings, "EMBEDDING_API_KEY", None),
            dimension=384,
        )
    else:
        logger.warning("Unknown embedding provider '%s'; defaulting to MockEmbeddingProvider", p_name)
        _embedding_provider_instance = MockEmbeddingProvider(dimension=384)

    return _embedding_provider_instance
