"""
tests/test_rag_ingest.py
------------------------
Unit tests verifying Phase 12 RAG corpus ingestion and idempotency.
"""
from __future__ import annotations

from app.rag.chroma_client import get_or_create_advisory_collection
from app.rag.ingest import ingest_corpus


class TestRagIngestion:
    def test_corpus_ingestion_idempotency(self):
        """
        Ingesting the corpus twice must result in the exact same chunk count,
        proving that stable IDs prevent duplicate records.
        """
        # Run 1: First ingestion
        result1 = ingest_corpus()
        assert result1["status"] == "ok"
        assert result1["total_files"] == 24
        assert result1["total_chunks"] >= 24
        count1 = result1["collection_count"]

        # Run 2: Second ingestion on identical sources
        result2 = ingest_corpus()
        assert result2["status"] == "ok"
        assert result2["total_files"] == 24
        assert result2["total_chunks"] == result1["total_chunks"]
        count2 = result2["collection_count"]

        # Idempotency assertion
        assert count1 == count2, f"Chunk count changed on re-ingestion: {count1} vs {count2}"

    def test_collection_is_queryable_and_non_empty(self):
        """
        Asserts that the 'advisories' ChromaDB collection is populated
        and supports standard count and query operations.
        """
        collection = get_or_create_advisory_collection()
        count = collection.count()
        assert count >= 24, f"Expected at least 24 chunks in collection, got {count}"

        peek_results = collection.peek(limit=5)
        assert len(peek_results["ids"]) > 0
        assert len(peek_results["documents"]) > 0
        assert len(peek_results["metadatas"]) > 0

        first_meta = peek_results["metadatas"][0]
        assert "source_title" in first_meta
        assert "source_type" in first_meta
        assert first_meta["source_type"] in ["CERT-In", "RBI", "Scam-Intel"]
