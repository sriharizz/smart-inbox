import re
import json
import time
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

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
6. MULTILINGUAL EQUIVALENCE: For non-English snippets (e.g. Spanish 'Necrólisis Epidérmica Tóxica'), if the clinical meaning translates directly to the standardized English fact ('Toxic Epidermal Necrolysis'), it SUPPORTS the fact. Never alter the original snippet text.
7. NOT STATED FACTS: A fact whose status is NOT_STATED or whose value is 'Not stated' can NEVER receive SUPPORTS.

Return ONLY a valid JSON object matching this schema:
{
  "verification_result": "SUPPORTS" | "CONTRADICTS" | "INSUFFICIENT",
  "confidence": float between 0.0 and 1.0,
  "rationale": "Concise 1 to 2 sentence clinical explanation for the determination"
}
"""


# ============================================================================
# 1. DETERMINISTIC CLINICAL VERIFICATION RULE ENGINE
# ============================================================================

class DeterministicClinicalVerifier:
    """
    Deterministic clinical NLI rule engine for fast-path evaluation, offline testing,
    and safe fallback when LLM providers are unavailable or rate-limited.
    """

    RESCUE_MEDS = {
        "epinephrine", "adrenaline", "vasopressin", "norepinephrine",
        "methylprednisolone", "diphenhydramine", "hydrocortisone",
        "dexamethasone", "albuterol", "salbutamol", "resuscitation", "rescue"
    }

    MULTILINGUAL_MAP = {
        "necrólisis epidérmica tóxica": "toxic epidermal necrolysis",
        "necrolisis epidermica toxica": "toxic epidermal necrolysis",
        "retirada definitiva": "drug withdrawn",
        "angioödem des rachens": "angioedema",
        "angioodem des rachens": "angioedema",
        "partículas flotantes": "particulate matter",
        "particulas flotantes": "particulate matter",
    }

    @staticmethod
    def verify(fact: Fact, candidate: Evidence) -> Tuple[VerificationResult, float, str]:
        """
        Applies deterministic clinical entailment rules to determine SUPPORTS, CONTRADICTS,
        or INSUFFICIENT.
        """
        val_str = str(fact.value).strip().lower()
        snippet = candidate.verbatim_snippet.strip().lower()
        field_name = fact.field.lower()

        # -------------------------------------------------------------
        # Rule 1: NOT_STATED Facts
        # -------------------------------------------------------------
        if fact.status == FactStatus.NOT_STATED or val_str in ["not stated", "unknown", "none", "n/a"]:
            return (
                VerificationResult.INSUFFICIENT,
                1.0,
                "Fact is unstated in source; candidate evidence cannot support an absent value."
            )

        # -------------------------------------------------------------
        # Rule 2: Explicit Negation & Polarity Reversal
        # -------------------------------------------------------------
        negation_patterns = [
            r"\b(?:no|not|denies|denied|without|negative for|absence of|zero|never)\s+([a-z\s]{0,30})",
            r"\b(?:no|not)\s+(?:signs|symptoms|evidence|history)\s+of\s+([a-z\s]{0,30})",
            r"\b(?:no|neither)\s+(?:adverse\s+event|defect|complaint)",
        ]
        has_negation = False
        for pat in negation_patterns:
            m = re.search(pat, snippet)
            if m:
                # If negation targets the fact entity
                negated_target = m.group(0)
                if any(token in negated_target for token in val_str.split() if len(token) > 3):
                    return (
                        VerificationResult.CONTRADICTS,
                        0.95,
                        f"Evidence explicitly negates or denies the reported entity ('{negated_target.strip()}')."
                    )
                if any(phrase in negated_target for phrase in ["no adverse event", "no defect", "no product defect", "no complaint"]):
                    if "reaction" in field_name or "event" in field_name or "defect" in field_name or "complaint" in field_name:
                        return (
                            VerificationResult.CONTRADICTS,
                            0.95,
                            f"Evidence explicitly confirms absence of event or defect ('{negated_target.strip()}')."
                        )
                has_negation = True

        # -------------------------------------------------------------
        # Rule 3: Rescue / Concomitant Medication Segregation
        # -------------------------------------------------------------
        if any(term in field_name for term in ["product", "dose", "drug", "medication"]):
            is_rescue_snippet = any(rm in snippet for rm in DeterministicClinicalVerifier.RESCUE_MEDS)
            # If fact is about suspect product (and suspect product is NOT epinephrine itself)
            if is_rescue_snippet and "epinephrine" not in val_str and "adrenaline" not in val_str:
                return (
                    VerificationResult.INSUFFICIENT,
                    0.90,
                    "Evidence snippet refers to emergency rescue intervention or resuscitation drug, not the suspect product."
                )

        # -------------------------------------------------------------
        # Rule 4: Patient Age Discrepancy or Vagueness
        # -------------------------------------------------------------
        if "age" in field_name:
            # Check for conflicting numeric age in snippet
            numeric_ages = re.findall(r"\b(\d{1,3})\s*(?:-|year|yr|yo|ans|jahre)", snippet)
            if not numeric_ages:
                numeric_ages = re.findall(r"\bage\b(?:\s+(?:was|is|of))?\s*(\d{1,3})\b", snippet)
            if not numeric_ages:
                numeric_ages = re.findall(r"\b(\d{1,3})\b", snippet)
            
            fact_age_match = re.search(r"\b(\d{1,3})\b", val_str)
            fact_age = fact_age_match.group(1) if fact_age_match else None

            if fact_age and numeric_ages:
                found_age = numeric_ages[0]
                if found_age == fact_age:
                    return (
                        VerificationResult.SUPPORTS,
                        0.95,
                        f"Evidence explicitly confirms patient age ({found_age})."
                    )
                else:
                    return (
                        VerificationResult.CONTRADICTS,
                        0.95,
                        f"Explicit numeric conflict: evidence states age {found_age}, contradicting asserted age {fact_age}."
                    )
            
            # Descriptive vagueness without numeric value
            if any(vague in snippet for vague in ["elderly", "senior", "adult", "middle-aged", "infant"]):
                if fact_age:
                    return (
                        VerificationResult.INSUFFICIENT,
                        0.85,
                        "Evidence provides general descriptive background ('elderly') but is insufficient to establish exact numeric age."
                    )

        # -------------------------------------------------------------
        # Rule 5: Reporter Attribution Distinction
        # -------------------------------------------------------------
        if "reporter" in field_name:
            indirect_mentions = [
                "physician mentioned", "doctor mentioned", "spoke with my doctor",
                "consulted dr", "attending was dr", "referred by dr"
            ]
            if any(im in snippet for im in indirect_mentions) and not any(dir_h in snippet for dir_h in ["from:", "reporter:", "submitted by"]):
                return (
                    VerificationResult.INSUFFICIENT,
                    0.85,
                    "Evidence mentions a healthcare provider inside narrative context, but does not establish them as the primary reporter."
                )

        # -------------------------------------------------------------
        # Rule 6: Temporal / Date Role Distinction
        # -------------------------------------------------------------
        if "start_date" in field_name or "treatment_start" in field_name:
            reaction_onset_terms = ["reaction onset", "onset date", "symptoms began", "symptoms started", "developed symptoms"]
            if any(rot in snippet for rot in reaction_onset_terms) and not any(st in snippet for st in ["started therapy", "initiated", "treatment start"]):
                return (
                    VerificationResult.INSUFFICIENT,
                    0.85,
                    "Evidence specifies date for adverse reaction onset, which does not establish treatment initiation start date."
                )

        # -------------------------------------------------------------
        # Rule 7: Multilingual Semantic Equivalence
        # -------------------------------------------------------------
        for foreign_phrase, eng_translation in DeterministicClinicalVerifier.MULTILINGUAL_MAP.items():
            if foreign_phrase in snippet:
                if eng_translation in val_str or val_str in eng_translation:
                    return (
                        VerificationResult.SUPPORTS,
                        0.95,
                        f"Original non-English source snippet ('{foreign_phrase}') semantically confirms the standardized regulatory fact."
                    )

        # -------------------------------------------------------------
        # Rule 8: Direct Lexical / Entailment Support
        # -------------------------------------------------------------
        # Clean exact containment without negation
        if not has_negation and val_str in snippet:
            return (
                VerificationResult.SUPPORTS,
                0.90,
                "Evidence snippet explicitly contains and clinically entails the extracted fact value."
            )

        # Normalized value check (e.g. integer 71 or normalized code)
        if fact.normalized_value is not None:
            norm_str = str(fact.normalized_value).lower()
            if not has_negation and norm_str in snippet:
                return (
                    VerificationResult.SUPPORTS,
                    0.88,
                    "Evidence snippet contains normalized entity value."
                )

        # -------------------------------------------------------------
        # Fallback: Topically related or ambiguous
        # -------------------------------------------------------------
        return (
            VerificationResult.INSUFFICIENT,
            0.50,
            "Evidence passage is topically related or ambiguous; insufficient explicit confirmation to verify the fact."
        )


# ============================================================================
# 2. EVIDENCE VERIFIER SERVICE
# ============================================================================

class EvidenceVerifier:
    """
    Semantic Evidence Verification service for Step 5.
    Determines whether retrieved candidate Evidence objects logically and clinically
    SUPPORT, CONTRADICT, or are INSUFFICIENT to establish an extracted Fact.
    """

    def __init__(self, provider: Optional[LLMProvider] = None, use_llm: Optional[bool] = None):
        self._provider = provider
        self._use_llm = use_llm

    def _get_provider(self) -> Optional[LLMProvider]:
        if self._provider is not None:
            return self._provider
        try:
            return get_llm_provider()
        except Exception:
            return None

    def verify_candidate(
        self,
        fact: Fact,
        candidate: Evidence,
        document_context: Optional[str] = None
    ) -> Evidence:
        """
        Verifies a single candidate Evidence item against a Fact.
        Updates candidate.verification_result, verification_confidence, verification_rationale,
        and verification_metadata in place, preserving retrieval scores and location.
        """
        # Fast-path: NOT_STATED facts immediately resolve to INSUFFICIENT
        if fact.status == FactStatus.NOT_STATED or str(fact.value).strip().lower() in ["not stated", "unknown", "none", "n/a"]:
            candidate.verification_result = VerificationResult.INSUFFICIENT
            candidate.verification_confidence = 1.0
            candidate.verification_rationale = "Fact is unstated in source; candidate evidence cannot support an absent value."
            candidate.verification_metadata = {
                "verifier_method": "deterministic_rule",
                "rule": "not_stated_guard",
                "timestamp": int(time.time())
            }
            return candidate

        # Check if LLM verification is enabled and provider is available
        provider = self._get_provider()
        if self._use_llm is not None:
            use_llm = self._use_llm and provider is not None
        else:
            use_llm = (
                settings.ENABLE_SEMANTIC_VERIFICATION
                and provider is not None
                and bool(settings.GEMINI_API_KEY)
            )

        # 1. Deterministic Rule Assessment (always executed as baseline / fast-path)
        det_result, det_conf, det_rationale = DeterministicClinicalVerifier.verify(fact, candidate)

        # Fast-path: If LLM is disabled, OR if using default provider and deterministic rules
        # already establish high confidence (>= 0.90), return deterministic determination immediately.
        if not use_llm or (self._provider is None and det_conf >= 0.90):
            candidate.verification_result = det_result
            candidate.verification_confidence = det_conf
            candidate.verification_rationale = det_rationale
            candidate.verification_metadata = {
                "verifier_method": "deterministic_clinical_rules",
                "timestamp": int(time.time())
            }
            return candidate

        # 2. LLM Semantic Entailment Verification
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
                "context_hint": document_context[:1000] if document_context else None
            }

            prompt_text = (
                f"Assess clinical entailment between the Fact and the candidate Evidence snippet:\n\n"
                f"{json.dumps(prompt_payload, indent=2)}\n\n"
                f"Determine whether the evidence SUPPORTS, CONTRADICTS, or is INSUFFICIENT. "
                f"Return JSON."
            )

            raw_resp = provider.generate_content(
                contents=prompt_text,
                system_instruction=VERIFIER_SYSTEM_INSTRUCTION,
                temperature=0.0
            )

            clean_json = raw_resp.strip()
            if clean_json.startswith("```"):
                lines = clean_json.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                clean_json = "\n".join(lines).strip()

            parsed = json.loads(clean_json)
            res_str = str(parsed.get("verification_result", "INSUFFICIENT")).upper()
            
            # Map to VerificationResult enum safely
            if res_str == "SUPPORTS":
                candidate.verification_result = VerificationResult.SUPPORTS
            elif res_str == "CONTRADICTS":
                candidate.verification_result = VerificationResult.CONTRADICTS
            else:
                candidate.verification_result = VerificationResult.INSUFFICIENT

            candidate.verification_confidence = float(parsed.get("confidence", 0.90))
            candidate.verification_rationale = str(parsed.get("rationale", "LLM semantic entailment verification."))
            candidate.verification_metadata = {
                "verifier_method": "llm_semantic_nli",
                "model": getattr(provider, "provider_name", "gemini"),
                "timestamp": int(time.time())
            }

        except Exception as e:
            logger.warning(f"LLM verification failed: {e}. Falling back safely to deterministic clinical rules.")
            candidate.verification_result = det_result
            candidate.verification_confidence = det_conf
            candidate.verification_rationale = f"{det_rationale} (Fallback: {str(e)[:50]})"
            candidate.verification_metadata = {
                "verifier_method": "deterministic_fallback",
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
        # Guard: NOT_STATED facts can never be supported
        if fact.status == FactStatus.NOT_STATED or str(fact.value).strip().lower() in ["not stated", "unknown", "none", "n/a"]:
            fact.verification_state = VerificationResult.INSUFFICIENT
            for cand in fact.evidence:
                self.verify_candidate(fact, cand, document_context=document_context)
            return fact

        if not fact.evidence:
            fact.verification_state = VerificationResult.INSUFFICIENT
            return fact

        # Verify each candidate individually
        has_support = False
        has_contradict = False

        for cand in fact.evidence:
            self.verify_candidate(fact, cand, document_context=document_context)
            if cand.verification_result == VerificationResult.SUPPORTS:
                has_support = True
            elif cand.verification_result == VerificationResult.CONTRADICTS:
                has_contradict = True

        # Synthesize overall verification state
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

        # Extract local document text for context if not provided
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
        logger.info(f"Verified CaseEnvelope {envelope.envelope_id} in {verification_latency}ms.")

        return envelope

evidence_verifier = EvidenceVerifier()
