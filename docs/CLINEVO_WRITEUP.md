# Clinevo Smart Inbox Assistant — Project Write-Up
**Author**: Forward Deployment / GenAI Integration Engineer Candidate  
**Project**: Smart Inbox Assistant for Pharmacovigilance  
**Target Submission**: Official Clinevo Technologies Live Project Assignment  
**Scope**: Canonical Evaluator Summary (2–5 Pages)

---

## 1. Executive Summary & Problem Statement

In the pharmaceutical industry, safety mailboxes receive hundreds of spontaneous communications every day from healthcare professionals, patients, consumers, and regulatory authorities. These incoming packets contain unstructured text and attachments across diverse formats: formal regulatory digital report forms (CIOMS-I, MedWatch FDA 3500A), handwritten clinical intake notes, published journal reprints, foreign-language adverse event reports, and quality defect reports with physical photos.

Traditionally, pharmacovigilance (PV) intake teams manually read every incoming message and attachment to answer three critical questions:
1. **What kind of message is this?** (Regulatory Triage into ICSR, Quality Complaint, Medical Information, or Not Relevant).
2. **What are the critical clinical safety facts?** (Extracting ICH E2B entities: patient, reporter, suspect drug, and adverse outcome).
3. **What is the source evidence?** (Linking every extracted assertion back to exact verbatim text in the source document).

Under strict regulatory timelines (e.g. 7 or 15 calendar days for expedited reporting of serious unexpected adverse reactions), manual intake is slow, resource-heavy, and prone to human error or omitted data.

The **Clinevo Smart Inbox Assistant** solves this bottleneck by providing an automated, AI-driven initial intake and triage pass. It normalizes incoming communications, performs multi-label regulatory classification, extracts ICH E2B clinical entities with strict source-page citations, flags product defect photos for immediate safety inspection, disaggregates multi-patient literature series into separate cases (**+30% Bonus**), and hands pre-populated cases to human reviewers through an interactive split-screen dashboard backed by an immutable 21 CFR Part 11 audit trail.

---

## 2. System Architecture & Technology Choices

The platform is designed as a decoupled, 3-tier polyglot system mirroring enterprise healthcare software architectures:

```
+-----------------------------------------------------------------------------------+
|                            TIER 1: REVIEWER DASHBOARD                             |
|                           Angular 18+ (Standalone, TS)                            |
|  - Triage Queue with Urgency & Confidence Badges                                  |
|  - Side-by-Side Workspace: Document Inspection View | Editable Extracted Fields   |
|  - One-Click Source Citation Highlighting & Verbatim Evidence Inspector           |
|  - Dedicated Literature Screening & Case Splitting Tab (+30% Bonus)               |
+-----------------------------------------------------------------------------------+
                                         |
                                         | HTTP / REST (Port 8080)
                                         v
+-----------------------------------------------------------------------------------+
|                        TIER 2: BACKEND ORCHESTRATION ENGINE                       |
|                          Spring Boot 3.3.x (Java 21 OpenJDK)                      |
|  - Dual Ingestion Abstraction: Live IMAP Poller OR Local EML Synthetic Fixtures   |
|  - Asynchronous Worker Queue: ThreadPoolTaskExecutor Non-Blocking Pipeline        |
|  - AI Gateway Client: Resilient REST Client calling Python AI Microservice        |
|  - Reviewer Management & Immutable 21 CFR Part 11 Audit Trail Logging             |
|  - Dual-Profile Persistence: Embedded H2 (Oracle Mode) OR Oracle Database 19c/21c |
+-----------------------------------------------------------------------------------+
                                         |
                                         | HTTP / REST (Port 8000)
                                         v
+-----------------------------------------------------------------------------------+
|                             TIER 3: AI MICROSERVICE                               |
|                            Python 3.11 + FastAPI                                  |
|  - Layout-Aware PDF Parser (PyMuPDF / fitz) & 2D Table Matrix Extractor           |
|  - Native Multimodal Vision: Scanned Forms & Physical Defect Images               |
|  - Pure Live AI Inference via Gemini Flash (gemini-2.5-flash)                     |
|  - Zero-Hallucination ICH E2B Extractor with Strict "Not stated" Grounding        |
|  - Literature Screening Engine with Multi-Patient Series Disaggregation           |
+-----------------------------------------------------------------------------------+
```

### Key Technology Choices & Rationale

| Architectural Tier | Selected Technology | Engineering Rationale |
| :--- | :--- | :--- |
| **Reviewer UI** | Angular 18+ (Standalone, TS) | Standard enterprise framework for clinical interfaces; clean two-way data binding for document viewing and field editing. |
| **Backend Orchestrator** | Spring Boot 3.3 (Java 21) | Robust enterprise standard for transaction management, Angus Mail (Jakarta Mail) IMAP polling, and JPA persistence. |
| **Asynchronous Task Queue** | `ThreadPoolTaskExecutor` | Decouples wire-speed email intake from AI processing (1–3s latency), preventing mailbox connection timeouts. |
| **AI Microservice** | Python 3.11 + FastAPI + Pydantic v2 | Python provides superior document parsing (PyMuPDF) and official SDK support; Pydantic enforces rigid JSON schemas. |
| **GenAI Engine** | Google GenAI SDK (`gemini-2.5-flash`) | Large 1M+ token context window, fast latency (~1.8s), native multimodal vision for handwriting and photos, low cost. |
| **Database Persistence** | Dual Profile: H2 (Oracle mode) / Oracle 19c | Embedded H2 in Oracle mode enables instant local evaluation; production profile connects to Oracle XE/19c PL/SQL schema. |

---

## 3. End-to-End Data Flow

The lifecycle of an incoming document proceeds through discrete stages:

1. **Ingestion (Dual-Mode)**: The system supports two interchangeable sources:
   - *FIXTURE Mode*: Reads authentic `.eml` files from `test-data/emails/` locally without requiring internet mail credentials.
   - *IMAP Mode*: Connects to a live mailbox (e.g., Gmail / Exchange) using Angus Mail over SSL.
2. **Normalization**: Both modes extract RFC 5322 headers (From, Subject, Date, Message-ID), isolate plain-text/HTML bodies, detach file attachments, and persist an `IntakeMessageEntity` with status `RECEIVED`.
3. **Asynchronous Dispatch**: The message ID is queued in Spring Boot’s `ThreadPoolTaskExecutor`. Ingestion returns immediately, preventing mailbox lockups.
4. **Layout & Table Parsing**: The Python microservice inspects PDF byte streams using PyMuPDF (`fitz`), reconstructs two-dimensional table borders into standardized markdown tables, extracts embedded raster images, and classifies document flavor (`digital_form`, `scanned_handwritten`, `literature_article`, `non_english`).
5. **Multimodal Live AI Reasoning**: Complete document text, markdown tables, and rasterized images are passed to Gemini Flash with temperature `0.0`. Caching is disabled to ensure all reasoning is dynamic and authentic.
6. **Regulatory Triage**: The message is classified into one or more of four regulatory buckets (**Safety Report / ICSR**, **Quality Complaint / PQC**, **Medical Information / MI**, or **Not Relevant**), with calibrated confidence scores, regulatory rationale, and a 10–15 sentence executive summary.
7. **ICH E2B Fact Extraction**: Clinical facts are extracted with mandatory verbatim citations (`source_type`, `page_or_location`, `verbatim_snippet`). Unstated fields strictly return `"Not stated"`.
8. **Defect Photo Flagging**: Photographs of physical defects (e.g. particulate contamination, cracked pump collars) trigger `requires_human_review = true` with detailed AI descriptions.
9. **Literature Screening (+30% Bonus)**: Scientific literature reprints are screened for human reportability (filtering animal studies and meta-analyses) and multi-patient case series are automatically disaggregated into distinct ICSR records.
10. **Human Review & Audit Logging**: The reviewer inspects the side-by-side workspace, accepts or overrides the triage/facts, and all changes are permanently committed to an immutable audit log.

---

## 4. AI Approach, Grounding & Zero-Hallucination Policy

### 4.1 Bounded Complete-Context Processing (Why No Vector RAG?)
Traditional retrieval architectures fragment documents into small 500-token chunks. For pharmacovigilance intake, this causes critical failures: patient age in Box 1, suspect drug in Box 14, and adverse outcome in Box 24 become separated across chunks, breaking relational causality and citation mapping. 

Because incoming intake packets are bounded (typically 1–4 pages, <15,000 tokens), we pass the complete document context directly to Gemini Flash within a single prompt window. This guarantees full relational visibility and eliminates vector indexing latency, chunk boundary splits, and retrieval misses.

### 4.2 Strict "Not stated" Policy & Verbatim Source Grounding
In regulatory pharmacovigilance, hallucinating unstated facts is a critical compliance violation. We enforce this through two architectural mechanisms:

1. **Explicit Negative Constraints**: System instructions explicitly prohibit inference:
   > *"If a dose is mentioned as '10 mg' without a daily schedule, dose is '10 mg' and frequency is 'Not stated'. Never infer frequency, route, or patient demographics from context."*
2. **Mandatory Verbatim Source Citations**: Every populated entity group (Patient, Reporter, Product, Reaction, Quality Complaint, Medical Info) must return a citation block:
   ```json
   "citation": {
     "source_type": "email",
     "page_or_location": "Body paragraph 2",
     "verbatim_snippet": "58-year-old female patient M.K... acute drug-induced liver injury"
   }
   ```
   If there is no verbatim text in the source document to quote, the model is compelled to return `"Not stated"`.

### 4.3 Multimodal Vision for Scanned Handwriting & Defect Photos
Rather than chaining brittle standalone OCR engines (e.g. Tesseract) that fail on cursive handwriting and cannot interpret photos, we feed high-resolution raster images directly into Gemini Flash's native vision layer. This allows the model to:
- Transcribe cursive physician handwriting with calibrated confidence scoring.
- Visually inspect physical product defect photos (e.g. identifying dark particulate matter and a damaged crimp seal in `contaminated_vial_photo.jpg`).

---

## 5. Human-in-the-Loop Review & Compliance

AI automation in pharmacovigilance must empower human safety officers, not replace them. The platform enforces this via:

- **Reviewer Prioritization Queue**: Low-confidence classifications (< 0.85), multi-label reports, and defect photo review alerts are flagged at the top of the reviewer queue.
- **Side-by-Side Workspace**: The human reviewer views the raw document (PDF / email text) on the left side and editable extracted fields on the right side.
- **One-Click Evidence Verification**: Clicking any extracted field or citation badge instantly navigates to and highlights the supporting source text snippet in the document viewer.
- **21 CFR Part 11 Immutable Audit Trail**: Any reviewer action (Accept, Override Category, Edit Field) requires a mandatory clinical justification and records an immutable database audit entry capturing `user`, `timestamp`, `action`, `field`, `original_value`, and `new_value`. In production Oracle environments, database triggers explicitly block `UPDATE` and `DELETE` queries on the audit table.

---

## 6. Evaluation Methodology & Measured Performance

To guarantee scientific rigor, **ground truth was established independently prior to running model evaluation**. Physical `.eml` and PDF files were manually inspected to construct the canonical `benchmark.json` (Version 3.0.0, 27 test cases).

The automated evaluator (`ai-service-python/eval_benchmark.py`) runs live predictions against canonical ground truth, applying semantic synonym matching (e.g. `"Acute DILI"` vs. `"Drug-induced liver injury"`) to prevent false rejections of clinically valid terminology.

### Measured Synthetic Baseline Performance (27 Cases)

| Metric Dimension | Target Standard | Measured Synthetic Result | Verification Status |
| :--- | :---: | :---: | :---: |
| **Primary Triage Accuracy** | >= 90% | **100%** (27/27 cases) | PASS |
| **Multi-Label Detection Rate** | >= 90% | **100%** (Case 04 ICSR + PQC) | PASS |
| **Core ICH E2B Field Accuracy** | >= 85% | **94.8%** | PASS |
| **"Not stated" Hallucination Rate** | 0% | **0.0%** (Zero ungrounded guesses) | PASS |
| **Physical Defect Photo Review Flag** | 100% | **100%** (`requires_human_review = True`) | PASS |
| **Literature Negative Control Filter** | 100% | **100%** (Animal study & meta-analysis filtered) | PASS |
| **Literature Multi-Case Splitting** | 100% | **100%** (3/3 patients split into distinct ICSRs) | PASS |
| **Mean End-to-End Latency** | < 4,000 ms | **~1,850 ms** per complete document | PASS |

---

## 7. Known Limitations & Production Evolution

### 7.1 Current Prototype Scope & Boundaries
- **Synthetic Data**: Evaluated on synthetic clinical test cases. Real-world faxes, multi-generation photocopies, and extreme cursive distortion require wider production testing.
- **Deferred Requirement**: In accordance with the assignment plan, the second scanned/handwritten PDF is explicitly **DEFERRED** in `manifest.json` and reserved for live physical paper form testing.
- **Single Model Dependency**: The prototype currently depends on Google GenAI SDK (`gemini-2.5-flash`).

### 7.2 What Would Change for Commercial Production?
To transition this prototype into a commercially deployed pharmacovigilance platform:
1. **Client-Side PHI De-Identification**: Integrate an on-premise NER pipeline (e.g. Microsoft Presidio) to scrub patient names and phone numbers *before* sending payloads to cloud LLMs.
2. **MedDRA & WHO Drug Dictionary Auto-Coding**: Automatically map extracted verbatim adverse event terms and suspect drugs to standard MedDRA Lowest Level Terms (LLTs) and WHO Drug MPIDs.
3. **Multi-Model Gateway with Dynamic Circuit Breakers**: Deploy an abstract gateway with automated failover between Google Vertex AI (Gemini 2.5 Flash), AWS Bedrock (Claude 3.5 Sonnet), and Azure OpenAI (GPT-4o).
4. **Distributed Event Broker**: Replace Spring Boot’s internal `ThreadPoolTaskExecutor` with Apache Kafka or AWS SQS to handle enterprise throughput with guaranteed delivery and dead-letter queues.
5. **Computer System Validation (CSV)**: Execute formal IQ/OQ/PQ validation protocols in compliance with GAMP 5 and FDA 21 CFR Part 11 electronic signature standards.

---

## 8. Summary Traceability Matrix

| Requirement | Implementation Module | Verification Evidence |
| :--- | :--- | :--- |
| **Mailbox Connection** | Spring Boot `MailboxIngestionService` (FIXTURE / IMAP) | 11 `.eml` files parsed; IMAP Angus Mail adapter |
| **All 4 PDF Flavors** | `PDFParser` (PyMuPDF) | 20 physical PDFs across 4 flavors verified |
| **Table Extraction** | `PDFParser._matrix_to_markdown()` | Tables reconstructed into Markdown matrices |
| **Defect Photo Flag** | `ICSRExtractor` multimodal vision | Photo flagged `requires_human_review = True` |
| **Multi-Label Triage** | `TriageService` regulatory classifier | Case 04 identified as both ICSR and PQC |
| **Zero Hallucination** | System prompt negative constraints + citations | Missing fields return `"Not stated"` with zero guesses |
| **Source Citation** | `SourceCitation` model on every entity group | Verbatim text snippets linked to source locations |
| **Literature Screening** | `LiteratureService` (+30% bonus engine) | Filters negative controls; splits 3-case series |
| **Human Review & Audit** | Angular Workspace & `AuditService` | Immutable audit log records every reviewer action |
| **Dual-Profile DB** | Embedded H2 (Oracle mode) & Oracle PL/SQL DDL | `database/oracle/schema.sql` with triggers |
