"""
Evaluation script: runs the claim pipeline on all sample cases
and checks decision accuracy, retrieval quality, and processing time.

Usage:
    cd insurance-claim-agent
    python -m tests.evaluate
"""

import os
import sys
import time
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.schemas import ClaimMetadata
from app.services.extract_pdf import extract_text_from_pdf, extract_full_text
from app.services.parse_bill import extract_bill_facts
from app.services.chunk_policy import chunk_policy_pages
from app.services.retrieve_clause import ClauseRetriever
from app.services.rules_engine import evaluate_rules
from app.services.decision_builder import build_decision
from datetime import date


SAMPLE_DIR = os.path.join("app", "storage", "samples")

# Expected outcomes for each test case
TEST_CASES = [
    {
        "name": "Approved Claim (Appendectomy)",
        "policy": "sample_policy.pdf",
        "bill": "bill_approved.pdf",
        "expected_decision": "APPROVE",
        "policy_start": date(2025, 1, 1),
        "claim_date": date(2025, 6, 15),
        "sum_insured": 500000.0,
    },
    {
        "name": "Rejected Claim (Cosmetic Procedure)",
        "policy": "sample_policy.pdf",
        "bill": "bill_rejected_exclusion.pdf",
        "expected_decision": "REJECT",
        "policy_start": date(2025, 1, 1),
        "claim_date": date(2025, 3, 10),
        "sum_insured": 500000.0,
    },
    {
        "name": "Partial Claim (Room Rent Exceeded)",
        "policy": "sample_policy.pdf",
        "bill": "bill_partial_room_rent.pdf",
        "expected_decision": "PARTIAL",
        "policy_start": date(2025, 1, 1),
        "claim_date": date(2025, 8, 20),
        "sum_insured": 500000.0,
    },
]


def run_evaluation():
    print("=" * 70)
    print("INSURANCE CLAIM AGENT — EVALUATION REPORT")
    print("=" * 70)

    total = len(TEST_CASES)
    correct = 0
    results = []

    for i, tc in enumerate(TEST_CASES, 1):
        print(f"\n--- Test Case {i}/{total}: {tc['name']} ---")

        policy_path = os.path.join(SAMPLE_DIR, tc["policy"])
        bill_path = os.path.join(SAMPLE_DIR, tc["bill"])

        if not os.path.exists(policy_path):
            print(f"  SKIP: Policy file not found: {policy_path}")
            print(f"  Run 'python -m tests.generate_samples' first.")
            continue
        if not os.path.exists(bill_path):
            print(f"  SKIP: Bill file not found: {bill_path}")
            continue

        start_time = time.time()

        # Pipeline
        policy_pages = extract_text_from_pdf(policy_path)
        bill_text = extract_full_text(bill_path)
        bill_facts = extract_bill_facts(bill_text)
        chunks = chunk_policy_pages(policy_pages)
        retriever = ClauseRetriever(chunks)

        meta = ClaimMetadata(
            policy_start_date=tc["policy_start"],
            claim_date=tc["claim_date"],
            sum_insured=tc["sum_insured"],
        )

        rule_results = evaluate_rules(bill_facts, meta, retriever)
        decision = build_decision(rule_results, bill_facts)

        elapsed = time.time() - start_time

        # Check accuracy
        match = decision.decision == tc["expected_decision"]
        if match:
            correct += 1

        status = "✅ PASS" if match else "❌ FAIL"
        print(f"  Expected: {tc['expected_decision']}")
        print(f"  Got:      {decision.decision}")
        print(f"  Result:   {status}")
        print(f"  Time:     {elapsed:.2f}s")
        print(f"  Summary:  {decision.summary_reason}")

        # Check citation quality
        cited_rules = [r for r in decision.rules_fired if r.citation is not None]
        print(f"  Citations: {len(cited_rules)}/{len(decision.rules_fired)} rules have policy citations")

        # Show failed rules
        failed = [r for r in decision.rules_fired if r.status == "fail"]
        if failed:
            print(f"  Failed rules:")
            for r in failed:
                page_info = f" (page {r.citation.page})" if r.citation else ""
                print(f"    - {r.name}: {r.reason}{page_info}")

        results.append({
            "name": tc["name"],
            "expected": tc["expected_decision"],
            "actual": decision.decision,
            "match": match,
            "time_seconds": round(elapsed, 2),
            "citation_coverage": f"{len(cited_rules)}/{len(decision.rules_fired)}",
        })

    # Summary
    print("\n" + "=" * 70)
    print("EVALUATION SUMMARY")
    print("=" * 70)
    print(f"Decision Accuracy: {correct}/{total} ({correct/total*100:.0f}%)")
    print(f"Total test cases:  {total}")

    avg_time = sum(r["time_seconds"] for r in results) / len(results) if results else 0
    print(f"Avg processing time: {avg_time:.2f}s per claim")

    # Save report
    report_path = os.path.join("app", "storage", "outputs", "evaluation_report.json")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w") as f:
        json.dump({
            "accuracy": f"{correct}/{total}",
            "accuracy_percent": round(correct / total * 100, 1) if total else 0,
            "avg_time_seconds": round(avg_time, 2),
            "cases": results,
        }, f, indent=2)
    print(f"\nDetailed report saved to: {report_path}")


if __name__ == "__main__":
    run_evaluation()
