"""
OCR fallback service.
Priority: Tesseract (if installed) > easyocr (pip-only, no binary needed).
Used when a PDF page has no embedded text layer.

Deployment:
  - Set env var  TESSERACT_PATH=/usr/bin  (or wherever tesseract lives)
    to use Tesseract on any machine.
  - If Tesseract is not available, easyocr (pure-pip) is used automatically.
  - Works on Linux, macOS, Windows, and cloud environments without changes.
"""

import io
import os
import re
import shutil
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance

# --- Discover Tesseract from environment or common locations ---
_TESSERACT_CMD = os.environ.get("TESSERACT_PATH")  # explicit override


def _find_tesseract_paths():
    """Build list of candidate Tesseract directories (portable, no hardcoded user)."""
    candidates = [
        r"C:\Program Files\Tesseract-OCR",
        r"C:\Program Files (x86)\Tesseract-OCR",
        "/usr/bin",
        "/usr/local/bin",
    ]
    # Also check user-local installs on Windows (AppData)
    local_app = os.environ.get("LOCALAPPDATA", "")
    if local_app:
        candidates.insert(0, os.path.join(local_app, "Programs", "Tesseract-OCR"))
    return candidates


if _TESSERACT_CMD and os.path.isdir(_TESSERACT_CMD):
    os.environ["PATH"] = _TESSERACT_CMD + os.pathsep + os.environ.get("PATH", "")
elif _TESSERACT_CMD and os.path.isfile(_TESSERACT_CMD):
    pass  # will be set on pytesseract below
else:
    for _tp in _find_tesseract_paths():
        if os.path.isdir(_tp) and _tp not in os.environ.get("PATH", ""):
            os.environ["PATH"] = _tp + os.pathsep + os.environ.get("PATH", "")
            break

# --- Determine which OCR backend is available ---
_TESSERACT_AVAILABLE = shutil.which("tesseract") is not None

if _TESSERACT_AVAILABLE:
    import pytesseract
    # If user gave full binary path, tell pytesseract directly
    if _TESSERACT_CMD and os.path.isfile(_TESSERACT_CMD):
        pytesseract.pytesseract.tesseract_cmd = _TESSERACT_CMD
else:
    pytesseract = None

try:
    import easyocr
    _easyocr_reader = None  # lazy init

    def _get_easyocr_reader():
        global _easyocr_reader
        if _easyocr_reader is None:
            _easyocr_reader = easyocr.Reader(["en"], gpu=False)
        return _easyocr_reader

    _EASYOCR_AVAILABLE = True
except ImportError:
    _EASYOCR_AVAILABLE = False


def _preprocess_for_ocr(image: Image.Image) -> Image.Image:
    """Light preprocessing for better OCR — avoids destroying text."""
    # Convert to grayscale
    if image.mode != "L":
        image = image.convert("L")

    # Upscale small images (OCR works best at ~300 DPI equivalent)
    w, h = image.size
    if w < 1000:
        scale = 1500 / w
        image = image.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

    # Sharpen to counteract blur from image-to-PDF conversion
    image = image.filter(ImageFilter.SHARPEN)

    return image


def _preprocess_variants(image: Image.Image) -> list:
    """
    Generate multiple preprocessing variants for multi-pass OCR.
    Returns list of (label, processed_image) tuples.
    """
    # Base: convert to grayscale
    if image.mode != "L":
        gray = image.convert("L")
    else:
        gray = image.copy()

    # Upscale if small
    w, h = gray.size
    if w < 1200:
        scale = 1800 / w
        gray = gray.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

    variants = []

    # Pass 1: Sharpen only (good for slightly blurry)
    v1 = gray.filter(ImageFilter.SHARPEN)
    variants.append(("sharpen", v1))

    # Pass 2: Contrast boost + sharpen (good for faded/washed out)
    enhancer = ImageEnhance.Contrast(gray)
    v2 = enhancer.enhance(1.5)
    v2 = v2.filter(ImageFilter.SHARPEN)
    variants.append(("contrast+sharpen", v2))

    # Pass 3: Adaptive threshold via stronger contrast (good for very blurry)
    enhancer2 = ImageEnhance.Contrast(gray)
    v3 = enhancer2.enhance(2.0)
    v3 = v3.filter(ImageFilter.SHARPEN)
    v3 = v3.filter(ImageFilter.SHARPEN)  # double sharpen
    variants.append(("high_contrast", v3))

    # Pass 4: Original grayscale (no filters — sometimes cleanest)
    variants.append(("original", gray))

    return variants


def _score_ocr_text(text: str) -> float:
    """
    Score OCR output quality. Higher = better.
    Based on: text length, real word ratio, medical term presence.
    """
    if not text:
        return 0.0

    words = text.split()
    if not words:
        return 0.0

    score = 0.0

    # Length bonus (more text generally = better OCR)
    score += min(len(text), 2000) / 2000 * 30  # max 30 pts

    # Real word ratio (has vowels, 3+ chars)
    real = 0
    for w in words:
        cleaned = re.sub(r"[^a-zA-Z]", "", w)
        if len(cleaned) >= 3 and re.search(r"[aeiouAEIOU]", cleaned):
            real += 1
    word_ratio = real / len(words)
    score += word_ratio * 40  # max 40 pts

    # Medical/bill signal terms
    text_lower = text.lower()
    signals = ["hospital", "patient", "bill", "total", "amount", "rs",
               "room", "charge", "medicine", "admission", "discharge",
               "date", "rent", "equipment", "consultation", "medical",
               "pharmacy", "pharmay", "consumable", "investigation"]
    signal_count = sum(1 for t in signals if t in text_lower)
    score += min(signal_count, 10) * 3  # max 30 pts

    return score


def _run_single_ocr(image: Image.Image) -> str:
    """Run OCR on a single image using best available backend."""
    if _TESSERACT_AVAILABLE:
        return pytesseract.image_to_string(image).strip()
    if _EASYOCR_AVAILABLE:
        return _ocr_with_easyocr(image)
    return ""


def _multi_pass_ocr(image: Image.Image) -> str:
    """
    Run OCR with multiple preprocessing variants and return the best result.
    This significantly improves accuracy for blurry or low-quality scans.
    """
    variants = _preprocess_variants(image)
    best_text = ""
    best_score = -1.0

    for label, processed in variants:
        text = _run_single_ocr(processed)
        score = _score_ocr_text(text)
        if score > best_score:
            best_score = score
            best_text = text

        # Early exit: if score is very high, no need to try more
        if score > 80:
            break

    return best_text


def _ocr_with_easyocr(image: Image.Image) -> str:
    """Run OCR using easyocr on a PIL Image."""
    reader = _get_easyocr_reader()
    img_array = np.array(image.convert("RGB") if image.mode != "RGB" else image)
    results = reader.readtext(img_array, detail=0)
    return "\n".join(results).strip()


def ocr_page_image(image_bytes: bytes) -> str:
    """Run OCR on a PNG image given as bytes (used by extract_pdf for scanned pages)."""
    image = Image.open(io.BytesIO(image_bytes))
    return _multi_pass_ocr(image)


def ocr_image_file(image_path: str) -> str:
    """Run OCR on an image file (jpg, png, jpeg, tiff, bmp)."""
    image = Image.open(image_path)
    return _multi_pass_ocr(image)
    return "[OCR unavailable — install easyocr: pip install easyocr]"
