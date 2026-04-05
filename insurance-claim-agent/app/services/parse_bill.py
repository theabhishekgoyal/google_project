"""
Parse hospital bill text and extract structured claim facts.
Uses regex and keyword matching for the MVP.
"""

import re
from typing import List
from dateutil import parser as dateparser
from app.schemas import BillFacts, BillLineItem
from app.services.normalize import normalize_text, normalize_amount


# Category mapping keywords
CATEGORY_KEYWORDS = {
    "room": ["room", "bed", "ward", "accommodation", "boarding"],
    "surgery": ["surgery", "operation", "surgeon", "procedure", "ot charge", "operation theatre"],
    "medicine": ["medicine", "drug", "pharmacy", "pharma", "injection", "iv fluid", "medication"],
    "diagnostic": ["diagnostic", "investigation", "test", "x-ray", "xray", "mri", "ct scan", "ultrasound", "blood test",
                    "pathology", "lab", "radiology", "ecg", "echo"],
    "consultation": ["consultation", "doctor", "visit", "physician", "specialist"],
    "icu": ["icu", "intensive care", "critical care", "ccunit"],
    "nursing": ["nursing", "nurse", "attendant"],
    "anesthesia": ["anesthesia", "anaesthesia", "anesthetist"],
}


# Common medical procedure keywords (lowercase)
PROCEDURE_KEYWORDS = [
    "surgery", "operation", "appendectomy", "angioplasty", "bypass",
    "dialysis", "chemotherapy", "radiation", "transplant", "cesarean",
    "endoscopy", "biopsy", "arthroscopy", "laparoscopy", "consultation",
    "icu", "ventilator", "physiotherapy", "dental", "cosmetic",
    "fertility", "ivf", "ayurvedic", "weight loss", "liposuction",
]

DIAGNOSIS_KEYWORDS = [
    "diabetes", "hypertension", "asthma", "thyroid", "heart disease",
    "kidney disease", "cancer", "tuberculosis", "hepatitis", "stroke",
    "pneumonia", "fracture", "infection", "appendicitis", "hernia",
]


def extract_bill_facts(raw_text: str) -> BillFacts:
    """Extract structured facts from bill text."""
    text = normalize_text(raw_text)
    text_lower = text.lower()

    patient_name = _extract_patient_name(text)
    hospital_name = _extract_hospital_name(text)
    admission_date = _extract_date(text, "admission")
    discharge_date = _extract_date(text, "discharge")

    # Fallback: if no labeled admission/discharge, find any date as bill date
    if not admission_date:
        admission_date = _extract_any_date(text)

    total_amount = _extract_total_amount(text)
    room_rent = _extract_room_rent(text)
    procedures = _extract_keywords(text_lower, PROCEDURE_KEYWORDS)
    diagnoses = _extract_keywords(text_lower, DIAGNOSIS_KEYWORDS)
    line_items = _extract_line_items(text, total_amount, raw_text=raw_text)
    ocr_confidence = _assess_ocr_quality(text)

    # Fallback room rent: derive from ROOM line item and length of stay
    if not room_rent and admission_date and discharge_date:
        room_item = next((li for li in line_items if li.category == "room"), None)
        if room_item:
            days = _days_between(admission_date, discharge_date)
            if days and days > 0:
                room_rent = round(room_item.amount / days, 2)

    # Infer unreadable line items: if sum of items < total, add remainder as "Other charges (OCR unreadable)"
    if total_amount and line_items:
        items_sum = sum(li.amount for li in line_items)
        gap = total_amount - items_sum
        if gap > 100:  # significant missing amount
            line_items.append(BillLineItem(
                description="Other Charges (OCR unreadable)",
                amount=round(gap, 2),
                category="other",
            ))

    return BillFacts(
        patient_name=patient_name,
        hospital_name=hospital_name,
        admission_date=admission_date,
        discharge_date=discharge_date,
        total_amount=total_amount,
        room_rent_per_day=room_rent,
        procedure_keywords=procedures,
        diagnosis_keywords=diagnoses,
        line_items=line_items,
        ocr_confidence=ocr_confidence,
        raw_text=text,
    )


def _extract_patient_name(text: str) -> str | None:
    patterns = [
        r"patient\s*name\s*[:\-]?\s*([A-Za-z\s\.]+)",
        r"name\s*of\s*(?:the\s*)?patient\s*[:\-]?\s*([A-Za-z\s\.]+)",
        r"patient\s*[:\-]\s*([A-Za-z\s\.]+)",
        r"insured\s*(?:name|person)\s*[:\-]?\s*([A-Za-z\s\.]+)",
        # "PATIENT DETAILS ... <numbers> ... Name Surname Bill No" (Apollo format)
        r"patient\s*details.*?\d{5,}\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})\s+(?:bill|age|plot|flat|address)",
        # Blurry OCR fallback: "Name Surname Bill No." (2-4 words before Bill No, allowing middle initials)
        r"([A-Z][a-z]{2,}(?:\s+[A-Z][a-z]*){1,3})\s+Bill\s*No",
        r"name\s*[:\-]\s*(?:mr\.?|mrs\.?|ms\.?)\s*([A-Za-z\s\.]+)",
        r"mr\.?\s+([A-Za-z\s]+)",
        r"mrs\.?\s+([A-Za-z\s]+)",
        r"ms\.?\s+([A-Za-z\s]+)",
    ]
    # Words that should stop the name capture
    _STOP = r"\s+(?:hospital|clinic|medical|age|gender|date|room|ward|bed|uhid|UHID|contact|phone|mobile|address|s/o|d/o|w/o|invoice|bill|receipt|description|quantity|unit|amount|charges|total|rate).*"
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            name = re.sub(_STOP, "", name, flags=re.IGNORECASE).strip()
            # Trim anything after a newline
            name = name.split("\n")[0].strip()
            # Indian names: keep first 2-4 words (names are rarely >4 words)
            words = name.split()
            if len(words) > 4:
                words = words[:4]
            # Remove trailing words that look like OCR noise (short, no capitals)
            while words and (len(words[-1]) <= 3 or not words[-1][0].isupper()):
                words.pop()
            name = " ".join(words).strip()
            if 2 < len(name) < 50:
                return name
    return None


def _extract_hospital_name(text: str) -> str | None:
    patterns = [
        r"hospital\s*name\s*[:\-]?\s*([A-Za-z\s\.&]+)",
        r"([A-Za-z][A-Za-z\s\.&]*hospital[s]?)",
        r"([A-Za-z\s\.&]+medical\s+cent[re]+)",
        r"([A-Za-z\s\.&]+clinic)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            # Fix common OCR garbles: "A lo" -> "Apollo", "Apo lo" -> "Apollo"
            name = re.sub(r"\bA\s*(?:po)?\s*lo\b", "Apollo", name, flags=re.IGNORECASE)
            # Clean up: if a known hospital brand appears, take from that point
            # e.g. "haderabacitapollohospitak com i Apollo Hospitals" -> "Apollo Hospitals"
            brand_match = re.search(
                r"\b((?:apollo|fortis|max|medanta|aiims|manipal|narayana)\s+\S+(?:\s+\S+){0,3})",
                name, re.IGNORECASE
            )
            if brand_match:
                name = brand_match.group(1).strip()
            if 3 < len(name) < 80:
                return name
    return None


def _extract_date(text: str, label: str) -> str | None:
    # Date patterns: numeric (15-06-2025) and alpha-month (15-Jun-2025)
    _DATE_NUM = r"[\d]{1,2}[\-/\.]\s?[\d]{1,2}[\-/\.]\s?[\d]{2,4}"
    _DATE_ALPHA = r"[\d]{1,2}[\-/\.]?\s?(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\-/\.]?\s?[\d]{2,4}"
    _DATE = rf"(?:{_DATE_ALPHA}|{_DATE_NUM})"

    search_patterns = [
        # Standard: "Admission Date: 10-Jun-2023"
        rf"{label}\s*(?:date)?\s*[:\-]?\s*({_DATE})",
        rf"date\s*of\s*{label}\s*[:\-]?\s*({_DATE})",
        # "Admission Dt./Time" or "Admission Dt/Time" (common hospital format)
        rf"{label}\s*(?:dt|d[tl])\s*[\./]?\s*(?:time)?\s*[:\-]?\s*({_DATE})",
        # OCR garbled "Dt." -> "OL" or "D1": "Admission OL Time : 10-Jun-2023"
        rf"{label}\s*[A-Z]{{1,2}}\s*[\./]?\s*(?:time)?\s*[:\-]?\s*({_DATE})",
    ]
    # Handle OCR garbles of "Discharge": Discahrge, Discahige, Dischage, etc.
    if label.lower().startswith("discharg"):
        search_patterns.append(rf"dis[ck]?[a-z]{{0,5}}ge\s*(?:dt|d[tl])?\s*[\./]?\s*(?:time)?\s*[:\-]?\s*({_DATE})")

    # DOA / DOD abbreviations
    abbrev = "doa" if label.lower().startswith("admis") else "dod"
    search_patterns.append(rf"{abbrev}\s*[:\-]?\s*({_DATE})")

    for pat in search_patterns:
        match = re.search(pat, text, re.IGNORECASE)
        if match:
            date_str = match.group(1).strip()
            date_str = re.sub(r"\s+", "-", date_str)
            return date_str
    return None


def _extract_any_date(text: str) -> str | None:
    """Fallback: find any date-like pattern in the text (for invoices without admission/discharge labels)."""
    patterns = [
        # "Date: 2/6/2022" or "Date 38 2/6/2022" (OCR noise before the actual date)
        r"\bdate\b[^\d]{0,15}(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})",
        # "15-Jun-2025" standalone alpha-month date
        r"(\d{1,2}[\-/]?\s?(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\-/]?\s?\d{2,4})",
        # Generic d/m/y or d-m-y
        r"(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{4})",
    ]
    for pat in patterns:
        match = re.search(pat, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def _extract_total_amount(text: str) -> float | None:
    # Priority order: NET/GRAND first (final amount), then generic total, then Rs. amounts
    priority_patterns = [
        r"net\s*(?:total)?\s*(?:amount|payable)\s*[:\-]?\s*(?:rs\.?|inr|₹)?\s*([\d,]+\.?\d*)",
        r"grand\s*total\s*[:\-]?\s*(?:rs\.?|inr|₹)?\s*([\d,]+\.?\d*)",
        r"net\s*total\s*[:\-]?\s*(?:rs\.?|inr|₹)?\s*([\d,]+\.?\d*)",
        r"total\s*(?:amount|bill|charge)[s]?\s*[:\-]?\s*(?:rs\.?|inr|₹)?\s*([\d,]+\.?\d*)",
    ]
    # Check priority patterns in order — return first match ≥ 100
    for pattern in priority_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            val = normalize_amount(match.group(1))
            if val and val >= 100:
                return val

    # Fallback: any "Rs. <amount>" — pick the largest
    fallback_patterns = [
        r"total\s*[:\-]?\s*(?:rs\.?|inr|₹)?\s*([\d,]+\.?\d*)",
        r"(?:rs\.?|inr|₹)\s*\.?\s*([\d,]{4,}(?:\.\d{1,2})?)",
        r"amount\s*(?:payable|paid|due)?\s*[:\-]?\s*(?:rs\.?|inr|₹)?\s*([\d,]+\.?\d*)",
    ]
    best = None
    for pattern in fallback_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            val = normalize_amount(match.group(1))
            if val and val >= 100:
                if best is None or val > best:
                    best = val
    return best


def _extract_room_rent(text: str) -> float | None:
    patterns = [
        # "Room Rent per day: Rs. 8,000" or "room rent: 5000"
        r"room\s*rent\s*(?:per\s*day)?\s*[:\-]?\s*(?:rs\.?|inr|₹)?\s*\.?\s*([\d,]+\.?\d*)",
        # "ROOM RENT" followed (possibly with noise) by "Rs. X"
        r"room\s*rent[^\d]{0,30}(?:rs\.?|inr|₹)\s*\.?\s*([\d,]+\.?\d*)",
        # "5 days × Rs. 8,000/day" → extract the per-day rate
        r"([\d,]+)\s*/\s*day",
        # "(3 days x Rs.4,000)" or "3 days × Rs. 4000" (× may be stripped to space)
        r"\d+\s*days?\s*[x×]?\s*(?:rs\.?|inr|₹)\s*\.?\s*([\d,]+\.?\d*)",
        r"room\s*(?:charge|rate)[s]?\s*[:\-]?\s*(?:rs\.?|inr|₹)?\s*\.?\s*([\d,]+\.?\d*)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            val = normalize_amount(match.group(1))
            if val and val >= 100:  # Room rent should be at least ₹100
                return val
    return None


def _extract_keywords(text_lower: str, keyword_list: List[str]) -> List[str]:
    found = []
    for kw in keyword_list:
        if kw in text_lower:
            found.append(kw)
    return found


def _days_between(date1: str, date2: str) -> int | None:
    """Calculate days between two date strings. Returns None on parse failure."""
    try:
        d1 = dateparser.parse(date1, dayfirst=True)
        d2 = dateparser.parse(date2, dayfirst=True)
        return abs((d2 - d1).days)
    except (ValueError, TypeError):
        return None


def _classify_category(description: str) -> str:
    """Classify a bill line item into a category."""
    desc_lower = description.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in desc_lower:
                return category
    return "other"


def _extract_line_items(text: str, total_amount: float | None = None, raw_text: str | None = None) -> List[BillLineItem]:
    """
    Extract individual bill line items (description + amount pairs).
    Uses two strategies:
    1. Line-by-line parsing from raw text (preserves newlines for tabular data)
    2. Regex pattern matching on normalized text (fallback)
    """
    items = []
    seen_descriptions = set()

    # --- Strategy 1: Line-by-line parsing from raw text (tabular formats) ---
    if raw_text:
        _extract_line_items_from_lines(raw_text, items, seen_descriptions, total_amount)

    # --- Strategy 2: Regex patterns on normalized (single-line) text ---
    patterns = [
        # Tabular: "ROOM RENT  1  Rs. 5,000  Rs. 5,000" — take last Rs. amount
        r"([A-Za-z][A-Za-z\s]{3,30}?)\s+\d+\s+(?:rs\.?|ris\.?|inr|₹)\s*\.?\s*[\d,]+\.?\d*\s+(?:rs\.?|ris\.?|inr|₹)\s*\.?\s*([\d,]+\.?\d*)",
        # "Description ... Rs. 12,000" with noise in between (|, a, etc.)
        r"([A-Za-z][A-Za-z\s\./&\-\(\)]{3,50}?)\s*[|:\-]?\s*(?:[a-z]?\s+)?(?:rs\.?|ris\.?|inr|₹)\s*\.?\s*([\d,]+\.?\d*)",
        # "Description  12,000" (description followed by spaces then number)
        r"([A-Za-z][A-Za-z\s\./&\-\(\)]{3,50})\s{2,}([\d,]{3,}\.?\d*)",
        # Short single-word service: "ROOM  18,000.00" or "RENT 22,765.54"
        r"([A-Z][A-Z]{2,})\s+([\d,]{3,}\.?\d*)",
        # "Rs. 12,000 - Description"
        r"(?:rs\.?|inr|₹)\s*([\d,]+\.?\d*)\s*[:\-]?\s*([A-Za-z][A-Za-z\s\./&\-\(\)]{3,50})",
    ]

    for pattern in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            groups = match.groups()
            if groups[0][0].isalpha():
                desc = groups[0].strip()
                amt_str = groups[1]
            else:
                amt_str = groups[0]
                desc = groups[1].strip()

            desc = _clean_description(desc)
            amt = normalize_amount(amt_str)
            _add_item_if_valid(desc, amt, items, seen_descriptions, total_amount)

    return items


def _extract_line_items_from_lines(raw_text: str, items: list, seen: set, total_amount: float | None):
    """Parse line items from raw text preserving newline structure."""
    from app.services.normalize import _fix_ocr_artifacts
    # Light normalization: fix OCR artifacts but preserve newlines
    text = _fix_ocr_artifacts(raw_text)
    text = re.sub(r"[^\x20-\x7E\n₹]", "", text)  # strip non-printable but keep newlines

    lines = text.split("\n")

    # Join continuation lines: if a line starts with space/lowercase and previous
    # line didn't end with a number, it's a continuation
    merged = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if merged and (line.startswith("  ") or (stripped and stripped[0].islower())):
            # Continuation of previous line
            merged[-1] = merged[-1].rstrip() + " " + stripped
        else:
            merged.append(stripped)

    for line in merged:
        # Pattern: description (text) followed by amount (number) at end of line
        # e.g. "Ward Charges 8,000.00" or "Medicine Charges 3,500.00"
        m = re.match(
            r'^([A-Za-z][\w\s\./&\-\(\),]+?)\s+([\d,]{3,}\.?\d{0,2})\s*$',
            line
        )
        if not m:
            # Also try: "Description  Rs. 12,000" at end of line
            m = re.match(
                r'^([A-Za-z][\w\s\./&\-\(\),]+?)\s+(?:rs\.?|ris\.?|inr|₹)\s*\.?\s*([\d,]{3,}\.?\d{0,2})\s*$',
                line, re.IGNORECASE
            )
        if not m:
            continue

        desc = m.group(1).strip()
        amt_str = m.group(2)

        desc = _clean_description(desc)
        amt = normalize_amount(amt_str)
        _add_item_if_valid(desc, amt, items, seen, total_amount)


def _clean_description(desc: str) -> str:
    """Clean up a candidate line-item description."""
    # Remove trailing dots, pipes, single chars
    desc = re.sub(r"[|]+", "", desc).strip()
    desc = re.sub(r"\s+[a-z]\s*$", "", desc).strip()
    desc = desc.rstrip(".")

    # Strip table headers preceding the real service name
    _TABLE_HEADERS = {"description", "quantity", "unit", "price", "amount",
                      "sl", "sr", "no", "sno", "particular", "particulars",
                      "service", "name", "rate", "patient",
                      "bill", "invoice", "date", "number", "to", "from"}
    words = desc.split()
    while len(words) > 1:
        w_lower = words[0].lower().rstrip(".")
        if w_lower in _TABLE_HEADERS or (len(w_lower) < 3 and not w_lower.isdigit()):
            words.pop(0)
        elif not _is_valid_description(words[0]) and _is_valid_description(" ".join(words[1:])):
            words.pop(0)
        else:
            break
    return " ".join(words)


def _add_item_if_valid(desc: str, amt: float | None, items: list, seen: set, total_amount: float | None):
    """Add a line item if it passes all validation checks."""
    if not amt or amt < 50:
        return
    if total_amount and amt > total_amount * 1.05:
        return
    desc_key = desc.lower().strip()
    if not desc_key:
        return
    # Skip headers/totals
    if any(skip in desc_key for skip in ["total", "grand", "net payable", "discount",
                                          "sub-total", "sub total", "bill amount",
                                          "in words", "amount (rs"]):
        return
    # Skip descriptions that end with Rs/Ris (false capture)
    if re.search(r"\b(?:rs|ris|inr)\.?\s*$", desc_key):
        return
    if not _is_valid_description(desc):
        return
    # Check for exact match or substring of existing descriptions (avoid duplicates)
    if desc_key in seen:
        return
    for existing in seen:
        if desc_key in existing or existing in desc_key:
            return
    seen.add(desc_key)
    category = _classify_category(desc)
    items.append(BillLineItem(
        description=desc,
        amount=amt,
        category=category,
    ))


def _is_valid_description(desc: str) -> bool:
    """Check if a description contains real English words, not OCR noise."""
    _VALID_KEYWORDS = {
        "room", "rent", "bed", "charge", "fee", "medicine", "drug", "surgery",
        "operation", "consultation", "diagnostic", "test", "nursing", "icu",
        "physiotherapy", "anesthesia", "anaesthesia", "oxygen", "blood",
        "theatre", "dressing", "implant", "stent", "prosthetic", "ambulance",
        "nebulization", "ventilator", "catheter", "injection", "xray",
        "x-ray", "mri", "scan", "echo", "ecg", "lab", "pathology",
        "radiology", "ultrasound", "equipment", "medical", "hospital",
        "pharmacy", "pharmay", "consumable", "material", "diet", "meals",
        "attendant", "charges", "medicines", "drugs", "services", "supplies",
        "care", "investigation", "ward", "neural", "doctor", "disease",
        "including", "procedure", "treatment", "therapy",
    }
    words = re.findall(r"[A-Za-z]{3,}", desc.lower())
    if not words:
        return False
    # Check with stemming (strip trailing s/es for plurals)
    def _match(w):
        if w in _VALID_KEYWORDS:
            return True
        if w.endswith("s") and w[:-1] in _VALID_KEYWORDS:
            return True
        if w.endswith("es") and w[:-2] in _VALID_KEYWORDS:
            return True
        return False
    known_count = sum(1 for w in words if _match(w))
    # Single-word descriptions: must be a known term
    if len(words) == 1:
        return _match(words[0])
    # Filter out filler words from the ratio calculation
    _FILLER = {"and", "the", "for", "per", "with", "pre", "post", "day", "days",
                "total", "other", "including", "fees"}
    real_words = [w for w in words if w not in _FILLER]
    if not real_words:
        return known_count >= 1
    if len(real_words) <= 2:
        return known_count >= 1
    # Longer descriptions need higher share of known words (rejects OCR noise mixed in)
    threshold = 0.55 if len(real_words) > 4 else 0.4
    return (known_count / len(real_words)) >= threshold


def _assess_ocr_quality(text: str) -> str:
    """
    Assess the quality of OCR output.
    Returns: "high", "medium", or "low"
    """
    if not text or len(text) < 20:
        return "low"

    words = text.split()
    if len(words) < 5:
        return "low"

    # Count words that look like real English (have vowels, 3+ chars)
    real_words = 0
    for w in words:
        cleaned = re.sub(r"[^a-zA-Z]", "", w)
        if len(cleaned) >= 3 and re.search(r"[aeiouAEIOU]", cleaned):
            real_words += 1

    ratio = real_words / len(words) if words else 0

    # Check for common bill/medical terms as a signal
    text_lower = text.lower()
    signal_terms = ["hospital", "patient", "bill", "total", "amount", "rs",
                     "room", "charge", "medicine", "surgery", "doctor", "invoice",
                     "discharge", "admission", "diagnosis", "receipt", "date"]
    signals_found = sum(1 for t in signal_terms if t in text_lower)

    # For short documents (< 100 words), be stricter
    if len(words) < 100:
        if ratio >= 0.6 and signals_found >= 5:
            return "high"
        elif ratio >= 0.4 and signals_found >= 3:
            return "medium"
        else:
            return "low"

    if ratio >= 0.6 and signals_found >= 4:
        return "high"
    elif ratio >= 0.4 and signals_found >= 2:
        return "medium"
    else:
        return "low"
