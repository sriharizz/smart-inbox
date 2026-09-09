from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, model_validator
from app.schemas.triage_schema import TriageResult

class SourceCitation(BaseModel):
    source_type: str = Field(default="email", description="'email' or 'pdf' or 'image'")
    page_or_location: str = Field(default="body", description="Page number or section name (e.g. 'Page 1', 'Email body')")
    verbatim_snippet: str = Field(default="Not stated", description="Exact verbatim snippet quoted from the original source")
    source_id: str = Field(default="source_doc", description="Source file ID or document reference")
    source_name: Optional[str] = Field(default=None, description="Human-readable filename of source asset")
    page_number: Optional[int] = Field(default=None, description="1-indexed page number if PDF")
    bounding_box: Optional[Dict[str, Any]] = Field(default=None, description="Coordinates on rendered document page (x0, y0, x1, y1)")
    char_start: Optional[int] = Field(default=None, description="Character start offset in email body text stream")
    char_end: Optional[int] = Field(default=None, description="Character end offset in email body text stream")
    anchor_level: str = Field(default="LEVEL_3_SNIPPET_ONLY", description="LEVEL_1_EXACT_VISUAL, LEVEL_2_PAGE_TEXT, or LEVEL_3_SNIPPET_ONLY")
    verification_result: str = Field(default="SUPPORTS", description="SUPPORTS, CONTRADICTS, or INSUFFICIENT")
    verification_rationale: Optional[str] = Field(default=None, description="Clinical verification rationale")

class PatientData(BaseModel):
    identifier: str = Field(default="Not stated", description="Patient name or initials (e.g. 'A.P. (Arthur Pendelton)')")
    dob: str = Field(default="Not stated", description="Patient date of birth or 'Not stated'")
    age: str = Field(default="Not stated", description="Patient age or 'Not stated'")
    sex: str = Field(default="Not stated", description="Patient sex (Male, Female) or 'Not stated'")
    weight: str = Field(default="Not stated", description="Patient weight or 'Not stated'")
    country: str = Field(default="Not stated", description="Patient country of residence or 'Not stated'")
    medical_history: str = Field(default="Not stated", description="Relevant prior conditions, medications, or allergies")
    citation: SourceCitation = Field(default_factory=SourceCitation)

class ReporterData(BaseModel):
    name: str = Field(default="Not stated", description="Reporter full name or 'Not stated'")
    role: str = Field(default="Not stated", description="Physician, Pharmacist, Nurse, Consumer, etc.")
    specialty: str = Field(default="Not stated", description="Reporter specialty / department or 'Not stated'")
    institution: str = Field(default="Not stated", description="Hospital, clinic, or pharmacy name")
    country: str = Field(default="Not stated", description="Country of origin")
    email_or_phone: str = Field(default="Not stated", description="Contact information")
    health_professional: str = Field(default="Not stated", description="Yes / No health professional status")
    citation: SourceCitation = Field(default_factory=SourceCitation)

class ProductData(BaseModel):
    product_name: str = Field(default="Not stated", description="Suspected medicinal product name")
    formulation: str = Field(default="Not stated", description="Formulation or dosage form")
    dose: str = Field(default="Not stated", description="Dose administered (strictly 'Not stated' if unstated)")
    frequency: str = Field(default="Not stated", description="Administration schedule or 'Not stated'")
    route: str = Field(default="Not stated", description="Route of administration (Oral, IV, IM, etc.)")
    lot_number: str = Field(default="Not stated", description="Manufacturing lot or batch number")
    expiry_date: str = Field(default="Not stated", description="Product expiration date")
    indication: str = Field(default="Not stated", description="Medical reason for prescribing")
    start_date: str = Field(default="Not stated", description="Therapy start date")
    stop_date: str = Field(default="Not stated", description="Therapy stop date")
    duration: str = Field(default="Not stated", description="Duration of therapy")
    action_taken: str = Field(default="Not stated", description="Action taken with suspect drug")
    citation: SourceCitation = Field(default_factory=SourceCitation)

class ReactionData(BaseModel):
    adverse_event: str = Field(default="Not stated", description="Primary adverse event or medical term")
    onset_date: str = Field(default="Not stated", description="Date or time symptom started")
    outcome: str = Field(default="Not stated", description="Recovered, Recovering, Not Recovered, Fatal, Unknown")
    seriousness_criteria: List[str] = Field(default_factory=list, description="Hospitalization, Life-threatening, Death, Disability, etc.")
    hospitalization: bool = Field(default=False)
    admission_date: str = Field(default="Not stated")
    life_threatening: bool = Field(default=False)
    death: bool = Field(default=False)
    disability: bool = Field(default=False)
    congenital_anomaly: bool = Field(default=False)
    medically_important: bool = Field(default=False)
    dechallenge: str = Field(default="Not stated", description="Positive, Negative, Not applicable, or Not stated")
    rechallenge: str = Field(default="Not stated", description="Positive, Negative, Not done, or Not stated")
    citation: SourceCitation = Field(default_factory=SourceCitation)

    @model_validator(mode="after")
    def reconcile_seriousness(self) -> "ReactionData":
        crit_lower = [str(c).strip().lower() for c in self.seriousness_criteria if str(c).strip()]

        if any("non-serious" in c or "nonserious" in c for c in crit_lower):
            self.hospitalization = False
            self.life_threatening = False
            self.death = False
            self.disability = False
            self.congenital_anomaly = False
            self.medically_important = False
            return self

        for c in crit_lower:
            if "hospital" in c or "inpatient" in c:
                self.hospitalization = True
            if "life-threatening" in c or "life threatening" in c:
                self.life_threatening = True
            if "death" in c or "fatal" in c:
                self.death = True
            if "disab" in c or "incapacit" in c:
                self.disability = True
            if "congenital" in c or "birth defect" in c:
                self.congenital_anomaly = True
            if "medically important" in c or "medically significant" in c or "other medically" in c:
                self.medically_important = True

        if self.hospitalization and not any("hospital" in c or "inpatient" in c for c in crit_lower):
            self.seriousness_criteria.append("Hospitalization")
        if self.life_threatening and not any("life-threatening" in c or "life threatening" in c for c in crit_lower):
            self.seriousness_criteria.append("Life-threatening")
        if self.death and not any("death" in c or "fatal" in c for c in crit_lower):
            self.seriousness_criteria.append("Death")
        if self.disability and not any("disab" in c for c in crit_lower):
            self.seriousness_criteria.append("Disability/Incapacity")
        if self.congenital_anomaly and not any("congenital" in c for c in crit_lower):
            self.seriousness_criteria.append("Congenital Anomaly")
        if self.medically_important and not any("medically" in c for c in crit_lower):
            self.seriousness_criteria.append("Other Medically Important Condition")

        return self

class LabTestItem(BaseModel):
    test_name: str
    value: str
    unit: str
    reference_range: str = "Not stated"
    interpretation: str = "Not stated"
    test_date: str = "Not stated"
    citation: Optional[SourceCitation] = None

class ConcomitantMedicationItem(BaseModel):
    medication_name: str
    dose_and_route: str = "Not stated"
    indication: str = "Not stated"
    dates: str = "Not stated"
    status: str = "Ongoing"
    citation: Optional[SourceCitation] = None

class RegulatoryMetadata(BaseModel):
    mfr_control_number: str = "Not stated"
    date_received_by_mfr: str = "Not stated"
    report_type: str = "Initial"
    citation: Optional[SourceCitation] = None

class QualityComplaintData(BaseModel):
    product_name: str = Field(default="Not stated")
    lot_number: str = Field(default="Not stated")
    defect_type: str = Field(default="Not stated", description="Packaging breach, Contamination, Defective seal, Counterfeit, etc.")
    defect_description: str = Field(default="Not stated", description="Detailed physical defect description")
    packaging_breached: bool = Field(default=False)
    photo_detected: bool = Field(default=False, description="Whether a photo of physical defect is detected")
    photo_description: str = Field(default="Not stated", description="AI description of defect image pixels")
    requires_human_review: bool = Field(default=False, description="Flagged for immediate human safety review")
    citation: SourceCitation = Field(default_factory=SourceCitation)

class MedicalInfoData(BaseModel):
    product_or_topic: str = Field(default="Not stated")
    inquiry_type: str = Field(default="Not stated", description="Dosing, Stability, Dilution, Compatibility, Crushing, etc.")
    question_text: str = Field(default="Not stated", description="Specific medical question asked by reporter")
    citation: SourceCitation = Field(default_factory=SourceCitation)

class ExtractionResult(BaseModel):
    case_id: Optional[str] = None
    source_filename: str = "Unknown"
    language_detected: str = "English"
    triage: TriageResult
    patient: PatientData = Field(default_factory=PatientData)
    reporter: ReporterData = Field(default_factory=ReporterData)
    product: ProductData = Field(default_factory=ProductData)
    reaction: ReactionData = Field(default_factory=ReactionData)
    lab_tests: List[LabTestItem] = Field(default_factory=list)
    concomitant_medications: List[ConcomitantMedicationItem] = Field(default_factory=list)
    regulatory: Optional[RegulatoryMetadata] = None
    quality_complaint: Optional[QualityComplaintData] = None
    medical_info: Optional[MedicalInfoData] = None
    narrative: str = Field(default="Not stated", description="Clinical plain-language case narrative")
    processing_time_ms: int = 0
    extraction_status: str = Field(default="SUCCESS", description="SUCCESS, NEEDS_REVIEW, or FAILED")
    extraction_error: Optional[str] = Field(default=None, description="Diagnostic extraction error details")
    citations: Dict[str, SourceCitation] = Field(default_factory=dict, description="Fact-level source citations mapping field to citation")
    attachment_metadata: List["AttachmentMetadata"] = Field(default_factory=list, description="Per-attachment metadata including flavor and detected language")
    document_summary: Optional[str] = Field(default=None, description="10-15 sentence regulatory document summary")
    envelope: Optional[Any] = Field(default=None, description="Canonical CaseEnvelope representation")


class AttachmentMetadata(BaseModel):
    filename: str
    flavor: str
    language: str
    document_summary: Optional[str] = Field(default=None, description="10-15 sentence regulatory document summary for this attachment")


