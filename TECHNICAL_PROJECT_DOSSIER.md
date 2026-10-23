# CLINEVO SMART INBOX ASSISTANT -- MASTER TECHNICAL DOSSIER & INTERVIEW BIBLE

> **Target Role:** Forward Deployment / GenAI Integration Engineer  
> **Company:** Clinevo Technologies Pvt. Ltd., Electronic City Phase 1, Bengaluru  
> **Interview Stage:** **ROUND II (Founder & Leadership Walk-In Walkthrough)**  
> **Candidate Qualification:** Successfully passed Round 1 Assignment Submission; invited for on-site live laptop demonstration & technical grilling  
> **Repository Root:** `C:\projects\SmartInbox`  
> **Date of Interview:** Thursday, 08-Oct-2026 at 09:00 AM IST  
> **Strict Evaluation Standard:** 100% grounded in ACTUAL repository implementation. Zero invented, inferred, or exaggerated claims.

---

## 1. PROJECT OVERVIEW

### What the Application Does
The **Clinevo Smart Inbox Assistant** is an enterprise-grade pharmacovigilance (PV) intake automation platform. It ingests incoming medical communications from live IMAP mailboxes or local synthetic `.eml` fixtures, extracts and parses complex multi-flavor PDF attachments (digital forms, scanned handwriting, scientific literature, and non-English regulatory reports), performs multi-label regulatory triage across 4 standard pharmacovigilance categories, extracts structured ICH E2B(R3) clinical entities with strict zero-hallucination guardrails, and renders the results on an Angular split-view reviewer workbench featuring real-time visual canvas bounding-box citations and an immutable 21 CFR Part 11 audit trail.

### The Business Problem
1. **The Shared Safety Mailbox Bottleneck:** Global pharmaceutical sponsors and Contract Research Organizations (CROs) receive hundreds of unstructured communications daily across central safety mailboxes (`drugsafety@company.com`).
2. **Document Diversity:** Emails contain everything from unformatted consumer reports to official CIOMS Form I / FDA 3500A digital grids, clinic triage sheets with blue-pen cursive handwriting, non-English reports (Spanish AEMPS, German BfArM), physical product defect complaints, and medical inquiries.
3. **Severe Regulatory Penalties:** Under US FDA (21 CFR 314.80), European EMA (GVP Module VI), and CDSCO mandates, any **serious, unexpected adverse drug reaction** must be triaged, extracted, and submitted within strict **7-calendar-day (fatal/life-threatening)** or **15-calendar-day (serious)** expedited regulatory reporting clocks. Manual review (30-45 minutes per case) creates severe compliance risks, warning letters, and audit sanctions.
4. **The Solution:** Automates the initial triage and extraction pass in ~8 seconds per case, presenting verified evidence directly to a human reviewer to review, confirm, or override.

### End-to-End User Flow
1. **Ingestion:** Backend monitors mailbox (`IMAP` or local fixture directory) -> detects new unread emails -> stores raw MIME envelope as `RECEIVED`.
2. **Async AI Processing:** Backend dispatches raw bytes to Python AI microservice -> PyMuPDF parses document geometry and 2D tables -> Gemini 3.5 Flash performs multimodal zero-hallucination extraction -> validated Pydantic envelope returned -> Backend updates status to `TRIAGED`.
3. **Reviewer Triage:** Reviewer opens Angular Dashboard (`http://localhost:4200`) -> views Review Queue sorted by urgency clocks (`EXPEDITED 15-DAY`, `ROUTINE`, `DEFECT ALERT`).
4. **Visual Verification:** Reviewer opens Case Workspace -> inspects source document on the left and extracted ICH E2B clinical entities on the right -> clicks any extracted field -> Angular renders an amber visual bounding box directly over the exact PDF coordinates and opens the Docked Evidence Inspector HUD.
5. **Human-in-the-Loop Override:** Reviewer clicks `[Confirm AI Case]` or enters `Reviewer Correction Mode` -> edits field or category -> system enforces a mandatory clinical justification -> backend commits an append-only row to the 21 CFR Part 11 audit trail.

### Implementation Status Breakdown
* **[IMPLEMENTED]**: Dual-mode email ingestion (Live IMAP via Angus Mail SSL 993 + local EML fixtures).
* **[IMPLEMENTED]**: 4-bucket multi-label triage classification (ICSR, PQC, MI, Not Relevant).
* **[IMPLEMENTED]**: Layout-aware digital PDF extraction with 2D table reconstruction (ALT, AST, Bilirubin).
* **[IMPLEMENTED]**: Scanned handwriting extraction via Gemini 3.5 Flash Multimodal Vision with calibrated uncertainty scores.
* **[IMPLEMENTED]**: Non-English intake (Spanish AEMPS RAM) with bilingual display (English translation + Spanish source).
* **[IMPLEMENTED]**: Physical defect photo flagging (cleanroom photo embedded in PDF flagged with amber review badge).
* **[IMPLEMENTED]**: Zero-hallucination enforcement (`"Not stated"` for unmentioned fields).
* **[IMPLEMENTED]**: Canvas visual bounding-box highlights for digital PDFs using physical page coordinates `[x, y, w, h]`.
* **[IMPLEMENTED]**: Docked Evidence Inspector HUD with verbatim snippets and Level 1 visual anchor badges.
* **[IMPLEMENTED]**: Literature screening workbench with multi-patient case series disaggregation (+30% bonus).
* **[IMPLEMENTED]**: 21 CFR Part 11 Audit Trail with client-side delta diffing and mandatory justification tracking.
* **[IMPLEMENTED]**: Dual database profiles (Embedded H2 in Oracle syntax mode for demo / Oracle 19c driver for production).
* **[PARTIALLY IMPLEMENTED]**: Scanned/handwritten bounding boxes: Raw camera photographs do not contain vector text layers; the system anchors to page number and verbatim text snippet, but does not draw coordinate boxes on pixel-only scans.
* **[PLANNED / NOT IMPLEMENTED]**: Distributed message broker (Kafka/RabbitMQ); currently runs on Spring's in-memory `ThreadPoolTaskExecutor`.
* **[PLANNED / NOT IMPLEMENTED]**: Cloud object storage (AWS S3/GCS) for PDF binaries; currently stored as database BLOBs/local files.

### 60-Second Elevator Pitch
"The Clinevo Smart Inbox Assistant is an intake automation platform for Pharmacovigilance. Pharmaceutical companies face strict FDA 7-day and 15-day expedited reporting deadlines for serious adverse events, but safety teams currently spend 30 to 45 minutes manually opening every email and clinical PDF. 

I built a decoupled 3-tier system matching Clinevo's enterprise architecture: an Angular 18 split-view reviewer workbench, a Spring Boot 3.3 transactional backend orchestrator, and a Python FastAPI microservice powered by PyMuPDF and Google Gemini 3.5 Flash. It ingests emails over IMAP or test fixtures, classifies them across 4 regulatory buckets with multi-label support, enforces a strict zero-hallucination policy where missing fields are recorded as 'Not stated', anchors clinical facts to exact visual bounding boxes on the PDF canvas, and logs every reviewer override in a 21 CFR Part 11 compliant audit trail."

### 2-Minute In-Depth Walkthrough
"In pharmaceutical safety operations, the primary compliance risk is regulatory latency. If a doctor reports a case of acute liver failure caused by a drug, global health authorities mandate expedited submission within 15 calendar days. Today, safety teams receive hundreds of emails containing digital CIOMS forms, handwritten ER triage sheets, defect complaints, and medical questions.

To solve this, I designed a decoupled polyglot architecture:
1. **Tier 2 (Spring Boot 3.3 Backend):** Acts as the robust transactional orchestrator. It connects to live mailboxes over IMAP SSL 993 or loads synthetic test fixtures. To prevent thread blocking during AI processing, it uses an asynchronous task executor with clean state transitions: RECEIVED, PROCESSING, TRIAGED, and REVIEWED.
2. **Tier 3 (Python FastAPI AI Microservice):** PyMuPDF parses PDF geometry, extracts 2D table grids for clinical lab values, and extracts bounding-box coordinates. We feed this to Google Gemini 3.5 Flash at temperature 0.0 with strict system prompts that forbid guessing -- if a dose or lot number is omitted, it must return 'Not stated'.
3. **Tier 1 (Angular 18 Frontend):** Reviewers manage an intake queue with clinical urgency clocks. In the split-screen workspace, clicking any extracted entity -- like an elevated ALT lab value -- instantly draws a geometric bounding box on the PDF canvas and opens our Evidence Inspector HUD.
4. **Compliance & Bonus Features:** The platform includes an immutable 21 CFR Part 11 audit trail tracking every reviewer edit with a mandatory clinical rationale. Finally, to fulfill the +30% bonus requirement, I implemented a dedicated Literature Screening workbench that filters out animal studies and automatically disaggregates multi-patient case series into independent, reportable ICSR cases."

---

## 2. COMPLETE REPOSITORY STRUCTURE

```
C:\projects\SmartInbox
├── README.md                          # Master architecture and user documentation
├── .env                               # Active local environment configuration (gitignored)
├── .env.example                       # Environment configuration template
├── run.bat / run.sh                   # 1-Click launcher (checks Java, Node, Python, starts 3 tiers)
├── start.bat / start.sh               # Lightweight process runner
├── stop.bat / stop.sh                 # Graceful termination script for all 3 tiers
├── docs/                              
│   ├── CLINEVO_TECHNICAL_WRITEUP.pdf  # Canonical evaluator write-up (Executive PDF)
│   ├── FINAL_REVIEW_PACKAGE.md        # 12-case rendered dossier package (1,449 lines)
│   └── screenshots/                   # High-resolution UI captures of all core screens
├── test-data/                         # Authoritative synthetic test corpus (Frozen)
│   ├── emails/                        # 11 authentic RFC 5322 .eml intake messages
│   ├── pdfs/                          # 20 synthetic PDFs across all 4 flavors
│   │   ├── digital_forms/             # CIOMS-I and FDA 3500A digital forms
│   │   ├── scanned_handwritten/       # Scanned clinic note and bedside photos
│   │   ├── quality_complaints/        # Defect reports and vial particulate photos
│   │   ├── literature_articles/       # Multi-patient case series & animal negative controls
│   │   └── non_english/               # Spanish (AEMPS RAM) and German reports
│   ├── ground_truth/benchmark.json    # Canonical evaluation dataset (V3.0.0, 28 cases)
│   ├── manifest.json                  # Physical inventory with SHA-256 hashes
│   └── TEST_CASES_AND_EMAILS.md       # Master 785-line clinical test catalog
├── backend-spring/                    # Tier 2: Backend Orchestrator (Java 21 / Spring Boot 3.3)
│   ├── pom.xml                        # Maven project descriptor
│   ├── mvnw / mvnw.cmd                # Maven wrapper
│   ├── data/                          # Embedded database store (smartinboxdb.mv.db)
│   └── src/main/java/com/clinevo/smartinbox/
│       ├── SmartInboxApplication.java # Spring Boot entry point
│       ├── config/                    # AsyncConfig (taskExecutor), WebConfig (CORS)
│       ├── controller/                # MessageController, AuditController, LiteratureController
│       ├── dto/                       # ExtractionResultDto, ReviewerOverrideRequest, etc.
│       ├── ingestion/                 # ImapIngestionSource, FixtureIngestionSource, RawPayloads
│       ├── model/                     # IntakeMessageEntity, IcsrReportEntity, AuditEventEntity, etc.
│       ├── repository/                # Spring Data JPA repositories (7 interfaces)
│       └── service/                   # MailboxIngestionService, AsyncDocumentProcessor, AuditService, AiGatewayClient
├── ai-service-python/                 # Tier 3: AI Microservice (Python 3.11 / FastAPI)
│   ├── requirements.txt               # Dependencies: fastapi, uvicorn, pymupdf, google-genai, pydantic
│   └── app/
│       ├── main.py                    # FastAPI application entry point
│       ├── core/                      # gemini_client, llm_provider, json_repair, normalizer
│       ├── parsers/                   # PyMuPDF layout parser, table extractor, mime parser
│       ├── schemas/                   # Pydantic v2 data contracts (triage, fact, extraction, envelope)
│       └── services/                  # triage_service, icsr_extractor, literature_service, evidence_retriever
└── frontend-angular/                  # Tier 1: Reviewer Dashboard (Angular 18 / TypeScript)
    ├── package.json                   # Dependencies: Angular 18, RxJS, pdfjs-dist
    ├── angular.json                   # Build and assets configuration
    └── src/app/
        ├── app.component.ts           # Root layout with top navigation bar
        ├── core/                      # Services (MessageService, AuditService, LiteratureService) and models
        └── features/
            ├── review-queue/          # Intake table, urgency badges, confidence meters
            ├── case-workspace/        # Split-screen PDF viewer, canvas highlighter, docked inspector, edit form
            ├── literature-screening/  # Multi-patient disaggregation workbench (+30% bonus)
            └── audit-trail/           # 21 CFR Part 11 append-only ledger with action filtering
```

### Environment Configuration & Secrets
* `.env` file location: Root directory `C:\projects\SmartInbox\.env` (auto-copied to `ai-service-python\.env` on boot).
* Variables:
  * `GEMINI_API_KEY`: Google GenAI API Key (`AIza...` placeholder for evaluation).
  * `GEMINI_MODEL_NAME`: `gemini-3.5-flash`
  * `INGESTION_MODE`: `IMAP` or `FIXTURE`
  * `MAIL_IMAP_HOST`: `imap.gmail.com`
  * `MAIL_IMAP_PORT`: `993`
  * `MAIL_IMAP_USERNAME`: Mailbox address (`clinevo.test.inbox12@gmail.com`)
  * `MAIL_IMAP_PASSWORD`: Gmail App Password (16-character application token)
  * `MAIL_IMAP_SSL`: `true`
  * `MAIL_POLL_INTERVAL_MS`: `15000` (15 seconds)
  * `PYTHON_AI_SERVICE_URL`: `http://127.0.0.1:8000`
  * `SPRING_BACKEND_URL`: `http://localhost:8081`
  * `SPRING_PROFILES_ACTIVE`: `demo`

### Startup Commands
* **1-Click All-in-One Launcher:** `run.bat`
* **Python AI Microservice:**
  ```cmd
  cd ai-service-python
  python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
  ```
* **Spring Boot Backend:**
  ```cmd
  cd backend-spring
  .\mvnw.cmd spring-boot:run
  ```
* **Angular Frontend:**
  ```cmd
  cd frontend-angular
  npm start
  ```

---

## 3. ACTUAL ARCHITECTURE & DATA COMMUNICATION

### The Real Stack
```
+---------------------------------------------------------------------------------------+
|                                 TIER 1: ANGULAR 18+                                   |
|               Runs in Browser at Port 4200 (TypeScript, SCSS, HTML5)                   |
+-------------------------------------------+-------------------------------------------+
                                            |
                                            | REST API / JSON (Port 8081)
                                            v
+---------------------------------------------------------------------------------------+
|                               TIER 2: SPRING BOOT 3.3+                                |
|             Runs on JVM 21 at Port 8081 (Orchestrator, JPA, Security, Audit)          |
|                                                                                       |
|   +------------------------------------+    +-------------------------------------+   |
|   |         IMAP Angus Mail Poller     |    |   ThreadPoolTaskExecutor (@Async)   |   |
|   +------------------------------------+    +-------------------------------------+   |
|                                                                                       |
|   Persistence: Embedded H2 Database (MODE=Oracle) on disk: smartinboxdb.mv.db         |
|   (Production Profile supports authentic Oracle Database 19c RAC)                     |
+-------------------------------------------+-------------------------------------------+
                                            |
                                            | Internal HTTP Multipart POST (Port 8000)
                                            v
+---------------------------------------------------------------------------------------+
|                                TIER 3: PYTHON FASTAPI                                 |
|               Runs on Python 3.11 at Port 8000 (PyMuPDF, Pydantic v2)                 |
|                                                                                       |
|   +------------------------------------+    +-------------------------------------+   |
|   |    PyMuPDF (fitz) Layout Parser    |    |  Google GenAI (gemini-3.5-flash)    |   |
|   +------------------------------------+    +-------------------------------------+   |
+---------------------------------------------------------------------------------------+
```

### End-to-End Processing Sequence
```
[Doctor/Sender]       [IMAP / Gmail]      [Spring Boot :8081]    [Python AI :8000]    [Gemini 3.5 Flash]    [H2 DB (Oracle)]    [Angular :4200]
       |                     |                     |                     |                    |                    |                   |
       |--- Sends Email ---->|                     |                     |                    |                    |                   |
       |    with PDF         |                     |                     |                    |                    |                   |
       |                     |-- Polls (15s) ----->|                     |                    |                    |                   |
       |                     |   MimeMessage       |                     |                    |                    |                   |
       |                     |                     |-- Save Status: RECEIVED -------------->|                    |                   |
       |                     |                     |                     |                    |                    |                   |
       |                     |                     |-- Async Task Queue  |                    |                    |                   |
       |                     |                     |   Status: PROCESSING|                    |                    |                   |
       |                     |                     |                     |                    |                    |                   |
       |                     |                     |-- Multipart POST -->|                    |                    |                   |
       |                     |                     |   /api/v1/process   |                    |                    |                   |
       |                     |                     |                     |-- PyMuPDF Parser   |                    |                   |
       |                     |                     |                     |   Tables & BBoxes  |                    |                   |
       |                     |                     |                     |                    |                    |                   |
       |                     |                     |                     |-- Prompt (Temp 0)->|                    |                   |
       |                     |                     |                     |   Multimodal Vision|                    |                   |
       |                     |                     |                     |                    |                    |                   |
       |                     |                     |                     |<-- Pydantic JSON --|                    |                   |
       |                     |                     |                     |    ICSR + Coords   |                    |                   |
       |                     |                     |<-- CaseEnvelope ----|                    |                    |                   |
       |                     |                     |                     |                    |                    |                   |
       |                     |                     |-- Persist ICSR/PQC ------------------------------------------>|                   |
       |                     |                     |-- Append Audit Log ------------------------------------------>|                   |
       |                     |                     |   Status: TRIAGED   |                    |                    |                   |
       |                     |                     |                     |                    |                    |                   |
       |                     |                     |<-- Poll /api/messages (every 5s) -------------------------------------------------|
       |                     |                     |-- Returns Cases with Urgency Clocks --------------------------------------------->|
       |                     |                     |                     |                    |                    |                   |
       |                     |                     |                     |                    |                    |   [Reviewer clicks]
       |                     |                     |                     |                    |                    |   Draws Bounding Box
       |                     |                     |                     |                    |                    |   on Canvas Overlay!
```

---

## 4. EMAIL INGESTION ENGINE

* **Implementation Status:** [IMPLEMENTED]
* **Files:** 
  * `backend-spring/src/main/java/com/clinevo/smartinbox/ingestion/ImapIngestionSource.java`
  * `backend-spring/src/main/java/com/clinevo/smartinbox/ingestion/FixtureIngestionSource.java`
  * `backend-spring/src/main/java/com/clinevo/smartinbox/service/MailboxIngestionService.java`

### Technical Answers:
1. **Real vs Mock:** Both are implemented. Controlled via `smartinbox.ingestion.mode=IMAP` or `FIXTURE`.
2. **Protocol & Library:** Real connection uses **Angus Mail** (`org.eclipse.angus:jakarta.mail`) connecting via IMAP over SSL (Port 993) to `imap.gmail.com`.
3. **Authentication:** Gmail Username + App Password (16-character application token).
4. **Trigger Mechanism:** Polling mechanism managed by Spring Boot running on a scheduled interval (default `15,000 ms` / 15 seconds) with initial delay of `3,000 ms`.
5. **Metadata Extraction:**
   * **Sender:** Extracted from `MimeMessage.getFrom()`. Parses display name and email address.
   * **Subject:** `MimeMessage.getSubject()`.
   * **Date:** `MimeMessage.getSentDate()`. If null, defaults to `LocalDateTime.now()`.
   * **Message-ID:** `MimeMessage.getMessageID()`. Used as unique regulatory reference.
6. **Body Extraction:** Recursive multipart tree traversal: extracts `text/plain` or strips HTML tags from `text/html`.
7. **Attachment Discovery:** Checks `Part.getDisposition()` matching `Part.ATTACHMENT` or `Part.INLINE` with filename. PDF attachments are buffered into byte arrays; other formats are logged as raw attachments.
8. **Deduplication:** The `intake_messages` table enforces unique constraints on `message_id`. If an email with the same Message-ID was already ingested, it is skipped.
9. **Failure Handling:** IMAP connection failures are caught, logged at `ERROR` level, and the poller sleeps until the next scheduled interval without crashing the JVM.

---

## 5. PDF PROCESSING PIPELINE

* **Implementation Status:** [IMPLEMENTED across all 5 flavors]
* **Files:** 
  * `ai-service-python/app/parsers/pdf_parser.py`
  * `ai-service-python/app/services/evidence_retriever.py`
  * `ai-service-python/app/services/icsr_extractor.py`

### Breakdown by Flavor:

#### A. Digital PDFs (e.g., CIOMS-I Form in Case 01, FDA 3500A in Case 04)
* **Detection:** Detected when text density exceeds 150 characters per page and selectable text streams exist.
* **Extraction:** PyMuPDF (`fitz.open()`) reads text blocks and vector geometries.
* **Table Extraction:** PyMuPDF's `page.find_tables()` isolates 2D tabular matrices (e.g., ALT, AST, Bilirubin lab grids) and preserves column headers and numeric cells.
* **Coordinates:** PyMuPDF computes word-level bounding boxes `[x0, y0, x1, y1]` relative to page dimensions `[792 x 612]`.

#### B & C. Scanned & Handwritten PDFs (e.g., ER Triage Note in Case 02, Clinic Note in Case 12)
* **Detection:** Detected when page text density is low (<50 characters) or embedded raster images dominate page area.
* **Extraction:** PyMuPDF renders PDF pages as high-resolution raster images (300 DPI) using `page.get_pixmap()`.
* **Vision Model:** Images are passed directly to **Google Gemini 3.5 Flash Multimodal Vision**.
* **Handwriting Uncertainty:** Calibrated uncertainty score is assigned to handwriting extractions.
* **Bounding Box Reality Check:** **[PARTIALLY IMPLEMENTED]** Because photographed handwriting lacks a digital vector text layer, the system provides page citations and verbatim snippets, but cannot project pixel-level bounding boxes on the canvas.

#### D. Published Scientific Literature (e.g., Clinical Journal Articles)
* **Detection:** Multi-column layouts detected via bounding-box gap analysis.
* **Extraction:** Reads text across columns in logical reading order, filtering out citations, reference lists, and editorial front-matter.
* **Bonus Processing:** Disaggregates multi-patient case series into discrete ICSR cards.

#### E. Non-English Reports (e.g., Spanish AEMPS RAM in Case 05, German BfArM)
* **Detection:** Python checks character sets and language distributions (Spanish `es`, German `de`).
* **Translation:** Gemini generates a certified English Regulatory Translation while preserving original foreign text strings for side-by-side bilingual comparison and PDF citation anchoring.

#### Embedded Physical Defect Photos (e.g., Cleanroom Photo in Case 04)
* **Extraction:** PyMuPDF extracts raw image streams (`image/jpeg`, `image/png`).
* **Flagging:** Evaluated by Gemini Vision; surfaces an amber **Physical Defect Flag** for human inspection.

---

## 6. LLM & GENAI PIPELINE

* **Implementation Status:** [IMPLEMENTED]
* **Files:**
  * `ai-service-python/app/core/gemini_client.py`
  * `ai-service-python/app/services/triage_service.py`
  * `ai-service-python/app/services/icsr_extractor.py`
  * `ai-service-python/app/core/json_repair.py`

### Technical Specifications:
* **Provider & Model:** Google GenAI SDK (`google-genai`), using `gemini-3.5-flash`.
* **Fallback Model:** `gemini-3.5-flash-lite` (or Groq API key configured in `.env`).
* **Why Selected:** 1-million-token context window allows processing complete multi-page PDF documents and images in a single call; native multimodal vision handles handwriting and defect photos; ultra-low latency (~8 seconds) and cost-efficiency.
* **Sampling Temperature:** **`0.0`** (strictly deterministic; zero creative hallucination).
* **RAG / Vector Database:** **NOT IMPLEMENTED / NOT USED**. The architecture intentionally uses **Direct In-Context Multimodal Processing**. In clinical intake, documents are discrete packages (1 to 20 pages). Chunking into a vector database fragments critical clinical correlations (e.g., separating patient initials on page 1 from the adverse event on page 2). Processing the whole document in-context avoids retrieval loss.
* **Structured Output Method:** Pydantic v2 schemas combined with `json_repair` validation to ensure valid JSON responses even under token edge limits.
* **Zero-Hallucination Policy:** Prompt strictly enforces: *"If information is absent, strictly record 'Not stated'. A false positive or assumed value is a severe regulatory integrity violation."*
* **Rescue Medication Segregation:** Prompt enforces: *"Strictly distinguish suspect product exposure from acute rescue or resuscitation treatment (epinephrine, vasopressors, IV fluids). NEVER assign a rescue dose to the suspect product!"*

---
## 7. CLASSIFICATION & TRIAGE LOGIC

* **Implementation Status:** [IMPLEMENTED]
* **Files:** `ai-service-python/app/services/triage_service.py`
* **Buckets:**
  1. `Safety Report (ICSR)`: Identifiable patient, reporter, suspect drug, adverse event.
  2. `Quality Complaint (PQC)`: Defective packaging, particulate, contamination, counterfeit.
  3. `Medical Information (MI)`: Dosing questions, stability, compatibility; no adverse event.
  4. `Not Relevant`: Marketing spam, commercial conferences, administrative emails.
* **Multi-Label Reality:** Fully supported. If a contaminated product causes sepsis (Case 04), the engine outputs `is_multi_label: true` and includes both `Safety Report (ICSR)` and `Quality Complaint (PQC)` in `labels[]`.
* **Confidence Calibration:** System caps ML confidence at `0.98` to prevent uncalibrated 100% certainty claims.
* **Storage:** Stored in `intake_messages` columns: `primary_category`, `confidence`, `is_multi_label`, and `summary`.

---

## 8. INFORMATION EXTRACTION (ICH E2B ENTITIES)

* **Implementation Status:** [IMPLEMENTED]
* **Files:** `ai-service-python/app/services/icsr_extractor.py` and `app/schemas/category_payloads.py`

### Extracted Field Contracts:

#### 1. Safety Report (ICSR):
* **Patient:** `patient_initials`, `patient_dob`, `patient_age`, `patient_sex`, `patient_weight`, `medical_history`.
* **Primary Reporter:** `reporter_name`, `reporter_role` (Physician, Pharmacist, Nurse, Consumer), `specialty`, `institution`, `contact_info`.
* **Suspect Product:** `product_name`, `dosage`, `frequency`, `route`, `start_date`, `stop_date`, `duration`, `lot_number`, `expiration_date`, `action_taken`.
* **Adverse Event:** `reaction_description`, `onset_date`, `outcome`, `dechallenge_outcome`, `rechallenge_outcome`, `seriousness_criteria` (Hospitalization, Life-threatening, Death, Medically Significant).
* **Laboratory Matrix:** Repeated rows of `test_name`, `test_date`, `result_value`, `test_unit`, `reference_range`, `clinical_interpretation`.
* **Clinical Narrative:** Chronological case narrative synthesized from document and email context.

#### 2. Quality Complaint (PQC):
* `defective_product`, `lot_number`, `physical_defect_classification`, `container_closure_integrity`, `defect_narrative`, `has_photo_evidence`.

#### 3. Medical Information (MI):
* `primary_inquiring_hcp`, `medical_inquiry_description`, `product_target`.

#### Missing-Value Behavior:
* If any parameter is not explicitly found in the source, it is strictly assigned `"Not stated"` with certainty status `NOT_STATED`. Guessing is prohibited.

---

## 9. SOURCE TRACEABILITY & CANVAS BOUNDING BOXES

* **Implementation Status:** [IMPLEMENTED]
* **Files:**
  * `frontend-angular/src/app/features/case-workspace/case-workspace.component.ts`
  * `ai-service-python/app/services/evidence_retriever.py`

### How Source Citations Work:
1. Every extracted entity stores a `source_citations_json` payload:
   ```json
   {
     "sourceName": "cioms_form_MK_Cardioril.pdf",
     "pageNumber": 1,
     "anchorLevel": "LEVEL_1_EXACT_VISUAL",
     "snippet": "3. DATE OF EVENT 14-NOV-2025",
     "boundingBox": {
       "pageNumber": 1,
       "x0": 406.0,
       "y0": 288.0,
       "x1": 474.3,
       "y1": 227.7
     }
   }
   ```
2. When the reviewer clicks any fact in the Angular UI:
   * The PDF canvas scrolls to the designated page.
   * Angular scales coordinates to active canvas resolution:
     ```typescript
     const scaleX = this.pdfCanvasWidth / 612.0;
     const scaleY = this.pdfCanvasHeight / 792.0;
     ```
   * Renders an amber geometric rectangle directly over the document text on the `<canvas>`.
   * Opens the **Docked Evidence Inspector HUD** displaying the verbatim quotation and Level 1 certification badge.

---

## 10. CONFIDENCE SCORING ARCHITECTURE

* **Implementation Status:** [IMPLEMENTED]
* **Signals:**
  1. **Overall Classification Confidence (0.0 to 0.98):** Calibrated score representing triage certainty across categories.
  2. **Fact Certainty States:**
     * `CONFIRMED`: Explicit, unambiguous textual evidence found.
     * `NOT_STATED`: Information is absent from the source.
     * `UNCERTAIN`: Ambiguous text, blurred scan, or handwriting.
     * `CONFLICT`: Discrepancy between email body and attachment.
  3. **Handwriting Calibration:** Capped at `0.82 - 0.85` for scanned handwriting to mandate human verification.

---

## 11. REVIEW WORKBENCH (ANGULAR 18)

* **Implementation Status:** [IMPLEMENTED]
* **Files:** `frontend-angular/src/app/features/`
* **Workflow:**
  1. **Intake Queue:** Incoming emails appear with category pills, urgency clocks, and confidence meters.
  2. **Split-Screen Workspace:** Left pane displays the original document (PDF canvas or raw email text); right pane displays extracted entities.
  3. **Evidence Navigation:** Clicking any field highlights the source on the canvas.
  4. **Human-in-the-Loop Override:** Reviewer enters `Reviewer Correction Mode`, edits data, and submits with a mandatory clinical rationale.
  5. **Delta Diffing Engine:** Evaluates which specific fields were modified and submits **only the delta**, preventing redundant audit rows.

---

## 12. BACKEND REST API SPECIFICATION

* **Implementation Status:** [IMPLEMENTED]
* **Base URL:** `http://localhost:8081`

| Endpoint | Method | Payload | Response | Purpose |
| :--- | :---: | :--- | :--- | :--- |
| `/api/messages` | `GET` | None | `List<MessageSummaryDto>` | Fetch all intake cases for review queue |
| `/api/messages/{id}` | `GET` | None | `IntakeMessageEntity` | Fetch complete case details, facts, citations |
| `/api/messages/{id}/accept` | `POST` | `ReviewerAcceptRequest` | `IntakeMessageEntity` | Commit reviewer approval (Status: `REVIEWED`) |
| `/api/messages/{id}/override` | `POST` | `ReviewerOverrideRequest` | `IntakeMessageEntity` | Commit category or field edits with audit rationale |
| `/api/messages/ingest` | `POST` | None | `Map<String, Object>` | Trigger immediate mailbox or fixture scan |
| `/api/messages/reset` | `POST` | None | `Map<String, Object>` | Reset database to clean 12 benchmark cases |
| `/api/audit` | `GET` | None | `List<AuditEventEntity>` | Fetch complete 21 CFR Part 11 audit history |
| `/api/v1/literature/screen-and-split` | `POST` | Multipart PDF | `LiteratureScreenResultDto` | Disaggregate multi-patient scientific articles |

---

## 13. DATABASE & PERSISTENCE

* **Implementation Status:** [IMPLEMENTED]
* **Actual Database:** **Embedded H2 Database in Oracle Compatibility Mode** (`smartinboxdb.mv.db`) located in `backend-spring/data/`.
* **Oracle 19c Compatibility:** Configured via Spring profile `prod` using `OracleDialect` and standard SQL-92 schema structures.
* **Core Tables:**
  1. `intake_messages`: Message-ID, sender, subject, status (`RECEIVED`, `PROCESSING`, `TRIAGED`, `REVIEWED`, `OVERRIDDEN`, `FAILED`), confidence, urgency.
  2. `attachments`: Filename, content-type, binary BLOB, file size.
  3. `icsr_reports`: Patient, reporter, product, adverse event, labs, and `source_citations_json`.
  4. `pqc_reports`: Defect classification, lot/batch, closure integrity, photo flags.
  5. `medical_info`: Clinical question, product topic.
  6. `literature_articles`: Article title, screening decision (`REPORTABLE`/`NON_REPORTABLE`), split case count.
  7. `audit_events`: Timestamp, reviewer username, action (`EDIT_FIELD`, `OVERRIDE_CATEGORY`, `CONFIRM_CASE`), target field, original value, new value, reviewer comments, `is_immutable`.

---
## 14. QUEUE & ASYNCHRONOUS PROCESSING

* **Implementation Status:** [IMPLEMENTED as an in-process queue]
* **Component:** Spring Boot `@Async("taskExecutor")` configured in `AsyncConfig.java`.
* **Executor Settings:** `ThreadPoolTaskExecutor` (core-pool-size: 1, max-pool-size: 1, queue-capacity: 100).
* **Why In-Process:** Fulfills Section 5 of the assignment (*"Use a simple queue (even an in-process one) rather than pure synchronous calls"*). Eliminates external middleware dependencies (Kafka/RabbitMQ) for standalone evaluation.
* **Lifecycle:** `RECEIVED` -> `PROCESSING` -> `TRIAGED` -> `REVIEWED` / `OVERRIDDEN`. If an exception occurs, transitions to `FAILED` and logs an audit error.

---

## 15. AUDIT LOGGING & 21 CFR PART 11 DEFENSE

* **Implementation Status:** [IMPLEMENTED]
* **Reality vs Claims:**
  * **What IS Implemented:** Append-only persistence in `audit_events` table; tracks timestamp, user identity, action, field changed, old value, new value, and mandatory reviewer clinical justification.
  * **What Is NOT Implemented:** Digital cryptographic X.509 PKI signatures and biometric authentication.
  * **Interview Defense:** Claim *"Part 11 compliant data audit trail principles (append-only, immutable history, forced justification)"*, NOT *"fully certified Part 11 electronic signature platform"*.

---

## 16. SECURITY & PRIVACY

* **Implementation Status:** [IMPLEMENTED]
* **Synthetic Test Data:** 100% of names, clinics, lot numbers, and vitals are fictional. Zero Protected Health Information (PHI) or Personally Identifiable Information (PII) is used.
* **Secrets Management:** Credentials and API keys are externalized into `.env` (gitignored).
* **Cloud API Data Trade-off:** Notes that sending data to public cloud APIs (Google Gemini) presents data residency considerations. In production, enterprise pharma requires self-hosted models or private cloud VPC endpoints (Google Cloud Vertex AI with zero data retention agreements).

---

## 17. TEST DATA & BENCHMARK CATALOG

* **Canonical Benchmark Results:** Evaluated against 28 test cases in `benchmark_eval_report.json`.
* **Summary of Primary Cases:**
  * **Case 01:** Digital CIOMS-I (Liver injury / DILI from Cardioril; ALT 540; Hy's Law; Expedited 15-day).
  * **Case 02:** Scanned Handwriting (InjectaPen acute anaphylaxis; vitals BP 85/50; dose strictly `"Not stated"`).
  * **Case 03:** Pure Email (Corzapan consumer tachycardia; unstated fields marked `"Not stated"`).
  * **Case 04:** Multi-Label ICSR + PQC (Contaminated Cefatox vial causing septic shock; defect photo flag).
  * **Case 05:** Non-English Spanish (Madrid hospital TEN from Lamotrigine; bilingual translation).
  * **Case 06:** Follow-up Report (Seizure resolved s/p Neuroval discontinuation; positive dechallenge).
  * **Case 07:** Pure PQC (Cardioril blister foil seal breach; crumbling tablets; zero adverse events).
  * **Case 08:** Pure PQC (Suspected counterfeit Lipocur bottles; font and cap color mismatch).
  * **Case 09:** Medical Information (Can Corzapan 10mg be crushed for feeding tubes?).
  * **Case 10:** Not Relevant (Marketing invite for Pharma Compliance & AI Summit 2026; 0 extractions).
  * **Case 11:** Medical Information (Cefatox 1g IV dilution kinetics and refrigerated stability).
  * **Case 12:** Scanned Clinic Note (Acute angioedema with dyspnea s/p Cardioril 20mg).

---

## 18. MEASURED PERFORMANCE METRICS

*Source: `ai-service-python/data/benchmark_eval_report.json` (Dated 2026-09-09)*

* **Total Test Cases Evaluated:** 28 cases
* **Passed Cases:** 28 / 28
* **Overall Accuracy:** **100.0%**
* **Average Latency:** **8,070 ms (~8.1 seconds per document)**
* **Latency Profile:**
  * Complex 2-page CIOMS with lab matrices (Case 01): `17,498 ms` (~17.5s)
  * High-resolution scanned handwriting note (Case 02): `14,049 ms` (~14.0s)
  * Pure email text extraction (Case 03): `8,384 ms` (~8.4s)
  * Pure marketing spam classification (Case 10): `4,210 ms` (~4.2s)

---

## 19. ERROR HANDLING & EDGE CASES

* **Empty Email / Missing Attachments:** Processed using available email body text; if no clinical facts exist, classified as `Not Relevant`.
* **Missing Clinical Entities:** Zero-hallucination guardrail assigns `"Not stated"` with `NOT_STATED` status.
* **Handwriting Ambiguities:** System assigns `UNCERTAIN` status with lowered confidence score (0.82).
* **LLM JSON Syntax Errors:** `json_repair.py` catches and repairs truncated or malformed JSON responses.
* **LLM Timeouts / Rate Limits:** Spring Boot catches timeouts (180s threshold) and flags case as `FAILED`.
* **Corrupted Attachments:** PyMuPDF throws layout errors caught by `pdf_parser.py`, logging errors and allowing email text extraction to continue.

---

## 20. DESIGN TRADE-OFFS & JUSTIFICATIONS

1. **Decoupled 3-Tier Architecture vs Python Monolith:**
   * *Decision:* Angular + Spring Boot + Python FastAPI.
   * *Alternative:* Pure Python Streamlit or FastAPI monolith.
   * *Reason:* Enterprise pharmacovigilance safety databases run on Java and Oracle. Spring Boot handles enterprise transactions, audit logging, and security, while Python excels at PDF layout parsing and LLM orchestration.
2. **Direct Multimodal Processing vs Chunked RAG:**
   * *Decision:* Whole-document multimodal in-context extraction.
   * *Alternative:* Vector embeddings + chunking + RAG.
   * *Reason:* Clinical cases are discrete documents (<20 pages). Chunking fragments clinical relationships across pages. Gemini's 1M context window handles whole documents cleanly without retrieval failure.
3. **In-Process Task Queue vs Distributed Kafka/RabbitMQ:**
   * *Decision:* Spring Boot `@Async` ThreadPoolTaskExecutor.
   * *Alternative:* Apache Kafka or RabbitMQ.
   * *Reason:* Eliminates heavy middleware dependencies for prototype evaluation while fulfilling the asynchronous decoupling mandate.
4. **Client-Side Canvas Highlight vs Server-Rendered PDF Overlays:**
   * *Decision:* Client-side bounding box overlay on `<canvas>`.
   * *Alternative:* Server-side PyMuPDF red-boxing generating flattened PDFs.
   * *Reason:* Zero-latency interactive highlighting without modifying or re-downloading the original regulatory source PDF.
5. **Zero-Hallucination Guardrails vs Generative Inference:**
   * *Decision:* Strict `"Not stated"` requirement.
   * *Alternative:* Letting the LLM infer standard medical dosages.
   * *Reason:* In regulated healthcare, guessing is a severe compliance violation.

---
## 21. KNOWN LIMITATIONS (BRUTALLY HONEST)

1. **No Vector Bounding Boxes on Raw Scanned Photos:** Hand-filled photos (Case 02) do not contain digital text streams. Citations point to page numbers and snippets, but cannot project coordinate boxes.
2. **In-Memory Queue Scalability:** The current `ThreadPoolTaskExecutor` does not survive application crashes; tasks in memory would be lost unless persisted in the database.
3. **Rate Limits on Public Cloud APIs:** High-volume spikes against public Gemini endpoints risk HTTP 429 quota errors without exponential backoff.
4. **Binary Storage in Database:** Storing large PDF files in database tables is suitable for hundreds of cases, but requires migration to AWS S3 or GCS for enterprise production.

---

## 22. CANDIDATE PERSONAL CONTRIBUTION ZONES

* **HIGH CONFIDENCE (Explain Deeply):**
  * Domain problem: Pharmacovigilance, ICSR vs PQC vs MI, 7/15-day expedited reporting clocks.
  * Zero-hallucination philosophy: Why guessing is illegal in healthcare and how `"Not stated"` is enforced.
  * Angular reviewer workbench: Split-screen UI, visual canvas bounding-box highlights, docked evidence inspector.
  * 21 CFR Part 11 Audit Trail: How delta diffing works and why human justifications are required.
  * Architecture justification: Why Spring Boot and Python were decoupled.
* **MEDIUM CONFIDENCE (Review Before Interview):**
  * PyMuPDF coordinate math: How `[x0, y0, x1, y1]` coordinates map to canvas pixels.
  * Literature screening multi-patient splitting: How multi-column papers are disaggregated.
* **LOW CONFIDENCE (Do Not Over-Claim):**
  * Advanced Core Java concurrency internals: Keep the explanation focused on `@Async` and clean MVC patterns.

---

## 23. TOP INTERVIEW QUESTIONS TIED TO ACTUAL CODE

1. **"Walk me through what happens when an email arrives."**
   * *Target:* `MailboxIngestionService.java` -> `AsyncDocumentProcessor.java` -> `triage_service.py`.
   * *Depth:* Explain the 7-step journey from IMAP socket to database status transition.
2. **"Why did you choose Spring Boot if you're a GenAI engineer?"**
   * *Target:* Architecture & decoupling rationale.
   * *Depth:* Match Clinevo's enterprise production stack (Java/Oracle) and explain separation of concerns.
3. **"How does the visual bounding box work in Angular?"**
   * *Target:* `case-workspace.component.ts` and `evidence_retriever.py`.
   * *Depth:* Explain PyMuPDF extracting coordinates `[x, y, w, h]` and Angular scaling them to canvas dimensions.
4. **"How do you prevent the LLM from making up dosages?"**
   * *Target:* `icsr_extractor.py` system prompt.
   * *Depth:* Explain the 4 atomic states, rescue medication segregation, and strict `"Not stated"` rule.
5. **"What is your database strategy? Did you use Oracle?"**
   * *Target:* `application.yml` and `smartinboxdb.mv.db`.
   * *Depth:* Explain dual profiles: H2 in Oracle syntax mode for local demo, and Oracle 19c driver for production.

---

## 24. DEFEND YOUR PROJECT (TOUGH CHALLENGE QUESTIONS)

* **Q: "Why not build the whole project in Python using FastAPI?"**  
  *A:* "A Python monolith is fine for a hackathon, but Clinevo's core safety platforms run on Java and Oracle. Decoupling allows the Java layer to handle transactions, security, and audit compliance, while the Python layer focuses purely on layout parsing and GenAI."
* **Q: "Why Gemini 3.5 Flash instead of GPT-4o?"**  
  *A:* "Gemini 3.5 Flash provides native multimodal vision for processing multi-page documents and handwriting in a single request, with an 8-second average latency and low cost, avoiding multi-chunk RAG complexity."
* **Q: "What if the LLM hallucinates an adverse reaction?"**  
  *A:* "Every extracted entity is anchored to verbatim text snippets and canvas bounding boxes. Medical reviewers inspect documents in split view; ungrounded facts are immediately caught."
* **Q: "How would you scale this to 100,000 cases per day?"**  
  *A:* "Replace in-memory `@Async` with Apache Kafka, move PDF binaries to S3/GCS, shard the Oracle database, and deploy dedicated self-hosted vision models in a private VPC."

---

## 25. DEMO & WALKTHROUGH SCRIPT (15 MINUTES)

1. **Minute 0–2 (Problem & Architecture):** Introduce the PV intake bottleneck, 7/15-day expedited deadlines, and the decoupled 3-tier architecture.
2. **Minute 2–4 (Review Queue):** Show `http://localhost:4200`. Point out urgency badges (`EXPEDITED 15-DAY`), multi-label tags, and confidence scores.
3. **Minute 4–7 (Case 01 — Digital Form & Visual Evidence):** Open Case 01. Click *ALT 540 U/L*. Show the amber bounding box on the PDF canvas and the Evidence Inspector HUD.
4. **Minute 7–9 (Case 02 — Handwriting & Zero-Hallucination):** Open Case 02. Show the doctor's handwriting scan. Point out that the dose is strictly `"Not stated"` rather than guessed.
5. **Minute 9–11 (Case 04 & 05 — Multi-Label & Bilingual):** Show Case 04 (ICSR + PQC with photo defect flag) and Case 05 (Spanish report with bilingual translation).
6. **Minute 11–13 (Literature Bonus):** Open Literature tab. Explain animal study filtering and multi-patient case splitting (+30% bonus).
7. **Minute 13–15 (21 CFR Part 11 Audit Trail):** Perform a field override on Case 01. Show the mandatory justification box, submit, and display the clean row in the Audit Trail.

---

## 26. FINAL ONE-PAGE CHEAT SHEET

* **Stack:** Angular 18 (Port 4200) | Spring Boot 3.3 (Port 8081) | Python FastAPI (Port 8000) | H2 (Oracle Mode)
* **Model:** Google Gemini 3.5 Flash @ Temperature 0.0
* **4 Buckets:** Safety Report (ICSR), Quality Complaint (PQC), Medical Info (MI), Not Relevant
* **Key Mandates:** ICH E2B(R3), FDA 21 CFR Part 11, Zero-Hallucination (`"Not stated"`), Expedited 7/15-day clocks
* **Run Commands:** Double-click `run.bat` or run each tier independently
* **Database Reset:** `run.bat --reset` restores clean 12 benchmark cases
## 21. KNOWN LIMITATIONS (BRUTALLY HONEST)

1. **No Vector Bounding Boxes on Raw Scanned Photos:** Hand-filled photos (Case 02) do not contain digital text streams. Citations point to page numbers and snippets, but cannot project coordinate boxes on pixel-only scans.
2. **In-Memory Queue Scalability:** The current `ThreadPoolTaskExecutor` does not survive application crashes; tasks in memory would be lost unless persisted in the database.
3. **Rate Limits on Public Cloud APIs:** High-volume spikes against public Gemini endpoints risk HTTP 429 quota errors without exponential backoff.
4. **Binary Storage in Database:** Storing large PDF files in database tables is suitable for hundreds of cases, but requires migration to AWS S3 or GCS for enterprise production.

---

## 22. CANDIDATE PERSONAL CONTRIBUTION ZONES

* **HIGH CONFIDENCE (Explain Deeply):**
  * Domain problem: Pharmacovigilance, ICSR vs PQC vs MI, 7/15-day expedited reporting clocks.
  * Zero-hallucination philosophy: Why guessing is illegal in healthcare and how `"Not stated"` is enforced.
  * Angular reviewer workbench: Split-screen UI, visual canvas bounding-box highlights, docked evidence inspector.
  * 21 CFR Part 11 Audit Trail: How delta diffing works and why human justifications are required.
  * Architecture justification: Why Spring Boot and Python were decoupled.
* **MEDIUM CONFIDENCE (Review Before Interview):**
  * PyMuPDF coordinate math: How `[x0, y0, x1, y1]` coordinates map to canvas pixels.
  * Literature screening multi-patient splitting: How multi-column papers are disaggregated.
* **LOW CONFIDENCE (Do Not Over-Claim):**
  * Advanced Core Java concurrency internals: Keep the explanation focused on `@Async` and clean MVC patterns.

---

## 23. TOP INTERVIEW QUESTIONS TIED TO ACTUAL CODE

1. **"Walk me through what happens when an email arrives."**
   * *Target:* `MailboxIngestionService.java` -> `AsyncDocumentProcessor.java` -> `triage_service.py`.
   * *Depth:* Explain the 7-step journey from IMAP socket to database status transition.
2. **"Why did you choose Spring Boot if you're a GenAI engineer?"**
   * *Target:* Architecture & decoupling rationale.
   * *Depth:* Match Clinevo's enterprise production stack (Java/Oracle) and explain separation of concerns.
3. **"How does the visual bounding box work in Angular?"**
   * *Target:* `case-workspace.component.ts` and `evidence_retriever.py`.
   * *Depth:* Explain PyMuPDF extracting coordinates `[x, y, w, h]` and Angular scaling them to canvas dimensions.
4. **"How do you prevent the LLM from making up dosages?"**
   * *Target:* `icsr_extractor.py` system prompt.
   * *Depth:* Explain the 4 atomic states, rescue medication segregation, and strict `"Not stated"` rule.
5. **"What is your database strategy? Did you use Oracle?"**
   * *Target:* `application.yml` and `smartinboxdb.mv.db`.
   * *Depth:* Explain dual profiles: H2 in Oracle syntax mode for local demo, and Oracle 19c driver for production.

---

## 24. DEFEND YOUR PROJECT (TOUGH CHALLENGE QUESTIONS)

* **Q: "Why not build the whole project in Python using FastAPI?"**  
  *A:* "A Python monolith is fine for a hackathon, but Clinevo's core safety platforms run on Java and Oracle. Decoupling allows the Java layer to handle transactions, compliance, and enterprise IAM, while the Python layer focuses purely on layout parsing and GenAI."
* **Q: "Why Gemini 3.5 Flash instead of GPT-4o?"**  
  *A:* "Gemini 3.5 Flash provides native multimodal vision for processing multi-page documents and handwriting in a single request, with an 8-second average latency and low cost, avoiding multi-chunk RAG complexity."
* **Q: "What if the LLM hallucinates an adverse reaction?"**  
  *A:* "Every extracted entity is anchored to verbatim text snippets and canvas bounding boxes. Medical reviewers inspect documents in split view; ungrounded facts are immediately caught."
* **Q: "How would you scale this to 100,000 cases per day?"**  
  *A:* "Replace in-memory `@Async` with Apache Kafka, move PDF binaries to S3/GCS, shard the Oracle database, and deploy dedicated self-hosted vision models in a private VPC."

---

## 25. DEMO & WALKTHROUGH SCRIPT (15 MINUTES)

1. **Minute 0–2 (Problem & Architecture):** Introduce the PV intake bottleneck, 7/15-day expedited deadlines, and the decoupled 3-tier architecture.
2. **Minute 2–4 (Review Queue):** Show `http://localhost:4200`. Point out urgency badges (`EXPEDITED 15-DAY`), multi-label tags, and confidence scores.
3. **Minute 4–7 (Case 01 — Digital Form & Visual Evidence):** Open Case 01. Click *ALT 540 U/L*. Show the amber bounding box on the PDF canvas and the Evidence Inspector HUD.
4. **Minute 7–9 (Case 02 — Handwriting & Zero-Hallucination):** Open Case 02. Show the doctor's handwriting note. Point out that the dose is strictly `"Not stated"` rather than guessed.
5. **Minute 9–11 (Case 04 & 05 — Multi-Label & Bilingual):** Show Case 04 (ICSR + PQC with photo defect flag) and Case 05 (Spanish report with bilingual translation).
6. **Minute 11–13 (Literature Bonus):** Open Literature tab. Explain animal study filtering and multi-patient case splitting (+30% bonus).
7. **Minute 13–15 (21 CFR Part 11 Audit Trail):** Perform a field override on Case 01. Show the mandatory justification box, submit, and display the clean row in the Audit Trail.

---

## 26. FINAL ONE-PAGE CHEAT SHEET

* **Stack:** Angular 18 (Port 4200) | Spring Boot 3.3 (Port 8081) | Python FastAPI (Port 8000) | H2 (Oracle Mode)
* **Model:** Google Gemini 3.5 Flash @ Temperature 0.0
* **4 Buckets:** Safety Report (ICSR), Quality Complaint (PQC), Medical Info (MI), Not Relevant
* **Key Mandates:** ICH E2B(R3), FDA 21 CFR Part 11, Zero-Hallucination (`"Not stated"`), Expedited 7/15-day clocks
* **Run Commands:** Double-click `run.bat` or run each tier independently
* **Database Reset:** `run.bat --reset` restores clean 12 benchmark cases
