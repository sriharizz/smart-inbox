# Canonical schemas and contracts for Clinevo Smart Inbox

from app.schemas.fact_contract import (
    FactStatus,
    VerificationResult,
    EvidenceType,
    BoundingBox,
    LocationReference,
    Evidence,
    Fact,
)

from app.schemas.category_payloads import (
    IcsrPatient,
    IcsrReporter,
    IcsrProduct,
    IcsrReaction,
    IcsrLabTest,
    IcsrPayload,
    PqcPhotoEvidence,
    PqcPayload,
    MiPayload,
    NotRelevantPayload,
)

from app.schemas.case_envelope import (
    CaseEnvelope,
    ReviewFocusCategory,
    ReviewFocusItem,
    FactSummaryStats,
    ReviewerBrief,
)

from app.schemas.triage_schema import (
    CategoryEnum,
    TriageLabel,
    TriageResult,
)

from app.schemas.literature_schema import (
    LiteratureScreenResult,
)

from app.schemas.legacy_adapter import (
    envelope_to_legacy,
)

# Backward-compatibility layer: allow existing code to import ExtractionResult
from app.schemas.extraction_schema import (
    ExtractionResult,
    SourceCitation,
    PatientData,
    ReporterData,
    ProductData,
    ReactionData,
    LabTestItem,
    QualityComplaintData,
    MedicalInfoData,
)


__all__ = [
    # Foundational contracts
    "FactStatus",
    "VerificationResult",
    "EvidenceType",
    "BoundingBox",
    "LocationReference",
    "Evidence",
    "Fact",
    # Category payloads
    "IcsrPatient",
    "IcsrReporter",
    "IcsrProduct",
    "IcsrReaction",
    "IcsrLabTest",
    "IcsrPayload",
    "PqcPhotoEvidence",
    "PqcPayload",
    "MiPayload",
    "NotRelevantPayload",
    # Common envelope & reviewer brief
    "CaseEnvelope",
    "ReviewFocusCategory",
    "ReviewFocusItem",
    "FactSummaryStats",
    "ReviewerBrief",
    # Triage & Literature
    "CategoryEnum",
    "TriageLabel",
    "TriageResult",
    "LiteratureScreenResult",
    # Backward compatibility
    "ExtractionResult",
    "SourceCitation",
    "PatientData",
    "ReporterData",
    "ProductData",
    "ReactionData",
    "LabTestItem",
    "QualityComplaintData",
    "MedicalInfoData",
]
