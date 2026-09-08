"""
app/rag/ingest.py
-----------------
Idempotent corpus ingestion engine for ThreatWeave Phase 12.

Reads curated advisory documents from app/rag/sources/, chunks them,
embeds them via local sentence-transformers, and upserts them into ChromaDB.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from app.rag.chroma_client import get_or_create_advisory_collection
from app.rag.chunking import AdvisoryChunk, chunk_document
from app.rag.embeddings import embed_texts

logger = logging.getLogger("threatweave-api.rag.ingest")

DEFAULT_SOURCES_DIR = Path(__file__).resolve().parent / "sources"


def ingest_corpus(sources_dir: Path | str | None = None) -> dict[str, Any]:
    """
    Scans the sources directory for all Markdown files, chunks each document,
    generates embeddings, and upserts them into ChromaDB.

    Idempotent: Uses deterministic chunk IDs based on document name and chunk index.
    Re-running this function on the same corpus results in identical chunk count.

    :param sources_dir: Path to directory containing advisory documents.
    :return: Summary dictionary with file and chunk counts.
    """
    root_path = Path(sources_dir) if sources_dir else DEFAULT_SOURCES_DIR
    if not root_path.exists():
        logger.warning("Sources directory does not exist: %s", root_path)
        return {"total_files": 0, "total_chunks": 0, "status": "empty"}

    doc_files = sorted(root_path.glob("**/*.md"))
    logger.info("Found %d advisory source files in %s", len(doc_files), root_path)

    all_chunks: list[AdvisoryChunk] = []
    for f in doc_files:
        chunks = chunk_document(f)
        all_chunks.extend(chunks)

    if not all_chunks:
        logger.warning("No chunks generated from source files in %s", root_path)
        return {"total_files": len(doc_files), "total_chunks": 0, "status": "no_chunks"}

    logger.info("Generated %d chunks across %d files. Embedding...", len(all_chunks), len(doc_files))

    chunk_texts = [c.text for c in all_chunks]
    chunk_ids = [c.chunk_id for c in all_chunks]
    chunk_metadatas = [c.metadata for c in all_chunks]

    embeddings = embed_texts(chunk_texts)

    collection = get_or_create_advisory_collection()
    logger.info("Upserting %d chunks into ChromaDB collection '%s'...", len(chunk_ids), collection.name)

    # Upsert in batches of 64
    batch_size = 64
    for i in range(0, len(chunk_ids), batch_size):
        b_ids = chunk_ids[i : i + batch_size]
        b_embs = embeddings[i : i + batch_size]
        b_docs = chunk_texts[i : i + batch_size]
        b_metas = chunk_metadatas[i : i + batch_size]

        collection.upsert(
            ids=b_ids,
            embeddings=b_embs,
            documents=b_docs,
            metadatas=b_metas,
        )

    final_count = collection.count()
    logger.info("Ingestion completed successfully. ChromaDB collection total count: %d", final_count)

    return {
        "total_files": len(doc_files),
        "total_chunks": len(all_chunks),
        "collection_count": final_count,
        "status": "ok",
    }
