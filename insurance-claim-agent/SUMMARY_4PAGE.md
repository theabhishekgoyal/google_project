# Insurance Claim Settlement Agent — 4-Page Technical Summary

## Page 1: Problem Statement and Approach

### Problem
Insurance claim processing is slow, opaque, and frustrating for patients. Rejection reasons are buried in dense 50-page policy documents. Patients rarely understand why a claim was denied.

### Our Solution
An automated claim evaluation engine that:
1. Reads scanned hospital bills using OCR (Tesseract)
2. Parses complex policy PDFs into searchable clause chunks
3. Uses NLP (TF-IDF vectorization + cosine similarity) to match bill items against policy clauses
4. Applies a configurable rule engine (10 business rules) to determine claim eligibility
5. Returns APPROVE / REJECT / PARTIAL with **exact policy citations** (page number + clause text) for every decision

### Key Differentiators
- **Line-item reconciliation**: Each bill item is individually matched to the policy, not just a binary yes/no
- **Explainability first**: Every rejection includes the exact policy clause and page number
- **Deterministic + auditable**: Same input always produces same output; every decision has an audit trail
- **No paid APIs**: Built entirely with free, open-source tools running locally

---

## Page 2: Technical Architecture and Core Logic

### Architecture: Modular Monolith
Single FastAPI service with clean internal modules. Streamlit UI for demo.

### Processing Pipeline

```
Bill PDF/Image → OCR (Tesseract) → Text Extraction → Bill Fact Parser
                                                          ↓
Policy PDF → PyMuPDF Text Extraction → Policy Chunker → TF-IDF Index
                                                          ↓
                                          ← Clause Retriever (cosine similarity)
                                                          ↓
                            Bill Facts + Retrieved Clauses → Rule Engine (10 rules)
                                                          ↓
                                          Line-Item Reconciliation
                                                          ↓
                                    Decision Builder → APPROVE / REJECT / PARTIAL
                                                          ↓
                                         Audit Record (JSON) + UI Display
```

### Core AI/ML Algorithms

1. **OCR Pipeline**: Tesseract with PyMuPDF fallback. EasyOCR as secondary fallback.
   - Auto-detects scanned vs text-based pages (threshold: < 50 characters)
   - Processes at 300 DPI for optimal accuracy

2. **NLP Retrieval (TF-IDF + Cosine Similarity)**:
   - Policy text is chunked into paragraph-level segments (~500 chars) with page metadata
   - Each chunk is vectorized using TF-IDF with bigrams (ngram_range=1,2)
   - For each rule query, cosine similarity finds the most relevant policy clause
   - Domain-specific preprocessing: OCR artifact correction, insurance stop-word removal

3. **Rule Engine**:
   - 10 configurable rules in YAML, each with query terms for clause retrieval
   - Rules: Waiting Period, Room Rent Cap, Excluded Procedure, Pre-Existing Disease, Co-Pay, Sum Insured Limit, Minimum Hospitalization, Non-Medical Items, Daycare Procedure, Documentation Completeness
   - Hard reject rules (Exclusion, Waiting Period) override partial approval

4. **Line-Item Reconciliation**:
   - Bill items are classified into categories (room, surgery, medicine, diagnostic, etc.)
   - Each item is matched against policy clauses using category-specific queries
   - Items are classified as: covered, excluded, sub-limited, or unknown

### Data Structures
- `PolicyChunk`: (text, page_number, heading) — indexed by TF-IDF
- `BillLineItem`: (description, amount, category) — classified by keyword matching
- `RuleResult`: (rule_id, status, reason, citation) — with page-level traceability
- `LineItemReconciliation`: (description, amount, status, reason, citation)

---

## Page 3: Evaluation and Reliability

### Test Strategy
We use a synthetic test suite since real medical bills contain sensitive data.

### Test Cases

| # | Scenario | Expected | Key Rule Triggered |
|---|----------|----------|-------------------|
| 1 | Clean appendectomy claim | APPROVE | None (all pass) |
| 2 | Cosmetic rhinoplasty | REJECT | Excluded Procedure |
| 3 | Pneumonia, high room rent | PARTIAL | Room Rent Cap |
| 4 | Claim within 15 days of policy | REJECT | Waiting Period |
| 5 | Diabetes treatment, new policy | REJECT | Pre-Existing Disease |

### Evaluation Metrics

| Metric | Target | Description |
|--------|--------|-------------|
| Decision Accuracy | 100% on synthetic suite | Correct APPROVE/REJECT/PARTIAL |
| Citation Coverage | >90% | % of rules with a valid policy citation |
| Retrieval Relevance | Manual check | Is the cited clause semantically correct? |
| Processing Time | <5 seconds per claim | End-to-end on CPU |
| OCR Extraction Rate | >80% field recovery | Fields extracted from scanned bills |

### Error Analysis
- **OCR noise**: Scanned bills may produce garbled text. Solution: amount minimum thresholds (₹100+), OCR artifact correction
- **Amount extraction**: Indian number formats (1,00,000) handled via multiple regex patterns
- **Policy chunk boundary**: Important clauses may span chunk boundaries. Solution: overlapping chunks, paragraph-level splitting
- **Ambiguous items**: Some bill items don't clearly map to any policy category. Solution: "unknown" status with manual review suggestion

### Reliability
- Deterministic: same input → same output
- Graceful fallback: OCR failure doesn't crash; missing fields flagged as "info" not "fail"
- Audit trail: every decision saved as JSON with unique audit ID

---

## Page 4: Impact, Scalability, and Future Work

### Real-World Impact
- **For patients**: Clear, readable explanations with exact policy references
- **For insurers**: Automated first-pass evaluation reduces manual review time
- **For regulators**: Full audit trail with traceable decisions and citations
- **Estimated efficiency**: 10x faster than manual review for straightforward claims

### Architectural Scalability
The modular design supports:
- Replacing TF-IDF with semantic embeddings (sentence-transformers) without changing the rule engine
- Adding new rules via YAML config without code changes
- Swapping OCR backend (Tesseract ↔ EasyOCR ↔ cloud) via the abstraction layer
- Scaling to multiple concurrent claims via FastAPI async + worker queues

### Technology Stack (All Free/Open-Source)

| Component | Technology | Purpose |
|-----------|------------|---------|
| Backend | FastAPI + Uvicorn | REST API |
| UI | Streamlit | Interactive demo |
| OCR | Tesseract / EasyOCR | Scanned document processing |
| PDF Parsing | PyMuPDF | Text extraction |
| NLP | scikit-learn TF-IDF | Clause retrieval |
| Config | YAML | Rule definitions |
| Storage | JSON + filesystem | Audit records |

### Future Improvements
1. **Named Entity Recognition** (spaCy/medaCy) for better medical field extraction
2. **Semantic embeddings** (sentence-transformers) for higher retrieval accuracy
3. **LLM-assisted explanations** for more natural language rejection reasons
4. **Database-backed storage** (PostgreSQL) for production-grade audit history
5. **Human-in-the-loop** review workflow for ambiguous cases
6. **Confidence scoring** per rule to flag low-confidence decisions
7. **Multi-language OCR** for regional hospital bills
8. **PDF table extraction** for structured bill parsing

### Conclusion
This system demonstrates that practical AI (OCR + NLP + deterministic rules) can solve a real, high-stakes problem while maintaining full transparency and accountability. The architecture is designed for correctness and explainability first, with clear extension paths for production deployment.
