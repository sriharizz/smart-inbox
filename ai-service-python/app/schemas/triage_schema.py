from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class CategoryEnum(str, Enum):
    SAFETY_REPORT_ICSR = "Safety Report (ICSR)"
    QUALITY_COMPLAINT_PQC = "Quality Complaint (PQC)"
    INFO_REQUEST_MI = "Info Request (MI)"
    MEDICAL_INFORMATION_MI = "Medical Information (MI)"
    NOT_RELEVANT = "Not Relevant"

class TriageLabel(BaseModel):
    category: CategoryEnum = Field(description="One of the 4 pharmacovigilance triage buckets")
    confidence: float = Field(ge=0.0, le=1.0, description="Calibrated confidence score between 0.0 and 1.0")
    reason: str = Field(description="One-line clinical or regulatory justification for this category")

class TriageResult(BaseModel):
    is_multi_label: bool = Field(default=False, description="True if document belongs to multiple buckets (e.g. ICSR + PQC)")
    primary_category: CategoryEnum = Field(description="The primary classification category")
    labels: List[TriageLabel] = Field(description="All assigned categories with individual confidence scores and reasons")
    executive_summary: str = Field(description="10-15 sentence comprehensive executive summary explaining clinical relevance and urgency")
