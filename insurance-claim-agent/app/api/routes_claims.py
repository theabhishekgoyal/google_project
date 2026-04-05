"""
FastAPI routes for claim evaluation.
Orchestrates the full pipeline: upload -> extract -> parse -> retrieve -> evaluate -> decide.
"""

import os
import json
import shutil
from datetime import date
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from app.schemas import ClaimDecision, ClaimMetadata
from app.services.extract_pdf import extract_text_from_pdf, extract_full_text
from app.services.ocr_service import ocr_image_file
from app.services.parse_bill import extract_bill_facts
from app.services.gemini_parser import parse_bill_with_gemini
from app.services.chunk_policy import chunk_policy_pages
from app.services.retrieve_clause import ClauseRetriever
from app.services.rules_engine import evaluate_rules
from app.services.decision_builder import build_decision

router = APIRouter()

UPLOAD_DIR = os.path.join("app", "storage", "uploads")
OUTPUT_DIR = os.path.join("app", "storage", "outputs")


@router.post("/evaluate", response_model=ClaimDecision)
async def evaluate_claim(
    policy_file: UploadFile = File(..., description="Insurance policy PDF"),
    bill_file: UploadFile = File(..., description="Hospital bill PDF or image"),
    policy_start_date: Optional[str] = Form(None, description="Policy start date (YYYY-MM-DD)"),
    claim_date: Optional[str] = Form(None, description="Claim date (YYYY-MM-DD)"),
    sum_insured: Optional[float] = Form(500000.0, description="Sum insured amount"),
):
    """
    Upload a policy PDF and a hospital bill, then evaluate the claim.
    Returns a structured decision with reasons and citations.
    """
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # Save uploaded files
    policy_path = os.path.join(UPLOAD_DIR, policy_file.filename)
    bill_path = os.path.join(UPLOAD_DIR, bill_file.filename)

    with open(policy_path, "wb") as f:
        shutil.copyfileobj(policy_file.file, f)
    with open(bill_path, "wb") as f:
        shutil.copyfileobj(bill_file.file, f)

    # --- Step 1: Extract policy text ---
    policy_pages = extract_text_from_pdf(policy_path)

    # --- Step 2 & 3: Parse bill (Gemini primary, OCR+regex fallback) ---
    bill_ext = os.path.splitext(bill_file.filename)[1].lower()
    if bill_ext not in (".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp"):
        raise HTTPException(status_code=400, detail=f"Unsupported bill file type: {bill_ext}")

    # Try Gemini first
    bill_facts = parse_bill_with_gemini(bill_path)

    # Fallback to OCR + regex
    if bill_facts is None:
        if bill_ext == ".pdf":
            bill_text = extract_full_text(bill_path)
        else:
            bill_text = ocr_image_file(bill_path)
        bill_facts = extract_bill_facts(bill_text)

    # --- Step 4: Chunk policy and build retriever ---
    chunks = chunk_policy_pages(policy_pages)
    retriever = ClauseRetriever(chunks)

    # --- Step 5: Build metadata ---
    meta = ClaimMetadata(
        policy_start_date=_parse_date(policy_start_date),
        claim_date=_parse_date(claim_date),
        sum_insured=sum_insured or 500000.0,
    )

    # --- Step 6: Evaluate rules ---
    rule_results = evaluate_rules(bill_facts, meta, retriever)

    # --- Step 7: Build decision ---
    decision = build_decision(rule_results, bill_facts)

    return decision


@router.get("/{audit_id}", response_model=ClaimDecision)
async def get_claim_result(audit_id: str):
    """Retrieve a previously evaluated claim by audit ID."""
    filepath = os.path.join(OUTPUT_DIR, f"{audit_id}.json")
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail=f"Audit record {audit_id} not found.")

    with open(filepath, "r") as f:
        data = json.load(f)

    return ClaimDecision(**data)


def _parse_date(date_str: Optional[str]) -> Optional[date]:
    """Parse a YYYY-MM-DD string into a date object."""
    if not date_str:
        return None
    try:
        return date.fromisoformat(date_str)
    except ValueError:
        return None
