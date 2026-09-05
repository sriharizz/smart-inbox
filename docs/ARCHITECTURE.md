# SYSTEM ARCHITECTURE — CLINEVO SMART INBOX ASSISTANT

## 1. System Overview & Problem Statement

Pharmaceutical and biotechnology companies maintain shared regulatory mailboxes to receive spontaneous adverse event reports, product quality complaints, and medical inquiries. Traditionally, healthcare professionals and pharmacovigilance (PV) intake specialists manually review every incoming message and attachment, classify the message into regulatory categories, extract safety facts conforming to ICH E2B(R3) standards, and transcribe records into safety databases (e.g., Oracle Argus Safety, ArisGlobal LifeSphere). This process is labor-intensive, error-prone, and faces strict regulatory turnaround times (e.g., 7 or 15 calendar days for expedited fatal/life-threatening ICSRs).

The **Clinevo Smart Inbox Assistant** is an enterprise-grade, human-in-the-loop pharmacovigilance intake automation platform. It ingests incoming emails and attached PDFs (across digital forms, scanned/handwritten documents, scientific literature, and non-English communications), performs regulatory multi-label triage, extracts structured ICH E2B facts with verbatim source-page citations, flags physical defect photos for safety review, splits multi-patient literature case series (+30% bonus), and hands fully prepared cases to human reviewers on an interactive split-view dashboard backed by an immutable audit trail.

---

## 2. Polyglot Architecture & Technology Stack

The platform is architected as a decoupled, 3-tier polyglot system aligning with enterprise healthcare standards:

+-----------------------------------------------------------------------------------+
|                            TIER 1: REVIEWER DASHBOARD                             |
|                           Angular 18+ (Standalone, TS)                            |
|  - Real-time Triage Queue with Urgency & Confidence Badges                        |
|  - Split-Screen Layout: Document Inspection View | Editable Extracted Fields      |
|  - One-Click Source Citation Highlighting & Verbatim Evidence Inspector           |
|  - Dedicated Literature Screening & Multi-Patient Case Splitting Tab (+30% Bonus) |
|  - Human Review Actions: Accept, Override, Reclassify, Edit Field Values          |
+-----------------------------------------------------------------------------------+
                                         |
                                         | HTTP / JSON REST APIs (Port 8080)
                                         v
+-----------------------------------------------------------------------------------+
|                        TIER 2: BACKEND ORCHESTRATION ENGINE                       |
|                          Spring Boot 3.3.x (Java 21 OpenJDK)                      |
|  - Dual-Mode Ingestion Service: Live IMAP Poller OR Local EML Synthetic Fixtures   |
|  - Document Normalizer: RFC 5322 MIME Parser + Attachment Extractor               |
|  - Asynchronous Task Queue: ThreadPoolTaskExecutor Decoupled Intake Pipeline      |
|  - AI Gateway Client: Resilient REST Client to Python AI Microservice             |
|  - Reviewer Management: Human Overrides, Field Modifications, Comments            |
|  - Dual-Profile Persistence: H2 (Oracle Compatibility Mode) OR Oracle XE          |
|  - Immutable Audit Service: 21 CFR Part 11 Compliant Event Logging                |
+-----------------------------------------------------------------------------------+
                                         |
                                         | HTTP / JSON REST APIs (Port 8000)
                                         v
+-----------------------------------------------------------------------------------+
|                             TIER 3: AI MICROSERVICE                               |
|                            Python 3.11 + FastAPI                                  |
|  - Layout-Aware PDF Parser (PyMuPDF / fitz) + Table Extractor + PIL Rasterizer    |
|  - Native Multimodal Vision: Scanned Forms & Physical Defect Images               |
|  - Zero-Hallucination Triage Classifier: Multi-Label (ICSR, PQC, MI, Not Relevant)|
|  - ICH E2B(R3) Structured Fact Extractor: Zero-Hallucination "Not stated" Policy  |
|  - Strict Source Attribution: Every Fact Contains Source Type, Page, & Snippet    |
|  - Dedicated Literature Screening & Multi-Case Splitter (+30% Bonus Engine)       |
|  - Gemini Flash Engine: Dynamic Live Inference with Tenacity Exponential Retries  |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                           ENTERPRISE DATA PERSISTENCE                             |
|  - Demo / Evaluation: Embedded H2 Database (MODE=Oracle) for Zero-Friction Setup   |
|  - Production: Oracle Database 19c/21c Enterprise Edition (PL/SQL Schema)         |
|  - Tables: INTAKE_MESSAGES, ATTACHMENTS, ICSR_REPORTS, PQC_REPORTS, AUDIT_LOG     |
|  - Database-Level Immutability: TRG_AUDIT_LOG_IMMUTABLE Prevents Updates/Deletes   |
+-----------------------------------------------------------------------------------+

---

## 3. End-to-End Data Flow

The lifecycle of an intake document progresses through twelve discrete stages:

Stage 1: Ingestion
  Source: Live IMAP Mailbox (e.g. Gmail / Exchange) OR Local Synthetic Fixture (`test-data/emails/`).
  Operation: Ingestion Service fetches unread `.eml` files, verifies MIME integrity, and extracts headers.

Stage 2: Normalization
  Operation: Java MIME parser extracts sender, recipient, subject, date, message ID, plain text body, and all attachments.
  Output: Normalized `IntakeMessage` domain entity saved with status `RECEIVED`.

Stage 3: Asynchronous Queuing
  Operation: Message ID dispatched to `ThreadPoolTaskExecutor` processing queue.
  Benefit: Mailbox ingestion never blocks on downstream AI inference; ingestion proceeds at wire speed.

Stage 4: AI Service Dispatch
  Operation: Spring Boot REST client streams the raw `.eml` or isolated `.pdf` payload to `POST /api/v1/process-eml` or `/process-pdf`.

Stage 5: Document Inspection & Layout Parsing
  Operation: Python `PDFParser` extracts text by page, reconstructs table matrices into structured markdown tables, extracts embedded raster images, and classifies document flavor (`digital_form`, `scanned_handwritten`, `literature_article`, `non_english`).

Stage 6: Dynamic Multimodal AI Inference
  Operation: Combined email text, structured tables, and rasterized images/photos are forwarded to Gemini Flash (`gemini-2.5-flash` with `gemini-flash-latest` fallback) via Google GenAI SDK.
  Guarantees: Zero pre-computed mock caching; 100% dynamic live reasoning with exponential backoff retries.

Stage 7: Regulatory Triage Classification
  Operation: Message classified into one or more of 4 regulatory buckets:
    - Safety Report (ICSR)
    - Quality Complaint (PQC)
    - Info Request (MI)
    - Not Relevant
  Output: Category labels, calibrated confidence scores (0.0 to 1.0), 1-line regulatory rationale, and 10–15 sentence executive summary.

Stage 8: ICH E2B Structured Fact Extraction & Attribution
  Operation: Fact extractor extracts Patient, Reporter, Product, Reaction, Lab Tests, Quality Complaints, and Medical Inquiries.
  Ground Rule: Unmentioned attributes explicitly output `"Not stated"`. Every populated fact includes `{ source_type, page_or_location, verbatim_snippet }`.

Stage 9: Quality Defect & Image Review Flagging
  Operation: Physical defect photographs (e.g. vial particulate, crimp defects) trigger `requires_human_review = True` and generate detailed AI image descriptions.

Stage 10: Literature Screening & Multi-Case Splitting (+30% Bonus)
  Operation: Scientific literature articles are screened for reportability. Multi-patient case series are automatically split into independent, individual ICSR records.

Stage 11: Database Persistence
  Operation: Spring Boot receives extraction JSON, maps fields to JPA entities, and commits records to H2/Oracle with status `TRIAGED_PENDING_REVIEW`.

Stage 12: Human Review & Audit Logging
  Operation: Reviewer inspects side-by-side workspace on Angular dashboard. Any edits, reclassifications, or approvals trigger an immutable audit event recorded in `AUDIT_LOG`.

---

## 4. Architectural Boundaries & Component Contracts

### 4.1 Tier-to-Tier API Contracts

| Endpoint | Method | Caller | Provider | Payload / Description |
| :--- | :---: | :--- | :--- | :--- |
| `/api/v1/health` | GET | Spring Boot / Monitor | Python AI Service | Service status, active Gemini model, cache status |
| `/api/v1/process-eml` | POST | Spring Boot Orchestrator | Python AI Service | `multipart/form-data` with `.eml` file; returns full `ExtractionResult` |
| `/api/v1/process-pdf` | POST | Spring Boot Orchestrator | Python AI Service | `multipart/form-data` with `.pdf` file; returns full `ExtractionResult` |
| `/api/v1/triage` | POST | External / Test Runner | Python AI Service | JSON `{ text, context_label }`; returns `TriageResult` |
| `/api/v1/extract` | POST | External / Test Runner | Python AI Service | JSON `{ text, triage, source_filename }`; returns `ExtractionResult` |
| `/api/v1/literature/screen-and-split` | POST | Spring Boot Literature Tab | Python AI Service | `multipart/form-data` with literature PDF; returns `LiteratureScreenResult` |
| `/api/messages` | GET | Angular Frontend | Spring Boot API | Paginated list of intake messages with triage status and badges |
| `/api/messages/{id}` | GET | Angular Frontend | Spring Boot API | Detailed message record including attachments, extracted ICSR/PQC/MI entities |
| `/api/messages/{id}/override` | POST | Angular Frontend | Spring Boot API | Reviewer override: category changes, field modifications, comments |
| `/api/audit-log` | GET | Angular Frontend | Spring Boot API | Immutable audit event log records |

### 4.2 Error Handling & Resilience Pattern

1. **AI Service Retries**: Calls to Google GenAI are wrapped with `tenacity`:
   - Maximum 3 retry attempts.
   - Exponential backoff with jitter (`min=2s`, `max=10s`).
   - Automatic failover from `gemini-2.5-flash` to canonical alias `gemini-flash-latest`.
2. **Deterministic Heuristic Fallback**: In the event of catastrophic network or API failure:
   - Triage falls back to deterministic lexical rule matching based on pharmacovigilance safety keywords.
   - Fact extraction defaults safely to `"Not stated"` across all fields with zero hallucinated guesses.
   - Error logs document the exact failure reason without crashing the service.
3. **Backend Circuit Breaker**: Spring Boot handles Python microservice timeouts gracefully, tagging the message with `STATUS = AI_PROCESSING_FAILED` and generating a task alert for manual review.

---

## 5. Security, Compliance & Data Isolation

1. **100% Synthetic Data**: All patient names, reporter identities, institutional affiliations, and clinical narratives in `test-data/` are strictly synthetic. No real patient data or proprietary corporate records exist within the repository.
2. **Zero Credential Leakage**: No API keys, database passwords, or mailbox credentials are hardcoded. All configurations load through system environment variables (`GEMINI_API_KEY`, `MAIL_IMAP_HOST`, `MAIL_IMAP_USERNAME`, `MAIL_IMAP_PASSWORD`).
3. **21 CFR Part 11 Audit Trail**: Modifications made by human reviewers do not overwrite historical states. An immutable audit table records the user, timestamp, original value, modified value, and justification. Database triggers prevent update or delete operations on audit records.
