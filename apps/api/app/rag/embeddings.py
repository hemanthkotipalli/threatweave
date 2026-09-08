"""
app/rag/embeddings.py
---------------------
Local CPU-only embedding engine for ThreatWeave Phase 12 RAG pipeline.

Uses the all-MiniLM-L6-v2 sentence-transformers model (384 dimensions)
with lazy singleton initialization. No external API keys required.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

logger = logging.getLogger("threatweave-api.rag.embeddings")

_MODEL_NAME = "all-MiniLM-L6-v2"
_CACHED_MODEL: SentenceTransformer | None = None


def get_embedding_model() -> SentenceTransformer:
    """
    Lazily loads and caches the local SentenceTransformer model on CPU.
    Guarantees thread-safe singleton access for embeddings.
    """
    global _CACHED_MODEL
    if _CACHED_MODEL is None:
        from sentence_transformers import SentenceTransformer

        logger.info("Initializing local SentenceTransformer model: %s (CPU)", _MODEL_NAME)
        _CACHED_MODEL = SentenceTransformer(_MODEL_NAME, device="cpu")
    return _CACHED_MODEL


def embed_text(text: str) -> list[float]:
    """
    Computes a 384-dimensional dense vector embedding for a single text string.

    :param text: Text string to embed.
    :return: Vector embedding as a list of floats.
    """
    if not text or not text.strip():
        # Return zero vector of dimension 384 for empty input
        return [0.0] * 384

    model = get_embedding_model()
    embedding = model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
    return embedding.tolist()


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Computes dense vector embeddings for a batch of text strings.

    :param texts: List of text strings to embed.
    :return: List of vector embeddings as lists of floats.
    """
    if not texts:
        return []

    model = get_embedding_model()
    # Batch encode on CPU with normalization for cosine distance
    embeddings = model.encode(texts, batch_size=32, convert_to_numpy=True, normalize_embeddings=True)
    return [e.tolist() for e in embeddings]
