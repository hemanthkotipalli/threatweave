"""
tests/test_rag_retriever.py
---------------------------
Unit tests for ThreatWeave Phase 12 advisory retriever.
Validates honest similarity threshold filtering, relevant citation retrieval,
and zero low-relevance fabrication.
"""
from __future__ import annotations

from app.core.config import settings
from app.rag.retriever import retrieve_relevant_advisories, search_advisories


class TestRagRetriever:
    def test_on_topic_query_returns_relevant_advisories_clearing_threshold(self):
        """
        Querying with realistic on-topic threat indicators and findings must return
        at least one advisory citation with similarity_score >= settings.RAG_SIMILARITY_THRESHOLD.
        Verifies that the returned chunk is genuinely relevant by asserting on category/source_type.
        """
        # Scenario: Banking phishing campaign with credential harvesting
        indicators = ["credential_request", "urgency_language", "lookalike_domain"]
        finding_texts = [
            "Phishing campaign impersonating major commercial bank with fraudulent login portal and credential harvesting lure"
        ]

        results = retrieve_relevant_advisories(
            indicators=indicators,
            finding_texts=finding_texts,
            top_k=5,
            threshold=settings.RAG_SIMILARITY_THRESHOLD,
        )

        assert len(results) >= 1, "Expected at least one advisory to clear threshold for banking phishing"
        top_result = results[0]

        assert top_result["similarity_score"] >= settings.RAG_SIMILARITY_THRESHOLD
        assert top_result["source_type"] in ["CERT-In", "RBI", "Scam-Intel"]
        assert top_result["category"] in ["phishing", "banking_fraud", "credential_harvesting", "identity_theft"]
        assert "source_title" in top_result
        assert "chunk_text" in top_result
        assert len(top_result["chunk_text"]) > 50

    def test_upi_fraud_indicators_return_rbi_upi_advisory(self):
        """
        Querying with UPI-specific indicators returns RBI advisory covering UPI collect request fraud.
        """
        indicators = ["qr_upi_deeplink_suspicious", "unauthorized_debit", "credential_request"]
        finding_texts = [
            "Fraudulent UPI collect request lure claiming recipient must enter UPI PIN to receive refund payment"
        ]

        results = retrieve_relevant_advisories(
            indicators=indicators,
            finding_texts=finding_texts,
            top_k=3,
        )

        assert len(results) >= 1
        top_result = results[0]
        assert top_result["similarity_score"] >= settings.RAG_SIMILARITY_THRESHOLD
        # Assert semantic relevance to UPI fraud
        matched_titles = [r["source_title"] for r in results]
        assert any("UPI" in t or "QR" in t for t in matched_titles)

    def test_deliberately_irrelevant_query_returns_empty_list(self):
        """
        CRITICAL HONESTY REQUIREMENT:
        A query designed to have no relevance to cyber threat advisories (e.g. nonsense string)
        MUST return an empty list [], NOT a forced or fabricated low-relevance citation.
        """
        nonsense_query = "xyzabc123nonsense random banana purple galaxy 987654"
        results = search_advisories(query=nonsense_query, top_k=5)

        assert results == [], f"Expected empty list for irrelevant query, but got {len(results)} results: {results}"

    def test_strict_threshold_filtering_never_leaks_below_threshold_results(self):
        """
        No result with similarity_score < settings.RAG_SIMILARITY_THRESHOLD must ever be returned.
        Tested across diverse queries.
        """
        test_queries = [
            "weather forecast for tomorrow morning in mumbai",
            "recipe for homemade chocolate chip cookies",
            "quantum mechanics wave particle duality",
            "gardening tips for indoor tomato plants",
        ]

        for q in test_queries:
            results = search_advisories(query=q, top_k=5)
            for r in results:
                assert r["similarity_score"] >= settings.RAG_SIMILARITY_THRESHOLD, (
                    f"Result leaked below threshold {settings.RAG_SIMILARITY_THRESHOLD}: "
                    f"score={r['similarity_score']} title='{r['source_title']}'"
                )
