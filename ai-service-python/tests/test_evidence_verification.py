import pytest
from typing import List, Optional

from app.schemas.fact_contract import (
    Fact, Evidence, FactStatus, VerificationResult, EvidenceType,
    LocationReference, BoundingBox
)
from app.schemas.case_envelope import CaseEnvelope
from app.schemas.triage_schema import TriageResult, CategoryEnum
from app.schemas.category_payloads import IcsrPayload, IcsrPatient, IcsrProduct, IcsrReaction, IcsrReporter
from app.core.llm_provider import LLMProvider
from app.services.evidence_verifier import (
    EvidenceVerifier, DeterministicClinicalVerifier
)


# ============================================================================
# MOCK LLM PROVIDER FIXTURES
# ============================================================================

class MockLLMProvider(LLMProvider):
    """Deterministic mock LLM provider simulating structured verification responses."""
    def __init__(self, mocked_result: str = "SUPPORTS", confidence: float = 0.95, rationale: str = "Mock rationale"):
        self.mocked_result = mocked_result
        self.confidence = confidence
        self.rationale = rationale

    @property
    def provider_name(self) -> str:
        return "mock-verifier-llm"

    def generate_content(self, contents, system_instruction=None, model=None, temperature=0.0) -> str:
        return f"""
        {{
            "verification_result": "{self.mocked_result}",
            "confidence": {self.confidence},
            "rationale": "{self.rationale}"
        }}
        """

    def generate_structured(self, contents, response_schema, system_instruction=None, model=None, temperature=0.0):
        raise NotImplementedError()

    def is_healthy(self) -> bool:
        return True


class FlakyFailingLLMProvider(LLMProvider):
    """Mock provider simulating API outage, rate limit exhaustion, or network timeout."""
    @property
    def provider_name(self) -> str:
        return "failing-verifier-llm"

    def generate_content(self, contents, system_instruction=None, model=None, temperature=0.0) -> str:
        raise RuntimeError("API connection timeout / 429 Quota Exceeded")

    def generate_structured(self, contents, response_schema, system_instruction=None, model=None, temperature=0.0):
        raise RuntimeError("API connection timeout / 429 Quota Exceeded")

    def is_healthy(self) -> bool:
        return False


# ============================================================================
# 1. SUPPORTS FOR DIRECT EXPLICIT EVIDENCE
# ============================================================================

def test_supports_for_direct_evidence():
    verifier = EvidenceVerifier(use_llm=False)

    fact = Fact(
        field="patient_age",
        value="71",
        status=FactStatus.CONFIRMED
    )
    candidate = Evidence(
        source_id="cioms_form.pdf",
        source_type=EvidenceType.PDF_TEXT,
        page_or_location="Page 1, Box 2",
        verbatim_snippet="The patient is a 71-year-old male with hypertension."
    )

    verified = verifier.verify_candidate(fact, candidate)
    assert verified.verification_result == VerificationResult.SUPPORTS
    assert verified.verification_confidence >= 0.90
    assert "71" in verified.verification_rationale


# ============================================================================
# 2. CONTRADICTS FOR EXPLICIT CONFLICTING EVIDENCE
# ============================================================================

def test_contradicts_for_explicit_conflicting_evidence():
    verifier = EvidenceVerifier(use_llm=False)

    fact = Fact(
        field="patient_age",
        value="71",
        status=FactStatus.CONFIRMED
    )
    candidate = Evidence(
        source_id="email_01.eml",
        source_type=EvidenceType.EMAIL_BODY,
        page_or_location="Paragraph 1",
        verbatim_snippet="The patient's age was 63 at the time of presentation."
    )

    verified = verifier.verify_candidate(fact, candidate)
    assert verified.verification_result == VerificationResult.CONTRADICTS
    assert verified.verification_confidence >= 0.90
    assert "conflict" in verified.verification_rationale.lower() or "contradict" in verified.verification_rationale.lower()


# ============================================================================
# 3. INSUFFICIENT FOR RELATED BUT NON-ENTAILING EVIDENCE
# ============================================================================

def test_insufficient_for_related_non_entailing_evidence():
    verifier = EvidenceVerifier(use_llm=False)

    fact = Fact(
        field="patient_age",
        value="71",
        status=FactStatus.CONFIRMED
    )
    candidate = Evidence(
        source_id="clinic_note.pdf",
        source_type=EvidenceType.PDF_TEXT,
        page_or_location="Page 1",
        verbatim_snippet="The patient was an elderly individual presenting with fatigue."
    )

    verified = verifier.verify_candidate(fact, candidate)
    assert verified.verification_result == VerificationResult.INSUFFICIENT
    assert "elderly" in verified.verification_rationale.lower() or "insufficient" in verified.verification_rationale.lower()


# ============================================================================
# 4. NEGATION & POLARITY HANDLING
# ============================================================================

def test_explicit_negation_contradicts_reported_reaction():
    verifier = EvidenceVerifier(use_llm=False)

    fact = Fact(
        field="adverse_event",
        value="anaphylaxis",
        status=FactStatus.CONFIRMED
    )
    candidate = Evidence(
        source_id="discharge_summary.pdf",
        source_type=EvidenceType.PDF_TEXT,
        page_or_location="Page 2",
        verbatim_snippet="Vital signs remained stable; no signs of anaphylaxis were observed."
    )

    verified = verifier.verify_candidate(fact, candidate)
    assert verified.verification_result == VerificationResult.CONTRADICTS
    assert "negate" in verified.verification_rationale.lower() or "denies" in verified.verification_rationale.lower()


def test_explicit_negation_contradicts_defect_claim():
    verifier = EvidenceVerifier(use_llm=False)

    fact = Fact(
        field="defect_description",
        value="particulate matter",
        status=FactStatus.CONFIRMED
    )
    candidate = Evidence(
        source_id="qa_inspection.pdf",
        source_type=EvidenceType.PDF_TEXT,
        page_or_location="Page 1",
        verbatim_snippet="Visual inspection of the lot was clear with no product defect detected."
    )

    verified = verifier.verify_candidate(fact, candidate)
    assert verified.verification_result == VerificationResult.CONTRADICTS


# ============================================================================
# 5. PRODUCT ROLE & RESCUE MEDICATION SEGREGATION
# ============================================================================

def test_rescue_medication_does_not_support_suspect_product_dose():
    verifier = EvidenceVerifier(use_llm=False)

    fact = Fact(
        field="product_dose",
        value="20 mg",
        status=FactStatus.CONFIRMED
    )
    candidate = Evidence(
        source_id="hospital_er_chart.pdf",
        source_type=EvidenceType.PDF_TEXT,
        page_or_location="Page 1, Resuscitation Section",
        verbatim_snippet="Epinephrine 0.3 mg IM was administered immediately for acute anaphylaxis resuscitation."
    )

    verified = verifier.verify_candidate(fact, candidate)
    assert verified.verification_result == VerificationResult.INSUFFICIENT
    assert "rescue" in verified.verification_rationale.lower() or "epinephrine" in verified.verification_rationale.lower()


# ============================================================================
# 6. REPORTER ROLE ATTRIBUTION DISTINCTION
# ============================================================================

def test_mentioned_physician_does_not_support_reporter_role():
    verifier = EvidenceVerifier(use_llm=False)

    fact = Fact(
        field="reporter_role",
        value="Physician",
        status=FactStatus.CONFIRMED
    )
    candidate = Evidence(
        source_id="email_03.eml",
        source_type=EvidenceType.EMAIL_BODY,
        page_or_location="Paragraph 3",
        verbatim_snippet="The physician mentioned in the email was Dr. Robert Vance, who treated me at urgent care."
    )

    verified = verifier.verify_candidate(fact, candidate)
    assert verified.verification_result == VerificationResult.INSUFFICIENT
    assert "narrative" in verified.verification_rationale.lower() or "reporter" in verified.verification_rationale.lower()


def test_author_signature_supports_reporter_role():
    verifier = EvidenceVerifier(use_llm=False)

    fact = Fact(
        field="reporter_name",
        value="Dr. Sarah Jenkins",
        status=FactStatus.CONFIRMED
    )
    candidate = Evidence(
        source_id="email_01.eml",
        source_type=EvidenceType.EMAIL_HEADER,
        page_or_location="Header",
        verbatim_snippet="From: Dr. Sarah Jenkins, MD <sjenkins@metrohealth.org>"
    )

    verified = verifier.verify_candidate(fact, candidate)
    assert verified.verification_result == VerificationResult.SUPPORTS
    assert verified.verification_confidence >= 0.90


# ============================================================================
# 7. TEMPORAL / DATE ROLE DISCRIMINATION
# ============================================================================

def test_reaction_onset_date_does_not_support_treatment_start_date():
    verifier = EvidenceVerifier(use_llm=False)

    fact = Fact(
        field="treatment_start_date",
        value="2025-11-14",
        status=FactStatus.CONFIRMED
    )
    candidate = Evidence(
        source_id="patient_log.pdf",
        source_type=EvidenceType.PDF_TEXT,
        page_or_location="Page 1",
        verbatim_snippet="Adverse reaction onset was noted on 2025-11-14 when rash developed."
    )

    verified = verifier.verify_candidate(fact, candidate)
    assert verified.verification_result == VerificationResult.INSUFFICIENT
    assert "onset" in verified.verification_rationale.lower()


# ============================================================================
# 8. MULTILINGUAL SOURCE FIDELITY & PRESERVATION
# ============================================================================

def test_multilingual_foreign_snippet_preservation_and_support():
    verifier = EvidenceVerifier(use_llm=False)

    fact = Fact(
        field="adverse_event",
        value="Toxic Epidermal Necrolysis",
        status=FactStatus.CONFIRMED
    )
    original_foreign_snippet = "Diagnóstico clínico: Necrólisis Epidérmica Tóxica severa."
    candidate = Evidence(
        source_id="informe_clinico.pdf",
        source_type=EvidenceType.PDF_TEXT,
        page_or_location="Página 1",
        verbatim_snippet=original_foreign_snippet
    )

    verified = verifier.verify_candidate(fact, candidate)
    # Original source verbatim text MUST be preserved intact
    assert verified.verbatim_snippet == original_foreign_snippet
    assert verified.verification_result == VerificationResult.SUPPORTS
    assert "necrólisis epidérmica tóxica" in verified.verification_rationale.lower()


# ============================================================================
# 9. NOT_STATED FACTS NEVER RECEIVE INVENTED SUPPORT
# ============================================================================

def test_not_stated_facts_never_receive_supporting_evidence():
    verifier = EvidenceVerifier(use_llm=False)

    fact = Fact(
        field="product_frequency",
        value="Not stated",
        status=FactStatus.NOT_STATED,
        evidence=[
            Evidence(
                source_id="email_03.eml",
                source_type=EvidenceType.EMAIL_BODY,
                page_or_location="Paragraph 2",
                verbatim_snippet="I took four pills over four days."
            )
        ]
    )

    verified_fact = verifier.verify_fact(fact)
    assert verified_fact.verification_state == VerificationResult.INSUFFICIENT
    for ev in verified_fact.evidence:
        assert ev.verification_result == VerificationResult.INSUFFICIENT
        assert "unstated" in ev.verification_rationale.lower()


# ============================================================================
# 10. RETRIEVAL SCORE AND VERIFICATION CONFIDENCE REMAIN SEPARATE
# ============================================================================

def test_retrieval_relevance_distinct_from_verification_confidence():
    verifier = EvidenceVerifier(use_llm=False)

    fact = Fact(
        field="product_dose",
        value="Cardioril 20 mg",
        status=FactStatus.CONFIRMED
    )
    # Candidate with high retrieval score (e.g. 0.92) due to lexical terms, but clinically insufficient
    candidate = Evidence(
        source_id="er_notes.pdf",
        source_type=EvidenceType.PDF_TEXT,
        page_or_location="Page 1",
        verbatim_snippet="Emergency resuscitation was attempted with Epinephrine 0.3 mg IM.",
        retrieval_metadata={"relevance_score": 0.92, "retrieval_method": "hybrid"}
    )

    verified = verifier.verify_candidate(fact, candidate)
    # High retrieval relevance score remains intact in retrieval_metadata
    assert verified.retrieval_metadata["relevance_score"] == 0.92
    # Verification determination is INSUFFICIENT with its own distinct confidence
    assert verified.verification_result == VerificationResult.INSUFFICIENT
    assert verified.verification_confidence == 0.90
    assert verified.retrieval_metadata["relevance_score"] != verified.verification_confidence


# ============================================================================
# 11. MULTIPLE CANDIDATES PRESERVE INDIVIDUAL VERIFICATION RESULTS
# ============================================================================

def test_multiple_candidates_preserve_individual_determinations():
    verifier = EvidenceVerifier(use_llm=False)

    fact = Fact(
        field="patient_age",
        value="71",
        status=FactStatus.CONFIRMED,
        evidence=[
            Evidence(
                source_id="doc_a.pdf",
                source_type=EvidenceType.PDF_TEXT,
                page_or_location="Page 1",
                verbatim_snippet="Patient is a 71-year-old retired teacher."
            ),
            Evidence(
                source_id="doc_a.pdf",
                source_type=EvidenceType.PDF_TEXT,
                page_or_location="Page 2",
                verbatim_snippet="Previous note incorrectly stated age 63."
            ),
            Evidence(
                source_id="doc_a.pdf",
                source_type=EvidenceType.PDF_TEXT,
                page_or_location="Page 3",
                verbatim_snippet="Patient appeared elderly and frail."
            )
        ]
    )

    verified_fact = verifier.verify_fact(fact)
    # Individual determinations must all be preserved
    results = [ev.verification_result for ev in verified_fact.evidence]
    assert results == [
        VerificationResult.SUPPORTS,
        VerificationResult.CONTRADICTS,
        VerificationResult.INSUFFICIENT
    ]
    # Because a contradiction exists, overall fact state reflects contradiction
    assert verified_fact.verification_state == VerificationResult.CONTRADICTS


# ============================================================================
# 12. PROVIDER FAILURE FAILS SAFELY
# ============================================================================

def test_provider_failure_fails_safely_to_deterministic_rules():
    failing_provider = FlakyFailingLLMProvider()
    verifier = EvidenceVerifier(provider=failing_provider)

    fact = Fact(
        field="suspect_product",
        value="Cardioril",
        status=FactStatus.CONFIRMED
    )
    candidate = Evidence(
        source_id="email_01.eml",
        source_type=EvidenceType.EMAIL_BODY,
        page_or_location="Paragraph 1",
        verbatim_snippet="Patient started taking Cardioril 20 mg."
    )

    # Must not raise exception, must not fabricate SUPPORTS if invalid
    verified = verifier.verify_candidate(fact, candidate)
    assert verified.verification_result == VerificationResult.SUPPORTS  # Rule engine succeeds
    assert "Fallback" in verified.verification_rationale or "explicitly contains" in verified.verification_rationale


def test_provider_failure_on_ambiguous_evidence_defaults_to_insufficient():
    failing_provider = FlakyFailingLLMProvider()
    verifier = EvidenceVerifier(provider=failing_provider)

    fact = Fact(
        field="suspect_product",
        value="Renotril",
        status=FactStatus.CONFIRMED
    )
    candidate = Evidence(
        source_id="clinic_note.pdf",
        source_type=EvidenceType.PDF_TEXT,
        page_or_location="Page 1",
        verbatim_snippet="Patient presented with elevated serum creatinine."
    )

    verified = verifier.verify_candidate(fact, candidate)
    assert verified.verification_result == VerificationResult.INSUFFICIENT
    assert verified.verification_confidence <= 0.50


# ============================================================================
# 13. MOCK LLM PROVIDER VERIFICATION PIPELINE
# ============================================================================

def test_mock_llm_provider_verification_pipeline():
    mock_provider = MockLLMProvider(mocked_result="SUPPORTS", confidence=0.98, rationale="Explicit entailment verified via mock LLM.")
    verifier = EvidenceVerifier(provider=mock_provider)

    fact = Fact(
        field="suspect_product",
        value="Cardioril",
        status=FactStatus.CONFIRMED
    )
    candidate = Evidence(
        source_id="email_01.eml",
        source_type=EvidenceType.EMAIL_BODY,
        page_or_location="Paragraph 1",
        verbatim_snippet="Patient took Cardioril 20 mg."
    )

    verified = verifier.verify_candidate(fact, candidate)
    assert verified.verification_result == VerificationResult.SUPPORTS
    assert verified.verification_confidence == 0.98
    assert "mock LLM" in verified.verification_rationale
    assert verified.verification_metadata["verifier_method"] == "llm_semantic_nli"


# ============================================================================
# 14. ENVELOPE VERIFICATION END-TO-END
# ============================================================================

def test_verify_envelope_enriches_all_fact_ledgers():
    verifier = EvidenceVerifier(use_llm=False)

    fact1 = Fact(
        field="patient_age",
        value="58",
        status=FactStatus.CONFIRMED,
        evidence=[
            Evidence(
                source_id="email_01.eml",
                source_type=EvidenceType.EMAIL_BODY,
                page_or_location="Paragraph 1",
                verbatim_snippet="Patient M.K., a 58-year-old female."
            )
        ]
    )
    fact2 = Fact(
        field="treated_indication",
        value="Not stated",
        status=FactStatus.NOT_STATED,
        evidence=[
            Evidence(
                source_id="email_01.eml",
                source_type=EvidenceType.EMAIL_BODY,
                page_or_location="Paragraph 1",
                verbatim_snippet="Patient presented with jaundice."
            )
        ]
    )

    envelope = CaseEnvelope(
        envelope_id="env-test-verify-01",
        message_id="msg-test-01",
        source_filename="email_01.eml",
        language_detected="English",
        triage=TriageResult(
            is_multi_label=False,
            primary_category=CategoryEnum.SAFETY_REPORT_ICSR,
            labels=[],
            executive_summary="Test clinical summary."
        ),
        document_summary="Test clinical summary.",
        reviewer_summary="Test brief.",
        icsr=IcsrPayload(
            patient=IcsrPatient(
                identifier="M.K.",
                age="58",
                sex="Female",
                facts=[fact1, fact2]
            ),
            facts=[fact1, fact2]
        ),
        fact_ledger=[fact1, fact2]
    )

    verified_env = verifier.verify_envelope(envelope)
    assert "verification_latency_ms" in verified_env.metadata
    assert fact1.verification_state == VerificationResult.SUPPORTS
    assert fact1.evidence[0].verification_result == VerificationResult.SUPPORTS
    assert fact2.verification_state == VerificationResult.INSUFFICIENT
    assert fact2.evidence[0].verification_result == VerificationResult.INSUFFICIENT
