import pytest
from unittest.mock import patch, MagicMock
from app.services.pdf_summary_validator import (
    split_sentences,
    count_sentences,
    validate_and_repair_document_summary
)


def test_split_sentences_with_abbreviations():
    """Verify abbreviation protection prevents improper sentence fragmentation."""
    text = (
        "The report was signed by Dr. Robert Lang, MD at St. Mary's Hospital. "
        "Patient Arthur Pendelton had a temperature of 39.8 C and blood pressure of 72/40 mmHg. "
        "The MedWatch Form FDA 3500A was submitted under Ref. No. 0910-0291."
    )
    sents = split_sentences(text)
    assert len(sents) == 3
    assert sents[0] == "The report was signed by Dr. Robert Lang, MD at St. Mary's Hospital."
    assert sents[1] == "Patient Arthur Pendelton had a temperature of 39.8 C and blood pressure of 72/40 mmHg."
    assert sents[2] == "The MedWatch Form FDA 3500A was submitted under Ref. No. 0910-0291."


def test_valid_summary_untouched():
    """Verify that a summary with 10-15 sentences passes through completely untouched."""
    valid_summary = " ".join([f"This is sentence number {i} detailing relevant clinical facts." for i in range(1, 12)])
    assert count_sentences(valid_summary) == 11

    with patch("app.core.gemini_client.gemini_client.generate_content") as mock_gemini:
        res = validate_and_repair_document_summary(valid_summary, filename="valid.pdf")
        assert res == valid_summary
        mock_gemini.assert_not_called()


def test_short_summary_repaired():
    """Verify that a 9-sentence summary triggers bounded repair and returns 10-15 sentences."""
    short_summary = " ".join([f"Sentence {i} covers key regulatory findings." for i in range(1, 10)])
    assert count_sentences(short_summary) == 9

    repaired_12 = " ".join([f"Repaired sentence {i} provides complete source-grounded clinical context." for i in range(1, 13)])

    with patch("app.core.gemini_client.gemini_client.generate_content", return_value=repaired_12) as mock_gemini:
        res = validate_and_repair_document_summary(short_summary, document_context="Source document context.", filename="case04.pdf")
        mock_gemini.assert_called_once()
        assert count_sentences(res) == 12
        assert 10 <= count_sentences(res) <= 15


def test_long_summary_condensed():
    """Verify that a summary with >15 sentences is condensed to 10-15 sentences."""
    long_summary = " ".join([f"Sentence {i} describing findings in depth." for i in range(1, 18)])
    assert count_sentences(long_summary) == 17

    condensed_11 = " ".join([f"Condensed sentence {i} summarizing the document." for i in range(1, 12)])

    with patch("app.core.gemini_client.gemini_client.generate_content", return_value=condensed_11) as mock_gemini:
        res = validate_and_repair_document_summary(long_summary, filename="long.pdf")
        assert count_sentences(res) == 11
        assert 10 <= count_sentences(res) <= 15
