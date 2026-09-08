"""
app/rag/retriever.py
--------------------
Honest similarity-filtered threat intelligence retriever for ThreatWeave Phase 12.

Queries the ChromaDB 'advisories' collection using indicator representations
or search query strings. Enforces strict similarity threshold filtering:
if no advisory clears settings.RAG_SIMILARITY_THRESHOLD, returns an empty list.
Never fabricates or forces low-relevance citations.
"""
from __future__ import annotations

import logging
from typing import Any

from app.core.config import settings
from app.rag.chroma_client import get_or_create_advisory_collection
from app.rag.embeddings import embed_text

logger = logging.getLogger("threatweave-api.rag.retriever")


def _format_indicator_query(
    indicators: list[str],
    finding_texts: list[str] | None = None,
) -> str:
    """
    Transforms a list of indicator identifiers and optional finding descriptions
    into a descriptive query string for dense vector embedding.
    """
    parts: list[str] = []

    if finding_texts:
        for text in finding_texts:
            clean = text.strip()
            if clean:
                parts.append(clean)

    if indicators:
        clean_terms: list[str] = []
        for ind in indicators:
            clean = ind.replace("_", " ").strip()
            if clean:
                clean_terms.append(clean)
        if clean_terms:
            parts.append("Threat indicators: " + ", ".join(clean_terms))

    return " ".join(parts).strip()


def search_advisories(
    query: str,
    top_k: int | None = None,
    threshold: float | None = None,
) -> list[dict[str, Any]]:
    """
    Performs dense vector similarity search against the 'advisories' collection.
    Enforces strict threshold filtering — candidates with similarity below threshold
    are discarded. If none clear the threshold, returns an empty list.

    :param query: Natural language search query or indicator summary text.
    :param top_k: Maximum number of candidates to retrieve (defaults to settings.RAG_TOP_K).
    :param threshold: Minimum similarity threshold (defaults to settings.RAG_SIMILARITY_THRESHOLD).
    :return: List of filtered advisory citation dicts sorted by descending similarity score.
    """
    if not query or not query.strip():
        logger.debug("search_advisories called with empty query string")
        return []

    effective_k = top_k if top_k is not None else settings.RAG_TOP_K
    effective_threshold = threshold if threshold is not None else settings.RAG_SIMILARITY_THRESHOLD

    try:
        collection = get_or_create_advisory_collection()
        if collection.count() == 0:
            logger.warning("Advisories collection is empty. Run scripts/ingest_corpus.py first.")
            return []

        query_embedding = embed_text(query)

        # Query ChromaDB using vector embedding
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(effective_k, collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        citations: list[dict[str, Any]] = []
        for doc, meta, dist in zip(documents, metadatas, distances):
            # For cosine space in ChromaDB: similarity = 1.0 - distance
            similarity = round(max(0.0, min(1.0, 1.0 - float(dist))), 4)

            # Strict threshold filtering: DO NOT return or force low-similarity results
            if similarity >= effective_threshold:
                citations.append({
                    "chunk_text": doc,
                    "source_title": meta.get("source_title", "Unknown Advisory"),
                    "source_type": meta.get("source_type", "Scam-Intel"),
                    "similarity_score": similarity,
                    "category": meta.get("category", "general"),
                    "url": meta.get("original_reference", None),
                })
            else:
                logger.debug(
                    "Filtered out candidate '%s' with similarity %.4f below threshold %.4f",
                    meta.get("source_title", "Unknown"),
                    similarity,
                    effective_threshold,
                )

        # Sort descending by similarity score
        citations.sort(key=lambda c: c["similarity_score"], reverse=True)
        return citations

    except Exception:
        logger.exception("Error during ChromaDB advisory search")
        return []


def retrieve_relevant_advisories(
    indicators: list[str],
    finding_texts: list[str] | None = None,
    top_k: int = 5,
    threshold: float | None = None,
) -> list[dict[str, Any]]:
    """
    Builds a query from candidate threat indicator strings and optional finding summaries,
    queries ChromaDB, and returns relevant advisory citations strictly clearing the similarity threshold.

    :param indicators: List of indicator strings discovered across agent findings.
    :param finding_texts: Optional summary statements or descriptions from specialist findings.
    :param top_k: Maximum number of citations to return.
    :param threshold: Optional similarity threshold override.
    :return: Filtered list of citations or empty list if none clear threshold.
    """
    if not indicators and not finding_texts:
        return []

    query_text = _format_indicator_query(indicators, finding_texts=finding_texts)
    return search_advisories(query=query_text, top_k=top_k, threshold=threshold)

