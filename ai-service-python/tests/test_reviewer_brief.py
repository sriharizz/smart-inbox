import pytest
from app.schemas.case_envelope import (
    CaseEnvelope, ReviewFocusCategory, ReviewFocusItem
)
from app.schemas.triage_schema import TriageResult, CategoryEnum, TriageLabel
from app.schemas.fact_contract import Fact, Evidence, FactStatus, VerificationResult, EvidenceType
from app.schemas.category_payloads import IcsrPayload, PqcPayload, PqcPhotoEvidence
from app.services.reviewer_brief_builder import reviewer_brief_builder


def test_build_brief_basic_icsr():
    triage = TriageResult(
        primary_category=CategoryEnum.SAFETY_REPORT_ICSR,
        is_multi_label=False,
        labels=[TriageLabel(category=CategoryEnum.SAFETY_REPORT_ICSR, confidence=0.95, reason="Adverse event")],
        executive_summary="Patient experienced adverse event."
    )
    facts = [
        Fact(field="patient_age", value="64 years", status=FactStatus.CONFIRMED, confidence=0.98),
        Fact(field="adverse_event", value="Anaphylaxis", status=FactStatus.CONFIRMED, confidence=0.99),
        Fact(field="suspect_product", value="Enbrel", status=FactStatus.CONFIRMED, confidence=0.97),
        Fact(field="reporter_name", value="Dr. Smith", status=FactStatus.CONFIRMED, confidence=0.95),
    ]
    envelope = CaseEnvelope(
        envelope_id="test-env-01",
        message_id="msg-01",
        source_filename="clinic_report.pdf",
        triage=triage,
        document_summary="Patient experienced anaphylaxis after injection.",
        reviewer_summary="Expedited ICSR for anaphylaxis.",
        fact_ledger=facts
    )

    brief = reviewer_brief_builder.build_brief(envelope)

    assert brief.case_id == "msg-01"
    assert brief.primary_category == "Safety Report (ICSR)"
    assert brief.urgency == "EXPEDITED"
    assert brief.fact_stats.total_facts == 4
    assert brief.fact_stats.confirmed_count == 4
    assert brief.fact_stats.conflict_count == 0
    assert brief.fact_stats.uncertain_count == 0


def test_build_brief_focus_items_attention():
    triage = TriageResult(
        primary_category=CategoryEnum.SAFETY_REPORT_ICSR,
        is_multi_label=True,
        labels=[
            TriageLabel(category=CategoryEnum.SAFETY_REPORT_ICSR, confidence=0.92, reason="Rash"),
            TriageLabel(category=CategoryEnum.QUALITY_COMPLAINT_PQC, confidence=0.91, reason="Broken vial")
        ],
        executive_summary="Multi-label ICSR and PQC."
    )
    ev_conflict = Evidence(
        source_id="email_04.eml",
        source_type=EvidenceType.EMAIL_BODY,
        page_or_location="Email body paragraph 2",
        verbatim_snippet="Dose was 50mg in email vs 100mg in form"
    )
    ev_uncertain = Evidence(
        source_id="scanned_case.pdf",
        source_type=EvidenceType.PDF_TEXT,
        page_or_location="Page 1, Box B",
        verbatim_snippet="Handwritten note partially illegible"
    )
    
    facts = [
        Fact(field="product_dose", value="50mg / 100mg", status=FactStatus.CONFLICT, confidence=0.50, evidence=[ev_conflict]),
        Fact(field="patient_age", value="~45", status=FactStatus.UNCERTAIN, confidence=0.60, evidence=[ev_uncertain]),
        Fact(field="lot_number", value="Not stated", status=FactStatus.NOT_STATED, confidence=1.0),
    ]
    
    pqc = PqcPayload(
        product_name="Humira",
        defect_type="Contaminated vial",
        requires_human_review=True,
        photo_evidence=PqcPhotoEvidence(detected=True, observation="Cloudy suspension in vial")
    )
    
    envelope = CaseEnvelope(
        envelope_id="test-env-02",
        message_id="msg-02",
        source_filename="scanned_case.pdf",
        language_detected="Spanish",
        triage=triage,
        pqc=pqc,
        fact_ledger=facts
    )

    brief = reviewer_brief_builder.build_brief(envelope)

    assert brief.urgency == "CRITICAL"
    assert len(brief.actionable_conflicts) == 1
    assert "product_dose" in brief.actionable_conflicts[0]
    assert "lot_number" in brief.missing_critical_fields

    # Check focus categories present
    focus_cats = {item.category for item in brief.review_focus}
    assert ReviewFocusCategory.EVIDENCE_CONFLICT in focus_cats
    assert ReviewFocusCategory.UNCERTAIN_HANDWRITING in focus_cats
    assert ReviewFocusCategory.MISSING_CRITICAL_FIELD in focus_cats
    assert ReviewFocusCategory.PHOTO_DEFECT_INSPECTION in focus_cats
    assert ReviewFocusCategory.MULTILINGUAL_TRANSLATION in focus_cats


def test_build_brief_arbitrary_novel_email():
    """
    Proves that a completely new, unseen email with novel wording and custom fields
    generates a valid, robust ReviewerBrief without hardcoded conditionals.
    """
    triage = TriageResult(
        primary_category=CategoryEnum.SAFETY_REPORT_ICSR,
        is_multi_label=False,
        labels=[TriageLabel(category=CategoryEnum.SAFETY_REPORT_ICSR, confidence=0.88, reason="Severe rash and Stevens-Johnson syndrome")],
        executive_summary="Unseen case: Stevens-Johnson syndrome after novel antibiotic therapy."
    )
    # Novel fields not in original benchmark
    facts = [
        Fact(field="reconstitution_volume", value="10 mL sterile water", status=FactStatus.CONFIRMED, confidence=0.92),
        Fact(field="adverse_event", value="Stevens-Johnson Syndrome", status=FactStatus.CONFIRMED, confidence=0.96),
        Fact(field="suspect_product", value="CefoNovel 500mg", status=FactStatus.CONFIRMED, confidence=0.94),
        Fact(field="patient_age", value="42 years", status=FactStatus.CONFIRMED, confidence=0.95),
        Fact(field="reporter_name", value="Dr. Gregory House", status=FactStatus.CONFIRMED, confidence=0.91),
        Fact(field="concurrent_medication", value="Acetaminophen", status=FactStatus.CONFIRMED, confidence=0.89)
    ]
    envelope = CaseEnvelope(
        envelope_id="novel-env-999",
        message_id="msg-novel-arbitrary-001",
        source_filename="arbitrary_doctor_email.eml",
        triage=triage,
        document_summary="Attending physician reports severe SJS presentation in 42yo patient receiving CefoNovel.",
        reviewer_summary="Expedited ICSR for Stevens-Johnson syndrome.",
        fact_ledger=facts
    )

    brief = reviewer_brief_builder.build_brief(envelope)

    assert brief.case_id == "msg-novel-arbitrary-001"
    assert brief.primary_category == "Safety Report (ICSR)"
    assert brief.fact_stats.total_facts == 6
    assert brief.fact_stats.confirmed_count == 6
    assert len(brief.review_focus) == 0  # Clean state: no missing critical fields or conflicts


def test_build_brief_medical_information_no_spurious_warnings():
    """
    Proves that pure Medical Information inquiry briefs do not trigger false
    ICSR missing critical field warnings.
    """
    from app.schemas.category_payloads import MiPayload

    triage = TriageResult(
        primary_category=CategoryEnum.MEDICAL_INFORMATION_MI,
        is_multi_label=False,
        labels=[TriageLabel(category=CategoryEnum.MEDICAL_INFORMATION_MI, confidence=0.97, reason="Stability inquiry")],
        executive_summary="Inquiry regarding reconstitution stability and refrigeration."
    )
    mi_facts = [
        Fact(field="product_or_topic", value="Cefatox 1g", status=FactStatus.CONFIRMED, confidence=0.98),
        Fact(field="inquiry_type", value="Stability & Dilution", status=FactStatus.CONFIRMED, confidence=0.95),
        Fact(field="question_text", value="1. What is the refrigerated stability in D5W? 2. Is it Y-site compatible with furosemide?", status=FactStatus.CONFIRMED, confidence=0.96)
    ]
    mi_payload = MiPayload(
        product_or_topic="Cefatox 1g",
        inquiry_type="Stability & Dilution",
        question_text="1. What is the refrigerated stability in D5W? 2. Is it Y-site compatible with furosemide?",
        clinical_context="Adult surgical ward compounding",
        information_requested="Reconstitution stability data"
    )
    envelope = CaseEnvelope(
        envelope_id="mi-env-888",
        message_id="msg-mi-inquiry-01",
        source_filename="hospital_pharmacy_query.eml",
        triage=triage,
        mi=mi_payload,
        fact_ledger=mi_facts
    )

    brief = reviewer_brief_builder.build_brief(envelope)

    assert brief.primary_category == "Medical Information (MI)"
    assert brief.urgency == "STANDARD"
    # Verify no ICSR missing critical fields were incorrectly generated
    assert len(brief.missing_critical_fields) == 0
    assert not any(item.category == ReviewFocusCategory.MISSING_CRITICAL_FIELD for item in brief.review_focus)


def test_build_brief_not_relevant_minimal():
    """
    Proves that Not Relevant cases do not produce spurious missing-field warnings.
    """
    from app.schemas.category_payloads import NotRelevantPayload

    triage = TriageResult(
        primary_category=CategoryEnum.NOT_RELEVANT,
        is_multi_label=False,
        labels=[TriageLabel(category=CategoryEnum.NOT_RELEVANT, confidence=0.99, reason="Commercial vendor solicitation")],
        executive_summary="Commercial spam for office supplies."
    )
    nr_payload = NotRelevantPayload(
        relevance_determination="Not Relevant",
        exclusion_reason="Commercial marketing email unrelated to pharmacovigilance."
    )
    envelope = CaseEnvelope(
        envelope_id="nr-env-777",
        message_id="msg-spam-01",
        source_filename="vendor_catalog.eml",
        triage=triage,
        not_relevant=nr_payload,
        fact_ledger=[]
    )

    brief = reviewer_brief_builder.build_brief(envelope)

    assert brief.primary_category == "Not Relevant"
    assert brief.urgency == "STANDARD"
    assert brief.fact_stats.total_facts == 0
    assert len(brief.missing_critical_fields) == 0
    assert len(brief.review_focus) == 0

