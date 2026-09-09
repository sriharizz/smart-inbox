import pytest
from app.schemas.fact_contract import (
    Fact, Evidence, VerificationResult, EvidenceType,
    LocationReference, BoundingBox
)
from app.schemas.legacy_adapter import select_best_evidence, _make_source_citation

def test_1_email_plus_pdf_candidates_for_same_fact():
    """
    Test 1: Email + PDF candidates for same fact:
    → PDF Level-1 visual evidence selected when it genuinely supports the fact.
    """
    fact = Fact(field="patient_weight", value="68 kg (150 lbs)")

    email_ev = Evidence(
        source_id="email_01.eml",
        source_type=EvidenceType.EMAIL_BODY,
        page_or_location="Email Body",
        verbatim_snippet="Patient M.K., female, weight 68 kg (150 lbs).",
        location=None,
        verification_result=VerificationResult.INSUFFICIENT
    )

    pdf_ev = Evidence(
        source_id="cioms_form_MK_Cardioril.pdf",
        source_type=EvidenceType.PDF_TEXT,
        page_or_location="Page 1, Box 3a",
        verbatim_snippet="3a. WEIGHT 68 kg (150 lbs)",
        location=LocationReference(
            page_number=1,
            bounding_box=BoundingBox(x0=450.0, y0=92.44, x1=502.91, y1=113.39, page_number=1)
        ),
        verification_result=VerificationResult.SUPPORTS
    )

    best = select_best_evidence([email_ev, pdf_ev], fact)
    assert best is not None
    assert best.source_id == "cioms_form_MK_Cardioril.pdf"
    assert best.location is not None
    assert best.location.bounding_box is not None
    assert best.location.bounding_box.x0 == 450.0

    cit = _make_source_citation(best)
    assert cit.source_type == "pdf"
    assert cit.anchor_level == "LEVEL_1_EXACT_VISUAL"
    assert cit.bounding_box is not None
    assert cit.page_number == 1

def test_2_email_only_case():
    """
    Test 2: Email-only case:
    → Email evidence remains selected.
    """
    fact = Fact(field="reporter_name", value="Dr. Marcus Vance, MD")

    coarse_email_ev = Evidence(
        source_id="imap_6.eml",
        source_type=EvidenceType.EMAIL_BODY,
        page_or_location="Email Header",
        verbatim_snippet="From: Dr. Marcus Vance, MD",
        location=None,
        verification_result=VerificationResult.INSUFFICIENT
    )

    span_email_ev = Evidence(
        source_id="imap_6.eml",
        source_type=EvidenceType.EMAIL_BODY,
        page_or_location="REPORTER DETAILS section",
        verbatim_snippet="Reporter: Dr. Marcus Vance, MD\nAttending Cardiologist",
        location=LocationReference(
            page_number=1,
            char_start=1175,
            char_end=1422
        ),
        verification_result=VerificationResult.SUPPORTS
    )

    best = select_best_evidence([coarse_email_ev, span_email_ev], fact)
    assert best is not None
    assert best.source_id == "imap_6.eml"
    assert best.location is not None
    assert best.location.char_start == 1175
    assert best.location.char_end == 1422

    cit = _make_source_citation(best)
    assert cit.source_type == "email"
    assert cit.anchor_level == "LEVEL_1_EXACT_VISUAL"

def test_3_pdf_candidate_without_valid_support():
    """
    Test 3: PDF candidate without valid support:
    → Do not select it merely because it is a PDF.
    """
    fact = Fact(field="patient_weight", value="68 kg")

    grounded_email_ev = Evidence(
        source_id="email_01.eml",
        source_type=EvidenceType.EMAIL_BODY,
        page_or_location="Email Body",
        verbatim_snippet="The patient's current weight is 68 kg on intake.",
        location=None,
        verification_result=VerificationResult.INSUFFICIENT
    )

    # PDF candidate from unrelated section that does NOT support or mention weight
    unrelated_pdf_ev = Evidence(
        source_id="cioms_form_MK_Cardioril.pdf",
        source_type=EvidenceType.PDF_TEXT,
        page_or_location="Page 1, Box 24",
        verbatim_snippet="Hospital admission date: 10-NOV-2025 for monitoring.",
        location=LocationReference(
            page_number=1,
            bounding_box=BoundingBox(x0=100.0, y0=200.0, x1=200.0, y1=250.0, page_number=1)
        ),
        verification_result=VerificationResult.INSUFFICIENT
    )

    best = select_best_evidence([grounded_email_ev, unrelated_pdf_ev], fact)
    assert best is not None
    assert best.source_id == "email_01.eml"
    assert "68 kg" in best.verbatim_snippet

def test_4_level_3_email_vs_level_1_pdf():
    """
    Test 4: Level-3 email vs Level-1 PDF:
    → Appropriate precise/verified Level-1 visual evidence selected when both support.
    """
    fact = Fact(field="lot_number", value="BL-8802")

    lvl3_email = Evidence(
        source_id="complaint.eml",
        source_type=EvidenceType.EMAIL_BODY,
        page_or_location="Email Body",
        verbatim_snippet="We have an issue with Lot BL-8802 packaging.",
        location=None,
        verification_result=VerificationResult.SUPPORTS
    )

    lvl1_pdf = Evidence(
        source_id="packaging_defect_report.pdf",
        source_type=EvidenceType.PDF_TEXT,
        page_or_location="Page 1, Section 2",
        verbatim_snippet="Product: Cardioril 10mg | Lot Number: BL-8802 | Exp: 11/2026",
        location=LocationReference(
            page_number=1,
            bounding_box=BoundingBox(x0=120.0, y0=80.0, x1=350.0, y1=105.0, page_number=1)
        ),
        verification_result=VerificationResult.SUPPORTS
    )

    best = select_best_evidence([lvl3_email, lvl1_pdf], fact)
    assert best is not None
    assert best.source_id == "packaging_defect_report.pdf"
    assert best.location.bounding_box is not None

def test_5_evidence_list_with_only_one_candidate():
    """
    Test 5: Evidence list with only one candidate:
    → Existing behavior preserved.
    """
    fact = Fact(field="adverse_event", value="Acute Hepatic Injury")

    single_ev = Evidence(
        source_id="report.pdf",
        source_type=EvidenceType.PDF_TEXT,
        page_or_location="Page 1",
        verbatim_snippet="Diagnosis: Acute Hepatic Injury",
        location=LocationReference(page_number=1),
        verification_result=VerificationResult.INSUFFICIENT
    )

    best = select_best_evidence([single_ev], fact)
    assert best is single_ev

def test_6_no_evidence():
    """
    Test 6: No evidence:
    → Citation remains absent (None).
    """
    fact = Fact(field="patient_weight", value="Not stated")

    assert select_best_evidence([], fact) is None
    assert select_best_evidence(None, fact) is None

def test_7_multiple_cases_with_different_source_types():
    """
    Test 7: Multiple cases with different source types:
    → No case-specific logic; defect images, scanned pages, tables correctly handled.
    """
    # Exhibit photo for defect
    pqc_fact = Fact(field="defect_photo", value="Cracked Crimp Seal")
    
    email_mention = Evidence(
        source_id="inbox_msg.eml",
        source_type=EvidenceType.EMAIL_BODY,
        page_or_location="Email Body",
        verbatim_snippet="Photo attached showing cracked crimp seal.",
        location=None,
        verification_result=VerificationResult.INSUFFICIENT
    )
    
    photo_ev = Evidence(
        source_id="exhibit_1_vial.png",
        source_type=EvidenceType.DEFECT_IMAGE,
        page_or_location="Exhibit 1",
        verbatim_snippet="Visual defect exhibit: cracked crimp seal on Cefatox vial.",
        location=LocationReference(
            page_number=1,
            bounding_box=BoundingBox(x0=50.0, y0=50.0, x1=400.0, y1=400.0, page_number=1)
        ),
        verification_result=VerificationResult.SUPPORTS
    )

    best_photo = select_best_evidence([email_mention, photo_ev], pqc_fact)
    assert best_photo is not None
    assert best_photo.source_id == "exhibit_1_vial.png"
    assert best_photo.source_type == EvidenceType.DEFECT_IMAGE

    cit = _make_source_citation(best_photo)
    assert cit.source_type == "image"
    assert cit.anchor_level == "LEVEL_1_EXACT_VISUAL"


def test_8_embedded_pdf_defect_photo_provenance():
    """
    Test 8: Embedded PDF defect photo citation preserves:
    - source_type == 'image'
    - source_id == originating PDF filename
    - page_number == originating page (e.g. 2)
    - bounding_box exact visual coordinates
    """
    photo_ev = Evidence(
        source_id="vial_contamination_sepsis.pdf",
        source_type=EvidenceType.DEFECT_IMAGE,
        page_or_location="Page 2, Defect Photograph",
        verbatim_snippet="Contaminated vial showing dark particulate matter.",
        location=LocationReference(
            page_number=2,
            section="Defect Photograph",
            bounding_box=BoundingBox(x0=144.0, y0=142.5, x1=468.0, y1=385.5, page_number=2)
        ),
        verification_result=VerificationResult.SUPPORTS
    )

    cit = _make_source_citation(photo_ev)
    assert cit.source_type == "image"
    assert cit.source_id == "vial_contamination_sepsis.pdf"
    assert cit.source_name == "vial_contamination_sepsis.pdf"
    assert cit.page_number == 2
    assert cit.bounding_box is not None
    assert cit.bounding_box["x0"] == 144.0
    assert cit.bounding_box["page_number"] == 2
    assert cit.anchor_level == "LEVEL_1_EXACT_VISUAL"


def test_9_mi_evidence_and_aliases_in_legacy_adapter():
    """
    Test 9: MI evidence and canonical aliases in envelope_to_legacy:
    - Verifies miProduct, inquiryType, question_1 aliases exist in citations dict.
    - Verifies section citations 'medical_info' and 'mi' are populated.
    """
    from app.schemas.case_envelope import CaseEnvelope
    from app.schemas.triage_schema import TriageResult, CategoryEnum, TriageLabel
    from app.schemas.category_payloads import MiPayload

    ev1 = Evidence(
        source_id="email_09.eml",
        source_type=EvidenceType.EMAIL_BODY,
        page_or_location="Email Body",
        verbatim_snippet="Can Cardioril 10mg be crushed for pediatric administration?",
        location=LocationReference(page_number=1, char_start=120, char_end=182),
        verification_result=VerificationResult.SUPPORTS
    )
    ev2 = Evidence(
        source_id="email_09.eml",
        source_type=EvidenceType.EMAIL_BODY,
        page_or_location="Email Body",
        verbatim_snippet="Inquiry regarding Cardioril administration in pediatric dysphagia.",
        location=LocationReference(page_number=1, char_start=40, char_end=106),
        verification_result=VerificationResult.SUPPORTS
    )

    f_prod = Fact(field="mi_product_or_topic", value="Cardioril", evidence=[ev2])
    f_inq = Fact(field="mi_inquiry_type", value="Dosage & Administration", evidence=[ev2])
    f_q1 = Fact(field="mi_question_1", value="Can Cardioril 10mg be crushed for pediatric administration?", evidence=[ev1])

    mi_payload = MiPayload(
        product_or_topic="Cardioril",
        inquiry_type="Dosage & Administration",
        question_text="Can Cardioril 10mg be crushed for pediatric administration?",
        facts=[f_prod, f_inq, f_q1]
    )

    envelope = CaseEnvelope(
        envelope_id="MI-CASE-TEST",
        source_filename="email_09.eml",
        triage=TriageResult(
            primary_category=CategoryEnum.MEDICAL_INFORMATION_MI,
            labels=[TriageLabel(category=CategoryEnum.MEDICAL_INFORMATION_MI, confidence=0.99, reason="Inquiry")],
            executive_summary="Summary"
        ),
        mi=mi_payload,
        fact_ledger=[f_prod, f_inq, f_q1]
    )

    from app.schemas.legacy_adapter import envelope_to_legacy
    legacy = envelope_to_legacy(envelope)

    assert legacy.medical_info is not None
    assert legacy.medical_info.product_or_topic == "Cardioril"
    assert legacy.medical_info.citation is not None
    assert legacy.medical_info.citation.source_type == "email"

    # Canonical aliases for MI fields
    assert "miProduct" in legacy.citations
    assert "product_or_topic" in legacy.citations
    assert "inquiryType" in legacy.citations
    assert "question_1" in legacy.citations
    assert "medical_info" in legacy.citations
    assert "mi" in legacy.citations

    # Verify anchor level and char offsets
    q1_cit = legacy.citations["question_1"]
    assert q1_cit.char_start == 120
    assert q1_cit.char_end == 182
    assert q1_cit.anchor_level == "LEVEL_1_EXACT_VISUAL"


def test_10_mi_evidence_grounding_safety_unstated():
    """
    Test 10: MI ungrounded / unstated fields do not fabricate citations.
    """
    from app.schemas.case_envelope import CaseEnvelope
    from app.schemas.triage_schema import TriageResult, CategoryEnum, TriageLabel
    from app.schemas.category_payloads import MiPayload
    from app.schemas.legacy_adapter import envelope_to_legacy

    f_prod = Fact(field="mi_product_or_topic", value="Not stated", evidence=[])
    f_inq = Fact(field="mi_inquiry_type", value="Not stated", evidence=[])

    mi_payload = MiPayload(
        product_or_topic="Not stated",
        inquiry_type="Not stated",
        facts=[f_prod, f_inq]
    )

    envelope = CaseEnvelope(
        envelope_id="MI-CASE-UNSTATED",
        source_filename="email_09.eml",
        triage=TriageResult(
            primary_category=CategoryEnum.MEDICAL_INFORMATION_MI,
            labels=[TriageLabel(category=CategoryEnum.MEDICAL_INFORMATION_MI, confidence=0.99, reason="Inquiry")],
            executive_summary="Summary"
        ),
        mi=mi_payload,
        fact_ledger=[f_prod, f_inq]
    )

    legacy = envelope_to_legacy(envelope)
    assert legacy.medical_info is not None
    # No citations must be fabricated into citations dict
    assert "miProduct" not in legacy.citations
    assert "inquiryType" not in legacy.citations
    assert "medical_info" not in legacy.citations
    assert "mi" not in legacy.citations
    assert "question_1" not in legacy.citations



