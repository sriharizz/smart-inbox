# CLINEVO TECHNOLOGIES — SMART INBOX ASSISTANT
## Master Assignment Specification & Scoring Rubric (Source of Truth)

**Role**: Forward Deployment / GenAI Integration Engineer (AI Full Stack Developer)  
**Target Domain**: Pharmacovigilance (PV) & Patient Safety Document Processing  
**Max Potential Score**: **100% (Core) + 30% (Bonus) = 130%**

---

## 1. Scoring Matrix & Priority Breakdown

| Priority | Evaluation Area | Weight | Exact Criteria from Clinevo | How We Guarantee Full Score |
| :---: | :--- | :---: | :--- | :--- |
| **P0** | **Core Functionality** | **30%** | Email/PDF intake, all 4 PDF types, tables/images, sorting, and fact extraction working end-to-end. | Fully automated intake: Mailbox connector + file upload + batch runner; all 4 PDF flavors parsed; tables extracted into JSON matrices; image descriptions flagged; multi-bucket classification. |
| **P0** | **AI / LLM Quality** | **25%** | Good prompt design, structured outputs, sensible confidence scoring, saying "unknown" / "Not stated" instead of guessing. | Strict Pydantic / JSON schemas; calibrated confidence score (0.0 to 1.0) on every single field; explicit prohibition against hallucination/guessing ("Not stated" if absent). |
| **P1** | **Code & Architecture** | **20%** | Clean separation across the stack, sensible API design, readable code. | 3-tier polyglot architecture matching Clinevo's stack: Angular 18+ frontend ⟷ Spring Boot 3 API ⟷ Python FastAPI AI service ⟷ Oracle PL/SQL / embedded DB; async processing queue. |
| **P1** | **Getting the Domain Right** | **10%** | Correctly telling the 4 categories apart using regulatory pharmacovigilance rules. | Exact adherence to ICH E2B(R3) & GVP guidelines: Valid ICSR requires the 4 minimum criteria (Patient, Reporter, Drug, Reaction); PQC requires physical defect; MI requires product inquiry; multi-label support. |
| **P1** | **Traceability & Data Handling** | **10%** | Every fact links to its source; good audit logging; no real patient data used. | Every extracted fact contains `{value, confidence, source_page, source_snippet}`; complete immutable audit event log with timestamps tracking AI extraction vs. human reviewer overrides; 100% synthetic data. |
| **P2** | **Documentation** | **5%** | Clear README and write-up (2–5 pages); can explain your trade-offs. | Comprehensive `README.md` with 1-command launch instructions; 4-page technical whitepaper with architecture diagrams, prompt engineering choices, and production trade-offs. |
| **BONUS**| **Literature Screening** | **+30%** | Independent batch of article PDFs; screen for identifiable patient case; split multiple cases within one article; summary + relevance reason. | Dedicated Literature Screening engine: multi-case extractor splitting clinical case series (e.g. 1 article → 3 distinct ICSR cases) with dedicated Angular screening tab. |

---

## 2. Core Functional Requirements (Section 3 of Assignment)

### A. Intake Engine (Email & Attachments)
- Connect to a test mailbox (Live IMAP / local test suite).
- Extract sender, subject, date, body text.
- Grab all PDF attachments for processing (log other file types).
- Persist messages and extracted outputs into a queryable database.

### B. Understanding the 4 PDF Flavors
1. **Normal Digital PDF**: Direct layout-aware text extraction keeping form fields/labels aligned.
2. **Scanned / Handwritten**: Multimodal OCR / Vision AI model with confidence scores indicating handwriting uncertainty.
3. **Published Article**: Multi-column layout handling; isolate clinical patient cases, filter out references/citations.
4. **Non-English**: Language detection + English translation + persistent link back to original foreign text.
- **Universal PDF Requirements**:
  - Extract tables (lab values, dosing schedules) into structured rows/columns.
  - Detect and describe meaningful images (damaged product photos, rashes, filled checkbox forms) and flag for human review.
  - Generate a 10–15 sentence executive summary of each PDF explaining relevance.

### C. Multi-Label Classification (The 4 Buckets)
- **Safety Report (ICSR)**: Patient had an adverse reaction to a drug. Must loosely have all 4 minimum criteria: Identifiable Patient, Identifiable Reporter, Suspected Drug, Adverse Outcome.
- **Quality Complaint (PQC)**: Physical defect with the product itself (broken seal, wrong color, contamination, packaging defect, counterfeit).
- **Medical Info Request (MI)**: Questions about dosing, administration, drug interactions (no adverse event and no defect).
- **Not Relevant**: Marketing, spam, internal chatter.
- *Rule*: Multi-label support (a message can be both PQC and ICSR). Output confidence score and 1-line justification for every label.

### D. Precision Fact Extraction (With Source Linking)
- **Safety Report (ICSR) Fields**:
  - Patient: Age, sex, weight/height, relevant medical history.
  - Reporter: Name, role (HCP, consumer, etc.), country.
  - Product: Drug name, dose, route, start/stop dates.
  - Reaction: Adverse event term, onset date, outcome.
  - Severity: Seriousness criteria (death, hospitalization, life-threatening, disability, congenital anomaly, medically significant).
  - Narrative: AI-written plain language clinical narrative.
  - **Source Linking (Mandatory)**: Every fact MUST link back to exact source (email body or PDF page number + text snippet).
- **Quality Complaint Fields**: Product name, lot/batch number, defect description, photo mentioned (yes/no).
- **Info Request Fields**: Actual question(s) asked, product/topic.

### E. Reviewer Screen (Human-in-the-Loop)
- Reviewer queue listing incoming items with AI classification, confidence badges, and executive summaries.
- Side-by-side workspace: Document viewer (PDF / email text) alongside editable extracted fields.
- Reviewer actions: Accept, override classification, edit field values, add review comments.
- Immutable audit trail: Tracks every reviewer edit with user, timestamp, original value, and new value.

### F. Mandatory Ground Rules
- **Say "Not stated" / "unknown"**: Never guess or hallucinate. Show a confidence score for every extracted field.
- **Log Everything**: Traceable AI decisions and timestamped reviewer actions.
- **Synthetic Data Only**: Never use real patient data.
- **Batch Benchmark**: Automatically process 10–15 sample documents and report duration per document.

---

## 3. Optional Bonus: Literature Screening (+30%)
- Accept batch of medical literature article PDFs uploaded independently.
- Determine whether each article describes a reportable human safety case (filter out animal studies, in-vitro studies, review articles).
- **Split multiple cases within one article** (e.g., a paper reporting 3 patients must produce 3 separate ICSR records).
- Produce a summary and relevance justification for each case.

---

## 4. Test Data Requirements (Section 6)
All data synthetic / fictional:
1. **10 sample emails** with varying levels of detail about an adverse reaction.
2. **5 normal digital PDF attachments** (e.g., CIOMS-I / MedWatch filled report forms).
3. **2 scanned / handwritten style PDFs** (simulated clinical intake forms with handwriting).
4. **5 medical journal article PDFs** describing clinical cases (including multi-patient case series).
5. **2 non-English PDFs** with case-relevant content (e.g., Spanish, German).
6. **2 quality-complaint-only** and **2 info-request-only** examples.
7. **1 clearly irrelevant example** (marketing / spam).

---

## 5. Technology Stack & Enterprise Standards
- **Frontend**: Angular 18+ (Standalone components, TypeScript, modern clinical UI).
- **Backend API**: Spring Boot 3 (Java 21) (REST, JPA, async queue, audit logging).
- **AI Microservice**: Python 3.11 + FastAPI (Google GenAI SDK with Gemini 3.x Flash, PyMuPDF, Pydantic v2).
- **Database**: Dual profile:
  - Production: Oracle PL/SQL (DDL, sequences, triggers).
  - Zero-Friction Local: In-memory / file H2 in Oracle compatibility mode.
- **Execution Target**: 100% reliable local startup via single-command launch script (`run-local.bat`).

---

## 6. Official Requirement Traceability Matrix

| Official Requirement | Architectural Design | Implementation Module | Test Suite / Verification | Physical Evidence |
| :--- | :--- | :--- | :--- | :--- |
| **Connect to a real test mailbox** | Ingestion Abstraction: Dual-mode IMAP & Local Fixture | `backend-spring` MailboxService & Angus Mail adapter | Integration test + `test-data/emails/` | 11 authentic `.eml` files; IMAP polling service |
| **Parse incoming emails & attachments** | MIME RFC 5322 Parser + PyMuPDF | `ai-service-python/app/parsers/` (`email_parser.py`, `pdf_parser.py`) | `tests/test_parsers.py` | Extracts headers, body, and attached PDFs into JSON |
| **All 4 PDF flavors supported** | Flavor Classifier + Specialized Extractors | `ai-service-python/app/parsers/pdf_parser.py` | `tests/test_parsers.py` | 20 physical PDFs covering Digital, Scanned, Literature, Non-English |
| **Extract structured tables** | PyMuPDF Table Grid Finder -> Markdown | `ai-service-python/app/parsers/pdf_parser.py` | `tests/test_parsers.py` | Reconstructs 2D table matrices into Markdown tables |
| **Detect meaningful images & review flag** | Multimodal Image Extraction & Vision AI | `ai-service-python/app/services/icsr_extractor.py` | `tests/test_api_endpoints.py` | Flagged `contaminated_vial_photo.jpg` for review |
| **10-15 sentence executive summary** | Regulatory Clinical Synthesis Prompt | `ai-service-python/app/services/triage_service.py` | `tests/test_api_endpoints.py` | Triage output includes 10-15 sentence clinical summary |
| **Multi-label classification (4 buckets)** | Regulatory Triage Classifier (ICSR, PQC, MI, Spam) | `ai-service-python/app/services/triage_service.py` | `tests/test_api_endpoints.py` | Case 04 classified as both ICSR and PQC with confidence |
| **Extract ICH E2B safety facts** | Zero-Hallucination Structured Extractor | `ai-service-python/app/services/icsr_extractor.py` | `tests/test_api_endpoints.py` | Patient, Reporter, Product, Reaction extracted |
| **Strict "Not stated" policy** | Grounded System Prompt & Negative Constraints | `ai-service-python/app/services/icsr_extractor.py` | `eval_benchmark.py` | Unmentioned fields explicitly return "Not stated" |
| **Source linking for every fact** | Source Citation Pydantic Model | `ai-service-python/app/schemas/extraction_schema.py` | `eval_benchmark.py` | Every fact includes source_type, page, and verbatim snippet |
| **Reviewer Screen (Human-in-the-Loop)** | Split-view Workspace: Viewer + Editable Fields | `frontend-angular` Reviewer Component | E2E Browser Testing | Angular split-screen with Accept/Override controls |
| **Immutable Audit Trail** | 21 CFR Part 11 Event Logging | `backend-spring` AuditService & Oracle triggers | JPA Audit Tests | Records user, timestamp, original value, new value |
| **Automated Batch Benchmark** | Batch Evaluation Runner & Latency Metric | `ai-service-python/eval_benchmark.py` | `eval_benchmark.py` | Automated run across 27 cases reporting latency |
| **Literature Screening (+30% Bonus)** | Literature Screening & Multi-Case Splitter | `ai-service-python/app/services/literature_service.py`| `tests/test_api_endpoints.py` | Splits `article_03` into 3 cases; filters `article_04/05` |
| **Synthetic data compliance** | 100% Synthetic Patient & Clinical Corpus | `test-data/` dataset | `scripts/validate_dataset_final.py` | All patient names, reporters, lots are synthetic |
| **2nd Scanned/Handwritten PDF** | Reserved for physical paper form testing | Explicitly declared DEFERRED in manifest | `scripts/validate_dataset_final.py` | Marked DEFERRED in `manifest.json` |

