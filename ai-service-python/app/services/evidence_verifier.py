import json
import time
import logging
from typing import List, Dict, Any, Optional, Tuple

from app.core.config import settings
from app.core.llm_provider import LLMProvider, get_llm_provider
from app.schemas.fact_contract import (
    Fact, Evidence, FactStatus, VerificationResult, EvidenceType
)
from app.schemas.case_envelope import CaseEnvelope

logger = logging.getLogger("smartinbox.verifier")

VERIFIER_SYSTEM_INSTRUCTION = """
You are a Principal Pharmacovigilance Regulatory Evidence Verification Specialist and Medical Safety Officer.
Your objective is to evaluate whether a candidate source evidence snippet from an incoming clinical communication establishes, contradicts, or is insufficient to support an extracted clinical Fact.

DEFINITIONS:
- 'SUPPORTS': The evidence snippet explicitly, unambiguously, and logically entails the Fact. The entity identity, clinical role, dosage association, and value must align directly.
- 'CONTRADICTS': The evidence snippet explicitly conflicts with or negates the Fact (e.g. Fact asserts adverse event occurred, but evidence states 'No signs of adverse event'; or Fact asserts patient age is 71, but evidence states age is 63).
- 'INSUFFICIENT': The evidence snippet is topically related, mentions similar terminology, or provides general background, but does NOT sufficiently establish the exact Fact value and role.

CRITICAL CLINICAL ENTAILMENT RULES:
1. POLARITY & NEGATION: If the evidence denies, negates, or documents the explicit absence of a condition or defect (e.g. 'no adverse event', 'no defect observed', 'denies fever', 'without reaction'), it CONTRADICTS any claim asserting the event or defect occurred.
2. PRODUCT vs RESCUE MEDICATION: Strictly distinguish the suspect medicinal product from acute emergency rescue treatments (e.g. Epinephrine, vasopressors, antihistamines, corticosteroids, IV fluids) administered for resuscitation. A rescue medication dose or route does NOT support the suspect product dose.
3. REPORTER ATTRIBUTION: Distinguish the author/sender of the communication from healthcare providers merely mentioned inside the narrative.
4. TEMPORAL BOUNDARIES: Distinguish treatment start date, treatment stop date, and reaction onset date. A date mentioned for adverse reaction onset does NOT support a treatment start date.
5. VAGUENESS vs EXACT NUMERIC VALUES: Descriptive background (e.g. 'elderly patient') is INSUFFICIENT to establish an exact numeric age (e.g. '71 years old').
6. MULTILINGUAL EQUIVALENCE: For non-English snippets (e.g. Spanish, German, French), if the clinical meaning translates directly to the standardized English regulatory fact, it SUPPORTS the fact. Never alter or translate the original snippet text.
7. NOT STATED FACTS: A fact whose status is NOT_STATED or whose value is 'Not stated' can NEVER receive SUPPORTS.

Return ONLY a valid JSON object matching this schema:
{
  "verification_result": "SUPPORTS" | "CONTRADICTS" | "INSUFFICIENT",
  "confidence": float between 0.0 and 1.0,
  "rationale": "Concise 1 to 2 sentence clinical explanation for the determination"
}
"""


# ============================================================================
# 1. MECHANICAL & INTEGRITY GUARDS (NON-SEMANTIC)
# ============================================================================

class VerificationIntegrityGuard:
    """
    Mechanical and structural integrity validator for evidence verification.
    Strictly handles input validity, unstated boundaries, and data integrity.
    Performs NO semantic reasoning or clinical interpretation.
    """

    @staticmethod
    def is_not_stated(fact: Fact) -> bool:
        """Determines if a fact represents an explicitly unstated field."""
        if fact.status == FactStatus.NOT_STATED:
            return True
        val_str = str(fact.value).strip().lower() if fact.value is not None else ""
        return val_str in ["not stated", "unknown", "none", "n/a", ""]

    @staticmethod
    def is_empty_candidate(candidate: Evidence) -> bool:
        """Determines if candidate evidence lacks usable text content."""
        if not candidate or not candidate.verbatim_snippet:
            return True
        return not candidate.verbatim_snippet.strip()


# ============================================================================
# 2. EVIDENCE VERIFIER SERVICE (LLM #2 - GROQ DRIVEN)
# ============================================================================

class EvidenceVerifier:
    """
    Semantic Evidence Verification service for Step 5.
    Uses Groq (LLM #2, openai/gpt-oss-20b) to determine whether retrieved candidate
    Evidence objects logically and clinically SUPPORT, CONTRADICT, or are INSUFFICIENT
    to establish an extracted Fact.
    """

    def __init__(self, provider: Optional[LLMProvider] = None):
        self._provider = provider

    def _get_provider(self) -> Optional[LLMProvider]:
        if self._provider is not None:
            return self._provider
        try:
            return get_llm_provider("groq")
        except Exception as e:
            logger.warning(f"Could not initialize Groq LLM provider: {e}")
            return None

    def verify_candidate(
        self,
        fact: Fact,
        candidate: Evidence,
        document_context: Optional[str] = None
    ) -> Evidence:
        """
        Verifies a single candidate Evidence item against a Fact using the verifier model (Groq).
        Updates candidate.verification_result, verification_confidence, verification_rationale,
        and verification_metadata in place, preserving retrieval scores and location.
        """
        # Guard 1: NOT_STATED facts immediately resolve to INSUFFICIENT
        if VerificationIntegrityGuard.is_not_stated(fact):
            candidate.verification_result = VerificationResult.INSUFFICIENT
            candidate.verification_confidence = 0.0
            candidate.verification_rationale = "Fact is unstated in source; candidate evidence cannot support an absent value."
            candidate.verification_metadata = {
                "verifier_method": "integrity_guard",
                "rule": "not_stated_guard",
                "timestamp": int(time.time())
            }
            return candidate

        # Guard 2: Missing or empty verbatim snippet
        if VerificationIntegrityGuard.is_empty_candidate(candidate):
            candidate.verification_result = VerificationResult.INSUFFICIENT
            candidate.verification_confidence = 0.0
            candidate.verification_rationale = "Candidate evidence verbatim snippet is empty or missing."
            candidate.verification_metadata = {
                "verifier_method": "integrity_guard",
                "rule": "empty_evidence_guard",
                "timestamp": int(time.time())
            }
            return candidate

        # Guard 3: Check configuration
        if not settings.ENABLE_SEMANTIC_VERIFICATION:
            candidate.verification_result = VerificationResult.INSUFFICIENT
            candidate.verification_confidence = 0.0
            candidate.verification_rationale = "Semantic evidence verification disabled by configuration."
            candidate.verification_metadata = {
                "verifier_method": "fallback",
                "reason": "disabled_by_config",
                "timestamp": int(time.time())
            }
            return candidate

        # Obtain Groq LLM verifier provider
        provider = self._get_provider()
        if not provider or not provider.is_healthy():
            candidate.verification_result = VerificationResult.INSUFFICIENT
            candidate.verification_confidence = 0.0
            candidate.verification_rationale = "Verification provider unavailable; defaulted safely to INSUFFICIENT."
            candidate.verification_metadata = {
                "verifier_method": "fallback",
                "reason": "provider_unavailable",
                "timestamp": int(time.time())
            }
            return candidate

        # LLM Semantic Entailment Verification (Groq openai/gpt-oss-20b)
        try:
            prompt_payload = {
                "fact": {
                    "field": fact.field,
                    "value": fact.value,
                    "normalized_value": fact.normalized_value,
                    "status": fact.status.value,
                },
                "candidate_evidence": {
                    "verbatim_snippet": candidate.verbatim_snippet,
                    "source_id": candidate.source_id,
                    "source_type": candidate.source_type.value if hasattr(candidate.source_type, "value") else str(candidate.source_type),
                    "page_or_location": candidate.page_or_location,
                },
                "context_hint": document_context[:600] if document_context else None
            }

            prompt_text = (
                f"Assess clinical entailment between the Fact and the candidate Evidence snippet:\n\n"
                f"{json.dumps(prompt_payload, indent=2)}\n\n"
                f"Determine whether the evidence SUPPORTS, CONTRADICTS, or is INSUFFICIENT. "
                f"Return JSON."
            )

            t0 = time.time()
            raw_resp = provider.generate_content(
                contents=prompt_text,
                system_instruction=VERIFIER_SYSTEM_INSTRUCTION,
                temperature=0.0
            )
            latency_ms = int((time.time() - t0) * 1000)

            clean_json = raw_resp.strip()
            if clean_json.startswith("```"):
                lines = clean_json.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                clean_json = "\n".join(lines).strip()

            parsed = json.loads(clean_json)
            res_str = str(parsed.get("verification_result", "INSUFFICIENT")).strip().upper()

            if res_str == "SUPPORTS":
                candidate.verification_result = VerificationResult.SUPPORTS
            elif res_str == "CONTRADICTS":
                candidate.verification_result = VerificationResult.CONTRADICTS
            else:
                candidate.verification_result = VerificationResult.INSUFFICIENT

            raw_conf = float(parsed.get("confidence", 0.0))
            candidate.verification_confidence = max(0.0, min(1.0, raw_conf))
            candidate.verification_rationale = str(parsed.get("rationale", "LLM semantic entailment verification."))
            candidate.verification_metadata = {
                "verifier_method": "llm_semantic_nli",
                "provider": provider.provider_name,
                "model": getattr(provider, "_default_model", settings.GROQ_VERIFIER_MODEL),
                "latency_ms": latency_ms,
                "timestamp": int(time.time())
            }

        except Exception as e:
            logger.warning(f"Groq semantic verification failed: {e}. Falling back safely to INSUFFICIENT.")
            candidate.verification_result = VerificationResult.INSUFFICIENT
            candidate.verification_confidence = 0.0
            candidate.verification_rationale = f"Semantic verification fallback due to provider failure: {str(e)[:80]}"
            candidate.verification_metadata = {
                "verifier_method": "fallback",
                "error": str(e),
                "timestamp": int(time.time())
            }

        return candidate

    def verify_fact(
        self,
        fact: Fact,
        document_context: Optional[str] = None
    ) -> Fact:
        """
        Verifies all candidate evidence items attached to a Fact.
        Preserves individual candidate results and synthesizes overall fact.verification_state.
        """
        if VerificationIntegrityGuard.is_not_stated(fact):
            fact.verification_state = VerificationResult.INSUFFICIENT
            for cand in fact.evidence:
                self.verify_candidate(fact, cand, document_context=document_context)
            return fact

        if not fact.evidence:
            fact.verification_state = VerificationResult.INSUFFICIENT
            return fact

        has_support = False
        has_contradict = False

        for cand in fact.evidence:
            self.verify_candidate(fact, cand, document_context=document_context)
            if cand.verification_result == VerificationResult.SUPPORTS:
                has_support = True
            elif cand.verification_result == VerificationResult.CONTRADICTS:
                has_contradict = True

        if has_contradict:
            fact.verification_state = VerificationResult.CONTRADICTS
        elif has_support:
            fact.verification_state = VerificationResult.SUPPORTS
        else:
            fact.verification_state = VerificationResult.INSUFFICIENT

        return fact

    def verify_envelope(
        self,
        envelope: CaseEnvelope,
        document_context: Optional[str] = None
    ) -> CaseEnvelope:
        """
        Executes semantic evidence verification across all facts in a CaseEnvelope:
        - Top-level atomic fact_ledger
        - ICSR patient, reporter, product facts
        - PQC complaint facts
        - MI inquiry facts
        - Not Relevant facts
        """
        start_time = time.time()
        context = document_context or envelope.document_summary or ""

        # 1. Verify top-level Fact ledger
        facts_list = getattr(envelope, "fact_ledger", None) or getattr(envelope, "facts", [])
        for f in facts_list:
            self.verify_fact(f, document_context=context)

        # 2. Verify sub-payload facts
        if envelope.icsr:
            if hasattr(envelope.icsr, "facts"):
                for f in envelope.icsr.facts:
                    self.verify_fact(f, document_context=context)
            if hasattr(envelope.icsr, "patient") and hasattr(envelope.icsr.patient, "facts"):
                for f in envelope.icsr.patient.facts:
                    self.verify_fact(f, document_context=context)
            if hasattr(envelope.icsr, "reporter") and hasattr(envelope.icsr.reporter, "facts"):
                for f in envelope.icsr.reporter.facts:
                    self.verify_fact(f, document_context=context)
            if hasattr(envelope.icsr, "product") and hasattr(envelope.icsr.product, "facts"):
                for f in envelope.icsr.product.facts:
                    self.verify_fact(f, document_context=context)

        pqc_payload = getattr(envelope, "pqc", None) or getattr(envelope, "quality_complaint", None)
        if pqc_payload and hasattr(pqc_payload, "facts"):
            for f in pqc_payload.facts:
                self.verify_fact(f, document_context=context)

        mi_payload = getattr(envelope, "mi", None) or getattr(envelope, "medical_info", None)
        if mi_payload and hasattr(mi_payload, "facts"):
            for f in mi_payload.facts:
                self.verify_fact(f, document_context=context)

        nr_payload = getattr(envelope, "not_relevant", None)
        if nr_payload and hasattr(nr_payload, "facts"):
            for f in nr_payload.facts:
                self.verify_fact(f, document_context=context)

        verification_latency = int((time.time() - start_time) * 1000)
        envelope.metadata["verification_latency_ms"] = verification_latency
        logger.info(f"Verified CaseEnvelope {envelope.envelope_id} via Groq in {verification_latency}ms.")

        return envelope

evidence_verifier = EvidenceVerifier()
