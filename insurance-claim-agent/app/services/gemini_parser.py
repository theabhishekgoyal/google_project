"""
Gemini-based PDF/image bill parser.
Sends the document directly to Gemini Vision API for structured extraction.
Falls back gracefully if the API key is missing or the call fails.
"""

import os
import json
import logging
import time
from typing import Optional

from app.schemas import BillFacts, BillLineItem

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

_MODELS = ["gemini-2.5-flash"]

_GEMINI_AVAILABLE = False
_client = None

try:
    from google import genai
    from google.genai import types
    if GEMINI_API_KEY:
        _client = genai.Client(api_key=GEMINI_API_KEY)
        _GEMINI_AVAILABLE = True
        logger.info("Gemini API client initialized successfully.")
    else:
        logger.warning("GEMINI_API_KEY not set — Gemini parser disabled.")
except ImportError:
    logger.warning("google-genai not installed — Gemini parser disabled.")


_EXTRACTION_PROMPT = """\
You are an expert hospital bill parser. Extract the following structured data from this hospital bill document.

Return a JSON object with these exact fields:
{
  "patient_name": "full name or null",
  "hospital_name": "hospital name or null",
  "admission_date": "DD/MM/YYYY or DD-MM-YYYY format or null",
  "discharge_date": "DD/MM/YYYY or DD-MM-YYYY format or null",
  "total_amount": numeric total bill amount or null,
  "room_rent_per_day": numeric room rent per day or null,
  "procedure_keywords": ["list", "of", "procedures"],
  "diagnosis_keywords": ["list", "of", "diagnoses"],
  "line_items": [
    {
      "description": "service description",
      "amount": numeric amount,
      "category": "one of: room, surgery, medicine, diagnostic, consultation, icu, nursing, anesthesia, other"
    }
  ]
}

Category classification rules:
- "room": room rent, bed charges, ward charges, accommodation, boarding
- "surgery": surgery, operation, surgeon fees, OT charges, procedure fees
- "medicine": medicines, drugs, pharmacy, injections, IV fluids
- "diagnostic": diagnostic tests, X-ray, MRI, CT scan, ultrasound, blood tests, pathology, lab, investigations, ECG
- "consultation": doctor consultation, physician visits, specialist fees
- "icu": ICU charges, intensive care, critical care
- "nursing": nursing charges, nurse fees, attendant
- "anesthesia": anesthesia, anaesthesia charges
- "other": anything that doesn't fit above categories

Important:
- Extract ALL line items from the bill, not just the first few.
- Amounts should be numeric (no currency symbols).
- Dates should be in DD/MM/YYYY or DD-MM-YYYY format.
- If room rent per day is not explicitly stated, set it to null.
- For total_amount, use the final/net/grand total, not subtotals.
- Return ONLY the JSON object, no extra text.
"""


def _get_mime_type(file_path: str) -> str:
    """Determine MIME type from file extension."""
    ext = os.path.splitext(file_path)[1].lower()
    mime_map = {
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".tiff": "image/tiff",
        ".bmp": "image/bmp",
        ".webp": "image/webp",
    }
    return mime_map.get(ext, "application/pdf")


def parse_bill_with_gemini(file_path: str) -> Optional[BillFacts]:
    """
    Parse a hospital bill PDF/image using Gemini Vision API.
    Returns BillFacts on success, None on failure.
    """
    if not _GEMINI_AVAILABLE or not _client:
        logger.info("Gemini not available, skipping.")
        return None

    try:
        with open(file_path, "rb") as f:
            file_bytes = f.read()

        mime_type = _get_mime_type(file_path)

        # Try models in order: prefer newer, fall back to older
        last_err = None
        response = None
        for model_name in _MODELS:
            for attempt in range(2):
                try:
                    response = _client.models.generate_content(
                        model=model_name,
                        contents=[
                            types.Part.from_bytes(data=file_bytes, mime_type=mime_type),
                            _EXTRACTION_PROMPT,
                        ],
                    )
                    break
                except Exception as e:
                    last_err = e
                    err_str = str(e)
                    # Retry once for per-minute rate limits
                    if "429" in err_str and "PerMinute" in err_str and attempt == 0:
                        logger.info(f"Gemini rate limited on {model_name}, retrying in 10s...")
                        time.sleep(10)
                        continue
                    break  # daily quota or other error — try next model
            if response is not None:
                break
        
        if response is None:
            if last_err:
                raise last_err
            return None

        raw_response = response.text.strip()
        # Strip markdown code fences if present
        if raw_response.startswith("```"):
            raw_response = raw_response.split("\n", 1)[1]
            if raw_response.endswith("```"):
                raw_response = raw_response[:-3].strip()

        data = json.loads(raw_response)
        return _convert_to_bill_facts(data, raw_response)

    except json.JSONDecodeError as e:
        logger.warning(f"Gemini returned invalid JSON: {e}")
        return None
    except Exception as e:
        logger.warning(f"Gemini parsing failed: {e}")
        return None


def _convert_to_bill_facts(data: dict, raw_json: str) -> BillFacts:
    """Convert Gemini JSON response to BillFacts model."""
    line_items = []
    for item in data.get("line_items", []):
        desc = item.get("description", "").strip()
        amt = item.get("amount")
        cat = item.get("category", "other").lower()
        if desc and amt is not None:
            try:
                amt = float(amt)
            except (ValueError, TypeError):
                continue
            if amt >= 50:
                line_items.append(BillLineItem(
                    description=desc,
                    amount=amt,
                    category=cat if cat in {
                        "room", "surgery", "medicine", "diagnostic",
                        "consultation", "icu", "nursing", "anesthesia", "other"
                    } else "other",
                ))

    room_rent = data.get("room_rent_per_day")
    if room_rent is not None:
        try:
            room_rent = float(room_rent)
        except (ValueError, TypeError):
            room_rent = None

    total_amount = data.get("total_amount")
    if total_amount is not None:
        try:
            total_amount = float(total_amount)
        except (ValueError, TypeError):
            total_amount = None

    return BillFacts(
        patient_name=data.get("patient_name"),
        hospital_name=data.get("hospital_name"),
        admission_date=data.get("admission_date"),
        discharge_date=data.get("discharge_date"),
        total_amount=total_amount,
        room_rent_per_day=room_rent,
        procedure_keywords=data.get("procedure_keywords", []),
        diagnosis_keywords=data.get("diagnosis_keywords", []),
        line_items=line_items,
        ocr_confidence="high",  # Gemini parsing is always high confidence
        raw_text=raw_json,
    )
