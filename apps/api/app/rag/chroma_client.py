"""
app/rag/chroma_client.py
------------------------
Connection manager for ChromaDB in ThreatWeave Phase 12.

Connects to the containerized ChromaDB service (CHROMA_HOST:CHROMA_PORT)
with automatic fallback to local persistent storage (CHROMA_PATH) for offline resilience.
"""
from __future__ import annotations

import logging
from typing import Any

import chromadb
from chromadb.api import ClientAPI

from app.core.config import settings

logger = logging.getLogger("threatweave-api.rag.chroma_client")

COLLECTION_NAME = "advisories"
_CLIENT_INSTANCE: ClientAPI | None = None
_WARMUP_IN_PROGRESS: bool = False
_RAG_READY: bool = False


def is_rag_ready() -> bool:
    """Returns True if the advisory collection in ChromaDB is initialized and confirmed ready."""
    return _RAG_READY


def is_rag_warming_up() -> bool:
    """Returns True if background collection warmup is currently in progress."""
    return _WARMUP_IN_PROGRESS


def warmup_rag() -> bool:
    """
    Pre-initializes ChromaDB connection and warms the advisory collection.
    Executed in a background thread during application startup to avoid blocking
    the FastAPI lifespan, ensuring /health is immediately responsive.

    :return: True if collection is ready, False if warmup encountered an error.
    """
    global _WARMUP_IN_PROGRESS, _RAG_READY
    _WARMUP_IN_PROGRESS = True
    try:
        col = get_or_create_advisory_collection()
        _ = col.count()
        _RAG_READY = True
        logger.info("ChromaDB background warmup complete: 'advisories' collection ready")
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("ChromaDB background warmup encountered an error (will retry on demand): %s", exc)
        return False
    finally:
        _WARMUP_IN_PROGRESS = False


def get_chroma_client() -> ClientAPI:
    """
    Returns an active ChromaDB client.
    Prefers HTTP Client connecting to the docker-compose service on port 8001.
    Falls back gracefully to PersistentClient if HTTP is unreachable.
    """
    global _CLIENT_INSTANCE
    if _CLIENT_INSTANCE is not None:
        return _CLIENT_INSTANCE

    # Attempt HTTP Client first
    try:
        logger.info(
            "Connecting to ChromaDB HTTP service at %s:%d",
            settings.CHROMA_HOST,
            settings.CHROMA_PORT,
        )
        http_client = chromadb.HttpClient(
            host=settings.CHROMA_HOST,
            port=settings.CHROMA_PORT,
        )
        # Verify connectivity via heartbeat
        http_client.heartbeat()
        logger.info("Successfully connected to ChromaDB HTTP service")
        _CLIENT_INSTANCE = http_client
        return _CLIENT_INSTANCE
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Could not connect to ChromaDB HTTP service (%s:%d): %s. "
            "Falling back to local PersistentClient at path '%s'",
            settings.CHROMA_HOST,
            settings.CHROMA_PORT,
            exc,
            settings.CHROMA_PATH,
        )

    # Fallback to local PersistentClient
    persistent_client = chromadb.PersistentClient(path=settings.CHROMA_PATH)
    _CLIENT_INSTANCE = persistent_client
    return _CLIENT_INSTANCE


def get_or_create_advisory_collection() -> Any:
    """
    Retrieves or creates the 'advisories' collection in ChromaDB.
    Configured with cosine space for distance calculation.
    """
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
