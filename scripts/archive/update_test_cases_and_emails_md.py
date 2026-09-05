import os

MD_PATH = r"c:\projects\SmartInbox\test-data\TEST_CASES_AND_EMAILS.md"

with open(MD_PATH, "r", encoding="utf-8") as f:
    existing_content = f.read()

# Locate where Case 10 ends
marker = "### Case 10: Pharmaceutical Conference Marketing (Not Relevant / Spam)"
if marker not in existing_content:
    raise ValueError(f"Could not find marker: {marker}")

# Keep everything through the end of Case 10
case_10_pos = existing_content.find(marker)
# Find the end of Case 10
case_10_end = existing_content.find("\n---\n", case_10_pos)
if case_10_end == -1:
    # It might be at the end of file
    case_10_content = existing_content[case_10_pos:]
    base_existing = existing_content[:case_10_pos] + case_10_content.rstrip() + "\n"
else:
    base_existing = existing_content[:case_10_end].rstrip() + "\n"

additional_content = """

---

## PART II: Published Medical Literature Articles (LIT-01 to LIT-05)
> **Regulatory Context**: Literature screening engine evaluates medical journal reprints (EMA GVP Module VI Section VI.B.1 & FDA 21 CFR 314.80).  
> **Key Objective**: Filter non-reportable review articles, accurately extract clinical cases from 2-column layouts, and split multi-case clinical series into separate individual ICSR records (**+30% Bonus Requirement**).

### LIT-01: Severe Drug-Induced Autoimmune Hepatitis (Single Case)
- **Document File**: `test-data/pdfs/literature_articles/article_01_dili_case.pdf`
- **Format**: 2-Column Academic Journal Layout (NEJM / Lancet style)
- **Citation**: *Journal of Clinical Hepatology & Pharmacovigilance*, Vol 42, No 4, DOI: `10.1016/j.jchpv.2025.04.012`
- **Authors**: Gregory House, MD, PhD; Lisa Cuddy, MD; James Wilson, MD (Princeton-Plainsboro Teaching Hospital)
- **Category**: `Safety Report (ICSR)` (Reportable: YES — Identifiable single patient)
- **Clinical Summary**:
  - **Patient**: 61-year-old Caucasian male, 10-year history of refractory hypertension.
  - **Suspect Drug**: Cardioril (cardioril hydrochloride) 40 mg PO QD for 42 days.
  - **Adverse Reaction**: Idiosyncratic drug-induced autoimmune-like hepatitis, jaundice, dark urine, fatigue.
  - **Diagnostics & Labs**: ALT 680 U/L (>12x ULN), AST 510 U/L (>12x ULN), Total Bilirubin 6.2 mg/dL, ANA seroconversion (titer 1:640, speckled), liver biopsy confirming interface hepatitis with bridging necrosis.
  - **De-challenge**: Cardioril discontinued; oral prednisone taper; transaminases normalized in 6 weeks.
- **Expected AI Extraction**:
  - `category`: `["Safety Report (ICSR)"]`
  - `patient`: `{"age": "61 YRS", "sex": "MALE", "history": "Refractory hypertension, hyperlipidemia"}`
  - `product`: `{"name": "Cardioril (cardioril hydrochloride)", "dose": "40 mg PO QD", "latency": "42 days"}`
  - `reaction`: `{"terms": ["Drug-Induced Autoimmune Hepatitis", "Jaundice", "Hyperbilirubinemia"], "serious": true, "hospitalization": true}`
  - `lab_findings`: `{"ALT": "680 U/L", "AST": "510 U/L", "Total_Bilirubin": "6.2 mg/dL", "ANA": "1:640"}`
  - `source_citation`: `"article_01_dili_case.pdf:Page1:Col1-Col2"`

---

### LIT-02: Stevens-Johnson Syndrome with Neuroval (Single Case)
- **Document File**: `test-data/pdfs/literature_articles/article_02_sjs_case.pdf`
- **Format**: 2-Column Academic Journal Layout
- **Citation**: *British Journal of Clinical Dermatology*, Case Reports, DOI: `10.1111/bjcd.2025.10921`
- **Authors**: Sanjay Gupta, MD; Priya Sharma, MD (Johns Hopkins Bayview Medical Center)
- **Category**: `Safety Report (ICSR)` (Reportable: YES — Identifiable single patient)
- **Clinical Summary**:
  - **Patient**: 24-year-old female with idiopathic trigeminal neuralgia.
  - **Suspect Drug**: Neuroval (neuroval HCl) 150 mg daily for 18 days.
  - **Adverse Reaction**: Stevens-Johnson syndrome (SJS), high fever (39.5°C), purpuric targetoid macules, 8% BSA epidermal detachment, lip hemorrhagic crusting, bilateral purulent conjunctivitis.
  - **Outcome / Seriousness**: ICU burn unit admission; IVIG (1 g/kg/day for 3 days); complete re-epithelialization by day 21. ALDEN score = 6 (very probable). Serious: YES (Life-Threatening & Hospitalization).
- **Expected AI Extraction**:
  - `category`: `["Safety Report (ICSR)"]`
  - `patient`: `{"age": "24 YRS", "sex": "FEMALE", "indication": "Trigeminal neuralgia"}`
  - `product`: `{"name": "Neuroval (neuroval HCl)", "dose": "150 mg daily", "onset_latency": "18 days"}`
  - `reaction`: `{"terms": ["Stevens-Johnson Syndrome (SJS)", "Epidermal Detachment 8% BSA", "Mucosal Crusting"], "serious": true, "life_threatening": true, "hospitalization": true}`
  - `source_citation`: `"article_02_sjs_case.pdf:Page1:Col1-Col2"`

---

### LIT-03: Cutaneous Adverse Reactions Series — 3 Distinct Patients (+30% Bonus Test Asset)
- **Document File**: `test-data/pdfs/literature_articles/article_03_multicase_series.pdf`
- **Format**: 2-Column Academic Journal Layout (Clinical Case Series)
- **Citation**: *The Lancet Regional Health — Europe*, DOI: `10.1016/j.lanepe.2025.100984`
- **Authors**: Marcus Sterling, MD, FRCP; Arthur Pendelton, MBChB; Eleanor Vance, MD (Royal Free Hospital & Guy's and St Thomas' NHS Trust, London)
- **Category**: `Safety Report (ICSR)` — **MULTI-CASE CLINICAL SERIES**
- **Crucial Engine Requirement (+30% Bonus)**: Literature engine must recognize this document describes **3 separate independent patients** and split it into **3 distinct ICSR records** rather than aggregating them into 1 record.
- **Patient Case Breakdown**:
  1. **Patient 1 (A.J.)**:
     - Demographics: 45-year-old male, weight 81 kg.
     - Drug: Cardioril 20 mg QD (onset day 22).
     - Reaction: Severe Erythema Multiforme Major (symmetric target lesions, blistering, oral erosions). Serious: YES (Hospitalization, systemic steroids).
  2. **Patient 2 (B.L.)**:
     - Demographics: 62-year-old female, weight 64 kg.
     - Drug: Corzapan 10 mg daily (onset 8 weeks).
     - Reaction: Subacute Cutaneous Lupus Erythematosus (SCLE), annular polycyclic plaques, Anti-Ro/SSA >240 U/mL, ANA 1:320. Serious: NO (Non-hospitalized, resolved with topical tacrolimus).
  3. **Patient 3 (C.M.)**:
     - Demographics: 38-year-old female, weight 59 kg.
     - Drug: Cardioril 10 mg daily (onset 90 minutes).
     - Reaction: Acute Urticaria and Periorbital Angioedema, dysphonia, pruritus. Serious: YES (Life-Threatening / Emergency IM epinephrine).
- **Expected AI Extraction**:
  - `multicase_detected`: `true`
  - `cases_extracted_count`: `3`
  - `split_records`: List of 3 independent ICSR objects with distinct patient demographics, drugs, reactions, and seriousness criteria.
  - `source_citation`: `"article_03_multicase_series.pdf:Page1:Col1 (Case 1), Col2 (Case 2 & Case 3)"`

---

### LIT-04: Preclinical In-Vitro & Animal Metabolism (Non-Reportable Negative Review)
- **Document File**: `test-data/pdfs/literature_articles/article_04_preclinical_review.pdf`
- **Format**: 2-Column Academic Journal Layout
- **Citation**: *European Journal of Pharmaceutical Sciences*, DOI: `10.1016/j.ejps.2025.105412`
- **Authors**: Heinrich Mueller, PhD; Klaus Schmidt, PhD (Technical University of Munich)
- **Category**: `Not Relevant` / `Literature: Non-Reportable`
- **Clinical/Scientific Context**: Preclinical in-vitro metabolic clearance and CYP450 interaction assays in Sprague-Dawley rat hepatocytes and human liver microsomes. Zero human patient exposure, zero clinical safety cases.
- **Expected AI Decision**:
  - `category`: `["Not Relevant"]` or `["Literature: Non-Reportable"]`
  - `reportable_to_health_authority`: `false`
  - `exclusion_reason`: *"Exclusively preclinical animal/in-vitro laboratory study without identifiable human clinical cases (GVP Module VI Section VI.B.1 exempt)."*
  - `extracted_patients_count`: `0`

---

### LIT-05: Meta-Analysis & Systematic Review (Non-Reportable Negative Review)
- **Document File**: `test-data/pdfs/literature_articles/article_05_meta_analysis_review.pdf`
- **Format**: 2-Column Academic Journal Layout
- **Citation**: *International Journal of Cardiology Reviews*, DOI: `10.1016/j.ijcard.2025.110294`
- **Authors**: Catherine Tremblay, MD; Jean-Luc Moreau, MD (Montreal Heart Institute & McGill University)
- **Category**: `Not Relevant` / `Literature: Non-Reportable`
- **Clinical/Scientific Context**: Meta-analysis and systematic review of 34 randomized controlled trials (28,450 aggregate participants) evaluating third-generation antihypertensives. Reports pooled aggregate odds ratios and mean blood pressure reduction. Zero individual identifiable patient reports.
- **Expected AI Decision**:
  - `category`: `["Not Relevant"]` or `["Literature: Non-Reportable"]`
  - `reportable_to_health_authority`: `false`
  - `exclusion_reason`: *"Aggregate epidemiological review and statistical meta-analysis without individual identifiable patient case safety reports."*
  - `extracted_patients_count`: `0`

---

## PART III: Additional Regulatory Forms & Specialized Test Documents

### NON-ENG-02: German Charité Berlin BfArM UAW Meldebogen
- **Document File**: `test-data/pdfs/non_english/bericht_uaw_charite_berlin.pdf`
- **Regulatory Standard**: Official German Federal Institute for Drugs and Medical Devices (*BfArM*) Adverse Drug Reaction Reporting Form (§ 63b AMG).
- **Originating Clinic**: Charité – Universitätsmedizin Berlin, Campus Virchow-Klinikum.
- **Language**: German (`de`)
- **Clinical Scenario**:
  - Patient: Hans Schneider (H.S.), 63 Jahre alt, männlich, 88 kg.
  - Verdächtiges Arzneimittel: Cardioril (Cardioril-HCl) 20 mg 1x täglich p.o., Ch.-B.: CR-2025-0814.
  - Unerwünschte Wirkung: Akutes Angioödem von Lippen, Zunge und Pharynx, schwere Dyspnoe, inspiratorischer Stridor, diffuses Urtikaria-Exanthem.
  - Schweregrad: Lebensbedrohlich: JA, Stationäre Aufnahme (Intensivstation Charité): JA.
  - Meldender Arzt: Dr. med. Wolfgang Becker (Charité Berlin).
- **Expected AI Extraction**:
  - `detected_language`: `"de"`
  - `category`: `["Safety Report (ICSR)"]`
  - `translated_reaction`: `"Acute Angioedema (Lips, Tongue, Pharynx), Severe Dyspnea, Inspiratory Stridor, Urticaria"`
  - `seriousness`: `{"life_threatening": true, "hospitalization": true}`
  - `traceability_link`: Links back to original German terms in `bericht_uaw_charite_berlin.pdf:Page1`.

---

### DIG-03: CIOMS Form I — Pediatric Oncology Acute Cytokine Release
- **Document File**: `test-data/pdfs/digital_forms/cioms_pediatric_oncology.pdf`
- **Format**: Official Monochrome CIOMS-I Special Population Grid
- **Scenario**: 8-year-old male (Lucas Torres, L.T., 26 kg) with ALL maintenance receiving OncoShield 50mg/m² IV (Lot #OS-2025-771). Developed acute cytokine release syndrome (rigors, fever 40.1°C, hypoxemia SpO2 88%, PICU admission).
- **Category**: `Safety Report (ICSR)` (Special Population: Pediatric, Seriousness: Life-threatening & PICU Hospitalization).
- **Reporter**: Dr. Amanda Bennett, MD, FAAP (Children's Memorial Hospital, Boston, MA).

---

### DIG-04: FDA Form 3500A — Initial Neuroval Seizure Report
- **Document File**: `test-data/pdfs/digital_forms/fda_medwatch_initial_neuroval.pdf`
- **Format**: Official Monochrome FDA MedWatch 3500A Grid
- **Scenario**: Initial report for 52-year-old male (David Miller, D.M., 79 kg) who suffered a new-onset generalized tonic-clonic seizure 48 hours following Neuroval dose escalation to 400mg daily. Admitted to Neuro ICU.
- **Category**: `Safety Report (ICSR)` (Initial report pairing with follow-up `fda_medwatch_followup.pdf` in Case 06).
- **Reporter**: Dr. Richard Vance, MD (Columbia University Medical Center).

---

### DIG-05: CIOMS Form I — Acute Kidney Injury / KDIGO Stage 3
- **Document File**: `test-data/pdfs/digital_forms/cioms_form_renal_injury.pdf`
- **Format**: Official Monochrome CIOMS-I Grid
- **Scenario**: 67-year-old male (George Taylor, G.T., 76 kg) initiated Renotril 30mg PO QD. Developed oliguria, serum creatinine spike from 1.0 to 4.2 mg/dL (KDIGO 3 AKI), BUN 68 mg/dL, potassium 5.6 mEq/L. Hospitalized 5 days.
- **Category**: `Safety Report (ICSR)` (Seriousness: Inpatient Hospitalization).
- **Reporter**: Dr. Keith Miller, MD (Nephrology, Vanderbilt University Medical Center).

---

### MED-01: Cardioril Clinical Monograph & Renal Dosing Reference
- **Document File**: `test-data/pdfs/medical_info/cardioril_clinical_monograph_dosing.pdf`
- **Format**: Medical Information Reference Document with structured dosing grid
- **Content**: Detailed clinical dosing recommendations stratified by eGFR (Normal, Mild, Moderate CKD 3, Severe CKD 4/5, ESRD hemodialysis) and dialysis clearance kinetics.
- **Category**: `Medical Information (MI)` ONLY (Zero patient data, zero adverse reactions, zero quality defects).

---

### MED-02: Corzapan Formulation Stability & Enteral Tube Interaction Guide
- **Document File**: `test-data/pdfs/medical_info/corzapan_drug_interaction_guide.pdf`
- **Format**: Medical Affairs Formulation Compatibility Table
- **Content**: Enteral tube flushing protocols, crushing stability across NG, G-tube, and J-tube administration, and CYP3A4/CYP2C9 pharmacokinetic interaction tables.
- **Category**: `Medical Information (MI)` ONLY (Pure pharmacology guidance inquiry reference).

---

### IRR-01: PharmaTech Global AI Summit Sponsorship Prospectus
- **Document File**: `test-data/pdfs/irrelevant/pharmatech_conference_prospectus.pdf`
- **Format**: Commercial Event Flyer & Sponsorship Pricing Matrix
- **Content**: Sponsorship tiers ($45,000 Diamond, $28,000 Platinum, $15,000 Gold), booth layouts, attendee demographics for pharma marketing.
- **Category**: `Not Relevant` ONLY (Spam / Commercial Marketing).

---

## PART IV: Master Evaluation & Ingestion Artifacts

### 1. `manifest.json` — System Inventory & Ingestion Catalog
- **Location**: [`test-data/manifest.json`](file:///c:/projects/SmartInbox/test-data/manifest.json)
- **Role**: Structured catalog indexing all 28 assets in the test suite.
- **Fields Provided per Asset**:
  - `id`: Unique asset identifier (`CASE-01`, `LIT-03`, `NON-ENG-02`)
  - `email`: Relative path to `.eml` file (or `null` if standalone literature reprint)
  - `pdf`: Relative path to `.pdf` document
  - `category`: Target clinical classification (`ICSR`, `PQC`, `MI`, `Not Relevant`)
  - `flavor`: Document typology (`Digital_PDF`, `Scanned_Handwritten`, `Published_Article`, `Non_English`, `Pure_Text_Email`)
  - `has_table`: Boolean indicating whether structured tables exist
  - `has_image`: Boolean indicating whether meaningful clinical images/photos exist
  - `language`: Primary document language (`en`, `es`, `de`)
  - `multicase_bonus`: Flag for literature splitting engine

### 2. `benchmark.json` — Ground Truth Evaluation Key
- **Location**: [`test-data/ground_truth/benchmark.json`](file:///c:/projects/SmartInbox/test-data/ground_truth/benchmark.json)
- **Role**: Gold-standard answers for automated grading of the AI microservice.
- **Grading Harness Capabilities**:
  - **Classification Accuracy**: Compares multi-label category outputs against expected buckets.
  - **Extraction Precision & Recall (F1)**: Compares patient age, sex, suspect drug, lot number, adverse events, lab test numbers, and seriousness flags.
  - **Zero-Guessing Validation**: Verifies that unmentioned fields are strictly returned as `"Not stated"` rather than hallucinated.
  - **Source Citation Verification**: Checks that every extracted fact links to the exact PDF page and section.
  - **Literature Multi-Case Split Metric**: Verifies that `article_03_multicase_series.pdf` generates exactly 3 distinct patient records.

---

## PART V: Final Minimum Assignment Requirements & Compliance Audit Checklist

### Physical File Audit Against Clinevo Assignment Requirements

| Data / Test Asset | Minimum Required | Target to Create | Current Physical Status | Audit Result | Remaining |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Intake `.eml` emails** | 10 | 10–11 | **10 files on disk** (`email_01.eml` to `email_10.eml`) | **Completed** | **0** |
| **Safety Report (ICSR) examples** | Covered in emails | 6+ | **6 emails + 8 PDFs** | **Completed** | **0** |
| **Quality Complaint (PQC)-only examples** | 2 | 2 | **2 emails** (Case 07, 08) + **2 PDFs** | **Completed** | **0** |
| **Medical Information (MI)-only examples** | 2 | 2 | **1 email** (Case 09) + **2 PDFs** (MED-01, 02) | **Completed** | **0** |
| **Not Relevant / Marketing examples** | 1 | 1+ | **1 email** (Case 10) + **1 PDF** (IRR-01) | **Completed** | **0** |
| **Multi-label ICSR + PQC example** | At least 1 | 1+ | **1 case** (Case 04 MedWatch + contaminated vial) | **Completed** | **0** |
| **Normal digital PDFs** | 5 | 5+ | **5 files on disk** (`digital_forms/*.pdf`) | **Completed** | **0** |
| **Scanned / handwritten PDFs** | 2 | 2 | **1 file on disk** (`urgent_care_intake_handwritten.pdf`) | **Pending User Photo** | **1** |
| **Published article PDFs (fictional cases)**| 5 | 5 | **5 files on disk** (`literature_articles/*.pdf`) | **Completed** | **0** |
| **Non-English PDFs** | 2 | 2 | **2 files on disk** (`notificacion_ram_madrid.pdf`, `bericht_uaw_charite_berlin.pdf`) | **Completed** | **0** |
| **PDF containing structured table(s)** | Required | 2+ | **8 PDFs on disk** (CIOMS labs, MedWatch grids, dosing tables) | **Completed** | **0** |
| **PDF containing meaningful image(s)** | Required | 2+ | **2 PDFs on disk** (handwritten intake, vial contamination) | **Completed** | **0** |
| **Image requiring human-review flag** | Required | 1+ | **1 photo exhibit** (cracked crimp seal with particulate) | **Completed** | **0** |
| **Documents with deliberately missing fields**| Required | 2+ | **Cases 02, 03, 08, 09** (testing `"Not stated"`) | **Completed** | **0** |
| **Field-level source/page traceability** | Required | All docs | **Full ground truth citations** in `benchmark.json` | **Completed** | **0** |
| **Machine-readable ground truth JSON** | Required | 1 file | **1 file on disk** (`benchmark.json`) | **Completed** | **0** |
| **Dataset manifest** | Recommended | 1 file | **1 file on disk** (`manifest.json`) | **Completed** | **0** |
| **Total Physical PDFs Verified** | 19 | 19 | **18 files on disk** (19th deferred for user photo) | **95% Complete** | **1** |

---

### Required PDF Flavor Coverage

| PDF Flavor | Minimum Required | Current Physical Count | Verification Location | Status |
| :--- | :---: | :---: | :--- | :---: |
| **Digital structured PDF** | 5 | **5** | `test-data/pdfs/digital_forms/` | **Completed** |
| **Scanned / handwritten** | 2 | **1** | `test-data/pdfs/scanned_handwritten/` | **1 Pending User Photo** |
| **Published medical article (fictional cases)** | 5 | **5** | `test-data/pdfs/literature_articles/` | **Completed** |
| **Non-English (Spanish & German)** | 2 | **2** | `test-data/pdfs/non_english/` | **Completed** |
| **Quality complaint specific** | 2 | **2** | `test-data/pdfs/quality_complaints/` | **Completed** |
| **Medical info specific** | 2 | **2** | `test-data/pdfs/medical_info/` | **Completed** |
| **Irrelevant / marketing** | 1 | **1** | `test-data/pdfs/irrelevant/` | **Completed** |

---

### Required Behavior Coverage in Test Suite

| Target Behavior | Test Asset | Verification Standard |
| :--- | :--- | :--- |
| **Digital PDF text extraction** | Cases 01, 04, 06, DIG-03, 04, 05 | Extracting clean typography without character drops |
| **OCR / handwriting recognition + confidence** | Case 02 (`urgent_care_intake_handwritten.pdf`) | Vision model reading blue ink handwriting with confidence score |
| **Multi-column article handling** | LIT-01 through LIT-05 | Reading left-to-right columns sequentially without interleaving |
| **Language detection** | Case 05 (`es`), NON-ENG-02 (`de`) | Correctly identifying ISO language code |
| **Translation & original-language linkage** | Case 05, NON-ENG-02 | Providing English clinical translation with links to original Spanish/German |
| **Table → structured rows/columns** | Case 01, Case 04, MED-01, MED-02 | Converting PDF table grid to structured JSON matrix |
| **Meaningful image description** | Case 04 (Exhibit 1) | Vision model identifying cracked crimp collar & black particulate |
| **Image → human review flag** | Case 04 | Flagging `photo_requires_human_review: true` in UI |
| **10–15 sentence PDF summary** | All PDFs | Executive narrative summarizing background, event, and outcome |
| **`"Not stated"` instead of guessing** | Cases 02, 03, 08 | Zero-hallucination policy for unstated lots, weights, or doses |
| **Confidence for extracted fields** | All Cases | Calibrated 0.0–1.0 score per extracted entity |
| **Source page & snippet for every fact** | All Cases | Traceability coordinates mapping each value to its source |
| **Literature Multi-Case Splitting (+30%)** | LIT-03 (`article_03_multicase_series.pdf`)| Disaggregating 1 journal reprint into 3 distinct ICSR records |
| **Reviewer accept / override** | Dashboard UI | Human reviewer editing or accepting AI proposals |
| **Audit timestamp for actions** | Audit event store | Recording `{timestamp, actor, action, previous_val, new_val}` |
"""

new_full_content = base_existing + additional_content

with open(MD_PATH, "w", encoding="utf-8") as f:
    f.write(new_full_content)

print(f"[SUCCESS] Updated {MD_PATH}. Total bytes: {len(new_full_content)}")
