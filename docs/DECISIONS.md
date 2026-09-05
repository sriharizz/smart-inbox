# ARCHITECTURE DECISION RECORDS (ADR) — CLINEVO SMART INBOX ASSISTANT

This document records the key architectural, AI, infrastructure, and engineering decisions established throughout the development of the Clinevo Smart Inbox Assistant.

---

## ADR-001: Bounded Complete-Context Processing vs. Vector RAG for Intake Documents

- **Status**: Accepted
- **Context**: Incoming regulatory communications consist of single emails (typically 1–3 pages) with 1 to 3 attached PDF documents (e.g. CIOMS-I 1-page form, FDA 3500A 1-page form, 2–4 page clinical reprints, or 1-page defect photos). In typical enterprise GenAI systems, teams frequently apply chunk-based vector Retrieval-Augmented Generation (RAG).
- **Decision**: Reject vector chunking / vector database retrieval for individual intake documents. Feed complete, bounded document context (email headers + email body + layout-preserved PDF text + structured tables + rasterized defect photos) directly into Gemini Flash within a single prompt window.
- **Alternatives Considered**:
  1. *Vector RAG (LangChain / ChromaDB / pgvector)*: Chunk documents into 500-token segments, embed with text-embedding models, and retrieve top-k chunks.
  2. *Summary-only Pipeline*: Summarize attachments first, then extract facts from summaries.
- **Rationale**:
  1. Pharmacovigilance criteria require cross-section synthesis (e.g., patient age in Box 1, suspect drug in Box 14, adverse reaction in Box 24). Vector chunking fragments these relational dependencies, leading to broken citations and missing clinical facts.
  2. The modern context window of Gemini Flash (1,000,000+ tokens) comfortably encompasses the entire intake packet (typically under 15,000 tokens) with near-instantaneous latency and complete contextual visibility.
- **Trade-offs**: Slightly higher token consumption per API call compared to retrieving 2 tiny chunks, but completely eliminates vector indexing overhead, embedding latency, chunk boundary edge cases, and retrieval misses.

---

## ADR-002: Dual Ingestion Architecture (Local EML Fixture vs. Live IMAP Polling)

- **Status**: Accepted
- **Context**: The assignment requires connecting to a real test mailbox. However, evaluators running the repository locally may lack immediate access to corporate mailboxes or wish to run automated tests offline without exposing credentials.
- **Decision**: Implement a unified Ingestion Abstraction supporting two interchangeable modes driven by configuration (`INGESTION_MODE=FIXTURE` vs. `INGESTION_MODE=IMAP`):
  1. `FIXTURE`: Scans `test-data/emails/` locally, reading authentic `.eml` files.
  2. `IMAP`: Connects via Angus Mail (Jakarta Mail) to a live IMAP mailbox (e.g. Gmail / Outlook).
  Both modes convert messages into an identical `IntakeMessage` domain model and feed into the exact same downstream queue and AI microservice.
- **Alternatives Considered**:
  1. *IMAP-only*: Forces every evaluator to set up a Gmail test account and App Password before running any code.
  2. *Mock Data Service*: Simulates emails using hardcoded JSON in code.
- **Rationale**: Guarantees 100% assignment compliance (real IMAP connectivity) while providing zero-friction out-of-the-box local evaluation using frozen, authentic `.eml` files.
- **Trade-offs**: Requires maintaining two ingestion adapter implementations behind a common interface.

---

## ADR-003: Single Multimodal LLM Engine (Gemini Flash) for Text Reasoning and Vision

- **Status**: Accepted
- **Context**: Pharmacovigilance documents involve digital text, scanned/handwritten clinical forms, and photographic evidence (defective vials, cracked pump collars).
- **Decision**: Standardize on Google GenAI SDK with Gemini Flash (`gemini-2.5-flash` with canonical fallback `gemini-flash-latest`) as the single unified foundation model for both text extraction/reasoning and native multimodal computer vision.
- **Alternatives Considered**:
  1. *Separate OCR Tool (Tesseract / EasyOCR) + Text LLM*: Run Tesseract for handwriting/images, then feed raw OCR output to an LLM.
  2. *Dual Model (OpenAI GPT-4o for vision + Claude 3.5 Sonnet for text)*: Multi-vendor setup.
- **Rationale**:
  1. Traditional standalone OCR tools perform poorly on clinical cursive handwriting and cannot interpret photographic evidence (e.g. assessing whether a vial cap has a crimp defect or floating particulate).
  2. Gemini Flash possesses native multimodal capabilities, allowing high-resolution PIL images and text to be passed in the same context, eliminating OCR pipeline drift and reducing vendor complexity.
- **Trade-offs**: Requires internet connectivity and an active `GEMINI_API_KEY`.

---

## ADR-004: Strict Zero-Hallucination "Not stated" Policy with Verbatim Citations

- **Status**: Accepted
- **Context**: Standard LLMs tend to be overly cooperative, frequently hallucinating unstated details (e.g., inferring "once daily" dosing if not stated, or assuming patient sex based on clinical conditions). In pharmacovigilance, hallucinating unstated facts is a critical regulatory violation.
- **Decision**: Enforce a strict "Not stated" policy in system instructions and Pydantic schemas. If any field is not explicitly present in the physical source document, the model MUST output `"Not stated"`. Furthermore, every populated entity group MUST provide an auditable `SourceCitation` (`source_type`, `page_or_location`, `verbatim_snippet`).
- **Alternatives Considered**:
  1. *Allowing Model Inference with Confidence Annotations*: Let the model guess with lower confidence.
  2. *Omitting Missing Keys*: Omitting null fields from JSON output.
- **Rationale**: Regulatory compliance demands transparent differentiation between explicit evidence and missing data. Requiring a verbatim quote forces the model to ground every non-"Not stated" value in physical text.
- **Trade-offs**: Prompts must be strictly calibrated; requires rigorous negative-control testing.

---

## ADR-005: Dual-Profile Database Persistence (H2 Oracle Mode vs. Oracle XE)

- **Status**: Accepted
- **Context**: Pharmacovigilance enterprise suites (Oracle Argus Safety) rely heavily on Oracle Database with PL/SQL triggers and sequences. However, requiring evaluators to install a multi-gigabyte Oracle XE database or container creates extreme evaluation friction.
- **Decision**: Implement dual database profiles in Spring Boot 3:
  1. `demo` (Default): Embedded in-memory H2 database configured in Oracle compatibility mode (`MODE=Oracle;DEFAULT_NULL_ORDERING=HIGH`).
  2. `prod`: Authentic Oracle Database 19c/21c with native PL/SQL sequences, triggers, and immutable audit log constraints.
- **Alternatives Considered**:
  1. *PostgreSQL*: Popular open-source database, but deviates from the pharmaceutical industry standard (Oracle).
  2. *Oracle-only*: High barrier to evaluation; requires Docker or cloud Oracle XE instance.
- **Rationale**: Provides zero-friction evaluation out of the box while preserving genuine enterprise Oracle PL/SQL readiness.
- **Trade-offs**: H2 Oracle mode emulates Oracle syntax but does not execute complex PL/SQL package procedures natively.

---

## ADR-006: Asynchronous Processing Queue Decoupling Mailbox Ingestion from AI Evaluation

- **Status**: Accepted
- **Context**: Fetching emails via IMAP takes milliseconds, whereas multimodal LLM inference takes 1–3 seconds per document. Synchronous processing would cause mailbox timeouts and block the intake loop.
- **Decision**: Use Spring Boot's asynchronous `ThreadPoolTaskExecutor` to decouple mailbox polling from AI document processing. Ingestion persists the message as `RECEIVED` and pushes the task ID to an internal bounded worker queue.
- **Alternatives Considered**:
  1. *Synchronous Ingestion*: Process each email immediately upon retrieval.
  2. *External Message Broker (Kafka / RabbitMQ)*: Enterprise message queue.
- **Rationale**: ThreadPoolTaskExecutor provides asynchronous decoupling without requiring additional infrastructure dependencies (like Kafka or Zookeeper) for local demonstration.
- **Trade-offs**: In a multi-node production deployment, an external broker like Kafka would be required for distributed queue persistence.

---

## ADR-007: Dynamic Live AI Inference over Pre-Computed Mock Caching

- **Status**: Accepted
- **Context**: During initial prototyping, local benchmark caching was explored to conserve API tokens. However, returning pre-computed benchmark JSON lookups resembles faking results.
- **Decision**: Disable and remove all mock/cache lookups from the AI processing services. All classifications and extractions run 100% dynamically through live Gemini Flash.
- **Alternatives Considered**:
  1. *Enable Local Benchmark Fallback*: If API fails or offline, return benchmark ground truth.
- **Rationale**: External reviewers must evaluate genuine AI reasoning, multimodal vision, and prompt grounding on physical files, not pre-computed static JSON files.
- **Trade-offs**: Requires a valid `GEMINI_API_KEY` and internet access during evaluation.

---

## ADR-008: Dedicated Literature Screening & Multi-Patient Case Splitting Pipeline (+30% Bonus)

- **Status**: Accepted
- **Context**: The Clinevo assignment offers a +30% bonus for automated literature screening: detecting whether published articles describe reportable patient cases, filtering out non-reportable papers (preclinical studies, meta-analyses), and splitting multi-case series into separate ICSR records.
- **Decision**: Implement a specialized service (`LiteratureService`) and REST endpoint (`POST /api/v1/literature/screen-and-split`), accompanied by a dedicated tab in the Angular reviewer interface.
- **Alternatives Considered**:
  1. *Route literature through standard email extractor*: Treat literature PDFs as regular single-patient intake attachments.
- **Rationale**: Literature articles possess distinct academic structures (abstracts, cohorts, discussion noise, references) and frequently report multiple patients in a single paper (e.g. 1 article -> 3 distinct ICSRs). A dedicated screening pipeline isolates clinical cases without polluting standard inbox triage.
- **Trade-offs**: Additional schema complexity (`LiteratureScreenResult`) and specialized prompt design.
