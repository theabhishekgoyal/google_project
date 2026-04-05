"""Convert SUMMARY_4PAGE.md into a clean 4-page PDF."""

from fpdf import FPDF
import os


class SummaryPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 5, "Insurance Claim Settlement Agent - Technical Summary", align="C")
        self.ln(3)
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(140, 140, 140)
        self.cell(0, 10, f"Page {self.page_no()} / 4", align="C")


def _sanitize(text: str) -> str:
    """Replace Unicode chars that latin-1 core fonts can't handle."""
    return (
        text
        .replace("\u2014", "-")   # em dash
        .replace("\u2013", "-")   # en dash
        .replace("\u2018", "'")   # left single quote
        .replace("\u2019", "'")   # right single quote
        .replace("\u201c", '"')   # left double quote
        .replace("\u201d", '"')   # right double quote
        .replace("\u2022", "-")   # bullet
        .replace("\u2026", "...")  # ellipsis
        .replace("\u2192", "->")  # right arrow
        .replace("\u2190", "<-")  # left arrow
        .replace("\u20b9", "Rs.") # rupee sign
        .replace("\u00d7", "x")   # multiplication sign
        .replace("\u2248", "~")   # approximately
        .replace("\u2265", ">=")  # >=
        .replace("\u2264", "<=")  # <=
    )


def build_pdf(output_path: str):
    pdf = SummaryPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.set_left_margin(14)
    pdf.set_right_margin(14)

    def title(text):
        pdf.set_font("Helvetica", "B", 15)
        pdf.set_text_color(20, 60, 120)
        pdf.cell(0, 8, _sanitize(text), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)

    def heading(text):
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(30, 30, 30)
        pdf.cell(0, 7, _sanitize(text), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)

    def subheading(text):
        pdf.set_font("Helvetica", "B", 9.5)
        pdf.set_text_color(50, 50, 50)
        pdf.cell(0, 6, _sanitize(text), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(0.5)

    def body(text):
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(40, 40, 40)
        pdf.multi_cell(0, 4.5, _sanitize(text))
        pdf.ln(1)

    def bullet(text):
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(40, 40, 40)
        pdf.cell(5)
        pdf.cell(4, 4.5, "-")
        pdf.multi_cell(0, 4.5, _sanitize(text))
        pdf.ln(0.5)

    def numbered(num, text):
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(40, 40, 40)
        pdf.cell(5)
        pdf.cell(5, 4.5, f"{num}.")
        pdf.multi_cell(0, 4.5, _sanitize(text))
        pdf.ln(0.5)

    def small_table(headers, rows, col_widths=None):
        usable = 182
        if col_widths is None:
            col_widths = [usable / len(headers)] * len(headers)
        # Header
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_fill_color(230, 240, 250)
        pdf.set_text_color(20, 20, 20)
        for i, h in enumerate(headers):
            pdf.cell(col_widths[i], 5.5, _sanitize(h), border=1, fill=True)
        pdf.ln()
        # Rows
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(40, 40, 40)
        for row in rows:
            max_h = 5
            for i, cell in enumerate(row):
                pdf.cell(col_widths[i], max_h, _sanitize(cell), border=1)
            pdf.ln()
        pdf.ln(2)

    def separator():
        pdf.set_draw_color(180, 180, 180)
        y = pdf.get_y()
        pdf.line(14, y, 196, y)
        pdf.ln(3)

    # ====================== PAGE 1 ======================
    pdf.add_page()
    title("Page 1: Problem Statement and Approach")
    pdf.ln(1)

    heading("Problem")
    body(
        "Insurance claim processing is slow, opaque, and frustrating for patients. "
        "Rejection reasons are buried in dense 50-page policy documents. Patients "
        "rarely understand why a claim was denied."
    )

    heading("Our Solution")
    body("An automated claim evaluation engine that:")
    numbered(1, "Reads scanned hospital bills using OCR (Tesseract + EasyOCR fallback)")
    numbered(2, "Parses complex policy PDFs into searchable clause chunks")
    numbered(3, "Uses NLP (TF-IDF vectorization + cosine similarity) to match bill items against policy clauses")
    numbered(4, "Applies a configurable rule engine (10 business rules) to determine claim eligibility")
    numbered(5, "Returns APPROVE / REJECT / PARTIAL with exact policy citations (page + clause) for every decision")
    pdf.ln(1)

    heading("Key Differentiators")
    bullet("Line-item reconciliation: Each bill item is individually matched to the policy, not just binary yes/no")
    bullet("Explainability first: Every rejection includes the exact policy clause and page number")
    bullet("Deterministic + auditable: Same input always produces same output; full audit trail")
    bullet("No paid APIs: Built entirely with free, open-source tools running locally")

    separator()

    heading("Processing Pipeline (High-Level)")
    pdf.set_font("Courier", "", 7.5)
    pdf.set_text_color(50, 50, 50)
    pipeline = (
        "Bill PDF --> OCR --> Text Extraction --> Bill Fact Parser\n"
        "                                             |\n"
        "Policy PDF --> PyMuPDF --> Policy Chunker --> TF-IDF Index\n"
        "                                             |\n"
        "                          Clause Retriever (cosine similarity)\n"
        "                                             |\n"
        "              Bill Facts + Clauses --> Rule Engine (10 rules)\n"
        "                                             |\n"
        "                       Line-Item Reconciliation\n"
        "                                             |\n"
        "                  Decision Builder --> APPROVE / REJECT / PARTIAL\n"
        "                                             |\n"
        "                       Audit Record (JSON) + UI Display"
    )
    pdf.multi_cell(0, 3.8, _sanitize(pipeline))
    pdf.ln(2)

    # ====================== PAGE 2 ======================
    pdf.add_page()
    title("Page 2: Technical Architecture and Core AI/ML")
    pdf.ln(1)

    heading("Architecture: Modular Monolith")
    body(
        "Single FastAPI service with clean internal modules. Streamlit UI for interactive demo. "
        "All modules communicate via typed Pydantic schemas. No external database required."
    )

    heading("Core AI/ML Algorithms")
    pdf.ln(0.5)

    subheading("1. OCR Pipeline (Tesseract + EasyOCR)")
    bullet("Auto-detects scanned vs text-based pages (threshold: < 50 characters of embedded text)")
    bullet("Tesseract configured at 300 DPI; EasyOCR as automatic fallback if Tesseract unavailable")
    bullet("OCR artifact correction: fixes common misreads (e.g., 'l' -> '1', 'O' -> '0' in numeric contexts)")
    pdf.ln(0.5)

    subheading("2. NLP Retrieval (TF-IDF + Cosine Similarity)")
    bullet("Policy text chunked into paragraph-level segments (~500 chars) with page metadata and headings")
    bullet("Vectorized using TF-IDF with bigrams (ngram_range=1,2) from scikit-learn")
    bullet("Each rule queries the index; cosine similarity returns the most relevant policy clause")
    bullet("Domain-specific preprocessing: insurance stop-word removal, Indian amount format normalization")
    pdf.ln(0.5)

    subheading("3. Rule Engine (10 Configurable Rules in YAML)")
    small_table(
        ["#", "Rule", "Type", "Logic"],
        [
            ["1", "Waiting Period", "Hard Reject", "Admission < 30 days from policy start"],
            ["2", "Room Rent Cap", "Partial", "Room rent > 1% of sum insured/day"],
            ["3", "Excluded Procedure", "Hard Reject", "Cosmetic, dental, fertility, etc."],
            ["4", "Pre-Existing Disease", "Hard Reject", "Known condition < 4 yrs coverage"],
            ["5", "Co-Pay", "Partial", "10% for age 60-75, 20% for 75+"],
            ["6", "Sum Insured Limit", "Partial", "Claim > sum insured"],
            ["7", "Min Hospitalization", "Info", "< 24 hours stay (non-daycare)"],
            ["8", "Non-Medical Items", "Partial", "Toiletries, TV, guest meals"],
            ["9", "Daycare Procedure", "Info", "Valid daycare < 24h exemption"],
            ["10", "Claim Documentation", "Info", "Missing required documents"],
        ],
        col_widths=[7, 35, 22, 118],
    )

    subheading("4. Line-Item Reconciliation")
    bullet("Each bill line item classified into categories: room, surgery, medicine, diagnostic, etc.")
    bullet("Category-specific policy queries match items against relevant clauses")
    bullet("Items tagged as: covered, excluded, sub-limited, or unknown")

    heading("Data Structures")
    small_table(
        ["Model", "Fields", "Purpose"],
        [
            ["PolicyChunk", "text, page_number, heading", "Indexed by TF-IDF"],
            ["BillLineItem", "description, amount, category", "Classified by keywords"],
            ["RuleResult", "rule_id, status, reason, citation", "Traceable per-rule output"],
            ["LineItemReconciliation", "desc, amount, status, reason, citation", "Per-item decision"],
        ],
        col_widths=[38, 70, 74],
    )

    # ====================== PAGE 3 ======================
    pdf.add_page()
    title("Page 3: Evaluation and Reliability")
    pdf.ln(1)

    heading("Test Strategy")
    body(
        "Synthetic test suite with 7 carefully designed scenarios covering all 10 rules. "
        "Real medical bills contain PHI; synthetic bills mimic realistic hospital output."
    )

    heading("Test Cases")
    small_table(
        ["#", "Scenario", "Expected", "Key Rule Triggered"],
        [
            ["1", "Clean appendectomy, within limits", "APPROVE", "None (all pass)"],
            ["2", "Cosmetic rhinoplasty", "REJECT", "Excluded Procedure"],
            ["3", "Pneumonia, Rs.8K room rent", "PARTIAL", "Room Rent Cap (>Rs.5K)"],
            ["4", "Hernia within 30-day wait", "REJECT", "Waiting Period"],
            ["5", "Diabetic foot, policy < 4 yrs", "REJECT", "Pre-Existing Disease"],
            ["6", "Cardiac surgery, patient 65 yrs", "PARTIAL", "Co-Pay (10%)"],
            ["7", "Brain surgery Rs.6.25L", "PARTIAL", "Sum Insured (Rs.5L cap)"],
        ],
        col_widths=[7, 48, 22, 105],
    )

    heading("Evaluation Metrics")
    small_table(
        ["Metric", "Target", "Description"],
        [
            ["Decision Accuracy", "100% on synthetic suite", "Correct APPROVE/REJECT/PARTIAL"],
            ["Citation Coverage", ">90%", "% of rules with valid policy citation"],
            ["Retrieval Relevance", "Manual check", "Is cited clause semantically correct?"],
            ["Processing Time", "<5 sec/claim", "End-to-end on CPU"],
            ["OCR Extraction Rate", ">80% fields", "Fields extracted from scanned bills"],
        ],
        col_widths=[36, 38, 108],
    )

    heading("Error Handling & Reliability")
    bullet("OCR noise: Amount minimum thresholds (Rs.100+), artifact correction regex")
    bullet("Indian number formats: handles 1,00,000 (lakhs) via multi-pattern regex")
    bullet("Policy chunk boundaries: paragraph-level splitting preserves clause integrity")
    bullet("Ambiguous items: flagged as 'unknown' with manual review suggestion")
    bullet("Deterministic: same input always produces same output")
    bullet("Graceful fallback: OCR failure doesn't crash; missing fields flagged as 'info'")
    bullet("Audit trail: every decision saved as JSON with unique audit ID")

    separator()

    heading("Technology Stack (All Free / Open-Source)")
    small_table(
        ["Component", "Technology", "Purpose"],
        [
            ["Backend", "FastAPI + Uvicorn", "REST API server"],
            ["UI", "Streamlit", "Interactive demo interface"],
            ["OCR", "Tesseract / EasyOCR", "Scanned document processing"],
            ["PDF Parsing", "PyMuPDF (fitz)", "Embedded text extraction"],
            ["NLP", "scikit-learn TF-IDF", "Clause retrieval + similarity"],
            ["Config", "YAML", "Rule definitions (no code change)"],
            ["Validation", "Pydantic", "Typed request/response schemas"],
            ["Storage", "JSON + filesystem", "Audit records"],
        ],
        col_widths=[30, 40, 112],
    )

    # ====================== PAGE 4 ======================
    pdf.add_page()
    title("Page 4: Impact, Scalability, and Future Work")
    pdf.ln(1)

    heading("Real-World Impact")
    bullet("For patients: Clear, readable explanations with exact policy references for every decision")
    bullet("For insurers: Automated first-pass evaluation reduces manual review time by ~10x")
    bullet("For regulators: Full audit trail with traceable decisions and citations")
    bullet("For hospitals: Faster cashless pre-authorization with transparent eligibility checks")

    heading("Architectural Scalability")
    body("The modular design supports seamless upgrades without rewriting:")
    bullet("Replace TF-IDF with semantic embeddings (sentence-transformers) without changing the rule engine")
    bullet("Add new rules via YAML config — zero code changes required")
    bullet("Swap OCR backend (Tesseract <-> EasyOCR <-> cloud API) via the abstraction layer")
    bullet("Scale to concurrent claims via FastAPI async + worker queues (Celery/Redis)")
    bullet("Add database backend (PostgreSQL) for production-grade audit storage")

    separator()

    heading("Future Improvements")
    numbered(1, "Named Entity Recognition (spaCy / medaCy) for better medical field extraction from OCR text")
    numbered(2, "Semantic embeddings (sentence-transformers) for higher retrieval accuracy on complex clauses")
    numbered(3, "LLM-assisted explanations (GPT / Llama) for more natural language rejection reasons")
    numbered(4, "Database-backed storage (PostgreSQL) replacing JSON files for production audit history")
    numbered(5, "Human-in-the-loop review workflow with confidence scoring for ambiguous cases")
    numbered(6, "Multi-language OCR for regional hospital bills (Hindi, Tamil, Telugu, etc.)")
    numbered(7, "PDF table extraction (Camelot/Tabula) for structured bill parsing")
    numbered(8, "Claims dashboard: insurer-facing analytics showing approval rates, common rejections, processing SLAs")

    separator()

    heading("Conclusion")
    body(
        "This system demonstrates that practical AI (OCR + NLP + deterministic rules) can solve "
        "a real, high-stakes problem while maintaining full transparency and accountability. "
        "Every decision is traceable to a specific policy clause, every amount is validated "
        "against configurable thresholds, and every audit record is preserved. The architecture "
        "is designed for correctness and explainability first, with clear extension paths for "
        "production deployment."
    )
    pdf.ln(2)

    # Bottom box
    pdf.set_fill_color(240, 245, 255)
    pdf.set_draw_color(100, 130, 200)
    y = pdf.get_y()
    pdf.rect(14, y, 182, 18, style="DF")
    pdf.set_xy(18, y + 2)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(20, 60, 120)
    pdf.cell(0, 5, _sanitize("Built with: Python | FastAPI | Tesseract | scikit-learn | PyMuPDF | Streamlit"))
    pdf.set_xy(18, y + 8)
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(60, 60, 60)
    pdf.cell(0, 5, "Zero paid APIs. Fully local. Fully auditable. Production-ready architecture.")

    pdf.output(output_path)
    print(f"PDF created: {os.path.abspath(output_path)}")


if __name__ == "__main__":
    build_pdf("SUMMARY_4PAGE.pdf")
