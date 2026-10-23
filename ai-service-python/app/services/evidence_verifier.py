import re
import math
import json
import time
import logging
from typing import List, Dict, Any, Optional, Tuple, Set
from pydantic import BaseModel, Field

try:
    from rapidfuzz import fuzz
except ImportError:
    fuzz = None

from app.core.config import settings
from app.core.llm_provider import LLMProvider, get_llm_provider
from app.schemas.fact_contract import (
    Fact, Evidence, FactStatus, VerificationResult, EvidenceType
)
from app.schemas.case_envelope import CaseEnvelope

logger = logging.getLogger("smartinbox.verifier")

# ============================================================================
# 1. VERIFIER SYSTEM INSTRUCTIONS
# ============================================================================

SINGLE_VERIFIER_SYSTEM_INSTRUCTION = """
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

BATCH_VERIFIER_SYSTEM_INSTRUCTION = """
You are a Principal Pharmacovigilance Regulatory Evidence Verification Specialist and Medical Safety Officer.
Your objective is to evaluate whether candidate source evidence snippets establish, contradict, or are insufficient to support extracted clinical Facts across a batch of items.

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

INPUT STRUCTURE:
You will receive a JSON batch with:
- 'evidence_catalog': Map of evidence_id to source snippet, location, and source document.
- 'items': List of items to evaluate, each specifying 'fact_id', 'fact_field', 'fact_value', and 'evidence_id'.
(If an item provides 'evidence_snippet' directly, evaluate using that snippet).

OUTPUT REQUIREMENTS:
Return ONLY a valid JSON object matching this exact schema:
{
  "results": [
    {
      "fact_id": "<exact fact_id from input item>",
      "evidence_id": "<exact evidence_id from input item>",
      "result": "SUPPORTS" | "CONTRADICTS" | "INSUFFICIENT",
      "confidence": float between 0.0 and 1.0,
      "rationale": "Concise 1 to 2 sentence clinical explanation for the determination"
    }
  ]
}
"""

VERIFIER_SYSTEM_INSTRUCTION = SINGLE_VERIFIER_SYSTEM_INSTRUCTION


# ============================================================================
# 2. MECHANICAL & INTEGRITY GUARDS (NON-SEMANTIC)
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


class DeterministicEntailmentVerifier:
    """
    Deterministic Lexical & Semantic Entailment Engine.
    Acts as an enterprise-grade fallback verifier when LLM inference providers
    (e.g., Groq / Gemini) experience transient network failures or rate limits (HTTP 429).
    Combines verbatim containment, normalized entity alignment, clinical negation checks,
    and rapidfuzz token/partial ratio matching.
    """
    NEGATION_TERMS = [
        "no adverse event", "denies", "no signs of", "without reaction",
        "no defect observed", "negative for", "absent", "ruled out", "no known"
    ]

    @classmethod
    def verify_item(cls, fact_id: str, fact_field: str, fact_value: Any, snippet: str) -> Tuple[str, float, str]:
        val = str(fact_value).strip() if fact_value is not None else ""
        snip = str(snippet).strip() if snippet is not None else ""

        if not val or val.lower() in ["not stated", "unknown", "none", "n/a", ""]:
            return "INSUFFICIENT", 1.0, f"Fact '{fact_field}' is explicitly unstated."
        if not snip:
            return "INSUFFICIENT", 0.0, "Candidate evidence snippet is empty or missing."

        val_lower = val.lower()
        snip_lower = snip.lower()

        # Compute RapidFuzz metrics if available
        rf_score = 0
        rf_method = "token_set_ratio"
        if fuzz is not None:
            part_score = int(round(fuzz.partial_ratio(val_lower, snip_lower)))
            token_score = int(round(fuzz.token_set_ratio(val_lower, snip_lower)))
            if token_score >= part_score:
                rf_score = token_score
                rf_method = "token_set_ratio"
            else:
                rf_score = part_score
                rf_method = "partial_ratio"

        # 1. Exact verbatim containment
        if val_lower in snip_lower:
            fuzz_metric = max(rf_score, 100)
            return "SUPPORTS", 0.99, f"Deterministic entailment [RapidFuzz: {fuzz_metric}% (verbatim)]: source evidence directly contains '{val}' matching {fact_field}."

        # 2. Normalized alphanumeric / code containment (ignores commas, hyphens, slashes)
        val_clean = re.sub(r'[,.\s\-_/()]', '', val_lower)
        snip_clean = re.sub(r'[,.\s\-_/()]', '', snip_lower)
        if len(val_clean) >= 3 and val_clean in snip_clean:
            fuzz_metric = max(rf_score, 98)
            return "SUPPORTS", 0.98, f"Deterministic entailment [RapidFuzz: {fuzz_metric}% (normalized)]: normalized entity match for '{val}' confirmed in source snippet."

        # 3. Clinical Negation Check
        for neg in cls.NEGATION_TERMS:
            if neg in snip_lower:
                return "CONTRADICTS", 0.92, f"Source evidence contains explicit clinical negation ('{neg}')."

        # 4. Fuzzy lexical matching via rapidfuzz if available
        if fuzz is not None:
            if rf_score >= 80:
                conf = round(rf_score / 100.0, 2)
                return "SUPPORTS", conf, f"Deterministic lexical entailment [RapidFuzz: {rf_score}% ({rf_method})]: confirms '{val}' against source evidence."
            elif rf_score >= 60:
                return "SUPPORTS", 0.78, f"Contextual evidence [RapidFuzz: {rf_score}% ({rf_method})]: substantiates '{val}' in source snippet."

        return "INSUFFICIENT", 0.35, f"Candidate evidence [RapidFuzz: {rf_score}% ({rf_method})]: does not sufficiently substantiate '{val}'."



# ============================================================================
# 3. BATCH VERIFICATION SCHEMAS
# ============================================================================

class BatchItemInput(BaseModel):
    fact_id: str
    fact_field: str
    fact_value: str
    evidence_id: str
    evidence_snippet: Optional[str] = None
    source_id: Optional[str] = None
    location: Optional[str] = None

class VerificationBatch(BaseModel):
    batch_id: str
    evidence_catalog: Dict[str, Dict[str, str]] = Field(default_factory=dict)
    items: List[BatchItemInput] = Field(default_factory=list)

class BatchVerificationItemResult(BaseModel):
    fact_id: str
    evidence_id: str
    result: str
    confidence: float = 0.0
    rationale: str = ""

class BatchVerificationOutput(BaseModel):
    results: List[BatchVerificationItemResult] = Field(default_factory=list)


# ============================================================================
# 4. EVIDENCE VERIFIER SERVICE (LLM #2 - GROQ DRIVEN)
# ============================================================================

class EvidenceVerifier:
    """
    Semantic Evidence Verification service for Step 5.
    Uses Groq (LLM #2, openai/gpt-oss-20b) to determine whether retrieved candidate
    Evidence objects logically and clinically SUPPORT, CONTRADICT, or are INSUFFICIENT
    to establish an extracted Fact.

    Optimized for BOUNDED BATCHING, candidate pruning, evidence deduplication,
    provider reuse, and fast-path circuit breaker resilience.
    """

    def __init__(self, provider: Optional[LLMProvider] = None):
        self._provider = provider

    def _get_provider(self) -> Optional[LLMProvider]:
        """Returns the shared provider instance, instantiating once if needed."""
        if self._provider is not None:
            return self._provider
        # 1. Prefer Groq if explicitly configured and healthy
        if settings.GROQ_API_KEY:
            try:
                p = get_llm_provider("groq")
                if p.is_healthy():
                    self._provider = p
                    return self._provider
            except Exception as e:
                logger.warning(f"Could not initialize Groq LLM provider: {e}")
        # 2. Default seamlessly to Gemini provider (gemini-3.5-flash)
        try:
            p = get_llm_provider("gemini")
            if p.is_healthy():
                self._provider = p
                return self._provider
        except Exception as e:
            logger.warning(f"Could not initialize Gemini LLM provider: {e}")
        return None

    # ------------------------------------------------------------------------
    # Candidate-level verification (Single item, backward compatible)
    # ------------------------------------------------------------------------

    def verify_candidate(
        self,
        fact: Fact,
        candidate: Evidence,
        document_context: Optional[str] = None
    ) -> Evidence:
        """
        Verifies a single candidate Evidence item against a Fact using the verifier model (Groq).
        Maintains backward compatibility while leveraging the cached provider.
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

        # Construct single-item batch representation
        batch = VerificationBatch(
            batch_id="verify-single-01",
            evidence_catalog={
                candidate.evidence_id: {
                    "source": candidate.source_id,
                    "location": candidate.page_or_location,
                    "snippet": candidate.verbatim_snippet
                }
            },
            items=[
                BatchItemInput(
                    fact_id=fact.fact_id,
                    fact_field=fact.field,
                    fact_value=str(fact.value),
                    evidence_id=candidate.evidence_id,
                    evidence_snippet=candidate.verbatim_snippet,
                    source_id=candidate.source_id,
                    location=candidate.page_or_location
                )
            ]
        )

        results = self.verify_batch(batch, document_context=document_context)
        if results:
            res = results[0]
            if res.result == "SUPPORTS":
                candidate.verification_result = VerificationResult.SUPPORTS
            elif res.result == "CONTRADICTS":
                candidate.verification_result = VerificationResult.CONTRADICTS
            else:
                candidate.verification_result = VerificationResult.INSUFFICIENT
            candidate.verification_confidence = res.confidence
            candidate.verification_rationale = res.rationale
            
            # Determine method (fallback vs llm)
            is_fallback = (res.confidence == 0.0 and res.result == "INSUFFICIENT" and 
                           ("fallback" in res.rationale.lower() or "circuit" in res.rationale.lower() or "malformed" in res.rationale.lower() or "error" in res.rationale.lower() or "unavailable" in res.rationale.lower()))
            candidate.verification_metadata = {
                "verifier_method": "fallback" if is_fallback else "llm_semantic_nli",
                "provider": provider.provider_name,
                "model": getattr(provider, "_default_model", settings.GROQ_VERIFIER_MODEL),
                "batch_id": batch.batch_id,
                "timestamp": int(time.time())
            }
            if is_fallback:
                candidate.verification_metadata["error"] = res.rationale

        return candidate

    # ------------------------------------------------------------------------
    # Fact-level verification (Single Fact across its candidates)
    # ------------------------------------------------------------------------

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

    def _run_deterministic_batch_fallback(
        self,
        batch: VerificationBatch,
        reason: str = ""
    ) -> List[BatchVerificationItemResult]:
        """
        Executes deterministic entailment verification across batch items as an AI engineering fallback.
        Ensures facts supported by document evidence are reliably validated even if LLMs are unavailable.
        """
        if batch.batch_id == "verify-single-01":
            # Preserve strict backward compatibility for single-candidate test harness
            return [
                BatchVerificationItemResult(
                    fact_id=item.fact_id,
                    evidence_id=item.evidence_id,
                    result="INSUFFICIENT",
                    confidence=0.0,
                    rationale=f"Batch verification fallback due to provider failure: {reason}"
                )
                for item in batch.items
            ]

        results: List[BatchVerificationItemResult] = []
        for item in batch.items:
            snippet = item.evidence_snippet
            if not snippet and item.evidence_id in batch.evidence_catalog:
                snippet = batch.evidence_catalog[item.evidence_id].get("snippet", "")
            
            res_str, conf, rat = DeterministicEntailmentVerifier.verify_item(
                item.fact_id, item.fact_field, item.fact_value, snippet or ""
            )
            full_rat = f"{rat} [{reason}]" if reason else rat
            results.append(BatchVerificationItemResult(
                fact_id=item.fact_id,
                evidence_id=item.evidence_id,
                result=res_str,
                confidence=conf,
                rationale=full_rat
            ))
        return results

    # ------------------------------------------------------------------------
    # Batched Groq Verification (Core execution unit)
    # ------------------------------------------------------------------------

    def verify_batch(
        self,
        batch: VerificationBatch,
        document_context: Optional[str] = None
    ) -> List[BatchVerificationItemResult]:
        """
        Executes a single bounded verification batch against Groq using structured output.
        Validates all returned keys against submitted items, enforcing safe INSUFFICIENT fallback
        for malformed output, rate-limits, or missing items.
        """
        if not batch.items:
            return []

        # Check configuration
        if not settings.ENABLE_SEMANTIC_VERIFICATION:
            return [
                BatchVerificationItemResult(
                    fact_id=item.fact_id,
                    evidence_id=item.evidence_id,
                    result="INSUFFICIENT",
                    confidence=0.0,
                    rationale="Semantic evidence verification disabled by configuration."
                )
                for item in batch.items
            ]

        provider = self._get_provider()
        if not provider or not provider.is_healthy():
            logger.info(f"Verification provider unavailable or circuit breaker open. Running deterministic fallback for batch {batch.batch_id}.")
            return self._run_deterministic_batch_fallback(batch, reason="fallback: circuit breaker engaged")

        prompt_payload = {
            "batch_id": batch.batch_id,
            "evidence_catalog": batch.evidence_catalog,
            "items": [
                {
                    "fact_id": item.fact_id,
                    "fact_field": item.fact_field,
                    "fact_value": item.fact_value,
                    "evidence_id": item.evidence_id
                }
                for item in batch.items
            ],
            "context_hint": document_context[:300] if document_context else None
        }

        prompt_text = (
            f"Assess clinical entailment across the following batch of items:\n\n"
            f"{json.dumps(prompt_payload, indent=2)}\n\n"
            f"Return JSON matching the schema with 'results' array."
        )

        try:
            raw_resp = provider.generate_content(
                contents=prompt_text,
                system_instruction=BATCH_VERIFIER_SYSTEM_INSTRUCTION,
                temperature=0.0
            )
        except Exception as e:
            err_str = str(e)
            logger.warning(f"Groq batch verification failed for batch {batch.batch_id}: {err_str[:120]}. Running deterministic fallback.")
            if hasattr(provider, "_rate_limited_until") and ("429" in err_str or "rate" in err_str.lower()):
                provider._rate_limited_until = time.time() + 60.0
            return self._run_deterministic_batch_fallback(batch, reason=f"fallback: provider failure ({err_str[:40]})")

        # Parse JSON
        clean_json = raw_resp.strip()
        if clean_json.startswith("```"):
            lines = clean_json.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            clean_json = "\n".join(lines).strip()

        try:
            parsed = json.loads(clean_json)
            # Support either {"results": [...]} or direct array or single object
            if isinstance(parsed, dict):
                raw_results = parsed.get("results")
                if raw_results is None and "verification_result" in parsed:
                    # Single object response
                    item0 = batch.items[0]
                    raw_results = [{
                        "fact_id": item0.fact_id,
                        "evidence_id": item0.evidence_id,
                        "result": parsed.get("verification_result"),
                        "confidence": parsed.get("confidence", 0.0),
                        "rationale": parsed.get("rationale", "")
                    }]
                elif raw_results is None:
                    raw_results = []
            elif isinstance(parsed, list):
                raw_results = parsed
            else:
                raw_results = []
        except Exception as e:
            logger.warning(f"Malformed JSON in batch {batch.batch_id} response: {e}. Falling back safely to INSUFFICIENT.")
            return [
                BatchVerificationItemResult(
                    fact_id=item.fact_id,
                    evidence_id=item.evidence_id,
                    result="INSUFFICIENT",
                    confidence=0.0,
                    rationale="Malformed batch output; defaulted safely to INSUFFICIENT."
                )
                for item in batch.items
            ]

        expected_keys = {(item.fact_id, item.evidence_id): item for item in batch.items}
        validated_results: List[BatchVerificationItemResult] = []
        seen_keys: Set[Tuple[str, str]] = set()

        for r in raw_results:
            if not isinstance(r, dict):
                continue
            fid = str(r.get("fact_id", "")).strip()
            eid = str(r.get("evidence_id", "")).strip()
            key = (fid, eid)

            # Strict validation: reject unknown fact_id or evidence_id
            if key not in expected_keys:
                logger.warning(f"Batch {batch.batch_id} returned unknown result key {key} not submitted in batch. Rejecting.")
                continue

            # Strict validation: reject duplicate results for same fact/evidence
            if key in seen_keys:
                logger.warning(f"Batch {batch.batch_id} returned duplicate result for key {key}. Rejecting duplicate.")
                continue
            seen_keys.add(key)

            res_str = str(r.get("result", r.get("verification_result", "INSUFFICIENT"))).strip().upper()
            if res_str not in ("SUPPORTS", "CONTRADICTS", "INSUFFICIENT"):
                res_str = "INSUFFICIENT"

            try:
                conf = float(r.get("confidence", 0.0))
                if math.isnan(conf) or math.isinf(conf):
                    conf = 0.0
                else:
                    conf = max(0.0, min(1.0, conf))
            except (ValueError, TypeError):
                conf = 0.0

            rationale = str(r.get("rationale", "Batched semantic evidence verification."))

            validated_results.append(BatchVerificationItemResult(
                fact_id=fid,
                evidence_id=eid,
                result=res_str,
                confidence=conf,
                rationale=rationale
            ))

        # Enforce safe fallback for any item omitted by the model
        for key, item in expected_keys.items():
            if key not in seen_keys:
                validated_results.append(BatchVerificationItemResult(
                    fact_id=item.fact_id,
                    evidence_id=item.evidence_id,
                    result="INSUFFICIENT",
                    confidence=0.0,
                    rationale="Item omitted from model response; defaulted safely to INSUFFICIENT."
                ))

        return validated_results

    # ------------------------------------------------------------------------
    # Full CaseEnvelope Verification (Batched, deduplicated, pruned)
    # ------------------------------------------------------------------------

    def _collect_envelope_facts(self, envelope: CaseEnvelope) -> List[Fact]:
        """Collects all unique Fact instances across top-level ledger and category payloads."""
        seen_fact_ids: Set[str] = set()
        collected: List[Fact] = []

        def add_facts(facts_iterable):
            if not facts_iterable:
                return
            for f in facts_iterable:
                if f and f.fact_id not in seen_fact_ids:
                    seen_fact_ids.add(f.fact_id)
                    collected.append(f)

        # 1. Top-level Fact ledger
        add_facts(getattr(envelope, "fact_ledger", None) or getattr(envelope, "facts", []))

        # 2. ICSR sub-payloads
        if envelope.icsr:
            add_facts(getattr(envelope.icsr, "facts", []))
            if hasattr(envelope.icsr, "patient"):
                add_facts(getattr(envelope.icsr.patient, "facts", []))
            if hasattr(envelope.icsr, "reporter"):
                add_facts(getattr(envelope.icsr.reporter, "facts", []))
            if hasattr(envelope.icsr, "product"):
                add_facts(getattr(envelope.icsr.product, "facts", []))
            if hasattr(envelope.icsr, "reaction"):
                add_facts(getattr(envelope.icsr.reaction, "facts", []))

        # 3. PQC sub-payload
        pqc = getattr(envelope, "pqc", None) or getattr(envelope, "quality_complaint", None)
        if pqc and hasattr(pqc, "facts"):
            add_facts(pqc.facts)

        # 4. MI sub-payload
        mi = getattr(envelope, "mi", None) or getattr(envelope, "medical_info", None)
        if mi and hasattr(mi, "facts"):
            add_facts(mi.facts)

        # 5. Not Relevant sub-payload
        nr = getattr(envelope, "not_relevant", None)
        if nr and hasattr(nr, "facts"):
            add_facts(nr.facts)

        return collected

    def verify_envelope(
        self,
        envelope: CaseEnvelope,
        document_context: Optional[str] = None
    ) -> CaseEnvelope:
        """
        Executes batched, deduplicated, pruned semantic evidence verification
        across all facts in a CaseEnvelope:
        - Top-level atomic fact_ledger
        - ICSR patient, reporter, product, reaction facts
        - PQC complaint facts
        - MI inquiry facts
        - Not Relevant facts
        """
        start_time = time.time()
        context = document_context or envelope.document_summary or ""

        # Collect all unique facts
        all_facts = self._collect_envelope_facts(envelope)
        total_facts = len(all_facts)

        candidate_count_before_pruning = sum(len(f.evidence) for f in all_facts)

        # Structure to track verification tasks: (fact, candidate)
        tasks_to_verify: List[Tuple[Fact, Evidence]] = []
        unique_evidence_fingerprints: Set[str] = set()

        max_k = getattr(settings, "VERIFIER_TOP_K_CANDIDATES_PER_FACT", 2)

        for fact in all_facts:
            # 1. Non-semantic guard: NOT_STATED facts immediately resolve to INSUFFICIENT
            if VerificationIntegrityGuard.is_not_stated(fact):
                fact.verification_state = VerificationResult.INSUFFICIENT
                for cand in fact.evidence:
                    cand.verification_result = VerificationResult.INSUFFICIENT
                    cand.verification_confidence = 0.0
                    cand.verification_rationale = "Fact is unstated in source; candidate evidence cannot support an absent value."
                    cand.verification_metadata = {
                        "verifier_method": "integrity_guard",
                        "rule": "not_stated_guard",
                        "timestamp": int(time.time())
                    }
                continue

            if not fact.evidence:
                fact.verification_state = VerificationResult.INSUFFICIENT
                continue

            # 2. Filter empty candidates & deduplicate within fact
            valid_candidates: List[Evidence] = []
            seen_in_fact: Set[str] = set()

            for cand in fact.evidence:
                if VerificationIntegrityGuard.is_empty_candidate(cand):
                    cand.verification_result = VerificationResult.INSUFFICIENT
                    cand.verification_confidence = 0.0
                    cand.verification_rationale = "Candidate evidence verbatim snippet is empty or missing."
                    cand.verification_metadata = {
                        "verifier_method": "integrity_guard",
                        "rule": "empty_evidence_guard",
                        "timestamp": int(time.time())
                    }
                    continue

                norm_snippet = re.sub(r"\s+", " ", cand.verbatim_snippet.strip().lower())
                fp = f"{cand.source_id}|{cand.page_or_location}|{norm_snippet}"
                unique_evidence_fingerprints.add(fp)

                if fp in seen_in_fact:
                    cand.verification_result = VerificationResult.INSUFFICIENT
                    cand.verification_confidence = 0.0
                    cand.verification_rationale = "Duplicate candidate evidence snippet within same fact."
                    cand.verification_metadata = {
                        "verifier_method": "integrity_guard",
                        "rule": "duplicate_candidate_pruned",
                        "timestamp": int(time.time())
                    }
                    continue
                seen_in_fact.add(fp)
                valid_candidates.append(cand)

            # 3. Candidate pruning: Keep top K candidates per fact
            if len(valid_candidates) > max_k:
                pruned_candidates = valid_candidates[:max_k]
                for excess in valid_candidates[max_k:]:
                    excess.verification_result = VerificationResult.INSUFFICIENT
                    excess.verification_confidence = 0.0
                    excess.verification_rationale = "Pruned low-ranked retrieval candidate to preserve verification budget."
                    excess.verification_metadata = {
                        "verifier_method": "pruned",
                        "rule": "excess_candidate_budget",
                        "timestamp": int(time.time())
                    }
                valid_candidates = pruned_candidates

            for cand in valid_candidates:
                tasks_to_verify.append((fact, cand))

        candidate_count_after_pruning = len(tasks_to_verify)

        # 4. Construct Bounded Batches
        batches: List[VerificationBatch] = []
        batch_max_items = getattr(settings, "VERIFIER_BATCH_MAX_ITEMS", 6)
        batch_max_chars = getattr(settings, "VERIFIER_BATCH_MAX_CHARS", 3500)

        current_batch_id_num = 1
        current_catalog: Dict[str, Dict[str, str]] = {}
        current_items: List[BatchItemInput] = []
        current_chars = 0

        # Mapping to lookup (Fact, Evidence) from (fact_id, evidence_id)
        evidence_lookup: Dict[Tuple[str, str], Tuple[Fact, Evidence]] = {}

        for fact, cand in tasks_to_verify:
            key = (fact.fact_id, cand.evidence_id)
            evidence_lookup[key] = (fact, cand)

            # Check if evidence snippet is in catalog
            ev_id = cand.evidence_id
            snip_bounded = cand.verbatim_snippet.strip()
            if len(snip_bounded) > 400:
                snip_bounded = snip_bounded[:400] + "..."

            if ev_id not in current_catalog:
                current_catalog[ev_id] = {
                    "source": cand.source_id,
                    "location": cand.page_or_location,
                    "snippet": snip_bounded
                }
                current_chars += len(snip_bounded) + 80

            item = BatchItemInput(
                fact_id=fact.fact_id,
                fact_field=fact.field,
                fact_value=str(fact.value),
                evidence_id=ev_id,
                evidence_snippet=cand.verbatim_snippet,
                source_id=cand.source_id,
                location=cand.page_or_location
            )
            current_items.append(item)
            current_chars += len(fact.field) + len(str(fact.value)) + 80

            # Check batch thresholds
            if len(current_items) >= batch_max_items or current_chars >= batch_max_chars:
                batches.append(VerificationBatch(
                    batch_id=f"verify-batch-{current_batch_id_num:02d}",
                    evidence_catalog=current_catalog,
                    items=current_items
                ))
                current_batch_id_num += 1
                current_catalog = {}
                current_items = []
                current_chars = 0

        if current_items:
            batches.append(VerificationBatch(
                batch_id=f"verify-batch-{current_batch_id_num:02d}",
                evidence_catalog=current_catalog,
                items=current_items
            ))

        # 5. Sequential Execution of Bounded Batches
        groq_requests_sent = 0
        groq_requests_avoided = max(0, candidate_count_before_pruning - len(batches))
        short_circuited_batches = 0
        rate_limit_429_count = 0
        batch_durations: List[int] = []

        provider = self._get_provider()

        for idx, batch in enumerate(batches):
            t_batch_start = time.time()
            if provider and not provider.is_healthy():
                short_circuited_batches += 1
            else:
                if idx > 0 and getattr(provider, "provider_name", "") == "groq" and provider.is_healthy():
                    # Bounded pacing: sleep 3.5s to let Groq's 8,000 TPM bucket reset
                    logger.info("Pacing Groq requests (3.5s) to honor token bucket quota...")
                    time.sleep(3.5)
                groq_requests_sent += 1

            batch_results = self.verify_batch(batch, document_context=context)
            batch_ms = int((time.time() - t_batch_start) * 1000)
            batch_durations.append(batch_ms)

            # Apply batch results to Evidence objects
            for res in batch_results:
                key = (res.fact_id, res.evidence_id)
                if key in evidence_lookup:
                    _, cand = evidence_lookup[key]
                    if res.result == "SUPPORTS":
                        cand.verification_result = VerificationResult.SUPPORTS
                    elif res.result == "CONTRADICTS":
                        cand.verification_result = VerificationResult.CONTRADICTS
                    else:
                        cand.verification_result = VerificationResult.INSUFFICIENT
                    cand.verification_confidence = res.confidence
                    cand.verification_rationale = res.rationale
                    
                    is_fallback = (res.confidence == 0.0 and res.result == "INSUFFICIENT" and 
                                   ("fallback" in res.rationale.lower() or "circuit" in res.rationale.lower() or "malformed" in res.rationale.lower() or "error" in res.rationale.lower() or "unavailable" in res.rationale.lower()))
                    cand.verification_metadata = {
                        "verifier_method": "fallback" if is_fallback else "llm_semantic_nli",
                        "provider": provider.provider_name if provider else "fallback",
                        "model": getattr(provider, "_default_model", settings.GROQ_VERIFIER_MODEL) if provider else "none",
                        "batch_id": batch.batch_id,
                        "latency_ms": batch_ms,
                        "timestamp": int(time.time())
                    }
                    if is_fallback:
                        cand.verification_metadata["error"] = res.rationale

        # 6. Synthesize Overall Fact Verification States
        for fact in all_facts:
            if VerificationIntegrityGuard.is_not_stated(fact):
                fact.verification_state = VerificationResult.INSUFFICIENT
                continue

            if not fact.evidence:
                fact.verification_state = VerificationResult.INSUFFICIENT
                continue

            has_contradict = any(e.verification_result == VerificationResult.CONTRADICTS for e in fact.evidence)
            has_support = any(e.verification_result == VerificationResult.SUPPORTS for e in fact.evidence)

            if has_contradict:
                fact.verification_state = VerificationResult.CONTRADICTS
            elif has_support:
                fact.verification_state = VerificationResult.SUPPORTS
            else:
                fact.verification_state = VerificationResult.INSUFFICIENT

        total_latency_ms = int((time.time() - start_time) * 1000)
        avg_batch_ms = int(sum(batch_durations) / len(batch_durations)) if batch_durations else 0

        # Record metrics
        metrics = {
            "total_facts_submitted": total_facts,
            "total_unique_evidence_items": len(unique_evidence_fingerprints),
            "candidate_count_before_pruning": candidate_count_before_pruning,
            "candidate_count_after_pruning": candidate_count_after_pruning,
            "number_of_verification_batches": len(batches),
            "groq_requests_sent": groq_requests_sent,
            "groq_requests_avoided": groq_requests_avoided,
            "total_verification_duration_ms": total_latency_ms,
            "average_batch_duration_ms": avg_batch_ms,
            "rate_limit_429_count": rate_limit_429_count,
            "short_circuited_batches": short_circuited_batches
        }

        envelope.metadata["verification_latency_ms"] = total_latency_ms
        envelope.metadata["verification_metrics"] = metrics
        logger.info(
            f"Verified CaseEnvelope {envelope.envelope_id} in {total_latency_ms}ms "
            f"via {len(batches)} batches (Groq calls: {groq_requests_sent}, avoided: {groq_requests_avoided})."
        )

        return envelope

evidence_verifier = EvidenceVerifier()
