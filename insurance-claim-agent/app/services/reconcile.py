"""
Bill-to-Policy Reconciliation Service.

For each line item in the hospital bill, this service:
1. Identifies the item category (room, surgery, medicine, etc.)
2. Retrieves the most relevant policy clause
3. Determines if the item is covered, excluded, or sub-limited
4. Provides a citation for the decision

This is the core NLP reconciliation logic required by the problem statement.
"""

import re
from typing import List, Optional

from app.schemas import (
    BillLineItem, LineItemReconciliation, Citation,
    BillFacts, ClaimMetadata, PolicyChunk, RuleResult,
)
from app.services.retrieve_clause import ClauseRetriever


# Queries to find policy sections relevant to each bill category
CATEGORY_POLICY_QUERIES = {
    "room": "room rent charges per day limit cap accommodation boarding",
    "surgery": "surgery surgical procedure operation covered treatment",
    "medicine": "medicine drugs pharmacy medical supplies prescribed",
    "diagnostic": "diagnostic test investigation laboratory pathology radiology",
    "consultation": "consultation doctor physician specialist charges fees",
    "icu": "intensive care unit ICU critical care charges",
    "nursing": "nursing care attendant charges",
    "anesthesia": "anesthesia anaesthesia charges",
    "other": "hospitalization expenses covered treatment charges",
}

# Keywords that indicate an exclusion in policy text
EXCLUSION_INDICATORS = [
    "not covered", "excluded", "not payable", "shall not",
    "does not cover", "exclusion", "will not pay",
    "not admissible", "not eligible", "not reimbursable",
]

# Keywords that indicate a sub-limit in policy text
SUB_LIMIT_INDICATORS = [
    "limited to", "subject to", "up to", "maximum of",
    "not exceeding", "capped at", "sub-limit", "sublimit",
    "percentage of", "% of sum insured",
]

# Non-medical items commonly excluded
NON_MEDICAL_ITEMS = [
    "toiletries", "personal comfort", "telephone", "tv", "television",
    "mineral water", "food packet", "snack", "guest meal",
    "registration", "admission charge", "service charge",
    "gown", "slippers", "tissue", "napkin",
]


def reconcile_bill_items(
    bill_facts: BillFacts,
    metadata: ClaimMetadata,
    retriever: ClauseRetriever,
    rule_results: Optional[List[RuleResult]] = None,
) -> List[LineItemReconciliation]:
    """
    Reconcile each bill line item against the policy.
    Uses rule_results to stay consistent with rule engine decisions.
    Returns a list of reconciliation results with coverage status and citations.
    """
    # Build a lookup of rule statuses for quick access
    rule_status = {}
    if rule_results:
        for r in rule_results:
            rule_status[r.rule_id] = r.status

    results = []

    for item in bill_facts.line_items:
        result = _reconcile_single_item(item, retriever, rule_status)
        results.append(result)

    return results


def _reconcile_single_item(
    item: BillLineItem,
    retriever: ClauseRetriever,
    rule_status: dict = None,
) -> LineItemReconciliation:
    """Reconcile a single bill line item against the policy."""
    if rule_status is None:
        rule_status = {}

    desc_lower = item.description.lower()

    # Check 1: Is it a non-medical item? (immediate exclude)
    for nm in NON_MEDICAL_ITEMS:
        if nm in desc_lower:
            citation = retriever.get_best_citation(
                "non-medical items personal comfort excluded not covered"
            )
            return LineItemReconciliation(
                description=item.description,
                amount=item.amount,
                category=item.category,
                status="excluded",
                reason=f"'{item.description}' is a non-medical/personal comfort item, typically excluded.",
                citation=citation,
            )

    # Check 2: Retrieve the most relevant policy clause for this category
    query = CATEGORY_POLICY_QUERIES.get(item.category, CATEGORY_POLICY_QUERIES["other"])
    # Also include the item description in the query for better matching
    full_query = f"{query} {item.description}"

    top_results = retriever.retrieve(full_query, top_k=3)

    if not top_results:
        return LineItemReconciliation(
            description=item.description,
            amount=item.amount,
            category=item.category,
            status="unknown",
            reason="No matching policy clause found for this item.",
            citation=None,
        )

    best_chunk, best_score = top_results[0]
    clause_text_lower = best_chunk.text.lower()

    # Rule-engine consistency: if the rule engine already evaluated this category, respect it
    # Room items: if ROOM_RENT_CAP passed, room is covered (not excluded)
    if item.category == "room" and rule_status.get("ROOM_RENT_CAP") == "pass":
        citation = _make_citation(best_chunk)
        return LineItemReconciliation(
            description=item.description,
            amount=item.amount,
            category=item.category,
            status="covered",
            reason=f"'{item.description}' is covered. Room rent is within the allowed policy cap.",
            citation=citation,
        )
    if item.category == "room" and rule_status.get("ROOM_RENT_CAP") == "fail":
        citation = _make_citation(best_chunk)
        return LineItemReconciliation(
            description=item.description,
            amount=item.amount,
            category=item.category,
            status="sub_limited",
            reason=f"'{item.description}' is covered but subject to proportionate deduction (room rent exceeds policy cap).",
            citation=citation,
        )

    # Check 3: For room/ICU, check sub-limits FIRST (room rent cap = partial, not exclusion)
    has_sub_limit = any(ind in clause_text_lower for ind in SUB_LIMIT_INDICATORS)

    if has_sub_limit and item.category in ("room", "icu"):
        citation = _make_citation(best_chunk)
        return LineItemReconciliation(
            description=item.description,
            amount=item.amount,
            category=item.category,
            status="sub_limited",
            reason=f"'{item.description}' is covered but subject to a sub-limit/proportionate deduction per policy terms.",
            citation=citation,
        )

    # Check 4: Does the matched clause indicate an exclusion?
    is_excluded = any(ind in clause_text_lower for ind in EXCLUSION_INDICATORS)
    # Check if the exclusion specifically mentions this item type
    item_mentioned_in_exclusion = _item_mentioned_in_text(desc_lower, clause_text_lower)

    if is_excluded and item_mentioned_in_exclusion:
        citation = _make_citation(best_chunk)
        return LineItemReconciliation(
            description=item.description,
            amount=item.amount,
            category=item.category,
            status="excluded",
            reason=f"Policy clause indicates '{item.description}' may be excluded from coverage.",
            citation=citation,
        )

    # Check 5: Sub-limits for other categories
    if has_sub_limit:
        citation = _make_citation(best_chunk)
        return LineItemReconciliation(
            description=item.description,
            amount=item.amount,
            category=item.category,
            status="sub_limited",
            reason=f"'{item.description}' is covered but subject to a sub-limit per policy terms.",
            citation=citation,
        )

    # Default: covered
    citation = _make_citation(best_chunk)
    return LineItemReconciliation(
        description=item.description,
        amount=item.amount,
        category=item.category,
        status="covered",
        reason=f"'{item.description}' is covered under the policy.",
        citation=citation,
    )


def _item_mentioned_in_text(item_desc_lower: str, text_lower: str) -> bool:
    """Check if any keyword from the item appears in the policy text."""
    words = item_desc_lower.split()
    significant_words = [w for w in words if len(w) > 3]
    if not significant_words:
        return False
    matches = sum(1 for w in significant_words if w in text_lower)
    return matches >= 1


def _make_citation(chunk: PolicyChunk) -> Citation:
    """Create a Citation from a PolicyChunk."""
    clause_text = chunk.text[:300]
    if len(chunk.text) > 300:
        clause_text += "..."
    return Citation(page=chunk.page, clause_text=clause_text)
