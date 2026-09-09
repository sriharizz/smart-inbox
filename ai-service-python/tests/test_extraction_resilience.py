import pytest
from unittest.mock import MagicMock
from app.services.icsr_extractor import ICSRExtractor, robust_json_loads, validate_extraction_schema
from app.schemas.triage_schema import TriageResult, CategoryEnum, TriageLabel
from app.schemas.case_envelope import CaseEnvelope

def test_robust_json_loads_markdown_fences():
    raw = '```json\n{"key": "value"}\n```'
    data, err = robust_json_loads(raw)
    assert err is None
    assert data == {"key": "value"}

def test_robust_json_loads_trailing_commas():
    raw = '{"key": "value", "list": [1, 2, ], }'
    data, err = robust_json_loads(raw)
    assert err is None
    assert data["key"] == "value"
    assert data["list"] == [1, 2]

def test_robust_json_loads_truncated_closing():
    raw = '{"icsr": {"patient": {"age": "45"}, "reporter": {"name": "Dr. A"}'
    data, err = robust_json_loads(raw)
    assert err is None
    assert data["icsr"]["patient"]["age"] == "45"

def test_validate_extraction_schema_icsr_valid():
    sample = {
        "icsr": {
            "patient": {"age": "50", "sex": "Male"},
            "reporter": {"qualification": "Physician"},
            "product": {"product_name": "Cardioril"},
            "reaction": {"reaction_pt": "Hepatotoxicity"}
        }
    }
    is_valid, reason = validate_extraction_schema(sample, is_icsr=True, is_pqc=False, is_mi=False, is_not_relevant=False, document_text="Cardioril adverse reaction")
    assert is_valid is True
    assert reason == "Valid"

def test_validate_extraction_schema_multilabel_missing_pqc():
    sample = {
        "icsr": {
            "patient": {"age": "50"},
            "product": {"product_name": "Cefatox"},
            "reaction": {"reaction_pt": "Anaphylaxis"}
        }
    }
    # Active is both ICSR and PQC
    is_valid, reason = validate_extraction_schema(sample, is_icsr=True, is_pqc=True, is_mi=False, is_not_relevant=False, document_text="Cefatox sepsis vial defect")
    assert is_valid is False
    assert "Missing or invalid 'pqc'" in reason

def test_validate_extraction_schema_empty_hull_detection():
    # When doc text has substantial clinical content (> 50 words), but all fields are 'Not stated'
    sample = {
        "icsr": {
            "patient": {"age": "Not stated", "sex": "Not stated"},
            "reporter": {"qualification": "Not stated"},
            "product": {"product_name": "Not stated"},
            "reaction": {"reaction_pt": "Not stated"}
        }
    }
    doc_text = "The patient John Doe experienced severe cardiotoxicity after taking DrugX 50mg daily. " * 10
    is_valid, reason = validate_extraction_schema(sample, is_icsr=True, is_pqc=False, is_mi=False, is_not_relevant=False, document_text=doc_text)
    assert is_valid is False
    assert "empty extraction hull" in reason.lower()

def test_extract_envelope_retry_success():
    extractor = ICSRExtractor()
    triage = TriageResult(
        is_multi_label=False,
        primary_category=CategoryEnum.SAFETY_REPORT_ICSR,
        labels=[TriageLabel(category=CategoryEnum.SAFETY_REPORT_ICSR, confidence=0.95, reason="Adverse event")],
        executive_summary="Patient adverse event summary"
    )

    extractor.provider = MagicMock()
    # First call returns malformed unparseable junk, retry call returns valid JSON
    extractor.provider.generate_content.side_effect = [
        "THIS IS NOT JSON {{{",
        '{"icsr": {"patient": {"age": "45"}, "reporter": {"qualification": "MD"}, "product": {"product_name": "DrugA"}, "reaction": {"reaction_pt": "Nausea"}}}'
    ]

    envelope = extractor.extract_envelope(
        document_text="Patient on DrugA had nausea.",
        triage_result=triage,
        source_filename="test_case.eml",
        fresh_processing=True
    )

    assert envelope.extraction_status == "SUCCESS"
    assert envelope.icsr is not None
    assert envelope.icsr.product.product_name == "DrugA"
    assert extractor.provider.generate_content.call_count == 2

def test_extract_envelope_fallback_when_both_fail():
    extractor = ICSRExtractor()
    triage = TriageResult(
        is_multi_label=False,
        primary_category=CategoryEnum.SAFETY_REPORT_ICSR,
        labels=[TriageLabel(category=CategoryEnum.SAFETY_REPORT_ICSR, confidence=0.95, reason="Adverse event")],
        executive_summary="Patient adverse event summary"
    )

    extractor.provider = MagicMock()
    # Both primary and retry fail
    extractor.provider.generate_content.side_effect = [
        "BAD JSON 1",
        "BAD JSON 2"
    ]

    envelope = extractor.extract_envelope(
        document_text="Patient on DrugA had nausea.",
        triage_result=triage,
        source_filename="test_case.eml",
        fresh_processing=True
    )

    assert envelope.extraction_status == "NEEDS_REVIEW"
    assert envelope.extraction_error is not None
    assert "JSON decode failed" in envelope.extraction_error
    assert "[EXTRACTION WARNING]" in envelope.document_summary
    assert envelope.reviewer_brief is not None
    assert len(envelope.reviewer_brief.review_focus) >= 1
