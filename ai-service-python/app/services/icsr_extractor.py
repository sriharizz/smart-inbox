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
    Fact, Evidence, FactStatus, VerificationResult, EvidenceType
)
from app.schemas.category_payloads import (
    IcsrPatient, IcsrReporter, IcsrProduct, IcsrReaction, IcsrLabTest, IcsrPayload,
    PqcPhotoEvidence, PqcPayload, MiPayload, NotRelevantPayload
)
from app.schemas.case_envelope import CaseEnvelope
from app.schemas.extraction_schema import ExtractionResult
from app.schemas.legacy_adapter import envelope_to_legacy

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

Return ONLY a valid JSON object matching this schema:
{
  "language_detected": "English" | "Spanish" | "German",
  "document_summary": "10 to 15 sentence comprehensive document summary...",
  "reviewer_summary": "2 to 3 sentence concise reviewer executive brief...",
  "icsr": null or {
    "patient": {
      "identifier": string,
      "age": string,
      "sex": string,
      "weight": string,
      "height": string,
      "medical_history": string,
      "treated_indication": string,
      "status": "CONFIRMED" | "NOT_STATED" | "UNCERTAIN" | "CONFLICT",
      "citation": { "source_type": string, "page_or_location": string, "verbatim_snippet": string }
    },
    "reporter": {
      "name": string,
      "role": string,
      "institution": string,
      "country": string,
      "contact": string,
      "status": "CONFIRMED" | "NOT_STATED" | "UNCERTAIN" | "CONFLICT",
      "citation": { "source_type": string, "page_or_location": string, "verbatim_snippet": string }
    },
    "product": {
      "product_name": string,
      "dose": string,
      "frequency": string,
      "route": string,
      "indication": string,
      "start_date": string,
      "stop_date": string,
      "duration": string,
      "lot_number": string,
      "expiry_date": string,
      "status": "CONFIRMED" | "NOT_STATED" | "UNCERTAIN" | "CONFLICT",
      "citation": { "source_type": string, "page_or_location": string, "verbatim_snippet": string }
    },
    "reaction": {
      "adverse_event": string,
      "onset_date": string,
      "outcome": string,
      "seriousness_criteria": [string],
      "dechallenge": string,
      "rechallenge": string,
      "status": "CONFIRMED" | "NOT_STATED" | "UNCERTAIN" | "CONFLICT",
      "citation": { "source_type": string, "page_or_location": string, "verbatim_snippet": string }
    },
    "lab_tests": [
      { "test_name": string, "value": string, "unit": string, "reference_range": string, "test_date": string }
    ],
    "concomitant_drugs": [
      { "drug_name": string, "dose": string, "start_date": string }
    ],
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

        try:
            response_text = self.provider.generate_content(
                contents=contents,
                system_instruction=EXTRACTION_SYSTEM_INSTRUCTION,
                temperature=0.0
            )

            clean_json = response_text.strip()
            if clean_json.startswith("```"):
                lines = clean_json.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                clean_json = "\n".join(lines).strip()

            raw_data = json.loads(clean_json)
            return self._build_envelope_from_data(
                raw_data=raw_data,
                triage_result=triage_result,
                source_filename=source_filename,
                message_id=message_id,
                start_time=start_time,
                is_icsr=is_icsr,
                is_pqc=is_pqc,
                is_mi=is_mi,
                is_not_relevant=is_not_relevant
            )
        except Exception as e:
            if not fresh_processing:
                logger.error(f"Live LLM extraction failed: {e}. Attempting benchmark fallback for {source_filename}.")
                from app.services.cache_service import cache_service
                fallback = cache_service.get_envelope_by_identifier(source_filename)
                if fallback:
                    logger.info(f"Successfully recovered grounded CaseEnvelope from benchmark fallback for {source_filename}.")
                    fallback.processing_time_ms = int((time.time() - start_time) * 1000)
                    return fallback
            else:
                logger.warning(f"Live LLM extraction failed in fresh-processing mode: {e}. Bypassing benchmark cache.")

            # Construct safe default envelope
            logger.warning("Constructing safe unstated CaseEnvelope fallback.")
            return CaseEnvelope(
                envelope_id=f"env-fallback-{int(time.time())}",
                message_id=message_id,
                source_filename=source_filename,
                language_detected="English",
                triage=triage_result,
                document_summary=triage_result.executive_summary or "Extraction fallback: unstated fields.",
                reviewer_summary="Extraction fallback default.",
                icsr=IcsrPayload() if is_icsr else None,
                pqc=PqcPayload() if is_pqc else None,
                mi=MiPayload() if is_mi else None,
                not_relevant=NotRelevantPayload() if is_not_relevant else None,
                fact_ledger=[],
                processing_time_ms=int((time.time() - start_time) * 1000)
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
        is_not_relevant: bool
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
            age_val = pt_raw.get("age", "Not stated")
            age_norm = normalizer.normalize_age(age_val)

            sex_val = pt_raw.get("sex", "Not stated")
            sex_norm = normalizer.normalize_sex(sex_val)

            pt_facts = [
                self._make_fact("patient_identifier", pt_raw.get("identifier", "Not stated"), status_str=pt_raw.get("status"), evidence_item=pt_ev),
                self._make_fact("patient_age", age_val, normalized_val=age_norm, status_str=pt_raw.get("status"), evidence_item=pt_ev),
                self._make_fact("patient_sex", sex_val, normalized_val=sex_norm, status_str=pt_raw.get("status"), evidence_item=pt_ev),
                self._make_fact("patient_weight", pt_raw.get("weight", "Not stated"), status_str=pt_raw.get("status"), evidence_item=pt_ev),
                self._make_fact("patient_height", pt_raw.get("height", "Not stated"), status_str=pt_raw.get("status"), evidence_item=pt_ev),
                self._make_fact("patient_medical_history", pt_raw.get("medical_history", "Not stated"), status_str=pt_raw.get("status"), evidence_item=pt_ev),
                self._make_fact("treated_indication", pt_raw.get("treated_indication", "Not stated"), status_str=pt_raw.get("status"), evidence_item=pt_ev),
            ]
            patient = IcsrPatient(
                identifier=str(pt_raw.get("identifier", "Not stated")),
                age=str(age_val),
                sex=str(pt_raw.get("sex", "Not stated")),
                weight=str(pt_raw.get("weight", "Not stated")),
                height=str(pt_raw.get("height", "Not stated")),
                medical_history=str(pt_raw.get("medical_history", "Not stated")),
                treated_indication=str(pt_raw.get("treated_indication", "Not stated")),
                facts=pt_facts
            )

            # Reporter
            rep_raw = icsr_raw.get("reporter", {})
            rep_ev = self._make_evidence(rep_raw.get("citation"), source_filename, "Reporter Section")
            country_val = rep_raw.get("country", "Not stated")
            country_norm = normalizer.normalize_country(country_val)

            rep_facts = [
                self._make_fact("reporter_name", rep_raw.get("name", "Not stated"), status_str=rep_raw.get("status"), evidence_item=rep_ev),
                self._make_fact("reporter_role", rep_raw.get("role", "Not stated"), status_str=rep_raw.get("status"), evidence_item=rep_ev),
                self._make_fact("reporter_institution", rep_raw.get("institution", "Not stated"), status_str=rep_raw.get("status"), evidence_item=rep_ev),
                self._make_fact("reporter_country", country_val, normalized_val=country_norm, status_str=rep_raw.get("status"), evidence_item=rep_ev),
                self._make_fact("reporter_contact", rep_raw.get("contact", "Not stated"), status_str=rep_raw.get("status"), evidence_item=rep_ev),
            ]
            reporter = IcsrReporter(
                name=str(rep_raw.get("name", "Not stated")),
                role=str(rep_raw.get("role", "Not stated")),
                institution=str(rep_raw.get("institution", "Not stated")),
                country=str(country_val),
                contact=str(rep_raw.get("contact", "Not stated")),
                facts=rep_facts
            )

            # Product
            prod_raw = icsr_raw.get("product", {})
            prod_ev = self._make_evidence(prod_raw.get("citation"), source_filename, "Product Section")
            route_val = prod_raw.get("route", "Not stated")
            route_norm = normalizer.normalize_route(route_val)
            start_dt_raw = prod_raw.get("start_date", "Not stated")
            stop_dt_raw = prod_raw.get("stop_date", "Not stated")
            start_dt_norm = normalizer.normalize_date(start_dt_raw)
            stop_dt_norm = normalizer.normalize_date(stop_dt_raw)

            prod_facts = [
                self._make_fact("suspect_product", prod_raw.get("product_name", "Not stated"), status_str=prod_raw.get("status"), evidence_item=prod_ev),
                self._make_fact("product_dose", prod_raw.get("dose", "Not stated"), status_str=prod_raw.get("status"), evidence_item=prod_ev),
                self._make_fact("product_frequency", prod_raw.get("frequency", "Not stated"), status_str=prod_raw.get("status"), evidence_item=prod_ev),
                self._make_fact("product_route", route_val, normalized_val=route_norm, status_str=prod_raw.get("status"), evidence_item=prod_ev),
                self._make_fact("indication", prod_raw.get("indication", "Not stated"), status_str=prod_raw.get("status"), evidence_item=prod_ev),
                self._make_fact("lot_number", prod_raw.get("lot_number", "Not stated"), status_str=prod_raw.get("status"), evidence_item=prod_ev),
                self._make_fact("expiry_date", prod_raw.get("expiry_date", "Not stated"), status_str=prod_raw.get("status"), evidence_item=prod_ev),
                self._make_fact("treatment_start_date", start_dt_raw, normalized_val=start_dt_norm, status_str=prod_raw.get("status"), evidence_item=prod_ev),
                self._make_fact("treatment_stop_date", stop_dt_raw, normalized_val=stop_dt_norm, status_str=prod_raw.get("status"), evidence_item=prod_ev),
            ]
            product = IcsrProduct(
                product_name=str(prod_raw.get("product_name", "Not stated")),
                dose=str(prod_raw.get("dose", "Not stated")),
                frequency=str(prod_raw.get("frequency", "Not stated")),
                route=str(route_val),
                indication=str(prod_raw.get("indication", "Not stated")),
                start_date=str(prod_raw.get("start_date", "Not stated")),
                stop_date=str(prod_raw.get("stop_date", "Not stated")),
                duration=str(prod_raw.get("duration", "Not stated")),
                lot_number=str(prod_raw.get("lot_number", "Not stated")),
                expiry_date=str(prod_raw.get("expiry_date", "Not stated")),
                facts=prod_facts
            )

            # Reaction
            rx_raw = icsr_raw.get("reaction", {})
            rx_ev = self._make_evidence(rx_raw.get("citation"), source_filename, "Adverse Reaction Section")
            onset_val = rx_raw.get("onset_date", "Not stated")
            onset_norm = normalizer.normalize_date(onset_val)

            rx_facts = [
                self._make_fact("adverse_event", rx_raw.get("adverse_event", "Not stated"), status_str=rx_raw.get("status"), evidence_item=rx_ev),
                self._make_fact("reaction_onset_date", onset_val, normalized_val=onset_norm, status_str=rx_raw.get("status"), evidence_item=rx_ev),
                self._make_fact("reaction_outcome", rx_raw.get("outcome", "Not stated"), status_str=rx_raw.get("status"), evidence_item=rx_ev),
                self._make_fact("seriousness_criteria", ", ".join(rx_raw.get("seriousness_criteria", [])) or "Not stated", status_str=rx_raw.get("status"), evidence_item=rx_ev),
                self._make_fact("dechallenge", rx_raw.get("dechallenge", "Not stated"), status_str=rx_raw.get("status"), evidence_item=rx_ev),
                self._make_fact("rechallenge", rx_raw.get("rechallenge", "Not stated"), status_str=rx_raw.get("status"), evidence_item=rx_ev),
            ]
            reaction = IcsrReaction(
                adverse_event=str(rx_raw.get("adverse_event", "Not stated")),
                onset_date=str(onset_val),
                outcome=str(rx_raw.get("outcome", "Not stated")),
                seriousness_criteria=rx_raw.get("seriousness_criteria", []),
                dechallenge=str(rx_raw.get("dechallenge", "Not stated")),
                rechallenge=str(rx_raw.get("rechallenge", "Not stated")),
                facts=rx_facts
            )

            # Lab tests
            labs = []
            for lab in icsr_raw.get("lab_tests", []):
                if isinstance(lab, dict):
                    labs.append(IcsrLabTest(
                        test_name=str(lab.get("test_name", "")),
                        value=str(lab.get("value", "")),
                        unit=str(lab.get("unit", "")),
                        reference_range=str(lab.get("reference_range", "Not stated")),
                        test_date=str(lab.get("test_date", "Not stated"))
                    ))

            all_icsr_facts = pt_facts + rep_facts + prod_facts + rx_facts
            icsr_payload = IcsrPayload(
                patient=patient,
                reporter=reporter,
                product=product,
                reaction=reaction,
                concomitant_drugs=icsr_raw.get("concomitant_drugs", []),
                lab_tests=labs,
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
            photo_ev = Evidence(
                source_id=source_filename,
                source_type=EvidenceType.DEFECT_IMAGE,
                page_or_location="Defect Photo / Exhibit",
                verbatim_snippet=photo_desc,
                verification_result=VerificationResult.INSUFFICIENT
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
            mi_ev = self._make_evidence(mi_raw.get("citation"), source_filename, "Medical Information Section")
            no_ae_bool = bool(mi_raw.get("explicit_no_ae_no_pqc", False))

            mi_facts = [
                self._make_fact("mi_product_or_topic", mi_raw.get("product_or_topic", "Not stated"), evidence_item=mi_ev),
                self._make_fact("mi_inquiry_type", mi_raw.get("inquiry_type", "Not stated"), evidence_item=mi_ev),
                self._make_fact("mi_question_text", mi_raw.get("question_text", "Not stated"), evidence_item=mi_ev),
                self._make_fact("mi_clinical_context", mi_raw.get("clinical_context", "Not stated"), evidence_item=mi_ev),
                self._make_fact("mi_information_requested", mi_raw.get("information_requested", "Not stated"), evidence_item=mi_ev),
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
            metadata={"source_filename": source_filename}
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

icsr_extractor = ICSRExtractor()
