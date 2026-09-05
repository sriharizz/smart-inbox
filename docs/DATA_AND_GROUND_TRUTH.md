# DATASET & GROUND TRUTH SPECIFICATION — CLINEVO SMART INBOX ASSISTANT

## 1. Synthetic Data Principle & Regulatory Compliance

In pharmacovigilance (PV), data privacy and regulatory confidentiality are paramount. Real-world Individual Case Safety Reports (ICSRs) contain Protected Health Information (PHI) and Personally Identifiable Information (PII) subject to HIPAA (Health Insurance Portability and Accountability Act), EU GDPR (General Data Protection Regulation), and global clinical trial confidentiality standards.

**All clinical, patient, healthcare professional, institution, and product lot data in this dataset are 100% synthetic.**
- Patient names are fictional initials or pseudonyms (e.g., M.K., J.R., A.J.).
- Healthcare practitioners and clinics are synthetic entities (e.g., "Dr. Sarah Jenkins", "St. Jude Community Hospital", "Clínica San Carlos").
- Suspect medications utilize fictional or generic drug names with realistic dosages (e.g., Cardioril, Cefatox, Neurozap, RespiraClear, Dermacool, Glucotear).
- Documents are styled after official regulatory forms (CIOMS-I, FDA MedWatch 3500A, AEMPS, BfArM) but clearly labelled as synthetic test artifacts.

---

## 2. Physical File Inventory

The dataset is physically located under `test-data/` and comprises the following verified physical assets:

| Asset Type | Count | Directory Location | Details / Formats |
| :--- | :---: | :--- | :--- |
| **Intake Emails** | 11 | `test-data/emails/` | RFC 5322 MIME `.eml` files (`email_01.eml` to `email_11.eml`) |
| **Physical PDFs** | 20 | `test-data/pdfs/` | 4 flavors: Digital Forms, Scanned/Handwritten, Literature, Non-English |
| **Physical Images** | 2 | `test-data/pdfs/` subdirs | Standalone defect & clinical evidence photos (`.jpg`) |
| **Ground Truth** | 1 | `test-data/ground_truth/` | `benchmark.json` (Version 3.0.0, 27 canonical cases) |
| **Asset Manifest** | 1 | `test-data/` | `manifest.json` with verified SHA-256 hashes |
| **Master Catalog** | 1 | `test-data/` | `TEST_CASES_AND_EMAILS.md` master reference catalog |

### 2.1 PDF Assets by Regulatory Flavor

1. **Normal Digital PDFs (6 assets)**:
   - `test-data/pdfs/digital_forms/cioms_form_MK_Cardioril.pdf` (CIOMS-I format, 1 page)
   - `test-data/pdfs/digital_forms/fda_3500a_JR_Neurozap.pdf` (FDA MedWatch 3500A format, 1 page)
   - `test-data/pdfs/digital_forms/cioms_form_dili_acute.pdf` (CIOMS-I format, 1 page)
   - `test-data/pdfs/digital_forms/fda_3500a_anaphylaxis.pdf` (FDA MedWatch 3500A format, 1 page)
   - `test-data/pdfs/quality_complaints/vial_contamination_sepsis.pdf` (Quality defect report with embedded image, 2 pages)
   - `test-data/pdfs/quality_complaints/pqc_cracked_collar_report.pdf` (Defect report, 1 page)

2. **Scanned & Handwritten PDFs (1 asset — 2nd explicitly DEFERRED)**:
   - `test-data/pdfs/scanned_handwritten/clinic_handwritten_note.pdf` (Scanned clinic intake note with handwritten entries, 1 page)
   - *Requirement Status*: 1 completed; 2nd requirement explicitly marked **DEFERRED** in `manifest.json` for synthetic hand-filled paper form.

3. **Published Scientific Literature PDFs (10 assets)**:
   - *Case-Bearing Clinical Articles (8 assets)*:
     - `article_01_cardioril_hepatotoxicity.pdf` (Single case: Drug-induced liver injury, 2 pages)
     - `article_02_neurozap_seizures.pdf` (Single case: Generalized tonic-clonic seizures, 2 pages)
     - `article_03_multicase_series.pdf` (Multi-case series: 3 distinct patient cases A.J., B.L., C.M., 3 pages)
     - `article_06_dermatology_case.pdf` (Single case: Severe cutaneous adverse reaction, 2 pages)
     - `article_07_oncology_case.pdf` (Single case: Immune checkpoint myocarditis, 2 pages)
     - `article_08_cardiology_buried_case.pdf` (Buried case: Case details nested within cohort background, 3 pages)
     - `article_09_pediatric_case.pdf` (Single case: Pediatric anaphylaxis, 2 pages)
     - `article_10_geriatric_polypharmacy.pdf` (Single case: Geriatric fall and subdural hematoma, 2 pages)
   - *Non-Reportable Negative Controls (2 assets)*:
     - `article_04_preclinical_in_vitro.pdf` (Preclinical animal/in-vitro metabolism study in rats; zero clinical patients, 2 pages)
     - `article_05_meta_analysis_sglt2.pdf` (Systematic review and meta-analysis of 34 RCTs; aggregate statistics only, 2 pages)

4. **Non-English PDFs (3 assets)**:
   - `test-data/pdfs/non_english/aemps_notificacion_es.pdf` (Spanish AEMPS adverse reaction form: Rabdomiólisis, 2 pages)
   - `test-data/pdfs/non_english/bfarm_uaw_bericht_de.pdf` (German BfArM UAW report: Akutes Angioödem, 2 pages)
   - `test-data/pdfs/non_english/spanish_case_report.pdf` (Spanish clinical report, 2 pages)

5. **Standalone Image Evidence Assets (2 assets)**:
   - `test-data/pdfs/quality_complaints/contaminated_vial_photo.jpg` (Photograph of defective Cefatox vial with particulate matter)
   - `test-data/pdfs/scanned_handwritten/handwritten_clinic_photo.jpg` (Photograph of handwritten intake document)

---

## 3. Ground Truth Methodology

### 3.1 Ground Truth Independence

A foundational principle of this project is that **ground truth is created independently of model output**. Under no circumstances is AI output used to generate or modify ground-truth benchmarks.

```
Physical Synthetic Source Files (.eml, .pdf, .jpg)
                   ↓
Human & Clinical Source Inspection
                   ↓
Canonical Expected Truth Established
                   ↓
benchmark.json (Version 3.0.0)
                   ↓
AI Model Prediction (Live Gemini Flash)
                   ↓
Automated Comparison & Scoring (eval_benchmark.py)
                   ↓
Objective Metrics (Precision, Recall, F1, Latency)
```

### 3.2 Canonical Meaning vs. Acceptable Formulations

Ground truth distinguishes between exact canonical concepts and acceptable semantic formulations to avoid brittle evaluation failures. For example:
- **Canonical Adverse Event**: `"Drug-induced liver injury (DILI)"`
- **Acceptable Synonyms**: `["acute toxic hepatitis", "acute hepatocellular injury", "hepatic necrosis", "drug-induced liver injury", "dili"]`
- **Canonical Reporter**: `"Dr. Sarah Jenkins"`
- **Acceptable Synonyms**: `["Sarah Jenkins, MD", "Dr. S. Jenkins", "Sarah Jenkins"]`

### 3.3 Strict "Not stated" Policy

If a clinical or administrative attribute is not explicitly mentioned in the physical source document:
- The ground-truth value is strictly `"Not stated"`.
- It must **never** be inferred, guessed, or extrapolated from typical clinical practices.
- Example: If an email mentions `"Cardioril 10 mg"` without specifying daily dosing, the dose is `"10 mg"`, but frequency is `"Not stated"`.

---

## 4. Logical Benchmark Inventory (27 Canonical Cases)

The benchmark indexes 27 logical cases spanning all required clinical and regulatory scenarios:

| Case ID | Source File | Category | Focus / Clinical Scenario |
| :--- | :--- | :--- | :--- |
| `CASE-01` | `email_01.eml` | Safety Report (ICSR) | Cardioril 20 mg - Acute DILI / Hepatic Injury |
| `CASE-02` | `email_02.eml` | Safety Report (ICSR) | Neurozap 500 mg - Status Epilepticus (Scanned Note) |
| `CASE-03` | `email_03.eml` | Safety Report (ICSR) | PulmoClear 10 mg - Acute Bronchospasm |
| `CASE-04` | `email_04.eml` | Multi-Label (ICSR + PQC) | Cefatox Contaminated Vial + Septic Shock (Defect Photo) |
| `CASE-05` | `email_05.eml` | Safety Report (ICSR) | OncoTax 100 mg - Severe Peripheral Neuropathy |
| `CASE-06` | `email_06.eml` | Safety Report (ICSR) | Cardioril 20 mg - Multi-organ failure / ICU admission |
| `CASE-07` | `email_07.eml` | Quality Complaint (PQC) | DermaCool Cream - Defective cracked pump collar (No AE) |
| `CASE-08` | `email_08.eml` | Quality Complaint (PQC) | RespiraClear Inhaler - Broken canister nozzle (No AE) |
| `CASE-09` | `email_09.eml` | Info Request (MI) | Glucotear - Crushing tablets for NG-tube administration |
| `CASE-10` | `email_10.eml` | Not Relevant | Commercial BioTech Pharma Summit 2026 sponsorship spam |
| `CASE-11` | `email_11.eml` | Info Request (MI) | Cardioril 20 mg - Dosing adjustments in renal impairment |
| `PDF-DIG-01` | `cioms_form_MK_Cardioril.pdf` | Safety Report (ICSR) | Digital CIOMS-I form: Jaundice, elevated ALT/AST |
| `PDF-DIG-02` | `fda_3500a_JR_Neurozap.pdf` | Safety Report (ICSR) | Digital FDA 3500A form: Refractory tonic-clonic seizures |
| `PDF-DIG-03` | `cioms_form_dili_acute.pdf` | Safety Report (ICSR) | Digital CIOMS-I form: Acute liver failure |
| `PDF-DIG-04` | `fda_3500a_anaphylaxis.pdf` | Safety Report (ICSR) | Digital FDA 3500A form: Severe anaphylactic shock |
| `PDF-PQC-01` | `vial_contamination_sepsis.pdf`| Quality Complaint (PQC) | Cefatox vial particulate matter report |
| `PDF-PQC-02` | `pqc_cracked_collar_report.pdf`| Quality Complaint (PQC) | DermaCool lot packaging defect report |
| `PDF-SCAN-01`| `clinic_handwritten_note.pdf` | Safety Report (ICSR) | Scanned clinical encounter note with handwriting |
| `PDF-SCAN-02`| *(None)* | Safety Report (ICSR) | **DEFERRED** (Reserved for synthetic hand-filled form) |
| `LIT-01` | `article_01_cardioril_hepatotoxicity.pdf` | Literature (Single Case) | Published case report: Acute drug-induced liver injury |
| `LIT-02` | `article_02_neurozap_seizures.pdf` | Literature (Single Case) | Published case report: De-novo status epilepticus |
| `LIT-03` | `article_03_multicase_series.pdf` | Literature (Multi-Case) | Published case series: 3 patients (A.J., B.L., C.M.) |
| `LIT-04` | `article_04_preclinical_in_vitro.pdf` | Literature (Negative Control)| Preclinical animal study in rats (Non-reportable) |
| `LIT-05` | `article_05_meta_analysis_sglt2.pdf` | Literature (Negative Control)| Systematic review & meta-analysis (Non-reportable) |
| `LIT-06` | `article_06_dermatology_case.pdf` | Literature (Single Case) | Published case report: Stevens-Johnson Syndrome |
| `LIT-07` | `article_07_oncology_case.pdf` | Literature (Single Case) | Published case report: Immune-mediated myocarditis |
| `LIT-08` | `article_08_cardiology_buried_case.pdf` | Literature (Buried Case) | Buried patient case within 40-patient cohort |
| `PDF-LANG-01`| `aemps_notificacion_es.pdf` | Safety Report (Spanish) | Spanish AEMPS form: Rabdomiólisis severa |
| `PDF-LANG-02`| `bfarm_uaw_bericht_de.pdf` | Safety Report (German) | German BfArM form: Akutes Angioödem |

---

## 5. Explicitly Deferred Requirement

- **Requirement**: Scanned/Handwritten PDFs >= 2.
- **Current Count**: 1 completed (`clinic_handwritten_note.pdf`).
- **Status**: **DEFERRED**.
- **Justification**: The second scanned/handwritten document is intentionally reserved for live user physical form evaluation. It is explicitly recorded in `manifest.json` with status `"DEFERRED"` and reason `"Reserved for final synthetic hand-filled paper form"`. The dataset is NOT claimed as 100% requirement-complete while this item remains deferred.
