import json
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.fact_contract import (
    FactStatus, VerificationResult, EvidenceType, Fact, Evidence
)
from app.schemas.category_payloads import (
    IcsrPayload, PqcPayload, MiPayload, NotRelevantPayload
)
from app.schemas.case_envelope import CaseEnvelope
from app.schemas.triage_schema import TriageResult, TriageLabel, CategoryEnum
from app.schemas.legacy_adapter import envelope_to_legacy
from app.services.icsr_extractor import icsr_extractor
from app.services.orchestrator import orchestrator
from app.services.cache_service import cache_service
from app.core.normalizer import normalizer

client = TestClient(app)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
TEST_DATA_DIR = BASE_DIR / "test-data"

# -------------------------------------------------------------
# 1. Category-Aware Decoupled Extraction Tests
# -------------------------------------------------------------

def test_icsr_extraction_populates_icsr_payload_only():
    """ICSR triage category strictly populates IcsrPayload without manufacturing PQC or MI."""
    envelope = cache_service.get_envelope_by_identifier("email_01.eml")
    assert envelope is not None
    assert envelope.icsr is not None
    assert envelope.pqc is None
    assert envelope.mi is None
    assert envelope.not_relevant is None

    # Check ICSR fields
    assert envelope.icsr.patient is not None
    assert envelope.icsr.product is not None
    assert envelope.icsr.reaction is not None
    assert "Cardioril" in envelope.icsr.product.product_name

def test_pqc_extraction_populates_pqc_payload_only():
    """Pure PQC triage category populates PqcPayload without manufacturing ICSR or MI."""
    envelope = cache_service.get_envelope_by_identifier("case-07")
    assert envelope is not None
    assert envelope.pqc is not None
    assert envelope.icsr is None
    assert envelope.mi is None
    assert envelope.not_relevant is None

    # Check PQC defect details
    assert envelope.pqc.product_name != "Not stated"
    assert envelope.pqc.defect_type != "Not stated"
    assert envelope.pqc.packaging_breached is True

def test_mi_extraction_populates_mi_payload_only():
    """Pure MI triage category populates MiPayload without manufacturing ICSR or PQC."""
    envelope = cache_service.get_envelope_by_identifier("case-09")
    assert envelope is not None
    assert envelope.mi is not None
    assert envelope.icsr is None
    assert envelope.pqc is None
    assert envelope.not_relevant is None

    # Check MI inquiry details
    assert envelope.mi.product_or_topic != "Not stated"
    assert envelope.mi.question_text != "Not stated"
    assert envelope.mi.explicit_no_ae_no_pqc is True

def test_multi_label_icsr_plus_pqc_populates_both():
    """Multi-label case (e.g. Case 04) populates both IcsrPayload and PqcPayload."""
    envelope = cache_service.get_envelope_by_identifier("case-04")
    assert envelope is not None
    assert envelope.triage.is_multi_label is True
    assert envelope.icsr is not None
    assert envelope.pqc is not None
    assert envelope.mi is None
    assert envelope.not_relevant is None

    # Check both payloads have specific facts
    assert "Robert Lang, MD" in envelope.icsr.reporter.name
    assert envelope.pqc.requires_human_review is True
    assert envelope.pqc.photo_evidence.detected is True

def test_not_relevant_populates_not_relevant_payload_only():
    """Not Relevant communication populates NotRelevantPayload without clinical data."""
    envelope = cache_service.get_envelope_by_identifier("case-10")
    assert envelope is not None
    assert envelope.not_relevant is not None
    assert envelope.icsr is None
    assert envelope.pqc is None
    assert envelope.mi is None

    assert envelope.not_relevant.relevance_determination == "Not Relevant"
    assert "commercial" in envelope.not_relevant.exclusion_reason.lower() or "marketing" in envelope.not_relevant.exclusion_reason.lower()

# -------------------------------------------------------------
# 2. Atomic Fact Ledger & Evidence Tests
# -------------------------------------------------------------

def test_atomic_fact_ledger_properties():
    """Validates that atomic facts in fact_ledger contain field, value, status, and confidence."""
    envelope = cache_service.get_envelope_by_identifier("email_01.eml")
    assert envelope is not None
    assert len(envelope.fact_ledger) > 10

    for fact in envelope.fact_ledger:
        assert isinstance(fact.field, str) and len(fact.field) > 0
        assert isinstance(fact.value, str)
        assert fact.status in (FactStatus.CONFIRMED, FactStatus.NOT_STATED, FactStatus.UNCERTAIN, FactStatus.CONFLICT)
        assert 0.0 <= fact.confidence <= 1.0
        assert fact.verification_state in (VerificationResult.SUPPORTS, VerificationResult.CONTRADICTS, VerificationResult.INSUFFICIENT)

def test_evidence_objects_preservation():
    """Validates that Evidence objects preserve source identifier, type, location, and snippet."""
    envelope = cache_service.get_envelope_by_identifier("email_01.eml")
    assert envelope is not None
    
    confirmed_facts = [f for f in envelope.fact_ledger if f.status == FactStatus.CONFIRMED and f.evidence]
    assert len(confirmed_facts) > 0

    first_evidence = confirmed_facts[0].evidence[0]
    assert isinstance(first_evidence, Evidence)
    assert first_evidence.source_id != ""
    assert isinstance(first_evidence.source_type, EvidenceType)
    assert first_evidence.page_or_location != ""
    assert first_evidence.verbatim_snippet != ""
    assert first_evidence.verification_result == VerificationResult.INSUFFICIENT

def test_not_stated_facts_have_no_evidence():
    """Unstated facts must have NOT_STATED status and zero evidence claims."""
    envelope = cache_service.get_envelope_by_identifier("email_01.eml")
    assert envelope is not None
    
    unstated_facts = [f for f in envelope.fact_ledger if f.status == FactStatus.NOT_STATED]
    assert len(unstated_facts) > 0
    for uf in unstated_facts:
        assert uf.value == "Not stated"
        assert len(uf.evidence) == 0

# -------------------------------------------------------------
# 3. Normalizer Tests
# -------------------------------------------------------------

def test_normalizer_functions():
    """Verifies standard normalization for age, route, country, and dates."""
    assert normalizer.normalize_age("71 YRS") == 71
    assert normalizer.normalize_age("54 ans") == 54
    assert normalizer.normalize_age("Not stated") is None

    assert normalizer.normalize_route("p.o.") == "Oral"
    assert normalizer.normalize_route("oralmente") == "Oral"
    assert normalizer.normalize_route("intravenous") == "Intravenous"

    assert normalizer.normalize_country("España") == "Spain"
    assert normalizer.normalize_country("Deutschland") == "Germany"
    assert normalizer.normalize_country("USA") == "United States"

    assert normalizer.normalize_date("2025-11-14") == "2025-11-14"
    assert normalizer.normalize_date("14/11/2025") == "2025-11-14"
    assert normalizer.normalize_date("November 14, 2025") == "2025-11-14"

# -------------------------------------------------------------
# 4. Legacy Adapter Compatibility Tests
# -------------------------------------------------------------

def test_envelope_to_legacy_mapping():
    """Validates envelope_to_legacy produces fully compatible ExtractionResult with attached envelope."""
    envelope = cache_service.get_envelope_by_identifier("case-04")
    assert envelope is not None

    legacy = envelope_to_legacy(envelope)
    assert legacy.triage.is_multi_label is True
    assert "Robert Lang, MD" in legacy.reporter.name
    assert legacy.quality_complaint is not None
    assert legacy.quality_complaint.requires_human_review is True
    assert legacy.envelope is not None
    assert legacy.envelope.envelope_id == envelope.envelope_id

# -------------------------------------------------------------
# 5. API Endpoints Integration Tests
# -------------------------------------------------------------

def test_api_extract_envelope_endpoint():
    """Validates /api/v1/extract-envelope endpoint returns canonical CaseEnvelope."""
    triage = TriageResult(
        is_multi_label=False,
        primary_category=CategoryEnum.SAFETY_REPORT_ICSR,
        labels=[TriageLabel(category=CategoryEnum.SAFETY_REPORT_ICSR, confidence=0.98, reason="Clinical event")],
        executive_summary="Safety case summary."
    )
    payload = {
        "text": "Dr. Sarah Jenkins reported patient A.P., 71 yo male, experienced anaphylaxis after Cardioril 10mg PO.",
        "triage": triage.model_dump(),
        "source_filename": "email_01.eml"
    }
    response = client.post("/api/v1/extract-envelope", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "envelope_id" in data
    assert "fact_ledger" in data
    assert data["icsr"] is not None
    assert data["pqc"] is None

def test_api_process_eml_envelope_endpoint():
    """Validates /api/v1/process-eml-envelope returns full CaseEnvelope with fact ledger."""
    eml_file = TEST_DATA_DIR / "emails" / "email_01.eml"
    assert eml_file.exists()
    with open(eml_file, "rb") as f:
        response = client.post(
            "/api/v1/process-eml-envelope",
            files={"file": ("email_01.eml", f.read(), "message/rfc822")}
        )
    assert response.status_code == 200
    data = response.json()
    assert "envelope_id" in data
    assert "fact_ledger" in data
    assert len(data["fact_ledger"]) > 0
    assert data["icsr"] is not None

def test_generalized_rescue_medication_segregation():
    """Validates that emergency rescue medication is segregated and suspect dose remains Not stated."""
    raw_data = {
        "language_detected": "English",
        "icsr": {
            "patient": {"identifier": "J.D.", "age": "33", "sex": "Female", "status": "CONFIRMED"},
            "reporter": {"name": "Dr. Peterson", "role": "Physician", "status": "CONFIRMED"},
            "product": {"product_name": "InjectaPen", "dose": "Not stated", "status": "NOT_STATED"},
            "reaction": {"adverse_event": "Acute Anaphylaxis", "status": "CONFIRMED"},
            "clinical_narrative": "Patient experienced anaphylaxis. Epinephrine 0.3mg IM administered as emergency resuscitation."
        }
    }
    triage = TriageResult(
        is_multi_label=False,
        primary_category=CategoryEnum.SAFETY_REPORT_ICSR,
        labels=[TriageLabel(category=CategoryEnum.SAFETY_REPORT_ICSR, confidence=0.95, reason="Adverse event")],
        executive_summary="Emergency anaphylaxis."
    )
    envelope = icsr_extractor._build_envelope_from_data(
        raw_data=raw_data,
        triage_result=triage,
        source_filename="emergency_intake.pdf",
        message_id="test-msg-02",
        start_time=0.0,
        is_icsr=True,
        is_pqc=False,
        is_mi=False,
        is_not_relevant=False
    )
    dose_fact = next(f for f in envelope.fact_ledger if f.field == "product_dose")
    assert dose_fact.value == "Not stated"
    assert dose_fact.status == FactStatus.NOT_STATED
    assert len(dose_fact.evidence) == 0
    assert "Epinephrine 0.3mg IM" in envelope.icsr.clinical_narrative

def test_generalized_indication_vs_reaction_separation():
    """Validates that unstated indication is preserved as NOT_STATED rather than inferred from reaction."""
    raw_data = {
        "icsr": {
            "patient": {"identifier": "Pt A", "treated_indication": "Not stated", "status": "CONFIRMED"},
            "product": {"product_name": "Cardioril", "indication": "Not stated", "dose": "20mg", "status": "CONFIRMED"},
            "reaction": {"adverse_event": "Drug-Induced Liver Injury", "status": "CONFIRMED"}
        }
    }
    triage = TriageResult(
        is_multi_label=False,
        primary_category=CategoryEnum.SAFETY_REPORT_ICSR,
        labels=[TriageLabel(category=CategoryEnum.SAFETY_REPORT_ICSR, confidence=0.92, reason="ICSR")],
        executive_summary="DILI report."
    )
    envelope = icsr_extractor._build_envelope_from_data(
        raw_data=raw_data,
        triage_result=triage,
        source_filename="report.pdf",
        message_id="test-msg-ind",
        start_time=0.0,
        is_icsr=True,
        is_pqc=False,
        is_mi=False,
        is_not_relevant=False
    )
    ind_fact = next(f for f in envelope.fact_ledger if f.field == "indication")
    assert ind_fact.value == "Not stated"
    assert ind_fact.status == FactStatus.NOT_STATED
    assert envelope.icsr.product.indication == "Not stated"

def test_generalized_reporter_role_qualification():
    """Validates reporter role distinction between Consumer/Patient and Physician."""
    consumer_raw = {
        "icsr": {
            "reporter": {"name": "Jane Consumer", "role": "Consumer / Patient", "status": "CONFIRMED", "citation": {"source_type": "email_body", "verbatim_snippet": "I am writing about my palpitations"}}
        }
    }
    triage = TriageResult(
        is_multi_label=False,
        primary_category=CategoryEnum.SAFETY_REPORT_ICSR,
        labels=[TriageLabel(category=CategoryEnum.SAFETY_REPORT_ICSR, confidence=0.9, reason="ICSR")],
        executive_summary="Self-reported palpitations."
    )
    envelope = icsr_extractor._build_envelope_from_data(
        raw_data=consumer_raw,
        triage_result=triage,
        source_filename="consumer.eml",
        message_id="test-msg-rep",
        start_time=0.0,
        is_icsr=True,
        is_pqc=False,
        is_mi=False,
        is_not_relevant=False
    )
    rep_fact = next(f for f in envelope.fact_ledger if f.field == "reporter_role")
    assert "Consumer" in rep_fact.value or "Patient" in rep_fact.value
    assert rep_fact.status == FactStatus.CONFIRMED

def test_multilingual_evidence_preservation_and_normalization():
    """Validates that non-English citations retain verbatim source text while values are standardized."""
    es_raw = {
        "language_detected": "Spanish",
        "icsr": {
            "reaction": {
                "adverse_event": "Toxic Epidermal Necrolysis",
                "status": "CONFIRMED",
                "citation": {
                    "source_type": "pdf_text",
                    "page_or_location": "Page 1",
                    "verbatim_snippet": "Necrólisis Epidérmica Tóxica grave en >35% superficie corporal"
                }
            }
        }
    }
    triage = TriageResult(
        is_multi_label=False,
        primary_category=CategoryEnum.SAFETY_REPORT_ICSR,
        labels=[TriageLabel(category=CategoryEnum.SAFETY_REPORT_ICSR, confidence=0.96, reason="RAM")],
        executive_summary="Spanish RAM."
    )
    envelope = icsr_extractor._build_envelope_from_data(
        raw_data=es_raw,
        triage_result=triage,
        source_filename="notificacion_madrid.pdf",
        message_id="test-msg-es",
        start_time=0.0,
        is_icsr=True,
        is_pqc=False,
        is_mi=False,
        is_not_relevant=False
    )
    ae_fact = next(f for f in envelope.fact_ledger if f.field == "adverse_event")
    assert ae_fact.value == "Toxic Epidermal Necrolysis"
    assert len(ae_fact.evidence) == 1
    assert "Necrólisis Epidérmica Tóxica" in ae_fact.evidence[0].verbatim_snippet

def test_pure_pqc_and_mi_cross_category_isolation():
    """Validates that pure PQC and pure MI produce null ICSR and enforce category boundaries."""
    # Pure PQC
    pqc_raw = {
        "pqc": {
            "product_name": "Cardioril 10mg",
            "lot_number": "BL-8802",
            "defect_type": "Packaging Integrity Failure",
            "defect_description": "Aluminum lidding foil unsealed",
            "packaging_breached": True,
            "patient_exposure": "None / Intercepted in pharmacy",
            "requires_human_review": False
        }
    }
    pqc_triage = TriageResult(
        is_multi_label=False,
        primary_category=CategoryEnum.QUALITY_COMPLAINT_PQC,
        labels=[TriageLabel(category=CategoryEnum.QUALITY_COMPLAINT_PQC, confidence=0.98, reason="PQC")],
        executive_summary="Defect complaint."
    )
    env_pqc = icsr_extractor._build_envelope_from_data(
        raw_data=pqc_raw,
        triage_result=pqc_triage,
        source_filename="pqc.pdf",
        message_id="test-pqc",
        start_time=0.0,
        is_icsr=False,
        is_pqc=True,
        is_mi=False,
        is_not_relevant=False
    )
    assert env_pqc.icsr is None
    assert env_pqc.pqc is not None
    assert env_pqc.pqc.product_name == "Cardioril 10mg"

    # Pure MI
    mi_raw = {
        "mi": {
            "product_or_topic": "Corzapan 10mg",
            "inquiry_type": "Enteral Administration",
            "question_text": "Can Corzapan 10mg tablets be crushed for NG-tube administration?",
            "explicit_no_ae_no_pqc": True
        }
    }
    mi_triage = TriageResult(
        is_multi_label=False,
        primary_category=CategoryEnum.INFO_REQUEST_MI,
        labels=[TriageLabel(category=CategoryEnum.INFO_REQUEST_MI, confidence=0.97, reason="MI")],
        executive_summary="Crushing inquiry."
    )
    env_mi = icsr_extractor._build_envelope_from_data(
        raw_data=mi_raw,
        triage_result=mi_triage,
        source_filename="mi.eml",
        message_id="test-mi",
        start_time=0.0,
        is_icsr=False,
        is_pqc=False,
        is_mi=True,
        is_not_relevant=False
    )
    assert env_mi.icsr is None
    assert env_mi.pqc is None
    assert env_mi.mi is not None
    assert env_mi.mi.explicit_no_ae_no_pqc is True


def test_hospitalization_boolean_consistency():
    """Validates deterministic resolution of hospitalization boolean and seriousness criteria."""
    triage = TriageResult(
        is_multi_label=False,
        primary_category=CategoryEnum.SAFETY_REPORT_ICSR,
        labels=[TriageLabel(category=CategoryEnum.SAFETY_REPORT_ICSR, confidence=0.99, reason="ICSR")],
        executive_summary="Safety report."
    )

    # 1. explicit hospitalization=True, no criteria
    raw_1 = {
        "icsr": {
            "reaction": {
                "adverse_event": "Acute Liver Injury",
                "onset_date": "08-NOV-2025",
                "outcome": "Recovered",
                "hospitalization": True,
                "admission_date": "10-NOV-2025",
                "seriousness_criteria": []
            }
        }
    }
    env_1 = icsr_extractor._build_envelope_from_data(raw_1, triage, "test.pdf", "m1", 0.0, True, False, False, False)
    assert env_1.icsr.reaction.hospitalization is True
    assert env_1.icsr.reaction.admission_date == "10-NOV-2025"
    fact_hosp_1 = next(f for f in env_1.fact_ledger if f.field == "hospitalization")
    assert fact_hosp_1.value == "Yes"
    # Verify unrelated fields unaffected
    assert env_1.icsr.reaction.adverse_event == "Acute Liver Injury"
    assert env_1.icsr.reaction.outcome == "Recovered"

    # 2. explicit hospitalization=False + seriousness criteria contains hospitalization -> canonical result must be True
    raw_2 = {
        "icsr": {
            "reaction": {
                "adverse_event": "Acute Liver Injury",
                "onset_date": "08-NOV-2025",
                "outcome": "Recovered",
                "hospitalization": False,
                "admission_date": "10-NOV-2025",
                "seriousness_criteria": ["Hospitalization", "Medically Significant"]
            }
        }
    }
    env_2 = icsr_extractor._build_envelope_from_data(raw_2, triage, "test.pdf", "m2", 0.0, True, False, False, False)
    assert env_2.icsr.reaction.hospitalization is True
    assert env_2.icsr.reaction.admission_date == "10-NOV-2025"
    fact_hosp_2 = next(f for f in env_2.fact_ledger if f.field == "hospitalization")
    assert fact_hosp_2.value == "Yes"
    # Legacy adapter reflects normalized hospitalization
    legacy_2 = envelope_to_legacy(env_2)
    assert legacy_2.reaction.hospitalization is True
    assert legacy_2.reaction.admission_date == "10-NOV-2025"

    # 3. explicit hospitalization=False + no hospitalization criteria -> remains False
    raw_3 = {
        "icsr": {
            "reaction": {
                "adverse_event": "Mild Rash",
                "onset_date": "08-NOV-2025",
                "outcome": "Recovered",
                "hospitalization": False,
                "seriousness_criteria": ["Medically Significant"]
            }
        }
    }
    env_3 = icsr_extractor._build_envelope_from_data(raw_3, triage, "test.pdf", "m3", 0.0, True, False, False, False)
    assert env_3.icsr.reaction.hospitalization is False
    fact_hosp_3 = next(f for f in env_3.fact_ledger if f.field == "hospitalization")
    assert fact_hosp_3.value == "No"

    # 4. hospitalization=True + no criteria -> remains True
    raw_4 = {
        "icsr": {
            "reaction": {
                "adverse_event": "Anaphylaxis",
                "onset_date": "08-NOV-2025",
                "outcome": "Recovering",
                "hospitalization": True,
                "seriousness_criteria": []
            }
        }
    }
    env_4 = icsr_extractor._build_envelope_from_data(raw_4, triage, "test.pdf", "m4", 0.0, True, False, False, False)
    assert env_4.icsr.reaction.hospitalization is True
    fact_hosp_4 = next(f for f in env_4.fact_ledger if f.field == "hospitalization")
    assert fact_hosp_4.value == "Yes"

    # 5. admission date is preserved when present
    raw_5 = {
        "icsr": {
            "reaction": {
                "adverse_event": "Drug-induced Liver Injury",
                "onset_date": "08-NOV-2025",
                "hospitalization": True,
                "admission_date": "10-NOV-2025",
                "seriousness_criteria": ["Hospitalization"]
            }
        }
    }
    env_5 = icsr_extractor._build_envelope_from_data(raw_5, triage, "test.pdf", "m5", 0.0, True, False, False, False)
    assert env_5.icsr.reaction.admission_date == "10-NOV-2025"
    fact_adm_5 = next(f for f in env_5.fact_ledger if f.field == "hospital_admission_date")
    assert fact_adm_5.value == "10-NOV-2025"

    # 6. no unrelated fields change
    assert env_5.icsr.reaction.adverse_event == "Drug-induced Liver Injury"
    assert env_5.icsr.reaction.onset_date == "08-NOV-2025"


