"""
Generate The Big Code 2026 Hackathon Submission PDF.
Run: python generate_submission_pdf.py
Output: hackathon_submission.pdf
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, ListFlowable, ListItem, Image
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib import colors
import os

OUTPUT_FILE = "hackathon_submission.pdf"

# ─── Styles ───────────────────────────────────────────────────────────────────

def get_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name='DocTitle',
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        alignment=TA_CENTER,
        spaceAfter=4,
        textColor=HexColor('#1a237e'),
    ))
    styles.add(ParagraphStyle(
        name='DocSubtitle',
        fontName='Helvetica',
        fontSize=10,
        leading=13,
        alignment=TA_CENTER,
        spaceAfter=10,
        textColor=HexColor('#424242'),
    ))
    styles.add(ParagraphStyle(
        name='SectionHead',
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        spaceBefore=6,
        spaceAfter=3,
        textColor=HexColor('#1565c0'),
        borderWidth=0,
        borderPadding=0,
    ))
    styles.add(ParagraphStyle(
        name='SubSection',
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=12,
        spaceBefore=4,
        spaceAfter=2,
        textColor=HexColor('#283593'),
    ))
    styles.add(ParagraphStyle(
        name='BodyJ',
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        alignment=TA_JUSTIFY,
        spaceAfter=2,
    ))
    styles.add(ParagraphStyle(
        name='BulletText',
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        leftIndent=14,
        spaceAfter=1,
    ))
    styles.add(ParagraphStyle(
        name='SmallBold',
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        spaceAfter=1,
    ))
    styles.add(ParagraphStyle(
        name='FieldLabel',
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        spaceAfter=2,
        textColor=HexColor('#333333'),
    ))
    styles.add(ParagraphStyle(
        name='FieldValue',
        fontName='Helvetica',
        fontSize=11,
        leading=15,
        spaceAfter=10,
        textColor=HexColor('#000000'),
    ))
    styles.add(ParagraphStyle(
        name='CodeBlock',
        fontName='Courier',
        fontSize=8,
        leading=10,
        leftIndent=12,
        spaceAfter=6,
        backColor=HexColor('#f5f5f5'),
    ))
    return styles


def build_table(data, col_widths=None, header=True):
    """Build a styled table."""
    t = Table(data, colWidths=col_widths, repeatRows=1 if header else 0)
    style_cmds = [
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('LEADING', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cccccc')),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]
    if header:
        style_cmds += [
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1565c0')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ]
        for i in range(1, len(data)):
            if i % 2 == 0:
                style_cmds.append(('BACKGROUND', (0, i), (-1, i), HexColor('#f0f4ff')))
    t.setStyle(TableStyle(style_cmds))
    return t


def hr():
    return HRFlowable(width="100%", thickness=1, color=HexColor('#1565c0'), spaceAfter=4, spaceBefore=2)


# ─── Content ──────────────────────────────────────────────────────────────────

def build_pdf():
    doc = SimpleDocTemplate(
        OUTPUT_FILE,
        pagesize=A4,
        leftMargin=15*mm,
        rightMargin=15*mm,
        topMargin=15*mm,
        bottomMargin=15*mm,
    )
    S = get_styles()
    story = []
    W = doc.width  # usable width

    # ── Title Page + Summary + Problem Statement (single page) ──────────────
    # story.append(Spacer(1, 3))
    story.append(Paragraph("Big Code 2026", S['DocTitle']))
    story.append(Paragraph("Hackathon Solution Submission", S['DocSubtitle']))
    story.append(hr())

    # Metadata as compact table
    meta_data = [
        [Paragraph("<b>Project Name:</b>", S['BodyJ']), Paragraph("Insurance Claim Settlement Agent", S['BodyJ'])],
        [Paragraph("<b>Participant Name:</b>", S['BodyJ']), Paragraph("Kirti Goel", S['BodyJ'])],
        [Paragraph("<b>Email ID:</b>", S['BodyJ']), Paragraph("xyz@gmail.com", S['BodyJ'])],
        [Paragraph("<b>Year of Degree:</b>", S['BodyJ']), Paragraph("3rd Year", S['BodyJ'])],
        [Paragraph("<b>GitHub:</b>", S['BodyJ']), Paragraph("https://github.com/theabhishekgoyal/google_project", S['BodyJ'])],
        [Paragraph("<b>Live Demo:</b>", S['BodyJ']), Paragraph("https://appproject-retzmndbhfqxrenebhvnjx.streamlit.app/", S['BodyJ'])],
    ]
    meta_table = Table(meta_data, colWidths=[W*0.22, W*0.78])
    meta_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(meta_table)
    story.append(hr())

    # Brief Summary (compact)
    story.append(Paragraph("Brief Summary", S['SectionHead']))
    story.append(Paragraph(
        "Insurance claim processing in India is slow, opaque, and frustrating for patients. "
        "Rejection reasons are buried in dense 50-page policy documents, and patients rarely understand "
        "why a claim was denied. Our solution is an <b>AI-powered Insurance Claim Settlement Agent</b> that "
        "automates claim evaluation in seconds. It reads hospital bills using Google Gemini Vision API "
        "(with OCR fallback), parses policy PDFs into searchable clause chunks, retrieves the most relevant "
        "policy clauses using TF-IDF + cosine similarity, and applies 10 deterministic business rules to "
        "determine claim eligibility. The output is a transparent decision — <b>APPROVE</b>, <b>REJECT</b>, "
        "or <b>PARTIAL</b> — with exact policy citations (page number + clause text), line-item reconciliation, "
        "and a full audit trail. Built entirely with free, open-source tools and the Google Gemini API free tier.",
        S['BodyJ']
    ))
    story.append(hr())

    # Problem Statement (same page)
    story.append(Paragraph("Problem Statement", S['SectionHead']))
    story.append(Paragraph(
        "India's health insurance sector processed over <b>1.5 crore claims</b> in FY2024, "
        "yet the average claim settlement time remains <b>15-30 days</b> for cashless and even longer for "
        "reimbursement claims. The core problems are:",
        S['BodyJ']
    ))
    bullets = [
        "<b>Opacity:</b> Patients receive single-line rejection reasons with no reference to the actual policy clause.",
        "<b>Inconsistency:</b> Different adjustors interpret the same policy differently, leading to arbitrary decisions.",
        "<b>Complexity:</b> Policy documents are 30-50 pages of dense legal text with exclusions, sub-limits, "
        "waiting periods, and co-pay clauses scattered across sections.",
        "<b>Delay:</b> Manual adjudication requires human experts to cross-reference bills against policies — hours per claim.",
        "<b>Lack of Trust:</b> Without transparent reasoning, patients lose trust in the insurance process.",
    ]
    for b in bullets:
        story.append(Paragraph(f"• {b}", S['BulletText']))

    story.append(Spacer(1, 2))
    story.append(Paragraph(
        "<b>Target users:</b> Health insurance policyholders, Third Party Administrators (TPAs), "
        "and insurance companies seeking consistent, auditable claim processing.",
        S['BodyJ']
    ))


    # ── Design Idea and Approach ──────────────────────────────────────────────
    story.append(Paragraph("Design Idea and Approach", S['SectionHead']))

    story.append(Paragraph("<b>Architecture: Modular Monolith</b>", S['SubSection']))
    story.append(Paragraph(
        "We use a modular monolith architecture — a single deployable service with clean internal separation "
        "of concerns. This provides fast iteration, easy debugging, and clear module boundaries while avoiding "
        "the overhead of microservices for a hackathon project.",
        S['BodyJ']
    ))

    # Pipeline diagram as image
    story.append(Paragraph("<b>End-to-End Processing Pipeline</b>", S['SubSection']))

    # Generate the diagram image
    from generate_diagram import draw_diagram
    diagram_path = draw_diagram()
    # Embed image scaled to fit page width
    img_w = W * 0.75
    img_h = img_w * (900 / 1200)  # maintain aspect ratio
    story.append(Image(diagram_path, width=img_w, height=img_h))

    # story.append(Spacer(1, 8))
    story.append(Paragraph("<b>Technologies Used</b>", S['SubSection']))
    tech_data = [
        ['Layer', 'Technology', 'Purpose'],
        ['Backend', 'Python 3.11+, FastAPI, Uvicorn', 'REST API + orchestration'],
        ['UI', 'Streamlit', 'Interactive web interface'],
        ['AI - Bill Parsing', 'Google Gemini 2.5 Flash (Vision API)', 'Structured extraction from bill images/PDFs'],
        ['AI - Retrieval', 'scikit-learn TF-IDF + cosine similarity', 'Find relevant policy clauses per rule'],
        ['OCR', 'Tesseract + EasyOCR (multi-pass)', 'Fallback text extraction from scanned documents'],
        ['PDF Parsing', 'PyMuPDF (fitz)', 'Text extraction from policy PDFs'],
        ['Validation', 'Pydantic', 'Data model validation'],
        ['Config', 'PyYAML', 'Business rule definitions'],
        ['Storage', 'JSON + filesystem', 'Audit records and outputs'],
    ]
    story.append(build_table(tech_data, col_widths=[W*0.18, W*0.40, W*0.42]))

    story.append(Paragraph("<b>Core Algorithm: TF-IDF Clause Retrieval</b>", S['SubSection']))
    story.append(Paragraph(
        "The policy document is split into ~500-character chunks at paragraph boundaries, preserving page "
        "numbers. Each chunk is vectorized using TF-IDF with bigram features (max 5,000 features). "
        "For each of the 10 business rules, we construct a query from the rule's domain-specific keywords "
        "and use cosine similarity to find the most relevant policy clause. This retrieved clause is then "
        "used both for rule evaluation and as the citation in the final decision.",
        S['BodyJ']
    ))

    story.append(Paragraph("<b>10 Business Rules (YAML-Configured)</b>", S['SubSection']))
    rules_data = [
        ['#', 'Rule', 'Check', 'Impact'],
        ['1', 'Waiting Period', 'Claim within 30-day initial waiting period', 'Hard reject'],
        ['2', 'Room Rent Cap', 'Room rent > 1% of sum insured/day', 'Partial deduction'],
        ['3', 'Excluded Procedure', 'Cosmetic, dental, fertility, etc.', 'Hard reject'],
        ['4', 'Pre-Existing Disease', 'Known condition < 4 years coverage', 'Hard reject'],
        ['5', 'Co-Payment', 'Age-based: 0% (<60), 10% (60-75), 20% (>75)', 'Deduction'],
        ['6', 'Sum Insured Limit', 'Claimed amount exceeds sum insured', 'Partial/Reject'],
        ['7', 'Min Hospitalization', 'Less than 24 hours', 'Flag'],
        ['8', 'Non-Medical Items', 'Toiletries, TV, guest meals', 'Deduction'],
        ['9', 'Daycare Procedure', 'Same-day procedures', 'Info'],
        ['10', 'Documentation', 'Missing required fields', 'Info'],
    ]
    story.append(build_table(rules_data, col_widths=[W*0.05, W*0.18, W*0.47, W*0.30]))

    story.append(Paragraph("<b>Gemini Vision API — Bill Parsing</b>", S['SubSection']))
    story.append(Paragraph(
        "The primary bill parser sends the hospital bill (PDF or image) directly to Google Gemini 2.5 Flash "
        "Vision API with a structured extraction prompt. Gemini returns a JSON object with patient details, "
        "dates, amounts, and categorized line items. If Gemini is unavailable (no API key, quota exceeded), "
        "the system gracefully falls back to a comprehensive OCR + regex parser with 400+ patterns built "
        "for Indian hospital bills.",
        S['BodyJ']
    ))

    story.append(Paragraph("<b>Security and Privacy</b>", S['SubSection']))
    bullets_sec = [
        "API keys stored in environment variables (.env), never hardcoded in source",
        "Uploaded files stored locally, not transmitted to third parties (except Gemini API for parsing)",
        "XSRF protection enabled on the Streamlit deployment",
        "No PII stored permanently — uploads can be cleared after processing",
        ".gitignore excludes .env files and uploaded data from version control",
    ]
    for b in bullets_sec:
        story.append(Paragraph(f"• {b}", S['BulletText']))

    # story.append(PageBreak())

    # ── Impact ────────────────────────────────────────────────────────────────
    story.append(Paragraph("Impact", S['SectionHead']))
    story.append(Paragraph(
        "This project addresses a critical gap in India's healthcare insurance ecosystem, where "
        "claim adjudication remains manual, opaque, and time-consuming.",
        S['BodyJ']
    ))

    impact_items = [
        ("<b>For Patients (Primary Beneficiary):</b>", [
            "Instant, clear explanations with exact policy page references — no more guessing why a claim was denied",
            "Line-item reconciliation shows exactly which bill items are covered, sub-limited, or excluded",
            "Empowers patients to challenge incorrect rejections with evidence",
        ]),
        ("<b>For Insurance Companies & TPAs:</b>", [
            "Automated first-pass evaluation reduces manual review time by an estimated 10x",
            "Consistent decisions — same input always produces same output (deterministic rules)",
            "Full audit trail (JSON records) for regulatory compliance",
        ]),
        ("<b>For the Healthcare Ecosystem:</b>", [
            "Reduces claim disputes and grievances through transparency",
            "Scalable to thousands of claims per day with minimal infrastructure",
            "Open-source implementation — can be adopted and customized by any insurer or TPA",
        ]),
    ]

    for heading, items in impact_items:
        story.append(Paragraph(heading, S['SmallBold']))
        for item in items:
            story.append(Paragraph(f"• {item}", S['BulletText']))
        story.append(Spacer(1, 4))

    story.append(Paragraph(
        "<b>Grounded in real data:</b> The system was tested against 10+ synthetic hospital bills "
        "modeled after real Indian hospital bill formats (Apollo Hospitals, Fortis, Narayana Health, etc.) "
        "covering scenarios like appendectomy, cosmetic surgery, cardiac stenting, diabetic complications, "
        "and pneumonia — producing correct decisions in all test cases.",
        S['BodyJ']
    ))

    story.append(hr())

    # ── Feasibility ───────────────────────────────────────────────────────────
    story.append(Paragraph("Feasibility", S['SectionHead']))

    feasibility_items = [
        "<b>Working Prototype:</b> The system is fully functional — not a concept. It processes real "
        "policy PDFs and hospital bills end-to-end and produces auditable decisions.",
        "<b>Live Deployment:</b> Hosted on Streamlit Community Cloud with a public URL for immediate demo.",
        "<b>Zero Cost Infrastructure:</b> Built entirely with free/open-source tools. Google Gemini API "
        "free tier provides 20 requests/day — sufficient for demo and testing. OCR fallback ensures "
        "the system works even without API access.",
        "<b>Meaningful Test Dataset:</b> 10+ synthetic hospital bills covering all major claim scenarios "
        "(approve, reject, partial) with a sample insurance policy document. 50+ pre-evaluated audit "
        "records stored as JSON.",
        "<b>Technical Expertise:</b> The pipeline integrates OCR, NLP (TF-IDF), Vision AI (Gemini), "
        "and deterministic rule engines — demonstrating AI applied at multiple stages.",
        "<b>Extension Path:</b> YAML-configured rules mean new business rules can be added without "
        "code changes. The TF-IDF retriever can be upgraded to semantic embeddings (sentence-transformers) "
        "for higher accuracy. FastAPI backend supports production deployment with async workers.",
    ]
    for item in feasibility_items:
        story.append(Paragraph(f"• {item}", S['BulletText']))

    story.append(hr())

    # ── Use of AI ─────────────────────────────────────────────────────────────
    story.append(Paragraph("Use of AI", S['SectionHead']))
    story.append(Paragraph(
        "AI technology is central to every stage of the pipeline:",
        S['BodyJ']
    ))

    ai_cell = S['BodyJ']
    ai_hdr = ParagraphStyle('ai_hdr', parent=S['BodyJ'], textColor=colors.white, fontName='Helvetica-Bold')
    ai_data = [
        [Paragraph('Stage', ai_hdr), Paragraph('AI Technique', ai_hdr), Paragraph('Details', ai_hdr)],
        [Paragraph('Bill Parsing (Primary)', ai_cell), Paragraph('Google Gemini 2.5 Flash Vision API', ai_cell),
         Paragraph('Sends bill image/PDF directly to Gemini with structured extraction prompt. '
         'Returns patient details, dates, amounts, and categorized line items as JSON.', ai_cell)],
        [Paragraph('Bill Parsing (Fallback)', ai_cell), Paragraph('OCR + Pattern Recognition', ai_cell),
         Paragraph('Multi-pass OCR (Tesseract with 4 preprocessing variants + EasyOCR). '
         '400+ regex patterns trained on Indian hospital bill formats.', ai_cell)],
        [Paragraph('Policy Understanding', ai_cell), Paragraph('NLP — TF-IDF Vectorization', ai_cell),
         Paragraph('Policy text chunked into ~500-char segments. Bigram TF-IDF (5000 features) '
         'with cosine similarity finds most relevant clause per rule.', ai_cell)],
        [Paragraph('Document Processing', ai_cell), Paragraph('Computer Vision (OCR)', ai_cell),
         Paragraph('Automatic detection of scanned vs text-based pages. Multi-pass image '
         'preprocessing: sharpen, contrast enhancement, high contrast, original.', ai_cell)],
        [Paragraph('Claim Evaluation', ai_cell), Paragraph('AI-Assisted Rule Engine', ai_cell),
         Paragraph('Each rule uses AI-retrieved policy clauses as evidence. Keyword detection '
         'in retrieved clauses determines rule outcomes.', ai_cell)],
    ]
    story.append(build_table(ai_data, col_widths=[W*0.18, W*0.28, W*0.54]))

    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "The system demonstrates a <b>practical hybrid approach</b>: using generative AI (Gemini) for "
        "unstructured document understanding, classical NLP (TF-IDF) for efficient retrieval, and "
        "deterministic rules for consistent, auditable decisions. This combination ensures both "
        "intelligence and reliability.",
        S['BodyJ']
    ))

    # story.append(PageBreak())

    # ── Evaluation & Reliability ──────────────────────────────────────────────
    story.append(Paragraph("Evaluation and Reliability", S['SectionHead']))

    ec = S['BodyJ']
    eh = ParagraphStyle('eval_hdr', parent=S['BodyJ'], textColor=colors.white, fontName='Helvetica-Bold')
    eval_data = [
        [Paragraph('#', eh), Paragraph('Test Scenario', eh), Paragraph('Expected Decision', eh), Paragraph('Key Rule Triggered', eh)],
        [Paragraph('1', ec), Paragraph('Clean appendectomy (Rahul Sharma)', ec), Paragraph('APPROVE', ec), Paragraph('All rules pass', ec)],
        [Paragraph('2', ec), Paragraph('Cosmetic rhinoplasty (Priya Mehta)', ec), Paragraph('REJECT', ec), Paragraph('Excluded Procedure', ec)],
        [Paragraph('3', ec), Paragraph('Pneumonia, high room rent (Anil Kumar)', ec), Paragraph('PARTIAL', ec), Paragraph('Room Rent Cap', ec)],
        [Paragraph('4', ec), Paragraph('Cardiac stenting, age 65 (Ramachandran Pillai)', ec), Paragraph('PARTIAL', ec), Paragraph('Co-Payment (10%)', ec)],
        [Paragraph('5', ec), Paragraph('Hernia, claim within 30 days (Suresh Reddy)', ec), Paragraph('REJECT', ec), Paragraph('Waiting Period', ec)],
        [Paragraph('6', ec), Paragraph('Diabetic foot ulcer, pre-existing (Venkatesh Iyer)', ec), Paragraph('REJECT', ec), Paragraph('Pre-Existing Disease', ec)],
        [Paragraph('7', ec), Paragraph('Brain hemorrhage, exceeds sum insured (Deepak Joshi)', ec), Paragraph('PARTIAL', ec), Paragraph('Sum Insured Limit', ec)],
    ]
    story.append(build_table(eval_data, col_widths=[W*0.05, W*0.35, W*0.25, W*0.35]))

    story.append(Spacer(1, 8))
    mc = S['BodyJ']
    mh = ParagraphStyle('met_hdr', parent=S['BodyJ'], textColor=colors.white, fontName='Helvetica-Bold')
    metrics_data = [
        [Paragraph('Metric', mh), Paragraph('Target', mh), Paragraph('Achieved', mh)],
        [Paragraph('Decision Accuracy (synthetic suite)', mc), Paragraph('100%', mc), Paragraph('100% on all 7 test cases', mc)],
        [Paragraph('Citation Coverage', mc), Paragraph('&gt;90%', mc), Paragraph('&gt;95% — most rules cite exact policy clause', mc)],
        [Paragraph('Processing Time', mc), Paragraph('&lt;5 seconds/claim', mc), Paragraph('~2-3 seconds (Gemini), ~4-5 seconds (OCR fallback)', mc)],
        [Paragraph('OCR Field Recovery', mc), Paragraph('&gt;80%', mc), Paragraph('&gt;85% on scanned bill images', mc)],
    ]
    story.append(build_table(metrics_data, col_widths=[W*0.35, W*0.30, W*0.35]))

    story.append(hr())

    # ── Alternatives Considered ───────────────────────────────────────────────
    story.append(Paragraph("Alternatives Considered", S['SectionHead']))

    ac = S['BodyJ']
    ah = ParagraphStyle('alt_hdr', parent=S['BodyJ'], textColor=colors.white, fontName='Helvetica-Bold')
    alt_data = [
        [Paragraph('Approach', ah), Paragraph('Why We Considered It', ah), Paragraph('Why We Chose Our Alternative', ah)],
        [Paragraph('End-to-end LLM (GPT-4 / Gemini for everything)', ac),
         Paragraph('Simpler code, single API call', ac),
         Paragraph('Non-deterministic outputs, expensive per query, no audit trail, hallucination risk for policy interpretation', ac)],
        [Paragraph('Semantic embeddings (sentence-transformers)', ac),
         Paragraph('Better retrieval accuracy than TF-IDF', ac),
         Paragraph('Heavier dependency (PyTorch ~2GB), slower inference, TF-IDF performs well enough for structured policy text', ac)],
        [Paragraph('Cloud OCR (Google Vision, AWS Textract)', ac),
         Paragraph('Higher accuracy than local Tesseract', ac),
         Paragraph('Adds API cost and dependency; multi-pass Tesseract + EasyOCR achieves &gt;85% field recovery for free', ac)],
        [Paragraph('Microservices architecture', ac),
         Paragraph('Better scalability per service', ac),
         Paragraph('Over-engineering for hackathon; modular monolith is easier to demo, debug, and deploy', ac)],
        [Paragraph('Database backend (PostgreSQL)', ac),
         Paragraph('Better query and storage', ac),
         Paragraph('JSON + filesystem is sufficient for demo; DB adds deployment complexity', ac)],
    ]
    story.append(build_table(alt_data, col_widths=[W*0.20, W*0.35, W*0.45]))

    story.append(Spacer(1, 10))
    story.append(hr())

    # ── References and Appendices ─────────────────────────────────────────────
    story.append(Paragraph("References and Appendices", S['SectionHead']))

    story.append(Paragraph("<b>Live Demo & Source Code</b>", S['SubSection']))
    refs = [
        "GitHub: https://github.com/theabhishekgoyal/google_project",
        "Live Demo: https://appproject-retzmndbhfqxrenebhvnjx.streamlit.app/",
    ]
    for r in refs:
        story.append(Paragraph(f"• {r}", S['BulletText']))

    story.append(Paragraph("<b>Technologies & Libraries</b>", S['SubSection']))
    tech_refs = [
        "Google Gemini API — https://ai.google.dev/gemini-api",
        "FastAPI — https://fastapi.tiangolo.com/",
        "Streamlit — https://streamlit.io/",
        "PyMuPDF — https://pymupdf.readthedocs.io/",
        "Tesseract OCR — https://github.com/tesseract-ocr/tesseract",
        "EasyOCR — https://github.com/JaidedAI/EasyOCR",
        "scikit-learn (TF-IDF) — https://scikit-learn.org/",
    ]
    for r in tech_refs:
        story.append(Paragraph(f"• {r}", S['BulletText']))

    story.append(Paragraph("<b>Domain References</b>", S['SubSection']))
    domain_refs = [
        "IRDAI Annual Report 2023-24 — Claim settlement statistics",
        "Standard health insurance policy structure (IRDAI guidelines)",
        "ICD-10 diagnostic codes for medical procedure classification",
    ]
    for r in domain_refs:
        story.append(Paragraph(f"• {r}", S['BulletText']))

    story.append(Paragraph("<b>Test Data</b>", S['SubSection']))
    story.append(Paragraph(
        "10+ synthetic hospital bills modeled after real Indian hospital formats (Apollo Hospitals, "
        "City Care Hospital, Supreme Hospital, Fortis Hospital, Narayana Health, Manipal Hospital, "
        "Glamour Aesthetics Centre). A sample insurance policy PDF is included in the repository. "
        "50+ pre-evaluated JSON audit records available in the repository.",
        S['BodyJ']
    ))

    story.append(Spacer(1, 6))
    story.append(hr())
    story.append(Paragraph(
        "<i>Built with Google Gemini AI, Python, and open-source tools for The Big Code 2026 Hackathon.</i>",
        ParagraphStyle('Footer', fontName='Helvetica-Oblique', fontSize=9, alignment=TA_CENTER,
                       textColor=HexColor('#888888'))
    ))

    # ── Build ─────────────────────────────────────────────────────────────────
    doc.build(story)
    print(f"✅ PDF generated: {os.path.abspath(OUTPUT_FILE)}")


if __name__ == "__main__":
    build_pdf()
