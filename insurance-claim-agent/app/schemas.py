from pydantic import BaseModel
from typing import List, Optional
from datetime import date


class ClaimMetadata(BaseModel):
    policy_start_date: Optional[date] = None
    claim_date: Optional[date] = None
    sum_insured: Optional[float] = 500000.0


class Citation(BaseModel):
    page: int
    clause_text: str


class RuleResult(BaseModel):
    rule_id: str
    name: str
    status: str  # "pass", "fail", or "info"
    reason: str
    citation: Optional[Citation] = None


class ClaimDecision(BaseModel):
    audit_id: str
    decision: str  # "APPROVE", "REJECT", "PARTIAL"
    summary_reason: str
    approved_amount: Optional[float] = None
    rejected_amount: Optional[float] = None
    total_claimed: Optional[float] = None
    rules_fired: List[RuleResult]


class BillFacts(BaseModel):
    patient_name: Optional[str] = None
    hospital_name: Optional[str] = None
    admission_date: Optional[str] = None
    discharge_date: Optional[str] = None
    total_amount: Optional[float] = None
    room_rent_per_day: Optional[float] = None
    procedure_keywords: List[str] = []
    diagnosis_keywords: List[str] = []
    line_items: List["BillLineItem"] = []
    ocr_confidence: Optional[str] = None  # "high", "medium", "low"
    raw_text: str = ""


class BillLineItem(BaseModel):
    description: str
    amount: Optional[float] = None
    category: str = "other"  # room, surgery, medicine, diagnostic, consultation, icu, other


class PolicyChunk(BaseModel):
    text: str
    page: int
    heading: Optional[str] = None


class LineItemReconciliation(BaseModel):
    description: str
    amount: Optional[float] = None
    category: str
    status: str  # "covered", "excluded", "sub_limited", "unknown"
    reason: str
    citation: Optional[Citation] = None
