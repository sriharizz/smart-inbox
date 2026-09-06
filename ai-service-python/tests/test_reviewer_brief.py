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
