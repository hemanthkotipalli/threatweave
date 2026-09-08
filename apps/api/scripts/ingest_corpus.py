"""
scripts/ingest_corpus.py
------------------------
CLI script to ingest and embed curated threat intelligence advisories into ChromaDB.

Usage:
    cd apps/api
    python scripts/ingest_corpus.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure api directory is in python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.rag.ingest import ingest_corpus


def main():
    print("================================================================")
    print(" ThreatWeave Phase 12: Ingesting Threat Intelligence Advisories ")
    print("================================================================")

    result = ingest_corpus()

    print("\n--- Ingestion Summary ---")
    print(f"Status:            {result.get('status')}")
    print(f"Source Files Read: {result.get('total_files')}")
    print(f"Chunks Processed:  {result.get('total_chunks')}")
    print(f"ChromaDB Chunks:   {result.get('collection_count')}")
    print("================================================================")
    print("Idempotent ingestion complete.")


if __name__ == "__main__":
    main()
