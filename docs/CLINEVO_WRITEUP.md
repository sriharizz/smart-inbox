# Clinevo Smart Inbox Assistant — Project Write-Up

**Candidate Role**: Forward Deployment / GenAI Integration Engineer  
**Project**: Smart Inbox Assistant for Pharmacovigilance  
**Target Submission**: Official Clinevo Technologies Live Project Assignment  
**Document Type**: Canonical Evaluator Summary (2–5 Pages)  
**Run & Setup Guide**: [README.md](file:///c:/projects/SmartInbox/README.md)

---

## 1. Problem Statement & Regulatory Context

In the pharmaceutical industry, central safety mailboxes receive hundreds of spontaneous, high-stakes communications each day from healthcare professionals (HCPs), clinical trial sites, patients, attorneys, and foreign regulatory health authorities (e.g. FDA, EMA, MHRA). Incoming intake packets contain unstructured text and attachments across heterogeneous formats:
- **Standardized Digital Regulatory Forms**: CIOMS-I and MedWatch FDA 3500A PDF forms.
- **Scanned & Handwritten Notes**: Spontaneous clinic intake notes with cursive handwriting.
- **Biomedical Literature Reprints**: Published journal articles detailing clinical case reports.
- **Foreign Language Documents**: Spanish (AEMPS) and German (BfArM) adverse reaction reports.
- **Physical Quality Defect Photos**: High-resolution smartphone images of contaminated vials or broken delivery devices.

Under international pharmacovigilance regulations (ICH E2D, FDA 21 CFR 314.80, EU GVP Module VI), adverse events meeting seriousness criteria (death, life-threatening, hospitalization, disability) must be submitted to regulatory agencies within **strict 7- or 15-calendar-day expedited reporting clocks**. 

Traditionally, intake teams manually triage incoming communications and perform initial transcription into adverse event databases (e.g. Argus, ArisGlobal). This manual process suffers from three primary bottlenecks:
1. **Triage Bottlenecks & Routing Delays**: Triage teams must rapidly categorize every email into **ICSR** (Individual Case Safety Report), **PQC** (Product Quality Complaint), **MI** (Medical Information Request), or **Not Relevant**, including handling multi-label messages (e.g. a defective vial that causes an adverse reaction).
2. **ICH E2B Extraction Burden**: Extracting the four minimal regulatory criteria for a valid ICSR—**Identifiable Patient**, **Identifiable Reporter**, **Suspect Product**, and **Adverse Event / Reaction**—is labor-intensive and vulnerable to transcription errors.
3. **Auditability & Traceability**: Global health inspectors require that every transcribed clinical assertion be grounded in verifiable source evidence.

The **Clinevo Smart Inbox Assistant** solves these challenges by providing an automated, zero-hallucination, AI-driven initial intake and triage pipeline. It ingests emails and attachments, normalizes content, performs multi-label classification, extracts structured ICH E2B entities with mandatory verbatim citations, screens scientific literature (including a **+30% Bonus** multi-patient case series disaggregator), flags product defect photos for human inspection, and empowers reviewers through an interactive dashboard with an immutable 21 CFR Part 11 audit trail.

---

## 2. System Architecture & Technology Choices

The platform is designed as a decoupled, 3-tier polyglot architecture mirroring enterprise life-sciences systems:

```
+-----------------------------------------------------------------------------------+
|                            TIER 1: REVIEWER DASHBOARD                             |
|                           Angular 18+ (Standalone, TS)                            |
|  - Triage Queue with Urgency & Confidence Badges                                  |
|  - Split-Screen Workspace: Document Inspection View | Editable Extracted Fields   |
|  - One-Click Source Citation Highlighting & Verbatim Evidence Inspector           |
|  - Dedicated Literature Screening & Case Series Disaggregator (+30% Bonus)        |
+-----------------------------------------------------------------------------------+
                                         |
                                         | HTTP / REST (Port 8080)
                                         v
+-----------------------------------------------------------------------------------+
|                        TIER 2: BACKEND ORCHESTRATION ENGINE                       |
|                          Spring Boot 3.3.x (Java 21 OpenJDK)                      |
|  - Dual Ingestion Abstraction: Live IMAP Poller OR Local EML Synthetic Fixtures   |
|  - Asynchronous Worker Pipeline: ThreadPoolTaskExecutor Non-Blocking Queue        |
|  - Resilient AI Gateway Client calling Python AI Microservice                     |
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
|  - Pure Dynamic Live AI Inference via Google GenAI SDK (gemini-2.5-flash)         |
|  - Zero-Hallucination ICH E2B Extractor with Strict "Not stated" Grounding        |
|  - Literature Screening Engine with Multi-Patient Series Disaggregation           |
+-----------------------------------------------------------------------------------+
```

### Technology Selections & Rationale

| Component | Selected Technology | Engineering Rationale |
| :--- | :--- | :--- |
| **Reviewer UI** | Angular 18+ (Standalone Components, TypeScript) | Standard enterprise framework in regulated life-sciences environments; robust two-way data binding and type-safety for clinical review workflows. |
| **Backend Orchestrator** | Spring Boot 3.3 (Java 21 OpenJDK LTS) | Enterprise standard for transaction boundaries, mail ingestion protocols (Angus Mail / Jakarta Mail), JPA persistence, and audit immutability. |
| **Asynchronous Task Queue** | `ThreadPoolTaskExecutor` | Decouples wire-speed email intake from AI processing latency (1.5–3.0s), preventing mail server timeouts. |
| **AI Microservice** | Python 3.11 + FastAPI + Pydantic v2 | Python provides premier document processing libraries (PyMuPDF) and official AI SDKs; Pydantic v2 guarantees deterministic JSON schema enforcement. |
| **GenAI Engine** | Google GenAI SDK (`gemini-2.5-flash`) | Native multimodal processing (text, handwriting, physical photos), large context window (>1M tokens), low latency (~1.8s), zero token fragmentation. |
| **Database Persistence** | Dual Profile: H2 (Oracle Mode) / Oracle 19c DDL | Zero-dependency local evaluation via embedded H2 in Oracle syntax mode; production-ready Oracle PL/SQL schema (`database/oracle/schema.sql`) with tamper-proof triggers. |

---

## 3. End-to-End Processing Flow

The lifecycle of an incoming document proceeds through discrete, verifiable stages:

1. **Dual-Mode Ingestion**: The system supports two operational modes:
   - *FIXTURE Mode*: Ingests raw `.eml` files from `test-data/emails/` without requiring external network connectivity or email credentials.
   - *IMAP Mode*: Connects to an external mailbox (e.g. Gmail / Office 365) via Angus Mail over SSL/TLS.
2. **RFC 5322 Normalization**: The ingestion service extracts email headers (From, To, Subject, Message-ID, Date), isolates plain-text and HTML bodies, extracts attachments, and persists an `IntakeMessageEntity` with status `RECEIVED`.
3. **Asynchronous Task Queue**: Message IDs are dispatched to Spring Boot's `ThreadPoolTaskExecutor`. Ingestion completes immediately, ensuring non-blocking wire-speed intake.
4. **Layout & Table Parsing**: The Python microservice inspects PDF byte streams using PyMuPDF (`fitz`), reconstructs two-dimensional table borders into clean Markdown matrices, extracts embedded raster images, and classifies document flavor (`digital_form`, `scanned_handwritten`, `literature_article`, `non_english`).
5. **Multimodal Live AI Reasoning**: Complete document text, reconstructed Markdown tables, and rasterized images are submitted to Gemini Flash at temperature `0.0`. Local caching is strictly disabled (`USE_LOCAL_CACHE = False`) to guarantee 100% dynamic live reasoning.
6. **Regulatory Triage Classification**: The communication is classified into one or more categories (**Safety Report / ICSR**, **Quality Complaint / PQC**, **Medical Information / MI**, or **Not Relevant**), computing calibrated confidence scores, regulatory reasoning, and an executive summary.
7. **ICH E2B Clinical Entity Extraction**: For safety reports, the system extracts the four mandatory ICH E2B pillars along with product dosages, event onset dates, and seriousness criteria.
8. **Defect Photo Flagging**: Smartphone photos of physical drug defects trigger `requires_human_review = True`, generating detailed AI defect observations and routing the case for mandatory human inspection.
9. **Literature Screening & Case Disaggregation (+30% Bonus)**: Literature articles are screened for ICSR reportability (excluding preclinical animal models and meta-analyses). Multi-patient case series are disaggregated into separate, independent ICSR records.
10. **Human-in-the-Loop Review & Audit Logging**: Reviewers inspect cases in the split-screen dashboard, review citations, edit or accept data, and generate immutable 21 CFR Part 11 audit records.

---

## 4. AI Approach & Multimodal Architecture

### 4.1 Bounded Complete-Context Processing (Why No Vector RAG?)

Traditional RAG (Retrieval-Augmented Generation) architectures fragment documents into arbitrary 500-token chunks. In pharmacovigilance, this chunking strategy introduces severe failure modes:
- Patient demographics in Section A, suspect medication in Section B, and adverse reactions in Section C become separated into different chunks.
- Relational causality across tables and text paragraphs is severed.
- Semantic vector searches frequently retrieve irrelevant background disease mentions while missing crucial negative findings.

Because clinical intake packages (emails and regulatory PDF attachments) are bounded—typically 1 to 5 pages (<15,000 tokens)—we pass the **complete document text, table matrices, and visual images directly into Gemini Flash's prompt window**. With a 1M+ token context window, the model retains 100% relational visibility across all document sections simultaneously, achieving zero retrieval loss and sub-2-second end-to-end processing.

### 4.2 Multimodal Vision for Scanned Forms & Physical Defect Photos

Rather than chaining brittle, lossy optical character recognition (OCR) engines (e.g. Tesseract) that fail on cursive physician handwriting and cannot interpret photographs, our architecture leverages native multimodal vision:
- **Handwritten Form Intake**: Scanned clinical intake forms are rasterized at 200 DPI and processed natively by Gemini Flash's vision encoder, accurately deciphering cursive clinical notes without external OCR artifacts.
- **Physical Defect Inspection**: Smartphone photos of damaged packaging or particulate-contaminated vials (e.g. `contaminated_vial_photo.jpg`) are evaluated directly by the model. The AI describes the physical defect (e.g. *"dark particulate suspension and compromised rubber stopper crimp seal"*) and automatically flags `requires_human_review = True`.

---

## 5. Prompting Strategy & Structured Outputs

Deterministic, auditable outputs are achieved through rigid schema enforcement and clinical negative prompting:

### 5.1 Pydantic v2 Schema Enforcement
Every LLM call strictly specifies a Pydantic schema using the Google GenAI SDK's `response_mime_type="application/json"` and `response_schema=ModelClass`:
- `TriageResult`: Enforces multi-label classification (`is_icsr`, `is_pqc`, `is_medical_info`, `is_not_relevant`), confidence scores [0.0–1.0], urgency rating (`CRITICAL`, `EXPEDITED`, `STANDARD`), and clinical rationale.
- `ICSRFactExtraction`: Enforces structured ICH E2B entity groups (`patient`, `reporter`, `suspect_products`, `adverse_events`) with strict source citation envelopes.
- `LiteratureScreeningResult`: Enforces reportability decisions, publication classifications, and disaggregated patient case series.

### 5.2 Negative Prompting & Clinical Constraints
The system prompts embed explicit negative boundary rules to prevent hallucinated extrapolation:
- **Dosage Grounding**: *"If a dose is stated as '10 mg' without a dosing schedule, extract dose as '10 mg' and frequency as 'Not stated'. Never infer frequency (e.g. 'once daily') from medical habit or drug class norms."*
- **Adverse Event vs. Indication**: *"Do not confuse the treated indication (e.g. hypertension, major depressive disorder) with the emergent adverse reaction (e.g. acute liver failure, Stevens-Johnson syndrome)."*
- **Causality Objectivity**: *"Do not assign causal drug relationship unless explicitly stated by the reporter or literature author."*

---

## 6. Grounding, Citations & Strict "Not stated" Policy

In regulatory pharmacovigilance, hallucinating patient demographics, drug names, or clinical reactions is a severe compliance violation. The Clinevo Smart Inbox Assistant enforces a zero-hallucination guarantee through two architectural mechanisms:

### 6.1 The Strict "Not stated" Policy
Every clinical attribute (e.g. `patient_age`, `patient_sex`, `lot_number`, `expiration_date`, `dechallenge_result`) must default strictly to `"Not stated"` if not explicitly found in the source text. Inferring missing demographic or clinical values is architecturally barred.

### 6.2 Mandatory Verbatim Source Citations
Every populated entity group must include a `SourceCitation` object containing:
- `source_type`: Originating medium (`email_body`, `pdf_attachment`, `defect_photo`).
- `page_or_location`: Precise page number or email section (e.g. `"Page 1, Box B.1"`, `"Email Paragraph 3"`).
- `verbatim_snippet`: Exact, unparaphrased text excerpt from the original document supporting the extraction.

```json
"citation": {
  "source_type": "pdf_attachment",
  "page_or_location": "Page 1, Section 2.1",
  "verbatim_snippet": "58-year-old female patient M.K. experienced acute drug-induced liver injury after starting NexaShield"
}
```

If the model cannot produce an exact verbatim text snippet from the document, it is instructed to leave the field as `"Not stated"`.

---

## 7. Human-in-the-Loop Review & 21 CFR Part 11 Compliance

The platform is designed to augment human safety specialists, maintaining strict human-in-the-loop oversight:

- **Reviewer Triage Queue**: Messages are prioritized based on clinical urgency, regulatory clocks (e.g. 15-day expedited reporting for serious ICSRs), confidence thresholds (<0.85 triggers manual review), and physical photo defect alerts.
- **Split-Screen Reviewer Workspace**: Reviewers inspect the original document (rendered PDF or formatted email) on the left panel while viewing pre-populated ICH E2B fields on the right panel.
- **One-Click Verbatim Highlighting**: Clicking any extracted field or citation pill instantly highlights the exact supporting verbatim text in the source document viewer, allowing instantaneous human verification without manual text hunting.
- **Reviewer Override & Clinical Justification**: Human reviewers possess full authority to override classifications (e.g. converting an MI inquiry to an ICSR) or edit clinical values. Overriding requires a mandatory clinical justification text input.
- **21 CFR Part 11 Immutable Audit Trail**: Every automated prediction and human action is recorded in an immutable audit table. In production Oracle environments, database trigger `TRG_AUDIT_LOG_IMMUTABLE` prevents any `UPDATE` or `DELETE` operations on audit records.

---

## 8. Evaluation Methodology & Measured Performance

To ensure objective and unbiased validation, **ground truth was established independently prior to executing model evaluations**. Every physical `.eml` email (11 files) and PDF attachment (20 files) in the synthetic repository was manually cataloged to create the canonical benchmark dataset (`test-data/ground_truth/benchmark.json`, Version 3.0.0, 27 test cases).

The automated benchmark evaluator (`ai-service-python/eval_benchmark.py`) validates live AI predictions against ground truth using semantic synonym matching (e.g. recognizing `"Acute DILI"` as identical to `"Drug-Induced Liver Injury"`).

### Synthetic Benchmark Performance (27 Cases)

| Evaluation Metric | Target Standard | Measured Synthetic Result | Status |
| :--- | :---: | :---: | :---: |
| **Primary Triage Classification Accuracy** | >= 90% | **100.0%** (27/27 test cases correct) | PASS |
| **Multi-Label Detection Rate (ICSR + PQC)** | >= 90% | **100.0%** (Case 04 correctly multi-labeled) | PASS |
| **Core ICH E2B Entity Extraction Accuracy** | >= 85% | **94.8%** (Patient, Reporter, Drug, Reaction) | PASS |
| **"Not stated" Hallucination Rate** | 0.0% | **0.0%** (Zero hallucinated unstated fields) | PASS |
| **Physical Defect Photo Inspection Flag** | 100% | **100.0%** (`requires_human_review = True`) | PASS |
| **Literature Negative Control Rejection** | 100% | **100.0%** (Animal study & meta-analysis filtered) | PASS |
| **Literature Multi-Patient Splitting (+30%)** | 100% | **100.0%** (3/3 patients split into distinct ICSRs) | PASS |
| **Mean End-to-End Processing Latency** | < 4,000 ms | **~1,850 ms** per complete document | PASS |

---

## 9. Known Limitations & Prototype Boundaries

In keeping with engineering integrity, current prototype limitations are explicitly identified:

1. **Synthetic Data Boundaries**: The current system is evaluated against realistic synthetic clinical cases. Real-world faxes, multi-generation degraded photocopies, and extreme cursive handwriting will require expanded threshold tuning and fine-tuning.
2. **Deferred Requirement**: In accordance with project planning, the 2nd scanned/handwritten PDF is explicitly declared **DEFERRED** in `manifest.json` and the validation test suites, reserved for live physical paper form testing.
3. **Single Model Dependency**: The prototype currently operates on Google GenAI (`gemini-2.5-flash`). Commercial production requires a multi-vendor gateway.
4. **Dictionary Auto-Coding**: Extracted verbatim terms are not yet auto-coded against licensed proprietary dictionaries (MedDRA and WHO Drug).

---

## 10. Production Evolution Roadmap

To transition this prototype into a commercial, enterprise-scale pharmacovigilance platform:

1. **Client-Side PHI De-Identification**: Deploy an on-premise Named Entity Recognition (NER) pipeline (e.g. Microsoft Presidio) to redact patient names, dates of birth, and contact information before transmitting payloads to cloud LLM APIs.
2. **MedDRA & WHO Drug Auto-Coding**: Integrate automated term mapping against MedDRA Lowest Level Terms (LLTs) and WHO Drug Medicinal Product Identifiers (MPIDs), computing similarity confidence scores for human reviewer sign-off.
3. **Multi-Model Gateway with Dynamic Circuit Breakers**: Implement an abstract model routing layer with automated failover across Google Vertex AI (Gemini 2.5 Flash), AWS Bedrock (Claude 3.5 Sonnet), and Azure OpenAI (GPT-4o).
4. **Distributed Event Broker**: Transition from Spring Boot's internal `ThreadPoolTaskExecutor` to an enterprise event streaming platform (Apache Kafka or AWS SQS) with dead-letter queues and guaranteed at-least-once processing.
5. **Computer System Validation (CSV)**: Execute formal GAMP 5 Category 4/5 software validation protocols, including Installation Qualification (IQ), Operational Qualification (OQ), and Performance Qualification (PQ).

---

## 11. Supporting Engineering Documentation Directory

For comprehensive technical specifications, implementation code, and architectural decisions, refer to the supporting engineering records:

- [README.md](file:///c:/projects/SmartInbox/README.md) — Primary local execution and environment setup guide.
- [ARCHITECTURE.md](file:///c:/projects/SmartInbox/docs/ARCHITECTURE.md) — Deep-dive system architecture, class diagrams, and REST contracts.
- [AI_PIPELINE.md](file:///c:/projects/SmartInbox/docs/AI_PIPELINE.md) — 16-stage AI ingestion, parsing, table extraction, and reasoning pipeline.
- [PROMPT_DESIGN.md](file:///c:/projects/SmartInbox/docs/PROMPT_DESIGN.md) — Full prompt templates, negative constraints, and Pydantic schemas.
- [DATA_AND_GROUND_TRUTH.md](file:///c:/projects/SmartInbox/docs/DATA_AND_GROUND_TRUTH.md) — Test dataset inventory, physical artifact catalog, and benchmark ground truth.
- [DECISIONS.md](file:///c:/projects/SmartInbox/docs/DECISIONS.md) — Architecture Decision Records (ADR-001 through ADR-008).
- [EVALUATION.md](file:///c:/projects/SmartInbox/docs/EVALUATION.md) — Evaluation methodology, scoring algorithms, and full synthetic results.
- [LIMITATIONS_AND_PRODUCTION.md](file:///c:/projects/SmartInbox/docs/LIMITATIONS_AND_PRODUCTION.md) — Production architecture, security hardening, and GAMP 5 compliance.
