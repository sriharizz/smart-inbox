# Clinevo Smart Inbox Assistant for Pharmacovigilance

> **Enterprise-grade, AI-powered pharmacovigilance intake automation platform with human-in-the-loop review.**  
> Built for the Clinevo Technologies Live Project Assignment (Forward Deployment / GenAI Integration Engineer).  
> 📄 **Canonical Evaluator Write-Up (2–5 pages)**: [docs/CLINEVO_WRITEUP.md](file:///c:/projects/SmartInbox/docs/CLINEVO_WRITEUP.md)

---

## 1. Problem Statement

Pharmaceutical companies receive hundreds of unstructured communications daily across shared safety mailboxes—including spontaneous adverse event reports from physicians and patients, product quality complaints from pharmacists, and medical inquiries. Traditionally, pharmacovigilance intake specialists manually read every email and attached PDF, sort messages into regulatory categories, extract clinical safety facts conforming to ICH E2B(R3) guidelines, and transcribe data into safety databases (e.g., Oracle Argus Safety, ArisGlobal LifeSphere).

This manual process is slow, expensive, and error-prone, creating serious compliance risks against strict regulatory expedited reporting deadlines (e.g. 7 or 15 calendar days).

The **Clinevo Smart Inbox Assistant** automates the initial intake and triage pass:
1. Ingests incoming emails and PDF attachments (Digital Forms, Scanned/Handwritten, Literature, Non-English).
2. Performs multi-label regulatory classification (**Safety Report / ICSR**, **Quality Complaint / PQC**, **Medical Information / MI**, and **Not Relevant**).
3. Extracts ICH E2B(R3) clinical entities with strict source-page citations and a zero-hallucination `"Not stated"` policy.
4. Identifies physical defect photographs (vial particulate, damaged packaging) and flags them for immediate human review.
5. Screens scientific literature articles and splits multi-patient case series into independent ICSR records (**+30% Bonus**).
6. Surfaces processed cases on an interactive Angular split-view reviewer dashboard backed by an immutable 21 CFR Part 11 audit trail.

---

## 2. Key Capabilities

- **Unified Intake Engine**: Ingests communications from live IMAP mailboxes (e.g., Gmail / Exchange) or local synthetic fixture files (`.eml` corpus) with identical downstream processing.
- **4 PDF Flavor Processing**:
  - *Digital Forms*: Layout-aware extraction preserving key-value grids and structured markdown tables.
  - *Scanned / Handwritten*: Multimodal vision transcription with calibrated handwriting uncertainty scores.
  - *Published Literature*: Identifies reportable patient cases and filters out non-reportable studies (animal studies, meta-analyses).
  - *Non-English*: Spanish (AEMPS) and German (BfArM) detection with English translation and original-language source linking.
- **Zero-Hallucination Extraction**: If a field (e.g., daily dose frequency, weight) is not explicitly present in the source, it is strictly assigned `"Not stated"`. Unsupported guessing is prohibited.
- **Mandatory Source Attribution**: Every extracted entity links to its exact source (`source_type`, `page_or_location`, and `verbatim_snippet`).
- **Literature Multi-Case Splitting (+30% Bonus)**: Automatically disaggregates multi-patient case series (e.g., 1 article reporting 3 patients) into 3 independent, discrete ICSR records.
- **Human-in-the-Loop Review**: Split-screen dashboard allowing medical reviewers to inspect documents side-by-side with editable AI extractions, accept cases, or override classifications with mandatory audit logging.

---

## 3. High-Level Architecture

The platform uses a decoupled, 3-tier polyglot architecture matching Clinevo's enterprise technology stack:

```
+-----------------------------------------------------------------------------------+
|                            TIER 1: REVIEWER DASHBOARD                             |
|                           Angular 18+ (Standalone, TS)                            |
|  - Real-time Triage Queue with Urgency & Confidence Badges                        |
|  - Split-Screen Workspace: Document Viewer  |  Editable Extracted Fields          |
|  - Verbatim Source Citation Highlighting & Visual Evidence Inspector              |
|  - Dedicated Literature Screening & Multi-Patient Case Splitting Tab (+30% Bonus) |
|  - Human Review Actions: Accept, Override, Reclassify, Modify Values              |
+-----------------------------------------------------------------------------------+
                                         |
                                         | HTTP / JSON REST APIs (Port 8081)
                                         v
+-----------------------------------------------------------------------------------+
|                        TIER 2: BACKEND ORCHESTRATION ENGINE                       |
|                          Spring Boot 3.3.x (Java 21 OpenJDK)                      |
|  - Dual Ingestion: Live IMAP Poller OR Local EML Synthetic Fixtures               |
|  - Document Normalizer: RFC 5322 MIME Parser + Attachment Extractor               |
|  - Asynchronous Task Queue: ThreadPoolTaskExecutor Decoupled Worker Pipeline      |
|  - AI Gateway Client: Resilient REST Client to Python AI Microservice             |
|  - Reviewer Management: Human Overrides, Field Modifications, Audit Events        |
|  - Dual-Profile Persistence: H2 (Oracle Mode) OR Oracle Database 19c/21c          |
+-----------------------------------------------------------------------------------+
                                         |
                                         | HTTP / JSON REST APIs (Port 8000)
                                         v
+-----------------------------------------------------------------------------------+
|                             TIER 3: AI MICROSERVICE                               |
|                            Python 3.11 + FastAPI                                  |
|  - Layout-Aware PDF Parser (PyMuPDF / fitz) + Table Matrix Extractor              |
|  - Native Multimodal Vision: Scanned Forms & Physical Defect Images               |
|  - Regulatory Multi-Label Triage Classifier (ICSR, PQC, MI, Not Relevant)         |
|  - ICH E2B(R3) Structured Fact Extractor with Zero-Hallucination Grounding        |
|  - Verbatim Evidence Citation Generator (Source, Page/Location, Quote)            |
|  - Dedicated Literature Screening & Multi-Case Splitter (+30% Bonus Engine)       |
|  - Gemini Flash Engine: Dynamic Live Inference with Tenacity Exponential Retries  |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                           ENTERPRISE DATA PERSISTENCE                             |
|  - Demo Profile (Default): Embedded H2 in Oracle Compatibility Mode (Zero Setup)  |
|  - Production Profile: Oracle Database 19c/21c with PL/SQL Sequences & Triggers   |
|  - Immutable Audit Trail: Database Constraints Prevent Updates/Deletions          |
+-----------------------------------------------------------------------------------+
```

---

## 4. Technology Stack

| Layer | Technologies & Frameworks |
| :--- | :--- |
| **Reviewer Frontend** | Angular 18+, TypeScript, HTML5, Vanilla CSS / Modern Healthcare Theme |
| **Backend Orchestration**| Spring Boot 3.3+, Java 21 OpenJDK, Spring Data JPA, Angus Mail (IMAP) |
| **AI Microservice** | Python 3.11+, FastAPI, Uvicorn, Pydantic v2, PyMuPDF (`fitz`), Pillow (PIL) |
| **GenAI Engine** | Google GenAI SDK (`gemini-3.5-flash` with `gemini-3.5-flash-lite` fallback) |
| **Database** | Dual Profile: Embedded H2 (`MODE=Oracle`) for demo / Oracle 19c/21c for production |
| **Dataset & Validation** | Python 3.11, SHA-256 Manifest Verification, 27 Canonical Benchmark Cases |

---

## 5. Repository Structure

```text
SmartInbox/
├── README.md                          # Master project documentation (this file)
├── ASSIGNMENT_SPEC.md                 # Official specification & traceability matrix
├── Clinevo_Assignment.pdf             # Original Clinevo assignment prompt
├── .env.example                       # Example environment configuration template
├── docs/                              # Detailed engineering documentation
│   ├── CLINEVO_WRITEUP.md             # Canonical evaluator write-up (2–5 pages)
│   ├── ARCHITECTURE.md                # System architecture & component contracts
│   ├── AI_PIPELINE.md                 # 16-stage AI processing pipeline specification
│   ├── DATA_AND_GROUND_TRUTH.md       # Synthetic dataset, inventory & ground truth
│   ├── PROMPT_DESIGN.md               # Prompt engineering, schemas & grounding rules
│   ├── DECISIONS.md                   # Architecture Decision Records (ADR-001 - 008)
│   ├── EVALUATION.md                  # Benchmark metrics & measured accuracy
│   ├── LIMITATIONS_AND_PRODUCTION.md  # Prototype limitations vs. production roadmap
│   ├── CHANGELOG.md                   # Project engineering milestone history
│   └── CLINEVO_ASSIGNMENT_ORIGINAL_TEXT.md # Raw text of Clinevo assignment
├── test-data/                         # Authoritative synthetic test corpus (Frozen)
│   ├── emails/                        # 11 authentic RFC 5322 .eml intake emails
│   ├── pdfs/                          # 20 PDFs across digital, scanned, literature, non-English
│   │   ├── digital_forms/             # CIOMS-I and FDA 3500A digital forms
│   │   ├── quality_complaints/        # Defect reports and vial particulate photo
│   │   ├── scanned_handwritten/       # Scanned clinic note and photo
│   │   ├── literature_articles/       # Case-bearing articles & negative controls
│   │   └── non_english/               # Spanish (AEMPS) and German (BfArM) reports
│   ├── ground_truth/                  # Canonical benchmark.json (V3.0.0, 27 cases)
│   ├── manifest.json                  # Physical inventory with verified SHA-256 hashes
│   └── TEST_CASES_AND_EMAILS.md       # Master 785-line catalog synchronized with files
├── ai-service-python/                 # Python AI Microservice (Phase 2)
│   ├── app/                           # Core FastAPI application
│   │   ├── api/v1/router.py           # REST endpoints (/triage, /extract, /process-eml)
│   │   ├── core/                      # Config and Gemini client with retries
│   │   ├── parsers/                   # PyMuPDF PDF parser and MIME email parser
│   │   ├── schemas/                   # Pydantic v2 schemas (triage, extraction, literature)
│   │   └── services/                  # Triage, ICSR extractor, literature splitter
│   ├── tests/                         # Pytest unit and endpoint test suites
│   ├── eval_benchmark.py              # Automated benchmark evaluation runner
│   └── requirements.txt               # Python dependencies
├── backend-spring/                    # Spring Boot 3 Orchestrator (Phase 3)
│   ├── src/main/java/                 # Java 21 controllers, services, repositories
│   └── pom.xml                        # Maven dependencies (Java 21, Angus Mail, H2)
├── frontend-angular/                  # Angular 18+ Reviewer UI (Phase 4)
│   └── src/app/                       # Standalone components, triage queue, reviewer view
├── database/                          # Database schemas
│   └── oracle/schema.sql              # Production Oracle PL/SQL DDL, triggers & sequences
└── scripts/                           # Tooling and validation scripts
    └── validate_dataset_final.py      # Comprehensive dataset validator
```

---

## 6. Quick Start: 1-Click Launch (Recommended for Reviewers)

For seamless evaluation, the repository includes an automated 1-click launcher for Windows, macOS, and Linux that validates prerequisites, installs dependencies, launches all 3 tiers, and opens the reviewer workbench in your default browser.

### 6.1 Three-Step Launch

1. **Clone the repository**:
   ```bash
   git clone https://github.com/sriharizz/smart-inbox.git
   cd smart-inbox
   ```

2. **Configure Environment Credentials**:
   Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
   Open `.env` and configure your credentials:
   - **Gemini AI Extraction**: Set `GEMINI_API_KEY=your_google_gemini_api_key` ([Google AI Studio](https://aistudio.google.com/))
   - **Live Gmail Ingestion (Optional)**: Set `MAIL_IMAP_PASSWORD=your_16_char_google_app_password` to enable automated 15-second background polling of `clinevo.test.inbox12@gmail.com`.

3. **Launch the platform**:
   - **Windows**: Double-click `run.bat` (or `start.bat`)
   - **macOS / Linux**: Run `./run.sh` (or `./start.sh`)

The launcher automatically:
- Checks Python 3.11+, Java JDK 17/21+, and Node.js
- Installs Python dependencies (`ai-service-python/requirements.txt`)
- Installs Angular frontend dependencies (`npm install`)
- Starts the **Python AI Microservice** on `http://localhost:8000`
- Starts the **Spring Boot Orchestrator** on `http://localhost:8081`
- Starts the **Angular Reviewer Dashboard** on `http://localhost:4200`
- Automatically opens your browser to `http://localhost:4200`

### 6.2 Populating Test Cases
Once the dashboard opens, click **`⚡ Ingest Fixtures`** in the top-right navigation bar. The orchestrator will parse the canonical synthetic `.eml` test cases, execute layout-aware AI triage & extraction, and populate the Review Queue.

### 6.3 Stopping the Services
- **Windows**: Double-click `stop.bat`
- **macOS / Linux**: Run `./stop.sh` or press `Ctrl+C` in the terminal

---

## 7. Manual Step-by-Step Setup

If you prefer to run services in separate terminal windows:

### 7.1 Prerequisites
- **Python**: Version 3.11 or higher
- **Java Development Kit (JDK)**: Java 17 or 21 (OpenJDK / Eclipse Temurin)
- **Node.js & npm**: Node.js v18+ and npm v10+
- **Google GenAI API Key**: Required for live Gemini Flash multimodal reasoning

### 7.2 Running the Python AI Microservice (Tier 3)

```powershell
cd ai-service-python
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
- Health endpoint: `http://localhost:8000/api/v1/health`
- Interactive Swagger docs: `http://localhost:8000/docs`

### 7.3 Running the Spring Boot Backend (Tier 2)

```powershell
cd backend-spring
./mvnw spring-boot:run
```
*(On Windows cmd, run `mvnw.cmd spring-boot:run` or `mvn spring-boot:run`)*
- Backend REST API: `http://localhost:8081/api/messages`
- H2 Console: `http://localhost:8081/h2-console`

### 7.4 Running the Angular Reviewer Dashboard (Tier 1)

```powershell
cd frontend-angular
npm install
npm start
```
- Access the Reviewer Dashboard: `http://localhost:4200` (automatically proxies `/api` requests to port 8081)

---

## 8. Automated Testing & Benchmark Evaluation

### 8.1 Validating the Synthetic Test Corpus

Run the comprehensive dataset validator to verify that all physical files, SHA-256 hashes in `manifest.json`, and ground truth facts in `benchmark.json` are consistent:

```powershell
python scripts/validate_dataset_final.py
```
*Expected output: 27/27 suites PASS, 0 failures, 1 explicitly DEFERRED (2nd handwritten PDF).*

### 8.2 Running Python AI Microservice Unit Tests

```powershell
cd ai-service-python
pytest tests/ -v
```
*Validates MIME email parsing, layout-aware PDF table extraction, defect photo detection, and API endpoints.*

### 8.3 Running the Automated Live Benchmark Evaluation

Execute the end-to-end evaluation runner comparing live Gemini Flash inference against canonical ground truth across all 27 cases:

```powershell
python ai-service-python/eval_benchmark.py
```

---

## 9. Regulatory & Ethical Data Statement

> **ALL DATA IN THIS REPOSITORY IS STRICTLY SYNTHETIC.**  
> No real patient records, proprietary corporate communications, or protected health information (PHI) are included. All clinical cases, patient initials, healthcare practitioners, institutions, and product lot numbers were synthetically generated for software testing purposes in compliance with HIPAA and EU GDPR standards.

---

## 10. Known Limitations & Deferred Requirements

1. **Second Scanned/Handwritten PDF**: Explicitly marked **DEFERRED** in `manifest.json` and documentation. Reserved for final synthetic hand-filled paper form testing.
2. **Prototype Scope**: This prototype demonstrates automated intake and human-in-the-loop review; it is not yet certified for GxP production without formal Computer System Validation (CSV), client-side PHI de-identification, and MedDRA dictionary auto-coding. Detailed production readiness requirements and roadmap are documented in [docs/CLINEVO_WRITEUP.md](file:///c:/projects/SmartInbox/docs/CLINEVO_WRITEUP.md#10-production-evolution-roadmap) and [docs/ENGINEERING_LOG.md](file:///c:/projects/SmartInbox/docs/ENGINEERING_LOG.md#5-prototype-boundaries--production-evolution).
