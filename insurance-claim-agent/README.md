# 🏥 Insurance Claim Settlement Agent

An AI-powered system that evaluates medical insurance claims against policy documents — producing **transparent, auditable decisions** with exact policy citations, rule-by-rule reasoning, and line-item reconciliation.

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green?logo=fastapi)
![Streamlit](https://img.shields.io/badge/Streamlit-UI-red?logo=streamlit)
![Gemini](https://img.shields.io/badge/Google_Gemini-Vision_API-orange?logo=google)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## Problem

Insurance claim processing is **slow, opaque, and error-prone**. Policyholders rarely understand why a claim was rejected. Manual adjudication takes days and lacks consistency.

## Solution

This system **automates claim evaluation** in seconds and provides:

- A clear decision: **APPROVE**, **REJECT**, or **PARTIAL**
- Human-readable reasons for every rule checked
- Exact **policy citations** (page number + clause text) for transparency
- **Line-item reconciliation** — each bill item mapped to coverage status
- A full **audit trail** saved as JSON for accountability

---

## Architecture

```
User uploads Policy PDF + Hospital Bill
        │
        ▼
┌──────────────────────────────────┐
│  Document Processing Layer       │
│  PyMuPDF + Multi-Pass OCR        │
│  (Tesseract → EasyOCR fallback)  │
└──────────┬───────────────────────┘
           │
     ┌─────┴──────┐
     ▼            ▼
┌──────────┐ ┌───────────────┐
│ Bill     │ │ Policy        │
│ Parser   │ │ Chunker       │
│          │ │ (~500 char    │
│ Primary: │ │  segments     │
│ Gemini   │ │  with page    │
│ Vision   │ │  metadata)    │
│          │ │               │
│ Fallback:│ └──────┬────────┘
│ OCR +    │        │
│ Regex    │ ┌──────▼────────┐
└────┬─────┘ │ TF-IDF        │
     │       │ Clause        │
     │       │ Retriever     │
     │       │ (bigrams +    │
     │       │  cosine sim)  │
     │       └──────┬────────┘
     │              │
     └──────┬───────┘
            ▼
   ┌─────────────────┐
   │  Rule Engine     │  ← 10 YAML-configured deterministic rules
   │  + Line-Item     │
   │  Reconciliation  │
   └───────┬─────────┘
           ▼
   ┌─────────────────┐
   │ Decision Builder │  → APPROVE / REJECT / PARTIAL
   │ + Audit Record   │  → Summary + amounts + citations
   └───────┬─────────┘
           ▼
   ┌─────────────────┐
   │ Streamlit UI     │  Interactive result display
   │ + FastAPI        │  Programmatic API access
   └─────────────────┘
```

---

## AI & Algorithm Stack

| Component | Technique | Purpose |
|-----------|-----------|---------|
| **Bill Parsing** | Google Gemini Vision API | Primary: structured extraction from bill images/PDFs |
| **OCR** | Tesseract + EasyOCR (multi-pass, 4 variants) | Fallback text extraction from scanned documents |
| **Text Extraction** | PyMuPDF with quality scoring | Parse text-based PDFs page by page |
| **Retrieval** | TF-IDF (bigrams, 5000 features) + cosine similarity | Find most relevant policy clause for each rule |
| **Bill Parsing (Fallback)** | 400+ regex patterns + keyword matching | Extract structured facts when Gemini unavailable |
| **Rule Engine** | YAML-configured deterministic rules | Evaluate claim against 10 business rules |
| **Reconciliation** | Category-based policy matching | Per-line-item coverage determination |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+, FastAPI, Uvicorn |
| UI | Streamlit |
| AI / ML | Google Gemini Vision API, scikit-learn (TF-IDF) |
| PDF Processing | PyMuPDF (`fitz`) |
| OCR | pytesseract, EasyOCR, Pillow |
| Data Validation | Pydantic |
| Configuration | PyYAML |
| Storage | Local filesystem (JSON) |

---

## Project Structure

```
insurance-claim-agent/
├── app/
│   ├── main.py                    # FastAPI entry point + CORS
│   ├── schemas.py                 # Pydantic data models
│   ├── api/
│   │   └── routes_claims.py       # API endpoints (evaluate, get result)
│   ├── services/
│   │   ├── gemini_parser.py       # Gemini Vision API bill parser (primary)
│   │   ├── extract_pdf.py         # PDF text extraction + OCR fallback
│   │   ├── ocr_service.py         # Multi-pass OCR (Tesseract + EasyOCR)
│   │   ├── normalize.py           # Text cleaning + OCR artifact fixing
│   │   ├── parse_bill.py          # Regex-based bill parser (fallback)
│   │   ├── chunk_policy.py        # Policy chunking with page metadata
│   │   ├── retrieve_clause.py     # TF-IDF clause retrieval
│   │   ├── rules_engine.py        # 10-rule evaluation engine
│   │   ├── reconcile.py           # Per-line-item policy reconciliation
│   │   └── decision_builder.py    # Final decision + audit record
│   ├── config/
│   │   └── rules.yaml             # Business rules configuration
│   └── storage/
│       ├── uploads/               # Uploaded files
│       ├── outputs/               # JSON audit records
│       ├── logs/                  # Application logs
│       └── samples/               # Generated test data
├── ui/
│   └── streamlit_app.py           # Streamlit interactive interface
├── tests/
│   ├── test_rules_engine.py       # Unit tests for all 10 rules
│   ├── evaluate.py                # End-to-end evaluation script
│   └── generate_samples.py        # Sample data generator (7 scenarios)
├── .env.example                   # Environment variable template
├── .gitignore                     # Git ignore rules
├── requirements.txt               # Python dependencies
└── README.md
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- (Optional) [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) — auto-detected if installed; EasyOCR works without it
- (Optional) [Google Gemini API Key](https://aistudio.google.com/apikey) — for AI-powered bill parsing; system works without it using OCR + regex

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/insurance-claim-agent.git
cd insurance-claim-agent

# Create virtual environment
python -m venv .venv
source .venv/bin/activate       # Linux/macOS
# .venv\Scripts\activate        # Windows

# Install dependencies
pip install -r requirements.txt
```

### Configuration

```bash
# Copy the example env file and add your Gemini API key
cp .env.example .env
# Edit .env and set GEMINI_API_KEY=your_key_here
```

### Generate Sample Data

```bash
python -m tests.generate_samples
```

### Run the API Server

```bash
uvicorn app.main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

### Run the Streamlit UI

```bash
streamlit run ui/streamlit_app.py
```

### Run Tests

```bash
# Unit tests
python -m pytest tests/test_rules_engine.py -v

# End-to-end evaluation
python -m tests.evaluate
```

---

## Business Rules

The system evaluates **10 deterministic rules** configured in `app/config/rules.yaml`:

| # | Rule | What It Checks | Decision Impact |
|---|------|---------------|-----------------|
| 1 | Waiting Period | Claim within 30-day initial waiting period | Hard reject |
| 2 | Room Rent Cap | Room rent exceeds 1% of sum insured/day | Partial (proportionate deduction) |
| 3 | Excluded Procedure | Cosmetic, dental, fertility, weight loss, etc. | Hard reject |
| 4 | Pre-Existing Disease | Diabetes, hypertension, etc. within 4-year window | Hard reject |
| 5 | Co-Pay | Co-payment percentage (age-based) | Deduction |
| 6 | Sum Insured Limit | Claimed amount exceeds sum insured | Partial or reject |
| 7 | Min Hospitalization | Less than 24 hours of stay | Fail |
| 8 | Non-Medical Items | Toiletries, telephone, TV, guest meals | Deduction |
| 9 | Daycare Procedure | Same-day admit/discharge detection | Info |
| 10 | Documentation | Missing patient name, hospital, amount, dates | Info |

---

## Test Cases

| # | Scenario | Bill Amount | Expected | Description |
|---|----------|-------------|----------|-------------|
| 1 | Appendectomy | ₹65,000 | APPROVE | Clean claim, all rules pass |
| 2 | Cosmetic rhinoplasty | ₹94,000 | REJECT | Excluded procedure |
| 3 | Pneumonia (room ₹8K/day) | ₹77,000 | PARTIAL | Room rent exceeds cap |
| 4 | Hernia (within 30 days) | ₹75,800 | REJECT | Waiting period violation |
| 5 | Diabetic foot | ₹1,01,000 | REJECT | Pre-existing disease |
| 6 | Senior cardiac (age 65) | ₹1,77,800 | PARTIAL | 10% co-pay applicable |
| 7 | Hemorrhage | ₹6,25,000 | PARTIAL | Exceeds ₹5L sum insured |

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/claims/evaluate` | Upload policy + bill, get decision |
| `GET` | `/claims/{audit_id}` | Retrieve stored evaluation |
| `GET` | `/health` | Health check |

### Sample Request

```bash
curl -X POST http://localhost:8000/claims/evaluate \
  -F "policy_file=@policy.pdf" \
  -F "bill_file=@bill.pdf" \
  -F "sum_insured=500000"
```

### Sample Response

```json
{
  "audit_id": "CLM-20260404-A1B2C3",
  "decision": "PARTIAL",
  "summary_reason": "Partially approved. Issues found: Room Rent Cap Check.",
  "approved_amount": 64167,
  "rejected_amount": 12833,
  "total_claimed": 77000,
  "rules_fired": [
    {
      "rule_id": "ROOM_RENT_CAP",
      "name": "Room Rent Cap Check",
      "status": "fail",
      "reason": "Claimed room rent of 8000.0/day exceeds the allowed cap of 5000.0/day.",
      "citation": {
        "page": 6,
        "clause_text": "Room Rent is limited to a maximum of 1% of the Sum Insured per day..."
      }
    }
  ]
}
```

---

## How It Works

### Bill Parsing Pipeline

```
Bill Document (PDF/Image)
      │
      ├─→ Gemini Vision API (primary)
      │     ├── Structured JSON extraction
      │     ├── Tries 3 models in order
      │     └── Rate-limit retry (10s)
      │
      └─→ OCR + Regex (fallback)
            ├── Multi-pass OCR (4 preprocessing variants)
            ├── Quality scoring (length + word validity + domain signals)
            └── 400+ regex patterns for field extraction
```

### Policy Retrieval Pipeline

```
Policy PDF
  → Page-wise text extraction (PyMuPDF)
  → Quality check (< 60% → OCR)
  → Chunking (~500 chars, paragraph boundaries)
  → TF-IDF vectorization (bigrams, 5000 features)
  → Cosine similarity retrieval per rule query
  → Citations with page numbers
```

---

## Evaluation Metrics

| Metric | Description |
|--------|-------------|
| **Decision Accuracy** | % of test cases with correct APPROVE/REJECT/PARTIAL |
| **Citation Coverage** | % of rule evaluations with a policy clause citation |
| **Processing Time** | Average seconds per claim evaluation |
| **Retrieval Quality** | Semantic relevance of cited clauses to rules |

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEY` | No | — | Google Gemini API key for bill parsing |
| `TESSERACT_PATH` | No | Auto-detected | Path to Tesseract OCR binary |

---

## Future Improvements

- Named Entity Recognition (NER) for medical field extraction
- Semantic embeddings (sentence-transformers) instead of TF-IDF
- LLM-assisted explanation generation
- Database-backed audit history (PostgreSQL)
- Multi-policy comparison
- Human-in-the-loop review workflow
- Confidence scoring per rule
- Batch claim processing
- Webhook notifications

---

## License

This project is built for educational and evaluation purposes. All tools and libraries used are free and open-source.
