"""
Decision Builder: combines all rule results into a final claim decision.
Generates the audit record with summary, amounts, and explainability.
"""

import json
import os
import re
import uuid
from datetime import datetime
from typing import List, Optional

from app.schemas import ClaimDecision, RuleResult, BillFacts


def build_decision(
    rules_fired: List[RuleResult],
    bill_facts: BillFacts,
) -> ClaimDecision:
    """
    Combine rule results into a final APPROVE / REJECT / PARTIAL decision.
    Calculates accurate approved/rejected amounts based on specific rule failures.
    """
    audit_id = f"CLM-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    fail_count = sum(1 for r in rules_fired if r.status == "fail")
    pass_count = sum(1 for r in rules_fired if r.status == "pass")
    total_rules = len(rules_fired)

    total_claimed = bill_facts.total_amount

    # Check if bill data is insufficient
    has_bill_data = (
        bill_facts.total_amount is not None
        or bill_facts.room_rent_per_day is not None
        or len(bill_facts.procedure_keywords) > 0
        or len(bill_facts.diagnosis_keywords) > 0
    )

    # OCR confidence warning
    ocr_warning = ""
    if bill_facts.ocr_confidence == "low":
        ocr_warning = " ⚠️ OCR quality is LOW — extracted data may be unreliable. Please verify with a clearer document."
    elif bill_facts.ocr_confidence == "medium":
        ocr_warning = " ⚠️ OCR quality is MEDIUM — some fields may be inaccurate."

    if not has_bill_data:
        decision = "INSUFFICIENT_DATA"
        summary = (
            "Could not extract sufficient information from the hospital bill. "
            "The bill may be a scanned image requiring OCR. "
            "Please ensure the bill text is readable or install Tesseract/easyocr."
        )
        approved_amount = None
        rejected_amount = None
    elif total_claimed is None or total_claimed == 0:
        # Bill partially read but amount missing
        if fail_count == 0:
            decision = "APPROVE"
            summary = (
                "All policy checks passed. Claim is approved. "
                "Note: Total claimed amount could not be extracted from the bill."
            )
        elif _has_hard_reject(rules_fired):
            decision = "REJECT"
            failed_names = [r.name for r in rules_fired if r.status == "fail"]
            summary = f"Claim rejected due to: {'; '.join(failed_names)}."
        else:
            decision = "PARTIAL"
            failed_names = [r.name for r in rules_fired if r.status == "fail"]
            summary = f"Partially approved. Issues found: {'; '.join(failed_names)}."
        approved_amount = None
        rejected_amount = None
    elif fail_count == 0:
        decision = "APPROVE"
        summary = "All policy checks passed. Claim is approved."
        approved_amount = total_claimed
        rejected_amount = 0.0
    elif fail_count == total_rules or _has_hard_reject(rules_fired):
        decision = "REJECT"
        failed_names = [r.name for r in rules_fired if r.status == "fail"]
        summary = f"Claim rejected due to: {'; '.join(failed_names)}."
        approved_amount = 0.0
        rejected_amount = total_claimed
    else:
        decision = "PARTIAL"
        failed_names = [r.name for r in rules_fired if r.status == "fail"]
        summary = f"Partially approved. Issues found: {'; '.join(failed_names)}."

        if total_claimed:
            rejected_amount = _calculate_deductions(rules_fired, bill_facts)
            approved_amount = round(total_claimed - rejected_amount, 2)
        else:
            approved_amount = None
            rejected_amount = None

    claim_decision = ClaimDecision(
        audit_id=audit_id,
        decision=decision,
        summary_reason=summary + ocr_warning,
        approved_amount=approved_amount,
        rejected_amount=rejected_amount,
        total_claimed=total_claimed,
        rules_fired=rules_fired,
    )

    # Save audit record
    _save_audit(claim_decision)

    return claim_decision


def _calculate_deductions(rules_fired: List[RuleResult], bill_facts: BillFacts) -> float:
    """Calculate the actual rejected amount based on specific rule failures."""
    total = bill_facts.total_amount or 0
    deductions = 0.0

    for r in rules_fired:
        if r.status != "fail":
            continue

        if r.rule_id == "ROOM_RENT_CAP" and bill_facts.room_rent_per_day:
            # Proportionate payment clause: all expenses reduced by ratio
            # allowed_rate / claimed_rate applied to total bill
            # Extract the allowed cap from the reason text
            cap_match = re.search(r"allowed cap of ([\d,.]+)", r.reason)
            if cap_match:
                allowed = float(cap_match.group(1).replace(",", ""))
                ratio = allowed / bill_facts.room_rent_per_day
                deductions += round(total * (1 - ratio), 2)
            else:
                # Fallback: use 10% if can't parse
                deductions += round(total * 0.10, 2)

        elif r.rule_id == "CO_PAY":
            # Extract co-pay percentage from reason
            pct_match = re.search(r"(\d+)%", r.reason)
            if pct_match:
                pct = float(pct_match.group(1))
                deductions += round(total * pct / 100, 2)

        elif r.rule_id == "SUM_INSURED_LIMIT":
            # Excess over sum insured
            # Match "remaining sum insured of X" or "available X"
            amt_match = re.search(r"(?:remaining\s+sum\s+insured\s+of|available)\s*([\d,]+(?:\.\d+)?)", r.reason)
            if amt_match:
                available = float(amt_match.group(1).replace(",", ""))
                deductions += max(0, total - available)

        elif r.rule_id == "NON_MEDICAL_ITEMS":
            # Flat 5% estimate for non-medical items
            deductions += round(total * 0.05, 2)

    # Ensure deductions don't exceed total
    return min(round(deductions, 2), total)


def _has_hard_reject(rules_fired: List[RuleResult]) -> bool:
    """Some rules cause an immediate full reject."""
    hard_reject_rules = {"EXCLUDED_PROCEDURE", "WAITING_PERIOD"}
    for r in rules_fired:
        if r.status == "fail" and r.rule_id in hard_reject_rules:
            return True
    return False


def _save_audit(decision: ClaimDecision) -> None:
    """Save the decision JSON to the outputs folder."""
    output_dir = os.path.join("app", "storage", "outputs")
    os.makedirs(output_dir, exist_ok=True)

    filepath = os.path.join(output_dir, f"{decision.audit_id}.json")
    with open(filepath, "w") as f:
        json.dump(decision.model_dump(mode="json"), f, indent=2, default=str)
