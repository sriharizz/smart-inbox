import pytest
from pathlib import Path
from app.parsers.email_parser import EmailParser
from app.parsers.pdf_parser import PDFParser

BASE_DIR = Path(__file__).resolve().parent.parent.parent
TEST_DATA_DIR = BASE_DIR / "test-data"

def test_email_parser_email_01():
    eml_file = TEST_DATA_DIR / "emails" / "email_01.eml"
    assert eml_file.exists(), f"Missing test email: {eml_file}"
    parsed = EmailParser.parse_eml_file(eml_file)
    assert parsed.sender == "Dr. Sarah Jenkins, MD"
    assert parsed.sender_email == "sjenkins@metrohealth-chicago.org"
    assert "Cardioril" in parsed.subject
    assert len(parsed.attachments) == 1
    assert parsed.attachments[0]["filename"] == "cioms_form_MK_Cardioril.pdf"

def test_email_parser_case_04_multi_label():
    eml_file = TEST_DATA_DIR / "emails" / "email_04.eml"
    assert eml_file.exists()
    parsed = EmailParser.parse_eml_file(eml_file)
    assert parsed.sender == "Dr. Robert Lang, MD"
    assert parsed.sender_email == "rlang@nmh-icu.org"
    assert "Cefatox" in parsed.subject
    assert len(parsed.attachments) == 1
    assert parsed.attachments[0]["filename"] == "vial_contamination_sepsis.pdf"

def test_pdf_parser_cioms_form():
    pdf_file = TEST_DATA_DIR / "pdfs" / "digital_forms" / "cioms_form_MK_Cardioril.pdf"
    assert pdf_file.exists()
    parsed = PDFParser.parse_pdf_file(pdf_file)
    assert parsed.flavor == "digital_form"
    assert parsed.page_count == 1
    assert len(parsed.tables_by_page[1]) > 0
    assert "M.K." in parsed.full_text

def test_pdf_parser_defect_image_case_04():
    pdf_file = TEST_DATA_DIR / "pdfs" / "quality_complaints" / "vial_contamination_sepsis.pdf"
    assert pdf_file.exists()
    parsed = PDFParser.parse_pdf_file(pdf_file)
    assert parsed.page_count == 2
    assert len(parsed.images) == 1
    assert parsed.images[0]["width"] >= 100
    assert parsed.images[0]["page"] == 2
    assert parsed.images[0]["source_filename"] == "vial_contamination_sepsis.pdf"
    assert parsed.images[0]["bbox"] is not None
    assert parsed.images[0]["bbox"] == (144.0, 142.5, 468.0, 385.5)

def test_language_and_flavor_spanish_pdf():
    pdf_file = TEST_DATA_DIR / "pdfs" / "non_english" / "notificacion_ram_madrid.pdf"
    assert pdf_file.exists()
    parsed = PDFParser.parse_pdf_file(pdf_file)
    assert parsed.detected_language == "Spanish"
    assert parsed.flavor == "non_english"

def test_language_and_flavor_german_pdf_second_non_english():
    pdf_file = TEST_DATA_DIR / "pdfs" / "non_english" / "bericht_uaw_charite_berlin.pdf"
    assert pdf_file.exists()
    parsed = PDFParser.parse_pdf_file(pdf_file)
    assert parsed.detected_language == "German"
    assert parsed.flavor == "non_english"

def test_language_and_flavor_misleading_english_filename():
    """Verify that a filename containing substring 'de' is NOT misclassified as non-English."""
    pdf_file = TEST_DATA_DIR / "pdfs" / "quality_complaints" / "packaging_defect_report.pdf"
    assert pdf_file.exists()
    parsed = PDFParser.parse_pdf_file(pdf_file)
    assert parsed.detected_language == "English"
    assert parsed.flavor == "digital_form"

def test_generic_language_detector_french_and_italian():
    from app.parsers.language_detector import detect_language
    french_text = "Le patient a présenté une réaction indésirable grave après avoir pris le médicament avec de la fièvre et des douleurs."
    assert detect_language(french_text) == "French"
    italian_text = "Il paziente ha manifestato una reazione avversa dopo la somministrazione del farmaco con febbre alta."
    assert detect_language(italian_text) == "Italian"

def test_email_and_attachment_language_separation():
    from app.services.orchestrator import DocumentOrchestrator
    # Construct an English email with an attached Spanish PDF
    spanish_pdf_path = TEST_DATA_DIR / "pdfs" / "non_english" / "notificacion_ram_madrid.pdf"
    assert spanish_pdf_path.exists()
    pdf_bytes = spanish_pdf_path.read_bytes()

    from email.message import EmailMessage
    msg = EmailMessage()
    msg["From"] = "safety-team@hospital.com"
    msg["To"] = "inbox@clinevo.com"
    msg["Subject"] = "Forwarded report for your review"
    msg.set_content("Please find attached the foreign regulatory safety report received from our regional affiliate.")
    msg.add_attachment(pdf_bytes, maintype="application", subtype="pdf", filename="notificacion_ram_madrid.pdf")

    eml_bytes = msg.as_bytes()
    envelope = DocumentOrchestrator.process_eml_envelope(eml_bytes, filename="test_mixed.eml", fresh_processing=True)

    # Message language MUST remain English
    assert envelope.language_detected == "English"
    
    # Attachment language must be Spanish and flavor non_english
    att_meta = envelope.metadata.get("attachment_metadata", [])
    assert len(att_meta) == 1
    assert att_meta[0]["filename"] == "notificacion_ram_madrid.pdf"
    assert att_meta[0]["language"] == "Spanish"
    assert att_meta[0]["flavor"] == "non_english"

