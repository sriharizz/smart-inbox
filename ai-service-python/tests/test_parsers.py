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
