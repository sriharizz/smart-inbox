from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.schemas.triage_schema import TriageResult

class SourceCitation(BaseModel):
    source_type: str = Field(default="email", description="'email' or 'pdf'")
    page_or_location: str = Field(default="body", description="Page number or section name (e.g. 'Page 1', 'Email body')")
    verbatim_snippet: str = Field(default="Not stated", description="Exact verbatim snippet quoted from the original source")

class PatientData(BaseModel):
    identifier: str = Field(default="Not stated", description="Patient name or initials (e.g. 'A.P. (Arthur Pendelton)')")
    age: str = Field(default="Not stated", description="Patient age or 'Not stated'")
    sex: str = Field(default="Not stated", description="Patient sex (Male, Female) or 'Not stated'")
    weight: str = Field(default="Not stated", description="Patient weight or 'Not stated'")
    medical_history: str = Field(default="Not stated", description="Relevant prior conditions, medications, or allergies")
    citation: SourceCitation = Field(default_factory=SourceCitation)

class ReporterData(BaseModel):
    name: str = Field(default="Not stated", description="Reporter full name or 'Not stated'")
    role: str = Field(default="Not stated", description="Physician, Pharmacist, Nurse, Consumer, etc.")
    institution: str = Field(default="Not stated", description="Hospital, clinic, or pharmacy name")
    country: str = Field(default="Not stated", description="Country of origin")
    email_or_phone: str = Field(default="Not stated", description="Contact information")
    citation: SourceCitation = Field(default_factory=SourceCitation)

class ProductData(BaseModel):
    product_name: str = Field(default="Not stated", description="Suspected medicinal product name")
    dose: str = Field(default="Not stated", description="Dose administered (strictly 'Not stated' if unstated)")
    frequency: str = Field(default="Not stated", description="Administration schedule or 'Not stated'")
    route: str = Field(default="Not stated", description="Route of administration (Oral, IV, IM, etc.)")
    lot_number: str = Field(default="Not stated", description="Manufacturing lot or batch number")
    expiry_date: str = Field(default="Not stated", description="Product expiration date")
    indication: str = Field(default="Not stated", description="Medical reason for prescribing")
    citation: SourceCitation = Field(default_factory=SourceCitation)

class ReactionData(BaseModel):
    adverse_event: str = Field(default="Not stated", description="Primary adverse event or medical term")
    onset_date: str = Field(default="Not stated", description="Date or time symptom started")
    outcome: str = Field(default="Not stated", description="Recovered, Recovering, Not Recovered, Fatal, Unknown")
    seriousness_criteria: List[str] = Field(default_factory=list, description="Hospitalization, Life-threatening, Death, Disability, etc.")
    dechallenge: str = Field(default="Not stated", description="Positive, Negative, Not applicable, or Not stated")
    rechallenge: str = Field(default="Not stated", description="Positive, Negative, Not done, or Not stated")
    citation: SourceCitation = Field(default_factory=SourceCitation)

class LabTestItem(BaseModel):
    test_name: str
    value: str
    unit: str
    reference_range: str = "Not stated"
    test_date: str = "Not stated"

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
    quality_complaint: Optional[QualityComplaintData] = None
    medical_info: Optional[MedicalInfoData] = None
    narrative: str = Field(default="Not stated", description="Clinical plain-language case narrative")
    processing_time_ms: int = 0
    envelope: Optional[Any] = Field(default=None, description="Canonical CaseEnvelope representation")

