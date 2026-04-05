"""
Rule Engine: evaluates each business rule against extracted bill facts
and retrieved policy clauses.

Each rule returns a RuleResult with status, reason, and citation.
"""

import os
import yaml
from datetime import datetime, date
from typing import List, Optional

from app.schemas import BillFacts, ClaimMetadata, RuleResult, Citation
from app.services.retrieve_clause import ClauseRetriever


def load_rules() -> list:
    """Load rules from the YAML config file."""
    config_path = os.path.join(os.path.dirname(__file__), "..", "config", "rules.yaml")
    config_path = os.path.normpath(config_path)
    with open(config_path, "r") as f:
        data = yaml.safe_load(f)
    return data.get("rules", [])


def evaluate_rules(
    bill_facts: BillFacts,
    metadata: ClaimMetadata,
    retriever: ClauseRetriever,
) -> List[RuleResult]:
    """Run all configured rules and return results."""
    rules = load_rules()
    results = []

    for rule in rules:
        rule_id = rule["rule_id"]

        if rule_id == "WAITING_PERIOD":
            result = _check_waiting_period(rule, bill_facts, metadata, retriever)
        elif rule_id == "ROOM_RENT_CAP":
            result = _check_room_rent_cap(rule, bill_facts, metadata, retriever)
        elif rule_id == "EXCLUDED_PROCEDURE":
            result = _check_excluded_procedure(rule, bill_facts, retriever)
        elif rule_id == "PRE_EXISTING_DISEASE":
            result = _check_pre_existing_disease(rule, bill_facts, metadata, retriever)
        elif rule_id == "CO_PAY":
            result = _check_co_pay(rule, bill_facts, metadata, retriever)
        elif rule_id == "SUM_INSURED_LIMIT":
            result = _check_sum_insured(rule, bill_facts, metadata, retriever)
        elif rule_id == "MIN_HOSPITALIZATION":
            result = _check_min_hospitalization(rule, bill_facts, retriever)
        elif rule_id == "NON_MEDICAL_ITEMS":
            result = _check_non_medical_items(rule, bill_facts, retriever)
        elif rule_id == "DAYCARE_PROCEDURE":
            result = _check_daycare(rule, bill_facts, retriever)
        elif rule_id == "CLAIM_DOCUMENTATION":
            result = _check_documentation(rule, bill_facts, retriever)
        else:
            result = RuleResult(
                rule_id=rule_id,
                name=rule.get("name", rule_id),
                status="info",
                reason=f"Rule {rule_id} is not implemented.",
            )

        results.append(result)

    return results


# ---------------------------------------------------------------------------
# Individual rule implementations
# ---------------------------------------------------------------------------

def _check_waiting_period(
    rule: dict, facts: BillFacts, meta: ClaimMetadata, retriever: ClauseRetriever
) -> RuleResult:
    citation = retriever.get_best_citation(rule["query_terms"])
    name = rule["name"]

    if meta.policy_start_date and meta.claim_date:
        days_since = (meta.claim_date - meta.policy_start_date).days
        waiting_days = rule.get("default_waiting_days", 30)

        if days_since < waiting_days:
            return RuleResult(
                rule_id=rule["rule_id"],
                name=name,
                status="fail",
                reason=rule["failure_message"].format(days=waiting_days),
                citation=citation,
            )
        return RuleResult(
            rule_id=rule["rule_id"],
            name=name,
            status="pass",
            reason=rule["success_message"],
            citation=citation,
        )

    return RuleResult(
        rule_id=rule["rule_id"],
        name=name,
        status="pass",
        reason="Dates not available; skipping waiting period check.",
        citation=citation,
    )


def _check_room_rent_cap(
    rule: dict, facts: BillFacts, meta: ClaimMetadata, retriever: ClauseRetriever
) -> RuleResult:
    citation = retriever.get_best_citation(rule["query_terms"])
    name = rule["name"]

    if facts.room_rent_per_day is not None and meta.sum_insured:
        cap_percent = rule.get("default_cap_percent", 1.0)
        allowed = meta.sum_insured * cap_percent / 100.0

        if facts.room_rent_per_day > allowed:
            return RuleResult(
                rule_id=rule["rule_id"],
                name=name,
                status="fail",
                reason=rule["failure_message"].format(
                    claimed=facts.room_rent_per_day, allowed=allowed
                ),
                citation=citation,
            )
        return RuleResult(
            rule_id=rule["rule_id"],
            name=name,
            status="pass",
            reason=rule["success_message"],
            citation=citation,
        )

    return RuleResult(
        rule_id=rule["rule_id"],
        name=name,
        status="pass",
        reason="Room rent data not available; skipping cap check.",
        citation=citation,
    )


def _check_excluded_procedure(
    rule: dict, facts: BillFacts, retriever: ClauseRetriever
) -> RuleResult:
    citation = retriever.get_best_citation(rule["query_terms"])
    name = rule["name"]
    excluded = [kw.lower() for kw in rule.get("excluded_keywords", [])]

    matched = [p for p in facts.procedure_keywords if p.lower() in excluded]

    if matched:
        return RuleResult(
            rule_id=rule["rule_id"],
            name=name,
            status="fail",
            reason=rule["failure_message"].format(procedure=", ".join(matched)),
            citation=citation,
        )

    return RuleResult(
        rule_id=rule["rule_id"],
        name=name,
        status="pass",
        reason=rule["success_message"],
        citation=citation,
    )


def _check_pre_existing_disease(
    rule: dict, facts: BillFacts, meta: ClaimMetadata, retriever: ClauseRetriever
) -> RuleResult:
    citation = retriever.get_best_citation(rule["query_terms"])
    name = rule["name"]
    pe_keywords = [kw.lower() for kw in rule.get("pre_existing_keywords", [])]
    exclusion_years = rule.get("exclusion_years", 4)

    matched = [d for d in facts.diagnosis_keywords if d.lower() in pe_keywords]

    if matched:
        # Check if within exclusion window
        within_window = True
        if meta.policy_start_date and meta.claim_date:
            years_since = (meta.claim_date - meta.policy_start_date).days / 365.25
            if years_since >= exclusion_years:
                within_window = False

        if within_window:
            return RuleResult(
                rule_id=rule["rule_id"],
                name=name,
                status="fail",
                reason=rule["failure_message"].format(
                    condition=", ".join(matched), years=exclusion_years
                ),
                citation=citation,
            )

    return RuleResult(
        rule_id=rule["rule_id"],
        name=name,
        status="pass",
        reason=rule["success_message"],
        citation=citation,
    )


def _check_co_pay(
    rule: dict, facts: BillFacts, meta: ClaimMetadata, retriever: ClauseRetriever
) -> RuleResult:
    citation = retriever.get_best_citation(rule["query_terms"])
    name = rule["name"]
    copay_percent = rule.get("default_copay_percent", 0)

    if copay_percent > 0 and facts.total_amount:
        deducted = facts.total_amount * copay_percent / 100.0
        return RuleResult(
            rule_id=rule["rule_id"],
            name=name,
            status="fail",
            reason=rule["failure_message"].format(percent=copay_percent, deducted=deducted),
            citation=citation,
        )

    return RuleResult(
        rule_id=rule["rule_id"],
        name=name,
        status="pass",
        reason=rule["success_message"],
        citation=citation,
    )


def _check_sum_insured(
    rule: dict, facts: BillFacts, meta: ClaimMetadata, retriever: ClauseRetriever
) -> RuleResult:
    citation = retriever.get_best_citation(rule["query_terms"])
    name = rule["name"]

    if facts.total_amount and meta.sum_insured:
        if facts.total_amount > meta.sum_insured:
            return RuleResult(
                rule_id=rule["rule_id"],
                name=name,
                status="fail",
                reason=rule["failure_message"].format(
                    claimed=facts.total_amount, available=meta.sum_insured
                ),
                citation=citation,
            )

    return RuleResult(
        rule_id=rule["rule_id"],
        name=name,
        status="pass",
        reason=rule["success_message"],
        citation=citation,
    )


def _check_min_hospitalization(
    rule: dict, facts: BillFacts, retriever: ClauseRetriever
) -> RuleResult:
    citation = retriever.get_best_citation(rule["query_terms"])
    name = rule["name"]
    min_hours = rule.get("min_hours", 24)

    if facts.admission_date and facts.discharge_date:
        try:
            from dateutil import parser as dateparser
            adm = dateparser.parse(facts.admission_date, dayfirst=True)
            dis = dateparser.parse(facts.discharge_date, dayfirst=True)
            hours = (dis - adm).total_seconds() / 3600
            if hours < min_hours:
                return RuleResult(
                    rule_id=rule["rule_id"],
                    name=name,
                    status="fail",
                    reason=rule["failure_message"].format(min_hours=min_hours),
                    citation=citation,
                )
        except Exception:
            pass

    return RuleResult(
        rule_id=rule["rule_id"],
        name=name,
        status="pass",
        reason=rule["success_message"],
        citation=citation,
    )


def _check_non_medical_items(
    rule: dict, facts: BillFacts, retriever: ClauseRetriever
) -> RuleResult:
    citation = retriever.get_best_citation(rule["query_terms"])
    name = rule["name"]
    nm_keywords = [kw.lower() for kw in rule.get("non_medical_keywords", [])]

    # Check line items
    found_items = []
    for item in facts.line_items:
        desc_lower = item.description.lower()
        for kw in nm_keywords:
            if kw in desc_lower:
                found_items.append(item.description)
                break

    # Also check raw text
    if not found_items:
        text_lower = facts.raw_text.lower()
        for kw in nm_keywords:
            if kw in text_lower:
                found_items.append(kw)

    if found_items:
        return RuleResult(
            rule_id=rule["rule_id"],
            name=name,
            status="fail",
            reason=rule["failure_message"].format(items=", ".join(found_items[:3])),
            citation=citation,
        )

    return RuleResult(
        rule_id=rule["rule_id"],
        name=name,
        status="pass",
        reason=rule["success_message"],
        citation=citation,
    )


def _check_daycare(
    rule: dict, facts: BillFacts, retriever: ClauseRetriever
) -> RuleResult:
    citation = retriever.get_best_citation(rule["query_terms"])
    name = rule["name"]

    # If same-day admission/discharge, it might be daycare
    is_daycare = False
    if facts.admission_date and facts.discharge_date:
        if facts.admission_date == facts.discharge_date:
            is_daycare = True

    if is_daycare and facts.procedure_keywords:
        return RuleResult(
            rule_id=rule["rule_id"],
            name=name,
            status="pass",
            reason=f"Daycare procedure detected ({', '.join(facts.procedure_keywords)}). Covered if listed in policy daycare list.",
            citation=citation,
        )

    return RuleResult(
        rule_id=rule["rule_id"],
        name=name,
        status="pass",
        reason=rule["success_message"],
        citation=citation,
    )


def _check_documentation(
    rule: dict, facts: BillFacts, retriever: ClauseRetriever
) -> RuleResult:
    citation = retriever.get_best_citation(rule["query_terms"])
    name = rule["name"]

    missing = []
    if not facts.patient_name:
        missing.append("patient name")
    if not facts.hospital_name:
        missing.append("hospital name")
    if facts.total_amount is None:
        missing.append("total amount")
    if not facts.admission_date:
        missing.append("admission date")

    if missing:
        return RuleResult(
            rule_id=rule["rule_id"],
            name=name,
            status="info",
            reason=rule["failure_message"].format(missing_fields=", ".join(missing)),
            citation=citation,
        )

    return RuleResult(
        rule_id=rule["rule_id"],
        name=name,
        status="pass",
        reason=rule["success_message"],
        citation=citation,
    )
