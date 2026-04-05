"""
Chunk a policy document into searchable clause-level segments.
Each chunk retains its page number for citation.
"""

import re
from typing import List, Tuple
from app.schemas import PolicyChunk
from app.services.normalize import normalize_text


def chunk_policy_pages(pages: List[Tuple[int, str]], max_chunk_len: int = 500) -> List[PolicyChunk]:
    """
    Split policy pages into smaller chunks.
    Each chunk keeps its source page number.
    Splits on paragraph boundaries (double newline or numbered sections).
    """
    chunks: List[PolicyChunk] = []

    for page_num, raw_text in pages:
        text = normalize_text(raw_text)
        if not text:
            continue

        # Split on common section/paragraph markers
        paragraphs = re.split(r"(?:\n\s*\n|\n(?=\d+[\.\)])|(?=Section\s+\d))", raw_text)

        current_chunk = ""
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if len(current_chunk) + len(para) < max_chunk_len:
                current_chunk += " " + para
            else:
                if current_chunk.strip():
                    chunks.append(PolicyChunk(
                        text=normalize_text(current_chunk),
                        page=page_num,
                        heading=_try_extract_heading(current_chunk),
                    ))
                current_chunk = para

        # Flush remaining
        if current_chunk.strip():
            chunks.append(PolicyChunk(
                text=normalize_text(current_chunk),
                page=page_num,
                heading=_try_extract_heading(current_chunk),
            ))

    return chunks


def _try_extract_heading(text: str) -> str | None:
    """Try to extract a heading from the beginning of a chunk."""
    match = re.match(r"^((?:Section|Clause|Article)\s*\d+[\.\:]\s*[^\n]{5,60})", text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    # Try numbered heading like "4.2 Room Rent"
    match = re.match(r"^(\d+\.?\d*\s+[A-Z][^\n]{3,60})", text)
    if match:
        return match.group(1).strip()
    return None
