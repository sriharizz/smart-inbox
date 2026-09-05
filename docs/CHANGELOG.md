# PROJECT CHANGELOG — CLINEVO SMART INBOX ASSISTANT

All significant architectural, AI, dataset, testing, and engineering milestones are recorded in this document.

## [2026-09-05] — Phase 4 Angular Reviewer Dashboard & End-to-End System Verification

### Frontend Reviewer Workspace (Phase 4)
- **Angular 18 Enterprise UI**: Built standalone Angular 18 single-page application (`frontend-angular/`) with clean, restrained Clinevo corporate aesthetics (white/light surfaces, deep blue accents, zero neon/glassmorphism/gradients).
- **Triage Review Queue**: Responsive, high-density table displaying urgency badges (`CRITICAL`, `EXPEDITED`, `STANDARD`), multi-category flags (ICSR, PQC, MI), confidence scores, and action shortcuts.
- **Split-Screen Case Workspace**: Implemented Case 004 review environment featuring dual-pane layout: source document inspector on the left, editable ICH E2B and PQC fields on the right, and interactive one-click verbatim citation inspector.
- **Human Review Actions & Overrides**: Integrated Accept and Override workflows requiring mandatory clinical justification with real-time optimistic UI updates.
- **Literature Screening & Case Splitting (+30% Bonus)**: Built dedicated literature screening view demonstrating automated article classification, reportability decisions, and disaggregation of multi-patient clinical case series into distinct ICSR records.
- **Part 11-Oriented Audit Trail Viewer**: Created chronological, immutable audit trail interface displaying all automated predictions, human overrides, field modifications, and clinical rationales.
- **Zero-Error Production Build**: Verified Angular production build (`ng build`) compiling with 0 errors and serving via modern development proxy to Spring Boot orchestrator.

---

## [2026-09-05] — Phase 3 Spring Boot 3 Orchestrator, Ingestion Pipeline & Persistence

### Backend Orchestration (Phase 3)
- **Spring Boot 3 Core**: Initialized Java 21 Spring Boot 3.3.3 orchestration service (`backend-spring/`) with Spring Web, Spring Data JPA, and Jakarta Mail.
- **Dual-Mode Ingestion Engine**: Implemented `IngestionSource` abstraction supporting interchangeable `FIXTURE` mode (reading synthetic `.eml` corpus) and `IMAP` mode (Angus Mail connection to live IMAP mailboxes), normalizing messages into standard domain entities.
- **Asynchronous Task Queue**: Configured `ThreadPoolTaskExecutor` (core 4, max 8, queue 100) to decouple mailbox ingestion from downstream AI inference, ensuring non-blocking wire-speed intake.
- **Resilient AI Gateway**: Implemented `AiGatewayClient` calling Python FastAPI microservice (`/api/v1/process-eml`, `/api/v1/process-pdf`, `/api/v1/literature/screen-and-split`).
- **Domain Persistence Layer**: Built JPA entities (`IntakeMessageEntity`, `AttachmentEntity`, `IcsrReportEntity`, `PqcReportEntity`, `MedicalInfoEntity`, `AuditEventEntity`, `LiteratureArticleEntity`) and repositories.
- **Reviewer & Audit APIs**: Created `MessageController` (triage queue, detailed message view, accept/override endpoints), `AuditController` (Part 11-oriented immutable audit trail), and `LiteratureController` (literature reprint screening and case disaggregation).
- **Dual-Profile Database**: Configured embedded H2 in Oracle compatibility mode (`MODE=Oracle`) for zero-friction demo and wrote production Oracle PL/SQL schema (`database/oracle/schema.sql`) with sequences and `TRG_AUDIT_LOG_IMMUTABLE` trigger.
- **Integration Tests**: Automated tests passed (`AuditServiceTest`, `FixtureIngestionTest`, `SmartInboxApplicationTests`) with `BUILD SUCCESS`.

---

## [2026-09-05] — Final Dataset Reconciliation, AI Microservice Implementation & Documentation Suite

### Dataset & Ground Truth
- **Reconciliation & Freeze**: Completed comprehensive cross-source reconciliation against physical `.eml`, `.pdf`, and `.jpg` artifacts. Established physical files as the authoritative source of truth.
- **Benchmark V3.0.0**: Built canonical `test-data/ground_truth/benchmark.json` comprising 27 canonical cases with semantic acceptable terms, explicit `"Not stated"` handling, and verbatim citation references.
- **Physical Manifest**: Created `test-data/manifest.json` with verified SHA-256 hashes for all 11 emails, 20 PDFs, and 2 image assets. Formally declared the 2nd scanned/handwritten PDF requirement as **DEFERRED**.
- **Master Catalog**: Synchronized `test-data/TEST_CASES_AND_EMAILS.md` with exact physical headers and clinical data.
- **Dataset Validator**: Created and passed `scripts/validate_dataset_final.py` (27/27 test suites passed, 0 failures, 1 deferred).

### AI Microservice (Phase 2)
- **FastAPI Core**: Implemented high-performance asynchronous REST microservice under `ai-service-python/app/`.
- **Gemini Flash Engine**: Centralized Google GenAI SDK client (`GeminiClient`) with `tenacity` exponential backoff retries, jitter, and automatic failover between `gemini-2.5-flash` and `gemini-flash-latest`.
- **Pure Live AI Execution**: Disabled pre-computed cache lookups (`USE_LOCAL_CACHE = False`), ensuring 100% dynamic live inference across all triage and extraction tasks.
- **Layout & Table Parsing**: Implemented `PDFParser` utilizing PyMuPDF (`fitz`) to detect and reconstruct table grids into markdown tables and render high-resolution raster images for multimodal vision.
- **MIME Parsing**: Built `EmailParser` extracting RFC 5322 headers, clean plain-text/HTML bodies, and nested MIME attachments.
- **Multimodal Defect Inspection**: Implemented photographic defect analysis detecting vial particulate and cracked pump collars, automatically setting `requires_human_review = True`.
- **Literature Screening & Case Splitting (+30% Bonus)**: Built `LiteratureService` to screen academic reprints and split multi-patient case series (e.g. 1 article -> 3 distinct ICSR records) with reportability classification and exclusion rationales.
- **Automated Testing**: Created and passed unit test suites (`tests/test_parsers.py` and `tests/test_api_endpoints.py`).

### Engineering Documentation Record
- Established comprehensive documentation suite:
  - `docs/ARCHITECTURE.md`: 3-tier polyglot architecture, component contracts, end-to-end data flow.
  - `docs/AI_PIPELINE.md`: Detailed specification of all 16 processing stages (A through P).
  - `docs/DATA_AND_GROUND_TRUTH.md`: Synthetic data principles, inventory, benchmark methodology, deferred item.
  - `docs/PROMPT_DESIGN.md`: Full prompt specifications, system instructions, schemas, grounding rules.
  - `docs/DECISIONS.md`: Architecture Decision Records (ADR-001 through ADR-008).
  - `docs/EVALUATION.md`: Benchmark metrics, scoring criteria, measured baseline performance.
  - `docs/LIMITATIONS_AND_PRODUCTION.md`: Current prototype limitations vs. enterprise production roadmap.
  - `README.md`: Evaluator-friendly repository overview, setup instructions, and architecture guide.

---

## [2026-09-04] — Synthetic Dataset Expansion & PDF Flavor Scaffolding

### Dataset
- Generated initial synthetic email corpus (`email_01.eml` to `email_10.eml`) covering ICSR, PQC, MI, and Not Relevant cases.
- Generated initial PDF corpus covering digital CIOMS-I/FDA 3500A forms, defect reports, scanned notes, and medical journal articles.
- Generated standalone photographic defect assets (`contaminated_vial_photo.jpg`).

---

## [2026-09-03] — Project Scaffolding & Assignment Analysis

### Project Initiation
- Extracted official assignment requirements from `Clinevo_Assignment.pdf`.
- Created `ASSIGNMENT_SPEC.md` mapping scoring criteria, core functional requirements, and bonus literature screening.
- Scaffolding of polyglot directories: `ai-service-python/`, `backend-spring/`, `frontend-angular/`, `database/`.
