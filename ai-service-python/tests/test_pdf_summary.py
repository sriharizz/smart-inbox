import pytest
from unittest.mock import patch, MagicMock
from app.schemas.case_envelope import CaseEnvelope
from app.schemas.triage_schema import TriageResult, CategoryEnum
from app.schemas.legacy_adapter import envelope_to_legacy
from app.services.orchestrator import DocumentOrchestrator
from app.parsers.email_parser import ParsedEmail
from app.parsers.pdf_parser import ParsedPDF


def test_document_summary_preserved_in_legacy_adapter():
    """Verify document_summary is preserved on ExtractionResult and does not mutate Executive Synthesis."""
    triage = TriageResult(
        is_multi_label=False,
        primary_category=CategoryEnum.SAFETY_REPORT_ICSR,
        labels=[],
        executive_summary="4-6 sentence message-level executive synthesis here."
    )
    envelope = CaseEnvelope(
        envelope_id="env-test-01",
        message_id="msg-test-01",
        source_filename="test.pdf",
        triage=triage,
        document_summary="10 to 15 sentence regulatory document summary specifically evaluating the attached PDF.",
        metadata={
            "attachment_metadata": [
                {
                    "filename": "clinical_report.pdf",
                    "flavor": "digital_form",
                    "language": "English",
                    "document_summary": "10 to 15 sentence regulatory document summary specifically evaluating the attached PDF."
                }
            ]
        }
    )

    result = envelope_to_legacy(envelope)

    # 1. document_summary is preserved on top-level result
    assert result.document_summary == "10 to 15 sentence regulatory document summary specifically evaluating the attached PDF."
    # 2. Executive Synthesis on triage remains completely unchanged
    assert result.triage.executive_summary == "4-6 sentence message-level executive synthesis here."
    # 3. Attachment carries its own document_summary
    assert len(result.attachment_metadata) == 1
    assert result.attachment_metadata[0].document_summary == "10 to 15 sentence regulatory document summary specifically evaluating the attached PDF."


def test_single_pdf_attachment_receives_document_summary():
    """Verify a single PDF attachment in an email receives the extraction's document_summary."""
    mock_email = ParsedEmail(
        message_id="<test@email.com>",
        date="2026-09-09",
        sender="Dr. Smith",
        sender_email="smith@hospital.org",
        recipient="safety@company.com",
        subject="ICSR Report",
        body_text="See attached form.",
        attachments=[{"filename": "patient_form.pdf", "bytes": b"%PDF-1.4 dummy", "content_type": "application/pdf"}]
    )

    mock_pdf = MagicMock(spec=ParsedPDF)
    mock_pdf.flavor = "digital_form"
    mock_pdf.detected_language = "English"
    mock_pdf.full_content_with_tables = "Patient M.K. developed DILI after Cardioril."
    mock_pdf.images = []

    mock_triage = TriageResult(
        is_multi_label=False,
        primary_category=CategoryEnum.SAFETY_REPORT_ICSR,
        labels=[],
        executive_summary="Executive synthesis."
    )

    mock_envelope = CaseEnvelope(
        envelope_id="env-01",
        message_id="msg-01",
        triage=mock_triage,
        document_summary="10-15 sentence comprehensive evaluation of patient_form.pdf showing DILI relevance."
    )

    with patch("app.parsers.email_parser.EmailParser.parse_eml_bytes", return_value=mock_email), \
         patch("app.parsers.pdf_parser.PDFParser.parse_pdf_bytes", return_value=mock_pdf), \
         patch("app.services.triage_service.triage_service.classify_text", return_value=mock_triage), \
         patch("app.services.icsr_extractor.icsr_extractor.extract_envelope", return_value=mock_envelope), \
         patch("app.services.evidence_retriever.evidence_retriever.build_index_for_email"), \
         patch("app.services.evidence_retriever.evidence_retriever.retrieve_for_envelope", side_effect=lambda env, idx: env), \
         patch("app.services.evidence_verifier.evidence_verifier.verify_envelope", side_effect=lambda env, document_context: env):

        envelope = DocumentOrchestrator.process_eml_envelope(b"dummy eml", filename="test.eml")

        assert len(envelope.metadata["attachment_metadata"]) == 1
        att_meta = envelope.metadata["attachment_metadata"][0]
        assert att_meta["filename"] == "patient_form.pdf"
        assert att_meta["document_summary"] == "10-15 sentence comprehensive evaluation of patient_form.pdf showing DILI relevance."


def test_multiple_pdf_attachments_do_not_share_summary():
    """Verify multiple PDF attachments receive independent, distinct summaries and do NOT share one summary."""
    mock_email = ParsedEmail(
        message_id="<multi@email.com>",
        date="2026-09-09",
        sender="Dr. Smith",
        sender_email="smith@hospital.org",
        recipient="safety@company.com",
        subject="Multi-Doc Report",
        body_text="Two PDFs attached.",
        attachments=[
            {"filename": "cioms_form.pdf", "bytes": b"%PDF-1.4 dummy 1", "content_type": "application/pdf"},
            {"filename": "lab_report.pdf", "bytes": b"%PDF-1.4 dummy 2", "content_type": "application/pdf"}
        ]
    )

    mock_pdf1 = MagicMock(spec=ParsedPDF)
    mock_pdf1.flavor = "digital_form"
    mock_pdf1.detected_language = "English"
    mock_pdf1.full_content_with_tables = "CIOMS Form content"
    mock_pdf1.images = []

    mock_pdf2 = MagicMock(spec=ParsedPDF)
    mock_pdf2.flavor = "digital_form"
    mock_pdf2.detected_language = "English"
    mock_pdf2.full_content_with_tables = "Lab Report content"
    mock_pdf2.images = []

    mock_triage = TriageResult(
        is_multi_label=False,
        primary_category=CategoryEnum.SAFETY_REPORT_ICSR,
        labels=[],
        executive_summary="Executive synthesis."
    )

    mock_envelope = CaseEnvelope(
        envelope_id="env-multi",
        message_id="msg-multi",
        triage=mock_triage,
        document_summary="Summary of CIOMS form (PDF 1)."
    )

    def fake_parse_pdf(bytes_data, filename=""):
        if "cioms" in filename:
            return mock_pdf1
        return mock_pdf2

    with patch("app.parsers.email_parser.EmailParser.parse_eml_bytes", return_value=mock_email), \
         patch("app.parsers.pdf_parser.PDFParser.parse_pdf_bytes", side_effect=fake_parse_pdf), \
         patch("app.services.triage_service.triage_service.classify_text", return_value=mock_triage), \
         patch("app.services.icsr_extractor.icsr_extractor.extract_envelope", return_value=mock_envelope), \
         patch("app.services.icsr_extractor.icsr_extractor.summarize_pdf_document", return_value="Independent summary of Lab Report (PDF 2)."), \
         patch("app.services.evidence_retriever.evidence_retriever.build_index_for_email"), \
         patch("app.services.evidence_retriever.evidence_retriever.retrieve_for_envelope", side_effect=lambda env, idx: env), \
         patch("app.services.evidence_verifier.evidence_verifier.verify_envelope", side_effect=lambda env, document_context: env):

        envelope = DocumentOrchestrator.process_eml_envelope(b"dummy eml", filename="multi.eml")

        att_metas = envelope.metadata["attachment_metadata"]
        assert len(att_metas) == 2
        # Verify first PDF has summary 1
        assert att_metas[0]["document_summary"] == "Summary of CIOMS form (PDF 1)."
        # Verify second PDF has independent summary 2, NOT sharing summary 1
        assert att_metas[1]["document_summary"] == "Independent summary of Lab Report (PDF 2)."
        assert att_metas[0]["document_summary"] != att_metas[1]["document_summary"]


def test_email_only_case_has_no_fake_pdf_summary():
    """Verify email-only messages have no PDF attachments and no fake PDF summary assigned."""
    mock_email = ParsedEmail(
        message_id="<email-only@hospital.org>",
        date="2026-09-09",
        sender="pharmacist@hospital.org",
        sender_email="pharmacist@hospital.org",
        recipient="safety@company.com",
        subject="Email Only Inquiry",
        body_text="Can drug X be crushed?",
        attachments=[]
    )

    mock_triage = TriageResult(
        is_multi_label=False,
        primary_category=CategoryEnum.INFO_REQUEST_MI,
        labels=[],
        executive_summary="Executive synthesis for medical inquiry."
    )

    mock_envelope = CaseEnvelope(
        envelope_id="env-mi",
        message_id="msg-mi",
        triage=mock_triage,
        document_summary="Not stated"
    )

    with patch("app.parsers.email_parser.EmailParser.parse_eml_bytes", return_value=mock_email), \
         patch("app.services.triage_service.triage_service.classify_text", return_value=mock_triage), \
         patch("app.services.icsr_extractor.icsr_extractor.extract_envelope", return_value=mock_envelope), \
         patch("app.services.evidence_retriever.evidence_retriever.build_index_for_email"), \
         patch("app.services.evidence_retriever.evidence_retriever.retrieve_for_envelope", side_effect=lambda env, idx: env), \
         patch("app.services.evidence_verifier.evidence_verifier.verify_envelope", side_effect=lambda env, document_context: env):

        envelope = DocumentOrchestrator.process_eml_envelope(b"dummy eml", filename="inquiry.eml")

        # Zero attachment metadata entries
        assert len(envelope.metadata["attachment_metadata"]) == 0

        # Legacy conversion produces zero attachments with no fake document_summary
        result = envelope_to_legacy(envelope)
        assert len(result.attachment_metadata) == 0
        # Executive synthesis remains intact
        assert result.triage.executive_summary == "Executive synthesis for medical inquiry."

