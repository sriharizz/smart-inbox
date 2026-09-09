import pytest
from pathlib import Path

from app.parsers.pdf_parser import PDFParser
from app.services.literature_service import literature_service
from app.schemas.literature_schema import LiteratureScreenResult

LITERATURE_PDF_DIR = Path(__file__).resolve().parent.parent.parent / "test-data" / "pdfs" / "literature_articles"


class TestLiteratureScreeningFoundation:
    """
    Test suite for the structured-table-aware literature screening and
    generic evidence grounding foundation across benchmark articles LIT-01 to LIT-07.
    """

    def test_lit_01_dili_single_case_with_table_lfts(self):
        pdf_path = LITERATURE_PDF_DIR / "article_01_dili_case.pdf"
        assert pdf_path.exists(), f"Missing benchmark PDF: {pdf_path}"

        parsed = PDFParser.parse_pdf_file(pdf_path)
        assert parsed.page_count == 1
        assert len(parsed.table_rows_by_page.get(1, [])) >= 6, "Expected structured LFT table rows"

        result = literature_service.screen_and_split(parsed, filename=pdf_path.name)
        assert result.is_reportable is True
        assert result.patient_cases_count == 1
        assert len(result.individual_cases) == 1

        case = result.individual_cases[0]
        assert "61" in case.patient.age or "61" in str(case.patient)
        assert "male" in case.patient.sex.lower()
        assert "cardioril" in case.product.product_name.lower()
        assert any(k in case.reaction.adverse_event.lower() for k in ["hepatitis", "dili", "jaundice", "autoimmune"])

        # Grounding & Citations
        assert len(case.citations) >= 5, "Case must have fact-level citations"
        assert case.patient.citation.page_number == 1
        assert case.product.citation.page_number == 1
        assert case.reaction.citation.page_number == 1
        assert case.reaction.citation.anchor_level in ("LEVEL_1_EXACT_VISUAL", "LEVEL_2_PAGE_TEXT")

        # Table Lab Tests Grounding
        alt_test = next((lt for lt in case.lab_tests if "alt" in lt.test_name.lower()), None)
        assert alt_test is not None, "ALT must be extracted from LFT table"
        assert "680" in alt_test.value
        assert alt_test.citation is not None
        assert alt_test.citation.anchor_level in ("LEVEL_1_EXACT_VISUAL", "LEVEL_2_PAGE_TEXT")

    def test_lit_02_sjs_single_case(self):
        pdf_path = LITERATURE_PDF_DIR / "article_02_sjs_case.pdf"
        assert pdf_path.exists()

        parsed = PDFParser.parse_pdf_file(pdf_path)
        result = literature_service.screen_and_split(parsed, filename=pdf_path.name)

        assert result.is_reportable is True
        assert result.patient_cases_count == 1
        case = result.individual_cases[0]

        assert "24" in case.patient.age
        assert "female" in case.patient.sex.lower()
        assert "neuroval" in case.product.product_name.lower()
        assert "stevens-johnson" in case.reaction.adverse_event.lower() or "sjs" in case.reaction.adverse_event.lower()
        assert case.reaction.hospitalization is True or "Hospitalization" in case.reaction.seriousness_criteria

        # Grounding
        assert case.reaction.citation.page_number == 1
        assert case.product.citation.page_number == 1

    def test_lit_03_multicase_series_splitting_and_isolation(self):
        pdf_path = LITERATURE_PDF_DIR / "article_03_multicase_series.pdf"
        assert pdf_path.exists()

        parsed = PDFParser.parse_pdf_file(pdf_path)
        # Verify PyMuPDF extracted all 3 matrix table rows
        table_rows = parsed.table_rows_by_page.get(1, [])
        assert len(table_rows) == 3, f"Expected 3 table rows for the 3 cases, got {len(table_rows)}"

        result = literature_service.screen_and_split(parsed, filename=pdf_path.name)
        assert result.is_reportable is True
        assert result.patient_cases_count == 3
        assert len(result.individual_cases) == 3

        case_1 = result.individual_cases[0]
        case_2 = result.individual_cases[1]
        case_3 = result.individual_cases[2]

        # Case 1: A.J., 45M, Cardioril 20 mg QD, Erythema Multiforme Major, Serious
        assert "A.J." in case_1.patient.identifier
        assert "45" in case_1.patient.age
        assert "Cardioril" in case_1.product.product_name
        assert "Erythema Multiforme" in case_1.reaction.adverse_event
        assert case_1.reaction.hospitalization is True or "Hospitalization" in case_1.reaction.seriousness_criteria

        # Case 2: B.L., 62F, Corzapan 10 mg QD, Subacute Cutaneous Lupus, Non-serious
        assert "B.L." in case_2.patient.identifier
        assert "62" in case_2.patient.age
        assert "Corzapan" in case_2.product.product_name
        assert "Lupus" in case_2.reaction.adverse_event or "SCLE" in case_2.reaction.adverse_event

        # Case 3: C.M., 38F, Cardioril 10 mg QD, Acute Angioedema & Urticaria, Life-threatening
        assert "C.M." in case_3.patient.identifier
        assert "38" in case_3.patient.age
        assert "Cardioril" in case_3.product.product_name
        assert "Urticaria" in case_3.reaction.adverse_event or "Angioedema" in case_3.reaction.adverse_event
        assert case_3.reaction.life_threatening is True or "Life-threatening" in case_3.reaction.seriousness_criteria

        # Grounding Isolation Verification:
        # Case 1 evidence must not cite Case 2 or Case 3 sections
        assert "B.L." not in case_1.patient.citation.verbatim_snippet
        assert "C.M." not in case_1.patient.citation.verbatim_snippet
        # Case 2 evidence must not cite Case 1 or Case 3 sections
        assert "A.J." not in case_2.patient.citation.verbatim_snippet
        assert "C.M." not in case_2.patient.citation.verbatim_snippet
        # Case 3 evidence must not cite Case 1 or Case 2 sections
        assert "A.J." not in case_3.patient.citation.verbatim_snippet
        assert "B.L." not in case_3.patient.citation.verbatim_snippet

    def test_lit_04_negative_control_preclinical(self):
        pdf_path = LITERATURE_PDF_DIR / "article_04_preclinical_review.pdf"
        assert pdf_path.exists()

        parsed = PDFParser.parse_pdf_file(pdf_path)
        result = literature_service.screen_and_split(parsed, filename=pdf_path.name)

        assert result.is_reportable is False
        assert result.patient_cases_count == 0
        assert len(result.individual_cases) == 0
        assert result.exclusion_reason is not None
        assert any(k in result.exclusion_reason.lower() for k in ["preclinical", "in-vitro", "rat", "animal", "zero human"])

    def test_lit_05_negative_control_meta_analysis(self):
        pdf_path = LITERATURE_PDF_DIR / "article_05_meta_analysis_review.pdf"
        assert pdf_path.exists()

        parsed = PDFParser.parse_pdf_file(pdf_path)
        result = literature_service.screen_and_split(parsed, filename=pdf_path.name)

        assert result.is_reportable is False
        assert result.patient_cases_count == 0
        assert len(result.individual_cases) == 0
        assert result.exclusion_reason is not None
        assert any(k in result.exclusion_reason.lower() for k in ["meta-analysis", "systematic review", "aggregate", "trials"])

    def test_lit_06_buried_case_study_with_cardiac_biomarkers(self):
        pdf_path = LITERATURE_PDF_DIR / "article_06_buried_case_study.pdf"
        assert pdf_path.exists()

        parsed = PDFParser.parse_pdf_file(pdf_path)
        assert parsed.page_count == 2
        # Page 2 has Table 1 with cardiac biomarker progression
        assert len(parsed.table_rows_by_page.get(2, [])) >= 5

        result = literature_service.screen_and_split(parsed, filename=pdf_path.name)
        assert result.is_reportable is True
        assert result.patient_cases_count == 1
        case = result.individual_cases[0]

        assert "H.L." in case.patient.identifier
        assert "68" in case.patient.age
        assert "female" in case.patient.sex.lower()
        assert any(k in case.product.product_name.lower() for k in ["nivolumab", "ipilimumab", "opdivo", "yervoy"])
        assert "myocarditis" in case.reaction.adverse_event.lower()

        # Check cardiac biomarker extraction and page 2 evidence grounding
        trop_test = next((lt for lt in case.lab_tests if "troponin" in lt.test_name.lower()), None)
        assert trop_test is not None, "Troponin T must be extracted"
        assert "1.84" in trop_test.value
        assert trop_test.citation is not None
        assert trop_test.citation.anchor_level in ("LEVEL_1_EXACT_VISUAL", "LEVEL_2_PAGE_TEXT")

    def test_lit_07_complex_screening_cohort_filtering_and_splitting(self):
        pdf_path = LITERATURE_PDF_DIR / "article_07_complex_screening_case.pdf"
        assert pdf_path.exists()

        parsed = PDFParser.parse_pdf_file(pdf_path)
        assert parsed.page_count == 2
        # Table 1 on page 2 directly contrasts Registry (n=420) with Patient T.K. and Patient M.S.
        assert len(parsed.table_rows_by_page.get(2, [])) >= 6

        result = literature_service.screen_and_split(parsed, filename=pdf_path.name)
        assert result.is_reportable is True
        # Registry cohort of 420 must NOT be extracted; exactly 2 distinct cases
        assert result.patient_cases_count == 2
        assert len(result.individual_cases) == 2

        case_1 = result.individual_cases[0]
        case_2 = result.individual_cases[1]

        # Case 1: Patient T.K., Infliximab, Interstitial Pneumonitis
        assert "T.K." in case_1.patient.identifier
        assert "54" in case_1.patient.age
        assert "infliximab" in case_1.product.product_name.lower()
        assert "pneumonitis" in case_1.reaction.adverse_event.lower() or "interstitial" in case_1.reaction.adverse_event.lower()

        # Case 2: Patient M.S., Leflunomide, Organizing Pneumonia / COP
        assert "M.S." in case_2.patient.identifier
        assert "41" in case_2.patient.age
        assert "leflunomide" in case_2.product.product_name.lower()
        assert any(k in case_2.reaction.adverse_event.lower() for k in ["organizing pneumonia", "cop", "boop"])

        # Grounding & Patient Isolation
        assert "M.S." not in case_1.patient.citation.verbatim_snippet
        assert "T.K." not in case_2.patient.citation.verbatim_snippet
        assert case_1.reaction.citation.anchor_level in ("LEVEL_1_EXACT_VISUAL", "LEVEL_2_PAGE_TEXT")
        assert case_2.reaction.citation.anchor_level in ("LEVEL_1_EXACT_VISUAL", "LEVEL_2_PAGE_TEXT")


class TestFixAStructuredTableEvidencePriority:
    """
    Focused tests for FIX A: Generic structured-table evidence priority for lab/biomarker facts.
    """
    def test_lit_01_alt_resolves_to_table_1_bbox(self):
        pdf_path = LITERATURE_PDF_DIR / "article_01_dili_case.pdf"
        parsed = PDFParser.parse_pdf_file(pdf_path)
        result = literature_service.screen_and_split(parsed, filename=pdf_path.name)
        case = result.individual_cases[0]
        alt_test = next((lt for lt in case.lab_tests if "alt" in lt.test_name.lower()), None)
        assert alt_test is not None, "ALT must be present"
        assert alt_test.citation is not None, "ALT must have a citation"
        assert alt_test.citation.bounding_box is not None, "ALT citation must have bounding box"
        bbox = alt_test.citation.bounding_box
        # Table 1 ALT row coordinates: x0 ~ 313.0, y0 ~ 224.2 (right column table, NOT left column text at x0 ~ 35-37)
        assert bbox["x0"] >= 300.0, f"Expected table column x0 >= 300, got {bbox['x0']}"
        assert bbox["y0"] >= 200.0, f"Expected table row y0 >= 200, got {bbox['y0']}"
        assert "Table 1" in alt_test.citation.page_or_location or "table" in alt_test.citation.page_or_location.lower()

    def test_lit_06_cardiac_biomarker_resolves_to_table_1_bbox(self):
        pdf_path = LITERATURE_PDF_DIR / "article_06_buried_case_study.pdf"
        parsed = PDFParser.parse_pdf_file(pdf_path)
        result = literature_service.screen_and_split(parsed, filename=pdf_path.name)
        case = result.individual_cases[0]
        trop_test = next((lt for lt in case.lab_tests if "troponin" in lt.test_name.lower()), None)
        assert trop_test is not None, "Troponin T must be present"
        assert trop_test.citation is not None, "Troponin T must have citation"
        # Table 1 with cardiac biomarkers is on Page 2
        assert trop_test.citation.page_number == 2, f"Expected page 2 table, got {trop_test.citation.page_number}"
        assert trop_test.citation.bounding_box is not None

    def test_lit_07_table_derived_patient_fact_resolves_to_table_row(self):
        pdf_path = LITERATURE_PDF_DIR / "article_07_complex_screening_case.pdf"
        parsed = PDFParser.parse_pdf_file(pdf_path)
        result = literature_service.screen_and_split(parsed, filename=pdf_path.name)
        assert len(result.individual_cases) == 2
        case_tk = result.individual_cases[0]
        case_ms = result.individual_cases[1]
        assert "T.K." in case_tk.patient.identifier
        assert "M.S." in case_ms.patient.identifier
        # Grounding should preserve patient scope
        assert "M.S." not in case_tk.patient.citation.verbatim_snippet
        assert "T.K." not in case_ms.patient.citation.verbatim_snippet

    def test_lit_03_multicase_table_evidence_remains_patient_scoped(self):
        pdf_path = LITERATURE_PDF_DIR / "article_03_multicase_series.pdf"
        parsed = PDFParser.parse_pdf_file(pdf_path)
        result = literature_service.screen_and_split(parsed, filename=pdf_path.name)
        assert len(result.individual_cases) == 3
        # Each patient's citation must be strictly scoped to their row/section
        for i, c in enumerate(result.individual_cases):
            for j, other_c in enumerate(result.individual_cases):
                if i != j and other_c.patient.identifier not in ("Not stated", ""):
                    assert other_c.patient.identifier not in c.patient.citation.verbatim_snippet


class TestFixBRegulatorySeriousnessReconciliation:
    """
    Focused tests for FIX B: Generic regulatory seriousness reconciliation.
    """
    def test_hospitalization_true_reconciles_to_serious(self):
        from app.schemas.extraction_schema import ReactionData
        rx = ReactionData(hospitalization=True)
        assert rx.hospitalization is True
        assert "Hospitalization" in rx.seriousness_criteria

    def test_life_threatening_true_reconciles_to_serious(self):
        from app.schemas.extraction_schema import ReactionData
        rx = ReactionData(life_threatening=True)
        assert rx.life_threatening is True
        assert "Life-threatening" in rx.seriousness_criteria

    def test_death_true_reconciles_to_serious(self):
        from app.schemas.extraction_schema import ReactionData
        rx = ReactionData(death=True)
        assert rx.death is True
        assert "Death" in rx.seriousness_criteria

    def test_medically_important_true_reconciles_to_serious(self):
        from app.schemas.extraction_schema import ReactionData
        rx = ReactionData(medically_important=True)
        assert rx.medically_important is True
        assert "Other Medically Important Condition" in rx.seriousness_criteria

    def test_seriousness_criteria_with_valid_criterion_reconciles_to_serious(self):
        from app.schemas.extraction_schema import ReactionData
        rx = ReactionData(seriousness_criteria=["Inpatient Hospitalization", "Medically Significant"])
        assert rx.hospitalization is True
        assert rx.medically_important is True
        assert rx.life_threatening is False
        assert rx.death is False

    def test_explicit_non_serious_criteria_preserves_non_serious(self):
        from app.schemas.extraction_schema import ReactionData
        rx = ReactionData(seriousness_criteria=["Non-serious"], hospitalization=True)
        assert rx.hospitalization is False
        assert rx.life_threatening is False
        assert rx.death is False
        assert rx.medically_important is False

    def test_missing_or_unknown_seriousness_does_not_invent_seriousness(self):
        from app.schemas.extraction_schema import ReactionData
        rx = ReactionData()
        assert rx.hospitalization is False
        assert rx.life_threatening is False
        assert rx.death is False
        assert rx.medically_important is False
        assert rx.seriousness_criteria == []
