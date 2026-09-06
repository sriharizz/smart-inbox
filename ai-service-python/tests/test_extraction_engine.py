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
