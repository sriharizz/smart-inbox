import subprocess
import os
import fitz

html_content = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Clinevo Smart Inbox Assistant — Technical Submission Write-Up</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Outfit:wght@600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

  @page {
    size: A4;
    margin: 10mm 14mm 10mm 14mm;
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
    font-size: 8.1pt;
    line-height: 1.36;
    margin: 0;
    padding: 0;
  }

  .sheet {
    page-break-after: always;
    break-after: page;
    height: 275mm;
    max-height: 275mm;
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
    padding-bottom: 3px;
    margin-bottom: 6px;
    font-size: 7pt;
    font-weight: 600;
    color: #64748b;
  }

  .page-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-top: 1px solid #cbd5e1;
    padding-top: 3px;
    margin-top: 4px;
    font-size: 7pt;
    color: #94a3b8;
  }

  h1.main-title {
    font-family: 'Outfit', sans-serif;
    font-size: 16.5pt;
    font-weight: 800;
    color: #0f172a;
    line-height: 1.15;
    margin: 0 0 2px 0;
  }

  .sub-title {
    font-size: 9.2pt;
    font-weight: 600;
    color: #334155;
    margin: 0 0 2px 0;
  }

  .tagline {
    font-size: 7.8pt;
    color: #64748b;
    margin: 0 0 6px 0;
  }

  .meta-bar {
    display: grid;
    grid-template-columns: 1.1fr 1.6fr 1.8fr;
    gap: 10px;
    background: #f8fafc;
    border-top: 1px solid #e2e8f0;
    border-bottom: 1px solid #e2e8f0;
    padding: 5px 8px;
    margin-bottom: 8px;
  }

  .meta-col {
    font-size: 7.5pt;
  }
  .meta-label {
    color: #64748b;
    font-weight: 600;
    display: block;
    margin-bottom: 1px;
    font-size: 6.6pt;
    text-transform: uppercase;
    letter-spacing: 0.3px;
  }
  .meta-val {
    color: #0f172a;
    font-weight: 600;
  }

  h2 {
    font-family: 'Outfit', sans-serif;
    font-size: 10pt;
    font-weight: 700;
    color: #0f172a;
    margin: 7px 0 3px 0;
    line-height: 1.2;
  }

  p {
    margin: 0 0 5px 0;
    text-align: justify;
  }

  /* 4 Categories 2x2 Grid */
  .category-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 6px;
    margin: 5px 0;
  }

  .cat-card {
    border: 1px solid #cbd5e1;
    border-radius: 4px;
    overflow: hidden;
  }

  .cat-header {
    background: #0f2744;
    color: #ffffff;
    font-weight: 700;
    font-size: 7.6pt;
    padding: 3px 7px;
  }
  .cat-header.accent {
    background: #1e528a;
  }

  .cat-body {
    padding: 4px 7px;
    font-size: 7.3pt;
    background: #ffffff;
    color: #334155;
    min-height: 24px;
  }

  /* Clean Vertical Architecture Diagram */
  .arch-container {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 5px;
    padding: 8px 12px;
    margin: 5px 0;
  }

  .arch-box {
    display: flex;
    flex-direction: column;
    align-items: center;
    max-width: 380px;
    margin: 0 auto;
  }

  .arch-node {
    width: 100%;
    background: #f8fafc;
    border: 1.2px solid #64748b;
    border-radius: 4px;
    padding: 3.5px 8px;
    text-align: center;
    font-weight: 600;
    font-size: 7.4pt;
    color: #0f172a;
  }

  .arch-node.ai-service {
    background: #f0f7ff;
    border-color: #1e528a;
    padding: 4px 8px;
  }

  .ai-title {
    font-weight: 700;
    color: #1e528a;
    font-size: 7.6pt;
    margin-bottom: 2px;
    text-align: center;
  }

  .ai-bullets {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 2px 10px;
    font-size: 6.9pt;
    color: #334155;
    text-align: left;
    padding: 0 10px;
  }

  .arch-node.human-node {
    background: #0f2744;
    color: #ffffff;
    border-color: #0f2744;
    font-weight: 700;
  }

  .arch-arrow {
    color: #64748b;
    font-weight: 700;
    font-size: 8.5pt;
    line-height: 1;
    margin: 1.5px 0;
  }

  /* Processing Flow Diagram */
  .process-container {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 5px;
    padding: 6px 8px;
    margin: 5px 0;
  }

  .flow-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 4px;
  }

  .proc-node {
    background: #f8fafc;
    border: 1.2px solid #64748b;
    border-radius: 4px;
    padding: 5px 4px;
    text-align: center;
    font-weight: 600;
    font-size: 7.2pt;
    flex: 1;
    color: #0f172a;
  }

  .proc-node.audit-node {
    background: #0f2744;
    border-color: #0f2744;
    color: #ffffff;
  }

  .arrow-right {
    color: #64748b;
    font-weight: 700;
    font-size: 8.5pt;
    padding: 0 1px;
    user-select: none;
  }

  .flow-connector {
    text-align: right;
    padding-right: 36px;
    color: #64748b;
    font-size: 8pt;
    line-height: 1;
    margin: 1px 0;
  }

  /* Tables */
  table {
    width: 100%;
    border-collapse: collapse;
    margin: 3px 0 5px 0;
    font-size: 7.2pt;
  }

  th {
    background: #0f2744;
    color: #ffffff;
    font-weight: 700;
    text-align: left;
    padding: 3.5px 6px;
    font-size: 7.1pt;
    border-bottom: 1.5px solid #0f172a;
  }

  td {
    padding: 3.2px 6px;
    border-bottom: 1px solid #e2e8f0;
    color: #1e293b;
    vertical-align: middle;
  }

  tr:nth-child(even) td {
    background: #f8fafc;
  }

  .table-clean th {
    background: #0f2744;
    color: #ffffff;
  }

  /* Callouts & Highlights */
  .callout {
    background: #f0f7ff;
    border: 1px solid #bfdbfe;
    border-radius: 4px;
    padding: 4px 8px;
    margin: 4px 0;
    font-size: 7.1pt;
    color: #1e40af;
  }

  /* Reviewer Workflow */
  .workflow-container {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 8px;
    margin: 5px 0 4px 0;
  }

  .wf-card {
    flex: 1;
    border: 1px solid #cbd5e1;
    border-radius: 4px;
    overflow: hidden;
  }

  .wf-header {
    background: #0f2744;
    color: #ffffff;
    font-weight: 700;
    font-size: 7.3pt;
    padding: 3px 6px;
    text-align: center;
    letter-spacing: 0.3px;
  }

  .wf-body {
    padding: 5px 8px;
    background: #ffffff;
    font-size: 7.1pt;
    line-height: 1.4;
    text-align: center;
    color: #334155;
  }

  .wf-buttons {
    display: flex;
    justify-content: center;
    gap: 10px;
    margin: 4px 0 5px 0;
  }

  .wf-btn {
    border: 1px solid #cbd5e1;
    background: #f8fafc;
    border-radius: 3px;
    padding: 2px 14px;
    font-weight: 600;
    font-size: 7.1pt;
    color: #0f172a;
  }

  .two-col-list {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    margin: 3px 0 5px 0;
  }

  .two-col-list ul {
    margin: 0;
    padding-left: 14px;
  }

  .two-col-list li {
    margin-bottom: 2px;
    font-size: 7.2pt;
  }

  .quote-box {
    background: #f1f5f9;
    border-radius: 4px;
    padding: 6px 9px;
    margin: 5px 0 8px 0;
    font-size: 7.2pt;
    font-style: italic;
    color: #334155;
    line-height: 1.38;
  }

  .footer-links {
    display: flex;
    justify-content: space-between;
    font-size: 7.1pt;
    font-weight: 600;
    color: #0f172a;
    padding-top: 3px;
  }
</style>
</head>
<body>

<!-- ================= PAGE 1 ================= -->
<div class="sheet">
  <div>
    <div class="page-header">
      <span>Clinevo Smart Inbox Assistant &bull; Technical Submission Write-Up</span>
      <span>Page 1</span>
    </div>

    <h1 class="main-title">Clinevo Smart Inbox Assistant</h1>
    <div class="sub-title">Technical Submission Write-Up</div>
    <div class="tagline">AI-Assisted Healthcare Email/PDF Intake, Classification &amp; Human Review</div>

    <div class="meta-bar">
      <div class="meta-col">
        <span class="meta-label">Candidate</span>
        <span class="meta-val">Sri Hari</span>
      </div>
      <div class="meta-col">
        <span class="meta-label">Deliverable Scope</span>
        <span class="meta-val">Core Intake (100%) + Literature Screening Bonus</span>
      </div>
      <div class="meta-col">
        <span class="meta-label">Tech Stack</span>
        <span class="meta-val">Angular 18 &bull; Spring Boot 3 &bull; Python / FastAPI</span>
      </div>
    </div>

    <h2>1. What I Built</h2>
    <p>
      The Clinevo Smart Inbox Assistant is a prototype that receives synthetic healthcare emails and PDF attachments, classifies each communication, extracts relevant facts, links those facts back to verifiable source passages, and presents the result to a human reviewer for confirmation or correction.
    </p>

    <div class="category-grid">
      <div class="cat-card">
        <div class="cat-header">Safety Report (ICSR)</div>
        <div class="cat-body">Adverse event experienced by a patient.</div>
      </div>
      <div class="cat-card">
        <div class="cat-header accent">Quality Complaint (PQC)</div>
        <div class="cat-body">Physical or packaging defect with a product.</div>
      </div>
      <div class="cat-card">
        <div class="cat-header accent">Medical Information (MI)</div>
        <div class="cat-body">Guidance inquiry with no adverse event or defect.</div>
      </div>
      <div class="cat-card">
        <div class="cat-header">Not Relevant</div>
        <div class="cat-body">Newsletters, marketing, or unrelated correspondence.</div>
      </div>
    </div>

    <p style="margin-top: 3px; margin-bottom: 6px;">
      Multi-label cases are explicitly supported &mdash; for example, a contaminated vial that also caused an adverse reaction is classified as both PQC and ICSR.
    </p>

    <h2>2. Architecture</h2>
    <div class="arch-container">
      <div class="arch-box">
        <div class="arch-node">Email / PDF</div>
        <div class="arch-arrow">&darr;</div>
        <div class="arch-node">Spring Boot Ingestion</div>
        <div class="arch-arrow">&darr;</div>
        <div class="arch-node ai-service">
          <div class="ai-title">Python AI Service</div>
          <div class="ai-bullets">
            <span>&bull; Document Understanding</span>
            <span>&bull; Classification</span>
            <span>&bull; Fact Extraction</span>
            <span>&bull; Evidence Verification</span>
          </div>
        </div>
        <div class="arch-arrow">&darr;</div>
        <div class="arch-node">Spring Boot API / Persistence</div>
        <div class="arch-arrow">&darr;</div>
        <div class="arch-node">Angular Reviewer UI</div>
        <div class="arch-arrow">&darr;</div>
        <div class="arch-node human-node">Human Reviewer</div>
      </div>
    </div>

    <h2>3. Processing Flow</h2>
    <div class="process-container">
      <div class="flow-row">
        <div class="proc-node">Receive</div>
        <div class="arrow-right">&rarr;</div>
        <div class="proc-node">Understand</div>
        <div class="arrow-right">&rarr;</div>
        <div class="proc-node">Classify</div>
        <div class="arrow-right">&rarr;</div>
        <div class="proc-node">Extract</div>
      </div>
      <div class="flow-connector">&darr;</div>
      <div class="flow-row">
        <div class="proc-node">Ground with Evidence</div>
        <div class="arrow-right">&rarr;</div>
        <div class="proc-node">Verify</div>
        <div class="arrow-right">&rarr;</div>
        <div class="proc-node">Human Review</div>
        <div class="arrow-right">&rarr;</div>
        <div class="proc-node audit-node">Audit</div>
      </div>
    </div>
  </div>

  <div class="page-footer">
    <span>Clinevo Smart Inbox Assistant &bull; Technical Submission Write-Up</span>
    <span>Page 1</span>
  </div>
</div>

<!-- ================= PAGE 2 ================= -->
<div class="sheet">
  <div>
    <div class="page-header">
      <span>Clinevo Smart Inbox Assistant &bull; Technical Submission Write-Up</span>
      <span>Page 2</span>
    </div>

    <h2>4. Key Engineering Decisions</h2>
    <table class="table-clean">
      <thead>
        <tr>
          <th style="width: 32%;">Decision</th>
          <th style="width: 34%;">Why</th>
          <th style="width: 34%;">Result</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><strong>Bounded document processing instead of global vector RAG</strong></td>
          <td>Intake packages are small; chunking would separate patient details from suspect drugs.</td>
          <td>Entire document is passed in-prompt with layout preserved; avoids document fragmentation caused by arbitrary chunk boundaries.</td>
        </tr>
        <tr>
          <td><strong>Category-specific payloads</strong></td>
          <td>Forcing all messages into an ICSR schema produced empty tables and false warnings.</td>
          <td>Distinct payloads per category give a clean, relevant reviewer view and reduce schema confusion.</td>
        </tr>
        <tr>
          <td><strong>Evidence-linked fact model</strong></td>
          <td>Reviewers need to see where an extracted value came from before trusting it.</td>
          <td>Extracted facts include source citations where available, providing location and verbatim snippet.</td>
        </tr>
        <tr>
          <td><strong>Separate retrieval from semantic verification</strong></td>
          <td>High lexical similarity does not guarantee a passage actually supports a fact.</td>
          <td>Retrieval and NLI-based verification are split into two steps; reduced false evidence linkages observed in earlier iterations.</td>
        </tr>
        <tr>
          <td><strong>&ldquo;Not stated&rdquo; for missing information</strong></td>
          <td>General-purpose models tend to infer unstated clinical details.</td>
          <td>Prompts enforce negative constraints; missing values are marked &ldquo;Not stated&rdquo; instead of guessing.</td>
        </tr>
        <tr>
          <td><strong>Fixture + live mailbox ingestion</strong></td>
          <td>Reviewers and tests need to run offline without live email credentials.</td>
          <td>An ingestion abstraction supports both live IMAP polling and offline fixtures.</td>
        </tr>
        <tr>
          <td><strong>Human-in-the-loop review</strong></td>
          <td>Autonomous decisions are inappropriate for patient-safety-relevant content.</td>
          <td>Human review remains required because model outputs can contain errors or omissions. The AI prepares a draft case; the human reviewer confirms or overrides it.</td>
        </tr>
      </tbody>
    </table>

    <h2>5. AI / Prompting Approach</h2>
    <div class="two-col-list">
      <ul>
        <li><strong>Structured outputs:</strong> Enforced via structured schemas to reduce output parsing issues.</li>
        <li><strong>Category-aware extraction:</strong> Tailored to the detected communication type (ICSR, PQC, or MI).</li>
        <li><strong>Source-grounded facts:</strong> Extracted facts include source citations where available.</li>
        <li><strong>&ldquo;Not stated&rdquo; for missing info:</strong> Negative constraints avoid guessing when data is absent.</li>
      </ul>
      <ul>
        <li><strong>Multilingual handling:</strong> Handles non-English communications (e.g. German, Spanish).</li>
        <li><strong>Tables / scanned documents:</strong> Layout-aware parsing and vision models handle complex documents.</li>
        <li><strong>Separate evidence verification:</strong> Two-stage verification checks passage support (SUPPORTS / CONTRADICTS).</li>
        <li><strong>Literature screening bonus:</strong> Screens journal PDFs, rejecting negative controls and splitting multi-patient cases.</li>
      </ul>
    </div>

    <div class="callout">
      <strong>Safety note:</strong> Model outputs can contain errors or omissions. The prototype is designed as a reviewer aid; the final decision remains with the human reviewer.
    </div>

    <h2>6. Reviewer Workflow</h2>
    <div class="workflow-container">
      <div class="wf-card">
        <div class="wf-header">SOURCE</div>
        <div class="wf-body">
          Email / PDF / Image
        </div>
      </div>
      <div class="arrow-right" style="font-size: 11pt;">&rarr;</div>
      <div class="wf-card" style="flex: 1.4;">
        <div class="wf-header">STRUCTURED REVIEW BRIEF</div>
        <div class="wf-body">
          Category &bull; Summary &bull; Facts &bull; Evidence
        </div>
      </div>
      <div class="arrow-right" style="font-size: 11pt;">&rarr;</div>
      <div class="wf-card">
        <div class="wf-header">REVIEWER</div>
        <div class="wf-body">
          Confirm &bull; Edit / Override &bull; Flag
        </div>
      </div>
    </div>

    <div class="wf-buttons">
      <div class="wf-btn">Confirm</div>
      <div class="wf-btn">Edit / Override</div>
      <div class="wf-btn">Flag</div>
    </div>

    <p style="margin-top: 3px; font-size: 7.3pt;">
      The reviewer workspace pairs the source document with a structured review brief so extracted facts can be verified in context. Clicking an evidence reference navigates to the relevant source region and provides document-level evidence highlighting where supported. The reviewer can confirm the draft case, edit or override any field, or flag it for further attention. Reviewer actions are recorded in the timestamped audit history.
    </p>

    <h2>7. Testing &amp; Results</h2>
    <table class="table-clean" style="margin-bottom: 0;">
      <thead>
        <tr>
          <th style="width: 60%;">Evaluation Area</th>
          <th style="width: 40%;">Measured Prototype Result</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>Primary triage classification</td>
          <td><strong>27 / 27 (100%)</strong></td>
        </tr>
        <tr>
          <td>Multi-label detection</td>
          <td><strong>100% on benchmark case</strong></td>
        </tr>
      </tbody>
    </table>
  </div>

  <div class="page-footer">
    <span>Clinevo Smart Inbox Assistant &bull; Technical Submission Write-Up</span>
    <span>Page 2</span>
  </div>
</div>

<!-- ================= PAGE 3 ================= -->
<div class="sheet">
  <div>
    <div class="page-header">
      <span>Clinevo Smart Inbox Assistant &bull; Technical Submission Write-Up</span>
      <span>Page 3</span>
    </div>

    <table class="table-clean" style="margin-top: 2px;">
      <thead>
        <tr>
          <th style="width: 60%;">Evaluation Area (Continued)</th>
          <th style="width: 40%;">Measured Prototype Result</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>Core fact extraction</td>
          <td><strong>94.8%</strong></td>
        </tr>
        <tr>
          <td>&ldquo;Not stated&rdquo; handling</td>
          <td><strong>No benchmark hallucinations observed</strong></td>
        </tr>
        <tr>
          <td>Defect photo flagging</td>
          <td><strong>100%</strong></td>
        </tr>
        <tr>
          <td>Literature negative controls</td>
          <td><strong>100%</strong></td>
        </tr>
        <tr>
          <td>Literature case splitting</td>
          <td><strong>3 / 3</strong></td>
        </tr>
        <tr>
          <td>AI service tests</td>
          <td><strong>114 / 114 passed</strong></td>
        </tr>
        <tr>
          <td>Angular tests</td>
          <td><strong>56 / 56 passed</strong></td>
        </tr>
        <tr>
          <td>Spring Boot tests</td>
          <td><strong>20 / 20 passed</strong> (7 core + 13 integration)</td>
        </tr>
        <tr>
          <td>Live mailbox ingestion</td>
          <td><strong>Verified end-to-end</strong></td>
        </tr>
      </tbody>
    </table>
    <p style="font-size: 6.8pt; color: #64748b; margin-top: 2px; margin-bottom: 6px;">
      Evaluated on a synthetic benchmark of 27 cases spanning emails, PDFs, and images. Results reflect prototype-stage evaluation, not a claim of production-grade certainty.
    </p>

    <h2>8. Important Engineering Fixes</h2>
    <ul style="margin: 2px 0 6px 0; padding-left: 14px; font-size: 7.2pt;">
      <li style="margin-bottom: 2px;"><strong>IMAP Fetching Optimization:</strong> Ingestion was optimized to index baseline UIDs and timestamps at startup, ignoring past mailbox clutter and ingesting only live emails.</li>
      <li style="margin-bottom: 2px;"><strong>Canonical Case Identifiers:</strong> Stable canonical case identifiers (CASE-01 through CASE-12) were decoupled from database auto-increment keys.</li>
      <li style="margin-bottom: 2px;"><strong>Retrieval vs. Semantic Verification Separation:</strong> Lexical retrieval and semantic NLI verification were separated into distinct stages; reduced false evidence linkages observed in earlier iterations.</li>
      <li style="margin-bottom: 2px;"><strong>Missing-Value Evidence Isolation:</strong> Fields marked &ldquo;Not stated&rdquo; were isolated so they do not receive unrelated document text passages as evidence.</li>
      <li style="margin-bottom: 2px;"><strong>Category-Specific Schemas:</strong> Distinct payloads were designed per category, reducing output parsing issues through structured schemas and removing irrelevant fields.</li>
      <li style="margin-bottom: 2px;"><strong>Verification Batching:</strong> Fact verification requests were batched; reduced unnecessary API calls and rate-limit pressure.</li>
      <li style="margin-bottom: 2px;"><strong>PDF Viewer / Highlighting Improvement:</strong> Coordinate-based document navigation was enhanced to direct reviewers to relevant source regions where supported.</li>
    </ul>

    <h2>9. Limitations</h2>
    <table class="table-clean" style="margin-bottom: 6px;">
      <thead>
        <tr>
          <th style="width: 50%;">Prototype Boundary</th>
          <th style="width: 50%;">Future Production Work</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>Synthetic data only</td>
          <td>Controlled real-data / privacy architecture</td>
        </tr>
        <tr>
          <td>Cloud model dependency</td>
          <td>Multi-provider fallback strategy</td>
        </tr>
        <tr>
          <td>Local H2 evaluation database</td>
          <td>Managed enterprise database</td>
        </tr>
        <tr>
          <td>No automatic MedDRA / WHO Drug coding</td>
          <td>Dictionary integration</td>
        </tr>
        <tr>
          <td>Prototype audit history</td>
          <td>Formal validation and operational controls</td>
        </tr>
        <tr>
          <td>PDF viewer limitations</td>
          <td>Document rendering / annotation layer improvements</td>
        </tr>
        <tr>
          <td>Human review required</td>
          <td>Workflow / identity controls for production</td>
        </tr>
      </tbody>
    </table>

    <h2>10. Production Next Steps</h2>
    <ul style="margin: 2px 0 6px 0; padding-left: 14px; font-size: 7.2pt;">
      <li style="margin-bottom: 2px;">Data privacy and de-identification</li>
      <li style="margin-bottom: 2px;">Enterprise authentication and access control</li>
      <li style="margin-bottom: 2px;">Production database and distributed processing</li>
      <li style="margin-bottom: 2px;">Formal validation and operational controls</li>
    </ul>

    <h2>11. Final Takeaway</h2>
    <div class="quote-box">
      &ldquo;This prototype demonstrates an end-to-end AI-assisted intake workflow for healthcare communications. It reduces first-pass manual work by organizing incoming messages, extracting relevant information, and linking facts back to source material. The reviewer remains responsible for confirmation and correction. The prototype was evaluated using synthetic benchmark data and is not presented as a production regulatory system.&rdquo;
    </div>

    <div class="footer-links">
      <span>GitHub: https://github.com/sriharizz/smart-inbox</span>
      <span>Run locally: run.bat / ./run.sh</span>
    </div>
  </div>

  <div class="page-footer">
    <span>Clinevo Smart Inbox Assistant &bull; Technical Submission Write-Up</span>
    <span>Page 3</span>
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

if os.path.exists(temp_html):
    os.remove(temp_html)

