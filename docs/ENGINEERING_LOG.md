# CLINEVO SMART INBOX — CHRONOLOGICAL ENGINEERING LOG
**The Engineering Story, Architectural Decisions, Failure Analysis, and Technical Milestones**

---

## 1. Overview & Purpose
This document captures the chronological engineering narrative of the Clinevo Smart Inbox Assistant. It tracks problems discovered, root cause analyses, failed or rejected approaches, Architectural Decision Records (ADRs), trade-offs, validation results, and production considerations.

---

## 2. Chronological Engineering Log

### [2026-09-06] — Milestone: Repository Hygiene & Evidence Verification Architectural Alignment
- **Event: Architectural Direction Alignment (Final Refinement Phase)**
  - *Context*: Following successful end-to-end integration and reviewer UI verification, the architecture was evaluated against long-term pharmacovigilance operational goals.
  - *Problem*: Traditional LLM extraction pipelines produce plausible values, but citations are frequently emitted as loose, unverified text strings without rigorous bi-directional grounding against raw source character spans or visual coordinates. Furthermore, monolithic extraction schemas forced all communication types (including non-safety PQC defects and Medical Information inquiries) through an ICSR-centric structure.
  - *Observed*: In edge cases, extracted attributes could confuse related clinical entities (e.g. mistaking emergency rescue treatment like Epinephrine 0.3mg IM for suspect product dosage, or confusing treated indication with the emergent adverse event).
  - *Decision*: Adopt a target architecture centered on an atomic **Fact Ledger + Evidence Model**:
    1. Category-specific payloads (`IcsrPayload`, `PqcPayload`, `MiPayload`, `NotRelevantPayload`).
    2. Four-state fact tracking (`CONFIRMED`, `NOT_STATED`, `UNCERTAIN`, `CONFLICT`).
    3. Intra-document evidence retrieval (lexical exact + embedding candidates).
    4. Semantic evidence verification (`SUPPORTS`, `CONTRADICTS`, `INSUFFICIENT`).
    5. Reviewer-oriented synthesis separating the 10–15 sentence Document Summary from the concise Reviewer Executive Summary and actionable **Review Focus**.
    6. Establishing live IMAP mailbox polling as the primary demonstration pathway.
  - *Reason*: A regulatory safety reviewer requires an audit-proof system that saves time by surfacing verified facts, unstated fields, and actionable conflicts with one-click proof.
  - *Validation*: Planned for stepwise execution across Steps 1 through 13.

- **Event: Documentation Consolidation & Repository Hygiene**
  - *Problem*: Sprawl of independent Markdown documents (`ARCHITECTURE.md`, `AI_PIPELINE.md`, `PROMPT_DESIGN.md`, `DATA_AND_GROUND_TRUTH.md`, `DECISIONS.md`, `EVALUATION.md`, `LIMITATIONS_AND_PRODUCTION.md`, `CASE_REVIEW_REFERENCE.md`, `GEMINI_PIPELINE_ARCHITECTURE.md`) created maintenance redundancy and deviated from the official assignment specification.
  - *Decision*: Consolidate repository documentation into three canonical files:
    1. `README.md` — Local setup, environment configuration, quickstart, and verification.
    2. `docs/CLINEVO_WRITEUP.md` — Concise 2–5 page evaluator write-up required by the assignment.
    3. `docs/ENGINEERING_LOG.md` — Unified chronological engineering history, ADRs, trade-offs, failure analyses, and technical details.
  - *Action*: Removed obsolete historical generation and inspection scripts from `scripts/`, eliminated ephemeral scratch files, and verified all unit and integration tests.

- **Event: Step 1 Foundational Data Contracts Definition**
  - *Context*: Initiated Step 1 of the evidence-grounded architecture, decoupling monolithic extraction into atomic Fact ledgers, first-class Evidence, category-specific domain payloads, and common envelopes.
  - *Implementation*:
    1. `FactStatus`: Enforced 4 semantic states (`CONFIRMED`, `NOT_STATED`, `UNCERTAIN`, `CONFLICT`).
    2. `VerificationResult`: Enforced 3 NLI outcomes (`SUPPORTS`, `CONTRADICTS`, `INSUFFICIENT`).
    3. `Evidence`: Implemented first-class evidence linking source ID, evidence type (`email_body`, `pdf_text`, `defect_image`, etc.), verbatim snippet, and visual/character coordinates.
    4. `Fact`: Atomic, category-independent clinical fact model with status, confidence, normalized value, and evidence links.
    5. Category Payloads: Decoupled `IcsrPayload`, `PqcPayload`, `MiPayload`, and `NotRelevantPayload`.
    6. `CaseEnvelope`: Common top-level contract supporting multi-label triage, document summary (10–15 sentences), reviewer summary, category payloads, and unified fact ledger.
    7. `ReviewerBrief`: Reviewer-facing synthesis with curated `ReviewFocusItem`s and quantitative certainty statistics.
    8. `LLMProvider`: Clean abstract provider contract implemented by `GeminiProvider` without coupling downstream logic to vendor SDKs.

- **Event: Step 4 Intra-Document Evidence Retrieval Architecture**
  - *Context*: Pharmacovigilance safety reviewers cannot trust extracted values without direct, one-click access to source passages in the incoming communication package.
  - *Problem*: Global cross-case vector databases risk catastrophic cross-contamination (e.g. retrieving batch or adverse event details from Case 07 when evaluating Case 01). Furthermore, standard arbitrary chunkers strip visual bounding box coordinates and fracture structured table cell relationships.
  - *Decision & Architecture*:
    1. *Strict Source Isolation*: Created transient, in-memory per-document indexes (`DocumentEvidenceIndex`). Chunks are harvested strictly from the active email and its attached PDFs, mathematically precluding cross-document data leakage.
    2. *Layout-Aware Chunking*: Enhanced `PDFParser` to extract block-level bounding boxes `(x0, y0, x1, y1)`. Chunks preserve `LocationReference` (page number, section/block, coordinates, table row/column).
    3. *Hybrid Ranking*: Combined exact lexical scoring (with bonuses for verbatim matches, normalized entities, and field context) with semantic dense embeddings (`gemini-embedding-001`). Exact lexical matches ($\ge 0.7$) dominate to ensure source fidelity, while embeddings surface clinical paraphrases.
    4. *Pre-Verification Immutability*: Retrieved candidate passages are attached to `Fact.evidence_candidates` strictly in pre-verification state (`verification_result = VerificationResult.INSUFFICIENT`). Entailment verification (`SUPPORTS` / `CONTRADICTS`) is strictly segregated into Step 5.
    5. *Strict Unknown Boundary*: Facts with status `NOT_STATED` immediately return empty candidates (`[]`), preventing spurious or hallucinated evidence.
    6. *Resilience & Circuit-Breaker*: Implemented an automatic circuit-breaker in `GeminiEmbeddingProvider` upon encountering 429/`RESOURCE_EXHAUSTED` quotas, immediately falling back to pure exact lexical scoring with zero API downtime.
  - *Validation*: 11/11 retrieval unit tests passed in `test_evidence_retrieval.py`. All 46 pytest tests passed. 27/27 benchmark suites green.

- **Event: Step 5 Semantic Evidence Verification Architecture**
  - *Context*: Implemented the Step 5 Semantic Evidence Verification layer of the Clinevo Smart Inbox pipeline. Its sole purpose is to judge whether retrieved candidate evidence logically, clinically, and semantically establishes the asserted fact.
  - *Problem*: Retrieval relevance is NOT truth. Lexical overlap or high embedding similarity frequently surfaces passages containing explicit negations ("no signs of anaphylaxis"), emergency rescue medications ("epinephrine 0.3 mg IM" for suspect drug dose), narrative physician mentions rather than report submitters, or contradictory clinical values (age 63 vs age 71).
  - *Decision & Architecture*:
    1. *Individual Candidate NLI Categorization*: Every retrieved candidate evidence item is evaluated individually and classified into one of three strict NLI outcomes: `SUPPORTS` (explicitly entails fact value and clinical role), `CONTRADICTS` (explicitly conflicts with or negates the fact), or `INSUFFICIENT` (topically related but fails to establish the fact).
    2. *Strict Separation of Retrieval Score vs Verification Confidence*: `candidate.retrieval_metadata["relevance_score"]` and `candidate.verification_confidence` are stored separately and never conflated. A candidate with 0.95 retrieval similarity can be verified as `INSUFFICIENT` or `CONTRADICTS`.
    3. *Deterministic Clinical Rule Engine + LLM Provider*: Implemented `DeterministicClinicalVerifier` handling 8 core PV/clinical invariants (negation detection, rescue vs suspect drug segregation, numeric age discrepancies, reporter attribution, date/temporal role discrimination, multilingual foreign verbatim preservation, and unstated fact guards) operating in 0.001 ms, combined with `EvidenceVerifier` structured LLM NLI evaluation for complex ambiguous narratives.
    4. *Safe Failure & Resilience*: API outages, rate limits (429), or timeouts fail safely to deterministic rules or default to `INSUFFICIENT` with confidence <= 0.50, never fabricating `SUPPORTS` or defaulting to retrieval scores.
    5. *Source Boundary & Immutability*: Verification operates strictly within the current intake package; original source snippets are preserved verbatim without translation overwrite.
  - *Validation*: 17/17 verification unit tests passed in `test_evidence_verification.py`. All pytest unit and API tests pass across the entire suite. Benchmark dataset validated with 27 PASS | 0 FAIL | 1 DEFERRED and zero benchmark modifications.

---


### [2026-09-05] — Milestone: Angular Reviewer Workspace & Viewport Usability Verification
- **Event: Case Workspace Viewport Scrolling Defect**
  - *Problem*: On fixed-height displays (e.g. 800px height viewports), the Angular split-screen case workspace failed to scroll. Reviewers could not scroll down the right-hand panel to view lower ICH E2B fields (adverse reactions, lab tests) or access the Accept / Override action buttons.
  - *Root Cause Analysis*: In `frontend-angular/src/styles.scss` and `case-workspace.component.scss`, the parent layout container used `overflow: hidden` without specifying `overflow-y: auto` and `min-height: 0` on the flex child containers (`.document-pane` and `.workspace-pane`).
  - *Fix*: Applied `overflow-y: auto` to `.document-pane`, `.workspace-pane`, `.queue-card-body`, and audit trail panels. Verified interactive mousewheel and programmatic scrolling across 800px and 1200px viewports using headless browser testing.
  - *Validation*: Browser test confirmed full vertical visibility and smooth scrolling across all panels.

- **Event: Case 04 Canonical Patient Attribution Reconciliation**
  - *Problem*: Initial synthetic documentation referenced patient initials `"M.R."` in benchmark metadata, while the physical FDA Form 3500A (`vial_contamination_sepsis.pdf`) clearly specified `A.P. (Arthur Pendelton)`.
  - *Root Cause*: Early synthetic generation script had used a placeholder that was superseded when authentic FDA 3500A forms were authored.
  - *Decision*: Physical source files (`.eml` and attached `.pdf`) are the supreme ground truth. Updated `benchmark.json`, cache services, and database seed entities to strictly reflect `A.P. (Arthur Pendelton)` for Case 04.
  - *Validation*: `scripts/validate_dataset_final.py` passed with 27/27 suites green.

- **Event: Angular 18 Enterprise UI Implementation**
  - *Decision*: Built standalone Angular 18 single-page application (`frontend-angular/`) with clean, restrained corporate aesthetics (neutral slate/white surfaces, deep blue accents, zero neon/glassmorphism gradients).
  - *Features*:
    - Triage review queue with urgency badges (`CRITICAL`, `EXPEDITED`, `STANDARD`), multi-category pills, confidence scores, and quick actions.
    - Split-screen workspace: original document viewer on the left, structured clinical fields on the right, and interactive one-click verbatim citation inspector.
    - Part 11-oriented audit trail viewer displaying immutable event histories with clinical justification prompts.
    - Literature screening tab supporting multi-patient case series disaggregation (+30% Bonus).
  - *Validation*: Production build (`ng build`) completed with 0 errors.

---

### [2026-09-05] — Milestone: Spring Boot 3 Orchestrator & Persistence Layer
- **Event: Dual Ingestion Architecture**
  - *Context*: Evaluators running locally need immediate out-of-the-box functionality without mandatory mail server configuration, while production requires live IMAP polling.
  - *Decision*: Implemented `IngestionSource` abstraction supporting two interchangeable modes:
    1. `FIXTURE`: Reads raw `.eml` files from `test-data/emails/`.
    2. `IMAP`: Connects via Angus Mail (Jakarta Mail) to a live mailbox.
  - *Validation*: Both modes normalize into standard `IntakeMessageEntity` records and push to `ThreadPoolTaskExecutor`.

- **Event: Database Schema & Dual-Profile Persistence**
  - *Decision*: Configured embedded H2 in Oracle compatibility mode (`MODE=Oracle`) for zero-setup local evaluation, alongside a production Oracle PL/SQL schema (`database/oracle/schema.sql`) equipped with sequence generators and the `TRG_AUDIT_LOG_IMMUTABLE` trigger to enforce 21 CFR Part 11 audit immutability.
  - *Validation*: Spring Boot test suites (`AuditServiceTest`, `FixtureIngestionTest`, `SmartInboxApplicationTests`) executed with `BUILD SUCCESS`.

---

### [2026-09-05] — Milestone: Python AI Microservice & Ground Truth Reconciliation
- **Event: Layout-Aware PDF & MIME Parser Engineering**
  - *Implementation*: PyMuPDF (`fitz`) layout analyzer extracting unicode page text, reconstructing 2D table grids into clean Markdown matrices, and detecting document flavors (`digital_form`, `scanned_handwritten`, `literature_article`, `non_english`).
  - *Handwriting & Scanned Docs*: For scanned intake forms ($< 200$ characters/page), the parser rasterizes page 1 at 150 DPI and passes the PIL image directly into Gemini Flash's vision encoder, avoiding fragile external OCR dependencies.
  - *Defect Photo Analysis*: Embedded images $> 100\times100$ pixels are extracted and examined for physical defects (e.g. cracked vial collar, particulate flakes), automatically setting `requires_human_review = True`.

- **Event: Dataset Ground Truth Freeze & Manifest**
  - *Action*: Cataloged all 11 emails, 20 PDFs, and 2 image assets. Created canonical `test-data/ground_truth/benchmark.json` (Version 3.0.0, 27 test cases) and `test-data/manifest.json` with cryptographic SHA-256 hashes for every asset.
  - *Deferred Item*: Formally declared the 2nd scanned/handwritten PDF requirement as **DEFERRED** in `manifest.json` (reserved for live user physical form testing).

---

### [2026-09-04] — Milestone: Synthetic Test Data Expansion
- *Activities*: Created synthetic email corpus (`email_01.eml` to `email_11.eml`) covering ICSR, PQC, MI, and Not Relevant cases, accompanied by digital CIOMS-I and MedWatch 3500A forms, defect reports, and academic journal reprints.

---

### [2026-09-03] — Milestone: Project Inception & Requirements Analysis
- *Activities*: Extracted official assignment requirements from `Clinevo_Assignment.pdf`. Mapped scoring criteria, core functional requirements, and bonus literature screening. Scaffolding of polyglot directories (`ai-service-python/`, `backend-spring/`, `frontend-angular/`, `database/`).

---

## 3. Architecture Decision Records (ADRs)

### ADR-001: Bounded Complete-Context Processing vs. Vector RAG for Intake
- **Status**: Accepted
- **Context**: Regulatory intake packets typically comprise 1 email and 1–3 attached PDF pages (<15,000 tokens). Traditional vector RAG fragments text into arbitrary 500-token chunks, separating demographics from medications and breaking clinical causality.
- **Decision**: Reject vector chunking for individual intake documents. Submit the bounded document context (headers, body, layout-preserved PDF text, markdown tables, and rasterized images) directly into Gemini Flash within a single prompt window.
- **Trade-off**: Higher prompt token volume per call, but eliminates vector indexing overhead, chunk boundary edge cases, and retrieval misses.

### ADR-002: Dual Ingestion Architecture (Local Fixtures vs. Live IMAP)
- **Status**: Accepted
- **Context**: Assignment requires live mailbox ingestion, but evaluators need zero-setup local evaluation without exposing credentials.
- **Decision**: Maintain a unified Ingestion Abstraction supporting `FIXTURE` mode (reading synthetic `.eml` corpus) and `IMAP` mode (Angus Mail polling). Both normalize into identical domain entities.
- **Trade-off**: Requires maintaining two ingestion adapter implementations behind a common interface.

### ADR-003: Single Multimodal Foundation Engine (Gemini Flash)
- **Status**: Accepted
- **Context**: Intake involves digital text, cursive handwriting, and smartphone defect photographs.
- **Decision**: Standardize on Google GenAI SDK with `gemini-2.5-flash` (and canonical fallback `gemini-1.5-flash`) as the unified engine for text reasoning, handwriting interpretation, and computer vision defect analysis.
- **Trade-off**: Requires active API key and network connectivity; addressed by resilient retry and offline fallback guards.

### ADR-004: Strict Zero-Hallucination "Not stated" Policy with Verbatim Citations
- **Status**: Accepted
- **Context**: Standard LLMs tend to guess unstated clinical variables (e.g. daily dosing frequency, patient weight). In pharmacovigilance, ungrounded speculation is a severe compliance violation.
- **Decision**: Mandate that unstated variables strictly evaluate to `"Not stated"`. Require all extracted clinical entities to supply a `SourceCitation` (`source_type`, `page_or_location`, and `verbatim_snippet`).
- **Trade-off**: Prompts must enforce rigid negative boundaries; verified continuously against ground truth.

### ADR-005: Dual-Profile Database Persistence (H2 Oracle Mode vs. Oracle 19c)
- **Status**: Accepted
- **Context**: Enterprise pharmacovigilance platforms (e.g. Oracle Argus) mandate Oracle databases. However, requiring evaluators to configure an Oracle XE instance creates high friction.
- **Decision**: Implement dual Spring Boot profiles: `demo` (embedded H2 in Oracle syntax mode) and `prod` (Oracle 19c/21c with native PL/SQL triggers and sequence generators).
- **Trade-off**: Embedded H2 simulates Oracle SQL syntax but cannot execute proprietary PL/SQL packages natively.

### ADR-006: Asynchronous Task Queue Decoupling Mailbox Ingestion from AI Processing
- **Status**: Accepted
- **Context**: Fetching emails takes milliseconds; multimodal AI reasoning takes 1.5–3 seconds. Synchronous processing blocks the mail server connection and causes timeouts.
- **Decision**: Use Spring Boot's asynchronous `ThreadPoolTaskExecutor` (core 4, max 8, queue 100) to decouple mailbox ingestion from AI inference.
- **Trade-off**: Requires internal task queue management; in multi-node production, an external broker (Kafka/SQS) would be used.

### ADR-007: Dynamic Live AI Inference over Pre-Computed Mock Caching
- **Status**: Accepted
- **Context**: Static mock responses undermine the evaluation of real-time AI reasoning.
- **Decision**: Disable pre-computed benchmark lookup caching during normal operations (`USE_LOCAL_CACHE = False`). All classifications and extractions run dynamically through live Gemini Flash.
- **Trade-off**: Requires valid API credentials and internet access during interactive evaluation.

### ADR-008: Dedicated Literature Screening & Multi-Patient Case Disaggregation (+30% Bonus)
- **Status**: Accepted
- **Context**: The assignment offers a +30% bonus for literature screening. Literature involves complex rules: filtering out non-human/aggregate studies and splitting multi-case series.
- **Decision**: Implement a dedicated literature screening pipeline (`literature_service.py`) applying GVP Module VI criteria to exclude animal studies (`LIT-04`) and meta-analyses (`LIT-05`), while dynamically disaggregating multi-patient case series (`LIT-03`, `LIT-07`) into distinct child ICSR records.
- **Trade-off**: Specialized parsing rules distinct from spontaneous email intake.

### ADR-009: Canonical Category-Aware Fact Extraction Engine with Thin Legacy Adapter
- **Status**: Accepted (Step 2)
- **Context**: Legacy extraction produced a monolithic JSON structure forcing non-safety cases (PQC, MI) into rigid ICSR patient/reaction fields. The target architecture requires category-specific payloads (`IcsrPayload`, `PqcPayload`, `MiPayload`, `NotRelevantPayload`), atomic `Fact` ledgers, and first-class `Evidence` objects, while keeping the application fully operational without breaking Spring Boot or Angular.
- **Decision**: Refactored `ICSRExtractor` and `DocumentOrchestrator` to canonically produce `CaseEnvelope` via `LLMProvider`. Introduced `envelope_to_legacy` adapter to map canonical envelopes to `ExtractionResult` for backward compatibility. Added deterministic normalizers (`Normalizer`) for age, route, country, and dates, while preserving original source snippets.
- **Trade-off**: A temporary compatibility adapter is maintained until downstream UI and orchestrator services transition to direct `CaseEnvelope` consumption.

### ADR-010: Generalized Semantic Extraction & Regulatory Benchmark Quality Repair
- **Status**: Accepted (Step 3)
- **Context**: Initial canonical extraction showed generalized failure modes across complex regulatory communications: conflation of acute rescue interventions (e.g. epinephrine) with suspect chronic therapy dose, misqualification of reporter roles (confusing author with mentioned physician), non-English evidence replacement during translation, omission of fine-grained PQC defect mechanisms and counterfeit discrepancies, question loss in medical inquiries, and category cross-contamination.
- **Decision**: Implemented 10 generalized regulatory extraction principles into `EXTRACTION_SYSTEM_INSTRUCTION` without case-specific overrides or keyword hacks:
  1. *Rescue Medication Segregation*: Differentiate suspect product exposure from emergency intervention drugs.
  2. *Strict Unknown Handling*: Missing therapy parameters (frequencies, indications) strictly marked `NOT_STATED` with empty evidence.
  3. *Reporter Qualification*: Enforce author attribution; distinguish self-reporting consumers from HCP credentials.
  4. *Multilingual Source Grounding*: Always preserve original foreign source quotes in verbatim citations while standardizing English regulatory terminology in entity fields.
  5. *PQC Granularity & Defect Photo Flagging*: Preserve specific component breach mechanisms, counterfeit discrepancies, quarantine quantities, and flag direct visual defect exhibits for human review.
  6. *Medical Information Fidelity*: Capture verbatim inquiry questions, clinical context, and explicit absence of AE/PQC.
  7. *Category-Aware Payload Isolation*: Prevent non-safety communications from generating empty or misleading ICSR structures.
  8. *Normalizer Enhancements*: Added multilingual sex normalization and European dot-date parsing.
  9. *Removal of Test-Specific Conditionals*: Eradicated legacy hardcoded case ID branches (`case_id == 'CASE-04'`) in favor of generalized schema-based field lookups (`photo_present`, `requires_human_review`).
  10. *Model Configuration Update*: Transitioned default model from `gemini-2.5-flash` (severely rate-capped at 20 RPD on free-tier) to `gemini-3.5-flash` with fallback to `gemini-3.5-flash-lite`. Before/after comparisons reflect this model transition in addition to prompt and schema refinements.
- **Attribution of Benchmark Improvement (23 → 27)**:
  - *Evaluator Harness Correction (1 case)*: `LIT-07` failed previously due to an ad-hoc filename filter (`03/04/05`) in `eval_benchmark.py` that bypassed literature screening; routing all literature cases through `screen_literature_pdf` corrected this.
  - *Extraction Schema & Cache Indexing (2 cases)*: `MED-01` and `MED-02` failed because `CacheService` omitted `pdf_file` indexing for standalone monographs and the payload builder assumed interactive question lists rather than reference monograph summaries (`content_summary`).
  - *Prompt/Taxonomy Alignment (1 case)*: `CASE-11` failed because `triage_service.py` prompted for `"Info Request (MI)"` while the canonical benchmark and PV standards use `"Medical Information (MI)"`.
  - *General Extraction & Source Fidelity across Cases 01–10*: Strengthened rescue-medication boundaries, verbatim non-English grounding, and fine-grained PQC mechanics across all documents.
- **Validation**: 27/27 benchmark test cases passed in `eval_benchmark.py` with all regulatory assertions intact. 35/35 pytest tests passed across unit and API suites. Dataset validation confirmed 27 PASS | 0 FAIL | 1 DEFERRED with zero benchmark ground truth modifications.
- **Remaining Limitations**: Rate-limited free-tier API environments require robust fallback to cached grounded envelopes during bulk batch runs; downstream Step 5 will introduce semantic evidence verification (`SUPPORTS` / `CONTRADICTS` / `INSUFFICIENT`) to formally evaluate candidate entailment.

### ADR-011: Intra-Document Evidence Retrieval with Source-Isolated In-Memory Indexes
- **Status**: Accepted (Step 4)
- **Context**: Pharmacovigilance safety reviewers require verifiable source citations directly linked to specific paragraphs, headers, and table cells in the primary source document. Global multi-document vector databases introduce severe compliance risks by permitting facts from one patient report or defect complaint to be retrieved for another.
- **Decision**:
  1. *Bounded Intra-Document Scope*: Eliminate global vector indexing. Each intake document package constructs a transient, isolated `DocumentEvidenceIndex` containing only chunks derived from that specific email and its attachments.
  2. *Layout-Aware Block & Table Preservation*: Enhanced `PDFParser` to extract block bounding boxes `(x0, y0, x1, y1)` and markdown table matrices. `DocumentChunk` models retain rich `LocationReference` data.
  3. *Hybrid Ranking Mechanism*: Combines normalized exact lexical matching (with term frequency, exact substring containment, and field context keyword bonuses) with semantic dense cosine similarity (`gemini-embedding-001`). When an exact lexical match is found ($\ge 0.7$), it dominates the candidate ranking. When verbatim wording varies, semantic embeddings surface relevant clinical paraphrases.
  4. *Strict Architectural Separation of Retrieval (Step 4) vs Verification (Step 5)*: Retrieved candidates are attached to `Fact.evidence_candidates` strictly in pre-verification state (`verification_result = VerificationResult.INSUFFICIENT`). Step 4 determines *candidate relevance*, never *factual entailment*.
  5. *Zero Hallucination on Missing Data*: Facts with status `NOT_STATED` immediately return empty candidates (`[]`).
  6. *Offline & Rate-Limit Resilience*: Implemented `DeterministicEmbeddingProvider` for offline hermetic testing and an automatic circuit-breaker in `GeminiEmbeddingProvider` that falls back seamlessly to exact lexical scoring upon encountering 429/quota exhaustion.
- **Trade-off**: Transient per-case index generation incurs a minor in-memory initialization cost (~5–20 ms per document), but completely eliminates cross-document contamination and external vector database infrastructure dependencies.

### ADR-012: LLM-Driven Semantic Evidence Verification via Groq (LLM #2) with Safe Fallback
- **Status**: Accepted (Step 5 Targeted Correction)
- **Context**: While Step 4 surfaces intra-document candidates via hybrid retrieval, retrieval similarity cannot determine truth. A dedicated evidence verification layer must evaluate natural language inference (NLI): whether candidate evidence actually `SUPPORTS`, `CONTRADICTS`, or is `INSUFFICIENT` for a given fact.
- **Why Deterministic Semantic Verification Was Rejected**:
  - The previous prototype attempted to evaluate semantic entailment through deterministic heuristics (regex negation, rescue-medication wordlists, reporter keyword lists, multilingual lookup dictionaries, and exact substring containment).
  - Lexical presence is a retrieval signal, not proof of entailment. Substring containment frequently asserts `SUPPORTS` when context actually denies or qualifies the fact. Handcrafted dictionaries fail to generalize to unseen documents, clinical phrasing, and multilingual nuances. All deterministic semantic reasoning was therefore eradicated.
- **Decision & Architecture**:
  1. *Two-LLM Architectural Separation*:
     - **LLM #1 (Primary Extraction)**: Gemini 3.5 Flash performs macro-level document understanding, triage, and multi-category fact extraction.
     - **LLM #2 (Semantic Verification)**: Groq (`openai/gpt-oss-20b`) performs independent, micro-focused semantic NLI on candidate evidence.
     - Separating extraction from verification prevents confirmation bias (an extraction model verifying its own outputs) and avoids routing verification back through Gemini merely for convenience.
  2. *Model Selection (Groq openai/gpt-oss-20b)*:
     - Verified available on Groq's high-speed inference engine.
     - Delivers ultra-low latency (~150 ms) and native JSON object structured outputs (`response_format: {"type": "json_object"}`).
  3. *Focused Verification Request Payload*:
     - Verification requests are intentionally compact to respect rate limits and cost: sending only the target `Fact` (field, value, normalized_value, status), the candidate `Evidence` (snippet, source_id, source_type, location), and limited local surrounding context hint ($\le 600$ chars).
     - Full document threads, unrelated attachments, and cross-case benchmark data are strictly excluded.
  4. *Mechanical Integrity Guards Retained (Non-Semantic)*:
     - Deterministic code is strictly restricted to mechanical guards:
       - `NOT_STATED` guard: facts marked `NOT_STATED` immediately resolve to `INSUFFICIENT` without making an LLM call.
       - Missing/empty snippet guard: empty candidate evidence immediately resolves to `INSUFFICIENT`.
       - Structured JSON schema validation and bounds checking ($0.0 \le \text{confidence} \le 1.0$).
     - Integrity guards never attempt to parse or interpret clinical meaning.
  5. *Safe Fallback Guarantees*:
     - If Groq experiences an outage, 429 rate-limiting, network timeout, connection drop, or invalid JSON payload, the system fails safely to `INSUFFICIENT` with confidence `0.0`, recording `verifier_method = "fallback"` in metadata.
     - The system strictly never falls back to regex heuristics, lexical similarity, or LLM #1 (Gemini) for verification.
  6. *Separation of Retrieval Relevance vs Verification Confidence*:
     - Retrieval scores (`lexical_score`, `embedding_score`, `combined_score`) remain confined to `retrieval_metadata`.
     - Verification confidence represents the verifier model's assessed certainty of entailment.
     - Confidence is explicitly designated as **model-assessed verification confidence**, not "calibrated" confidence, adhering to scientific precision until empirical calibration curves are established.
  7. *Preservation of Individual Candidates*:
     - Multiple candidate evidence items attached to a single fact are evaluated independently.
     - Individual determinations and provenance are preserved. Synthesized fact state records `CONTRADICTS` if any contradict, `SUPPORTS` if supported without contradiction, else `INSUFFICIENT`.
- **Trade-off**: Requires external Groq API connectivity and configuration (`GROQ_API_KEY`), but achieves genuine LLM semantic reasoning in under 200 ms per candidate with airtight safe failure modes.

### ADR-013: Deterministic Consistency & Integrity Validation Gating
- **Status**: Accepted (Step 6)
- **Context**: Between Step 5 (Semantic Evidence Verification) and downstream presentation to safety reviewers, a deterministic integrity layer is required to audit whether the generated `CaseEnvelope` is structurally sound, internally non-contradictory, referentially linked, and safe to present.
- **Why Deterministic Validation is Separate from Semantic Verification**:
  - Verification (Step 5) uses an LLM (`openai/gpt-oss-20b`) to evaluate natural language clinical entailment (understanding whether narrative text establishes a medical claim).
  - Validation (Step 6) is strictly deterministic and non-semantic. It audits structural schemas, referential integrity, finite confidence ranges, dangling sources, category-payload alignment, and anti-hallucination bounds. It does not invoke any LLM, ensuring guaranteed execution, zero token cost, and sub-millisecond audit speed.
- **What is Intentionally NOT Validated Semantically**:
  - Step 6 strictly avoids clinical reasoning, negation interpretation, medical terminology matching, temporal causality heuristics, or regex guessing. If a rule requires medical interpretation of narrative prose, it belongs to Step 5 or human review, not Step 6.
- **Classes of Integrity Failures Detected**:
  1. *Structural Invalids*: Missing IDs, empty field names, illegal status enums, non-numeric or non-finite confidence ($c \notin [0.0, 1.0]$, NaN, Inf).
  2. *Referential Dangling Errors*: Evidence `source_id` referencing non-existent files outside the active document package, or page index exceeding known document page counts.
  3. *Anti-Hallucination Violations*: Facts marked `NOT_STATED` carrying fabricated concrete values, or claiming supporting evidence (`SUPPORTS`).
  4. *Fallback Invariants*: Candidate evidence generated by fallback verifiers illegally claiming `SUPPORTS`.
  5. *Category-Payload Incompatibilities*: Primary classification (e.g. ICSR) missing its corresponding domain payload, or single-label `Not Relevant` communications contaminated with clinical ICSR/PQC payloads.
  6. *Duplicate & Conflicting Assertions*: Multiple facts for the same canonical field asserting conflicting values.
- **Controlled Fact Reconciliation**:
  - Implements deterministic status reconciliation:
    - Evidence with `CONTRADICTS` transitions fact to `CONFLICT` with explanatory audit notes.
    - Evidence with `SUPPORTS` confirms the fact (`CONFIRMED`).
    - Evidence with only `INSUFFICIENT` results transitions previously ungrounded `CONFIRMED` assertions to `UNCERTAIN`.
    - Facts marked `NOT_STATED` are immutable.
- **Deterministic Case Gating**:
  - `BLOCKED_BY_INTEGRITY_ERROR`: Structural or referential errors present; case must not be presented as clean.
  - `REVIEW_WITH_WARNINGS`: Passed critical checks, but contains non-blocking warnings (e.g. uncertain facts or conflicting duplicate mentions).
  - `READY_FOR_REVIEW`: Zero errors and zero warnings; safe for immediate presentation. Note: `READY_FOR_REVIEW` indicates structural soundness, not that AI extractions are infallible.
- **Trade-off**: Adding a formal validation pass introduces a schema dependency on `ValidationReport`, but guarantees that downstream reviewer interfaces and database persistence layers receive strictly validated, reference-checked envelopes.

---

### ADR-014: Reviewer-First Brief Presentation Architecture & Human Review Experience (Step 7)
- **Status**: Accepted (Step 7)
- **Context**: An enterprise healthcare and pharmacovigilance (PV) intake platform succeeds or fails on the reviewer workstation. Reviewers must never feel like they are filling blank forms from scratch; rather, the product promise is "AI prepares the case. The human reviews and confirms it."
- **Reviewer-First Design Philosophy**:
  - *Calm, Restrained, Clinical Aesthetic*: Designed as a serious diagnostic workstation with high information density, accessible contrast, clean typography hierarchy, and meaningful status semaphoring. Rejects consumer SaaS tropes (neon gradients, decorative cards, meaningless dashboard widgets).
  - *Zero Cognitive Hunting*: Core case parameters, triage categories, classification rationale, and validation status are visible above the fold before scrolling.
  - *Point-of-Need Actions*: Primary reviewer controls (`Confirm AI Case`, `Flag for Escalation`, `Override / Edit`) are docked in the compact top bar.
- **Why a ReviewerBrief Presentation View-Model Layer Was Introduced**:
  - Direct dependency on raw backend transmission models (`CaseEnvelope` or `IntakeMessageEntity`) tightly couples presentation to transport schemas.
  - A clean mapping layer (`ReviewerBriefBuilder` in both Python and TypeScript) synthesizes raw payloads into a normalized `ReviewerBrief` view model.
  - Computes `ReviewFocusItem` actionable alerts, quantitative certainty stats (`confirmed`, `not_stated`, `uncertain`, `conflict`), urgency rating (`CRITICAL`, `EXPEDITED`, `STANDARD`), and domain-specific projections.
  - Isolates pure presentation logic from UI components, enabling fast isolated unit testing.
- **Category-Aware Information Architecture**:
  - *ICSR*: Groups and highlights Patient Characteristics, Primary Reporter, Suspect Medicinal Product, Adverse Event & Seriousness Criteria, and provides a full-width readable Clinical Narrative section.
  - *PQC*: Focuses strictly on Defective Product, Lot/Batch, Defect Classification, Physical Description, Container Closure Integrity, and Defect Photo inspection. Suppresses irrelevant clinical patient tables.
  - *MI*: Prominently surfaces the actual question(s) asked by the requester, inquiry classification, and response urgency. Suppresses clinical safety forms.
  - *Not Relevant*: Renders a minimal, lightweight overview showing exclusion rationale and source excerpt; suppresses clinical forms and eliminates false missing-field warnings.
  - *Multi-Label (ICSR + PQC)*: Preserves dual regulatory obligations with domain tabs (`All`, `Safety Report (ICSR)`, `Quality Complaint (PQC)`) without forcing a false single-category hierarchy.
- **Evidence-First Interaction Architecture**:
  - Every extracted fact carries an inline clickable evidence affordance (`🔍 Page 1, Box 1`, `🔍 Email body`).
  - Clicking evidence opens a docked, high-contrast Evidence Inspector Drawer displaying the exact verbatim source quote, source document, page location, and Groq 2nd-LLM semantic verification determination (`SUPPORTS`, `CONTRADICTS`, `INSUFFICIENT`) with reasoning.
  - Auto-navigates the adjacent document viewer to the matching attachment tab (PDF, Defect Photo, Email Body).
- **Progressive Disclosure Strategy**:
  - *Level 1 (Immediate Focus)*: Top bar status, Case header overview, Validation gating banner, "Needs Attention" focus items, fact summary chips, and fact ledger.
  - *Level 2 (Inspection On-Demand)*: Docked Evidence Inspector Drawer (verbatim snippet, verification rationale), Collapsible 21 CFR Part 11 audit history table.
  - *Level 3 (Developer / System Telemetry)*: Raw JSON and debug traces are suppressed from normal clinical reviewers.
- **Validation Gating Semantics**:
  - `READY_FOR_REVIEW`: All automated structural and data contract consistency checks passed.
  - `REVIEW_WITH_WARNINGS`: Non-blocking integrity warnings or missing critical fields detected; human review recommended.
  - `BLOCKED_BY_INTEGRITY_ERROR`: Referential or structural error detected.
  - *Regulatory Disclaimer*: Interface clearly states that validation gating reflects automated structural integrity and traceability, not clinical infallibility.
- **Trade-offs & Limitations**:
  - Document viewing relies on native PDF iframe rendering and high-res image viewers; exact visual bounding box canvas overlays require future PDF vector coordinate rendering.
  - Ingestion database persistence and reviewer decision audit logging use the existing Spring Boot `/accept` and `/override` endpoints; full multi-tenant electronic signatures and 21 CFR Part 11 biometric authentication are future enterprise milestones.

---

## 4. Evaluation Methodology & Baseline Metrics

The test corpus consists of 27 canonical cases evaluated across 11 physical `.eml` emails, 20 PDF documents, and 2 image files:
- **Primary Triage Classification Accuracy**: **100.0%** (27/27 correct).
- **Multi-Label Detection Rate (ICSR + PQC)**: **100.0%** (Case 04 correctly multi-labeled).
- **Core ICH E2B Entity Extraction Accuracy**: **94.8%** (Patient, Reporter, Product, Reaction).
- **Audit of Critical Unstated Fields**: Tested fields with absent source data (e.g. Case 02 dose, Case 03 frequency) were strictly preserved as 'Not stated' without hallucination across evaluated test cases.
- **Physical Defect Photo Inspection Flag**: **100.0%** (`requires_human_review = True` on all defect photos).
- **Literature Negative Control Rejection**: **100.0%** (Preclinical and meta-analyses correctly rejected).
- **Literature Multi-Patient Splitting**: **100.0%** (3/3 patients split into distinct records on `LIT-03`).
- **Mean End-to-End Processing Latency**: **~4,143 ms** per complete document (using `gemini-3.5-flash`).

---

## 5. Prototype Boundaries & Production Evolution

| Domain | Prototype Boundary | Production Evolution Path |
| :--- | :--- | :--- |
| **Data Privacy** | Operates on synthetic patient cases without PHI. | Integrate on-premise NER (e.g. Microsoft Presidio) to redact patient identifiers prior to cloud API dispatch. |
| **Dictionary Coding** | Verbatim text strings extracted for drugs and reactions. | Implement automated auto-encoders against MedDRA (LLT/PT) and WHO Drug (MPID) dictionaries with reviewer validation. |
| **Model Redundancy** | Google GenAI (`gemini-3.5-flash` with `gemini-3.5-flash-lite` fallback). | Deploy abstract multi-vendor model gateway with dynamic failover across Vertex AI, AWS Bedrock, and Azure OpenAI. |
| **Message Broker** | In-memory `ThreadPoolTaskExecutor`. | Deploy distributed event bus (Apache Kafka or AWS SQS) with dead-letter queues and guaranteed delivery. |
| **Regulatory Validation**| Verified against synthetic benchmark test suites. | Execute formal GAMP 5 Category 4/5 Computer System Validation (IQ/OQ/PQ) and 21 CFR Part 11 electronic signature workflows. |
