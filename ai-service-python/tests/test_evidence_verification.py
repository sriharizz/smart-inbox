import os
import json
import time
import pytest
from unittest.mock import MagicMock, patch
from typing import List, Optional, Any

from app.schemas.fact_contract import (
    Fact, Evidence, FactStatus, VerificationResult, EvidenceType
)
from app.schemas.case_envelope import CaseEnvelope
from app.schemas.triage_schema import TriageResult, CategoryEnum
from app.schemas.category_payloads import IcsrPayload, IcsrPatient, IcsrProduct, IcsrReaction, IcsrReporter
from app.core.config import settings
from app.core.llm_provider import LLMProvider, GroqProvider, get_llm_provider
from app.services.evidence_verifier import (
    EvidenceVerifier, VerificationIntegrityGuard
)


# ============================================================================
# MOCK PROVIDER FIXTURES FOR HERMETIC UNIT TESTING
# ============================================================================

class MockLLMProvider(LLMProvider):
    """Deterministic mock LLM provider simulating structured verification responses."""
    def __init__(self, result: str = "SUPPORTS", confidence: float = 0.95, rationale: str = "Mock entailment rationale"):
        self._result = result
        self._confidence = confidence
        self._rationale = rationale
        self.call_count = 0
        self.last_contents = None

    @property
    def provider_name(self) -> str:
        return "mock-groq-provider"

    def generate_content(self, contents, system_instruction=None, model=None, temperature=0.0) -> str:
        self.call_count += 1
        self.last_contents = contents
        return json.dumps({
            "verification_result": self._result,
            "confidence": self._confidence,
            "rationale": self._rationale
        })

    def generate_structured(self, contents, response_schema, system_instruction=None, model=None, temperature=0.0):
        raw = self.generate_content(contents, system_instruction, model, temperature)
        return response_schema.model_validate(json.loads(raw))

    def is_healthy(self) -> bool:
        return True


class DynamicMockLLMProvider(LLMProvider):
    """Dynamic mock provider that returns answers mapped to snippets or callbacks."""
    def __init__(self, response_map: dict):
        self._response_map = response_map
        self.call_count = 0

    @property
    def provider_name(self) -> str:
        return "dynamic-mock-groq"

    def generate_content(self, contents, system_instruction=None, model=None, temperature=0.0) -> str:
        self.call_count += 1
        for snippet_key, resp in self._response_map.items():
            if snippet_key in str(contents):
                return json.dumps(resp)
        return json.dumps({
            "verification_result": "INSUFFICIENT",
            "confidence": 0.5,
            "rationale": "Default dynamic mock fallback"
        })

    def generate_structured(self, contents, response_schema, system_instruction=None, model=None, temperature=0.0):
        raw = self.generate_content(contents, system_instruction, model, temperature)
        return response_schema.model_validate(json.loads(raw))

    def is_healthy(self) -> bool:
        return True


class FlakyFailingLLMProvider(LLMProvider):
    """Mock provider simulating an API outage, timeout, or rate-limit exhaustion."""
    def __init__(self, error_message: str = "Groq 429 RESOURCE_EXHAUSTED / Timeout"):
        self.error_message = error_message

    @property
    def provider_name(self) -> str:
        return "failing-groq-provider"

    def generate_content(self, contents, system_instruction=None, model=None, temperature=0.0) -> str:
        raise RuntimeError(self.error_message)

    def generate_structured(self, contents, response_schema, system_instruction=None, model=None, temperature=0.0):
        raise RuntimeError(self.error_message)

    def is_healthy(self) -> bool:
        return True


class MalformedJsonLLMProvider(LLMProvider):
    """Mock provider returning non-JSON or malformed output."""
    @property
    def provider_name(self) -> str:
        return "malformed-groq-provider"

    def generate_content(self, contents, system_instruction=None, model=None, temperature=0.0) -> str:
        return "I am an AI and here is your analysis: The candidate seems to support the claim partially."

    def generate_structured(self, contents, response_schema, system_instruction=None, model=None, temperature=0.0):
        raise ValueError("Invalid JSON response")

    def is_healthy(self) -> bool:
        return True


class FailIfCalledProvider(LLMProvider):
    """Provider that raises an AssertionError if called, proving a guard short-circuited."""
    @property
    def provider_name(self) -> str:
        return "fail-if-called"

    def generate_content(self, contents, system_instruction=None, model=None, temperature=0.0) -> str:
        raise AssertionError("Provider was called unexpectedly when short-circuit guard should have triggered!")

    def generate_structured(self, contents, response_schema, system_instruction=None, model=None, temperature=0.0):
        raise AssertionError("Provider was called unexpectedly!")

    def is_healthy(self) -> bool:
        return True


# ============================================================================
# 1. SUPPORTS FOR DIRECT ENTAILMENT
# ============================================================================

def test_supports_for_direct_entailment():
    provider = MockLLMProvider(result="SUPPORTS", confidence=0.96, rationale="Candidate explicitly establishes patient age 71.")
    verifier = EvidenceVerifier(provider=provider)

    fact = Fact(field="patient_age", value="71", status=FactStatus.CONFIRMED)
    candidate = Evidence(
        source_id="cioms_form.pdf",
        source_type=EvidenceType.PDF_TEXT,
        page_or_location="Page 1, Box 2",
        verbatim_snippet="The patient is a 71-year-old male with hypertension."
    )

    verified = verifier.verify_candidate(fact, candidate)
    assert verified.verification_result == VerificationResult.SUPPORTS
    assert verified.verification_confidence == 0.96
    assert "71" in verified.verification_rationale
    assert verified.verification_metadata["verifier_method"] == "llm_semantic_nli"
    assert verified.verification_metadata["provider"] == "mock-groq-provider"
    assert provider.call_count == 1


# ============================================================================
# 2. CONTRADICTS FOR EXPLICIT CONTRADICTION
# ============================================================================

def test_contradicts_for_explicit_contradiction():
    provider = MockLLMProvider(result="CONTRADICTS", confidence=0.94, rationale="Explicit contradiction: source states age 63 vs asserted age 71.")
    verifier = EvidenceVerifier(provider=provider)

    fact = Fact(field="patient_age", value="71", status=FactStatus.CONFIRMED)
    candidate = Evidence(
        source_id="email_01.eml",
        source_type=EvidenceType.EMAIL_BODY,
        page_or_location="Paragraph 1",
        verbatim_snippet="The patient's age was 63 at presentation."
    )

    verified = verifier.verify_candidate(fact, candidate)
    assert verified.verification_result == VerificationResult.CONTRADICTS
    assert verified.verification_confidence == 0.94
    assert "contradiction" in verified.verification_rationale.lower()
    assert provider.call_count == 1


# ============================================================================
# 3. INSUFFICIENT FOR RELATED NON-ENTAILING EVIDENCE
# ============================================================================

def test_insufficient_for_related_non_entailing_evidence():
    provider = MockLLMProvider(result="INSUFFICIENT", confidence=0.35, rationale="Emergency intervention mention does not establish adverse event anaphylaxis.")
    verifier = EvidenceVerifier(provider=provider)

    fact = Fact(field="adverse_event", value="anaphylaxis", status=FactStatus.CONFIRMED)
    candidate = Evidence(
        source_id="er_notes.pdf",
        source_type=EvidenceType.PDF_TEXT,
        page_or_location="Page 1",
        verbatim_snippet="The patient received emergency department treatment."
    )

    verified = verifier.verify_candidate(fact, candidate)
    assert verified.verification_result == VerificationResult.INSUFFICIENT
    assert verified.verification_confidence == 0.35
    assert provider.call_count == 1


# ============================================================================
# 4. NEGATION REASONING VIA LLM
# ============================================================================

def test_negation_interpretation_via_llm():
    provider = MockLLMProvider(result="CONTRADICTS", confidence=0.98, rationale="Passage documents explicit absence of anaphylaxis ('no signs of anaphylaxis').")
    verifier = EvidenceVerifier(provider=provider)

    fact = Fact(field="adverse_event", value="anaphylaxis", status=FactStatus.CONFIRMED)
    candidate = Evidence(
        source_id="discharge_summary.pdf",
        source_type=EvidenceType.PDF_TEXT,
        page_or_location="Page 2",
        verbatim_snippet="Vital signs remained stable; no signs of anaphylaxis were observed."
    )

    verified = verifier.verify_candidate(fact, candidate)
    assert verified.verification_result == VerificationResult.CONTRADICTS
    assert verified.verification_confidence == 0.98


# ============================================================================
# 5. RESCUE / CONCOMITANT MEDICATION DISTINCTION VIA LLM
# ============================================================================

def test_rescue_medication_segregation_via_llm():
    provider = MockLLMProvider(result="INSUFFICIENT", confidence=0.15, rationale="Epinephrine 0.3 mg IM is an acute resuscitation drug, not suspect product dose.")
    verifier = EvidenceVerifier(provider=provider)

    fact = Fact(field="product_dose", value="20 mg", status=FactStatus.CONFIRMED)
    candidate = Evidence(
        source_id="hospital_chart.pdf",
        source_type=EvidenceType.PDF_TEXT,
        page_or_location="Resuscitation Section",
        verbatim_snippet="Epinephrine 0.3 mg IM was administered immediately for acute anaphylaxis resuscitation."
    )

    verified = verifier.verify_candidate(fact, candidate)
    assert verified.verification_result == VerificationResult.INSUFFICIENT
    assert "resuscitation" in verified.verification_rationale.lower() or "rescue" in verified.verification_rationale.lower()


# ============================================================================
# 6. REPORTER ATTRIBUTION REASONING VIA LLM
# ============================================================================

def test_reporter_attribution_via_llm():
    provider = MockLLMProvider(result="INSUFFICIENT", confidence=0.20, rationale="Dr. Robert Vance is mentioned in narrative as attending physician, not submitting reporter.")
    verifier = EvidenceVerifier(provider=provider)

    fact = Fact(field="reporter_role", value="Physician", status=FactStatus.CONFIRMED)
    candidate = Evidence(
        source_id="email_03.eml",
        source_type=EvidenceType.EMAIL_BODY,
        page_or_location="Paragraph 3",
        verbatim_snippet="The physician mentioned in the email was Dr. Robert Vance, who treated me at urgent care."
    )

    verified = verifier.verify_candidate(fact, candidate)
    assert verified.verification_result == VerificationResult.INSUFFICIENT


# ============================================================================
# 7. DATE-ROLE TEMPORAL DISCRIMINATION VIA LLM
# ============================================================================

def test_date_role_distinction_via_llm():
    provider = MockLLMProvider(result="INSUFFICIENT", confidence=0.25, rationale="Date 2025-11-14 refers to reaction onset, not treatment start date.")
    verifier = EvidenceVerifier(provider=provider)

    fact = Fact(field="treatment_start_date", value="2025-11-14", status=FactStatus.CONFIRMED)
    candidate = Evidence(
        source_id="patient_log.pdf",
        source_type=EvidenceType.PDF_TEXT,
        page_or_location="Page 1",
        verbatim_snippet="Adverse reaction onset was noted on 2025-11-14 when rash developed."
    )

    verified = verifier.verify_candidate(fact, candidate)
    assert verified.verification_result == VerificationResult.INSUFFICIENT


# ============================================================================
# 8. MULTILINGUAL SEMANTIC EQUIVALENCE (VERBATIM SNIPPET PRESERVED)
# ============================================================================

def test_multilingual_semantic_equivalence_via_llm():
    provider = MockLLMProvider(result="SUPPORTS", confidence=0.95, rationale="Spanish clinical diagnosis 'Necrólisis Epidérmica Tóxica' entails Toxic Epidermal Necrolysis.")
    verifier = EvidenceVerifier(provider=provider)

    fact = Fact(field="adverse_event", value="Toxic Epidermal Necrolysis", status=FactStatus.CONFIRMED)
    original_spanish_snippet = "Diagnóstico clínico: Necrólisis Epidérmica Tóxica severa en >35% SC."
    candidate = Evidence(
        source_id="informe_madrid.pdf",
        source_type=EvidenceType.PDF_TEXT,
        page_or_location="Página 1",
        verbatim_snippet=original_spanish_snippet
    )

    verified = verifier.verify_candidate(fact, candidate)
    assert verified.verification_result == VerificationResult.SUPPORTS
    # Original non-English snippet must remain strictly untouched
    assert verified.verbatim_snippet == original_spanish_snippet


# ============================================================================
# 9. VAGUE WORDING IS INSUFFICIENT FOR EXACT VALUE
# ============================================================================

def test_vague_wording_via_llm():
    provider = MockLLMProvider(result="INSUFFICIENT", confidence=0.30, rationale="Descriptive term 'elderly' does not establish exact numeric age 71.")
    verifier = EvidenceVerifier(provider=provider)

    fact = Fact(field="patient_age", value="71", status=FactStatus.CONFIRMED)
    candidate = Evidence(
        source_id="clinic_note.pdf",
        source_type=EvidenceType.PDF_TEXT,
        page_or_location="Page 1",
        verbatim_snippet="The patient was an elderly individual presenting with fatigue."
    )

    verified = verifier.verify_candidate(fact, candidate)
    assert verified.verification_result == VerificationResult.INSUFFICIENT


# ============================================================================
# 10. NOT_STATED MECHANICAL GUARD (NO LLM CALL)
# ============================================================================

def test_not_stated_guard_bypasses_llm_completely():
    # If the provider is called, it will raise an AssertionError
    verifier = EvidenceVerifier(provider=FailIfCalledProvider())

    fact = Fact(field="treatment_stop_date", value="Not stated", status=FactStatus.NOT_STATED)
    candidate = Evidence(
        source_id="email_01.eml",
        source_type=EvidenceType.EMAIL_BODY,
        page_or_location="Paragraph 1",
        verbatim_snippet="Patient took medication regularly."
    )

    verified = verifier.verify_candidate(fact, candidate)
    assert verified.verification_result == VerificationResult.INSUFFICIENT
    assert verified.verification_confidence == 0.0
    assert verified.verification_metadata["verifier_method"] == "integrity_guard"
    assert verified.verification_metadata["rule"] == "not_stated_guard"


# ============================================================================
# 11. RETRIEVAL SCORE AND VERIFICATION CONFIDENCE REMAIN DISTINCT
# ============================================================================

def test_retrieval_relevance_distinct_from_verification_confidence():
    provider = MockLLMProvider(result="INSUFFICIENT", confidence=0.10, rationale="High lexical similarity on resuscitation terms does not establish suspect dose.")
    verifier = EvidenceVerifier(provider=provider)

    fact = Fact(field="product_dose", value="Cardioril 20 mg", status=FactStatus.CONFIRMED)
    candidate = Evidence(
        source_id="er_notes.pdf",
        source_type=EvidenceType.PDF_TEXT,
        page_or_location="Page 1",
        verbatim_snippet="Emergency resuscitation was attempted with Epinephrine 0.3 mg IM.",
        retrieval_metadata={"relevance_score": 0.94, "retrieval_method": "hybrid"}
    )

    verified = verifier.verify_candidate(fact, candidate)
    # Retrieval score remains 0.94
    assert verified.retrieval_metadata["relevance_score"] == 0.94
    # Verification determination is INSUFFICIENT with confidence 0.10
    assert verified.verification_result == VerificationResult.INSUFFICIENT
    assert verified.verification_confidence == 0.10
    assert verified.retrieval_metadata["relevance_score"] != verified.verification_confidence


# ============================================================================
# 12. MULTIPLE CANDIDATES PRESERVE INDIVIDUAL DETERMINATIONS
# ============================================================================

def test_multiple_candidates_preserve_individual_determinations():
    response_map = {
        "71-year-old retired teacher": {"verification_result": "SUPPORTS", "confidence": 0.96, "rationale": "Explicitly confirms 71."},
        "incorrectly stated age 63": {"verification_result": "CONTRADICTS", "confidence": 0.92, "rationale": "Contains conflicting age 63."},
        "elderly and frail": {"verification_result": "INSUFFICIENT", "confidence": 0.30, "rationale": "Vague description without age."}
    }
    dynamic_provider = DynamicMockLLMProvider(response_map=response_map)
    verifier = EvidenceVerifier(provider=dynamic_provider)

    cand1 = Evidence(source_id="doc.pdf", source_type=EvidenceType.PDF_TEXT, page_or_location="P1", verbatim_snippet="Patient is a 71-year-old retired teacher.")
    cand2 = Evidence(source_id="doc.pdf", source_type=EvidenceType.PDF_TEXT, page_or_location="P2", verbatim_snippet="Previous note incorrectly stated age 63.")
    cand3 = Evidence(source_id="doc.pdf", source_type=EvidenceType.PDF_TEXT, page_or_location="P3", verbatim_snippet="Patient appeared elderly and frail.")

    fact = Fact(field="patient_age", value="71", status=FactStatus.CONFIRMED, evidence=[cand1, cand2, cand3])

    verified_fact = verifier.verify_fact(fact)
    # Individual results preserved
    assert [e.verification_result for e in verified_fact.evidence] == [
        VerificationResult.SUPPORTS,
        VerificationResult.CONTRADICTS,
        VerificationResult.INSUFFICIENT
    ]
    # Conflict detected among candidates
    assert verified_fact.verification_state == VerificationResult.CONTRADICTS


# ============================================================================
# 13. GROQ PROVIDER REQUEST / RESPONSE MAPPING (MOCKED HTTP BOUNDARY)
# ============================================================================

def test_groq_provider_request_and_response_mapping():
    mock_http_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{
            "message": {
                "content": json.dumps({
                    "verification_result": "SUPPORTS",
                    "confidence": 0.92,
                    "rationale": "Structured Groq verification test."
                })
            }
        }]
    }
    mock_http_client.post.return_value = mock_resp

    groq_provider = GroqProvider(api_key="mock_key", client=mock_http_client)
    raw = groq_provider.generate_content("Fact & Evidence Payload", system_instruction="Verifier prompt")

    assert "SUPPORTS" in raw
    # Verify call parameters
    assert mock_http_client.post.called
    args, kwargs = mock_http_client.post.call_args
    assert "https://api.groq.com/openai/v1/chat/completions" in args[0]
    assert kwargs["headers"]["Authorization"] == "Bearer mock_key"
    assert kwargs["json"]["model"] == "openai/gpt-oss-20b"
    assert kwargs["json"]["response_format"] == {"type": "json_object"}


# ============================================================================
# 14. INVALID GROQ STRUCTURED OUTPUT FAILS SAFELY
# ============================================================================

def test_groq_invalid_json_fails_safely_to_insufficient():
    malformed_provider = MalformedJsonLLMProvider()
    verifier = EvidenceVerifier(provider=malformed_provider)

    fact = Fact(field="suspect_product", value="Cardioril", status=FactStatus.CONFIRMED)
    candidate = Evidence(
        source_id="email.eml",
        source_type=EvidenceType.EMAIL_BODY,
        page_or_location="Body",
        verbatim_snippet="Patient took Cardioril 20 mg."
    )

    verified = verifier.verify_candidate(fact, candidate)
    # Must fail safely to INSUFFICIENT with 0.0 confidence and fallback method
    assert verified.verification_result == VerificationResult.INSUFFICIENT
    assert verified.verification_confidence == 0.0
    assert verified.verification_metadata["verifier_method"] == "fallback"


# ============================================================================
# 15. GROQ TIMEOUT OR 429 RATE-LIMIT FAILS SAFELY
# ============================================================================

def test_groq_timeout_or_429_fails_safely_to_insufficient():
    failing_provider = FlakyFailingLLMProvider("Groq 429 Too Many Requests: Rate limit exceeded")
    verifier = EvidenceVerifier(provider=failing_provider)

    fact = Fact(field="suspect_product", value="Cardioril", status=FactStatus.CONFIRMED)
    candidate = Evidence(
        source_id="email.eml",
        source_type=EvidenceType.EMAIL_BODY,
        page_or_location="Body",
        verbatim_snippet="Patient took Cardioril 20 mg."
    )

    verified = verifier.verify_candidate(fact, candidate)
    # Must not raise an unhandled exception; must fail safely to INSUFFICIENT
    assert verified.verification_result == VerificationResult.INSUFFICIENT
    assert verified.verification_confidence == 0.0
    assert verified.verification_metadata["verifier_method"] == "fallback"
    assert "429" in verified.verification_metadata["error"]


# ============================================================================
# 16. NO DETERMINISTIC SEMANTIC RULE BYPASSES PROVIDER
# ============================================================================

def test_no_deterministic_semantic_rule_bypasses_provider():
    """
    Ensures that exact substring matches (e.g. Cardioril in snippet) are NOT
    automatically marked SUPPORTS without consulting the LLM provider.
    """
    provider = MockLLMProvider(result="CONTRADICTS", confidence=0.88, rationale="Snippet denies Cardioril administration.")
    verifier = EvidenceVerifier(provider=provider)

    fact = Fact(field="suspect_product", value="Cardioril", status=FactStatus.CONFIRMED)
    candidate = Evidence(
        source_id="note.pdf",
        source_type=EvidenceType.PDF_TEXT,
        page_or_location="P1",
        verbatim_snippet="Cardioril was withheld; patient never took Cardioril."
    )

    verified = verifier.verify_candidate(fact, candidate)
    # Provider was called and its determination was respected (NOT overridden by substring check)
    assert verified.verification_result == VerificationResult.CONTRADICTS
    assert provider.call_count == 1


# ============================================================================
# 17. NO BENCHMARK-SPECIFIC DICTIONARY IN EVIDENCE VERIFIER
# ============================================================================

def test_no_benchmark_specific_dictionary_in_verifier():
    """Confirms MULTILINGUAL_MAP and RESCUE_MEDS keyword dictionaries were removed."""
    import app.services.evidence_verifier as ev_module
    assert not hasattr(ev_module, "MULTILINGUAL_MAP")
    assert not hasattr(ev_module, "RESCUE_MEDS")
    assert not hasattr(ev_module, "DeterministicClinicalVerifier")


# ============================================================================
# 18. SOURCE ISOLATION & ENVELOPE VERIFICATION
# ============================================================================

def test_source_isolation_and_envelope_traversal():
    provider = MockLLMProvider(result="SUPPORTS", confidence=0.95, rationale="Verified from envelope local context.")
    verifier = EvidenceVerifier(provider=provider)

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
            patient=IcsrPatient(identifier="M.K.", age="58", sex="Female", facts=[fact1]),
            facts=[fact1]
        ),
        fact_ledger=[fact1]
    )

    verified_env = verifier.verify_envelope(envelope, document_context="Local document context for email_01.eml")
    assert "verification_latency_ms" in verified_env.metadata
    assert fact1.verification_state == VerificationResult.SUPPORTS
    assert fact1.evidence[0].verification_result == VerificationResult.SUPPORTS
    assert fact1.evidence[0].verification_metadata["verifier_method"] == "llm_semantic_nli"


# ============================================================================
# 19. OPTIONAL LIVE GROQ API INTEGRATION TEST
# ============================================================================

@pytest.mark.integration
def test_live_groq_verification_integration():
    """
    Live integration test against Groq's openai/gpt-oss-20b API.
    Runs only when GROQ_API_KEY is configured in the environment.
    """
    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        pytest.skip("GROQ_API_KEY environment variable is not set; skipping live Groq API test.")

    groq_provider = GroqProvider(api_key=groq_key)
    verifier = EvidenceVerifier(provider=groq_provider)

    fact = Fact(field="patient_age", value="71", status=FactStatus.CONFIRMED)
    candidate = Evidence(
        source_id="live_test.pdf",
        source_type=EvidenceType.PDF_TEXT,
        page_or_location="Page 1",
        verbatim_snippet="The patient is a 71-year-old retired schoolteacher."
    )

    verified = verifier.verify_candidate(fact, candidate)
    assert verified.verification_result == VerificationResult.SUPPORTS
    assert verified.verification_confidence > 0.5
    assert verified.verification_metadata["provider"] == "groq"
    assert verified.verification_metadata["model"] == "openai/gpt-oss-20b"
    assert "latency_ms" in verified.verification_metadata


# ============================================================================
# STEP 5 OPTIMIZATION: BATCHED VERIFICATION TESTS (22 MANDATORY REQUIREMENTS)
# ============================================================================

class MockBatchLLMProvider(LLMProvider):
    """Deterministic mock provider returning structured responses for batched verification."""
    def __init__(self, default_result: str = "SUPPORTS", default_confidence: float = 0.95):
        self.default_result = default_result
        self.default_confidence = default_confidence
        self.call_count = 0
        self.submitted_prompts = []

    @property
    def provider_name(self) -> str:
        return "mock-batch-groq"

    def is_healthy(self) -> bool:
        return True

    def generate_content(self, contents, system_instruction=None, model=None, temperature=0.0) -> str:
        self.call_count += 1
        self.submitted_prompts.append(str(contents))
        
        # Parse items from submitted payload
        content_str = str(contents)
        try:
            start_idx = content_str.find("{")
            end_idx = content_str.rfind("}") + 1
            payload = json.loads(content_str[start_idx:end_idx])
            items = payload.get("items", [])
            results = [
                {
                    "fact_id": item["fact_id"],
                    "evidence_id": item["evidence_id"],
                    "result": self.default_result,
                    "confidence": self.default_confidence,
                    "rationale": f"Mock batch verification for {item['fact_id']}"
                }
                for item in items
            ]
            return json.dumps({"results": results})
        except Exception:
            return json.dumps({"results": []})

    def generate_structured(self, contents, response_schema, system_instruction=None, model=None, temperature=0.0):
        raw = self.generate_content(contents, system_instruction, model, temperature)
        return response_schema.model_validate(json.loads(raw))


class FailingAfterFirstBatchProvider(LLMProvider):
    """Simulates Groq succeeding on Batch 1, then failing with 429 on Batch 2."""
    def __init__(self):
        self.call_count = 0
        self._rate_limited_until = 0.0

    @property
    def provider_name(self) -> str:
        return "failing-after-first"

    def is_healthy(self) -> bool:
        return self._rate_limited_until <= time.time()

    def generate_content(self, contents, system_instruction=None, model=None, temperature=0.0) -> str:
        self.call_count += 1
        if self.call_count == 1:
            content_str = str(contents)
            start_idx = content_str.find("{")
            end_idx = content_str.rfind("}") + 1
            payload = json.loads(content_str[start_idx:end_idx])
            results = [
                {
                    "fact_id": item["fact_id"],
                    "evidence_id": item["evidence_id"],
                    "result": "SUPPORTS",
                    "confidence": 0.95,
                    "rationale": "Batch 1 success"
                }
                for item in payload.get("items", [])
            ]
            return json.dumps({"results": results})
        else:
            self._rate_limited_until = time.time() + 60.0
            raise RuntimeError("HTTP 429: Rate limit reached on tokens per day (TPD)")

    def generate_structured(self, contents, response_schema, system_instruction=None, model=None, temperature=0.0):
        raw = self.generate_content(contents, system_instruction, model, temperature)
        return response_schema.model_validate(json.loads(raw))


def _make_test_envelope(num_facts: int = 3, duplicate_evidence: bool = False, candidates_per_fact: int = 1) -> CaseEnvelope:
    """Helper to build synthetic CaseEnvelope with controlled fact & candidate counts."""
    facts = []
    shared_ev = Evidence(
        source_id="test_case.pdf",
        source_type=EvidenceType.PDF_TEXT,
        page_or_location="Page 1, Box 1",
        verbatim_snippet="Common clinical documentation snippet shared across facts."
    )

    for i in range(num_facts):
        ev_list = []
        if duplicate_evidence:
            ev_list.append(shared_ev)
        else:
            for c in range(candidates_per_fact):
                ev_list.append(Evidence(
                    source_id="test_case.pdf",
                    source_type=EvidenceType.PDF_TEXT,
                    page_or_location=f"Page {i+1}, Box {c+1}",
                    verbatim_snippet=f"Unique clinical observation {i}_{c} establishing assertion."
                ))
        
        f = Fact(
            fact_id=f"fact-test-{i+1:03d}",
            field=f"clinical_field_{i+1}",
            value=f"Value_{i+1}",
            status=FactStatus.CONFIRMED,
            evidence=ev_list
        )
        facts.append(f)

    return CaseEnvelope(
        envelope_id="env-batch-test-01",
        message_id="msg-batch-01",
        source_filename="test_case.pdf",
        language_detected="English",
        triage=TriageResult(
            is_multi_label=False,
            primary_category=CategoryEnum.SAFETY_REPORT_ICSR,
            labels=[],
            executive_summary="Batch verification test case."
        ),
        document_summary="Synthetic batch test document.",
        reviewer_summary="Synthetic brief.",
        icsr=IcsrPayload(facts=facts),
        fact_ledger=facts
    )


# 1. One small case uses one batch
def test_batching_small_case_uses_one_batch():
    provider = MockBatchLLMProvider(default_result="SUPPORTS", default_confidence=0.95)
    verifier = EvidenceVerifier(provider=provider)
    envelope = _make_test_envelope(num_facts=3)

    verified = verifier.verify_envelope(envelope)
    metrics = verified.metadata["verification_metrics"]
    assert metrics["number_of_verification_batches"] == 1
    assert metrics["groq_requests_sent"] == 1
    assert provider.call_count == 1


# 2. Medium case splits into multiple batches
def test_batching_medium_case_splits_into_multiple_batches():
    provider = MockBatchLLMProvider(default_result="SUPPORTS", default_confidence=0.95)
    verifier = EvidenceVerifier(provider=provider)
    # 20 facts with max batch items 15 -> 2 batches
    envelope = _make_test_envelope(num_facts=20)

    verified = verifier.verify_envelope(envelope)
    metrics = verified.metadata["verification_metrics"]
    assert metrics["number_of_verification_batches"] == 2
    assert metrics["groq_requests_sent"] == 2
    assert provider.call_count == 2


# 3. Dense case uses bounded batches
def test_batching_dense_case_uses_bounded_batches():
    provider = MockBatchLLMProvider(default_result="SUPPORTS", default_confidence=0.95)
    verifier = EvidenceVerifier(provider=provider)
    # 45 facts with max batch items 15 -> 3 batches
    envelope = _make_test_envelope(num_facts=45)

    verified = verifier.verify_envelope(envelope)
    metrics = verified.metadata["verification_metrics"]
    assert metrics["number_of_verification_batches"] == 3
    assert metrics["groq_requests_sent"] == 3
    assert provider.call_count == 3
    assert metrics["groq_requests_avoided"] == 45 - 3


# 4. Duplicate evidence is deduplicated in catalog
def test_batching_duplicate_evidence_is_deduplicated():
    provider = MockBatchLLMProvider(default_result="SUPPORTS", default_confidence=0.95)
    verifier = EvidenceVerifier(provider=provider)
    # 10 facts sharing the exact same evidence snippet
    envelope = _make_test_envelope(num_facts=10, duplicate_evidence=True)

    verified = verifier.verify_envelope(envelope)
    metrics = verified.metadata["verification_metrics"]
    assert metrics["total_unique_evidence_items"] == 1
    # Check that in the submitted prompt, evidence catalog has 1 entry
    prompt = provider.submitted_prompts[0]
    assert "evidence_catalog" in prompt


# 5. Weak redundant candidates are pruned
def test_batching_weak_redundant_candidates_are_pruned():
    provider = MockBatchLLMProvider(default_result="SUPPORTS", default_confidence=0.95)
    verifier = EvidenceVerifier(provider=provider)
    # 1 fact with 5 candidates, default top K is 2
    envelope = _make_test_envelope(num_facts=1, candidates_per_fact=5)

    verified = verifier.verify_envelope(envelope)
    fact = verified.fact_ledger[0]
    assert len(fact.evidence) == 5
    # First 2 candidates were evaluated
    assert fact.evidence[0].verification_metadata["verifier_method"] == "llm_semantic_nli"
    assert fact.evidence[1].verification_metadata["verifier_method"] == "llm_semantic_nli"
    # Excess 3 candidates were pruned
    for excess in fact.evidence[2:]:
        assert excess.verification_result == VerificationResult.INSUFFICIENT
        assert excess.verification_metadata["verifier_method"] == "pruned"
        assert excess.verification_metadata["rule"] == "excess_candidate_budget"


# 6. Every verification result preserves fact_id
def test_batching_every_verification_result_preserves_fact_id():
    provider = MockBatchLLMProvider(default_result="SUPPORTS", default_confidence=0.95)
    verifier = EvidenceVerifier(provider=provider)
    envelope = _make_test_envelope(num_facts=5)

    verified = verifier.verify_envelope(envelope)
    for i, f in enumerate(verified.fact_ledger):
        assert f.fact_id == f"fact-test-{i+1:03d}"


# 7. Every verification result preserves evidence_id
def test_batching_every_verification_result_preserves_evidence_id():
    provider = MockBatchLLMProvider(default_result="SUPPORTS", default_confidence=0.95)
    verifier = EvidenceVerifier(provider=provider)
    envelope = _make_test_envelope(num_facts=4)

    original_ids = [f.evidence[0].evidence_id for f in envelope.fact_ledger]
    verified = verifier.verify_envelope(envelope)
    for i, f in enumerate(verified.fact_ledger):
        assert f.evidence[0].evidence_id == original_ids[i]


# 8. Malformed structured output is rejected safely
def test_batching_malformed_structured_output_is_rejected_safely():
    malformed_provider = MalformedJsonLLMProvider()
    verifier = EvidenceVerifier(provider=malformed_provider)
    envelope = _make_test_envelope(num_facts=3)

    verified = verifier.verify_envelope(envelope)
    for f in verified.fact_ledger:
        for ev in f.evidence:
            assert ev.verification_result == VerificationResult.INSUFFICIENT
            assert ev.verification_confidence == 0.0
            assert ev.verification_metadata["verifier_method"] == "fallback"


# 9. Unknown fact_id is rejected
def test_batching_unknown_fact_id_is_rejected():
    class RogueFactProvider(LLMProvider):
        @property
        def provider_name(self) -> str:
            return "rogue-fact-provider"
        def is_healthy(self) -> bool:
            return True
        def generate_content(self, contents, system_instruction=None, model=None, temperature=0.0) -> str:
            return json.dumps({
                "results": [
                    {"fact_id": "fact-UNKNOWN-999", "evidence_id": "ev-01", "result": "SUPPORTS", "confidence": 0.99, "rationale": "Rogue fact injection"}
                ]
            })
        def generate_structured(self, contents, response_schema, system_instruction=None, model=None, temperature=0.0):
            return response_schema.model_validate(json.loads(self.generate_content(contents)))

    verifier = EvidenceVerifier(provider=RogueFactProvider())
    envelope = _make_test_envelope(num_facts=2)

    verified = verifier.verify_envelope(envelope)
    # Submitted items were not matched by the rogue fact_id, so they must safely fall back to INSUFFICIENT
    for f in verified.fact_ledger:
        for ev in f.evidence:
            assert ev.verification_result == VerificationResult.INSUFFICIENT
            assert ev.verification_confidence == 0.0


# 10. Unknown evidence_id is rejected
def test_batching_unknown_evidence_id_is_rejected():
    class RogueEvidenceProvider(LLMProvider):
        @property
        def provider_name(self) -> str:
            return "rogue-evidence-provider"
        def is_healthy(self) -> bool:
            return True
        def generate_content(self, contents, system_instruction=None, model=None, temperature=0.0) -> str:
            content_str = str(contents)
            start_idx = content_str.find("{")
            end_idx = content_str.rfind("}") + 1
            payload = json.loads(content_str[start_idx:end_idx])
            items = payload.get("items", [])
            return json.dumps({
                "results": [
                    {"fact_id": items[0]["fact_id"], "evidence_id": "UNKNOWN-EVID-999", "result": "SUPPORTS", "confidence": 0.99, "rationale": "Rogue evidence"}
                ]
            })
        def generate_structured(self, contents, response_schema, system_instruction=None, model=None, temperature=0.0):
            return response_schema.model_validate(json.loads(self.generate_content(contents)))

    verifier = EvidenceVerifier(provider=RogueEvidenceProvider())
    envelope = _make_test_envelope(num_facts=2)

    verified = verifier.verify_envelope(envelope)
    # First item had wrong evidence_id, so it falls back to INSUFFICIENT
    assert verified.fact_ledger[0].evidence[0].verification_result == VerificationResult.INSUFFICIENT


# 11. Duplicate returned result is rejected
def test_batching_duplicate_returned_result_is_rejected():
    class DuplicateResultProvider(LLMProvider):
        @property
        def provider_name(self) -> str:
            return "dup-result-provider"
        def is_healthy(self) -> bool:
            return True
        def generate_content(self, contents, system_instruction=None, model=None, temperature=0.0) -> str:
            content_str = str(contents)
            start_idx = content_str.find("{")
            end_idx = content_str.rfind("}") + 1
            payload = json.loads(content_str[start_idx:end_idx])
            items = payload.get("items", [])
            f0 = items[0]["fact_id"]
            e0 = items[0]["evidence_id"]
            return json.dumps({
                "results": [
                    {"fact_id": f0, "evidence_id": e0, "result": "SUPPORTS", "confidence": 0.95, "rationale": "First result"},
                    {"fact_id": f0, "evidence_id": e0, "result": "CONTRADICTS", "confidence": 0.10, "rationale": "Duplicate illegal result"}
                ]
            })
        def generate_structured(self, contents, response_schema, system_instruction=None, model=None, temperature=0.0):
            return response_schema.model_validate(json.loads(self.generate_content(contents)))

    verifier = EvidenceVerifier(provider=DuplicateResultProvider())
    envelope = _make_test_envelope(num_facts=1)

    verified = verifier.verify_envelope(envelope)
    # First result was SUPPORTS, second was rejected
    assert verified.fact_ledger[0].evidence[0].verification_result == VerificationResult.SUPPORTS
    assert verified.fact_ledger[0].evidence[0].verification_confidence == 0.95


# 12. Confidence validation works (bounds and finite floats)
def test_batching_confidence_validation_works():
    class OutOfBoundsConfidenceProvider(LLMProvider):
        @property
        def provider_name(self) -> str:
            return "bounds-provider"
        def is_healthy(self) -> bool:
            return True
        def generate_content(self, contents, system_instruction=None, model=None, temperature=0.0) -> str:
            content_str = str(contents)
            start_idx = content_str.find("{")
            end_idx = content_str.rfind("}") + 1
            payload = json.loads(content_str[start_idx:end_idx])
            items = payload.get("items", [])
            return json.dumps({
                "results": [
                    {"fact_id": items[0]["fact_id"], "evidence_id": items[0]["evidence_id"], "result": "SUPPORTS", "confidence": 1.45, "rationale": "Over 1.0"},
                    {"fact_id": items[1]["fact_id"], "evidence_id": items[1]["evidence_id"], "result": "SUPPORTS", "confidence": -0.80, "rationale": "Negative"}
                ]
            })
        def generate_structured(self, contents, response_schema, system_instruction=None, model=None, temperature=0.0):
            return response_schema.model_validate(json.loads(self.generate_content(contents)))

    verifier = EvidenceVerifier(provider=OutOfBoundsConfidenceProvider())
    envelope = _make_test_envelope(num_facts=2)

    verified = verifier.verify_envelope(envelope)
    assert verified.fact_ledger[0].evidence[0].verification_confidence == 1.0  # Clamped to 1.0
    assert verified.fact_ledger[1].evidence[0].verification_confidence == 0.0  # Clamped to 0.0


# 13. SUPPORTS preserved
def test_batching_supports_preserved():
    provider = MockBatchLLMProvider(default_result="SUPPORTS", default_confidence=0.98)
    verifier = EvidenceVerifier(provider=provider)
    envelope = _make_test_envelope(num_facts=2)

    verified = verifier.verify_envelope(envelope)
    assert verified.fact_ledger[0].evidence[0].verification_result == VerificationResult.SUPPORTS
    assert verified.fact_ledger[0].verification_state == VerificationResult.SUPPORTS


# 14. CONTRADICTS preserved
def test_batching_contradicts_preserved():
    provider = MockBatchLLMProvider(default_result="CONTRADICTS", default_confidence=0.97)
    verifier = EvidenceVerifier(provider=provider)
    envelope = _make_test_envelope(num_facts=2)

    verified = verifier.verify_envelope(envelope)
    assert verified.fact_ledger[0].evidence[0].verification_result == VerificationResult.CONTRADICTS
    assert verified.fact_ledger[0].verification_state == VerificationResult.CONTRADICTS


# 15. INSUFFICIENT preserved
def test_batching_insufficient_preserved():
    provider = MockBatchLLMProvider(default_result="INSUFFICIENT", default_confidence=0.30)
    verifier = EvidenceVerifier(provider=provider)
    envelope = _make_test_envelope(num_facts=2)

    verified = verifier.verify_envelope(envelope)
    assert verified.fact_ledger[0].evidence[0].verification_result == VerificationResult.INSUFFICIENT
    assert verified.fact_ledger[0].verification_state == VerificationResult.INSUFFICIENT


# 16. Provider instance reused across batches
def test_batching_provider_instance_reused_across_batches():
    provider = MockBatchLLMProvider(default_result="SUPPORTS", default_confidence=0.95)
    verifier = EvidenceVerifier(provider=provider)
    envelope = _make_test_envelope(num_facts=32)  # 3 batches

    verified = verifier.verify_envelope(envelope)
    # The exact same provider was called 3 times
    assert provider.call_count == 3
    assert verifier._provider is provider


# 17. Groq 429 opens circuit breaker
def test_batching_groq_429_opens_circuit_breaker():
    provider = FailingAfterFirstBatchProvider()
    verifier = EvidenceVerifier(provider=provider)
    envelope = _make_test_envelope(num_facts=32)  # 3 batches

    verified = verifier.verify_envelope(envelope)
    # On batch 2, 429 was raised, setting _rate_limited_until
    assert provider._rate_limited_until > time.time()
    assert not provider.is_healthy()


# 18. Later batches do NOT make additional Groq calls after breaker opens
def test_batching_later_batches_do_not_call_groq_after_breaker_opens():
    provider = FailingAfterFirstBatchProvider()
    verifier = EvidenceVerifier(provider=provider)
    envelope = _make_test_envelope(num_facts=45)  # 3 batches: Batch 1 (OK), Batch 2 (429), Batch 3 (Short-circuited)

    verified = verifier.verify_envelope(envelope)
    # Call count stopped at 2; batch 3 did NOT invoke generate_content
    assert provider.call_count == 2
    metrics = verified.metadata["verification_metrics"]
    assert metrics["short_circuited_batches"] == 1


# 19. Unresolved batches become INSUFFICIENT
def test_batching_unresolved_batches_become_insufficient():
    provider = FailingAfterFirstBatchProvider()
    verifier = EvidenceVerifier(provider=provider)
    envelope = _make_test_envelope(num_facts=32)  # 3 batches

    verified = verifier.verify_envelope(envelope)
    # Batch 1 facts have SUPPORTS
    assert verified.fact_ledger[0].evidence[0].verification_result == VerificationResult.SUPPORTS
    # Batch 2 and 3 facts have INSUFFICIENT
    assert verified.fact_ledger[20].evidence[0].verification_result == VerificationResult.INSUFFICIENT
    assert verified.fact_ledger[30].evidence[0].verification_result == VerificationResult.INSUFFICIENT


# 20. Step 6 receives valid per-fact verification results
def test_batching_step6_receives_valid_per_fact_verification_results():
    from app.services.consistency_validator import ConsistencyValidator
    from app.schemas.validation_schema import ValidationGatingStatus
    provider = MockBatchLLMProvider(default_result="SUPPORTS", default_confidence=0.95)
    verifier = EvidenceVerifier(provider=provider)
    envelope = _make_test_envelope(num_facts=5)

    verified = verifier.verify_envelope(envelope)
    validator = ConsistencyValidator()
    report = validator.validate_envelope(verified)
    assert report.passed is True
    assert report.gating_status in (ValidationGatingStatus.READY_FOR_REVIEW, ValidationGatingStatus.REVIEW_WITH_WARNINGS)
    # Zero verification integrity errors
    verification_errors = [i for i in (report.errors + report.warnings) if i.code.startswith("VERIFICATION_")]
    assert len(verification_errors) == 0


# 21. No benchmark-specific logic in verifier
def test_batching_no_benchmark_specific_logic():
    import app.services.evidence_verifier as ev_mod
    src = open(ev_mod.__file__, "r", encoding="utf-8").read()
    assert "Cardioril" not in src
    assert "Pt M.K." not in src
    assert "cioms_form_MK_Cardioril" not in src


# 22. Arbitrary synthetic case works cleanly
def test_batching_arbitrary_synthetic_case_works():
    provider = MockBatchLLMProvider(default_result="SUPPORTS", default_confidence=0.92)
    verifier = EvidenceVerifier(provider=provider)

    fact = Fact(
        fact_id="fact-novel-001",
        field="adverse_event",
        value="Acute Myoclonus",
        status=FactStatus.CONFIRMED,
        evidence=[
            Evidence(
                source_id="novel_report.pdf",
                source_type=EvidenceType.PDF_TEXT,
                page_or_location="Page 1",
                verbatim_snippet="Patient experienced acute myoclonus following administration of Neurobexil."
            )
        ]
    )

    envelope = CaseEnvelope(
        envelope_id="env-synthetic-novel",
        message_id="msg-novel-99",
        source_filename="novel_report.pdf",
        language_detected="English",
        triage=TriageResult(
            is_multi_label=False,
            primary_category=CategoryEnum.SAFETY_REPORT_ICSR,
            labels=[],
            executive_summary="Novel drug case."
        ),
        document_summary="Novel report summary.",
        reviewer_summary="Novel brief.",
        fact_ledger=[fact]
    )

    verified = verifier.verify_envelope(envelope)
    assert verified.fact_ledger[0].verification_state == VerificationResult.SUPPORTS
    assert verified.metadata["verification_metrics"]["number_of_verification_batches"] == 1
