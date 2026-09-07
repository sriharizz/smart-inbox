import pytest
from unittest.mock import patch, MagicMock
from app.services.icsr_extractor import ICSRExtractor
from app.schemas.triage_schema import TriageResult, CategoryEnum, TriageLabel
from app.schemas.case_envelope import CaseEnvelope

def test_fresh_processing_bypasses_cache_on_failure():
    extractor = ICSRExtractor()
    triage = TriageResult(
        is_multi_label=False,
        primary_category=CategoryEnum.SAFETY_REPORT_ICSR,
        labels=[
            TriageLabel(category=CategoryEnum.SAFETY_REPORT_ICSR, confidence=0.95, reason="Adverse event reported")
        ],
        executive_summary="Executive summary for test"
    )
    
    # Mock LLM provider to raise an exception
    extractor.provider = MagicMock()
    extractor.provider.generate_content.side_effect = Exception("Live API error")

    with patch("app.services.cache_service.cache_service.get_envelope_by_identifier") as mock_cache:
        mock_cache.return_value = CaseEnvelope(
            envelope_id="cached-env",
            message_id="msg-1",
            source_filename="email_01.eml",
            language_detected="English",
            triage=triage,
            document_summary="Cached summary",
            reviewer_summary="Cached reviewer summary",
            fact_ledger=[]
        )

        # 1. When fresh_processing is True: cache should NOT be queried
        res_fresh = extractor.extract_envelope(
            document_text="Test",
            triage_result=triage,
            source_filename="email_01.eml",
            fresh_processing=True
        )
        mock_cache.assert_not_called()
        assert res_fresh.envelope_id != "cached-env"
        assert "fallback" in res_fresh.envelope_id

        # 2. When fresh_processing is False: cache SHOULD be queried and used
        res_cached = extractor.extract_envelope(
            document_text="Test",
            triage_result=triage,
            source_filename="email_01.eml",
            fresh_processing=False
        )
        mock_cache.assert_called_once_with("email_01.eml")
        assert res_cached.envelope_id == "cached-env"
