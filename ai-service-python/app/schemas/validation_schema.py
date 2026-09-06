import time
import uuid
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ValidationSeverity(str, Enum):
    """Severity tier for validation findings."""
    ERROR = "ERROR"      # Critical structural, referential, or data integrity violation.
    WARNING = "WARNING"  # Non-blocking ambiguity, conflict, or unverified assertion needing reviewer attention.
    INFO = "INFO"        # Informational telemetry or audit trace.


class ValidationGatingStatus(str, Enum):
    """
    Deterministic case-level outcome deciding whether a CaseEnvelope is safe for human review presentation.
    Note: READY_FOR_REVIEW denotes structural and integrity soundness, NOT that AI extractions are infallibly true.
    """
    READY_FOR_REVIEW = "READY_FOR_REVIEW"                      # Passed all integrity checks; safe for immediate presentation.
    REVIEW_WITH_WARNINGS = "REVIEW_WITH_WARNINGS"              # Structurally valid, but has warnings/conflicts requiring reviewer scrutiny.
    BLOCKED_BY_INTEGRITY_ERROR = "BLOCKED_BY_INTEGRITY_ERROR"  # Failed critical structural/referential checks; blocked from clean presentation.


class ValidationIssue(BaseModel):
    """
    Structured machine-readable representation of a specific validation finding.
    """
    issue_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8], description="Unique issue identifier")
    code: str = Field(..., description="Machine-readable violation code (e.g. EVIDENCE_DANGLING_SOURCE)")
    severity: ValidationSeverity = Field(..., description="Severity level: ERROR, WARNING, or INFO")
    message: str = Field(..., description="Human-readable explanation of the validation issue")
    object_type: str = Field(..., description="Target entity type: Fact, Evidence, CaseEnvelope, Payload, or Verification")
    object_id: Optional[str] = Field(default=None, description="Identifier of the offending object (e.g. fact_id or evidence_id)")
    field: Optional[str] = Field(default=None, description="Specific clinical/regulatory field name if applicable")
    related_ids: List[str] = Field(default_factory=list, description="Related entity identifiers involved in the issue")


class ValidationReport(BaseModel):
    """
    Comprehensive machine-readable report summarizing Step 6 consistency and integrity validation.
    """
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8], description="Unique report identifier")
    envelope_id: str = Field(..., description="ID of the validated CaseEnvelope")
    passed: bool = Field(..., description="True if zero ERROR issues were discovered")
    gating_status: ValidationGatingStatus = Field(..., description="Deterministic gating determination for reviewer routing")
    errors: List[ValidationIssue] = Field(default_factory=list, description="Collection of critical integrity violations")
    warnings: List[ValidationIssue] = Field(default_factory=list, description="Collection of non-blocking warnings and conflicts")
    infos: List[ValidationIssue] = Field(default_factory=list, description="Collection of audit traces and informational notices")
    checked_counts: Dict[str, int] = Field(default_factory=dict, description="Audit counts of objects checked")
    summary: str = Field(..., description="Concise human-readable executive validation summary")
    timestamp: int = Field(default_factory=lambda: int(time.time()), description="Epoch timestamp of validation")
