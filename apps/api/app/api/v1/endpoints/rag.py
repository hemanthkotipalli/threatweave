"""
app/api/v1/endpoints/rag.py
---------------------------
Ad-hoc search and debugging endpoint for ThreatWeave Phase 12 RAG pipeline.
"""
from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Query

from app.core.config import settings
from app.rag.retriever import search_advisories
from app.schemas.rag import RagSearchItemResponse, RagSearchResponse

router = APIRouter()
logger = logging.getLogger("threatweave-api.endpoints.rag")


@router.get("/search", response_model=RagSearchResponse)
def search_threat_advisories(
    q: Annotated[str, Query(description="Threat description, indicator keywords, or query string", min_length=1)],
    top_k: Annotated[int, Query(ge=1, le=20)] = 5,
    threshold: Annotated[float | None, Query(ge=0.0, le=1.0)] = None,
) -> RagSearchResponse:
    """
    Performs vector similarity search against curated CERT-In, RBI, and Scam-Intel advisories.
    Applies strict similarity threshold filtering (default 0.55).
    Returns an empty list if no advisories clear the threshold.
    """
    effective_threshold = threshold if threshold is not None else settings.RAG_SIMILARITY_THRESHOLD
    logger.info("Executing RAG search for query: '%s' (top_k=%d, threshold=%.2f)", q, top_k, effective_threshold)

    citations = search_advisories(query=q, top_k=top_k, threshold=effective_threshold)

    results = [
        RagSearchItemResponse(
            source_title=c["source_title"],
            source_type=c["source_type"],
            chunk_text=c["chunk_text"],
            similarity_score=c["similarity_score"],
            category=c.get("category"),
            url=c.get("url"),
        )
        for c in citations
    ]

    return RagSearchResponse(
        query=q,
        threshold=effective_threshold,
        total_results=len(results),
        results=results,
    )
