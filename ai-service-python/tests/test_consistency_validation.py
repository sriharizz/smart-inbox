import math
import pytest
from typing import List

from app.schemas.fact_contract import (
    Fact, Evidence, FactStatus, VerificationResult, EvidenceType, LocationReference
)
from app.schemas.triage_schema import TriageResult, TriageLabel, CategoryEnum
from app.schemas.category_payloads import (
    IcsrPayload, IcsrPatient, IcsrReporter, IcsrProduct, IcsrReaction,
    PqcPayload, MiPayload, NotRelevantPayload
)
from app.schemas.case_envelope import CaseEnvelope
from app.schemas.validation_schema import (
    ValidationSeverity, ValidationGatingStatus, ValidationIssue, ValidationReport
)
from app.services.consistency_validator import ConsistencyValidator, consistency_validator


def _build_valid_case_envelope() -> CaseEnvelope:
    """Helper to build a clean, valid CaseEnvelope passing all checks."""
    triage = TriageResult(
        primary_category=CategoryEnum.SAFETY_REPORT_ICSR,
        confidence=0.98,
        labels=[
            TriageLabel(category=CategoryEnum.SAFETY_REPORT_ICSR, confidence=0.98, reason="Adverse event identified")
        ],
        executive_summary="Valid adverse event report."
    )

    ev1 = Evidence(
        evidence_id="ev-001",
        source_id="email_01.eml",
        source_type=EvidenceType.EMAIL_BODY,
        page_or_location="Email body line 4",
        verbatim_snippet="Patient took Cardioril 20 mg daily.",
        verification_result=VerificationResult.SUPPORTS,
        verification_confidence=0.94,
        verification_metadata={"verifier_method": "llm_semantic_nli", "provider": "groq"}
    )

    ev2 = Evidence(
        evidence_id="ev-002",
        source_id="email_01.eml",
        source_type=EvidenceType.EMAIL_BODY,
        page_or_location="Email body line 6",
        verbatim_snippet="Patient experienced severe palpitations and tachycardia.",
        verification_result=VerificationResult.SUPPORTS,
        verification_confidence=0.92,
        verification_metadata={"verifier_method": "llm_semantic_nli", "provider": "groq"}
    )

    fact1 = Fact(
        fact_id="f-001",
        field="suspect_product",
        value="Cardioril",
        normalized_value="Cardioril",
        status=FactStatus.CONFIRMED,
        confidence=0.96,
        evidence=[ev1],
        verification_state=VerificationResult.SUPPORTS
    )

    fact2 = Fact(
        fact_id="f-002",
        field="adverse_event",
        value="Palpitations and tachycardia",
        normalized_value="Tachycardia",
        status=FactStatus.CONFIRMED,
        confidence=0.95,
        evidence=[ev2],
        verification_state=VerificationResult.SUPPORTS
    )

    fact3 = Fact(
        fact_id="f-003",
        field="concomitant_therapy",
        value="Not stated",
        normalized_value=None,
        status=FactStatus.NOT_STATED,
        confidence=1.0,
        evidence=[],
        verification_state=VerificationResult.INSUFFICIENT
    )

    icsr = IcsrPayload(
        patient=IcsrPatient(age="68", sex="Female"),
        reporter=IcsrReporter(name="Dr. Jane Smith", qualification="Physician"),
        products=[IcsrProduct(name="Cardioril", role="SUSPECT", dose="20 mg")],
        reactions=[IcsrReaction(reaction_term="Tachycardia", outcome="Recovered")],
        facts=[fact1, fact2, fact3]
    )

    envelope = CaseEnvelope(
        envelope_id="env-clean-123",
        message_id="msg-clean-123",
        source_filename="email_01.eml",
        triage=triage,
        document_summary="Valid summary of intake document.",
        reviewer_summary="Valid reviewer executive brief.",
        icsr=icsr,
        fact_ledger=[fact1, fact2, fact3],
        metadata={"attachment_filenames": []}
    )

    return envelope


# ============================================================================
# 1. FULLY VALID CASE ENVELOPE
# ============================================================================

def test_fully_valid_case_envelope_passes():
    envelope = _build_valid_case_envelope()
    report = consistency_validator.validate_envelope(envelope)

    assert report.passed is True
    assert report.gating_status == ValidationGatingStatus.READY_FOR_REVIEW
    assert len(report.errors) == 0
    assert report.checked_counts["facts_checked"] == 3
    assert report.checked_counts["evidence_checked"] == 2


# ============================================================================
# 2. INVALID CONFIDENCE
# ============================================================================

def test_invalid_confidence_fails_integrity():
    envelope = _build_valid_case_envelope()
    # Set confidence out of bounds (> 1.0)
    envelope.fact_ledger[0].confidence = 1.45

    report = consistency_validator.validate_envelope(envelope)
    assert report.passed is False
    assert report.gating_status == ValidationGatingStatus.BLOCKED_BY_INTEGRITY_ERROR
    assert any(e.code == "CONFIDENCE_OUT_OF_BOUNDS" for e in report.errors)

    # Set NaN confidence
    envelope2 = _build_valid_case_envelope()
    envelope2.fact_ledger[0].evidence[0].verification_confidence = float("nan")
    report2 = consistency_validator.validate_envelope(envelope2)
    assert report2.passed is False
    assert any(e.code == "CONFIDENCE_OUT_OF_BOUNDS" for e in report2.errors)


# ============================================================================
# 3. MISSING OR INVALID FACT STATUS
# ============================================================================

def test_invalid_fact_status_flags_error():
    envelope = _build_valid_case_envelope()
    # Assign an invalid status value
    envelope.fact_ledger[0].status = "INVENTED_STATUS"

    report = consistency_validator.validate_envelope(envelope)
    assert report.passed is False
    assert any(e.code == "FACT_INVALID_STATUS" for e in report.errors)


# ============================================================================
# 4. DANGLING EVIDENCE SOURCE
# ============================================================================

def test_dangling_evidence_source_flags_error():
    envelope = _build_valid_case_envelope()
    # Source ID points to an external unassociated file
    envelope.fact_ledger[0].evidence[0].source_id = "completely_unrelated_hospital_record.pdf"

    report = consistency_validator.validate_envelope(envelope)
    assert report.passed is False
    assert any(e.code == "EVIDENCE_DANGLING_SOURCE" for e in report.errors)


# ============================================================================
# 5. DANGLING VERIFICATION REFERENCE & FALLBACK ILLEGAL SUPPORT
# ============================================================================

def test_fallback_verifier_marked_supports_flags_error():
    envelope = _build_valid_case_envelope()
    # A fallback result must NEVER be marked SUPPORTS
    envelope.fact_ledger[0].evidence[0].verification_metadata = {
        "verifier_method": "fallback",
        "error": "Groq API 429 timeout"
    }
    envelope.fact_ledger[0].evidence[0].verification_result = VerificationResult.SUPPORTS

    report = consistency_validator.validate_envelope(envelope)
    assert report.passed is False
    assert any(e.code == "VERIFICATION_FALLBACK_ILLEGAL_SUPPORT" for e in report.errors)


# ============================================================================
# 6. INVALID VERIFICATION RESULT
# ============================================================================

def test_invalid_verification_result_enum_flags_error():
    envelope = _build_valid_case_envelope()
    envelope.fact_ledger[0].evidence[0].verification_result = "MAYBE_TRUE"

    report = consistency_validator.validate_envelope(envelope)
    assert report.passed is False
    assert any(e.code == "VERIFICATION_UNKNOWN_RESULT" for e in report.errors)


# ============================================================================
# 7. NOT_STATED WITH INCONSISTENT DATA
# ============================================================================

def test_not_stated_with_supporting_evidence_flags_error():
    envelope = _build_valid_case_envelope()
    # Give the NOT_STATED fact supporting evidence
    illegal_ev = Evidence(
        evidence_id="ev-illegal-01",
        source_id="email_01.eml",
        source_type=EvidenceType.EMAIL_BODY,
        page_or_location="Line 10",
        verbatim_snippet="Patient took concomitant Lisinopril.",
        verification_result=VerificationResult.SUPPORTS,
        verification_confidence=0.9
    )
    envelope.fact_ledger[2].evidence = [illegal_ev]

    report = consistency_validator.validate_envelope(envelope)
    assert report.passed is False
    assert any(e.code == "FACT_NOT_STATED_HAS_SUPPORTING_EVIDENCE" for e in report.errors)


def test_not_stated_with_fabricated_concrete_value_flags_error():
    envelope = _build_valid_case_envelope()
    envelope.fact_ledger[2].value = "Lisinopril 10mg daily"
    envelope.fact_ledger[2].normalized_value = "Lisinopril"

    report = consistency_validator.validate_envelope(envelope)
    assert report.passed is False
    assert any(e.code == "FACT_NOT_STATED_INCONSISTENT_VALUE" for e in report.errors)


# ============================================================================
# 8. CATEGORY / PAYLOAD MISMATCH
# ============================================================================

def test_category_payload_mismatch_flags_error():
    envelope = _build_valid_case_envelope()
    # Null out ICSR payload when primary category is ICSR
    envelope.icsr = None

    report = consistency_validator.validate_envelope(envelope)
    assert report.passed is False
    assert any(e.code == "CATEGORY_PAYLOAD_MISMATCH" for e in report.errors)


def test_not_relevant_category_polluted_with_clinical_payload():
    envelope = _build_valid_case_envelope()
    envelope.triage.primary_category = CategoryEnum.NOT_RELEVANT
    envelope.triage.labels = [TriageLabel(category=CategoryEnum.NOT_RELEVANT, confidence=0.99, reason="Commercial spam")]
    envelope.not_relevant = NotRelevantPayload(
        relevance_determination="Not Relevant",
        exclusion_reason="Commercial marketing solicitation"
    )
    # Keeping icsr populated on a purely Not Relevant communication is a pollution error
    report = consistency_validator.validate_envelope(envelope)
    assert report.passed is False
    assert any(e.code == "CATEGORY_NOT_RELEVANT_POLLUTED" for e in report.errors)


# ============================================================================
# 9. DUPLICATE / CONFLICTING FACTS
# ============================================================================

def test_duplicate_conflicting_facts_flags_warning():
    envelope = _build_valid_case_envelope()
    # Add a second fact for suspect_product with conflicting value
    conflicting_fact = Fact(
        fact_id="f-001b",
        field="suspect_product",
        value="AlternativeDrug 50mg",
        normalized_value="AlternativeDrug",
        status=FactStatus.CONFIRMED,
        confidence=0.85,
        evidence=[]
    )
    envelope.fact_ledger.append(conflicting_fact)

    report = consistency_validator.validate_envelope(envelope)
    # Duplicate conflicting facts should generate a warning (non-blocking for review, but flagged)
    assert any(w.code == "DUPLICATE_CONFLICTING_FACT" for w in report.warnings)


# ============================================================================
# 10. INVALID PAGE REFERENCE
# ============================================================================

def test_invalid_page_reference_flags_error():
    envelope = _build_valid_case_envelope()
    envelope.fact_ledger[0].evidence[0].source_type = EvidenceType.PDF_TEXT
    envelope.fact_ledger[0].evidence[0].location = LocationReference(page_number=0)  # 0 is invalid (must be >= 1)

    report = consistency_validator.validate_envelope(envelope)
    assert report.passed is False
    assert any(e.code == "EVIDENCE_INVALID_PAGE" for e in report.errors)


def test_page_exceeds_total_page_count():
    envelope = _build_valid_case_envelope()
    envelope.metadata["page_count"] = 3
    envelope.fact_ledger[0].evidence[0].source_type = EvidenceType.PDF_TEXT
    envelope.fact_ledger[0].evidence[0].location = LocationReference(page_number=5)

    report = consistency_validator.validate_envelope(envelope)
    assert report.passed is False
    assert any(e.code == "EVIDENCE_PAGE_EXCEEDS_TOTAL" for e in report.errors)


# ============================================================================
# 11. MISSING VERIFICATION METADATA
# ============================================================================

def test_missing_verification_metadata_flags_warning():
    envelope = _build_valid_case_envelope()
    # Candidate evidence is INSUFFICIENT and lacks verification metadata
    envelope.fact_ledger[0].evidence[0].verification_result = VerificationResult.INSUFFICIENT
    envelope.fact_ledger[0].evidence[0].verification_confidence = 0.0
    envelope.fact_ledger[0].evidence[0].verification_metadata = {}

    report = consistency_validator.validate_envelope(envelope)
    assert any(w.code == "VERIFICATION_UNVERIFIED_CANDIDATE" for w in report.warnings)


# ============================================================================
# 12. SUPPORTS -> STATUS RECONCILED TO CONFIRMED
# ============================================================================

def test_reconciliation_supports_reconciles_to_confirmed():
    validator = ConsistencyValidator(strict_reconciliation=True)
    fact = Fact(
        fact_id="f-rec-1",
        field="patient_age",
        value="68",
        status=FactStatus.UNCERTAIN,  # Was uncertain at extraction
        evidence=[
            Evidence(
                evidence_id="ev-1",
                source_id="test.pdf",
                page_or_location="Page 1",
                verbatim_snippet="Patient is a 68-year-old female.",
                verification_result=VerificationResult.SUPPORTS,
                verification_confidence=0.95
            )
        ]
    )

    reconciled, issues = validator.reconcile_fact_status(fact)
    assert reconciled.status == FactStatus.CONFIRMED
    assert any(i.code == "FACT_RECONCILED_TO_CONFIRMED" for i in issues)


# ============================================================================
# 13. CONTRADICTS -> STATUS RECONCILED TO CONFLICT
# ============================================================================

def test_reconciliation_contradicts_reconciles_to_conflict():
    validator = ConsistencyValidator(strict_reconciliation=True)
    fact = Fact(
        fact_id="f-rec-2",
        field="suspect_product",
        value="Cardioril",
        status=FactStatus.CONFIRMED,
        evidence=[
            Evidence(
                evidence_id="ev-2",
                source_id="test.pdf",
                page_or_location="Page 1",
                verbatim_snippet="Patient explicitly was NOT taking Cardioril.",
                verification_result=VerificationResult.CONTRADICTS,
                verification_confidence=0.91
            )
        ]
    )

    reconciled, issues = validator.reconcile_fact_status(fact)
    assert reconciled.status == FactStatus.CONFLICT
    assert any(i.code == "FACT_RECONCILED_TO_CONFLICT" for i in issues)
    assert "CONFLICT" in reconciled.notes


# ============================================================================
# 14. INSUFFICIENT -> STATUS RECONCILED TO UNCERTAIN
# ============================================================================

def test_reconciliation_insufficient_reconciles_to_uncertain():
    validator = ConsistencyValidator(strict_reconciliation=True)
    fact = Fact(
        fact_id="f-rec-3",
        field="adverse_event",
        value="Myocardial Infarction",
        status=FactStatus.CONFIRMED,  # Extracted as confirmed, but verification found evidence insufficient
        evidence=[
            Evidence(
                evidence_id="ev-3",
                source_id="test.pdf",
                page_or_location="Page 1",
                verbatim_snippet="Patient had a history of MI five years prior.",
                verification_result=VerificationResult.INSUFFICIENT,
                verification_confidence=0.4
            )
        ]
    )

    reconciled, issues = validator.reconcile_fact_status(fact)
    assert reconciled.status == FactStatus.UNCERTAIN
    assert any(i.code == "FACT_RECONCILED_TO_UNCERTAIN" for i in issues)
    assert "UNCERTAIN" in reconciled.notes


# ============================================================================
# 15. MULTI-LABEL CATEGORY CASE
# ============================================================================

def test_multi_label_category_case_both_payloads_valid():
    envelope = _build_valid_case_envelope()
    envelope.triage.is_multi_label = True
    envelope.triage.labels = [
        TriageLabel(category=CategoryEnum.SAFETY_REPORT_ICSR, confidence=0.95, reason="Adverse event"),
        TriageLabel(category=CategoryEnum.QUALITY_COMPLAINT_PQC, confidence=0.92, reason="Quality defect")
    ]
    # Attach valid PQC payload alongside ICSR payload
    envelope.pqc = PqcPayload(
        product_name="Cardioril",
        lot_number="BL-9901",
        defect_type="Particulate contamination",
        complaint_description="White precipitate in vial"
    )

    report = consistency_validator.validate_envelope(envelope)
    assert report.passed is True
    assert report.gating_status == ValidationGatingStatus.READY_FOR_REVIEW
    assert len(report.errors) == 0


# ============================================================================
# 16. EMAIL EVIDENCE WITHOUT PDF PAGE NUMBER
# ============================================================================

def test_email_evidence_without_pdf_page_is_completely_valid():
    envelope = _build_valid_case_envelope()
    ev = envelope.fact_ledger[0].evidence[0]
    ev.source_type = EvidenceType.EMAIL_BODY
    ev.location = None  # No location/page reference

    report = consistency_validator.validate_envelope(envelope)
    assert report.passed is True
    assert not any(e.code == "EVIDENCE_INVALID_PAGE" for e in report.errors)


# ============================================================================
# 17. CLEAN CASE BECOMES READY_FOR_REVIEW
# ============================================================================

def test_clean_case_becomes_ready_for_review():
    envelope = _build_valid_case_envelope()
    report = consistency_validator.validate_envelope(envelope)

    assert report.passed is True
    assert report.gating_status == ValidationGatingStatus.READY_FOR_REVIEW
    assert "READY_FOR_REVIEW" in report.summary


# ============================================================================
# 18. WARNINGS PRODUCE REVIEW_WITH_WARNINGS
# ============================================================================

def test_warnings_produce_review_with_warnings():
    envelope = _build_valid_case_envelope()
    # Create non-blocking warning: unverified candidate evidence
    envelope.fact_ledger[0].evidence[0].verification_result = VerificationResult.INSUFFICIENT
    envelope.fact_ledger[0].evidence[0].verification_confidence = 0.0
    envelope.fact_ledger[0].evidence[0].verification_metadata = {}

    report = consistency_validator.validate_envelope(envelope)
    assert report.passed is True  # Passed critical checks
    assert report.gating_status == ValidationGatingStatus.REVIEW_WITH_WARNINGS
    assert len(report.warnings) > 0


# ============================================================================
# 19. STRUCTURAL ERRORS PRODUCE BLOCKED_BY_INTEGRITY_ERROR
# ============================================================================

def test_structural_errors_produce_blocked_by_integrity_error():
    envelope = _build_valid_case_envelope()
    # Introduce critical error: Empty verbatim snippet
    envelope.fact_ledger[0].evidence[0].verbatim_snippet = ""

    report = consistency_validator.validate_envelope(envelope)
    assert report.passed is False
    assert report.gating_status == ValidationGatingStatus.BLOCKED_BY_INTEGRITY_ERROR
    assert any(e.code == "EVIDENCE_EMPTY_SNIPPET" for e in report.errors)
