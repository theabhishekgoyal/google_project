"""
Unit tests for the rules engine and retrieval components.

Usage:
    cd insurance-claim-agent
    python -m pytest tests/test_rules_engine.py -v
"""

import sys
import os
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.schemas import BillFacts, ClaimMetadata, PolicyChunk
from app.services.retrieve_clause import ClauseRetriever
from app.services.rules_engine import evaluate_rules


def _make_retriever():
    """Create a retriever with sample policy chunks."""
    chunks = [
        PolicyChunk(text="Room rent is limited to 1% of the sum insured per day.", page=3),
        PolicyChunk(text="Initial waiting period of 30 days from policy start date.", page=4),
        PolicyChunk(text="Cosmetic surgery and dental treatment are not covered.", page=5),
        PolicyChunk(text="Pre-existing conditions are excluded for the first 4 years.", page=5),
        PolicyChunk(text="No co-payment for policyholders below 60 years of age.", page=6),
        PolicyChunk(text="Maximum liability shall not exceed the sum insured.", page=6),
    ]
    return ClauseRetriever(chunks)


def test_approved_claim():
    """A clean claim with no rule violations should be APPROVE."""
    facts = BillFacts(
        total_amount=65000,
        room_rent_per_day=4000,
        procedure_keywords=["appendectomy"],
        diagnosis_keywords=["appendicitis"],
        raw_text="test",
    )
    meta = ClaimMetadata(
        policy_start_date=date(2025, 1, 1),
        claim_date=date(2025, 6, 15),
        sum_insured=500000,
    )
    retriever = _make_retriever()
    results = evaluate_rules(facts, meta, retriever)

    statuses = [r.status for r in results]
    assert "fail" not in statuses, f"Expected all pass but got: {[(r.rule_id, r.status) for r in results]}"


def test_excluded_procedure():
    """A cosmetic procedure should trigger EXCLUDED_PROCEDURE fail."""
    facts = BillFacts(
        total_amount=94000,
        room_rent_per_day=6000,
        procedure_keywords=["cosmetic"],
        diagnosis_keywords=[],
        raw_text="test",
    )
    meta = ClaimMetadata(
        policy_start_date=date(2025, 1, 1),
        claim_date=date(2025, 3, 10),
        sum_insured=500000,
    )
    retriever = _make_retriever()
    results = evaluate_rules(facts, meta, retriever)

    exclusion_result = next(r for r in results if r.rule_id == "EXCLUDED_PROCEDURE")
    assert exclusion_result.status == "fail", f"Expected fail but got {exclusion_result.status}"


def test_room_rent_exceeded():
    """Room rent above cap should trigger ROOM_RENT_CAP fail."""
    facts = BillFacts(
        total_amount=77000,
        room_rent_per_day=8000,  # Cap is 1% of 500000 = 5000
        procedure_keywords=[],
        diagnosis_keywords=[],
        raw_text="test",
    )
    meta = ClaimMetadata(
        policy_start_date=date(2025, 1, 1),
        claim_date=date(2025, 8, 20),
        sum_insured=500000,
    )
    retriever = _make_retriever()
    results = evaluate_rules(facts, meta, retriever)

    rent_result = next(r for r in results if r.rule_id == "ROOM_RENT_CAP")
    assert rent_result.status == "fail", f"Expected fail but got {rent_result.status}"


def test_waiting_period():
    """Claim within 30-day waiting period should fail."""
    facts = BillFacts(
        total_amount=30000,
        procedure_keywords=[],
        diagnosis_keywords=[],
        raw_text="test",
    )
    meta = ClaimMetadata(
        policy_start_date=date(2025, 1, 1),
        claim_date=date(2025, 1, 15),  # Only 14 days
        sum_insured=500000,
    )
    retriever = _make_retriever()
    results = evaluate_rules(facts, meta, retriever)

    wait_result = next(r for r in results if r.rule_id == "WAITING_PERIOD")
    assert wait_result.status == "fail", f"Expected fail but got {wait_result.status}"


def test_pre_existing_disease():
    """Diabetes diagnosed within 4-year exclusion window should fail."""
    facts = BillFacts(
        total_amount=50000,
        procedure_keywords=[],
        diagnosis_keywords=["diabetes"],
        raw_text="test",
    )
    meta = ClaimMetadata(
        policy_start_date=date(2025, 1, 1),
        claim_date=date(2025, 6, 1),  # Less than 4 years
        sum_insured=500000,
    )
    retriever = _make_retriever()
    results = evaluate_rules(facts, meta, retriever)

    pe_result = next(r for r in results if r.rule_id == "PRE_EXISTING_DISEASE")
    assert pe_result.status == "fail", f"Expected fail but got {pe_result.status}"


def test_citation_present():
    """Every rule result should have a citation."""
    facts = BillFacts(
        total_amount=65000,
        room_rent_per_day=4000,
        procedure_keywords=["appendectomy"],
        diagnosis_keywords=[],
        raw_text="test",
    )
    meta = ClaimMetadata(
        policy_start_date=date(2025, 1, 1),
        claim_date=date(2025, 6, 15),
        sum_insured=500000,
    )
    retriever = _make_retriever()
    results = evaluate_rules(facts, meta, retriever)

    for r in results:
        assert r.citation is not None, f"Rule {r.rule_id} missing citation"
        assert r.citation.page > 0, f"Rule {r.rule_id} has invalid page number"


if __name__ == "__main__":
    tests = [
        test_approved_claim,
        test_excluded_procedure,
        test_room_rent_exceeded,
        test_waiting_period,
        test_pre_existing_disease,
        test_citation_present,
    ]
    for t in tests:
        try:
            t()
            print(f"✅ {t.__name__}")
        except AssertionError as e:
            print(f"❌ {t.__name__}: {e}")
        except Exception as e:
            print(f"❌ {t.__name__}: {type(e).__name__}: {e}")
