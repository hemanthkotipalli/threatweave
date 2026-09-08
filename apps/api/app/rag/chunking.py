"""
app/rag/chunking.py
-------------------
Paragraph-aware document chunker for ThreatWeave Phase 12 RAG pipeline.

Splits advisory documents into ~300-500 token chunks with ~15% overlap,
extracting frontmatter metadata and assigning stable deterministic chunk IDs.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class AdvisoryChunk:
    """Represents a single chunk of an advisory document with associated metadata."""
    chunk_id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)
    doc_id: str = ""
    chunk_index: int = 0


def _parse_frontmatter(content: str) -> tuple[dict[str, str], str]:
    """
    Extracts YAML-style frontmatter headers if present at the top of the file.
    Returns (metadata_dict, remaining_body_text).
    """
    metadata: dict[str, str] = {}
    body = content

    pattern = r"^---\s*\n(.*?)\n---\s*\n"
    match = re.match(pattern, content, re.DOTALL)
    if match:
        raw_meta = match.group(1)
        body = content[match.end():]
        for line in raw_meta.splitlines():
            if ":" in line:
                key, val = line.split(":", 1)
                metadata[key.strip()] = val.strip().strip('"').strip("'")

    return metadata, body


def chunk_document(
    file_path: Path | str,
    target_words: int = 300,
    overlap_words: int = 45,
) -> list[AdvisoryChunk]:
    """
    Parses a single Markdown/text advisory file into paragraph-aware chunks.

    :param file_path: Path to the advisory document.
    :param target_words: Target word count per chunk (~300-400 words ≈ 400-500 tokens).
    :param overlap_words: Overlap word count between consecutive chunks (~15%).
    :return: List of AdvisoryChunk objects with stable IDs and complete metadata.
    """
    path = Path(file_path)
    if not path.exists():
        return []

    raw_text = path.read_text(encoding="utf-8")
    doc_id = path.stem
    metadata, body = _parse_frontmatter(raw_text)

    source_title = metadata.get("title", doc_id.replace("_", " ").title())
    source_type = metadata.get("source_type", "Scam-Intel")
    category = metadata.get("category", "general")
    original_reference = metadata.get(
        "original_reference", f"Curated advisory on {source_title}"
    )

    # Split body into natural paragraphs
    raw_paragraphs = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    if not raw_paragraphs:
        return []

    chunks: list[AdvisoryChunk] = []
    current_paragraphs: list[str] = []
    current_word_count = 0
    chunk_idx = 0

    for para in raw_paragraphs:
        words_in_para = len(para.split())
        current_paragraphs.append(para)
        current_word_count += words_in_para

        if current_word_count >= target_words:
            chunk_text = "\n\n".join(current_paragraphs)
            stable_id = f"{doc_id}_{chunk_idx}"
            chunks.append(
                AdvisoryChunk(
                    chunk_id=stable_id,
                    text=chunk_text,
                    metadata={
                        "source_title": source_title,
                        "source_type": source_type,
                        "category": category,
                        "original_reference": original_reference,
                        "doc_id": doc_id,
                        "chunk_index": chunk_idx,
                    },
                    doc_id=doc_id,
                    chunk_index=chunk_idx,
                )
            )
            chunk_idx += 1

            # Keep overlapping tail paragraphs for the next window
            overlap_acc = 0
            retained: list[str] = []
            for p in reversed(current_paragraphs):
                p_words = len(p.split())
                if overlap_acc + p_words <= overlap_words or not retained:
                    retained.insert(0, p)
                    overlap_acc += p_words
                else:
                    break
            current_paragraphs = retained
            current_word_count = sum(len(p.split()) for p in current_paragraphs)

    # Residual chunk
    if current_paragraphs:
        chunk_text = "\n\n".join(current_paragraphs)
        # Avoid creating a tiny duplicate if text was already emitted
        if not chunks or chunk_text != chunks[-1].text:
            stable_id = f"{doc_id}_{chunk_idx}"
            chunks.append(
                AdvisoryChunk(
                    chunk_id=stable_id,
                    text=chunk_text,
                    metadata={
                        "source_title": source_title,
                        "source_type": source_type,
                        "category": category,
                        "original_reference": original_reference,
                        "doc_id": doc_id,
                        "chunk_index": chunk_idx,
                    },
                    doc_id=doc_id,
                    chunk_index=chunk_idx,
                )
            )

    return chunks
