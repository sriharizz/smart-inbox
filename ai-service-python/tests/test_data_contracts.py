import json
import pytest
from app.schemas.fact_contract import (
    FactStatus,
    VerificationResult,
    EvidenceType,
    LocationReference,
    BoundingBox,
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
    ReviewerBrief,
    ReviewFocusCategory,
    ReviewFocusItem,
    FactSummaryStats,
)
from app.schemas.triage_schema import (
    CategoryEnum,
    TriageLabel,
    TriageResult,
)
from app.core.llm_provider import LLMProvider, GeminiProvider, get_llm_provider

# -------------------------------------------------------------
# 1. FactStatus & VerificationResult Semantic Tests
# -------------------------------------------------------------

def test_fact_status_semantic_states():
    """Validates that exactly the 4 required semantic states exist and are distinct."""
    assert FactStatus.CONFIRMED.value == "CONFIRMED"
    assert FactStatus.NOT_STATED.value == "NOT_STATED"
    assert FactStatus.UNCERTAIN.value == "UNCERTAIN"
    assert FactStatus.CONFLICT.value == "CONFLICT"

    states = {FactStatus.CONFIRMED, FactStatus.NOT_STATED, FactStatus.UNCERTAIN, FactStatus.CONFLICT}
    assert len(states) == 4

def test_verification_result_semantic_states():
    """Validates that exactly the 3 required NLI verification outcomes exist."""
    assert VerificationResult.SUPPORTS.value == "SUPPORTS"
    assert VerificationResult.CONTRADICTS.value == "CONTRADICTS"
    assert VerificationResult.INSUFFICIENT.value == "INSUFFICIENT"

    outcomes = {VerificationResult.SUPPORTS, VerificationResult.CONTRADICTS, VerificationResult.INSUFFICIENT}
    assert len(outcomes) == 3

# -------------------------------------------------------------
# 2. Evidence Contract Tests
# -------------------------------------------------------------

def test_evidence_model_serialization_and_extensibility():
    """Validates Evidence serialization with structured location and verification result."""
    bbox = BoundingBox(x0=100.5, y0=200.0, x1=350.0, y1=450.0, page_number=2)
    location = LocationReference(
        page_number=2,
        section="Exhibit 1: Photo Log",
        char_start=500,
        char_end=580,
        bounding_box=bbox
    )
    evidence = Evidence(
        source_id="vial_contamination_sepsis.pdf",
        source_type=EvidenceType.DEFECT_IMAGE,
        page_or_location="Page 2, Exhibit 1",
        verbatim_snippet="compromised rubber stopper crimp seal with dark particulate suspension",
        location=location,
        retrieval_metadata={"method": "exact_span_search", "confidence": 0.99},
        verification_result=VerificationResult.SUPPORTS
    )

    data = evidence.model_dump()
    assert data["source_id"] == "vial_contamination_sepsis.pdf"
    assert data["source_type"] == "defect_image"
    assert data["verification_result"] == "SUPPORTS"
    assert data["location"]["bounding_box"]["x0"] == 100.5

    # Roundtrip json test
    json_str = evidence.model_dump_json()
    reloaded = Evidence.model_validate_json(json_str)
    assert reloaded.source_id == evidence.source_id
    assert reloaded.verification_result == VerificationResult.SUPPORTS

def test_evidence_types_coverage():
    """Ensures evidence types cover emails, PDFs, tables, scanned docs, and images."""
    types = {e.value for e in EvidenceType}
    expected = {"email_body", "email_header", "pdf_text", "table_cell", "defect_image", "scanned_page", "other"}
    assert expected.issubset(types)

# -------------------------------------------------------------
# 3. Atomic Fact Model Tests
# -------------------------------------------------------------

def test_atomic_fact_model_confirmed():
    """Validates Fact with CONFIRMED status, normalized value, and linked evidence."""
    ev = Evidence(
        source_id="email_04.eml",
        source_type=EvidenceType.EMAIL_BODY,
        page_or_location="Email paragraph 2",
        verbatim_snippet="patient Arthur Pendelton (71yo male) developed septic shock",
        verification_result=VerificationResult.SUPPORTS
    )
    fact = Fact(
        field="patient_age",
        value="71yo",
        normalized_value=71,
        status=FactStatus.CONFIRMED,
        confidence=0.98,
        evidence=[ev],
        verification_state=VerificationResult.SUPPORTS
    )

    assert fact.field == "patient_age"
    assert fact.normalized_value == 71
    assert fact.status == FactStatus.CONFIRMED
    assert len(fact.evidence) == 1
    assert fact.evidence[0].verification_result == VerificationResult.SUPPORTS

def test_atomic_fact_distinguishes_not_stated_uncertain_conflict():
    """Validates that NOT_STATED, UNCERTAIN, and CONFLICT are strictly distinct without guessing."""
    fact_not_stated = Fact(
        field="dose_frequency",
        value="Not stated",
        status=FactStatus.NOT_STATED,
        confidence=1.0
    )
    fact_uncertain = Fact(
        field="suspect_dose",
        value="0.3mg (?)",
        status=FactStatus.UNCERTAIN,
        confidence=0.55,
        notes="Illegible cursive script in urgent care handwritten record."
    )
    fact_conflict = Fact(
        field="event_onset_date",
        value="Discrepant: 10-NOV vs 14-NOV",
        status=FactStatus.CONFLICT,
        confidence=0.40,
        notes="Email body indicates 10-NOV onset; attached MedWatch indicates 14-NOV onset."
    )

    assert fact_not_stated.status == FactStatus.NOT_STATED
    assert fact_uncertain.status == FactStatus.UNCERTAIN
    assert fact_conflict.status == FactStatus.CONFLICT
    assert fact_not_stated.status != fact_uncertain.status
    assert fact_uncertain.status != fact_conflict.status

# -------------------------------------------------------------
# 4. Decoupled Category-Specific Payloads Tests
# -------------------------------------------------------------

def test_category_payloads_decoupling():
    """Ensures each domain payload can be populated independently without forcing irrelevant fields."""
    # PQC Payload without any ICSR fields
    pqc = PqcPayload(
        product_name="Cardioril 10mg",
        lot_number="BL-8802",
        defect_type="Blister delamination & chemical odor",
        defect_description="Aluminum foil seal peeled from PVC blister cavities",
        packaging_breached=True,
        requires_human_review=True
    )
    assert pqc.product_name == "Cardioril 10mg"
    assert pqc.packaging_breached is True
    assert not hasattr(pqc, "adverse_event")  # PQC does not have ICSR adverse_event

    # MI Payload without ICSR or PQC fields
    mi = MiPayload(
        product_or_topic="Corzapan 10mg",
        inquiry_type="Crushing / Administration",
        question_text="Can Corzapan tablets be crushed for administration via nasogastric tube?",
        explicit_no_ae_no_pqc=True
    )
    assert mi.product_or_topic == "Corzapan 10mg"
    assert mi.explicit_no_ae_no_pqc is True

    # Not Relevant Payload
    nr = NotRelevantPayload(
        relevance_determination="Commercial Marketing / Spam",
        exclusion_reason="Conference promotional announcement without patient safety data or quality defect."
    )
    assert nr.relevance_determination == "Commercial Marketing / Spam"

# -------------------------------------------------------------
# 5. CaseEnvelope Multi-Label & Payload Absence Tests
# -------------------------------------------------------------

def test_case_envelope_multi_label_icsr_and_pqc():
    """Validates CaseEnvelope supporting dual-label ICSR + PQC simultaneously (e.g. Case 04)."""
    triage = TriageResult(
        is_multi_label=True,
        primary_category=CategoryEnum.SAFETY_REPORT_ICSR,
        labels=[
            TriageLabel(category=CategoryEnum.SAFETY_REPORT_ICSR, confidence=0.98, reason="Septic shock adverse event"),
            TriageLabel(category=CategoryEnum.QUALITY_COMPLAINT_PQC, confidence=0.96, reason="Vial seal rupture & contamination")
        ],
        executive_summary="Patient developed septic shock following infusion of contaminated Cefatox."
    )

    icsr = IcsrPayload(
        patient=IcsrPatient(identifier="A.P. (Arthur Pendelton)", age="71 YRS", sex="MALE"),
        product=IcsrProduct(product_name="Cefatox 1g", lot_number="CX54831"),
        reaction=IcsrReaction(adverse_event="Distributive Septic Shock", seriousness_criteria=["Hospitalization", "Life-threatening"])
    )
    pqc = PqcPayload(
        product_name="Cefatox 1g",
        lot_number="CX54831",
        defect_type="Cracked aluminum crimp collar & dark particulate",
        packaging_breached=True,
        photo_evidence=PqcPhotoEvidence(detected=True, observation="visible black flakes", interpretation="contamination"),
        requires_human_review=True
    )

    envelope = CaseEnvelope(
        message_id="CASE-04",
        source_filename="email_04.eml",
        triage=triage,
        document_summary="10-15 sentence comprehensive document summary...",
        reviewer_summary="Dual ICSR+PQC case: contaminated vial led to ICU septic shock.",
        icsr=icsr,
        pqc=pqc,
        mi=None,            # Correctly absent when irrelevant
        not_relevant=None   # Correctly absent when irrelevant
    )

    assert envelope.triage.is_multi_label is True
    assert envelope.icsr is not None
    assert envelope.pqc is not None
    assert envelope.mi is None
    assert envelope.not_relevant is None
    assert envelope.icsr.patient.identifier == "A.P. (Arthur Pendelton)"
    assert envelope.pqc.photo_evidence.detected is True

# -------------------------------------------------------------
# 6. ReviewerBrief Contract Tests
# -------------------------------------------------------------

def test_reviewer_brief_contract():
    """Validates ReviewerBrief containing executive summary, review focus items, and fact stats."""
    focus1 = ReviewFocusItem(
        category=ReviewFocusCategory.PHOTO_DEFECT_INSPECTION,
        field_affected="photo_evidence",
        headline="Physical Defect Photo Inspection Required",
        detail="Photograph of contaminated Cefatox vial Exhibit 1 attached.",
        action_suggested="Inspect photograph and confirm particulate contamination"
    )
    brief = ReviewerBrief(
        case_id="CASE-04",
        subject="CRITICAL ALERT: Sepsis caused by Contaminated Cefatox 1g Vial",
        sender="Dr. Robert Lang, MD",
        received_date="2025-11-14",
        primary_category="Safety Report (ICSR)",
        all_categories=["Safety Report (ICSR)", "Quality Complaint (PQC)"],
        confidence=0.98,
        urgency="CRITICAL",
        executive_summary="71-year-old male ICU patient developed septic shock 45 minutes after Cefatox partial infusion.",
        review_focus=[focus1],
        fact_stats=FactSummaryStats(total_facts=12, confirmed_count=10, not_stated_count=2, uncertain_count=0, conflict_count=0),
        actionable_conflicts=[],
        missing_critical_fields=["treatment_stop_date"]
    )

    assert brief.case_id == "CASE-04"
    assert brief.urgency == "CRITICAL"
    assert len(brief.review_focus) == 1
    assert brief.review_focus[0].category == ReviewFocusCategory.PHOTO_DEFECT_INSPECTION
    assert brief.fact_stats.confirmed_count == 10

# -------------------------------------------------------------
# 7. LLM Provider Abstraction Tests
# -------------------------------------------------------------

def test_llm_provider_abstraction_contract():
    """Validates that LLMProvider interface is cleanly implemented by GeminiProvider."""
    provider = get_llm_provider("gemini")
    assert isinstance(provider, LLMProvider)
    assert isinstance(provider, GeminiProvider)
    assert provider.provider_name == "gemini"

    # Unsupported provider raises ValueError
    with pytest.raises(ValueError, match="Unsupported LLM provider: unknown"):
        get_llm_provider("unknown")
