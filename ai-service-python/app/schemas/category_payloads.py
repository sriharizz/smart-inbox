from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.schemas.fact_contract import Fact, Evidence

# -------------------------------------------------------------
# 1. ICSR (Individual Case Safety Report) Domain Models
# -------------------------------------------------------------

class IcsrPatient(BaseModel):
    """ICH E2B(R3) Section B.1: Patient Characteristics."""
    identifier: str = Field(default="Not stated", description="Patient initials or identifier (e.g. 'A.P. (Arthur Pendelton)')")
    age: str = Field(default="Not stated", description="Patient age at onset of reaction (e.g. '71 YRS')")
    sex: str = Field(default="Not stated", description="Patient gender/sex (e.g. 'MALE', 'FEMALE')")
    weight: str = Field(default="Not stated", description="Patient weight with units (e.g. '74 kg')")
    medical_history: str = Field(default="Not stated", description="Relevant prior conditions, risk factors, or pre-existing diseases")
    treated_indication: str = Field(default="Not stated", description="Medical condition treated by the suspect drug")
    facts: List[Fact] = Field(default_factory=list, description="Associated atomic patient facts")

class IcsrReporter(BaseModel):
    """ICH E2B(R3) Section A.2: Primary Source / Reporter Information."""
    name: str = Field(default="Not stated", description="Reporter full name and credentials")
    role: str = Field(default="Not stated", description="Reporter qualification: Physician, Pharmacist, Nurse, Consumer, etc.")
    institution: str = Field(default="Not stated", description="Reporting clinic, hospital, or department")
    country: str = Field(default="Not stated", description="Country of primary source")
    contact: str = Field(default="Not stated", description="Reporter email address, phone, or physical address")
    facts: List[Fact] = Field(default_factory=list, description="Associated atomic reporter facts")

class IcsrProduct(BaseModel):
    """ICH E2B(R3) Section B.4: Drug Information (Suspect Product)."""
    product_name: str = Field(default="Not stated", description="Brand name and generic substance")
    dose: str = Field(default="Not stated", description="Dose administered (e.g. '1g IV piggyback', strictly 'Not stated' if omitted)")
    frequency: str = Field(default="Not stated", description="Dosing schedule (strictly 'Not stated' if unstated)")
    route: str = Field(default="Not stated", description="Route of administration (e.g. 'Oral', 'Intravenous')")
    start_date: str = Field(default="Not stated", description="Therapy start date")
    stop_date: str = Field(default="Not stated", description="Therapy stop date")
    duration: str = Field(default="Not stated", description="Duration of therapy prior to adverse event onset")
    lot_number: str = Field(default="Not stated", description="Manufacturing batch or lot identifier")
    expiry_date: str = Field(default="Not stated", description="Product expiration date")
    facts: List[Fact] = Field(default_factory=list, description="Associated atomic product facts")

class IcsrReaction(BaseModel):
    """ICH E2B(R3) Section B.2: Reaction(s) / Adverse Event(s)."""
    adverse_event: str = Field(default="Not stated", description="Primary clinical adverse event term")
    onset_date: str = Field(default="Not stated", description="Date/time of first symptom presentation")
    outcome: str = Field(default="Not stated", description="Recovered, Recovering, Not Recovered, Fatal, Unknown")
    seriousness_criteria: List[str] = Field(default_factory=list, description="Hospitalization, Life-threatening, Death, Disability, etc.")
    dechallenge: str = Field(default="Not stated", description="Outcome after drug withdrawal (Positive, Negative, Not applicable, Not stated)")
    rechallenge: str = Field(default="Not stated", description="Outcome upon re-introduction (Positive, Negative, Not done, Not stated)")
    facts: List[Fact] = Field(default_factory=list, description="Associated atomic adverse reaction facts")

class IcsrLabTest(BaseModel):
    """ICH E2B(R3) Section B.3: Test / Laboratory Data."""
    test_name: str = Field(..., description="Name of laboratory assay (e.g. 'ALT', 'Serum Creatinine')")
    value: str = Field(..., description="Numerical or qualitative result")
    unit: str = Field(default="", description="Measurement units")
    reference_range: str = Field(default="Not stated", description="Normal biological reference interval")
    test_date: str = Field(default="Not stated", description="Date laboratory specimen obtained")

class IcsrPayload(BaseModel):
    """
    Decoupled payload populated exclusively when a communication contains ICSR safety elements.
    """
    patient: IcsrPatient = Field(default_factory=IcsrPatient)
    reporter: IcsrReporter = Field(default_factory=IcsrReporter)
    product: IcsrProduct = Field(default_factory=IcsrProduct)
    reaction: IcsrReaction = Field(default_factory=IcsrReaction)
    concomitant_drugs: List[Dict[str, str]] = Field(default_factory=list, description="Co-administered medications and dates")
    lab_tests: List[IcsrLabTest] = Field(default_factory=list, description="Structured chemistry, hematology, or pathology panels")
    clinical_narrative: str = Field(default="Not stated", description="Chronological, plain-language clinical narrative")
    facts: List[Fact] = Field(default_factory=list, description="All atomic facts belonging to this ICSR")

# -------------------------------------------------------------
# 2. PQC (Product Quality Complaint) Domain Models
# -------------------------------------------------------------

class PqcPhotoEvidence(BaseModel):
    """Specific observation and interpretation of photographic quality defect evidence."""
    detected: bool = Field(default=False, description="True if an image of physical defect is detected")
    observation: str = Field(default="Not stated", description="Direct physical observation (e.g. 'dark particulate flakes visible in solution')")
    interpretation: str = Field(default="Not stated", description="AI preliminary interpretation (e.g. 'possible particulate contamination')")
    evidence_ref: Optional[Evidence] = Field(default=None, description="Pointer to physical image asset or coordinates")

class PqcPayload(BaseModel):
    """
    Decoupled payload populated exclusively when a communication contains Product Quality Complaint elements.
    """
    product_name: str = Field(default="Not stated", description="Medicinal product name")
    lot_number: str = Field(default="Not stated", description="Manufacturing lot / batch number")
    expiry_date: str = Field(default="Not stated", description="Product expiry date")
    defect_type: str = Field(default="Not stated", description="Defect category: Packaging breach, Contamination, Defective seal, etc.")
    defect_description: str = Field(default="Not stated", description="Detailed physical defect description")
    packaging_breached: bool = Field(default=False, description="True if container closure integrity was compromised")
    patient_exposure: str = Field(default="Not stated", description="Exposure status: Administered, Partial infusion, Intercepted prior to use")
    quarantine_quantity_disposition: str = Field(default="Not stated", description="Quantity affected/quarantined and hospital disposition")
    photo_evidence: PqcPhotoEvidence = Field(default_factory=PqcPhotoEvidence)
    requires_human_review: bool = Field(default=False, description="Flag enforcing mandatory human visual inspection")
    facts: List[Fact] = Field(default_factory=list, description="All atomic facts belonging to this PQC")

# -------------------------------------------------------------
# 3. MI (Medical Information) Domain Models
# -------------------------------------------------------------

class MiPayload(BaseModel):
    """
    Decoupled payload populated exclusively when a communication represents a Medical Information inquiry.
    """
    product_or_topic: str = Field(default="Not stated", description="Subject medicinal product or therapeutic topic")
    inquiry_type: str = Field(default="Not stated", description="Inquiry category: Dosing, Stability, Dilution, Compatibility, Crushing, etc.")
    question_text: str = Field(default="Not stated", description="Exact question asked by reporter")
    clinical_context: str = Field(default="Not stated", description="Clinical rationale or setting for inquiry (e.g. ICU patient with NG tube)")
    information_requested: str = Field(default="Not stated", description="Pharmacological, pharmacokinetic, or regulatory information requested")
    explicit_no_ae_no_pqc: bool = Field(default=False, description="Explicit confirmation in source that no adverse event or quality defect occurred")
    facts: List[Fact] = Field(default_factory=list, description="All atomic facts belonging to this MI inquiry")

# -------------------------------------------------------------
# 4. Not Relevant Domain Models
# -------------------------------------------------------------

class NotRelevantPayload(BaseModel):
    """
    Decoupled payload populated when a communication is non-relevant to pharmacovigilance or quality.
    """
    relevance_determination: str = Field(default="Not Relevant", description="Commercial marketing, spam, academic conference, HR solicitation")
    exclusion_reason: str = Field(default="Not stated", description="Detailed regulatory justification for non-retention")
    facts: List[Fact] = Field(default_factory=list, description="All atomic facts belonging to this non-relevant communication")
