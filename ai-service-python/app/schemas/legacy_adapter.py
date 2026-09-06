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
    QualityComplaintData,
    MedicalInfoData,
    SourceCitation,
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
        patient.age = pt.age
        patient.sex = pt.sex
        patient.weight = pt.weight
        patient.medical_history = pt.medical_history
        
        pt_ev = next((f.evidence[0] for f in pt.facts if f.evidence), None)
        if pt_ev:
            st = "pdf" if "pdf" in pt_ev.source_type.value else "email"
            patient.citation = SourceCitation(
                source_type=st,
                page_or_location=pt_ev.page_or_location,
                verbatim_snippet=pt_ev.verbatim_snippet
            )

    # 2. Reporter Data
    reporter = ReporterData()
    if envelope.icsr and envelope.icsr.reporter:
        rep = envelope.icsr.reporter
        reporter.name = rep.name
        reporter.role = rep.role
        reporter.institution = rep.institution
        reporter.country = rep.country
        reporter.email_or_phone = rep.contact
        
        rep_ev = next((f.evidence[0] for f in rep.facts if f.evidence), None)
        if rep_ev:
            st = "pdf" if "pdf" in rep_ev.source_type.value else "email"
            reporter.citation = SourceCitation(
                source_type=st,
                page_or_location=rep_ev.page_or_location,
                verbatim_snippet=rep_ev.verbatim_snippet
            )

    # 3. Product Data
    product = ProductData()
    if envelope.icsr and envelope.icsr.product:
        pr = envelope.icsr.product
        product.product_name = pr.product_name
        product.dose = pr.dose
        product.frequency = pr.frequency
        product.route = pr.route
        product.lot_number = pr.lot_number
        product.expiry_date = pr.expiry_date
        product.indication = pr.indication if pr.indication != "Not stated" else (
            envelope.icsr.patient.treated_indication if envelope.icsr.patient else "Not stated"
        )
        
        prod_ev = next((f.evidence[0] for f in pr.facts if f.evidence), None)
        if prod_ev:
            st = "pdf" if "pdf" in prod_ev.source_type.value else "email"
            product.citation = SourceCitation(
                source_type=st,
                page_or_location=prod_ev.page_or_location,
                verbatim_snippet=prod_ev.verbatim_snippet
            )

    # 4. Reaction Data
    reaction = ReactionData()
    if envelope.icsr and envelope.icsr.reaction:
        rx = envelope.icsr.reaction
        reaction.adverse_event = rx.adverse_event
        reaction.onset_date = rx.onset_date
        reaction.outcome = rx.outcome
        reaction.seriousness_criteria = rx.seriousness_criteria
        reaction.dechallenge = rx.dechallenge
        reaction.rechallenge = rx.rechallenge
        
        rx_ev = next((f.evidence[0] for f in rx.facts if f.evidence), None)
        if rx_ev:
            st = "pdf" if "pdf" in rx_ev.source_type.value else "email"
            reaction.citation = SourceCitation(
                source_type=st,
                page_or_location=rx_ev.page_or_location,
                verbatim_snippet=rx_ev.verbatim_snippet
            )

    # 5. Lab Tests
    labs: List[LabTestItem] = []
    if envelope.icsr and envelope.icsr.lab_tests:
        for lt in envelope.icsr.lab_tests:
            labs.append(LabTestItem(
                test_name=lt.test_name,
                value=lt.value,
                unit=lt.unit,
                reference_range=lt.reference_range,
                test_date=lt.test_date
            ))

    # 6. Quality Complaint Data
    qc_data: Optional[QualityComplaintData] = None
    if envelope.pqc:
        pqc = envelope.pqc
        pqc_ev = next((f.evidence[0] for f in pqc.facts if f.evidence), None)
        st = "pdf" if (pqc_ev and "pdf" in pqc_ev.source_type.value) else "email"
        
        qc_data = QualityComplaintData(
            product_name=pqc.product_name,
            lot_number=pqc.lot_number,
            defect_type=pqc.defect_type,
            defect_description=pqc.defect_description,
            packaging_breached=pqc.packaging_breached,
            photo_detected=pqc.photo_evidence.detected if pqc.photo_evidence else False,
            photo_description=pqc.photo_evidence.observation if pqc.photo_evidence else "Not stated",
            requires_human_review=pqc.requires_human_review,
            citation=SourceCitation(
                source_type=st,
                page_or_location=pqc_ev.page_or_location if pqc_ev else "Quality defect block",
                verbatim_snippet=pqc_ev.verbatim_snippet if pqc_ev else "Not stated"
            )
        )

    # 7. Medical Info Data
    mi_data: Optional[MedicalInfoData] = None
    if envelope.mi:
        mi = envelope.mi
        mi_ev = next((f.evidence[0] for f in mi.facts if f.evidence), None)
        st = "pdf" if (mi_ev and "pdf" in mi_ev.source_type.value) else "email"
        
        mi_data = MedicalInfoData(
            product_or_topic=mi.product_or_topic,
            inquiry_type=mi.inquiry_type,
            question_text=mi.question_text,
            citation=SourceCitation(
                source_type=st,
                page_or_location=mi_ev.page_or_location if mi_ev else "Medical information block",
                verbatim_snippet=mi_ev.verbatim_snippet if mi_ev else "Not stated"
            )
        )

    # 8. Clinical Narrative / Document Summary
    narrative = "Not stated"
    if envelope.icsr and envelope.icsr.clinical_narrative not in ("Not stated", ""):
        narrative = envelope.icsr.clinical_narrative
    elif envelope.document_summary not in ("Not stated", ""):
        narrative = envelope.document_summary
    elif envelope.reviewer_summary not in ("Not stated", ""):
        narrative = envelope.reviewer_summary

    case_id = envelope.metadata.get("case_id")

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
        quality_complaint=qc_data,
        medical_info=mi_data,
        narrative=narrative,
        processing_time_ms=envelope.processing_time_ms,
        envelope=envelope
    )
