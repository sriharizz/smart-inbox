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
    font-size: 8.2pt;
    line-height: 1.38;
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
    margin-bottom: 8px;
    font-size: 7pt;
    font-weight: 600;
    color: #64748b;
  }

  .page-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-top: 1px solid #cbd5e1;
    padding-top: 4px;
    margin-top: 6px;
    font-size: 7pt;
    color: #94a3b8;
  }

  h1.main-title {
    font-family: 'Outfit', sans-serif;
    font-size: 17pt;
    font-weight: 800;
    color: #0f172a;
    line-height: 1.15;
    margin: 0 0 2px 0;
  }

  .sub-title {
    font-size: 9.5pt;
    font-weight: 600;
    color: #334155;
    margin: 0 0 2px 0;
  }

  .tagline {
    font-size: 8pt;
    color: #64748b;
    margin: 0 0 8px 0;
  }

  .meta-bar {
    display: grid;
    grid-template-columns: 1.2fr 1.5fr 1.8fr;
    gap: 12px;
    background: #f8fafc;
    border-top: 1px solid #e2e8f0;
    border-bottom: 1px solid #e2e8f0;
    padding: 6px 10px;
    margin-bottom: 10px;
  }

  .meta-col {
    font-size: 7.6pt;
  }
  .meta-label {
    color: #64748b;
    font-weight: 600;
    display: block;
    margin-bottom: 1px;
    font-size: 6.8pt;
    text-transform: uppercase;
    letter-spacing: 0.3px;
  }
  .meta-val {
    color: #0f172a;
    font-weight: 600;
  }

  h2 {
    font-family: 'Outfit', sans-serif;
    font-size: 10.5pt;
    font-weight: 700;
    color: #0f172a;
    margin: 8px 0 4px 0;
    line-height: 1.2;
  }

  p {
    margin: 0 0 6px 0;
    text-align: justify;
  }

  /* 4 Categories 2x2 Grid */
  .category-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    margin: 6px 0;
  }

  .cat-card {
    border: 1px solid #cbd5e1;
    border-radius: 5px;
    overflow: hidden;
  }

  .cat-header {
    background: #0f2744;
    color: #ffffff;
    font-weight: 700;
    font-size: 7.8pt;
    padding: 3.5px 8px;
  }
  .cat-header.accent {
    background: #1e528a;
  }

  .cat-body {
    padding: 5px 8px;
    font-size: 7.4pt;
    background: #ffffff;
    color: #334155;
    min-height: 28px;
  }

  /* Architecture & Flow Diagrams */
  .arch-container {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 10px 8px 6px 8px;
    margin: 6px 0;
  }

  .flow-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 4px;
  }

  .node-box {
    background: #f8fafc;
    border: 1.2px solid #64748b;
    border-radius: 5px;
    padding: 8px 6px;
    text-align: center;
    font-weight: 600;
    font-size: 7.5pt;
    color: #0f172a;
    flex: 1;
    min-height: 38px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .node-ai-group {
    flex: 1.25;
    display: flex;
    flex-direction: column;
    gap: 3px;
  }

  .node-ai-header {
    background: #1e528a;
    color: #ffffff;
    border: 1px solid #1e528a;
    border-radius: 4px;
    padding: 6px 4px;
    text-align: center;
    font-weight: 700;
    font-size: 7.8pt;
  }

  .node-ai-sub {
    background: #f8fafc;
    border: 1px solid #94a3b8;
    border-radius: 3px;
    padding: 2.5px 4px;
    text-align: center;
    font-size: 6.8pt;
    color: #334155;
  }

  .node-human {
    background: #0f2744;
    color: #ffffff;
    border: 1px solid #0f2744;
    border-radius: 4px;
    padding: 6px 4px;
    text-align: center;
    font-weight: 700;
    font-size: 7.5pt;
    margin-top: 6px;
  }

  .arrow-right {
    color: #64748b;
    font-weight: 700;
    font-size: 10pt;
    padding: 0 1px;
    user-select: none;
  }

  .arch-banner {
    background: #e2e8f0;
    border-radius: 3px;
    padding: 4px;
    text-align: center;
    font-weight: 600;
    font-size: 7.2pt;
    color: #1e293b;
    margin-top: 8px;
  }

  /* Processing Flow Diagram */
  .process-grid {
    display: flex;
    flex-direction: column;
    gap: 6px;
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 8px 8px;
    margin: 6px 0;
  }

  .proc-node {
    background: #ffffff;
    border: 1.2px solid #64748b;
    border-radius: 4px;
    padding: 7px 4px;
    text-align: center;
    font-weight: 600;
    font-size: 7.4pt;
    flex: 1;
    color: #0f172a;
  }

  .proc-node.dark {
    background: #1e528a;
    border-color: #1e528a;
    color: #ffffff;
    font-weight: 700;
  }

  /* Tables */
  table {
    width: 100%;
    border-collapse: collapse;
    margin: 4px 0 6px 0;
    font-size: 7.3pt;
  }

  th {
    background: #0f2744;
    color: #ffffff;
    font-weight: 700;
    text-align: left;
    padding: 4px 6px;
    font-size: 7.2pt;
    border-bottom: 1.5px solid #0f172a;
  }

  td {
    padding: 3.5px 6px;
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
    padding: 5px 8px;
    margin: 5px 0;
    font-size: 7.2pt;
    color: #1e40af;
  }

  /* Reviewer Workflow */
  .workflow-container {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
    margin: 6px 0 4px 0;
  }

  .wf-card {
    flex: 1;
    border: 1px solid #cbd5e1;
    border-radius: 5px;
    overflow: hidden;
  }

  .wf-header {
    background: #0f2744;
    color: #ffffff;
    font-weight: 700;
    font-size: 7.5pt;
    padding: 3.5px 8px;
    text-align: center;
    letter-spacing: 0.4px;
  }

  .wf-body {
    padding: 6px 10px;
    background: #ffffff;
    font-size: 7.3pt;
    line-height: 1.45;
    text-align: center;
  }

  .wf-buttons {
    display: flex;
    justify-content: center;
    gap: 10px;
    margin: 4px 0 6px 0;
  }

  .wf-btn {
    border: 1px solid #cbd5e1;
    background: #f8fafc;
    border-radius: 3px;
    padding: 2.5px 14px;
    font-weight: 600;
    font-size: 7.2pt;
    color: #0f172a;
  }

  .two-col-list {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    margin: 4px 0 6px 0;
  }

  .two-col-list ul {
    margin: 0;
    padding-left: 14px;
  }

  .two-col-list li {
    margin-bottom: 2.5px;
    font-size: 7.3pt;
  }

  .quote-box {
    background: #f1f5f9;
    border-radius: 4px;
    padding: 8px 10px;
    margin: 6px 0 10px 0;
    font-size: 7.3pt;
    font-style: italic;
    color: #334155;
    line-height: 1.4;
  }

  .footer-links {
    display: flex;
    justify-content: space-between;
    font-size: 7.2pt;
    font-weight: 600;
    color: #0f172a;
    padding-top: 4px;
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
        <span class="meta-val">Core (100%) + Literature Bonus (30%)</span>
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

    <p style="margin-top: 4px; margin-bottom: 8px;">
      Multi-label cases are explicitly supported &mdash; for example, a contaminated vial that also caused an adverse reaction is classified as both PQC and ICSR.
    </p>

    <h2>2. Architecture</h2>
    <div class="arch-container">
      <div class="flow-row">
        <div class="node-box">Email / PDF<br>Input</div>
        <div class="arrow-right">&rarr;</div>
        <div class="node-box">Spring Boot<br>Ingestion</div>
        <div class="arrow-right">&rarr;</div>
        <div class="node-ai-group">
          <div class="node-ai-header">Python AI Service</div>
          <div class="node-ai-sub">Document Understanding</div>
          <div class="node-ai-sub">Classification</div>
          <div class="node-ai-sub">Fact Extraction</div>
          <div class="node-ai-sub">Evidence Verification</div>
        </div>
        <div class="arrow-right">&rarr;</div>
        <div class="node-box">Spring Boot<br>Persistence / API</div>
        <div class="arrow-right">&rarr;</div>
        <div style="flex: 1; display: flex; flex-direction: column;">
          <div class="node-box" style="width: 100%;">Angular<br>Reviewer UI</div>
          <div style="text-align: center; color: #64748b; font-size: 8pt; margin: 1px 0;">&darr;</div>
          <div class="node-human">Human Reviewer</div>
        </div>
      </div>
      <div class="arch-banner">
        Angular 18 &nbsp;|&nbsp; Spring Boot 3 &nbsp;|&nbsp; Python / FastAPI &nbsp;|&nbsp; H2 (local evaluation)
      </div>
    </div>

    <h2>3. Processing Flow</h2>
    <div class="process-grid">
      <div class="flow-row">
        <div class="proc-node">Receive</div>
        <div class="arrow-right">&rarr;</div>
        <div class="proc-node">Understand</div>
        <div class="arrow-right">&rarr;</div>
        <div class="proc-node">Classify</div>
        <div class="arrow-right">&rarr;</div>
        <div class="proc-node">Extract</div>
      </div>
      <div style="display: flex; justify-content: flex-end; padding-right: 48px; color: #64748b; font-size: 9pt; margin: -3px 0;">
        &darr;
      </div>
      <div class="flow-row">
        <div class="proc-node">Ground with<br>Evidence</div>
        <div class="arrow-right">&rarr;</div>
        <div class="proc-node">Verify</div>
        <div class="arrow-right">&rarr;</div>
        <div class="proc-node">Human Review</div>
        <div class="arrow-right">&rarr;</div>
        <div class="proc-node dark">Audit</div>
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
          <td>Entire document is passed in-prompt with layout preserved; no chunk-boundary errors.</td>
        </tr>
        <tr>
          <td><strong>Category-specific payloads</strong></td>
          <td>Forcing all messages into an ICSR schema produced empty tables and false warnings.</td>
          <td>Distinct payloads per category give a clean, relevant reviewer view.</td>
        </tr>
        <tr>
          <td><strong>Evidence-linked fact model</strong></td>
          <td>Reviewers need to see where an extracted value came from before trusting it.</td>
          <td>Every fact links to a source citation with location and verbatim snippet.</td>
        </tr>
        <tr>
          <td><strong>Separate retrieval from semantic verification</strong></td>
          <td>High lexical similarity does not guarantee a passage actually supports a fact.</td>
          <td>Retrieval and NLI-based verification are split into two steps, reducing false linkages.</td>
        </tr>
        <tr>
          <td><strong>&ldquo;Not stated&rdquo; for missing information</strong></td>
          <td>General-purpose models tend to infer unstated clinical details.</td>
          <td>Prompts enforce negative constraints; missing values are marked &ldquo;Not stated.&rdquo;</td>
        </tr>
        <tr>
          <td><strong>Fixture + live mailbox ingestion</strong></td>
          <td>Reviewers and tests need to run offline without live email credentials.</td>
          <td>An ingestion abstraction supports both live IMAP polling and offline fixtures.</td>
        </tr>
        <tr>
          <td><strong>Human-in-the-loop review</strong></td>
          <td>Autonomous decisions are inappropriate for patient-safety-relevant content.</td>
          <td>The AI prepares a draft case; the human reviewer confirms or overrides it.</td>
        </tr>
      </tbody>
    </table>

    <h2>5. AI / Prompting Approach</h2>
    <div class="two-col-list">
      <ul>
        <li>Structured model outputs enforced via strict schemas</li>
        <li>Category-aware extraction tailored to the detected communication type</li>
        <li>Source-grounded facts, with every value traceable to source text</li>
        <li>&ldquo;Not stated&rdquo; used instead of guessing at missing values</li>
      </ul>
      <ul>
        <li>Multilingual document handling (e.g. German, Spanish reports)</li>
        <li>Table and scanned-document handling via layout-aware parsing</li>
        <li>Separate evidence verification step (SUPPORTS / CONTRADICTS / INSUFFICIENT)</li>
        <li>Literature screening extension for journal PDFs (bonus scope)</li>
      </ul>
    </div>

    <div class="callout">
      <strong>Safety note:</strong> Model outputs can contain errors or omissions. The prototype is designed as a reviewer aid; the final decision remains with the human reviewer.
    </div>

    <h2>6. Reviewer Workflow</h2>
    <div class="workflow-container">
      <div class="wf-card">
        <div class="wf-header">SOURCE DOCUMENT</div>
        <div class="wf-body">
          Email / PDF / Image<br>
          Evidence source location<br>
          Verbatim source passages
        </div>
      </div>
      <div class="arrow-right" style="font-size: 14pt;">&rarr;</div>
      <div class="wf-card">
        <div class="wf-header">STRUCTURED REVIEW BRIEF</div>
        <div class="wf-body">
          Category<br>
          Summary<br>
          Extracted facts<br>
          Evidence links<br>
          Reviewer actions
        </div>
      </div>
    </div>

    <div class="wf-buttons">
      <div class="wf-btn">Confirm</div>
      <div class="wf-btn">Edit / Override</div>
      <div class="wf-btn">Flag</div>
    </div>

    <p style="margin-top: 4px; font-size: 7.4pt;">
      The reviewer workspace pairs the original source document with a structured review brief so every extracted fact can be checked in context. Clicking an evidence reference scrolls the source viewer directly to the supporting passage. The reviewer can confirm the draft case, edit or override any field, or flag it for further attention &mdash; with every action recorded in a timestamped audit history.
    </p>

    <h2>7. Testing &amp; Results</h2>
    <table class="table-clean" style="margin-bottom: 0;">
      <thead>
        <tr>
          <th style="width: 60%;">Evaluation</th>
          <th style="width: 40%;">Result</th>
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
          <th style="width: 60%;">Evaluation</th>
          <th style="width: 40%;">Result</th>
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
    <p style="font-size: 6.8pt; color: #64748b; margin-top: 2px; margin-bottom: 8px;">
      Evaluated on a synthetic benchmark of 27 cases spanning emails, PDFs, and images. Results reflect prototype-stage evaluation, not a claim of production-grade certainty.
    </p>

    <h2>8. Important Engineering Fixes</h2>
    <ul style="margin: 3px 0 8px 0; padding-left: 14px; font-size: 7.3pt;">
      <li style="margin-bottom: 2.5px;"><strong>IMAP Startup Baseline Polling:</strong> Ingestion was updated to index historical UIDs/timestamps at boot, ignoring past mailbox clutter and ingesting only live emails sent post-startup.</li>
      <li style="margin-bottom: 2.5px;"><strong>Canonical Case Identifier Stability:</strong> Canonical CASE-01... identifiers were separated from database auto-increment IDs.</li>
      <li style="margin-bottom: 2.5px;"><strong>Decoupled Semantic Verification:</strong> Retrieval and semantic verification were separated to remove false evidence linkages.</li>
      <li style="margin-bottom: 2.5px;"><strong>Missing Value Evidence Isolation:</strong> &ldquo;Not stated&rdquo; fields were prevented from receiving unrelated evidence chunks.</li>
      <li style="margin-bottom: 2.5px;"><strong>Category-Specific View Schemas:</strong> Distinct payloads removed irrelevant ICSR fields from PQC/MI cases.</li>
      <li style="margin-bottom: 2.5px;"><strong>Entailment Request Batching:</strong> Verification was batched to reduce unnecessary API calls by ~96% and eliminate rate-limit pressure.</li>
    </ul>

    <h2>9. Limitations</h2>
    <table class="table-clean" style="margin-bottom: 8px;">
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
          <td>Multi-provider strategy</td>
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
          <td>Formal validation / signature controls</td>
        </tr>
        <tr>
          <td>PDF highlighting has some viewer limitations</td>
          <td>Stronger document rendering / annotation layer</td>
        </tr>
        <tr>
          <td>Human review required</td>
          <td>Workflow / identity controls for production</td>
        </tr>
      </tbody>
    </table>

    <h2>10. Production Next Steps</h2>
    <ul style="margin: 3px 0 8px 0; padding-left: 14px; font-size: 7.3pt;">
      <li style="margin-bottom: 2.5px;">Data privacy and de-identification</li>
      <li style="margin-bottom: 2.5px;">Enterprise authentication and access control</li>
      <li style="margin-bottom: 2.5px;">Production database and distributed processing</li>
      <li style="margin-bottom: 2.5px;">Formal validation and operational controls</li>
    </ul>

    <h2>11. Final Takeaway</h2>
    <div class="quote-box">
      &ldquo;This prototype demonstrates an end-to-end AI-assisted intake workflow for healthcare communications. It reduces first-pass manual work by organizing incoming messages, extracting relevant information, and linking facts back to source material. The reviewer remains responsible for confirmation and correction. The prototype was evaluated using synthetic benchmark data and is not presented as a production regulatory system.&rdquo;
    </div>

    <div class="footer-links">
      <span>GitHub: github.com/sriharizz/smart-inbox</span>
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
