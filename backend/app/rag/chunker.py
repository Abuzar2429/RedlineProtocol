"""
Document chunking and text normalization for Phase 9 RAG Engine.
Implements section-aware splitting at 500 tokens with 50-token overlap,
deterministic chunk IDs, and SHA-256 content hashing.
"""
import hashlib
import re
from typing import List, Tuple

from app.config.settings import settings
from app.schemas.data_models import GovernanceDocument
from app.schemas.rag_models import DocumentChunk


def normalize_text(text: str) -> str:
    """
    Normalizes text while strictly preserving headings, lists, and structural markers.
    """
    if not text:
        return ""
    # Standardize line breaks
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Strip trailing whitespace on lines
    lines = [line.rstrip() for line in text.splitlines()]
    cleaned = "\n".join(lines)
    # Collapse 3+ consecutive newlines to 2
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def slugify_section(section_name: str) -> str:
    """
    Generates a deterministic slug for a section heading.
    E.g. '## 1. Purpose and Preamble' -> 'purpose_and_preamble'
    """
    cleaned = re.sub(r"^[#\s\d\.\-:]+", "", section_name).strip()
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", cleaned).strip("_").lower()
    return slug or "section"


def estimate_token_count(text: str) -> int:
    """
    Estimates token count (~4 characters per token).
    """
    return max(1, len(text) // 4)


class GovernanceChunker:
    """
    Deterministic chunker for governance knowledge documents.
    Splits at configured chunk_size (default 500 tokens) with chunk_overlap (default 50 tokens).
    Preserves document identity and section headings.
    """

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ):
        self.chunk_size = chunk_size or getattr(settings, "RAG_CHUNK_SIZE", 500)
        self.chunk_overlap = chunk_overlap or getattr(settings, "RAG_CHUNK_OVERLAP", 50)
        # Approximate characters: 1 token ~ 4 characters
        self.max_chars = self.chunk_size * 4
        self.overlap_chars = self.chunk_overlap * 4

    def chunk_document(self, doc: GovernanceDocument) -> List[DocumentChunk]:
        """
        Chunks a parsed GovernanceDocument deterministically.
        """
        doc_id = doc.metadata.doc_id
        title = doc.metadata.title
        category = doc.metadata.category
        relevance_tags = list(doc.metadata.relevance_tags)
        version = doc.metadata.version

        chunks: List[DocumentChunk] = []
        global_chunk_idx = 0

        # Parse sections from markdown body if not already separated
        sections_to_process = self._extract_sections(doc)

        for sec_title, sec_content in sections_to_process:
            normalized_body = normalize_text(sec_content)
            if not normalized_body:
                continue

            sec_slug = slugify_section(sec_title)

            # Check if section fits within max chunk size
            if len(normalized_body) <= self.max_chars:
                chunk_text = f"## {sec_title}\n\n{normalized_body}" if not normalized_body.startswith("#") else normalized_body
                chunk_id = f"{doc_id}_{sec_slug}_chk_{global_chunk_idx:03d}"
                c_hash = hashlib.sha256(chunk_text.encode("utf-8")).hexdigest()

                chunks.append(
                    DocumentChunk(
                        chunk_id=chunk_id,
                        doc_id=doc_id,
                        title=title,
                        category=category,
                        section=sec_title,
                        chunk_index=global_chunk_idx,
                        text=chunk_text,
                        token_count=estimate_token_count(chunk_text),
                        content_hash=c_hash,
                        relevance_tags=relevance_tags,
                        metadata={
                            "doc_id": doc_id,
                            "version": version,
                            "section": sec_title,
                        },
                    )
                )
                global_chunk_idx += 1
            else:
                # Split large section into overlapping windows
                sub_chunks = self._split_with_overlap(normalized_body)
                for sub_idx, sub_text in enumerate(sub_chunks):
                    formatted_sub = (
                        f"## {sec_title} (Part {sub_idx + 1})\n\n{sub_text}"
                        if not sub_text.startswith("#")
                        else sub_text
                    )
                    chunk_id = f"{doc_id}_{sec_slug}_chk_{global_chunk_idx:03d}"
                    c_hash = hashlib.sha256(formatted_sub.encode("utf-8")).hexdigest()

                    chunks.append(
                        DocumentChunk(
                            chunk_id=chunk_id,
                            doc_id=doc_id,
                            title=title,
                            category=category,
                            section=sec_title,
                            chunk_index=global_chunk_idx,
                            text=formatted_sub,
                            token_count=estimate_token_count(formatted_sub),
                            content_hash=c_hash,
                            relevance_tags=relevance_tags,
                            metadata={
                                "doc_id": doc_id,
                                "version": version,
                                "section": sec_title,
                                "part": sub_idx + 1,
                            },
                        )
                    )
                    global_chunk_idx += 1

        return chunks

    def _extract_sections(self, doc: GovernanceDocument) -> List[Tuple[str, str]]:
        """
        Extracts markdown sections (e.g. ## 1. Purpose) from doc.content or doc.sections.
        """
        if doc.sections and len(doc.sections) > 1:
            return [(k, v) for k, v in doc.sections.items() if v.strip()]

        content = doc.content
        # Regex split by ## or # headings
        pattern = r"(?m)^(#{1,3}\s+.+)$"
        parts = re.split(pattern, content)

        sections: List[Tuple[str, str]] = []
        current_title = "Overview"
        current_content = ""

        if parts and not parts[0].startswith("#"):
            preamble = parts[0].strip()
            if preamble:
                sections.append(("Preamble", preamble))
            parts = parts[1:]

        i = 0
        while i < len(parts):
            if parts[i].startswith("#"):
                current_title = parts[i].lstrip("#").strip()
                body = parts[i + 1].strip() if i + 1 < len(parts) else ""
                sections.append((current_title, body))
                i += 2
            else:
                i += 1

        return sections if sections else [("Full Document", content)]

    def _split_with_overlap(self, text: str) -> List[str]:
        """
        Splits long text into overlapping chunks using paragraph or sentence boundaries.
        """
        paragraphs = text.split("\n\n")
        chunks: List[str] = []
        current_paras: List[str] = []
        current_len = 0

        for p in paragraphs:
            p_clean = p.strip()
            if not p_clean:
                continue

            p_len = len(p_clean)
            if current_len + p_len + 2 > self.max_chars and current_paras:
                chunks.append("\n\n".join(current_paras))
                # Retain tail for overlap
                overlap_acc: List[str] = []
                overlap_len = 0
                for rev_p in reversed(current_paras):
                    if overlap_len + len(rev_p) < self.overlap_chars:
                        overlap_acc.insert(0, rev_p)
                        overlap_len += len(rev_p) + 2
                    else:
                        break
                current_paras = overlap_acc
                current_len = sum(len(x) + 2 for x in current_paras)

            current_paras.append(p_clean)
            current_len += p_len + 2

        if current_paras:
            chunks.append("\n\n".join(current_paras))

        return chunks if chunks else [text]
