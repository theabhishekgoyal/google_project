"""
Extract text from PDF files page by page.
Uses PyMuPDF (fitz) for text-based PDFs.
Falls back to OCR when a page has no extractable text.
Uses multi-pass OCR to improve accuracy for blurry/scanned documents.
"""

import re
import fitz  # PyMuPDF
from typing import List, Tuple
from app.services.ocr_service import ocr_page_image, _score_ocr_text


def _text_quality_score(text: str) -> float:
    """Quick quality check for embedded PDF text — returns 0-100."""
    return _score_ocr_text(text)


def extract_text_from_pdf(pdf_path: str) -> List[Tuple[int, str]]:
    """
    Extract text from each page of a PDF.
    Returns a list of (page_number, text) tuples. Page numbers are 1-based.
    
    Strategy:
    1. Try PyMuPDF embedded text first.
    2. If text is too short (<50 chars), use multi-pass OCR.
    3. If text quality is low, also try OCR and pick the better result.
    """
    pages = []
    with fitz.open(pdf_path) as doc:
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text").strip()

            if len(text) < 50:
                # No embedded text — OCR is the only option
                pix = page.get_pixmap(dpi=300)
                img_bytes = pix.tobytes("png")
                text = ocr_page_image(img_bytes)
            else:
                # Embedded text exists — check if quality is acceptable
                fitz_score = _text_quality_score(text)
                if fitz_score < 60:
                    # Quality is low — also try OCR and pick the better one
                    pix = page.get_pixmap(dpi=300)
                    img_bytes = pix.tobytes("png")
                    ocr_text = ocr_page_image(img_bytes)
                    ocr_score = _text_quality_score(ocr_text)
                    if ocr_score > fitz_score:
                        text = ocr_text

            pages.append((page_num + 1, text))

    return pages


def extract_full_text(pdf_path: str) -> str:
    """Return all page text concatenated."""
    pages = extract_text_from_pdf(pdf_path)
    return "\n\n".join(text for _, text in pages)
