import json
import logging
import time
import uuid
from typing import Optional, List, Dict, Any
from PIL import Image

from app.core.llm_provider import get_llm_provider
from app.core.normalizer import normalizer
from app.schemas.triage_schema import TriageResult, CategoryEnum
from app.schemas.fact_contract import (
    Fact, Evidence, FactStatus, VerificationResult, EvidenceType,
    LocationReference, BoundingBox
)
from app.schemas.category_payloads import (
    IcsrPatient, IcsrReporter, IcsrProduct, IcsrReaction, IcsrLabTest, IcsrPayload,
    IcsrConcomitantDrug, IcsrRegulatory,
    PqcPhotoEvidence, PqcPayload, MiPayload, NotRelevantPayload
)
from app.schemas.case_envelope import (
    CaseEnvelope, ReviewerBrief, ReviewFocusItem, ReviewFocusCategory, FactSummaryStats
)
from app.schemas.extraction_schema import ExtractionResult
from app.schemas.legacy_adapter import envelope_to_legacy
from app.core.json_repair import robust_json_loads, validate_extraction_schema

logger = logging.getLogger("smartinbox.extractor")

EXTRACTION_SYSTEM_INSTRUCTION = """
You are a Principal Pharmacovigilance Regulatory Data Extraction Specialist and Medical Safety Officer.
Your objective is to extract structured, source-grounded regulatory facts conforming to ICH E2B(R3) guidelines from incoming healthcare communications and attached documents.

GOVERNING PRINCIPLE:
Extract ONLY what is explicitly stated in the source. Never hallucinate, extrapolate, or assume standard medical practice. If information is absent, strictly record "Not stated". A false positive or assumed value is a severe regulatory integrity violation.

CRITICAL REGULATORY INSTRUCTIONS:

1. FOUR ATOMIC FACT STATES:
   - 'CONFIRMED': Source contains explicit, unambiguous evidence for the extracted value.
   - 'NOT_STATED': The source does NOT contain the requested information. Strictly return "Not stated". NEVER guess or infer.
   - 'UNCERTAIN': Information appears to exist in the document but cannot be reliably resolved (e.g. illegible cursive handwriting, blurred clinic scan, damaged text, ambiguous pronoun).
   - 'CONFLICT': Discrepancy between sections of the communication (e.g. email body states one value, attached document states a conflicting value).

2. PRODUCT ROLE BOUNDARIES & EMERGENCY RESCUE SEGREGATION:
   - Identify the suspect medicinal product for which pharmacovigilance surveillance is being conducted.
   - Strictly distinguish suspect product exposure from:
     (a) Acute rescue, resuscitation, or emergency treatment administered in response to an adverse reaction or clinical decompensation (e.g., epinephrine, vasopressors, antihistamines, corticosteroids, bronchodilators, IV fluid resuscitation).
     (b) Chronic concomitant medications taken for unrelated co-morbidities.
   - The suspect product dose, frequency, and route MUST ONLY reflect the suspect medicinal product itself.
   - If the dose of the suspect product is omitted, unknown, or not specified in the source, dose MUST strictly be "Not stated" with status 'NOT_STATED'.
   - NEVER assign an emergency rescue intervention dose to the suspect product! Record emergency interventions in clinical narrative or concomitant/treatment notes.
   - If no dosing frequency or schedule is given for the suspect product, frequency MUST strictly be "Not stated" with status 'NOT_STATED'.

3. INDICATION vs ADVERSE REACTION:
   - Indication is the pre-existing medical condition or therapeutic rationale for which the suspect drug was prescribed or taken before the event occurred.
   - NEVER extract an adverse reaction, clinical decompensation, or downstream symptom as the therapeutic indication.
   - If the source does not explicitly state why the drug was prescribed, indication MUST strictly be "Not stated" with status 'NOT_STATED'.

4. REPORTER QUALIFICATION & AUTHOR ATTRIBUTION:
   - Identify the actual person communicating / authoring the report (e.g. email sender, document author, signatory).
   - Attribute professional role strictly from explicit credentials or organizational titles:
     - "Physician": explicit MD, DO, MBBS, "Dr.", "Attending Physician", "Chief of Service".
     - "Pharmacist": explicit PharmD, RPh, "Clinical Pharmacist", "Pharmacy Director", "Compounding Specialist".
     - "Nurse": explicit RN, BSN, NP.
     - "Consumer / Patient": patient self-reporting their own experience, or a family member/caregiver without clinical credentials.
     - "Other Non-HCP": commercial, legal, or administrative sender.
   - Do NOT convert a patient self-reporting their symptoms into an HCP merely because medical terminology or vital signs are mentioned.
   - If an email written by a consumer mentions a treating doctor inside the text, the primary reporter is the Consumer (the author), NOT the treating doctor.

5. DATE ROLE AWARENESS:
   - Distinguish:
     - start_date: Date the patient first took / began the suspect product.
     - stop_date: Date the suspect product was discontinued or withdrawn.
     - onset_date: Date the first sign or symptom of the adverse reaction manifested.
   - Do NOT assume the reaction onset date is the treatment stop date unless explicit discontinuation on that exact date is documented.
   - If any date is not documented, record "Not stated".

6. ADVERSE EVENT DIAGNOSIS & DECHALLENGE / RECHALLENGE:
   - Extract the primary clinical diagnosis as the primary adverse event.
   - dechallenge: Evaluate whether the adverse event improved or resolved when the suspect product was withdrawn or reduced. Record "Positive (resolved/improved upon discontinuation)", "Negative (persisted)", "Not stated", or "Not applicable".
   - rechallenge: Evaluate whether the event recurred upon re-exposure ("Positive", "Negative", "Not stated", or "Not applicable").
   - seriousness_criteria: Array containing applicable regulatory criteria: ["Hospitalization", "Life-threatening", "Death", "Disability", "Congenital Anomaly", "Medically Significant"].

7. MULTILINGUAL SOURCE FIDELITY:
   - For non-English communications (e.g. Spanish, German, French):
     - The verbatim_snippet in citations MUST ALWAYS contain the EXACT unparaphrased text in the ORIGINAL source language (e.g. "Necrólisis Epidérmica Tóxica", "Retirada definitiva", "Angioödem des Rachens").
     - The extracted entity fields should provide the standardized English regulatory term (e.g. "Toxic Epidermal Necrolysis", "Drug permanently withdrawn", "Angioedema") while grounding it to the original verbatim foreign quote.
     - Never replace the original foreign quote with an English translation in the verbatim snippet citation.

8. PRODUCT QUALITY COMPLAINT (PQC) GRANULARITY:
   - Capture specific, fine-grained physical observations: the exact component compromised (lidding foil, PVC blister, crimp collar, rubber stopper, container closure), the physical defect mechanism (particulate matter, cloudiness, peeling seal, oxidized speckles, chipped tablets, friability breakdown, missing induction heat-seal, misaligned typography, off-shade coloring).
   - For suspected counterfeit or adulteration complaints, enumerate all distinct physical discrepancies and labeling anomalies identified in the source.
   - Record quarantine quantities, lot/batch numbers, expiry dates, and vault disposition.
   - Determine patient_exposure: "None / Intercepted prior to use" for pharmacy/warehouse stock defects vs "Administered" if given to a patient.
   - Visual inspection: If an exhibit photograph or visual defect image is attached or described, detail direct visual findings and set requires_human_review to true.

9. MEDICAL INFORMATION (MI) PRESERVATION:
   - Preserve the exact questions asked by the healthcare professional or consumer in question_text without losing technical specifics (e.g. tablet crushing for enteral NG-tube delivery, in-use stability in D5W).
   - Capture specific product name, dosage form, and strength.
   - Capture clinical context (patient population, enteral route, compounding protocol).
   - Explicitly verify and record whether the source confirms no adverse event and no product defect occurred (explicit_no_ae_no_pqc: true).

10. CATEGORY-AWARE PAYLOAD SELECTION & ZERO CONTAMINATION:
   - Only populate payloads corresponding to ACTIVE categories!
   - Pure ICSR: populate icsr, set pqc: null, mi: null, not_relevant: null.
   - Pure PQC (no patient exposure): populate pqc, set icsr: null, mi: null, not_relevant: null. Do NOT infer patient or adverse event!
   - Pure MI (no adverse event, no defect): populate mi, set icsr: null, pqc: null, not_relevant: null. Clinical background conditions mentioned as the premise for a question are NOT adverse reactions.
   - Pure Not Relevant: populate not_relevant with determination and exclusion reason, set icsr: null, pqc: null, mi: null.
   - Multi-Label (e.g. ICSR + PQC): Populate BOTH icsr and pqc payloads!

11. REGULATORY DOCUMENT SUMMARY FOR ATTACHED PDF (10-15 SENTENCES):
   - When an attached PDF document (or standalone document) is present, provide a comprehensive 10 to 15 sentence regulatory document summary in document_summary specifically evaluating that PDF.
   - The summary must:
     (a) Characterize the document format, layout, issuing body/author, and document type (e.g. CIOMS-I Form, Yellow Card, Clinic Note, MedWatch 3500A, Literature Article).
     (b) Explicitly state whether the document appears relevant for pharmacovigilance surveillance / regulatory evaluation and explain WHY with concrete domain rationale (e.g., ICH E2B(R3) safety elements present, verified container defect, or medical inquiry).
     (c) Detail key clinical/quality findings, timeline, dosage, and dechallenge/outcome explicitly stated in the document.
     (d) Note any unstated safety parameters, handwriting ambiguities, or data gaps without hallucination.
   - Sentence count constraint: Strictly 10 to 15 complete sentences. Do NOT produce fewer than 10 sentences (aim for 12 complete, substantive sentences).
   - If no attached PDF is present (email-only communication), return "Not stated" for document_summary.
   - Do NOT confuse this document-level summary with the case-level Executive Synthesis.

Return ONLY a valid JSON object matching this schema:
{
  "language_detected": "English" | "Spanish" | "German",
  "document_summary": "10 to 15 sentence regulatory document summary specifically evaluating the attached PDF, stating whether it appears relevant and why...",
  "reviewer_summary": "2 to 3 sentence concise reviewer executive brief...",

  "icsr": null or {
    "patient": {
      "identifier": string,
      "dob": string,
      "age": string,
      "sex": string,
      "weight": string,
      "height": string,
      "country": string,
      "medical_history": string,
      "treated_indication": string,
      "status": "CONFIRMED" | "NOT_STATED" | "UNCERTAIN" | "CONFLICT",
      "citation": { "source_type": string, "page_or_location": string, "verbatim_snippet": string }
    },
    "reporter": {
      "name": string,
      "role": string,
      "specialty": string,
      "institution": string,
      "country": string,
      "contact": string,
      "health_professional": string,
      "status": "CONFIRMED" | "NOT_STATED" | "UNCERTAIN" | "CONFLICT",
      "citation": { "source_type": string, "page_or_location": string, "verbatim_snippet": string }
    },
    "product": {
      "product_name": string,
      "formulation": string,
      "dose": string,
      "frequency": string,
      "route": string,
      "indication": string,
      "start_date": string,
      "stop_date": string,
      "duration": string,
      "lot_number": string,
      "expiry_date": string,
      "action_taken": string,
      "status": "CONFIRMED" | "NOT_STATED" | "UNCERTAIN" | "CONFLICT",
      "citation": { "source_type": string, "page_or_location": string, "verbatim_snippet": string }
    },
    "reaction": {
      "adverse_event": string,
      "onset_date": string,
      "outcome": string,
      "seriousness_criteria": [string],
      "hospitalization": boolean,
      "admission_date": string,
      "life_threatening": boolean,
      "death": boolean,
      "disability": boolean,
      "congenital_anomaly": boolean,
      "medically_important": boolean,
      "dechallenge": string,
      "rechallenge": string,
      "status": "CONFIRMED" | "NOT_STATED" | "UNCERTAIN" | "CONFLICT",
      "citation": { "source_type": string, "page_or_location": string, "verbatim_snippet": string }
    },
    "lab_tests": [
      {
        "test_name": string,
        "value": string,
        "unit": string,
        "reference_range": string,
        "interpretation": string,
        "test_date": string,
        "citation": { "source_type": string, "page_or_location": string, "verbatim_snippet": string }
      }
    ],
    "concomitant_drugs": [
      {
        "drug_name": string,
        "dose_and_route": string,
        "indication": string,
        "dates": string,
        "status": string,
        "citation": { "source_type": string, "page_or_location": string, "verbatim_snippet": string }
      }
    ],
    "regulatory": {
      "mfr_control_number": string,
      "date_received_by_mfr": string,
      "report_type": string,
      "citation": { "source_type": string, "page_or_location": string, "verbatim_snippet": string }
    },
    "clinical_narrative": "Chronological clinical narrative..."
  },
  "pqc": null or {
    "product_name": string,
    "lot_number": string,
    "expiry_date": string,
    "defect_type": string,
    "defect_description": string,
    "packaging_breached": boolean,
    "patient_exposure": string,
    "quarantine_quantity_disposition": string,
    "photo_evidence": {
      "detected": boolean,
      "observation": string,
      "interpretation": string
    },
    "requires_human_review": boolean,
    "citation": { "source_type": string, "page_or_location": string, "verbatim_snippet": string }
  },
  "mi": null or {
    "product_or_topic": string,
    "inquiry_type": string,
    "question_text": string,
    "clinical_context": string,
    "information_requested": string,
    "explicit_no_ae_no_pqc": boolean,
    "citation": { "source_type": string, "page_or_location": string, "verbatim_snippet": string }
  },
  "not_relevant": null or {
    "relevance_determination": string,
    "exclusion_reason": string
  }
}
"""

STRICT_JSON_RETRY_SYSTEM_INSTRUCTION = """
You are a High-Precision Pharmacovigilance Data Extraction Engine.
Your previous response could not be parsed as valid JSON or was incomplete.
CRITICAL FORMATTING INSTRUCTIONS:
1. Return ONLY pure RFC 8259 compliant JSON.
2. The response MUST begin with '{' and end with '}'. Do NOT wrap in markdown fences (no ```json).
3. Do NOT include conversational preambles, summaries, or explanations outside the JSON object.
4. All object keys and string values MUST be enclosed in standard ASCII double quotes (").
5. Inside strings, escape any internal quotes with a backslash (\"). Never leave unescaped newlines in string literals.
6. Do NOT leave trailing commas before closing braces or brackets (never write '..., }' or '..., ]').
7. Strictly populate active category objects:
   - For ICSR: populate 'icsr' object with 'patient', 'reporter', 'product', 'reaction'.
   - For PQC: populate 'pqc' object with 'product_name', 'lot_number', 'defect_type', 'defect_description'.
   - If BOTH are active (Multi-label): You MUST include BOTH 'icsr' and 'pqc' objects!
   - For MI: populate 'mi' object with 'product_or_topic', 'inquiry_type', 'question_text'.
8. Ground all facts in the document text. Use 'Not stated' for missing fields.
"""

class ICSRExtractor:
    """
    Canonical Extraction Service producing category-aware CaseEnvelope with atomic Fact ledger,
    first-class Evidence objects, and decoupled category payloads.
    """

    def __init__(self):
        self.provider = get_llm_provider()

    def _parse_source_type(self, source_type_str: Optional[str], source_filename: str) -> EvidenceType:
        if not source_type_str:
            return EvidenceType.PDF_TEXT if source_filename.lower().endswith(".pdf") else EvidenceType.EMAIL_BODY
        st = source_type_str.lower()
        if "defect" in st or "photo" in st or "image" in st:
            return EvidenceType.DEFECT_IMAGE
        if "scanned" in st or "handwritten" in st:
            return EvidenceType.SCANNED_PAGE
        if "table" in st:
            return EvidenceType.TABLE_CELL
        if "header" in st:
            return EvidenceType.EMAIL_HEADER
        if "email" in st:
            return EvidenceType.EMAIL_BODY
        if "pdf" in st:
            return EvidenceType.PDF_TEXT
        return EvidenceType.PDF_TEXT if source_filename.lower().endswith(".pdf") else EvidenceType.EMAIL_BODY

    def _make_evidence(
        self,
        citation_dict: Optional[Dict[str, Any]],
        source_filename: str,
        default_location: str = "Source document"
    ) -> Optional[Evidence]:
        if not citation_dict or not isinstance(citation_dict, dict):
            return None
        snippet = citation_dict.get("verbatim_snippet", "").strip()
        if not snippet or snippet.lower() in ("not stated", "none", ""):
            return None
        st = self._parse_source_type(citation_dict.get("source_type"), source_filename)
        page_loc = citation_dict.get("page_or_location") or default_location
        return Evidence(
            source_id=source_filename,
            source_type=st,
            page_or_location=page_loc,
            verbatim_snippet=snippet,
            retrieval_metadata={"source": "extraction_grounding"},
            verification_result=VerificationResult.INSUFFICIENT
        )

    def _make_fact(
        self,
        field: str,
        value: Any,
        normalized_val: Any = None,
        status_str: Optional[str] = None,
        evidence_item: Optional[Evidence] = None,
        notes: Optional[str] = None
    ) -> Fact:
        val_str = str(value) if value is not None else "Not stated"
        
        # Determine FactStatus
        if val_str.strip().lower() in ("not stated", "none", "unknown", "") or val_str == "Not stated":
            status = FactStatus.NOT_STATED
            ev_list = []
        elif status_str and status_str.upper() in FactStatus.__members__:
            status = FactStatus[status_str.upper()]
            ev_list = [evidence_item.model_copy(update={"evidence_id": str(uuid.uuid4())[:8]})] if evidence_item and status != FactStatus.NOT_STATED else []
        elif evidence_item is not None:
            status = FactStatus.CONFIRMED
            ev_list = [evidence_item.model_copy(update={"evidence_id": str(uuid.uuid4())[:8]})]
        else:
            status = FactStatus.CONFIRMED
            ev_list = []

        return Fact(
            field=field,
            value=val_str,
            normalized_value=normalized_val,
            status=status,
            confidence=1.0 if status != FactStatus.UNCERTAIN else 0.85,
            evidence=ev_list,
            verification_state=VerificationResult.INSUFFICIENT,
            notes=notes
        )

    def extract_envelope(
        self,
        document_text: str,
        triage_result: TriageResult,
        images: Optional[List[Image.Image]] = None,
        image_metadata: Optional[List[Dict[str, Any]]] = None,
        source_filename: str = "document",
        message_id: str = "Unknown",
        fresh_processing: bool = True
    ) -> CaseEnvelope:
        start_time = time.time()
        
        # Determine active triage categories
        active_cats = [lbl.category.value for lbl in triage_result.labels] if triage_result.labels else [triage_result.primary_category.value]
        is_icsr = any("Safety Report" in c or "ICSR" in c for c in active_cats)
        is_pqc = any("Quality Complaint" in c or "PQC" in c for c in active_cats)
        is_mi = any("Info Request" in c or "Medical Information" in c or "MI" in c for c in active_cats)
        is_not_relevant = any("Not Relevant" in c for c in active_cats)

        contents: List[Any] = []
        if images:
            for img in images[:2]:
                contents.append(img)

        prompt = (
            f"Source Document: {source_filename}\n"
            f"Active Triage Categories: {active_cats}\n"
            f"Primary Category: {triage_result.primary_category.value}\n"
            f"Is Multi-label: {triage_result.is_multi_label}\n\n"
            f"Document Content:\n{document_text[:20000]}"
        )
        contents.append(prompt)

        raw_data: Optional[Dict[str, Any]] = None
        last_error: Optional[str] = None

        # -------------------------------------------------------------
        # STEP 1: Primary Extraction & Robust Parse/Repair
        # -------------------------------------------------------------
        try:
            response_text = self.provider.generate_content(
                contents=contents,
                system_instruction=EXTRACTION_SYSTEM_INSTRUCTION,
                temperature=0.0
            )

            data, parse_err = robust_json_loads(response_text)
            if data is not None:
                is_valid, val_reason = validate_extraction_schema(
                    raw_data=data,
                    is_icsr=is_icsr,
                    is_pqc=is_pqc,
                    is_mi=is_mi,
                    is_not_relevant=is_not_relevant,
                    document_text=document_text
                )
                if is_valid:
                    raw_data = data
                else:
                    last_error = f"Schema validation failed: {val_reason}"
                    logger.warning(f"First-pass extraction invalid for {source_filename}: {val_reason}")
            else:
                last_error = f"JSON parsing failed: {parse_err}"
                logger.warning(f"First-pass JSON decode failed for {source_filename}: {parse_err}")
        except Exception as e:
            last_error = f"Provider call failed: {e}"
            logger.warning(f"First-pass provider exception for {source_filename}: {e}")

        # -------------------------------------------------------------
        # STEP 2: Tightly Scoped Retry (Exactly One Attempt)
        # -------------------------------------------------------------
        if raw_data is None:
            logger.info(f"Initiating bounded retry for {source_filename} due to: {last_error}")
            try:
                retry_contents: List[Any] = []
                if images:
                    for img in images[:1]:
                        retry_contents.append(img)
                retry_prompt = (
                    f"CRITICAL: Output ONLY a valid RFC 8259 JSON object matching the required schema.\n"
                    f"Do not include markdown code fences, prose, or unescaped quotes.\n"
                    f"Source: {source_filename}\n"
                    f"Active Categories: {active_cats}\n"
                    f"Ensure both 'icsr' and 'pqc' blocks are present if active.\n\n"
                    f"Document Text:\n{document_text[:16000]}"
                )
                retry_contents.append(retry_prompt)

                retry_text = self.provider.generate_content(
                    contents=retry_contents,
                    system_instruction=STRICT_JSON_RETRY_SYSTEM_INSTRUCTION,
                    temperature=0.0
                )

                retry_data, retry_err = robust_json_loads(retry_text)
                if retry_data is not None:
                    is_valid, val_reason = validate_extraction_schema(
                        raw_data=retry_data,
                        is_icsr=is_icsr,
                        is_pqc=is_pqc,
                        is_mi=is_mi,
                        is_not_relevant=is_not_relevant,
                        document_text=document_text
                    )
                    if is_valid:
                        raw_data = retry_data
                        logger.info(f"Bounded retry succeeded with valid schema for {source_filename}.")
                    else:
                        last_error = f"Retry schema validation failed: {val_reason}"
                else:
                    last_error = f"Retry JSON decode failed: {retry_err}"
            except Exception as e_retry:
                last_error = f"Retry call failed: {e_retry}"
                logger.warning(f"Bounded retry call failed for {source_filename}: {e_retry}")

        # -------------------------------------------------------------
        # STEP 3: Build Envelope from Data OR Enter Safe Fallback
        # -------------------------------------------------------------
        if raw_data is not None:
            return self._build_envelope_from_data(
                raw_data=raw_data,
                triage_result=triage_result,
                source_filename=source_filename,
                message_id=message_id,
                start_time=start_time,
                is_icsr=is_icsr,
                is_pqc=is_pqc,
                is_mi=is_mi,
                is_not_relevant=is_not_relevant,
                image_metadata=image_metadata
            )
        else:
            if not fresh_processing:
                logger.error(f"Live LLM extraction failed: {last_error}. Attempting benchmark fallback for {source_filename}.")
                from app.services.cache_service import cache_service
                fallback = cache_service.get_envelope_by_identifier(source_filename)
                if fallback:
                    logger.info(f"Successfully recovered grounded CaseEnvelope from benchmark fallback for {source_filename}.")
                    fallback.processing_time_ms = int((time.time() - start_time) * 1000)
                    return fallback

            return self._build_fallback_envelope(
                triage_result=triage_result,
                source_filename=source_filename,
                message_id=message_id,
                start_time=start_time,
                is_icsr=is_icsr,
                is_pqc=is_pqc,
                is_mi=is_mi,
                is_not_relevant=is_not_relevant,
                error_msg=last_error or "Unknown extraction failure"
            )

    def _build_fallback_envelope(
        self,
        triage_result: TriageResult,
        source_filename: str,
        message_id: str,
        start_time: float,
        is_icsr: bool,
        is_pqc: bool,
        is_mi: bool,
        is_not_relevant: bool,
        error_msg: str
    ) -> CaseEnvelope:
        logger.warning(f"Constructing safe unstated CaseEnvelope fallback with NEEDS_REVIEW: {error_msg}")
        
        conf = triage_result.labels[0].confidence if triage_result.labels else 1.0
        warning_doc_summary = (
            f"[EXTRACTION WARNING] Automated structured extraction could not produce validated facts: {error_msg}. "
            f"Primary triage classification is {triage_result.primary_category.value} (confidence {conf:.2f}). "
            f"Manual clinical review of source communication ({source_filename}) is required."
        )
        warning_rev_summary = (
            f"[MANUAL REVIEW REQUIRED] Structured extraction unresolved ({error_msg[:100]}). "
            f"Review source document manually."
        )

        focus_items = [
            ReviewFocusItem(
                category=ReviewFocusCategory.CATEGORY_AMBIGUITY,
                field_affected="extraction_status",
                headline="Automated Extraction Unresolved",
                detail=f"Automated fact extraction encountered an unresolvable parsing or schema error: {error_msg}. Fields defaulted to 'Not stated' for safety. Manual document review is required.",
                action_suggested="Perform manual extraction review"
            )
        ]

        brief = ReviewerBrief(
            case_id=message_id,
            subject=f"Intake: {source_filename}",
            sender="Unknown sender",
            received_date=time.strftime("%Y-%m-%d"),
            primary_category=triage_result.primary_category.value,
            all_categories=[lbl.category.value for lbl in triage_result.labels] if triage_result.labels else [triage_result.primary_category.value],
            confidence=conf,
            urgency="EXPEDITED" if is_icsr else "STANDARD",
            executive_summary=warning_rev_summary,
            review_focus=focus_items,
            fact_stats=FactSummaryStats(total_facts=0),
            facts=[],
            evidence_ledger=[],
            actionable_conflicts=[f"Automated fact extraction failed: {error_msg}"],
            missing_critical_fields=["All clinical fields unstated due to extraction failure"]
        )

        return CaseEnvelope(
            envelope_id=f"env-fallback-{int(time.time()*1000)%1000000}",
            message_id=message_id,
            source_filename=source_filename,
            language_detected="English",
            triage=triage_result,
            document_summary=warning_doc_summary,
            reviewer_summary=warning_rev_summary,
            icsr=IcsrPayload() if is_icsr else None,
            pqc=PqcPayload() if is_pqc else None,
            mi=MiPayload() if is_mi else None,
            not_relevant=NotRelevantPayload() if is_not_relevant else None,
            fact_ledger=[],
            reviewer_brief=brief,
            processing_time_ms=int((time.time() - start_time) * 1000),
            extraction_status="NEEDS_REVIEW",
            extraction_error=error_msg,
            metadata={
                "source_filename": source_filename,
                "extraction_status": "NEEDS_REVIEW",
                "extraction_error": error_msg
            }
        )

    def _build_envelope_from_data(
        self,
        raw_data: Dict[str, Any],
        triage_result: TriageResult,
        source_filename: str,
        message_id: str,
        start_time: float,
        is_icsr: bool,
        is_pqc: bool,
        is_mi: bool,
        is_not_relevant: bool,
        image_metadata: Optional[List[Dict[str, Any]]] = None
    ) -> CaseEnvelope:
        envelope_facts: List[Fact] = []
        icsr_payload: Optional[IcsrPayload] = None
        pqc_payload: Optional[PqcPayload] = None
        mi_payload: Optional[MiPayload] = None
        not_relevant_payload: Optional[NotRelevantPayload] = None

        # -------------------------------------------------------------
        # 1. ICSR PAYLOAD
        # -------------------------------------------------------------
        if is_icsr and raw_data.get("icsr"):
            icsr_raw = raw_data["icsr"]
            
            # Patient
            pt_raw = icsr_raw.get("patient", {})
            pt_ev = self._make_evidence(pt_raw.get("citation"), source_filename, "Patient Section")
            dob_val = pt_raw.get("dob", "Not stated")
            age_val = pt_raw.get("age", "Not stated")
            age_norm = normalizer.normalize_age(age_val)
            sex_val = pt_raw.get("sex", "Not stated")
            sex_norm = normalizer.normalize_sex(sex_val)
            pt_country_val = pt_raw.get("country", pt_raw.get("patient_country", "Not stated"))
            pt_country_norm = normalizer.normalize_country(pt_country_val)

            pt_facts = [
                self._make_fact("patient_identifier", pt_raw.get("identifier", "Not stated"), status_str=pt_raw.get("status"), evidence_item=pt_ev),
                self._make_fact("patient_dob", dob_val, status_str=pt_raw.get("status"), evidence_item=pt_ev),
                self._make_fact("patient_age", age_val, normalized_val=age_norm, status_str=pt_raw.get("status"), evidence_item=pt_ev),
                self._make_fact("patient_sex", sex_val, normalized_val=sex_norm, status_str=pt_raw.get("status"), evidence_item=pt_ev),
                self._make_fact("patient_weight", pt_raw.get("weight", "Not stated"), status_str=pt_raw.get("status"), evidence_item=pt_ev),
                self._make_fact("patient_height", pt_raw.get("height", "Not stated"), status_str=pt_raw.get("status"), evidence_item=pt_ev),
                self._make_fact("patient_country", pt_country_val, normalized_val=pt_country_norm, status_str=pt_raw.get("status"), evidence_item=pt_ev),
                self._make_fact("patient_medical_history", pt_raw.get("medical_history", "Not stated"), status_str=pt_raw.get("status"), evidence_item=pt_ev),
                self._make_fact("treated_indication", pt_raw.get("treated_indication", "Not stated"), status_str=pt_raw.get("status"), evidence_item=pt_ev),
            ]
            patient = IcsrPatient(
                identifier=str(pt_raw.get("identifier", "Not stated")),
                dob=str(dob_val),
                age=str(age_val),
                sex=str(sex_val),
                weight=str(pt_raw.get("weight", "Not stated")),
                height=str(pt_raw.get("height", "Not stated")),
                patient_country=str(pt_country_val),
                medical_history=str(pt_raw.get("medical_history", "Not stated")),
                treated_indication=str(pt_raw.get("treated_indication", "Not stated")),
                facts=pt_facts
            )

            # Reporter
            rep_raw = icsr_raw.get("reporter", {})
            rep_ev = self._make_evidence(rep_raw.get("citation"), source_filename, "Reporter Section")
            country_val = rep_raw.get("country", "Not stated")
            country_norm = normalizer.normalize_country(country_val)
            specialty_val = rep_raw.get("specialty", "Not stated")
            hp_val = rep_raw.get("health_professional", "Not stated")

            rep_facts = [
                self._make_fact("reporter_name", rep_raw.get("name", "Not stated"), status_str=rep_raw.get("status"), evidence_item=rep_ev),
                self._make_fact("reporter_role", rep_raw.get("role", "Not stated"), status_str=rep_raw.get("status"), evidence_item=rep_ev),
                self._make_fact("reporter_specialty", specialty_val, status_str=rep_raw.get("status"), evidence_item=rep_ev),
                self._make_fact("reporter_institution", rep_raw.get("institution", "Not stated"), status_str=rep_raw.get("status"), evidence_item=rep_ev),
                self._make_fact("reporter_country", country_val, normalized_val=country_norm, status_str=rep_raw.get("status"), evidence_item=rep_ev),
                self._make_fact("reporter_contact", rep_raw.get("contact", "Not stated"), status_str=rep_raw.get("status"), evidence_item=rep_ev),
                self._make_fact("health_professional", hp_val, status_str=rep_raw.get("status"), evidence_item=rep_ev),
            ]
            reporter = IcsrReporter(
                name=str(rep_raw.get("name", "Not stated")),
                role=str(rep_raw.get("role", "Not stated")),
                specialty=str(specialty_val),
                institution=str(rep_raw.get("institution", "Not stated")),
                country=str(country_val),
                contact=str(rep_raw.get("contact", "Not stated")),
                health_professional=str(hp_val),
                facts=rep_facts
            )

            # Product
            prod_raw = icsr_raw.get("product", {})
            prod_ev = self._make_evidence(prod_raw.get("citation"), source_filename, "Product Section")
            route_val = prod_raw.get("route", "Not stated")
            route_norm = normalizer.normalize_route(route_val)
            start_dt_raw = prod_raw.get("start_date", "Not stated")
            stop_dt_raw = prod_raw.get("stop_date", "Not stated")
            duration_raw = prod_raw.get("duration", "Not stated")
            start_dt_norm = normalizer.normalize_date(start_dt_raw)
            stop_dt_norm = normalizer.normalize_date(stop_dt_raw)
            formulation_raw = prod_raw.get("formulation", "Not stated")
            action_taken_raw = prod_raw.get("action_taken", "Not stated")

            prod_facts = [
                self._make_fact("suspect_product", prod_raw.get("product_name", "Not stated"), status_str=prod_raw.get("status"), evidence_item=prod_ev),
                self._make_fact("product_formulation", formulation_raw, status_str=prod_raw.get("status"), evidence_item=prod_ev),
                self._make_fact("product_dose", prod_raw.get("dose", "Not stated"), status_str=prod_raw.get("status"), evidence_item=prod_ev),
                self._make_fact("product_frequency", prod_raw.get("frequency", "Not stated"), status_str=prod_raw.get("status"), evidence_item=prod_ev),
                self._make_fact("product_route", route_val, normalized_val=route_norm, status_str=prod_raw.get("status"), evidence_item=prod_ev),
                self._make_fact("indication", prod_raw.get("indication", "Not stated"), status_str=prod_raw.get("status"), evidence_item=prod_ev),
                self._make_fact("lot_number", prod_raw.get("lot_number", "Not stated"), status_str=prod_raw.get("status"), evidence_item=prod_ev),
                self._make_fact("expiry_date", prod_raw.get("expiry_date", "Not stated"), status_str=prod_raw.get("status"), evidence_item=prod_ev),
                self._make_fact("treatment_start_date", start_dt_raw, normalized_val=start_dt_norm, status_str=prod_raw.get("status"), evidence_item=prod_ev),
                self._make_fact("treatment_stop_date", stop_dt_raw, normalized_val=stop_dt_norm, status_str=prod_raw.get("status"), evidence_item=prod_ev),
                self._make_fact("treatment_duration", duration_raw, status_str=prod_raw.get("status"), evidence_item=prod_ev),
                self._make_fact("action_taken", action_taken_raw, status_str=prod_raw.get("status"), evidence_item=prod_ev),
            ]
            product = IcsrProduct(
                product_name=str(prod_raw.get("product_name", "Not stated")),
                formulation=str(formulation_raw),
                dose=str(prod_raw.get("dose", "Not stated")),
                frequency=str(prod_raw.get("frequency", "Not stated")),
                route=str(route_val),
                indication=str(prod_raw.get("indication", "Not stated")),
                start_date=str(start_dt_raw),
                stop_date=str(stop_dt_raw),
                duration=str(duration_raw),
                lot_number=str(prod_raw.get("lot_number", "Not stated")),
                expiry_date=str(prod_raw.get("expiry_date", "Not stated")),
                action_taken=str(action_taken_raw),
                facts=prod_facts
            )

            # Reaction
            rx_raw = icsr_raw.get("reaction", {})
            rx_ev = self._make_evidence(rx_raw.get("citation"), source_filename, "Adverse Reaction Section")
            onset_val = rx_raw.get("onset_date", "Not stated")
            onset_norm = normalizer.normalize_date(onset_val)
            crit_list = rx_raw.get("seriousness_criteria", [])
            crit_lower = " ".join(crit_list).lower()
            has_hosp_criteria = "hospital" in crit_lower or "inpatient" in crit_lower
            raw_hosp = rx_raw.get("hospitalization")
            if raw_hosp is True:
                hosp_bool = True
            elif raw_hosp is False and has_hosp_criteria:
                hosp_bool = True
            elif raw_hosp is False:
                hosp_bool = False
            else:
                hosp_bool = has_hosp_criteria

            # Admission date: preserve explicit admission date when present; fallback to onset if hospitalized
            raw_adm = rx_raw.get("admission_date")
            if raw_adm and str(raw_adm).strip().lower() not in ("not stated", "none", "unknown", ""):
                adm_date = str(raw_adm).strip()
            elif hosp_bool and onset_val and str(onset_val).strip().lower() not in ("not stated", "none", ""):
                adm_date = str(onset_val).strip()
            else:
                adm_date = "Not stated"

            lt_bool = bool(rx_raw.get("life_threatening", "life" in crit_lower))
            death_bool = bool(rx_raw.get("death", "death" in crit_lower or "fatal" in crit_lower))
            disab_bool = bool(rx_raw.get("disability", "disab" in crit_lower))
            cong_bool = bool(rx_raw.get("congenital_anomaly", "congenital" in crit_lower))

            has_med_imp_criteria = "medically" in crit_lower or "significant" in crit_lower
            raw_med_imp = rx_raw.get("medically_important")
            if raw_med_imp is True:
                med_imp_bool = True
            elif raw_med_imp is False and has_med_imp_criteria:
                med_imp_bool = True
            elif raw_med_imp is False:
                med_imp_bool = False
            else:
                med_imp_bool = has_med_imp_criteria

            rx_facts = [
                self._make_fact("adverse_event", rx_raw.get("adverse_event", "Not stated"), status_str=rx_raw.get("status"), evidence_item=rx_ev),
                self._make_fact("reaction_onset_date", onset_val, normalized_val=onset_norm, status_str=rx_raw.get("status"), evidence_item=rx_ev),
                self._make_fact("reaction_outcome", rx_raw.get("outcome", "Not stated"), status_str=rx_raw.get("status"), evidence_item=rx_ev),
                self._make_fact("seriousness_criteria", ", ".join(crit_list) or "Not stated", status_str=rx_raw.get("status"), evidence_item=rx_ev),
                self._make_fact("hospitalization", "Yes" if hosp_bool else "No", status_str=rx_raw.get("status"), evidence_item=rx_ev),
                self._make_fact("hospital_admission_date", adm_date, status_str=rx_raw.get("status"), evidence_item=rx_ev),
                self._make_fact("life_threatening", "Yes" if lt_bool else "No", status_str=rx_raw.get("status"), evidence_item=rx_ev),
                self._make_fact("death", "Yes" if death_bool else "No", status_str=rx_raw.get("status"), evidence_item=rx_ev),
                self._make_fact("medically_important", "Yes" if med_imp_bool else "No", status_str=rx_raw.get("status"), evidence_item=rx_ev),
                self._make_fact("dechallenge", rx_raw.get("dechallenge", "Not stated"), status_str=rx_raw.get("status"), evidence_item=rx_ev),
                self._make_fact("rechallenge", rx_raw.get("rechallenge", "Not stated"), status_str=rx_raw.get("status"), evidence_item=rx_ev),
            ]
            reaction = IcsrReaction(
                adverse_event=str(rx_raw.get("adverse_event", "Not stated")),
                onset_date=str(onset_val),
                outcome=str(rx_raw.get("outcome", "Not stated")),
                seriousness_criteria=crit_list,
                hospitalization=hosp_bool,
                admission_date=adm_date,
                life_threatening=lt_bool,
                death=death_bool,
                disability=disab_bool,
                congenital_anomaly=cong_bool,
                medically_important=med_imp_bool,
                dechallenge=str(rx_raw.get("dechallenge", "Not stated")),
                rechallenge=str(rx_raw.get("rechallenge", "Not stated")),
                facts=rx_facts
            )

            # Concomitant Medications
            concomitant_entries: List[IcsrConcomitantDrug] = []
            concomitant_facts: List[Fact] = []
            for i, c in enumerate(icsr_raw.get("concomitant_drugs", [])):
                if isinstance(c, dict):
                    d_name = c.get("drug_name") or c.get("medication_name") or "Not stated"
                    d_dose = c.get("dose_and_route") or c.get("dose") or "Not stated"
                    d_ind = c.get("indication", "Not stated")
                    d_dates = c.get("dates") or c.get("start_date") or "Not stated"
                    d_status = c.get("status", "Ongoing")
                    c_ev = self._make_evidence(c.get("citation"), source_filename, f"Concomitant Medications Section (Item {i+1})")
                    concomitant_entries.append(IcsrConcomitantDrug(
                        drug_name=str(d_name),
                        dose_and_route=str(d_dose),
                        indication=str(d_ind),
                        dates=str(d_dates),
                        status=str(d_status),
                        evidence=c_ev
                    ))
                    concomitant_facts.append(
                        self._make_fact(f"concomitant_drug_{i+1}", f"{d_name} ({d_dose})", evidence_item=c_ev)
                    )

            # Lab tests
            labs: List[IcsrLabTest] = []
            lab_facts: List[Fact] = []
            for i, lab in enumerate(icsr_raw.get("lab_tests", [])):
                if isinstance(lab, dict):
                    t_name = str(lab.get("test_name", ""))
                    t_val = str(lab.get("value", ""))
                    t_unit = str(lab.get("unit", ""))
                    t_ref = str(lab.get("reference_range", "Not stated"))
                    t_interp = str(lab.get("interpretation", "Not stated"))
                    t_date = str(lab.get("test_date", "Not stated"))
                    lab_ev = self._make_evidence(lab.get("citation"), source_filename, f"Laboratory Data Section ({t_name})")
                    labs.append(IcsrLabTest(
                        test_name=t_name,
                        value=t_val,
                        unit=t_unit,
                        reference_range=t_ref,
                        interpretation=t_interp,
                        test_date=t_date,
                        evidence=lab_ev
                    ))
                    if t_name:
                        lab_facts.append(
                            self._make_fact(f"lab_test_{t_name.lower().replace(' ', '_')}", f"{t_name}: {t_val} {t_unit}", evidence_item=lab_ev)
                        )

            # Regulatory / Manufacturer Metadata
            reg_raw = icsr_raw.get("regulatory", {})
            reg_ev = self._make_evidence(reg_raw.get("citation"), source_filename, "Regulatory Metadata Section")
            mfr_ctrl_val = reg_raw.get("mfr_control_number", "Not stated")
            rcvd_dt_val = reg_raw.get("date_received_by_mfr", "Not stated")
            rpt_type_val = reg_raw.get("report_type", "Initial")

            reg_facts = [
                self._make_fact("mfr_control_number", mfr_ctrl_val, evidence_item=reg_ev),
                self._make_fact("date_received_by_mfr", rcvd_dt_val, evidence_item=reg_ev),
            ]
            regulatory = IcsrRegulatory(
                mfr_control_number=str(mfr_ctrl_val),
                date_received_by_mfr=str(rcvd_dt_val),
                report_type=str(rpt_type_val),
                evidence=reg_ev
            )

            all_icsr_facts = pt_facts + rep_facts + prod_facts + rx_facts + concomitant_facts + lab_facts + reg_facts
            icsr_payload = IcsrPayload(
                patient=patient,
                reporter=reporter,
                product=product,
                reaction=reaction,
                concomitant_drugs=icsr_raw.get("concomitant_drugs", []),
                concomitant_medications=concomitant_entries,
                lab_tests=labs,
                regulatory=regulatory,
                clinical_narrative=str(icsr_raw.get("clinical_narrative", raw_data.get("narrative", "Clinical narrative not stated in source."))),
                facts=all_icsr_facts
            )
            envelope_facts.extend(all_icsr_facts)

        # -------------------------------------------------------------
        # 2. PQC PAYLOAD
        # -------------------------------------------------------------
        if is_pqc and raw_data.get("pqc"):
            pqc_raw = raw_data["pqc"]
            pqc_ev = self._make_evidence(pqc_raw.get("citation"), source_filename, "Quality Complaint Section")
            
            photo_info = pqc_raw.get("photo_evidence") or {}
            photo_detected = bool(photo_info.get("detected", False))
            photo_desc = str(photo_info.get("observation", "Not stated"))

            photo_source_id = source_filename
            photo_page_num = None
            photo_loc_ref = None
            photo_loc_str = "Defect Photo / Exhibit"

            if photo_detected and image_metadata and len(image_metadata) > 0:
                img_meta = next((m for m in image_metadata if m.get("bbox")), image_metadata[0])
                photo_source_id = img_meta.get("source_filename") or source_filename
                photo_page_num = img_meta.get("page_number")
                if photo_page_num:
                    photo_loc_str = f"Page {photo_page_num}, Defect Photograph"
                raw_bbox = img_meta.get("bbox")
                bbox_obj = None
                if raw_bbox:
                    bbox_obj = BoundingBox(
                        x0=float(raw_bbox[0]),
                        y0=float(raw_bbox[1]),
                        x1=float(raw_bbox[2]),
                        y1=float(raw_bbox[3]),
                        page_number=photo_page_num or 1
                    )
                if photo_page_num or bbox_obj:
                    photo_loc_ref = LocationReference(
                        page_number=photo_page_num or 1,
                        section="Defect Photograph",
                        bounding_box=bbox_obj
                    )

            photo_ev = Evidence(
                source_id=photo_source_id,
                source_type=EvidenceType.DEFECT_IMAGE,
                page_or_location=photo_loc_str,
                verbatim_snippet=photo_desc,
                location=photo_loc_ref,
                verification_result=VerificationResult.SUPPORTS if photo_detected else VerificationResult.INSUFFICIENT
            ) if photo_detected else None

            pqc_facts = [
                self._make_fact("pqc_product_name", pqc_raw.get("product_name", "Not stated"), evidence_item=pqc_ev),
                self._make_fact("pqc_lot_number", pqc_raw.get("lot_number", "Not stated"), evidence_item=pqc_ev),
                self._make_fact("pqc_expiry_date", pqc_raw.get("expiry_date", "Not stated"), evidence_item=pqc_ev),
                self._make_fact("pqc_defect_type", pqc_raw.get("defect_type", "Not stated"), evidence_item=pqc_ev),
                self._make_fact("pqc_defect_description", pqc_raw.get("defect_description", "Not stated"), evidence_item=pqc_ev),
                self._make_fact("packaging_breached", str(pqc_raw.get("packaging_breached", False)), normalized_val=pqc_raw.get("packaging_breached", False), evidence_item=pqc_ev),
                self._make_fact("patient_exposure", pqc_raw.get("patient_exposure", "Not stated"), evidence_item=pqc_ev),
                self._make_fact("quarantine_quantity_disposition", pqc_raw.get("quarantine_quantity_disposition", "Not stated"), evidence_item=pqc_ev),
                self._make_fact("pqc_photo_detected", str(photo_detected), normalized_val=photo_detected, evidence_item=photo_ev or pqc_ev),
                self._make_fact("pqc_requires_human_review", str(pqc_raw.get("requires_human_review", False)), normalized_val=pqc_raw.get("requires_human_review", False), evidence_item=photo_ev or pqc_ev),
            ]

            photo_data = PqcPhotoEvidence(
                detected=photo_detected,
                observation=photo_desc,
                interpretation=str(photo_info.get("interpretation", "Quality defect inspection")),
                evidence_ref=photo_ev
            )

            pqc_payload = PqcPayload(
                product_name=str(pqc_raw.get("product_name", "Not stated")),
                lot_number=str(pqc_raw.get("lot_number", "Not stated")),
                expiry_date=str(pqc_raw.get("expiry_date", "Not stated")),
                defect_type=str(pqc_raw.get("defect_type", "Not stated")),
                defect_description=str(pqc_raw.get("defect_description", "Not stated")),
                packaging_breached=bool(pqc_raw.get("packaging_breached", False)),
                patient_exposure=str(pqc_raw.get("patient_exposure", "Not stated")),
                quarantine_quantity_disposition=str(pqc_raw.get("quarantine_quantity_disposition", "Not stated")),
                photo_evidence=photo_data,
                requires_human_review=bool(pqc_raw.get("requires_human_review", False)),
                facts=pqc_facts
            )
            envelope_facts.extend(pqc_facts)

        # -------------------------------------------------------------
        # 3. MI PAYLOAD
        # -------------------------------------------------------------
        if is_mi and raw_data.get("mi"):
            mi_raw = raw_data["mi"]
            mi_cits = mi_raw.get("citations") if isinstance(mi_raw.get("citations"), dict) else {}
            mi_ev = self._make_evidence(mi_raw.get("citation"), source_filename, "Medical Information Section")
            no_ae_bool = bool(mi_raw.get("explicit_no_ae_no_pqc", False))

            prod_ev = self._make_evidence(mi_cits.get("product_or_topic") or mi_cits.get("product"), source_filename, "Inquired Product") or mi_ev
            type_ev = self._make_evidence(mi_cits.get("inquiry_type"), source_filename, "Inquiry Classification") or mi_ev
            q_ev = self._make_evidence(mi_cits.get("question_text"), source_filename, "Inquiry Question") or mi_ev
            ctx_ev = self._make_evidence(mi_cits.get("clinical_context"), source_filename, "Clinical Context") or mi_ev
            req_ev = self._make_evidence(mi_cits.get("information_requested"), source_filename, "Information Requested") or mi_ev

            mi_facts = [
                self._make_fact("mi_product_or_topic", mi_raw.get("product_or_topic", "Not stated"), evidence_item=prod_ev),
                self._make_fact("mi_inquiry_type", mi_raw.get("inquiry_type", "Not stated"), evidence_item=type_ev),
                self._make_fact("mi_question_text", mi_raw.get("question_text", "Not stated"), evidence_item=q_ev),
                self._make_fact("mi_clinical_context", mi_raw.get("clinical_context", "Not stated"), evidence_item=ctx_ev),
                self._make_fact("mi_information_requested", mi_raw.get("information_requested", "Not stated"), evidence_item=req_ev),
                self._make_fact("mi_explicit_no_ae_no_pqc", str(no_ae_bool), normalized_val=no_ae_bool, evidence_item=mi_ev),
            ]

            mi_payload = MiPayload(
                product_or_topic=str(mi_raw.get("product_or_topic", "Not stated")),
                inquiry_type=str(mi_raw.get("inquiry_type", "Not stated")),
                question_text=str(mi_raw.get("question_text", "Not stated")),
                clinical_context=str(mi_raw.get("clinical_context", "Not stated")),
                information_requested=str(mi_raw.get("information_requested", "Not stated")),
                explicit_no_ae_no_pqc=no_ae_bool,
                facts=mi_facts
            )
            envelope_facts.extend(mi_facts)

        # -------------------------------------------------------------
        # 4. NOT RELEVANT PAYLOAD
        # -------------------------------------------------------------
        if is_not_relevant and raw_data.get("not_relevant"):
            nr_raw = raw_data["not_relevant"]
            nr_ev = Evidence(
                source_id=source_filename,
                source_type=EvidenceType.PDF_TEXT if source_filename.lower().endswith(".pdf") else EvidenceType.EMAIL_BODY,
                page_or_location="Header / First paragraph",
                verbatim_snippet=str(nr_raw.get("exclusion_reason", "Non-relevant communication")),
                verification_result=VerificationResult.INSUFFICIENT
            )
            nr_facts = [
                self._make_fact("relevance_determination", str(nr_raw.get("relevance_determination", "Not Relevant")), evidence_item=nr_ev),
                self._make_fact("exclusion_reason", str(nr_raw.get("exclusion_reason", "Not stated")), evidence_item=nr_ev),
            ]
            not_relevant_payload = NotRelevantPayload(
                relevance_determination=str(nr_raw.get("relevance_determination", "Not Relevant")),
                exclusion_reason=str(nr_raw.get("exclusion_reason", "Not stated")),
                facts=nr_facts
            )
            envelope_facts.extend(nr_facts)

        doc_summary = raw_data.get("document_summary") or triage_result.executive_summary or "Document summary extracted from source."
        if doc_summary and doc_summary not in ("Not stated", "") and not doc_summary.startswith("[EXTRACTION WARNING]"):
            from app.services.pdf_summary_validator import validate_and_repair_document_summary
            doc_summary = validate_and_repair_document_summary(
                summary=doc_summary,
                document_context=document_text,
                filename=source_filename
            )
        rev_summary = raw_data.get("reviewer_summary") or f"First-pass review for {triage_result.primary_category.value}."

        return CaseEnvelope(
            envelope_id=f"env-{int(time.time()*1000)%1000000}",
            message_id=message_id,
            source_filename=source_filename,
            language_detected=raw_data.get("language_detected", "English"),
            triage=triage_result,
            document_summary=doc_summary,
            reviewer_summary=rev_summary,
            icsr=icsr_payload,
            pqc=pqc_payload,
            mi=mi_payload,
            not_relevant=not_relevant_payload,
            fact_ledger=envelope_facts,
            reviewer_brief=None,
            processing_time_ms=int((time.time() - start_time) * 1000),
            extraction_status="SUCCESS",
            extraction_error=None,
            metadata={
                "source_filename": source_filename,
                "extraction_status": "SUCCESS"
            }
        )

    def extract_facts(
        self,
        document_text: str,
        triage_result: TriageResult,
        images: Optional[List[Image.Image]] = None,
        source_filename: str = "document"
    ) -> ExtractionResult:
        """
        Legacy compatibility entrypoint.
        Extracts the canonical CaseEnvelope and converts it into ExtractionResult via the legacy adapter.
        """
        envelope = self.extract_envelope(
            document_text=document_text,
            triage_result=triage_result,
            images=images,
            source_filename=source_filename
        )
        return envelope_to_legacy(envelope)

    def summarize_pdf_document(self, pdf_content: str, filename: str) -> str:
        """
        Generates an independent 10-15 sentence regulatory document summary for a secondary PDF
        when multiple PDF attachments are present. Only invoked when multiple PDFs exist.
        """
        if not pdf_content or not pdf_content.strip():
            return f"Document {filename} contains no extractable text."
        prompt = (
            f"Provide a 10 to 15 sentence regulatory document summary for the attached document '{filename}'. "
            f"Characterize the document format, layout, and issuing body. "
            f"State whether the document appears relevant to pharmacovigilance / regulatory evaluation and explain why with concrete domain rationale. "
            f"Detail key clinical or quality findings and explicitly note any data gaps. Maintain source grounding.\n\n"
            f"DOCUMENT CONTENT:\n{pdf_content[:8000]}"
        )
        try:
            from app.core.gemini_client import gemini_client
            res = gemini_client.generate_content(
                contents=prompt,
                system_instruction=EXTRACTION_SYSTEM_INSTRUCTION,
                temperature=0.0
            )
            raw_res = res.strip()
            from app.services.pdf_summary_validator import validate_and_repair_document_summary
            return validate_and_repair_document_summary(
                summary=raw_res,
                document_context=pdf_content,
                filename=filename
            )
        except Exception as e:
            logger.warning(f"Secondary PDF summary generation failed for {filename}: {e}")
            return f"Regulatory document summary for {filename}: Clinical evaluation in progress."

icsr_extractor = ICSRExtractor()

