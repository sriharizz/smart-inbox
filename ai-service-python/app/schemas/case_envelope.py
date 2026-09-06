import uuid
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from app.schemas.triage_schema import TriageResult
from app.schemas.fact_contract import Fact, Evidence, FactStatus
from app.schemas.category_payloads import (
    IcsrPayload, PqcPayload, MiPayload, NotRelevantPayload
)

# -------------------------------------------------------------
# 1. Reviewer Focus & Synthesis Contracts
# -------------------------------------------------------------

class ReviewFocusCategory(str, Enum):
    """
    Taxonomy of actionable items requiring human reviewer intervention.
    """
    UNCERTAIN_HANDWRITING = "UNCERTAIN_HANDWRITING"       # Cursive notes or blurred clinic scans requiring manual deciphering.
    PHOTO_DEFECT_INSPECTION = "PHOTO_DEFECT_INSPECTION"   # Defect photo detected; mandatory visual confirmation required.
    EVIDENCE_CONFLICT = "EVIDENCE_CONFLICT"               # Disagreement between source artifacts (e.g. email vs PDF form).
    MISSING_CRITICAL_FIELD = "MISSING_CRITICAL_FIELD"     # Vital regulatory parameter is unstated (e.g. dose, lot).
    MULTILINGUAL_TRANSLATION = "MULTILINGUAL_TRANSLATION" # Foreign language submission needing reviewer translation check.
    EXPEDITED_15_DAY_CLOCK = "EXPEDITED_15_DAY_CLOCK"     # Serious adverse event requiring expedited 15-day regulatory clock.
    CATEGORY_AMBIGUITY = "CATEGORY_AMBIGUITY"             # Multi-label or borderline categorization needing review.
    FOLLOW_UP_CHANGE = "FOLLOW_UP_CHANGE"                 # Follow-up communication with modified clinical facts.

class ReviewFocusItem(BaseModel):
    """
    Specific, actionable issue surfaced directly to the human reviewer.
    """
    focus_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8], description="Unique identifier for focus item")
    category: ReviewFocusCategory = Field(..., description="Classification of the review issue")
    field_affected: Optional[str] = Field(default=None, description="Associated fact or field name")
    headline: str = Field(..., description="Short, user-facing summary headline")
    detail: str = Field(..., description="Actionable clinical or regulatory explanation")
    evidence_ref: Optional[Evidence] = Field(default=None, description="Direct clickable evidence pointer")
    action_suggested: str = Field(default="Verify and confirm", description="Suggested action: 'Verify photo', 'Resolve conflict', 'Accept'")

class FactSummaryStats(BaseModel):
    """
    Quantitative metrics on clinical certainty across the fact ledger.
    """
    total_facts: int = 0
    confirmed_count: int = 0
    not_stated_count: int = 0
    uncertain_count: int = 0
    conflict_count: int = 0

class ReviewerBrief(BaseModel):
    """
    Synthesized case overview designed to minimize human cognitive load and maximize review speed.
    """
    case_id: str = Field(..., description="Case or message identity")
    subject: str = Field(default="No subject", description="Email subject or document title")
    sender: str = Field(default="Unknown sender", description="Primary sender or reporter")
    received_date: str = Field(default="Unknown date", description="Date received")
    primary_category: str = Field(..., description="Primary regulatory classification")
    all_categories: List[str] = Field(default_factory=list, description="All assigned categories (multi-label)")
    confidence: float = Field(ge=0.0, le=1.0, default=1.0, description="Overall classification confidence")
    urgency: str = Field(default="STANDARD", description="CRITICAL, EXPEDITED, or STANDARD")
    
    # Core Reviewer Synthesis
    executive_summary: str = Field(..., description="Concise, high-value clinical executive brief")
    review_focus: List[ReviewFocusItem] = Field(default_factory=list, description="Curated list of actionable items needing review")
    
    # Fact & Evidence Statistics
    fact_stats: FactSummaryStats = Field(default_factory=FactSummaryStats)
    facts: List[Fact] = Field(default_factory=list, description="Key atomic facts relevant for reviewer display")
    evidence_ledger: List[Evidence] = Field(default_factory=list, description="All clickable evidence items supporting facts")
    
    # Conflicts & Missing Fields
    actionable_conflicts: List[str] = Field(default_factory=list, description="Explicit cross-source discrepancies")
    missing_critical_fields: List[str] = Field(default_factory=list, description="Critical regulatory fields that are NOT_STATED")

# -------------------------------------------------------------
# 2. Common Case / Result Envelope
# -------------------------------------------------------------

class CaseEnvelope(BaseModel):
    """
    Top-level result contract encapsulating multi-label triage, decoupled domain payloads,
    unified atomic fact ledger, and regulatory document summaries.
    """
    envelope_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8], description="Unique envelope UUID")
    message_id: str = Field(default="Unknown", description="Original intake message or file ID")
    source_filename: str = Field(default="Unknown", description="Primary source file name")
    received_date: Optional[str] = Field(default=None, description="Intake timestamp")
    language_detected: str = Field(default="English", description="Detected language: English, Spanish, German")
    
    # Multi-label Regulatory Triage
    triage: TriageResult = Field(..., description="Triage classification result with calibrated probabilities")
    
    # Summaries: Document Summary (10-15 sentences, assignment spec) vs. Reviewer Summary
    document_summary: str = Field(default="Not stated", description="10-15 sentence comprehensive document summary")
    reviewer_summary: str = Field(default="Not stated", description="Short, high-value reviewer executive synthesis")
    
    # Category-Aware Decoupled Domain Payloads
    icsr: Optional[IcsrPayload] = Field(default=None, description="Present when document contains ICSR safety elements")
    pqc: Optional[PqcPayload] = Field(default=None, description="Present when document contains Product Quality Complaint elements")
    mi: Optional[MiPayload] = Field(default=None, description="Present when document contains Medical Information inquiry")
    not_relevant: Optional[NotRelevantPayload] = Field(default=None, description="Present when document is Not Relevant")
    
    # Unified Fact Ledger & Evidence
    fact_ledger: List[Fact] = Field(default_factory=list, description="Atomic, category-independent clinical facts")
    
    # Synthesized Reviewer Brief
    reviewer_brief: Optional[ReviewerBrief] = Field(default=None, description="Pre-computed reviewer decision brief")
    
    # Performance & Diagnostics
    processing_time_ms: int = Field(default=0, description="Processing latency in milliseconds")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Extensible execution metadata")

    def __init__(self, **data):
        if "facts" in data and "fact_ledger" not in data:
            data["fact_ledger"] = data.pop("facts")
        super().__init__(**data)

    @property
    def facts(self) -> List[Fact]:
        """Convenience accessor for the atomic fact ledger."""
        return self.fact_ledger
