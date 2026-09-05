# AI PIPELINE SPECIFICATION — CLINEVO SMART INBOX ASSISTANT

## 1. Overview & Operational Philosophy

The AI Pipeline automates document understanding, regulatory triage classification, and precision fact extraction for pharmacovigilance intake communications. Pharmacovigilance is a strictly regulated domain (governed by FDA 21 CFR 314.80, EMA GVP Module VI, and ICH E2B(R3)); downstream medical reviewers and regulatory authorities require zero-hallucination fidelity, complete auditable traceability to source evidence, and explicit differentiation between stated facts and unmentioned parameters.

The pipeline processes bounded intake documents using complete context rather than fragmented vector chunking, combining deterministic local structural parsing (MIME headers, PDF layouts, table matrices) with native multimodal generative AI (Gemini Flash) for clinical reasoning and visual evidence inspection.

---

## 2. Pipeline Stages (A through P)

### Stage A: Email Normalization
- **Implementation**: `ai-service-python/app/parsers/email_parser.py` (`EmailParser`)
- **Input**: Raw RFC 5322 MIME email bytes (`.eml` or `.msg`).
- **Processing**:
  - Parses standard RFC headers: `From`, `To`, `Date`, `Subject`, `Message-ID`.
  - Splits compound `From` headers into display name and email address.
  - Extracts plain text bodies; if absent, cleans HTML body using regex-based tag stripping.
  - Traverses MIME multipart trees to isolate all file attachments, recording filename, MIME type, payload bytes, and byte size.
- **Output**: Normalized `ParsedEmail` object containing structured metadata, clean body text, and detached attachments.
- **Failure Handling**: If MIME parsing fails or character encoding is corrupted, the parser applies UTF-8 with character replacement (`errors="replace"`), falling back to raw ASCII body text.

### Stage B: PDF Inspection & Flavor Classification
- **Implementation**: `ai-service-python/app/parsers/pdf_parser.py` (`PDFParser`)
- **Input**: Raw PDF bytes (`.pdf`).
- **Processing**:
  - PyMuPDF (`fitz`) opens document and inspects page count, character count, embedded font descriptors, and image xref streams.
  - Computes total character density per page.
  - Classifies document flavor into one of four regulatory categories:
    1. `digital_form`: High character count with structured form keywords (e.g. "CIOMS-I", "FDA 3500A", "MedWatch", "Adverse Event Report").
    2. `scanned_handwritten`: Low character density (<200 characters across <=3 pages) with raster bitmap backgrounds.
    3. `literature_article`: High text volume containing academic markers ("Abstract", "References", "Case Series", "Journal", "DOI").
    4. `non_english`: Document containing foreign regulatory linguistic markers (e.g. Spanish AEMPS or German BfArM terms).
- **Output**: `ParsedPDF` instance with page-indexed text, table grids, embedded images, and flavor tag.
- **Failure Handling**: If PyMuPDF encounters a malformed PDF structure, it logs a warning and attempts page-by-page recovery.

### Stage C: Digital PDF Processing
- **Implementation**: `ai-service-python/app/parsers/pdf_parser.py`
- **Input**: Digital PDF stream.
- **Processing**:
  - Extracts text while preserving spatial layout and section headers.
  - Executes PyMuPDF `find_tables()` to detect rectangular table borders.
  - Reconstructs two-dimensional table matrices into standardized GitHub-flavored Markdown tables.
  - Injects formatted tables into the per-page text stream under `[STRUCTURED TABLES ON PAGE N]`.
- **Output**: Text representation maintaining key-value form relationships and structured laboratory matrices.
- **Failure Handling**: Table detection exceptions default to standard text block extraction without failing the document parse.

### Stage D: Scanned & Handwritten Processing
- **Implementation**: `ai-service-python/app/parsers/pdf_parser.py` & `ai-service-python/app/services/icsr_extractor.py`
- **Input**: Scanned or photocopy PDF / raster image.
- **Processing**:
  - Renders pages to high-resolution 150 DPI PIL images via `page.get_pixmap()`.
  - Dispatches page images directly to Gemini Flash native multimodal vision engine.
  - Instructs model to transcribe handwriting, recognize handwritten checkboxes/dosing annotations, and assess visual clarity.
- **Output**: Transcribed text integrated with multimodal extraction confidence scores.
- **Failure Handling**: If rendering fails, raw extracted text is passed with a flagged warning: `OCR_FALLBACK_APPLIED`.

### Stage E: Image Handling & Meaningful Image Flagging
- **Implementation**: `ai-service-python/app/parsers/pdf_parser.py` & `app/schemas/extraction_schema.py`
- **Input**: Embedded raster images (JPEG, PNG) extracted from PDF xref streams.
- **Processing**:
  - Filters out decorative elements, icons, and bullets (dimension threshold: width >= 100px and height >= 100px).
  - Supplies candidate images to Gemini Flash multimodal context.
  - Evaluates whether the image depicts a physical defect (vial contamination, broken seal, particulate matter) or clinical symptom (rash).
  - If a physical defect is detected, populates `photo_description` and asserts `requires_human_review = True`.
- **Output**: `photo_detected: bool`, `photo_description: str`, `requires_human_review: bool`.
- **Failure Handling**: Corrupted image streams are skipped; text-only extraction continues uninterrupted.

### Stage F: Non-English Handling & Translation Traceability
- **Implementation**: `ai-service-python/app/parsers/pdf_parser.py` & `app/services/icsr_extractor.py`
- **Input**: Foreign-language documents (Spanish, German).
- **Processing**:
  - Lexical keyword matching detects language (`Spanish`, `German`, `English`).
  - Gemini Flash translates clinical information into English for ICH E2B standardization.
  - Preserves verbatim foreign-language citations in `verbatim_snippet` alongside translated values to guarantee cross-lingual traceability.
- **Output**: `language_detected: str`, English standardized fields, original-language verbatim source citations.
- **Failure Handling**: If language detection is ambiguous, model defaults to English and extracts text verbatim.

### Stage G: Regulatory Triage Classification
- **Implementation**: `ai-service-python/app/services/triage_service.py` (`TriageService`)
- **Input**: Complete document context (email headers, body, attached PDF text/tables).
- **Processing**:
  - Evaluates message against four regulatory buckets:
    - **Safety Report (ICSR)**: Minimum 4 criteria loosely present (Patient, Reporter, Product, Adverse Event).
    - **Quality Complaint (PQC)**: Product defect, packaging breach, contamination, counterfeit.
    - **Info Request (MI)**: Product inquiries without adverse reactions or defects.
    - **Not Relevant**: Commercial spam, conference promotions, administrative notes.
  - Supports multi-label assignment (e.g. PQC + ICSR).
  - Calculates calibrated confidence (0.0 to 1.0) and generates 1-line regulatory rationale per bucket.
  - Produces 10–15 sentence executive summary explaining clinical significance and urgency.
- **Output**: `TriageResult` object.
- **Failure Handling**: Fallback to rule-based keyword classification if LLM service is unavailable.

### Stage H: Safety Fact Extraction (ICH E2B)
- **Implementation**: `ai-service-python/app/services/icsr_extractor.py` (`ICSRExtractor`)
- **Input**: Document context + `TriageResult`.
- **Processing**:
  - Extracts ICH E2B(R3) safety entities:
    - **Patient**: Age, sex, weight, relevant medical history.
    - **Reporter**: Name, role (HCP, consumer), institution, country, contact details.
    - **Product**: Product name, dose, frequency, route, lot number, expiry date, indication.
    - **Reaction**: Adverse event term, onset date, outcome, seriousness criteria, dechallenge, rechallenge.
    - **Lab Tests**: Structured list of `{ test_name, value, unit, reference_range, test_date }`.
    - **Narrative**: Chronological plain-language clinical summary.
  - **Ground Rule**: Unmentioned attributes are assigned `"Not stated"` with zero hallucinated guessing.
- **Output**: Populated `ExtractionResult` containing `PatientData`, `ReporterData`, `ProductData`, `ReactionData`.
- **Failure Handling**: Unparseable responses default safely to empty records with all fields set to `"Not stated"`.

### Stage I: Quality Complaint (PQC) Extraction
- **Implementation**: `ai-service-python/app/services/icsr_extractor.py`
- **Input**: Document context where PQC is indicated.
- **Processing**:
  - Extracts product name, lot/batch number, defect type, defect description, packaging breach status (`True`/`False`).
  - Evaluates accompanying photos for physical evidence of defect.
  - Sets `requires_human_review = True` for contaminated or breached products.
- **Output**: `QualityComplaintData` sub-model.
- **Failure Handling**: If defect details are absent, `defect_type` is set to `"Not stated"`.

### Stage J: Medical Information (MI) Request Extraction
- **Implementation**: `ai-service-python/app/services/icsr_extractor.py`
- **Input**: Document context where MI is indicated.
- **Processing**:
  - Extracts subject/topic, inquiry type (e.g., Dosing, Administration, Compatibility, Stability), and specific question text.
- **Output**: `MedicalInfoData` sub-model.
- **Failure Handling**: Defaults to `"Not stated"` if question cannot be clearly isolated.

### Stage K: Scientific Literature Screening
- **Implementation**: `ai-service-python/app/services/literature_service.py` (`LiteratureService`)
- **Input**: Academic reprint / journal article PDF text.
- **Processing**:
  - Determines reportability (`is_reportable: bool`):
    - Reportable: Contains at least one identifiable human patient experiencing an adverse reaction associated with a suspect medicinal product.
    - Non-Reportable: Animal/in-vitro studies, systematic reviews/meta-analyses with aggregate data, reviews without individual patient cases.
  - Classifies study type: `Single Case Report`, `Multi-Patient Case Series`, `Preclinical Animal/In-Vitro`, `Systematic Review / Meta-Analysis`.
  - Provides regulatory exclusion reason if non-reportable.
  - Generates 10–15 sentence literature screening summary.
- **Output**: `LiteratureScreenResult` metadata.
- **Failure Handling**: Keyword-based fallback screens for animal/meta-analysis markers.

### Stage L: Multi-Patient Case Series Splitting (+30% Bonus)
- **Implementation**: `ai-service-python/app/services/literature_service.py`
- **Input**: Case-bearing literature article containing multiple patients.
- **Processing**:
  - Scans clinical presentation for distinct individual patients (e.g. Patient 1 A.J., Patient 2 B.L., Patient 3 C.M.).
  - Extracts independent ICSR records for each patient, isolating patient demographics, specific dosing, and adverse event progression.
  - Prevents merging multiple patients into a single report.
- **Output**: `individual_cases: List[ExtractionResult]` with `patient_cases_count`.
- **Failure Handling**: If splitting fails, creates a single consolidated case flagged for manual triage splitting.

### Stage M: Confidence & Uncertainty Scoring
- **Implementation**: `ai-service-python/app/schemas/triage_schema.py` & `icsr_extractor.py`
- **Processing**:
  - Every triage label provides a calibrated confidence float between 0.0 and 1.0.
  - Scanned/handwritten extractions apply lower confidence weights to indicate handwriting uncertainty.
  - Reviewer UI displays confidence badges (Green >= 0.85, Amber 0.60–0.84, Red < 0.60) to guide human inspection.

### Stage N: Evidence & Source Traceability Mapping
- **Implementation**: `ai-service-python/app/schemas/extraction_schema.py` (`SourceCitation`)
- **Processing**:
  - Every entity group (Patient, Reporter, Product, Reaction, Quality Complaint, Medical Info) includes a mandatory `SourceCitation`:
    - `source_type`: `'email'` or `'pdf'`
    - `page_or_location`: e.g. `'Email body'`, `'Page 1'`, `'Section 6'`
    - `verbatim_snippet`: Exact source sentence quoted verbatim.
- **Output**: Enables one-click reviewer source verification on the frontend split-view.

### Stage O: Deterministic Schema Validation
- **Implementation**: Pydantic v2 validation in FastAPI router.
- **Processing**:
  - All LLM JSON responses pass through strict Pydantic model validation.
  - Type coercions, range constraints (`ge=0.0, le=1.0`), and null checks are enforced.
- **Output**: Validated typed objects or HTTP 422 validation errors.

### Stage P: Human-in-the-Loop Review
- **Implementation**: Spring Boot Reviewer API + Angular Workspace.
- **Processing**:
  - Triage queue displays urgent and low-confidence items at top.
  - Reviewer inspects side-by-side: original document on left, editable AI fields on right.
  - Reviewer accepts, overrides classification, or modifies extracted values.
  - All actions recorded in immutable 21 CFR Part 11 audit log.
