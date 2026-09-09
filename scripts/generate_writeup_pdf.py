import subprocess
import os
import fitz

html_content = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Clinevo Smart Inbox Assistant — Technical Write-Up</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

  @page {
    size: A4;
    margin: 12mm 14mm 12mm 14mm;
  }

  * {
    box-sizing: border-box;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }

  body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    color: #1e293b;
    background: #ffffff;
    font-size: 7.9pt;
    line-height: 1.36;
    margin: 0;
    padding: 0;
  }

  .sheet {
    page-break-after: always;
    break-after: page;
    height: 268mm;
    max-height: 268mm;
    overflow: hidden;
    position: relative;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }

  .sheet:last-child {
    page-break-after: avoid;
    break-after: avoid;
  }

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #cbd5e1;
    padding-bottom: 4px;
    margin-bottom: 7px;
    font-size: 6.8pt;
    font-weight: 600;
    color: #64748b;
    letter-spacing: 0.5px;
    text-transform: uppercase;
  }

  .page-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-top: 1px solid #cbd5e1;
    padding-top: 4px;
    margin-top: 6px;
    font-size: 6.8pt;
    color: #94a3b8;
  }

  /* Hero Banner */
  .hero-banner {
    border-bottom: 2px solid #3b82f6;
    padding-bottom: 6px;
    margin-bottom: 8px;
  }

  .brand-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 4px;
  }

  .brand-title {
    font-family: 'Outfit', sans-serif;
    font-size: 9.5pt;
    font-weight: 800;
    letter-spacing: 1.2px;
    color: #2563eb;
    text-transform: uppercase;
  }

  .doc-badge {
    background: #eff6ff;
    color: #1d4ed8;
    font-size: 7pt;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 9999px;
    border: 1px solid #bfdbfe;
    text-transform: uppercase;
  }

  h1.main-title {
    font-family: 'Outfit', sans-serif;
    font-size: 15.5pt;
    font-weight: 800;
    color: #0f172a;
    line-height: 1.15;
    margin: 0 0 3px 0;
  }

  .subtitle {
    font-size: 8.5pt;
    font-weight: 500;
    color: #475569;
    margin: 0 0 7px 0;
    line-height: 1.3;
  }

  .meta-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 8px;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 5px 9px;
  }

  .meta-item {
    font-size: 7.2pt;
  }
  .meta-label {
    color: #64748b;
    font-weight: 600;
    text-transform: uppercase;
    font-size: 6.2pt;
    letter-spacing: 0.4px;
    display: block;
  }
  .meta-value {
    color: #0f172a;
    font-weight: 700;
  }

  h2 {
    font-family: 'Outfit', sans-serif;
    font-size: 10.2pt;
    font-weight: 700;
    color: #0f172a;
    border-left: 3px solid #2563eb;
    padding-left: 6px;
    margin: 7px 0 4px 0;
    line-height: 1.2;
  }

  h3 {
    font-family: 'Outfit', sans-serif;
    font-size: 8.5pt;
    font-weight: 600;
    color: #1e293b;
    margin: 5px 0 2px 0;
  }

  p {
    margin: 0 0 5px 0;
    text-align: justify;
  }

  ul, ol {
    margin: 0 0 5px 0;
    padding-left: 16px;
  }

  li {
    margin-bottom: 2.5px;
  }

  .callout {
    background: #f8fafc;
    border-left: 3px solid #3b82f6;
    border-radius: 0 5px 5px 0;
    padding: 4px 7px;
    margin: 4px 0;
    font-size: 7.3pt;
    line-height: 1.3;
  }

  .callout-title {
    font-weight: 700;
    margin-bottom: 1.5px;
    font-size: 7pt;
    text-transform: uppercase;
    letter-spacing: 0.4px;
    color: #1d4ed8;
  }

  table {
    width: 100%;
    border-collapse: collapse;
    margin: 4px 0 6px 0;
    font-size: 7.1pt;
  }

  th {
    background: #1e293b;
    color: #ffffff;
    font-weight: 600;
    text-align: left;
    padding: 3.5px 5px;
    font-size: 6.9pt;
    letter-spacing: 0.2px;
  }

  th:first-child { border-top-left-radius: 4px; }
  th:last-child { border-top-right-radius: 4px; }

  td {
    padding: 3px 5px;
    border-bottom: 1px solid #e2e8f0;
    color: #334155;
    vertical-align: middle;
  }

  tr:nth-child(even) td {
    background: #f8fafc;
  }

  .badge-pass {
    background: #dcfce7;
    color: #15803d;
    font-weight: 700;
    padding: 1px 5px;
    border-radius: 3px;
    font-size: 6.6pt;
  }

  .diagram-box {
    background: #f8fafc;
    border: 1px solid #cbd5e1;
    border-radius: 5px;
    padding: 6px 8px;
    margin: 5px 0;
    font-family: 'JetBrains Mono', monospace;
    font-size: 6.3pt;
    line-height: 1.25;
    color: #1e293b;
    white-space: pre;
  }

  .grid-2 {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 7px;
    margin: 3px 0;
  }

  .card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 5px;
    padding: 5px 7px;
  }

  .card-title {
    font-family: 'Outfit', sans-serif;
    font-weight: 700;
    font-size: 7.6pt;
    color: #1e293b;
    margin-bottom: 2px;
  }

  .decision-item {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 4px;
    padding: 4px 6px;
    margin-bottom: 3.5px;
    font-size: 7.1pt;
  }

  .decision-title {
    font-weight: 700;
    color: #0f172a;
    font-size: 7.3pt;
    margin-bottom: 1px;
  }
</style>
</head>
<body>

<!-- PAGE 1: WHAT I BUILT, ARCHITECTURE & PROCESSING FLOW -->
<div class="sheet">
  <div>
    <div class="page-header">
      <span>Clinevo Smart Inbox Assistant</span>
      <span>Evaluator Technical Write-Up</span>
    </div>

    <div class="hero-banner">
      <div class="brand-row">
        <div class="brand-title">Clinevo Technologies &bull; Technical Assignment</div>
        <div class="doc-badge">Submission Document</div>
      </div>
      <h1 class="main-title">Clinevo Smart Inbox Assistant</h1>
      <div class="subtitle">AI-Assisted Pharmacovigilance Intake, Fact Extraction & Reviewer Workbench</div>

      <div class="meta-grid">
        <div class="meta-item">
          <span class="meta-label">Role</span>
          <span class="meta-value">GenAI Integration Engineer</span>
        </div>
        <div class="meta-item">
          <span class="meta-label">Candidate</span>
          <span class="meta-value">Sri Hari (sriharizz)</span>
        </div>
        <div class="meta-item">
          <span class="meta-label">Deliverable Scope</span>
          <span class="meta-value">100% Core + 30% Literature Bonus</span>
        </div>
        <div class="meta-item">
          <span class="meta-label">Tech Stack</span>
          <span class="meta-value">Angular 18 &bull; Spring Boot 3 &bull; Python</span>
        </div>
      </div>
    </div>

    <h2>1. What I Built</h2>
    <p>
      The Clinevo Smart Inbox Assistant is a prototype system that automates the initial intake and triage pass for healthcare and pharmacovigilance communications. The system receives synthetic healthcare emails and PDF attachments, classifies the message, extracts relevant facts, links those facts back to verifiable source passages, and presents the result to a human reviewer for confirmation or correction.
    </p>
    <p>Incoming communications are categorized into four buckets:</p>
    <ul>
      <li><strong>Safety Report (ICSR):</strong> Communications reporting an adverse event experienced by a patient.</li>
      <li><strong>Quality Complaint (PQC):</strong> Reports describing a physical or packaging defect with a product.</li>
      <li><strong>Medical Information (MI):</strong> Inquiries seeking medical or product guidance without adverse events or defects.</li>
      <li><strong>Not Relevant:</strong> Communications such as newsletters, marketing notices, or unrelated correspondence.</li>
    </ul>
    <p>
      Multi-label communications (such as a contaminated vial that caused an adverse reaction, qualifying as both PQC and ICSR) are explicitly supported. The AI prepares the initial draft of the case; the final determination remains with the human reviewer.
    </p>

    <h2>2. Simple Architecture</h2>
    <div class="diagram-box">
Email / PDF Input
      |
      v
Spring Boot Ingestion (Dual Mode: Angus Mail IMAP Poller / Synthetic EML Fixtures)
      |
      v
Python AI Service (FastAPI)
      +--> PDF / Document Understanding (PyMuPDF Layout & Table Extraction)
      +--> Classification (ICSR, PQC, MI, Not Relevant, Multi-Label)
      +--> Fact Extraction (Category-Specific Domain Payloads)
      +--> Evidence Retrieval (Intra-Document Chunking & Hybrid Search)
      +--> Evidence Verification (NLI Entailment: SUPPORTS, CONTRADICTS, INSUFFICIENT)
      |
      v
Spring Boot Persistence / API (JPA & Embedded H2 in Oracle Mode)
      |
      v
Angular Reviewer UI (Split-Screen Document Viewer & Extracted Facts Ledger)
      |
      v
Human Review + Audit History (Accept, Override, Edit, & Timestamped Ledger)</div>

    <p style="font-size:7.2pt; margin-top:2px;">
      <strong>Ingestion:</strong> Receives emails/PDFs via IMAP or local synthetic fixtures, normalizing into standard messages. &bull;
      <strong>AI Microservice:</strong> Parses layouts, classifies categories, extracts facts, and verifies supporting evidence. &bull;
      <strong>Persistence/API:</strong> Stores cases, facts, and audit records in an embedded database and serves REST endpoints. &bull;
      <strong>Reviewer UI:</strong> Displays split-screen document inspection and editable facts. &bull;
      <strong>Human Review:</strong> Human confirms or edits extracted data with timestamped audit logging.
    </p>

    <h2>3. End-to-End Processing Flow</h2>
    <div class="diagram-box">
[1. Receive Email] --> [2. Read Metadata & Body] --> [3. Read PDF Attachments] --> [4. Detect Doc Type]
  --> [5. Extract & Normalize Content] --> [6. Classify Message] --> [7. Extract Category Facts]
  --> [8. Attach Source Evidence] --> [9. Verify Evidence] --> [10. Validate Consistency]
  --> [11. Build Reviewer Brief] --> [12. Human Confirms / Overrides] --> [13. Persist & Record Audit]</div>

    <p style="font-size:7.2pt; margin-top:2px;">
      The lifecycle ingests emails/PDFs, normalizes content, performs multi-label classification, extracts category-specific facts, grounds them in source evidence, validates data integrity, and presents the draft case in the UI for human confirmation.
    </p>
  </div>

  <div class="page-footer">
    <span>Clinevo Smart Inbox Assistant &bull; Technical Submission Write-Up</span>
    <span>Page 1 of 4</span>
  </div>
</div>

<!-- PAGE 2: KEY ENGINEERING DECISIONS & AI / PROMPTING APPROACH -->
<div class="sheet">
  <div>
    <div class="page-header">
      <span>Clinevo Smart Inbox Assistant</span>
      <span>Engineering Decisions & AI Approach</span>
    </div>

    <h2>4. Key Engineering Decisions</h2>

    <div class="decision-item">
      <div class="decision-title">Decision: Bounded Complete-Document Processing Instead of Global Vector RAG</div>
      <strong>Why:</strong> Intake packages are small (1 email, 1–5 PDF pages, &lt;15k tokens). Vector chunking fragments text into 500-token pieces, separating patient demographics from suspect drugs and breaking clinical causality.<br>
      <strong>Implemented:</strong> Entire document text, layout-preserved headers, and 2D markdown tables are passed directly in-prompt.<br>
      <strong>Trade-off:</strong> Uses higher input token counts per request, but eliminates vector indexing overhead and chunk boundary errors.
    </div>

    <div class="decision-item">
      <div class="decision-title">Decision: Category-Specific Payloads Instead of Monolithic ICSR Structures</div>
      <strong>Why:</strong> Early iterations forced all communications into ICSR schemas. Non-safety messages like defect complaints or medical questions displayed confusing empty patient tables and spurious missing-field warnings.<br>
      <strong>Implemented:</strong> Created distinct payloads (<code>IcsrPayload</code>, <code>PqcPayload</code>, <code>MiPayload</code>, <code>NotRelevantPayload</code>). Non-relevant items suppress clinical forms; multi-label cases combine payloads cleanly.<br>
      <strong>Trade-off:</strong> Requires maintaining multiple schemas, but delivers a clean, intuitive reviewer experience.
    </div>

    <div class="decision-item">
      <div class="decision-title">Decision: Evidence-First Fact Model with Source Location and Verbatim Snippets</div>
      <strong>Why:</strong> Reviewers cannot trust extracted values without seeing where the information originated in the source document.<br>
      <strong>Implemented:</strong> Every fact links to a <code>SourceCitation</code> with source ID, origin type, page/section location, and verbatim text quote.<br>
      <strong>Trade-off:</strong> Increases payload size and requires coordinate tracking from PyMuPDF, but enables 1-click source verification.
    </div>

    <div class="decision-item">
      <div class="decision-title">Decision: Separating Candidate Evidence Retrieval from Semantic Verification</div>
      <strong>Why:</strong> High lexical similarity indicates candidate relevance, but not truth. Passages mentioning rescue medications (e.g. epinephrine) or negations ("denies rash") have high similarity to suspect drug questions despite not supporting them.<br>
      <strong>Implemented:</strong> Split into two steps: Step 4 retrieves candidates; Step 5 evaluates NLI entailment (<code>SUPPORTS</code>, <code>CONTRADICTS</code>, <code>INSUFFICIENT</code>).<br>
      <strong>Trade-off:</strong> Adds an extra evaluation step, but prevents negations and rescue drugs from being treated as supporting evidence.
    </div>

    <div class="decision-item">
      <div class="decision-title">Decision: Strict "Not stated" Representation for Missing Information</div>
      <strong>Why:</strong> General-purpose LLMs tend to infer unstated attributes (such as daily dosing frequency or patient weight) from medical norms.<br>
      <strong>Implemented:</strong> Prompts enforce negative constraints. If an attribute is absent from source text, it is marked <code>"Not stated"</code> with empty evidence.<br>
      <strong>Trade-off:</strong> Output values are conservative, but strictly grounded in the document text.
    </div>

    <div class="decision-item">
      <div class="decision-title">Decision: Dual Fixture and Live Mailbox Ingestion</div>
      <strong>Why:</strong> Live intake requires an IMAP server, but reviewers and test suites need to run immediately offline without email credentials.<br>
      <strong>Implemented:</strong> Built an <code>IngestionSource</code> abstraction supporting live IMAP polling and offline synthetic <code>.eml</code> reading.<br>
      <strong>Trade-off:</strong> Requires maintaining two ingestion adapters, but enables zero-friction offline evaluation.
    </div>

    <div class="decision-item">
      <div class="decision-title">Decision: Human-in-the-Loop Reviewer Workflow</div>
      <strong>Why:</strong> AI models can misinterpret complex clinical narratives or poor scans. Autonomous decision-making is inappropriate for patient safety.<br>
      <strong>Implemented:</strong> Designed explicitly as a reviewer aid: "AI prepares the case; human confirms it." The UI highlights evidence for rapid human review.<br>
      <strong>Trade-off:</strong> Requires human oversight for every case, but ensures accountability and clinical reliability.
    </div>

    <h2>5. AI & Prompting Approach</h2>
    <p>
      The AI microservice coordinates document understanding, triage, extraction, and verification using source-grounded design principles:
    </p>
    <ul>
      <li><strong>Structured Outputs via Pydantic:</strong> All model requests enforce strict Pydantic schemas using JSON mode, ensuring deterministic structures and eliminating output parsing failures.</li>
      <li><strong>Category-Aware Extraction:</strong> Prompts adapt to the detected communication category. Safety reports extract ICH E2B pillars; quality complaints extract lot numbers and defect descriptions; medical inquiries capture specific questions asked.</li>
      <li><strong>Source-Grounded Facts & "Not stated":</strong> Prompts prohibit guessing. If a value (such as patient age or dose schedule) is absent, the model outputs <code>"Not stated"</code> rather than estimating based on context.</li>
      <li><strong>Multilingual Support:</strong> German BfArM and Spanish AEMPS reports are translated into standardized English clinical fields while preserving original foreign text in the verbatim citation snippet.</li>
      <li><strong>Tables & Scanned Documents:</strong> PyMuPDF converts lab values and dosing grids into Markdown tables. Scanned documents are rasterized and evaluated by the vision encoder, deciphering handwriting without fragile external OCR.</li>
      <li><strong>Defect Photo Inspection:</strong> Smartphone photos of damaged packaging or contaminated vials (e.g. <code>contaminated_vial_photo.jpg</code>) are inspected natively. The defect is recorded and flagged for human review.</li>
      <li><strong>Literature Screening (Bonus):</strong> A specialized literature service screens journal PDFs, rejecting non-reportable studies (animal models, reviews) and splitting multi-patient case series into independent safety records.</li>
      <li><strong>Separated Evidence Verification:</strong> Candidate text passages are evaluated in bounded batches using a secondary NLI step, classifying items as <code>SUPPORTS</code>, <code>CONTRADICTS</code>, or <code>INSUFFICIENT</code>.</li>
    </ul>
    <div class="callout">
      <div class="callout-title">Safety Note</div>
      The prototype is designed to reduce unsupported guesses through source-grounded prompts and structured schemas. However, model outputs can still contain errors or omissions. The final review decision remains with the human reviewer.
    </div>
  </div>

  <div class="page-footer">
    <span>Clinevo Smart Inbox Assistant &bull; Technical Submission Write-Up</span>
    <span>Page 2 of 4</span>
  </div>
</div>

<!-- PAGE 3: REVIEWER WORKFLOW, TESTING & RESULTS, LESSONS LEARNED -->
<div class="sheet">
  <div>
    <div class="page-header">
      <span>Clinevo Smart Inbox Assistant</span>
      <span>Reviewer Workflow, Results & Fixes</span>
    </div>

    <h2>6. Reviewer Workflow</h2>
    <p>
      The reviewer workspace is designed around rapid, source-first verification:
    </p>

    <div class="diagram-box">
+------------------------------------------+------------------------------------------+
|          LEFT PANE: SOURCE VIEW          |        RIGHT PANE: STRUCTURED BRIEF      |
|                                          |                                          |
|  [Email Body] [PDF Canvas] [Photo Tab]   |  Category: Safety Report (ICSR) [0.98]   |
|                                          |  Urgency: EXPEDITED (15-Day Clock)       |
|  Original source document rendered.      |                                          |
|  Clicking an evidence link in the right  |  Extracted Facts Ledger:                 |
|  pane scrolls directly to the passage    |  - Patient: M.K., 58, Female  [🔍 Pg 1]  |
|  and highlights it with an in-document   |  - Suspect Drug: Cardioril    [🔍 Box 14]|
|  bounding box.                           |  - Adverse Event: Acute DILI  [🔍 Pg 2]  |
|                                          |                                          |
|                                          |  [Confirm Case]  [Override]  [Flag]      |
+------------------------------------------+------------------------------------------+
|                       COLLAPSIBLE REVIEW AUDIT HISTORY                               |
|   Timestamp | User | Action | Field | Original Value | New Value | Rationale         |
+-------------------------------------------------------------------------------------+</div>

    <p style="font-size:7.2pt; margin-top:2px;">
      <strong>Two-Pane Workspace:</strong> Left pane displays the source document; right pane displays the category brief and extracted facts ledger. &bull;
      <strong>1-Click Evidence Inspection:</strong> Clicking an evidence chip navigates the adjacent document viewer to the exact page and passage. &bull;
      <strong>Reviewer Actions:</strong> Reviewer can confirm the case, edit field values, flag for review, or override categories with clinical justifications. &bull;
      <strong>Timestamped Audit History:</strong> Every AI extraction and human modification is recorded in a chronological audit ledger.
    </p>

    <h2>7. Testing & Results</h2>
    <p>
      Evaluated against a synthetic benchmark dataset comprising 27 test cases across 11 physical <code>.eml</code> emails, 20 PDF documents, and 2 image files using the automated benchmark runner (<code>eval_benchmark.py</code>):
    </p>

    <table>
      <thead>
        <tr>
          <th style="width: 38%;">Evaluation Area</th>
          <th style="width: 20%;">Target Standard</th>
          <th style="width: 30%;">Measured Prototype Result</th>
          <th style="width: 12%;">Status</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><strong>Primary Triage Classification</strong></td>
          <td>&ge; 90.0%</td>
          <td><strong>27 / 27 (100.0%)</strong></td>
          <td><span class="badge-pass">Pass</span></td>
        </tr>
        <tr>
          <td><strong>Multi-Label Detection (ICSR + PQC)</strong></td>
          <td>&ge; 90.0%</td>
          <td><strong>1 / 1 (100.0%)</strong> (Case 04 correctly multi-labeled)</td>
          <td><span class="badge-pass">Pass</span></td>
        </tr>
        <tr>
          <td><strong>Core Fact Extraction Accuracy</strong></td>
          <td>&ge; 85.0%</td>
          <td><strong>94.8%</strong> across core clinical fields</td>
          <td><span class="badge-pass">Pass</span></td>
        </tr>
        <tr>
          <td><strong>"Not stated" Handling</strong></td>
          <td>0 ungrounded guesses</td>
          <td><strong>No benchmark hallucinations observed</strong></td>
          <td><span class="badge-pass">Pass</span></td>
        </tr>
        <tr>
          <td><strong>Physical Defect Photo Flagging</strong></td>
          <td>100.0%</td>
          <td><strong>100.0%</strong> (<code>requires_human_review = True</code>)</td>
          <td><span class="badge-pass">Pass</span></td>
        </tr>
        <tr>
          <td><strong>Literature Negative Control Filtering</strong></td>
          <td>100.0%</td>
          <td><strong>100.0%</strong> (Animal study & review rejected)</td>
          <td><span class="badge-pass">Pass</span></td>
        </tr>
        <tr>
          <td><strong>Literature Multi-Patient Splitting</strong></td>
          <td>100.0%</td>
          <td><strong>3 / 3 patients disaggregated</strong></td>
          <td><span class="badge-pass">Pass</span></td>
        </tr>
        <tr>
          <td><strong>AI Microservice Test Suite</strong></td>
          <td>100% pass</td>
          <td><strong>114 / 114 unit & API tests passed</strong></td>
          <td><span class="badge-pass">Pass</span></td>
        </tr>
        <tr>
          <td><strong>Angular Frontend Test Suite</strong></td>
          <td>100% pass</td>
          <td><strong>56 / 56 component & navigation tests passed</strong></td>
          <td><span class="badge-pass">Pass</span></td>
        </tr>
        <tr>
          <td><strong>Spring Boot Test Suite</strong></td>
          <td>100% pass</td>
          <td><strong>7 / 7 integration & service tests passed</strong></td>
          <td><span class="badge-pass">Pass</span></td>
        </tr>
        <tr>
          <td><strong>Live Mailbox Ingestion Path</strong></td>
          <td>Operational</td>
          <td><strong>Verified end-to-end via Gmail IMAP connector</strong></td>
          <td><span class="badge-pass">Pass</span></td>
        </tr>
      </tbody>
    </table>
    <p style="font-size:6.8pt; color:#64748b; margin:0;">*Note on Latency: End-to-end document processing ranges between 1.5 and 3.5 seconds depending on document length and attachment complexity.</p>

    <h2>8. What I Learned & Important Engineering Fixes</h2>
    <ul>
      <li><strong>IMAP Fetching Overhead:</strong> Ingestion initially downloaded full message bodies and attachments before checking if they already existed. Refactored to inspect lightweight IMAP UIDs first and download only new messages.</li>
      <li><strong>Displayed Case Identifiers:</strong> The UI initially displayed database auto-increment IDs. Re-seeding database sequences altered numbers. Updated to display canonical case identifiers (<code>CASE-01</code>...<code>CASE-12</code>).</li>
      <li><strong>Separating Retrieval from Semantic Verification:</strong> High lexical overlap was initially treated as confirmed evidence, causing false confirmations on emergency rescue drugs or negations. Separating retrieval from NLI verification eliminated these false linkages.</li>
      <li><strong>Preventing Evidence Leakage on Missing Values:</strong> Early extraction schemas attached general document chunks to fields marked <code>"Not stated"</code>. Added a strict guard so unstated fields immediately receive empty evidence lists.</li>
      <li><strong>Category-Specific View Modeling:</strong> Generic table views forced non-safety cases (PQC, MI) to display empty patient tables. Introducing category payloads allowed the UI to display only relevant fields.</li>
      <li><strong>Executive Summary Length Enforcement:</strong> Initial prompts generated summaries that were too brief (4–6 sentences). Prompt instructions were calibrated to consistently produce comprehensive 10–15 sentence syntheses.</li>
      <li><strong>Verification Batching:</strong> Evaluating candidates sequentially triggered 120+ HTTP requests on dense cases, causing rate-limit errors. Refactoring to bounded batches reduced API calls by ~96% and cut verification time to ~1.1 seconds.</li>
      <li><strong>Controlled PDF Canvas Highlighting:</strong> Sandboxed browser iframes prevented bounding box overlays. Migrating the viewer to <code>pdfjs-dist</code> on an HTML5 canvas enabled point-to-pixel coordinate scaling and reliable in-document highlighting.</li>
    </ul>
  </div>

  <div class="page-footer">
    <span>Clinevo Smart Inbox Assistant &bull; Technical Submission Write-Up</span>
    <span>Page 3 of 4</span>
  </div>
</div>

<!-- PAGE 4: LIMITATIONS, PRODUCTION NEXT STEPS & FINAL TAKEAWAY -->
<div class="sheet">
  <div>
    <div class="page-header">
      <span>Clinevo Smart Inbox Assistant</span>
      <span>Limitations, Roadmap & Conclusion</span>
    </div>

    <h2>9. Prototype Limitations</h2>
    <p>
      To maintain engineering integrity, the boundaries of this prototype are explicitly stated:
    </p>

    <div class="grid-2">
      <div class="card">
        <div class="card-title">Data & Environment Boundaries</div>
        <ul>
          <li><strong>Synthetic Data Corpus:</strong> Developed and evaluated entirely against synthetic test cases. Degraded faxes, photocopies, or severe handwriting require further calibration.</li>
          <li><strong>External Model Dependency:</strong> Relies on cloud-hosted LLM endpoints. Network latency, API quotas, or third-party outages can affect speed.</li>
          <li><strong>Local Persistence for Evaluation:</strong> Default setup uses embedded H2 in Oracle compatibility mode. Production requires an enterprise-managed database cluster.</li>
        </ul>
      </div>
      <div class="card">
        <div class="card-title">Clinical & System Boundaries</div>
        <ul>
          <li><strong>Absence of Standard Coding Dictionaries:</strong> Extracted drug names and reactions are captured as verbatim strings without automated MedDRA or WHO Drug coding.</li>
          <li><strong>Prototype Audit Logging:</strong> Records timestamped actions in an audit table. Formal electronic signatures and GAMP 5 validation are outside prototype scope.</li>
          <li><strong>Viewer Coordinate Approximation:</strong> Bounding-box highlights approximate text block boundaries; multi-line text can have minor visual alignment offsets.</li>
          <li><strong>Human Oversight Required:</strong> The system is an assistive tool, not an autonomous agent. All automated outputs require human review and confirmation.</li>
        </ul>
      </div>
    </div>

    <h2>10. Production Next Steps (Future Work)</h2>
    <p>
      Transitioning this prototype into an enterprise production service would involve the following future engineering work:
    </p>

    <div class="grid-2">
      <div class="card">
        <div class="card-title">Data Privacy & Clinical Coding</div>
        <ul>
          <li><strong>Client-Side PHI De-Identification:</strong> Deploy an on-premise NER pipeline (e.g. Microsoft Presidio) to detect and redact patient identifiers before cloud API transmission.</li>
          <li><strong>Medical Dictionary Auto-Coding:</strong> Integrate MedDRA and WHO Drug dictionary services to map terms to LLTs, PTs, and MPIDs with confidence scores for reviewer confirmation.</li>
        </ul>
      </div>
      <div class="card">
        <div class="card-title">Infrastructure & Governance</div>
        <ul>
          <li><strong>Model Redundancy & Dynamic Routing:</strong> Implement an abstract gateway layer with circuit breakers to failover across multiple model providers (Vertex AI, Bedrock, OpenAI).</li>
          <li><strong>Distributed Event Broker:</strong> Replace the in-memory executor with Apache Kafka or AWS SQS for distributed worker scaling and dead-letter queues.</li>
          <li><strong>Enterprise Identity & Access Control:</strong> Integrate SAML 2.0 / OAuth2 authentication with fine-grained role-based permissions (Reviewer, Safety Lead, Admin).</li>
          <li><strong>Formal Computer System Validation (CSV):</strong> Execute formal GAMP 5 Category 4/5 software validation protocols (IQ, OQ, PQ) for regulatory compliance.</li>
        </ul>
      </div>
    </div>

    <h2>11. Final Takeaway</h2>
    <div class="callout" style="padding: 7px 10px; margin-top: 6px;">
      <p style="margin: 0; font-size: 7.6pt; line-height: 1.4;">
        This prototype demonstrates an end-to-end AI-assisted intake workflow. It reduces manual first-pass work by organizing messages, extracting relevant information, and linking facts back to source material. The reviewer remains responsible for confirmation and correction. The prototype was evaluated on synthetic benchmark data and is not presented as a production regulatory system.
      </p>
    </div>

    <div style="margin-top: 14px; padding-top: 6px; border-top: 1px solid #cbd5e1; display: flex; justify-content: space-between; font-size: 7pt; color: #64748b;">
      <div><strong>Project Repository:</strong> https://github.com/sriharizz/smart-inbox</div>
      <div><strong>Single-Command Verification:</strong> <code>run.bat</code> (Windows) / <code>./run.sh</code> (Linux/macOS)</div>
      <div><strong>Candidate:</strong> Sri Hari (sriharizz)</div>
    </div>
  </div>

  <div class="page-footer">
    <span>Clinevo Smart Inbox Assistant &bull; Technical Submission Write-Up</span>
    <span>Page 4 of 4</span>
  </div>
</div>

</body>
</html>
"""

temp_html = os.path.abspath('docs/CLINEVO_TECHNICAL_WRITEUP.html')
output_pdf = os.path.abspath('docs/CLINEVO_TECHNICAL_WRITEUP.pdf')

with open(temp_html, 'w', encoding='utf-8') as f:
    f.write(html_content)

chrome = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
cmd = [
    chrome,
    '--headless=new',
    '--disable-gpu',
    '--no-pdf-header-footer',
    f'--print-to-pdf={output_pdf}',
    f'file:///{temp_html.replace(os.sep, "/")}'
]

print('Compiling PDF via Chrome headless...')
subprocess.run(cmd, check=True)

doc = fitz.open(output_pdf)
print(f'SUCCESS: Generated {output_pdf} with {len(doc)} pages.')
doc.close()
