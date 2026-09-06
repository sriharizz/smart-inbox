import uuid
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class FactStatus(str, Enum):
    """
    Four semantic states representing clinical knowledge certainty in pharmacovigilance.
    """
    CONFIRMED = "CONFIRMED"      # Source contains explicit and sufficient evidence.
    NOT_STATED = "NOT_STATED"    # Source omits the requested information; guessing is strictly barred.
    UNCERTAIN = "UNCERTAIN"      # Relevant mention exists but cannot be reliably resolved (e.g. illegible cursive, blurred scan).
    CONFLICT = "CONFLICT"        # Multiple claims or sections in the source disagree and require clinical resolution.

class VerificationResult(str, Enum):
    """
    NLI / verification status assessing whether a candidate evidence snippet establishes a fact.
    Note: Semantic similarity must never be confused with truth or logical support.
    """
    SUPPORTS = "SUPPORTS"          # Evidence logically and clinically supports the claim.
    CONTRADICTS = "CONTRADICTS"    # Evidence directly contradicts the claim (e.g. 'no adverse event' vs 'adverse event').
    INSUFFICIENT = "INSUFFICIENT"  # Evidence is insufficient or ambiguous to establish the claim.

class EvidenceType(str, Enum):
    """
    Underlying medium or structure where evidence was discovered.
    """
    EMAIL_BODY = "email_body"
    EMAIL_HEADER = "email_header"
    PDF_TEXT = "pdf_text"
    TABLE_CELL = "table_cell"
    DEFECT_IMAGE = "defect_image"
    SCANNED_PAGE = "scanned_page"
    OTHER = "other"

class BoundingBox(BaseModel):
    """Coordinates on a rendered PDF page (72/150 DPI) or photographic defect asset."""
    x0: float = Field(..., description="Left coordinate")
    y0: float = Field(..., description="Top coordinate")
    x1: float = Field(..., description="Right coordinate")
    y1: float = Field(..., description="Bottom coordinate")
    page_number: int = Field(default=1, description="1-indexed page number")

class LocationReference(BaseModel):
    """Structured location metadata enabling one-click navigation and text highlighting in reviewer UI."""
    page_number: Optional[int] = Field(default=None, description="1-indexed page number")
    section: Optional[str] = Field(default=None, description="Section or box identifier (e.g. 'Box 24a', 'Section B')")
    char_start: Optional[int] = Field(default=None, description="Character start offset in text stream")
    char_end: Optional[int] = Field(default=None, description="Character end offset in text stream")
    table_row: Optional[int] = Field(default=None, description="Table row index if extracted from structured table")
    table_col: Optional[int] = Field(default=None, description="Table column index if extracted from structured table")
    bounding_box: Optional[BoundingBox] = Field(default=None, description="Visual coordinates on rendered page or image")

class Evidence(BaseModel):
    """
    First-class Evidence model linking an extracted clinical fact to physical document proof.
    """
    evidence_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8], description="Unique evidence identifier")
    source_id: str = Field(..., description="Source document identifier or filename (e.g. 'email_04.eml', 'vial_contamination_sepsis.pdf')")
    source_type: EvidenceType = Field(default=EvidenceType.PDF_TEXT, description="Type of source artifact containing the evidence")
    page_or_location: str = Field(..., description="Human-readable location reference (e.g. 'Page 1, Box B.1', 'Email body paragraph 2')")
    verbatim_snippet: str = Field(..., description="Exact unparaphrased text snippet quoted directly from source")
    location: Optional[LocationReference] = Field(default=None, description="Structured location coordinates for UI jumping and highlighting")
    retrieval_metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata on how candidate evidence was retrieved (method, candidate rank)")
    verification_result: VerificationResult = Field(default=VerificationResult.INSUFFICIENT, description="Verification determination: SUPPORTS, CONTRADICTS, or INSUFFICIENT")

class Fact(BaseModel):
    """
    Atomic, category-independent Fact model representing a single clinical or regulatory assertion.
    """
    fact_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8], description="Unique atomic fact identifier")
    field: str = Field(..., description="Canonical clinical or regulatory field name (e.g. 'patient_age', 'suspect_product', 'adverse_event')")
    value: str = Field(..., description="Extracted textual value as stated in source, or 'Not stated'")
    normalized_value: Optional[Any] = Field(default=None, description="Canonical normalized representation (e.g. integer 71, ISO date '2025-11-14')")
    status: FactStatus = Field(default=FactStatus.CONFIRMED, description="Four-state semantic status: CONFIRMED, NOT_STATED, UNCERTAIN, CONFLICT")
    confidence: float = Field(ge=0.0, le=1.0, default=1.0, description="Per-fact calibrated extraction confidence score (0.0 to 1.0)")
    evidence: List[Evidence] = Field(default_factory=list, description="Associated evidence references proving or disproving this fact")
    verification_state: VerificationResult = Field(default=VerificationResult.INSUFFICIENT, description="Overall verification outcome: SUPPORTS, CONTRADICTS, or INSUFFICIENT")
    notes: Optional[str] = Field(default=None, description="Reviewer clarification, conflict notes, or ambiguity rationale")
