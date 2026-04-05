"""
Streamlit UI for the Insurance Claim Settlement Agent.
Upload policy + bill, view decision, reasons, and citations.
"""

import os
import sys
import json
from datetime import date
from pathlib import Path

# Load .env file
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

import streamlit as st

# Streamlit Cloud: inject secrets as env vars if not already set
try:
    for key in st.secrets:
        if key not in os.environ:
            os.environ[key] = str(st.secrets[key])
except Exception:
    pass  # No secrets configured (local dev)

# Add project root to path so we can import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.schemas import ClaimMetadata
from app.services.extract_pdf import extract_text_from_pdf, extract_full_text
from app.services.ocr_service import ocr_image_file
from app.services.parse_bill import extract_bill_facts
from app.services.gemini_parser import parse_bill_with_gemini
from app.services.chunk_policy import chunk_policy_pages
from app.services.retrieve_clause import ClauseRetriever
from app.services.rules_engine import evaluate_rules
from app.services.reconcile import reconcile_bill_items
from app.services.decision_builder import build_decision

st.set_page_config(page_title="Insurance Claim Agent", page_icon="🏥", layout="wide")

st.title("🏥 Insurance Claim Settlement Agent")
st.markdown("Upload a policy document and hospital bill to evaluate the claim.")

# ---- Sidebar: Inputs ----
with st.sidebar:
    st.header("📋 Claim Details")
    policy_file = st.file_uploader("Upload Policy PDF", type=["pdf"])
    bill_file = st.file_uploader("Upload Hospital Bill", type=["pdf", "png", "jpg", "jpeg"])

    st.markdown("---")

    evaluate_btn = st.button("🔍 Evaluate Claim", type="primary", use_container_width=True)


# ---- Main Area ----
if evaluate_btn:
    if not policy_file or not bill_file:
        st.error("Please upload both a policy PDF and a hospital bill.")
    else:
        with st.spinner("Processing documents..."):
            # Save uploads to temp
            temp_dir = os.path.join("app", "storage", "uploads")
            os.makedirs(temp_dir, exist_ok=True)

            policy_path = os.path.join(temp_dir, policy_file.name)
            bill_path = os.path.join(temp_dir, bill_file.name)

            with open(policy_path, "wb") as f:
                f.write(policy_file.read())
            with open(bill_path, "wb") as f:
                f.write(bill_file.read())

            # Step 1: Extract policy text
            policy_pages = extract_text_from_pdf(policy_path)

            # Step 2 & 3: Parse bill (Gemini primary, OCR+regex fallback)
            bill_facts = parse_bill_with_gemini(bill_path)
            if bill_facts:
                # st.success("✅ Bill parsed using Gemini AI")
                pass
            else:
                bill_ext = os.path.splitext(bill_file.name)[1].lower()
                if bill_ext == ".pdf":
                    bill_text = extract_full_text(bill_path)
                else:
                    try:
                        bill_text = ocr_image_file(bill_path)
                    except Exception as e:
                        st.error(
                            "OCR failed. Tesseract may not be installed.\n\n"
                            "**Fix:** Upload the bill as a PDF instead, or install Tesseract OCR:\n"
                            "https://github.com/UB-Mannheim/tesseract/wiki"
                        )
                        st.stop()
                bill_facts = extract_bill_facts(bill_text)
                st.info("ℹ️ Bill parsed using OCR + regex (Gemini unavailable)")

            # Step 4: Chunk + retrieve
            chunks = chunk_policy_pages(policy_pages)
            retriever = ClauseRetriever(chunks)

            # Step 5: Metadata
            meta = ClaimMetadata()

            # Step 6: Evaluate
            rule_results = evaluate_rules(bill_facts, meta, retriever)

            # Step 7: Reconcile line items against policy
            reconciliation = reconcile_bill_items(bill_facts, meta, retriever, rule_results)

            # Step 8: Decision
            decision = build_decision(rule_results, bill_facts)

        # Receipt Details card
        st.markdown("---")
        st.subheader("🧾 Receipt Details")
        r1, r2 = st.columns(2)
        with r1:
            st.markdown(f"**Patient Name:** {bill_facts.patient_name or 'N/A'}")
            st.markdown(f"**Admission Date:** {bill_facts.admission_date or 'N/A'}")
            st.markdown(f"**Total Amount:** ₹{bill_facts.total_amount:,.0f}" if bill_facts.total_amount else "**Total Amount:** N/A")
        with r2:
            st.markdown(f"**Hospital Name:** {bill_facts.hospital_name or 'N/A'}")
            st.markdown(f"**Discharge Date:** {bill_facts.discharge_date or 'N/A'}")
        if bill_facts.diagnosis_keywords:
            st.markdown(f"**Diagnosis:** {', '.join(bill_facts.diagnosis_keywords)}")
        if bill_facts.procedure_keywords:
            st.markdown(f"**Procedures:** {', '.join(bill_facts.procedure_keywords)}")

        # ---- Display Results ----
        st.markdown("---")

        # OCR confidence warning
        if bill_facts.ocr_confidence == "low":
            st.warning(
                "⚠️ **Low OCR Quality Detected** — The bill text is heavily garbled. "
                "Extracted data (patient name, amounts, dates) may be unreliable. "
                "Consider uploading a clearer scan or a text-based PDF."
            )
        elif bill_facts.ocr_confidence == "medium":
            st.info(
                "ℹ️ **Medium OCR Quality** — Some fields may be inaccurate. "
                "Review the extracted facts below for correctness."
            )

        # Decision banner
        color_map = {"APPROVE": "green", "REJECT": "red", "PARTIAL": "orange", "INSUFFICIENT_DATA": "gray"}
        color = color_map.get(decision.decision, "gray")
        st.markdown(
            f"<h2 style='color:{color};'>Decision: {decision.decision}</h2>",
            unsafe_allow_html=True,
        )
        st.markdown(f"**Audit ID:** `{decision.audit_id}`")
        st.markdown(f"**Summary:** {decision.summary_reason}")

        # Amounts
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Claimed", f"₹{decision.total_claimed or 0:,.0f}")
        with col2:
            st.metric("Approved", f"₹{decision.approved_amount or 0:,.0f}")
        with col3:
            st.metric("Rejected", f"₹{decision.rejected_amount or 0:,.0f}")

        

        # Settlement Breakdown from reconciliation
        if reconciliation:
            st.markdown("---")
            st.subheader("💰 Settlement Breakdown")

            covered_amt = sum(r.amount or 0 for r in reconciliation if r.status == "covered")
            sub_limited_amt = sum(r.amount or 0 for r in reconciliation if r.status == "sub_limited")
            excluded_amt = sum(r.amount or 0 for r in reconciliation if r.status == "excluded")
            unknown_amt = sum(r.amount or 0 for r in reconciliation if r.status == "unknown")

            sb1, sb2, sb3, sb4 = st.columns(4)
            with sb1:
                st.metric("✅ Covered", f"₹{covered_amt:,.0f}")
            with sb2:
                st.metric("⚠️ Sub-Limited", f"₹{sub_limited_amt:,.0f}")
            with sb3:
                st.metric("❌ Excluded", f"₹{excluded_amt:,.0f}")
            with sb4:
                st.metric("❓ Unknown", f"₹{unknown_amt:,.0f}")

            if sub_limited_amt > 0 or excluded_amt > 0:
                parts = []
                if sub_limited_amt > 0:
                    parts.append(f"₹{sub_limited_amt:,.0f} sub-limited")
                if excluded_amt > 0:
                    parts.append(f"₹{excluded_amt:,.0f} excluded")
                st.warning(
                    f"**Note:** ₹{sub_limited_amt + excluded_amt:,.0f} of the claimed amount "
                    f"may not be fully reimbursed ({' + '.join(parts)}). "
                    f"Check the line-item reconciliation below for details."
                )

        # Rule details
        st.markdown("---")
        st.subheader("📜 Rule-by-Rule Audit Trail")

        for rule in decision.rules_fired:
            icon = "✅" if rule.status == "pass" else ("❌" if rule.status == "fail" else "ℹ️")
            with st.expander(f"{icon} {rule.name} — {rule.status.upper()}"):
                st.markdown(f"**Rule ID:** `{rule.rule_id}`")
                st.markdown(f"**Status:** {rule.status}")
                st.markdown(f"**Reason:** {rule.reason}")
                if rule.citation:
                    st.markdown(f"**Policy Citation (Page {rule.citation.page}):**")
                    st.info(rule.citation.clause_text)

        # Bill Line-Item Reconciliation
        if reconciliation:
            st.markdown("---")
            st.subheader("🔗 Bill Line-Item Reconciliation")
            st.markdown("Each bill item is matched against the policy to determine coverage.")

            for rec in reconciliation:
                status_icons = {"covered": "✅", "excluded": "❌", "sub_limited": "⚠️", "unknown": "❓"}
                icon = status_icons.get(rec.status, "❓")
                amt_str = f"₹{rec.amount:,.0f}" if rec.amount else "N/A"
                with st.expander(f"{icon} {rec.description} — {amt_str} — {rec.status.upper()}"):
                    st.markdown(f"**Category:** {rec.category}")
                    st.markdown(f"**Status:** {rec.status}")
                    st.markdown(f"**Reason:** {rec.reason}")
                    if rec.citation:
                        st.markdown(f"**Policy Citation (Page {rec.citation.page}):**")
                        st.info(rec.citation.clause_text)

        # Show raw OCR text for debugging
        # if raw_text_content:
        #     with st.expander("🔍 Raw Extracted Bill Text (for debugging)"):
        #         st.text(raw_text_content[:3000])

        # Policy chunks info
        # st.markdown("---")
        # st.subheader("📚 Policy Processing Info")
        # st.write(f"Total pages processed: {len(policy_pages)}")
        # st.write(f"Total chunks created: {len(chunks)}")

        # Raw JSON output
        # st.markdown("---")
        # with st.expander("🔧 Full JSON Response"):
        #     st.json(json.loads(decision.model_dump_json()))

else:
    # Landing info
    st.info("👈 Upload your documents in the sidebar and click **Evaluate Claim** to start.")

    st.markdown("### How it works")
    st.markdown("""
    1. **Upload** your insurance policy PDF and hospital bill.
    2. The system **extracts text** using PDF parsing or OCR.
    3. **NLP retrieval** finds the most relevant policy clauses.
    4. A **rule engine** checks claim eligibility against 10 business rules.
    5. You get a **transparent decision** with reasons and exact policy citations.
    """)
