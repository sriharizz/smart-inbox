import re
from typing import Optional, List, Dict, Any
from app.schemas.case_envelope import CaseEnvelope
from app.schemas.fact_contract import Fact, Evidence, FactStatus, VerificationResult, EvidenceType
from app.schemas.extraction_schema import (
    ExtractionResult,
    PatientData,
    ReporterData,
    ProductData,
    ReactionData,
    LabTestItem,
    ConcomitantMedicationItem,
    RegulatoryMetadata,
    QualityComplaintData,
    MedicalInfoData,
    SourceCitation,
    AttachmentMetadata,
)
from app.schemas.category_payloads import (
    IcsrPatient,
    IcsrReporter,
    IcsrProduct,
    IcsrReaction,
    IcsrLabTest,
    IcsrPayload,
    PqcPhotoEvidence,
    PqcPayload,
    MiPayload,
    NotRelevantPayload,
)

def select_best_evidence(
    evidence_list: Optional[List[Evidence]], 
    fact: Optional[Fact] = None
) -> Optional[Evidence]:
    """
    Selects the highest-fidelity, most reliable Evidence object for a given Fact or category.
    Prioritizes semantically supported, precise visual/located citations over coarse snippets,
    while guaranteeing that evidence is only selected if it genuinely supports the fact.
    """
    if not evidence_list:
        return None

    # Filter out candidates with explicit contradiction
    valid_candidates = [ev for ev in evidence_list if ev and ev.verification_result != VerificationResult.CONTRADICTS]
    if not valid_candidates:
        return None

    if len(valid_candidates) == 1:
        return valid_candidates[0]

    def _score(ev: Evidence) -> float:
        snippet_lower = (ev.verbatim_snippet or "").lower()
        fact_val_lower = str(fact.value).strip().lower() if fact and fact.value else ""

        # 1. Semantic Grounding / Support Check
        is_grounded = False
        if not fact_val_lower or fact_val_lower in ("not stated", "unknown", "none"):
            # For unstated facts, snippet presence is not required
            is_grounded = True
        else:
            # Check for exact substring match
            if fact_val_lower in snippet_lower:
                is_grounded = True
            else:
                # Token / numeric matching
                digits = re.findall(r"\d+", fact_val_lower)
                if digits and any(d in snippet_lower for d in digits if len(d) >= 2):
                    is_grounded = True
                else:
                    words = [w for w in re.split(r"[^\w]+", fact_val_lower) if len(w) >= 3]
                    if words and any(w in snippet_lower for w in words):
                        is_grounded = True

        # Verification result evaluation
        is_verified_support = (ev.verification_result == VerificationResult.SUPPORTS)
        if is_verified_support:
            is_grounded = True

        # Heavy penalty if candidate does NOT support the fact (do not select PDF merely because it's a PDF)
        if not is_grounded:
            return -500.0

        score = 0.0

        # Verification bonus
        if is_verified_support:
            score += 50.0
            if ev.verification_confidence > 0:
                score += ev.verification_confidence * 20.0
        elif ev.verification_result == VerificationResult.INSUFFICIENT:
            score += 10.0

        # 2. Location Precision / Anchor Hierarchy
        st_val = ev.source_type.value if hasattr(ev.source_type, "value") else str(ev.source_type)
        is_visual = any(t in st_val.lower() for t in ("pdf", "scanned", "image"))

        has_bbox = (
            ev.location is not None
            and ev.location.bounding_box is not None
            and ev.location.page_number is not None
        )
        has_char_span = (
            ev.location is not None
            and ev.location.char_start is not None
            and ev.location.char_end is not None
            and ev.location.char_end > ev.location.char_start
        )
        has_page = (
            ev.location is not None
            and ev.location.page_number is not None
        )

        if has_bbox and is_visual:
            score += 100.0  # Level 1 Exact Visual Anchor (PDF bounding box)
        elif has_char_span and not is_visual:
            score += 80.0   # Level 1 Exact Visual Anchor (Email character range)
        elif has_page and is_visual:
            score += 40.0   # Level 2 Page-level Anchor
        elif ev.location and ev.location.section:
            score += 20.0   # Section reference
        else:
            score += 5.0    # Level 3 Snippet Only

        # Retrieval relevance score tie-breaker
        if ev.retrieval_metadata:
            rel = ev.retrieval_metadata.get("relevance_score")
            if isinstance(rel, (int, float)):
                score += float(rel) * 10.0

        return score

    # Sort descending by score; stable sort preserves original order on ties
    scored = sorted(valid_candidates, key=_score, reverse=True)
    best = scored[0]

    # If even the best candidate scored negative (completely ungrounded),
    # fallback to the original candidate rather than losing evidence
    if _score(best) < 0:
        return valid_candidates[0]

    return best

def _make_source_citation(ev: Optional[Evidence]) -> SourceCitation:
    if not ev:
        return SourceCitation()
    
    st_val = (ev.source_type.value if hasattr(ev.source_type, "value") else str(ev.source_type)).lower()
    if "image" in st_val:
        st = "image"
    elif "pdf" in st_val or "scanned" in st_val or "table" in st_val or (ev.source_id and str(ev.source_id).lower().endswith(".pdf")):
        st = "pdf"
    else:
        st = "email"

    page_num = ev.location.page_number if ev.location else None
    bbox_dict = None
    if ev.location and ev.location.bounding_box:
        bbox = ev.location.bounding_box
        bbox_dict = {
            "x0": bbox.x0,
            "y0": bbox.y0,
            "x1": bbox.x1,
            "y1": bbox.y1,
            "page_number": bbox.page_number
        }
        if not page_num:
            page_num = bbox.page_number

    char_start = ev.location.char_start if ev.location else None
    char_end = ev.location.char_end if ev.location else None

    # Determine honest anchor level:
    # Level 1: reliable page and bounding box
    # Level 2: page known or email passage with char range
    # Level 3: snippet only
    if bbox_dict and st in ("pdf", "image"):
        anchor_level = "LEVEL_1_EXACT_VISUAL"
    elif st == "email" and char_start is not None and char_end is not None:
        anchor_level = "LEVEL_1_EXACT_VISUAL"
    elif page_num is not None:
        anchor_level = "LEVEL_2_PAGE_TEXT"
    else:
        anchor_level = "LEVEL_3_SNIPPET_ONLY"

    verif_res = ev.verification_result.value if hasattr(ev.verification_result, "value") else str(ev.verification_result)

    return SourceCitation(
        source_type=st,
        page_or_location=ev.page_or_location,
        verbatim_snippet=ev.verbatim_snippet,
        source_id=ev.source_id,
        source_name=ev.source_id,
        page_number=page_num,
        bounding_box=bbox_dict,
        char_start=char_start,
        char_end=char_end,
        anchor_level=anchor_level,
        verification_result=verif_res,
        verification_rationale=ev.verification_rationale
    )

def envelope_to_legacy(envelope: CaseEnvelope) -> ExtractionResult:
    """
    Thin, clearly identifiable backward-compatibility adapter.
    Converts a canonical CaseEnvelope into the legacy ExtractionResult shape.
    """
    triage = envelope.triage

    # 1. Patient Data
    patient = PatientData()
    if envelope.icsr and envelope.icsr.patient:
        pt = envelope.icsr.patient
        patient.identifier = pt.identifier
        patient.dob = pt.dob
        patient.age = pt.age
        patient.sex = pt.sex
        patient.weight = pt.weight
        patient.country = pt.patient_country
        patient.medical_history = pt.medical_history
        
        all_pt_ev = [ev for f in pt.facts for ev in f.evidence] if pt.facts else []
        best_pt_ev = select_best_evidence(all_pt_ev)
        if best_pt_ev:
            patient.citation = _make_source_citation(best_pt_ev)

    # 2. Reporter Data
    reporter = ReporterData()
    if envelope.icsr and envelope.icsr.reporter:
        rep = envelope.icsr.reporter
        reporter.name = rep.name
        reporter.role = rep.role
        reporter.specialty = rep.specialty
        reporter.institution = rep.institution
        reporter.country = rep.country
        reporter.email_or_phone = rep.contact
        reporter.health_professional = rep.health_professional
        
        all_rep_ev = [ev for f in rep.facts for ev in f.evidence] if rep.facts else []
        best_rep_ev = select_best_evidence(all_rep_ev)
        if best_rep_ev:
            reporter.citation = _make_source_citation(best_rep_ev)

    # 3. Product Data
    product = ProductData()
    if envelope.icsr and envelope.icsr.product:
        pr = envelope.icsr.product
        product.product_name = pr.product_name
        product.formulation = pr.formulation
        product.dose = pr.dose
        product.frequency = pr.frequency
        product.route = pr.route
        product.lot_number = pr.lot_number
        product.expiry_date = pr.expiry_date
        product.indication = pr.indication if pr.indication != "Not stated" else (
            envelope.icsr.patient.treated_indication if envelope.icsr.patient else "Not stated"
        )
        product.start_date = pr.start_date
        product.stop_date = pr.stop_date
        product.duration = pr.duration
        product.action_taken = pr.action_taken
        
        all_pr_ev = [ev for f in pr.facts for ev in f.evidence] if pr.facts else []
        best_pr_ev = select_best_evidence(all_pr_ev)
        if best_pr_ev:
            product.citation = _make_source_citation(best_pr_ev)

    # 4. Reaction Data
    reaction = ReactionData()
    if envelope.icsr and envelope.icsr.reaction:
        rx = envelope.icsr.reaction
        reaction.adverse_event = rx.adverse_event
        reaction.onset_date = rx.onset_date
        reaction.outcome = rx.outcome
        reaction.seriousness_criteria = rx.seriousness_criteria
        reaction.hospitalization = rx.hospitalization
        reaction.admission_date = rx.admission_date
        reaction.life_threatening = rx.life_threatening
        reaction.death = rx.death
        reaction.disability = rx.disability
        reaction.congenital_anomaly = rx.congenital_anomaly
        reaction.medically_important = rx.medically_important
        reaction.dechallenge = rx.dechallenge
        reaction.rechallenge = rx.rechallenge
        
        all_rx_ev = [ev for f in rx.facts for ev in f.evidence] if rx.facts else []
        best_rx_ev = select_best_evidence(all_rx_ev)
        if best_rx_ev:
            reaction.citation = _make_source_citation(best_rx_ev)

    # 5. Lab Tests
    labs: List[LabTestItem] = []
    if envelope.icsr and envelope.icsr.lab_tests:
        for lt in envelope.icsr.lab_tests:
            matching_fact = None
            if envelope.fact_ledger:
                matching_fact = next(
                    (f for f in envelope.fact_ledger if f.field.startswith("lab_test_") and lt.test_name.lower() in f.field),
                    None
                )
            selected_ev = select_best_evidence(matching_fact.evidence, matching_fact) if matching_fact and matching_fact.evidence else lt.evidence
            labs.append(LabTestItem(
                test_name=lt.test_name,
                value=lt.value,
                unit=lt.unit,
                reference_range=lt.reference_range,
                interpretation=lt.interpretation,
                test_date=lt.test_date,
                citation=_make_source_citation(selected_ev) if selected_ev else None
            ))

    # 6. Concomitant Medications
    concomitants: List[ConcomitantMedicationItem] = []
    if envelope.icsr and envelope.icsr.concomitant_medications:
        for c in envelope.icsr.concomitant_medications:
            concomitants.append(ConcomitantMedicationItem(
                medication_name=c.drug_name,
                dose_and_route=c.dose_and_route,
                indication=c.indication,
                dates=c.dates,
                status=c.status,
                citation=_make_source_citation(c.evidence) if c.evidence else None
            ))

    # 7. Regulatory Metadata
    reg_data: Optional[RegulatoryMetadata] = None
    if envelope.icsr and envelope.icsr.regulatory:
        reg = envelope.icsr.regulatory
        reg_data = RegulatoryMetadata(
            mfr_control_number=reg.mfr_control_number,
            date_received_by_mfr=reg.date_received_by_mfr,
            report_type=reg.report_type,
            citation=_make_source_citation(reg.evidence) if reg.evidence else None
        )

    # 8. Quality Complaint Data
    qc_data: Optional[QualityComplaintData] = None
    if envelope.pqc:
        pqc = envelope.pqc
        all_pqc_ev = [ev for f in pqc.facts for ev in f.evidence] if pqc.facts else []
        best_pqc_ev = select_best_evidence(all_pqc_ev)
        
        qc_data = QualityComplaintData(
            product_name=pqc.product_name,
            lot_number=pqc.lot_number,
            defect_type=pqc.defect_type,
            defect_description=pqc.defect_description,
            packaging_breached=pqc.packaging_breached,
            photo_detected=pqc.photo_evidence.detected if pqc.photo_evidence else False,
            photo_description=pqc.photo_evidence.observation if pqc.photo_evidence else "Not stated",
            requires_human_review=pqc.requires_human_review,
            citation=_make_source_citation(best_pqc_ev)
        )

    # 9. Medical Info Data
    mi_data: Optional[MedicalInfoData] = None
    if envelope.mi:
        mi = envelope.mi
        all_mi_ev = [ev for f in mi.facts for ev in f.evidence] if mi.facts else []
        best_mi_ev = select_best_evidence(all_mi_ev)
        
        mi_data = MedicalInfoData(
            product_or_topic=mi.product_or_topic,
            inquiry_type=mi.inquiry_type,
            question_text=mi.question_text,
            citation=_make_source_citation(best_mi_ev)
        )

    # 10. Clinical Narrative / Document Summary
    narrative = "Not stated"
    if envelope.icsr and envelope.icsr.clinical_narrative not in ("Not stated", ""):
        narrative = envelope.icsr.clinical_narrative
    elif envelope.document_summary not in ("Not stated", ""):
        narrative = envelope.document_summary
    elif envelope.reviewer_summary not in ("Not stated", ""):
        narrative = envelope.reviewer_summary

    case_id = envelope.metadata.get("case_id")

    # 11. Fact-Level Citations Map
    citations_dict: Dict[str, SourceCitation] = {}
    all_facts_to_index = list(envelope.fact_ledger or [])
    if envelope.mi and envelope.mi.facts:
        for mf in envelope.mi.facts:
            if mf not in all_facts_to_index:
                all_facts_to_index.append(mf)

    for f in all_facts_to_index:
        if f.evidence:
            best_ev = select_best_evidence(f.evidence, f)
            if best_ev:
                citation = _make_source_citation(best_ev)
                citations_dict[f.field] = citation
                # Canonical aliases for common consumer field variations
                if f.field == "lot_number":
                    citations_dict["product_lot"] = citation
                elif f.field == "suspect_product":
                    citations_dict["product_name"] = citation
                elif f.field == "adverse_event":
                    citations_dict["reaction"] = citation
                elif f.field in ("pqc_photo_detected", "pqc_requires_human_review") and citation.source_type == "image":
                    citations_dict["defect_photo"] = citation
                    citations_dict["photo_evidence"] = citation
                elif f.field == "mi_product_or_topic":
                    citations_dict["miProduct"] = citation
                    citations_dict["product_or_topic"] = citation
                    citations_dict["product_name"] = citation
                    citations_dict["mi_product"] = citation
                    citations_dict["product"] = citation
                elif f.field == "mi_inquiry_type":
                    citations_dict["inquiryType"] = citation
                    citations_dict["inquiry_type"] = citation
                elif f.field == "mi_question_text":
                    citations_dict["inquirySummary"] = citation
                    citations_dict["inquiry_summary"] = citation
                    citations_dict["question_text"] = citation
                    citations_dict["questionText"] = citation
                    citations_dict["question"] = citation
                elif f.field == "mi_clinical_context":
                    citations_dict["clinicalContext"] = citation
                    citations_dict["clinical_context"] = citation
                elif f.field == "mi_information_requested":
                    citations_dict["informationRequested"] = citation
                    citations_dict["information_requested"] = citation
                elif f.field.startswith("mi_question_"):
                    suffix = f.field.replace("mi_question_", "")
                    citations_dict[f"question_{suffix}"] = citation
                    citations_dict[f"question-{suffix}"] = citation

    if envelope.pqc and envelope.pqc.photo_evidence and envelope.pqc.photo_evidence.evidence_ref:
        photo_cit = _make_source_citation(envelope.pqc.photo_evidence.evidence_ref)
        citations_dict["defect_photo"] = photo_cit
        citations_dict["photo_evidence"] = photo_cit

    if envelope.mi:
        all_mi_ev = [ev for f in envelope.mi.facts for ev in f.evidence] if envelope.mi.facts else []
        best_mi_ev = select_best_evidence(all_mi_ev)
        if best_mi_ev:
            mi_sec_cit = _make_source_citation(best_mi_ev)
            citations_dict["medical_info"] = mi_sec_cit
            citations_dict["mi"] = mi_sec_cit

    raw_att_meta = envelope.metadata.get("attachment_metadata", [])
    attachment_metadata = [
        AttachmentMetadata(
            filename=m.get("filename", ""),
            flavor=m.get("flavor", "digital_form"),
            language=m.get("language", "English"),
            document_summary=m.get("document_summary")
        )
        for m in raw_att_meta
    ]

    return ExtractionResult(
        case_id=case_id,
        source_filename=envelope.source_filename,
        language_detected=envelope.language_detected,
        triage=triage,
        patient=patient,
        reporter=reporter,
        product=product,
        reaction=reaction,
        lab_tests=labs,
        concomitant_medications=concomitants,
        regulatory=reg_data,
        quality_complaint=qc_data,
        medical_info=mi_data,
        narrative=narrative,
        processing_time_ms=envelope.processing_time_ms,
        extraction_status=getattr(envelope, "extraction_status", "SUCCESS"),
        extraction_error=getattr(envelope, "extraction_error", None),
        citations=citations_dict,
        attachment_metadata=attachment_metadata,
        document_summary=getattr(envelope, "document_summary", None),
        envelope=envelope
    )

