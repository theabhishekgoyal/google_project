"""
Text normalization and NLP preprocessing utilities.
Cleans raw extracted text for downstream NLP and rule processing.
"""

import re


# Common stop words for insurance domain
INSURANCE_STOP_WORDS = {
    "the", "is", "at", "which", "on", "a", "an", "and", "or", "but",
    "in", "of", "to", "for", "with", "by", "from", "as", "be", "this",
    "that", "it", "are", "was", "were", "has", "have", "had", "been",
    "will", "shall", "may", "can", "would", "should", "could",
}


def normalize_text(text: str) -> str:
    """Clean and normalize extracted text."""
    # Replace multiple whitespace/newlines with single space
    text = re.sub(r"\s+", " ", text)
    # Remove non-printable characters but keep common currency symbols
    text = re.sub(r"[^\x20-\x7E\n₹]", "", text)
    # Fix common OCR errors
    text = _fix_ocr_artifacts(text)
    # Strip leading/trailing whitespace
    text = text.strip()
    return text


def _fix_ocr_artifacts(text: str) -> str:
    """Fix common OCR misreads."""
    # Common OCR substitutions
    replacements = {
        "|": "l",  # pipe -> l
        "0": "O",  # only in clearly alphabetic context (skip for numbers)
    }
    # Fix £ misread: OCR sometimes reads "8" as "£" (e.g. "£5,000" should be "85,000")
    text = re.sub(r"£(\d)", r"8\1", text)
    # Fix broken amounts like "Rs , 5,000" -> "Rs. 5,000"
    text = re.sub(r"Rs\s*,\s*", "Rs. ", text)
    # Fix "1NR" -> "INR"
    text = re.sub(r"1NR", "INR", text)
    # Fix spacing in amounts "5, 000" -> "5,000"
    text = re.sub(r"(\d),\s+(\d)", r"\1,\2", text)
    return text


def preprocess_for_tfidf(text: str) -> str:
    """
    Preprocess text specifically for TF-IDF vectorization.
    Lowercases, removes punctuation, removes stop words.
    """
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    words = text.split()
    words = [w for w in words if w not in INSURANCE_STOP_WORDS and len(w) > 1]
    return " ".join(words)


def normalize_amount(text: str) -> float | None:
    """
    Try to extract a numeric amount from a string like 'Rs. 45,000' or '₹ 12000'.
    Returns float or None.
    """
    cleaned = re.sub(r"[^\d.]", "", text)
    if cleaned:
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None


def extract_all_amounts(text: str) -> list[float]:
    """Extract all monetary amounts from text, sorted descending."""
    pattern = r"(?:rs\.?|inr|₹)\s*([\d,]+\.?\d*)"
    amounts = []
    for match in re.finditer(pattern, text, re.IGNORECASE):
        val = normalize_amount(match.group(1))
        if val and val >= 100:
            amounts.append(val)
    # Also catch standalone large numbers
    for match in re.finditer(r"\b(\d{1,2},\d{2},\d{3}(?:\.\d{2})?)\b", text):
        val = normalize_amount(match.group(1))
        if val and val >= 100:
            amounts.append(val)
    return sorted(set(amounts), reverse=True)
