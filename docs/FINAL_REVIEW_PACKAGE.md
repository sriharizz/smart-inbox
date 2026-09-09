# CLINICAL REVIEWER WORKSPACE: 12-CASE DOSSIER PACKAGE

> **Document Purpose:** Complete deterministic capture of the reviewer-facing content presented by the Angular Case Workspace for CASE-01 through CASE-12. All values, summaries, section parameters, evidence citations, and human-review flags reflect the exact rendered state of the active reviewer interface.

---

## CASE-01

### 1. Case Identification
- **Case ID:** `CASE-001`
- **Email Subject:** URGENT: Individual Case Safety Report (ICSR) - Suspect DILI with Cardioril (Pt M.K.)
- **Sender:** Dr. Sarah Jenkins, MD (clinevo.test.inbox12@gmail.com)
- **Date:** Thu Nov 13 01:52:10 IST 2025
- **Attachment Filenames:** cioms_form_MK_Cardioril.pdf
- **Primary Category:** `Safety Report (ICSR)`
- **All Categories / Labels:** ['Safety Report (ICSR)']
- **Multi-Label Status:** `No`
- **AI Confidence:** `100%`
- **Clinical Urgency / Clock:** `EXPEDITED`

### 2. Reviewer-Facing Summary
> This regulatory triage evaluation concerns an urgent spontaneous Individual Case Safety Report (ICSR) submitted by Dr. Sarah Jenkins, a gastroenterologist at MetroHealth Medical Center. The report describes a serious adverse event of acute drug-induced liver injury (DILI) in a 58-year-old female patient (initials M.K.) associated with the use of Cardioril (cardioril hydrochloride) 20 mg once daily. The patient initiated Cardioril therapy on October 15, 2025, for the treatment of refractory essential hypertension. Approximately 24 days later, on November 8, 2025, the patient presented with progressive fatigue, anorexia, severe generalized pruritus, dark urine, and painless clinical jaundice. Laboratory evaluation on November 10, 2025, revealed critical transaminitis with an ALT of 540 U/L (>9x ULN), AST of 420 U/L (>10x ULN), and severe hyperbilirubinemia with a total bilirubin of 4.8 mg/dL. These laboratory findings satisfy the criteria for Hy's Law, which is highly predictive of severe, potentially fatal drug-induced hepatotoxicity. Due to the severity of the clinical presentation, the patient was emergently admitted to the MetroHealth Gastroenterology Service on November 10, 2025. Diagnostic workup successfully ruled out alternative etiologies, as viral hepatitis serologies (A, B, C, and E) were non-reactive, and an abdominal ultrasound showed normal liver parenchyma without biliary obstruction. Cardioril was permanently discontinued upon admission, and the patient's transaminases have since begun to trend downward, indicating a positive dechallenge. Concomitant medications included long-term metformin and amlodipine, with no reported use of hepatotoxic over-the-counter agents, acetaminophen, or herbal supplements. The suspect product is identified as Cardioril 20 mg, Lot #CR-2025-0981, with an expiration date of August 2027. This case meets regulatory seriousness criteria due to inpatient hospitalization and representing an otherwise medically important condition. As a serious, unexpected suspected adverse reaction, this case requires expedited 15-day regulatory reporting to global health authorities. It is recommended that the Pharmacovigilance department immediately process this ICSR, assign the manufacturer control number CR-2025-US-00891, and submit the completed CIOMS-I form to the FDA and other relevant regulatory bodies within the mandated timeframe. Follow-up should be initiated with the reporting physician to monitor the patient's complete recovery and obtain final liver function test results.

### 3. Structured Review Content
#### Section: Patient Demographics & Medical History (Scope: `ICSR` | Type: `GRID`)
| Parameter | Rendered Value | Status |
|:---|:---|:---|
| Patient Identifier | M.K. | `CONFIRMED` |
| Date of Birth | 14-MAY-1967 | `CONFIRMED` |
| Patient Age | 58 YRS | `CONFIRMED` |
| Sex / Gender | FEMALE | `CONFIRMED` |
| Patient Weight | 68 kg (150 lbs) | `CONFIRMED` |
| Country | USA | `CONFIRMED` |
| Medical History | Essential hypertension (5 yrs), Type 2 diabetes mellitus (4 yrs). No prior history of hepatobiliary disease, jaundice, or ethanol abuse. | `CONFIRMED` |

#### Section: Healthcare Professional & Primary Reporter (Scope: `ICSR` | Type: `GRID`)
| Parameter | Rendered Value | Status |
|:---|:---|:---|
| Reporter Name | Sarah Jenkins, MD, FACP | `CONFIRMED` |
| Qualification / Role | Physician | `CONFIRMED` |
| Medical Specialty | Gastroenterologist | `CONFIRMED` |
| Health Professional | Yes (HCP Confirmed) | `CONFIRMED` |
| Institution / Clinic | MetroHealth Medical Center | `CONFIRMED` |
| Country | USA | `CONFIRMED` |
| Contact Information | (312) 555-0188 | sjenkins@metrohealth-chicago.org | `CONFIRMED` |

#### Section: Suspect Product & Administration Regimen (Scope: `ICSR` | Type: `GRID`)
| Parameter | Rendered Value | Status |
|:---|:---|:---|
| Suspect Product | Cardioril (cardioril hydrochloride) | `CONFIRMED` |
| Dosage Formulation | Tablet (Oral) | `CONFIRMED` |
| Administered Dose | 20 mg once daily (QD) | `CONFIRMED` |
| Dosing Frequency | Once daily (QD) | `CONFIRMED` |
| Route of Administration | Oral | `CONFIRMED` |
| Therapeutic Indication | Refractory Essential Hypertension | `CONFIRMED` |
| Therapy Start Date | 15-OCT-2025 | `CONFIRMED` |
| Therapy Stop Date | 10-NOV-2025 | `CONFIRMED` |
| Treatment Duration | 26 days | `CONFIRMED` |
| Lot / Batch Number | Lot #CR-2025-0981 | `CONFIRMED` |
| Expiration Date | 08/2027 | `CONFIRMED` |
| Action Taken with Drug | Drug permanently withdrawn | `CONFIRMED` |

#### Section: Adverse Event & Seriousness Profile (Scope: `ICSR` | Type: `GRID`)
| Parameter | Rendered Value | Status |
|:---|:---|:---|
| Adverse Reaction | Acute Drug-Induced Liver Injury (DILI) with Jaundice | `CONFIRMED` |
| Reaction Onset Date | 08-NOV-2025 | `CONFIRMED` |
| Clinical Outcome | Recovering with trending decrease in transaminases on serial daily testing. | `CONFIRMED` |
| Dechallenge Outcome | Positive (resolved/improved upon discontinuation) | `CONFIRMED` |
| Rechallenge Outcome | Not stated | `NOT_STATED` |
| Seriousness Criteria | Hospitalization, Medically Significant | `CONFIRMED` |
| Inpatient Hospitalization | Yes (Hospitalized) | `CONFIRMED` |
| Hospital Admission Date | 10-NOV-2025 | `CONFIRMED` |
| Medically Important | Yes (Medically Important) | `CONFIRMED` |

#### Section: Concomitant Medications & Prior Therapy (Scope: `ICSR` | Type: `TABLE`)
| Concomitant Medication | Indication | Dose & Schedule | Therapy Dates |
|:---|:---|:---|:---|
| Not stated | Type 2 Diabetes Mellitus | Not stated | Start: 12-JAN-2021, Ongoing |
| Not stated | Hypertension | Not stated | Start: 05-MAR-2023, Ongoing |

#### Section: Laboratory & Diagnostic Investigations Matrix (Scope: `ICSR` | Type: `TABLE`)
| Test / Parameter | Date | Result | Unit | Normal Range | Interpretation |
|:---|:---|:---|:---|:---|:---|
| Alanine Aminotransferase (ALT / SGPT) | 10-NOV-2025 | 540 | U/L | 7 – 56 | CRITICAL ELEVATION (>9x ULN) |
| Aspartate Aminotransferase (AST / SGOT) | 10-NOV-2025 | 420 | U/L | 10 – 40 | CRITICAL ELEVATION (>10x ULN) |
| Total Bilirubin | 10-NOV-2025 | 4.8 | mg/dL | 0.1 – 1.2 | SEVERE HYPERBILIRUBINEMIA (Hy's Law) |
| Alkaline Phosphatase (ALP) | 10-NOV-2025 | 210 | U/L | 44 – 147 | ELEVATED |
| Serum Creatinine | 10-NOV-2025 | 0.9 | mg/dL | 0.6 – 1.2 | NORMAL |
| Hepatitis A, B, C Serology (IgM, HBsAg, HCV-Ab) | 11-NOV-2025 | Negative | - | Negative | NON-REACTIVE (Viral etiology ruled out) |

#### Section: Clinical Chronological Narrative (Scope: `ICSR` | Type: `NARRATIVE`)
**Narrative Text:**

A 58-year-old female patient with a medical history of essential hypertension (5 years) and type 2 diabetes mellitus (4 years) initiated Cardioril 20 mg once daily on October 15, 2025. On November 8, 2025 (~24 days post-initiation), she presented with progressive fatigue, anorexia, severe generalized pruritus, dark brown urine, and visible scleral icterus with painless clinical jaundice. Outpatient chemistry panel demonstrated profound transaminitis (ALT 540 U/L, AST 420 U/L) and total bilirubin 4.8 mg/dL, meeting Hy's Law criteria. She was emergently admitted to the MetroHealth Gastroenterology Service on November 10, 2025, for acute drug-induced liver injury (DILI). Viral hepatitis panel (anti-HAV IgM, HBsAg, anti-HCV, anti-HEV IgM) was non-reactive. Abdominal ultrasound revealed normal liver parenchyma without biliary ductal dilatation or cholelithiasis. Cardioril was discontinued permanently on admission (November 10, 2025). The patient's outcome is currently recovering with a trending decrease in transaminases on serial daily testing.

#### Section: Regulatory & Manufacturer Processing Metadata (Scope: `ICSR` | Type: `GRID`)
| Parameter | Rendered Value | Status |
|:---|:---|:---|
| Report Classification | Spontaneous | `CONFIRMED` |

### 4. Evidence Shown to Reviewer
| Displayed Fact | Source Document | Page / Location | Anchor Level | Displayed Evidence Snippet |
|:---|:---|:---|:---|:---|
| Patient Identifier: **M.K.** | `cioms_form_MK_Cardioril.pdf` | `Page 1, Block 4` | `LEVEL_1_EXACT_VISUAL` | “1. PATIENT INITIALS M.K.” |
| Date of Birth: **14-MAY-1967** | `cioms_form_MK_Cardioril.pdf` | `Page 1, Structured Table 1` | `LEVEL_2_PAGE_TEXT` | “| 1. PATIENT INITIALS M.K. | 1a. COUNTRY USA |  | 2. DATE OF BIRTH 14-MAY-1967 |  | 2a. AGE 58 YR...” |
| Patient Age: **58 YRS** | `cioms_form_MK_Cardioril.pdf` | `Page 1, Block 7` | `LEVEL_1_EXACT_VISUAL` | “2a. AGE 58 YRS” |
| Sex / Gender: **FEMALE** | `cioms_form_MK_Cardioril.pdf` | `Page 1, Block 8` | `LEVEL_1_EXACT_VISUAL` | “3. SEX FEMALE” |
| Patient Weight: **68 kg (150 lbs)** | `cioms_form_MK_Cardioril.pdf` | `Page 1, Block 9` | `LEVEL_1_EXACT_VISUAL` | “3a. WEIGHT 68 kg (150 lbs)” |
| Patient Country: **USA** | `cioms_form_MK_Cardioril.pdf` | `Page 1, Block 5` | `LEVEL_1_EXACT_VISUAL` | “1a. COUNTRY USA” |
| Reporter Name: **Sarah Jenkins, MD, FACP** | `cioms_form_MK_Cardioril.pdf` | `Page 1, Block 35` | `LEVEL_1_EXACT_VISUAL` | “24a. NAME AND ADDRESS OF REPORTER Sarah Jenkins, MD, FACP Division of Gastroenterology & Hepatolo...” |
| Reporter Qualification: **Physician** | `cioms_form_MK_Cardioril.pdf` | `Page 1, Block 39` | `LEVEL_1_EXACT_VISUAL` | “24e. OCCUPATION / SPECIALTY Physician / Gastroenterologist Tel: (312) 555-0188” |
| Medical Specialty: **Gastroenterologist** | `cioms_form_MK_Cardioril.pdf` | `Page 1, Block 39` | `LEVEL_1_EXACT_VISUAL` | “24e. OCCUPATION / SPECIALTY Physician / Gastroenterologist Tel: (312) 555-0188” |
| Health Professional: **Yes (HCP Confirmed)** | `cioms_form_MK_Cardioril.pdf` | `Page 1, Block 38` | `LEVEL_1_EXACT_VISUAL` | “24d. HEALTH PROFESSIONAL? [X] YES    [   ] NO” |
| Institution / Clinic: **MetroHealth Medical Center** | `cioms_form_MK_Cardioril.pdf` | `Page 1, Block 35` | `LEVEL_1_EXACT_VISUAL` | “24a. NAME AND ADDRESS OF REPORTER Sarah Jenkins, MD, FACP Division of Gastroenterology & Hepatolo...” |
| Country: **USA** | `cioms_form_MK_Cardioril.pdf` | `Page 1, Block 5` | `LEVEL_1_EXACT_VISUAL` | “1a. COUNTRY USA” |
| Contact Information: **(312) 555-0188 | sjenkins@metrohealth-chicago.org** | `cioms_form_MK_Cardioril.pdf` | `Page 1, Block 39` | `LEVEL_1_EXACT_VISUAL` | “24e. OCCUPATION / SPECIALTY Physician / Gastroenterologist Tel: (312) 555-0188” |
| Suspect Product: **Cardioril (cardioril hydrochloride)** | `cioms_form_MK_Cardioril.pdf` | `Page 1, Block 15` | `LEVEL_1_EXACT_VISUAL` | “14. SUSPECT DRUG NAME (Brand & Generic) Cardioril (cardioril hydrochloride)” |
| Dosage Formulation: **Tablet (Oral)** | `cioms_form_MK_Cardioril.pdf` | `Page 1, Block 17` | `LEVEL_1_EXACT_VISUAL` | “16. ROUTE OF ADMIN. Oral (tablet)” |
| Administered Dose: **20 mg once daily (QD)** | `cioms_form_MK_Cardioril.pdf` | `Page 1, Block 16` | `LEVEL_1_EXACT_VISUAL` | “15. DAILY DOSE(S) 20 mg once daily (QD)” |
| Dosing Frequency: **Once daily (QD)** | `cioms_form_MK_Cardioril.pdf` | `Page 1, Block 16` | `LEVEL_1_EXACT_VISUAL` | “15. DAILY DOSE(S) 20 mg once daily (QD)” |
| Route of Administration: **Oral** | `cioms_form_MK_Cardioril.pdf` | `Page 1, Block 17` | `LEVEL_1_EXACT_VISUAL` | “16. ROUTE OF ADMIN. Oral (tablet)” |
| Therapy Start Date: **15-OCT-2025** | `cioms_form_MK_Cardioril.pdf` | `Page 1, Block 19` | `LEVEL_1_EXACT_VISUAL` | “18. THERAPY DATES (start / stop) 15-OCT-2025 to 10-NOV-2025” |
| Therapy Stop Date: **10-NOV-2025** | `cioms_form_MK_Cardioril.pdf` | `Page 1, Block 19` | `LEVEL_1_EXACT_VISUAL` | “18. THERAPY DATES (start / stop) 15-OCT-2025 to 10-NOV-2025” |
| Treatment Duration: **26 days** | `cioms_form_MK_Cardioril.pdf` | `Page 1, Block 20` | `LEVEL_1_EXACT_VISUAL` | “19. THERAPY DURATION 26 days” |
| Product Lot / Batch: **Lot #CR-2025-0981** | `cioms_form_MK_Cardioril.pdf` | `Page 1, Block 21` | `LEVEL_1_EXACT_VISUAL` | “20. LOT / BATCH NUMBER Lot #CR-2025-0981 (Exp: 08/2027)” |
| Action Taken with Drug: **Drug permanently withdrawn** | `cioms_form_MK_Cardioril.pdf` | `Page 1, Block 22` | `LEVEL_1_EXACT_VISUAL` | “21. ACTION TAKEN [X] Drug permanently withdrawn” |
| Adverse Reaction: **Acute Drug-Induced Liver Injury (DILI) with Jaundice** | `imap_18.eml` | `Email Body, Paragraph 2` | `LEVEL_1_EXACT_VISUAL` | “I am submitting an urgent spontaneous adverse drug reaction report concerning a 58-year-old femal...” |
| Seriousness Criteria: **Hospitalization, Medically Significant** | `cioms_form_MK_Cardioril.pdf` | `Page 1, Structured Table 1` | `LEVEL_2_PAGE_TEXT` | “| 1. PATIENT INITIALS M.K. | 1a. COUNTRY USA |  | 2. DATE OF BIRTH 14-MAY-1967 |  | 2a. AGE 58 YR...” |
| Inpatient Hospitalization: **Yes (Hospitalized)** | `cioms_form_MK_Cardioril.pdf` | `Page 1, Block 12` | `LEVEL_1_EXACT_VISUAL` | “8–12. CHECK ALL APPROPRIATE TO ADVERSE REACTION: [   ] PATIENT DIED                              ...” |
| Hospital Admission Date: **10-NOV-2025** | `cioms_form_MK_Cardioril.pdf` | `Page 1, Block 12` | `LEVEL_1_EXACT_VISUAL` | “8–12. CHECK ALL APPROPRIATE TO ADVERSE REACTION: [   ] PATIENT DIED                              ...” |
| Medically Important: **Yes (Medically Important)** | `cioms_form_MK_Cardioril.pdf` | `Page 1, Block 12` | `LEVEL_1_EXACT_VISUAL` | “8–12. CHECK ALL APPROPRIATE TO ADVERSE REACTION: [   ] PATIENT DIED                              ...” |
| Dechallenge Outcome: **Positive (resolved/improved upon discontinuation)** | `imap_18.eml` | `Page 1, Section I` | `LEVEL_3_SNIPPET_ONLY` | “[ X ] INVOLVED OR PROLONGED INPATIENT HOSPITALIZATION (Admitted: 10-NOV-2025) ... [ X ] OTHER MED...” |

### 5. Reviewer Flags / Warnings
- ✓ **Clean Processing State:** Structural and evidence-integrity checks passed. No conflicting evidence, handwriting ambiguities, or unstated critical parameters detected.
- **Validation Gating Status:** `READY_FOR_REVIEW`

### 6. Human Review State
- **Current Intake Status:** `TRIAGED`
- **Review Urgency Priority:** `EXPEDITED`
- **Confidence Score:** `100%`
- **Available Reviewer Primary Actions:** `[✓ Confirm AI Case]`, `[✎ Override / Edit]`, `[🚩 Flag for Escalation]`

### 7. Source Reference Section
- **Original Email File:** `test-data/emails/email_01.eml`
- **Original PDF Attachment(s):** `test-data/pdfs/.../cioms_form_MK_Cardioril.pdf`

**Source Email Excerpt:**
```text
Dear Pharmacovigilance Team,
I am submitting an urgent spontaneous adverse drug reaction report concerning a 58-year-old female patient (M.K.) under my care who developed acute drug-induced liver injury (DILI) and jaundice following treatment with Cardioril 20 mg once daily.
The patient required acute hospital admission on November 10, 2025 due to significantly elevated transaminases (>9x ULN) and hyperbilirubinemia (Total Bili: 4.8 mg/dL) meeting Hy's law criteria. Viral hepatitis serologies and abdominal ultrasound were negative for biliary obstruction.
Cardioril was promptly discontinued on admission, and liver transaminases are beginning to trend down. Please find attached the completed official CIOMS-I reporting form along with the structured hepatic chemistry laboratory panel for your expedited safety evaluation.
Please acknowledge receipt of this regulatory submission.
Sincerely,
...
```

**Source PDF Excerpt (`cioms_form_MK_Cardioril.pdf`):**
```text
CIOMS FORM I
SUSPECT ADVERSE REACTION REPORT
Council for International Organizations of Medical Sciences (CIOMS) — Standard Reporting Form
I. REACTION INFORMATION
1. PATIENT INITIALS
M.K.
1a. COUNTRY
USA
...
```

---

## CASE-02

### 1. Case Identification
- **Case ID:** `CASE-002`
- **Email Subject:** URGENT: Adverse Drug Event Report - Acute Anaphylaxis s/p InjectaPen (Pt Jane Doe)
- **Sender:** Dr. A. Peterson, MD (clinevo.test.inbox12@gmail.com)
- **Date:** Mon Dec 11 02:00:00 IST 2023
- **Attachment Filenames:** urgent_care_intake_handwritten.pdf
- **Primary Category:** `Safety Report (ICSR)`
- **All Categories / Labels:** ['Safety Report (ICSR)']
- **Multi-Label Status:** `No`
- **AI Confidence:** `100%`
- **Clinical Urgency / Clock:** `EXPEDITED`

### 2. Reviewer-Facing Summary
> This urgent medical communication originates from Dr. A. Peterson, an Emergency Department physician at St. Mary's General Hospital, regarding a serious adverse drug reaction. A 33-year-old female patient, Jane Doe, developed severe acute anaphylactic shock within 20 minutes of self-administering the suspect drug InjectaPen. The clinical presentation included life-threatening manifestations such as generalized urticaria, marked lip and perioral angioedema, inspiratory stridor, and profound hypotension requiring emergency resuscitation. Immediate interventions administered at the bedside included intramuscular epinephrine, high-flow supplemental oxygen, and intravenous fluid resuscitation, followed by an acute care admission. An attached emergency intake and triage record provides documented corroboration of the clinical events. All four core data elements for an Individual Case Safety Report (ICSR)—identifiable patient, identifiable reporter, suspect medicinal product, and a serious adverse event outcome—are fully satisfied. The case represents a high-priority safety signal requiring immediate regulatory triage, expedited intake into the global safety database, and subsequent medical review for potential label updates or regulatory reporting. No product quality complaints or standard medical information inquiries were reported in this communication.

### 3. Structured Review Content
#### Section: Patient Demographics & Medical History (Scope: `ICSR` | Type: `GRID`)
| Parameter | Rendered Value | Status |
|:---|:---|:---|
| Patient Identifier | Jane Doe | `CONFIRMED` |
| Date of Birth | 05/18/1990 | `CONFIRMED` |
| Patient Age | 33 | `CONFIRMED` |
| Sex / Gender | F | `CONFIRMED` |
| Patient Weight | Not stated | `NOT_STATED` |
| Country | USA | `CONFIRMED` |
| Medical History | Not stated | `NOT_STATED` |

#### Section: Healthcare Professional & Primary Reporter (Scope: `ICSR` | Type: `GRID`)
| Parameter | Rendered Value | Status |
|:---|:---|:---|
| Reporter Name | Dr. A. Peterson, MD | `CONFIRMED` |
| Qualification / Role | Physician | `CONFIRMED` |
| Medical Specialty | Attending Emergency Physician | `CONFIRMED` |
| Health Professional | Yes (HCP Confirmed) | `CONFIRMED` |
| Institution / Clinic | St. Mary's General Hospital, Emergency Department | `CONFIRMED` |
| Country | USA | `CONFIRMED` |
| Contact Information | a.peterson@stmarys-hospital.org | `CONFIRMED` |

#### Section: Suspect Product & Administration Regimen (Scope: `ICSR` | Type: `GRID`)
| Parameter | Rendered Value | Status |
|:---|:---|:---|
| Suspect Product | InjectaPen | `CONFIRMED` |
| Administered Dose | Not stated | `NOT_STATED` |
| Dosing Frequency | Not stated | `NOT_STATED` |
| Route of Administration | Subcutaneous / self-injection | `CONFIRMED` |
| Therapeutic Indication | Not stated | `NOT_STATED` |
| Therapy Start Date | 10-DEC-2023 | `CONFIRMED` |
| Treatment Duration | Single acute event | `CONFIRMED` |
| Lot / Batch Number | Not stated | `NOT_STATED` |
| Expiration Date | Not stated | `NOT_STATED` |

#### Section: Adverse Event & Seriousness Profile (Scope: `ICSR` | Type: `GRID`)
| Parameter | Rendered Value | Status |
|:---|:---|:---|
| Adverse Reaction | Acute anaphylaxis, generalized urticaria, facial and perioral angioedema, inspiratory stridor, profound hypotension | `CONFIRMED` |
| Reaction Onset Date | 10-DEC-2023 | `CONFIRMED` |
| Clinical Outcome | Recovering / admitted to emergency unit | `CONFIRMED` |
| Dechallenge Outcome | Not applicable - single acute dose. | `CONFIRMED` |
| Rechallenge Outcome | Not done / not stated. | `CONFIRMED` |
| Seriousness Criteria | Hospitalization, Life-threatening, Medically Significant | `CONFIRMED` |
| Inpatient Hospitalization | Yes (Hospitalized) | `CONFIRMED` |
| Hospital Admission Date | 10-DEC-2023 | `CONFIRMED` |
| Life Threatening | Yes (Life Threatening) | `CONFIRMED` |
| Medically Important | Yes (Medically Important) | `CONFIRMED` |

#### Section: Clinical Chronological Narrative (Scope: `ICSR` | Type: `NARRATIVE`)
**Narrative Text:**

On 10-DEC-2023 at 14:35, a 33-year-old female patient (Jane Doe) presented to the Emergency Department at St. Mary's General Hospital with acute onset of generalized hives, facial swelling, and difficulty breathing approximately 20 minutes after a subcutaneous self-injection of InjectaPen. Vital signs on arrival revealed a blood pressure of 85/50 mmHg, heart rate of 128 bpm, and oxygen saturation of 91% on room air. Clinical findings included acute anaphylaxis (Grade 3), generalized urticaria/hives, facial and perioral angioedema, inspiratory stridor, and profound hypotension. Emergency management was promptly administered, including Epinephrine 0.3 mg IM, high-flow oxygen, IV fluid resuscitation, and emergency unit admission. The patient is currently recovering in the emergency unit. The dose and lot number of InjectaPen were unrecorded at bedside triage.

#### Section: Regulatory & Manufacturer Processing Metadata (Scope: `ICSR` | Type: `GRID`)
| Parameter | Rendered Value | Status |
|:---|:---|:---|
| Report Classification | Initial | `CONFIRMED` |

### 4. Evidence Shown to Reviewer
| Displayed Fact | Source Document | Page / Location | Anchor Level | Displayed Evidence Snippet |
|:---|:---|:---|:---|:---|
| Patient Identifier: **Jane Doe** | `imap_19.eml` | `Email Body, Paragraph 2` | `LEVEL_1_EXACT_VISUAL` | “I am urgently submitting an initial adverse event report for a 33-year-old female patient (Jane D...” |
| Date of Birth: **05/18/1990** | `imap_19.eml` | `Email Body, Paragraph 2` | `LEVEL_1_EXACT_VISUAL` | “I am urgently submitting an initial adverse event report for a 33-year-old female patient (Jane D...” |
| Patient Age: **33** | `imap_19.eml` | `Email Body, Paragraph 2` | `LEVEL_1_EXACT_VISUAL` | “I am urgently submitting an initial adverse event report for a 33-year-old female patient (Jane D...” |
| Sex / Gender: **F** | `imap_19.eml` | `Email Body, Paragraph 2` | `LEVEL_1_EXACT_VISUAL` | “I am urgently submitting an initial adverse event report for a 33-year-old female patient (Jane D...” |
| Patient Country: **USA** | `imap_19.eml` | `Page 1` | `LEVEL_3_SNIPPET_ONLY` | “Patient: Jane Doe DOB: 05/18/1990 (age 33) Sex: F” |
| Reporter Name: **Dr. A. Peterson, MD** | `imap_19.eml` | `Email Header` | `LEVEL_1_EXACT_VISUAL` | “From: Dr. A. Peterson, MD <clinevo.test.inbox12@gmail.com> Date: Sun, 10 Dec 2023 15:30:00 -0500 ...” |
| Reporter Qualification: **Physician** | `imap_19.eml` | `Page 1` | `LEVEL_3_SNIPPET_ONLY` | “Reporter: Dr. A. Peterson, MD Attending Emergency Physician St. Mary's General Hospital Emergency...” |
| Medical Specialty: **Attending Emergency Physician** | `imap_19.eml` | `Email Body, Paragraph 2` | `LEVEL_1_EXACT_VISUAL` | “I am urgently submitting an initial adverse event report for a 33-year-old female patient (Jane D...” |
| Health Professional: **Yes (HCP Confirmed)** | `imap_19.eml` | `Page 1` | `LEVEL_3_SNIPPET_ONLY` | “Reporter: Dr. A. Peterson, MD Attending Emergency Physician St. Mary's General Hospital Emergency...” |
| Institution / Clinic: **St. Mary's General Hospital, Emergency Department** | `imap_19.eml` | `Email Body, Paragraph 5` | `LEVEL_1_EXACT_VISUAL` | “Sincerely, Dr. A. Peterson, MD Emergency Department, St. Mary's General Hospital NPI: 9876543210 ...” |
| Country: **USA** | `imap_19.eml` | `Page 1` | `LEVEL_3_SNIPPET_ONLY` | “Reporter: Dr. A. Peterson, MD Attending Emergency Physician St. Mary's General Hospital Emergency...” |
| Contact Information: **a.peterson@stmarys-hospital.org** | `imap_19.eml` | `Email Body, Paragraph 5` | `LEVEL_1_EXACT_VISUAL` | “Sincerely, Dr. A. Peterson, MD Emergency Department, St. Mary's General Hospital NPI: 9876543210 ...” |
| Suspect Product: **InjectaPen** | `imap_19.eml` | `Email Header` | `LEVEL_1_EXACT_VISUAL` | “From: Dr. A. Peterson, MD <clinevo.test.inbox12@gmail.com> Date: Sun, 10 Dec 2023 15:30:00 -0500 ...” |
| Route of Administration: **Subcutaneous / self-injection** | `imap_19.eml` | `Email Body, Paragraph 2` | `LEVEL_1_EXACT_VISUAL` | “I am urgently submitting an initial adverse event report for a 33-year-old female patient (Jane D...” |
| Therapy Start Date: **10-DEC-2023** | `imap_19.eml` | `Page 1` | `LEVEL_3_SNIPPET_ONLY` | “Suspect Product: InjectaPen Dose: Not stated Route: Subcutaneous / self-injection Frequency: Not ...” |
| Treatment Duration: **Single acute event** | `imap_19.eml` | `Email Header` | `LEVEL_1_EXACT_VISUAL` | “From: Dr. A. Peterson, MD <clinevo.test.inbox12@gmail.com> Date: Sun, 10 Dec 2023 15:30:00 -0500 ...” |
| Adverse Reaction: **Acute anaphylaxis, generalized urticaria, facial and perioral angioedema, inspiratory stridor, profound hypotension** | `imap_19.eml` | `Email Body, Paragraph 3` | `LEVEL_1_EXACT_VISUAL` | “Patient presented with generalized urticaria, marked lip and perioral angioedema, inspiratory str...” |
| Clinical Outcome: **Recovering / admitted to emergency unit** | `imap_19.eml` | `Email Body, Paragraph 3` | `LEVEL_1_EXACT_VISUAL` | “Patient presented with generalized urticaria, marked lip and perioral angioedema, inspiratory str...” |
| Seriousness Criteria: **Hospitalization, Life-threatening, Medically Significant** | `imap_19.eml` | `Page 1` | `LEVEL_3_SNIPPET_ONLY` | “Symptoms/Findings: - Acute anaphylaxis (Grade 3) - Generalized urticaria / hives - Facial and per...” |
| Inpatient Hospitalization: **Yes (Hospitalized)** | `imap_19.eml` | `Page 1` | `LEVEL_3_SNIPPET_ONLY` | “Symptoms/Findings: - Acute anaphylaxis (Grade 3) - Generalized urticaria / hives - Facial and per...” |
| Hospital Admission Date: **10-DEC-2023** | `imap_19.eml` | `Page 1` | `LEVEL_3_SNIPPET_ONLY` | “Symptoms/Findings: - Acute anaphylaxis (Grade 3) - Generalized urticaria / hives - Facial and per...” |
| Life Threatening: **Yes (Life Threatening)** | `imap_19.eml` | `Page 1` | `LEVEL_3_SNIPPET_ONLY` | “Symptoms/Findings: - Acute anaphylaxis (Grade 3) - Generalized urticaria / hives - Facial and per...” |
| Medically Important: **Yes (Medically Important)** | `imap_19.eml` | `Page 1` | `LEVEL_3_SNIPPET_ONLY` | “Symptoms/Findings: - Acute anaphylaxis (Grade 3) - Generalized urticaria / hives - Facial and per...” |
| Dechallenge Outcome: **Not applicable - single acute dose.** | `imap_19.eml` | `Email Header` | `LEVEL_1_EXACT_VISUAL` | “From: Dr. A. Peterson, MD <clinevo.test.inbox12@gmail.com> Date: Sun, 10 Dec 2023 15:30:00 -0500 ...” |
| Rechallenge Outcome: **Not done / not stated.** | `imap_19.eml` | `Page 1` | `LEVEL_3_SNIPPET_ONLY` | “Symptoms/Findings: - Acute anaphylaxis (Grade 3) - Generalized urticaria / hives - Facial and per...” |

### 5. Reviewer Flags / Warnings
- ⚠️ **Critical Field Unstated: Administered Dose** (`MISSING_CRITICAL_FIELD`): Regulatory parameter 'Administered Dose' was omitted from the intake transmission. Anti-hallucination guard verified absence. [Action: *Confirm absence or trigger targeted query*]
- **Validation Gating Status:** `REVIEW_WITH_WARNINGS`

### 6. Human Review State
- **Current Intake Status:** `TRIAGED`
- **Review Urgency Priority:** `EXPEDITED`
- **Confidence Score:** `100%`
- **Available Reviewer Primary Actions:** `[✓ Confirm AI Case]`, `[✎ Override / Edit]`, `[🚩 Flag for Escalation]`

### 7. Source Reference Section
- **Original Email File:** `test-data/emails/email_02.eml`
- **Original PDF Attachment(s):** `test-data/pdfs/.../urgent_care_intake_handwritten.pdf`
- **Original Image Asset(s):** `test-data/pdfs/.../handwritten_clinic_photo.jpg`

**Source Email Excerpt:**
```text
Dear Pharmacovigilance Department,
I am urgently submitting an initial adverse event report for a 33-year-old female patient (Jane Doe, DOB: 05/18/1990) who presented to St. Mary's Emergency Department in severe acute anaphylactic shock 20 minutes following self-injection of InjectaPen.
Patient presented with generalized urticaria, marked lip and perioral angioedema, inspiratory stridor, and profound hypotension (BP 85/50, HR 128). Immediate emergency intervention was initiated: Epinephrine 0.3 mg IM, high-flow oxygen, IV fluid resuscitation, and admission to the emergency unit.
Attached is the photograph of our emergency intake and triage record completed at bedside.
Sincerely,
Dr. A. Peterson, MD
...
```

---

## CASE-03

### 1. Case Identification
- **Case ID:** `CASE-003`
- **Email Subject:** Terrible heart palpitations and dizzy spells after taking Corzapan 10mg
- **Sender:** Emily Watson (clinevo.test.inbox12@gmail.com)
- **Date:** Fri Nov 14 21:44:22 IST 2025
- **Attachment Filenames:** None
- **Primary Category:** `Safety Report (ICSR)`
- **All Categories / Labels:** ['Safety Report (ICSR)']
- **Multi-Label Status:** `No`
- **AI Confidence:** `100%`
- **Clinical Urgency / Clock:** `EXPEDITED`

### 2. Reviewer-Facing Summary
> The incoming communication is an unsolicited spontaneous consumer report submitted by a 42-year-old female patient, Emily Watson, detailing a serious adverse event following the administration of Corzapan 10mg tablets. The patient was prescribed Corzapan four days prior for mild hypertension and work-related anxiety. Approximately one hour after taking her fourth dose on November 13, 2025, she experienced acute, severe heart palpitations, extreme lightheadedness, diaphoresis, near-syncope, chest tightness, and dyspnea lasting nearly two hours. A smartwatch recorded a resting pulse rate of 154 bpm during the episode. The patient sought medical evaluation from her family physician, Dr. Robert Hayes at Denver Family Medicine, who diagnosed an acute drug-induced tachycardia and palpitations episode and instructed her to discontinue the medication immediately. The patient reports ongoing fatigue on the day following the event, while her heart rate has normalized to 78 bpm. Although the patient discarded the prescription bottle and cannot provide a specific lot or batch number, the product was dispensed by a known pharmacy location in Denver, Colorado. There is no indication of any physical product defect, rendering this strictly a pharmacovigilance safety case rather than a product quality complaint. The case involves an unlabeled or known class adverse reaction of significant clinical severity requiring expedited intake and processing into the global safety database. Immediate regulatory action mandates case logging, medical review by a safety physician, and downstream reporting to health authorities in accordance with standard operating procedures and regulatory timelines.

### 3. Structured Review Content
#### Section: Patient Demographics & Medical History (Scope: `ICSR` | Type: `GRID`)
| Parameter | Rendered Value | Status |
|:---|:---|:---|
| Patient Identifier | Emily Watson | `CONFIRMED` |
| Patient Age | 42 years old | `CONFIRMED` |
| Sex / Gender | Female | `CONFIRMED` |
| Patient Weight | Not stated | `NOT_STATED` |
| Country | USA | `CONFIRMED` |
| Medical History | Mild hypertension, work-related anxiety | `CONFIRMED` |

#### Section: Healthcare Professional & Primary Reporter (Scope: `ICSR` | Type: `GRID`)
| Parameter | Rendered Value | Status |
|:---|:---|:---|
| Reporter Name | Emily Watson | `CONFIRMED` |
| Qualification / Role | Consumer / Patient | `CONFIRMED` |
| Health Professional | Yes (HCP Confirmed) | `CONFIRMED` |
| Institution / Clinic | Not stated | `NOT_STATED` |
| Country | USA | `CONFIRMED` |
| Contact Information | emily.watson92@consumer-mail.com / (303) 555-0192 | `CONFIRMED` |

#### Section: Suspect Product & Administration Regimen (Scope: `ICSR` | Type: `GRID`)
| Parameter | Rendered Value | Status |
|:---|:---|:---|
| Suspect Product | Corzapan | `CONFIRMED` |
| Dosage Formulation | Tablets | `CONFIRMED` |
| Administered Dose | 10mg | `CONFIRMED` |
| Dosing Frequency | Not stated | `NOT_STATED` |
| Route of Administration | Not stated | `NOT_STATED` |
| Therapeutic Indication | Mild hypertension and work-related anxiety | `CONFIRMED` |
| Therapy Start Date | Four days prior to report (circa November 10, 2025) | `CONFIRMED` |
| Therapy Stop Date | November 13, 2025 | `CONFIRMED` |
| Treatment Duration | 4 days | `CONFIRMED` |
| Lot / Batch Number | Not stated | `NOT_STATED` |
| Expiration Date | Not stated | `NOT_STATED` |
| Action Taken with Drug | Drug withdrawn / stopped | `CONFIRMED` |

#### Section: Adverse Event & Seriousness Profile (Scope: `ICSR` | Type: `GRID`)
| Parameter | Rendered Value | Status |
|:---|:---|:---|
| Adverse Reaction | Acute drug-induced tachycardia and palpitations | `CONFIRMED` |
| Reaction Onset Date | November 13, 2025 | `CONFIRMED` |
| Clinical Outcome | Recovering / persisting fatigue | `CONFIRMED` |
| Dechallenge Outcome | Positive (resolved/improved upon discontinuation) | `CONFIRMED` |
| Rechallenge Outcome | Not stated | `NOT_STATED` |
| Seriousness Criteria | Medically Significant | `CONFIRMED` |
| Inpatient Hospitalization | No | `CONFIRMED` |
| Medically Important | Yes (Medically Important) | `CONFIRMED` |

#### Section: Laboratory & Diagnostic Investigations Matrix (Scope: `ICSR` | Type: `TABLE`)
| Test / Parameter | Date | Result | Unit | Normal Range | Interpretation |
|:---|:---|:---|:---|:---|:---|
| Resting pulse (Smartwatch) | November 13, 2025 | 154 | bpm | Not stated | Elevated during acute event |
| Heart rate | November 14, 2025 | 78 | bpm | Not stated | Calmed down |

#### Section: Clinical Chronological Narrative (Scope: `ICSR` | Type: `NARRATIVE`)
**Narrative Text:**

A 42-year-old female consumer experienced acute heart palpitations, lightheadedness, cold sweat, near-syncope, chest tightness, and shortness of breath approximately one hour after taking her fourth dose of Corzapan 10mg tablets on November 13, 2025. Her smartwatch recorded a resting pulse of 154 bpm. She was evaluated by Dr. Robert Hayes at Denver Family Medicine, who diagnosed acute drug-induced tachycardia and palpitations and instructed her to immediately discontinue the medication. The patient stopped Corzapan and her symptoms improved, though she experienced residual fatigue the following day with her heart rate returning to 78 bpm.

#### Section: Regulatory & Manufacturer Processing Metadata (Scope: `ICSR` | Type: `GRID`)
| Parameter | Rendered Value | Status |
|:---|:---|:---|
| Report Classification | Spontaneous | `CONFIRMED` |

### 4. Evidence Shown to Reviewer
| Displayed Fact | Source Document | Page / Location | Anchor Level | Displayed Evidence Snippet |
|:---|:---|:---|:---|:---|
| Patient Identifier: **Emily Watson** | `imap_20.eml` | `Patient Information Section` | `LEVEL_1_EXACT_VISUAL` | “Name: Emily Watson Age: 42 years old Sex: Female Location: Denver, Colorado, USA” |
| Patient Age: **42 years old** | `imap_20.eml` | `Patient Information Section` | `LEVEL_1_EXACT_VISUAL` | “Name: Emily Watson Age: 42 years old Sex: Female Location: Denver, Colorado, USA” |
| Sex / Gender: **Female** | `imap_20.eml` | `Patient Information Section` | `LEVEL_1_EXACT_VISUAL` | “Name: Emily Watson Age: 42 years old Sex: Female Location: Denver, Colorado, USA” |
| Patient Country: **USA** | `imap_20.eml` | `Patient Information Section` | `LEVEL_1_EXACT_VISUAL` | “Name: Emily Watson Age: 42 years old Sex: Female Location: Denver, Colorado, USA” |
| Reporter Name: **Emily Watson** | `imap_20.eml` | `Email Body, Paragraph 6` | `LEVEL_1_EXACT_VISUAL` | “Patient Information: Name: Emily Watson Age: 42 years old Sex: Female Location: Denver, Colorado,...” |
| Reporter Qualification: **Consumer / Patient** | `imap_20.eml` | `Email Header & Patient Information Section` | `LEVEL_3_SNIPPET_ONLY` | “From: Emily Watson <clinevo.test.inbox12@gmail.com> Email: emily.watson92@consumer-mail.com” |
| Health Professional: **Yes (HCP Confirmed)** | `imap_20.eml` | `Email Header & Patient Information Section` | `LEVEL_3_SNIPPET_ONLY` | “From: Emily Watson <clinevo.test.inbox12@gmail.com> Email: emily.watson92@consumer-mail.com” |
| Country: **USA** | `imap_20.eml` | `Email Body, Paragraph 6` | `LEVEL_1_EXACT_VISUAL` | “Patient Information: Name: Emily Watson Age: 42 years old Sex: Female Location: Denver, Colorado,...” |
| Contact Information: **emily.watson92@consumer-mail.com / (303) 555-0192** | `imap_20.eml` | `Email Body, Paragraph 6` | `LEVEL_1_EXACT_VISUAL` | “Patient Information: Name: Emily Watson Age: 42 years old Sex: Female Location: Denver, Colorado,...” |
| Suspect Product: **Corzapan** | `imap_20.eml` | `Email Header` | `LEVEL_1_EXACT_VISUAL` | “From: Emily Watson <clinevo.test.inbox12@gmail.com> Date: Fri, 14 Nov 2025 09:14:22 -0700 Subject...” |
| Dosage Formulation: **Tablets** | `imap_20.eml` | `Email Body, Paragraph 2` | `LEVEL_1_EXACT_VISUAL` | “I am writing this email to report a really scary reaction I just experienced after taking Corzapa...” |
| Administered Dose: **10mg** | `imap_20.eml` | `Email Header` | `LEVEL_1_EXACT_VISUAL` | “From: Emily Watson <clinevo.test.inbox12@gmail.com> Date: Fri, 14 Nov 2025 09:14:22 -0700 Subject...” |
| Therapy Start Date: **Four days prior to report (circa November 10, 2025)** | `imap_20.eml` | `Email Body, Paragraph 2` | `LEVEL_1_EXACT_VISUAL` | “I am writing this email to report a really scary reaction I just experienced after taking Corzapa...” |
| Therapy Stop Date: **November 13, 2025** | `imap_20.eml` | `Email Header` | `LEVEL_1_EXACT_VISUAL` | “From: Emily Watson <clinevo.test.inbox12@gmail.com> Date: Fri, 14 Nov 2025 09:14:22 -0700 Subject...” |
| Treatment Duration: **4 days** | `imap_20.eml` | `Email Body, Paragraph 2` | `LEVEL_1_EXACT_VISUAL` | “I am writing this email to report a really scary reaction I just experienced after taking Corzapa...” |
| Action Taken with Drug: **Drug withdrawn / stopped** | `imap_20.eml` | `Email Body, Paragraph 1` | `LEVEL_1_EXACT_VISUAL` | “Hello Drug Safety Team,” |
| Adverse Reaction: **Acute drug-induced tachycardia and palpitations** | `imap_20.eml` | `Email Body, Paragraph 4` | `LEVEL_1_EXACT_VISUAL` | “My husband drove me to our family doctor (Dr. Robert Hayes at Denver Family Medicine) who examine...” |
| Seriousness Criteria: **Medically Significant** | `imap_20.eml` | `Paragraph 2 & 3` | `LEVEL_3_SNIPPET_ONLY` | “Yesterday morning (November 13th), about an hour after taking my fourth pill, my heart started po...” |
| Inpatient Hospitalization: **No** | `imap_20.eml` | `Paragraph 2 & 3` | `LEVEL_3_SNIPPET_ONLY` | “Yesterday morning (November 13th), about an hour after taking my fourth pill, my heart started po...” |
| Medically Important: **Yes (Medically Important)** | `imap_20.eml` | `Email Body, Paragraph 4` | `LEVEL_1_EXACT_VISUAL` | “My husband drove me to our family doctor (Dr. Robert Hayes at Denver Family Medicine) who examine...” |
| Dechallenge Outcome: **Positive (resolved/improved upon discontinuation)** | `imap_20.eml` | `Paragraph 2 & 3` | `LEVEL_3_SNIPPET_ONLY` | “Yesterday morning (November 13th), about an hour after taking my fourth pill, my heart started po...” |

### 5. Reviewer Flags / Warnings
- ✓ **Clean Processing State:** Structural and evidence-integrity checks passed. No conflicting evidence, handwriting ambiguities, or unstated critical parameters detected.
- **Validation Gating Status:** `READY_FOR_REVIEW`

### 6. Human Review State
- **Current Intake Status:** `TRIAGED`
- **Review Urgency Priority:** `EXPEDITED`
- **Confidence Score:** `100%`
- **Available Reviewer Primary Actions:** `[✓ Confirm AI Case]`, `[✎ Override / Edit]`, `[🚩 Flag for Escalation]`

### 7. Source Reference Section
- **Original Email File:** `test-data/emails/email_03.eml`

**Source Email Excerpt:**
```text
Hello Drug Safety Team,
I am writing this email to report a really scary reaction I just experienced after taking Corzapan 10mg tablets. My doctor prescribed this to me four days ago for mild hypertension and work-related anxiety.
Yesterday morning (November 13th), about an hour after taking my fourth pill, my heart started pounding uncontrollably like it was going to jump right out of my chest. I felt extremely lightheaded, broke out into a cold sweat, and almost passed out on my kitchen floor. My smartwatch alerted me that my resting pulse shot up to 154 bpm while I was just sitting down. I also felt tight in my chest and had trouble catching my breath for nearly two hours.
My husband drove me to our family doctor (Dr. Robert Hayes at Denver Family Medicine) who examined me and told me to immediately stop taking Corzapan. He said it was an acute drug-induced tachycardia and palpitations episode.
I am still feeling fatigued today, but my heart rate has calmed down to 78 bpm. I wanted to report this so other patients are warned. I threw the prescription bottle away, so I don't know the exact batch number, but it was filled last week at the Walgreens on Colfax.
Patient Information:
...
```

---

## CASE-04

### 1. Case Identification
- **Case ID:** `CASE-004`
- **Email Subject:** CRITICAL ALERT: Sepsis caused by Contaminated Cefatox 1g Vial (Lot #CX54831) - FDA Form 3500A Attached
- **Sender:** Dr. Robert Lang, MD (clinevo.test.inbox12@gmail.com)
- **Date:** Sat Nov 15 01:40:00 IST 2025
- **Attachment Filenames:** vial_contamination_sepsis.pdf
- **Primary Category:** `Safety Report (ICSR)`
- **All Categories / Labels:** ['Safety Report (ICSR)', 'Quality Complaint (PQC)']
- **Multi-Label Status:** `Yes (Multi-Label Submission)`
- **AI Confidence:** `100%`
- **Clinical Urgency / Clock:** `CRITICAL`

### 2. Reviewer-Facing Summary
> This critical medical communication details an urgent dual-category report submitted by Dr. Robert Lang, Director of the Medical ICU at Northwestern Memorial Hospital, involving a 71-year-old male patient (Arthur Pendelton) who developed acute septic shock, severe hypotension, and high fever following the intravenous administration of Cefatox 1g (cefatoxime sodium, Lot #CX54831). Upon inspection of the suspect medication vial, clinical staff discovered a cracked aluminum crimp collar compromising container closure integrity, along with visible dark foreign particulate matter floating in the reconstituted solution. The patient immediately required intensive care resuscitation, including continuous norepinephrine vasopressor support and broad-spectrum antimicrobial therapy, and remains in critical condition. Concurrently, hospital quality assurance and central pharmacy personnel identified a severe product quality defect, quarantining all 48 remaining inventory units of the affected lot and compiling photographic evidence. An official FDA Form 3500A (Mandatory 15-Day Alert) and risk management photo log were attached to the report to document both the serious adverse reaction and the physical product defect. From a regulatory perspective, this communication demands immediate dual processing as both an expedited Individual Case Safety Report (ICSR) and a high-priority Product Quality Complaint (PQC). Immediate regulatory actions include expedited intake into the global safety database, urgent notification of manufacturing and quality assurance teams for lot quarantine investigations, and prompt submission to health authorities in compliance with 15-day alert mandates.

### 3. Structured Review Content
#### Section: Patient Demographics & Medical History (Scope: `ICSR` | Type: `GRID`)
| Parameter | Rendered Value | Status |
|:---|:---|:---|
| Patient Identifier | A.P. (Arthur Pendelton) | `CONFIRMED` |
| Date of Birth | 19-AUG-1954 | `CONFIRMED` |
| Patient Age | 71 YRS | `CONFIRMED` |
| Sex / Gender | MALE | `CONFIRMED` |
| Patient Weight | 74 kg (163 lbs) | `CONFIRMED` |
| Country | USA | `CONFIRMED` |
| Medical History | Post-op pneumonia | `CONFIRMED` |

#### Section: Healthcare Professional & Primary Reporter (Scope: `ICSR` | Type: `GRID`)
| Parameter | Rendered Value | Status |
|:---|:---|:---|
| Reporter Name | Robert Lang, MD, FCCM | `CONFIRMED` |
| Qualification / Role | Physician | `CONFIRMED` |
| Medical Specialty | Director of Critical Care Medicine / Intensivist | `CONFIRMED` |
| Health Professional | Yes (HCP Confirmed) | `CONFIRMED` |
| Institution / Clinic | Northwestern Memorial Hospital — Medical ICU | `CONFIRMED` |
| Country | USA | `CONFIRMED` |
| Contact Information | Tel: (312) 555-0320 | Email: rlang@nmh-icu.org | `CONFIRMED` |

#### Section: Suspect Product & Administration Regimen (Scope: `ICSR` | Type: `GRID`)
| Parameter | Rendered Value | Status |
|:---|:---|:---|
| Suspect Product | Cefatox (cefatoxime sodium) 1g for Inj. | `CONFIRMED` |
| Dosage Formulation | 1g for Injection (20ml) | `CONFIRMED` |
| Administered Dose | 1g | `CONFIRMED` |
| Dosing Frequency | once | `CONFIRMED` |
| Route of Administration | IV piggyback | `CONFIRMED` |
| Therapeutic Indication | Post-operative Aspiration Pneumonia | `CONFIRMED` |
| Therapy Start Date | 14-NOV-2025 | `CONFIRMED` |
| Therapy Stop Date | 14-NOV-2025 | `CONFIRMED` |
| Treatment Duration | Single partial dose (~35mL infused) | `CONFIRMED` |
| Lot / Batch Number | CX54831 | `CONFIRMED` |
| Expiration Date | 08/2025 | `CONFIRMED` |
| Action Taken with Drug | Infusion halted immediately | `CONFIRMED` |

#### Section: Adverse Event & Seriousness Profile (Scope: `ICSR` | Type: `GRID`)
| Parameter | Rendered Value | Status |
|:---|:---|:---|
| Adverse Reaction | Septic shock and severe hypotension | `CONFIRMED` |
| Reaction Onset Date | 14-NOV-2025 | `CONFIRMED` |
| Clinical Outcome | Patient remains in critical condition under ICU resuscitation | `CONFIRMED` |
| Dechallenge Outcome | Negative (persisted) | `CONFIRMED` |
| Rechallenge Outcome | Not applicable | `CONFIRMED` |
| Seriousness Criteria | Life-threatening, Hospitalization, Required Intervention to Prevent Damage, Other Medically Important Condition | `CONFIRMED` |
| Inpatient Hospitalization | Yes (Hospitalized) | `CONFIRMED` |
| Hospital Admission Date | 14-NOV-2025 | `CONFIRMED` |
| Life Threatening | Yes (Life Threatening) | `CONFIRMED` |
| Medically Important | Yes (Medically Important) | `CONFIRMED` |

#### Section: Concomitant Medications & Prior Therapy (Scope: `ICSR` | Type: `TABLE`)
| Concomitant Medication | Indication | Dose & Schedule | Therapy Dates |
|:---|:---|:---|:---|
| Not stated | Vasopressor therapy / Septic shock hemodynamic support | Not stated | 14-NOV-2025 |

#### Section: Laboratory & Diagnostic Investigations Matrix (Scope: `ICSR` | Type: `TABLE`)
| Test / Parameter | Date | Result | Unit | Normal Range | Interpretation |
|:---|:---|:---|:---|:---|:---|
| Blood Pressure | 14-NOV-2025 | 72/40 | mmHg | Not stated | Severe hypotension / Septic shock |
| Body Temperature | 14-NOV-2025 | 39.8 | °C (103.6°F) | Not stated | Fever / Temperature spike |

#### Section: Clinical Chronological Narrative (Scope: `ICSR` | Type: `NARRATIVE`)
**Narrative Text:**

At 11:30 on November 14, 2025, in the Medical ICU at Northwestern Memorial Hospital, patient Arthur Pendelton (71-year-old male treated for post-operative aspiration pneumonia) was initiated on an intravenous infusion of Cefatox 1g. After approximately 35mL had infused, the bedside nurse noted visible turbidity and dark particulate matter inside the piggyback container, and the infusion was halted immediately. Within 45 minutes, the patient developed acute rigors, a temperature spike to 39.8°C, severe hypotension (BP 72/40 mmHg, MAP 50), and signs of distributive septic shock. Vasopressor therapy with Norepinephrine (titrated to 0.14 mcg/kg/min) and broad-spectrum empiric coverage were promptly initiated. Visual inspection of the vial confirmed a cracked aluminum crimp collar compromising container closure integrity, with visible black particulate matter floating in the solution. The central pharmacy placed all 48 hospital units of Lot #CX54831 into immediate quarantine. The patient remains in critical condition under ICU resuscitation.

#### Section: Regulatory & Manufacturer Processing Metadata (Scope: `ICSR` | Type: `GRID`)
| Parameter | Rendered Value | Status |
|:---|:---|:---|
| Report Classification | Mandatory 15-Day Alert | `CONFIRMED` |

#### Section: Product Quality Complaint Parameters (Scope: `PQC` | Type: `GRID`)
| Parameter | Rendered Value | Status |
|:---|:---|:---|
| Defective Product | Cefatox 1g for Injection (20ml) | `CONFIRMED` |
| Lot / Batch Number | CX54831 | `CONFIRMED` |
| Physical Defect Classification | Container Closure Integrity Compromise & Foreign Particulate Contamination | `CONFIRMED` |
| Container Closure Integrity | Breached (Integrity Compromised) | `CONFIRMED` |
| Defect Narrative Description | Irregular mechanical rupture/tear in the aluminum crimp collar securing the blue elastomeric stopper. Macroscopic particulate matter (multiple dark, black/brown foreign fragments and flakes) suspended throughout the reconstituted solution. | `CONFIRMED` |

#### Section: Physical Defect Visual Assessment (Scope: `PQC` | Type: `GRID`)
| Parameter | Rendered Value | Status |
|:---|:---|:---|
| Physical Photo Evidence | Yes (Visual Inspection Required) | `CONFIRMED` |
| Visual Inspection Assessment | Close examination of the 20mL glass container reveals an irregular mechanical rupture/tear in the aluminum crimp collar securing the blue elastomeric stopper. Macroscopic dark particulate matter is clearly visible suspended throughout the reconstituted solution. | `CONFIRMED` |
| Quality Review Status | Mandatory Human Verification Required | `CONFIRMED` |

### 4. Evidence Shown to Reviewer
| Displayed Fact | Source Document | Page / Location | Anchor Level | Displayed Evidence Snippet |
|:---|:---|:---|:---|:---|
| Patient Identifier: **A.P. (Arthur Pendelton)** | `vial_contamination_sepsis.pdf` | `Page 1, Block 5` | `LEVEL_1_EXACT_VISUAL` | “1. PATIENT IDENTIFIER A.P. (Arthur Pendelton)” |
| Date of Birth: **19-AUG-1954** | `vial_contamination_sepsis.pdf` | `Page 1, Block 7` | `LEVEL_1_EXACT_VISUAL` | “2a. DATE OF BIRTH 19-AUG-1954” |
| Patient Age: **71 YRS** | `vial_contamination_sepsis.pdf` | `Page 1, Block 6` | `LEVEL_1_EXACT_VISUAL` | “2. AGE AT TIME OF EVENT 71 YRS” |
| Sex / Gender: **MALE** | `vial_contamination_sepsis.pdf` | `Page 1, Block 8` | `LEVEL_1_EXACT_VISUAL` | “3. SEX MALE” |
| Patient Weight: **74 kg (163 lbs)** | `vial_contamination_sepsis.pdf` | `Page 1, Block 9` | `LEVEL_1_EXACT_VISUAL` | “4. WEIGHT 74 kg (163 lbs)” |
| Patient Country: **USA** | `vial_contamination_sepsis.pdf` | `Page 1, Block 27` | `LEVEL_1_EXACT_VISUAL` | “1. NAME AND ADDRESS OF REPORTER Robert Lang, MD, FCCM (Director of Critical Care Medicine) Northw...” |
| Reporter Name: **Robert Lang, MD, FCCM** | `vial_contamination_sepsis.pdf` | `Page 1, Block 27` | `LEVEL_1_EXACT_VISUAL` | “1. NAME AND ADDRESS OF REPORTER Robert Lang, MD, FCCM (Director of Critical Care Medicine) Northw...” |
| Reporter Qualification: **Physician** | `vial_contamination_sepsis.pdf` | `Page 1, Block 29` | `LEVEL_1_EXACT_VISUAL` | “3. OCCUPATION: Physician / Intensivist” |
| Medical Specialty: **Director of Critical Care Medicine / Intensivist** | `vial_contamination_sepsis.pdf` | `Page 1, Block 27` | `LEVEL_1_EXACT_VISUAL` | “1. NAME AND ADDRESS OF REPORTER Robert Lang, MD, FCCM (Director of Critical Care Medicine) Northw...” |
| Health Professional: **Yes (HCP Confirmed)** | `vial_contamination_sepsis.pdf` | `Page 1, Block 28` | `LEVEL_1_EXACT_VISUAL` | “2. HEALTH PROFESSIONAL? [ X ] YES    [   ] NO” |
| Institution / Clinic: **Northwestern Memorial Hospital — Medical ICU** | `vial_contamination_sepsis.pdf` | `Page 1, Block 27` | `LEVEL_1_EXACT_VISUAL` | “1. NAME AND ADDRESS OF REPORTER Robert Lang, MD, FCCM (Director of Critical Care Medicine) Northw...” |
| Country: **USA** | `vial_contamination_sepsis.pdf` | `Page 1, Block 27` | `LEVEL_1_EXACT_VISUAL` | “1. NAME AND ADDRESS OF REPORTER Robert Lang, MD, FCCM (Director of Critical Care Medicine) Northw...” |
| Contact Information: **Tel: (312) 555-0320 | Email: rlang@nmh-icu.org** | `vial_contamination_sepsis.pdf` | `Page 1, Block 30` | `LEVEL_1_EXACT_VISUAL` | “4. CONTACT TELEPHONE & EMAIL: Tel: (312) 555-0320 Email: rlang@nmh-icu.org” |
| Suspect Product: **Cefatox (cefatoxime sodium) 1g for Inj.** | `vial_contamination_sepsis.pdf` | `Page 1, Structured Table 2` | `LEVEL_2_PAGE_TEXT` | “| 1. NAME, STRENGTH, MANUFACTURER Cefatox (cefatoxime sodium) 1g for Inj. | 2. DOSE, FREQUENCY & ...” |
| Dosage Formulation: **1g for Injection (20ml)** | `vial_contamination_sepsis.pdf` | `Page 2, Block 5` | `LEVEL_1_EXACT_VISUAL` | “PRODUCT: Cefatox 1g for Injection (20ml) LOT / BATCH: Lot #CX54831 (Exp 08/25) SECURITY QUARANTIN...” |
| Administered Dose: **1g** | `vial_contamination_sepsis.pdf` | `Page 1, Block 15` | `LEVEL_1_EXACT_VISUAL` | “5. DESCRIBE EVENT OR PROBLEM (Include relevant tests, laboratory data, dates, and defect observat...” |
| Dosing Frequency: **once** | `vial_contamination_sepsis.pdf` | `Page 1, Block 18` | `LEVEL_1_EXACT_VISUAL` | “2. DOSE, FREQUENCY & ROUTE 1g IV piggyback once” |
| Route of Administration: **IV piggyback** | `vial_contamination_sepsis.pdf` | `Page 1, Block 18` | `LEVEL_1_EXACT_VISUAL` | “2. DOSE, FREQUENCY & ROUTE 1g IV piggyback once” |
| Therapy Start Date: **14-NOV-2025** | `vial_contamination_sepsis.pdf` | `Page 1, Block 13` | `LEVEL_1_EXACT_VISUAL` | “3. DATE OF EVENT 14-NOV-2025” |
| Therapy Stop Date: **14-NOV-2025** | `vial_contamination_sepsis.pdf` | `Page 1, Block 13` | `LEVEL_1_EXACT_VISUAL` | “3. DATE OF EVENT 14-NOV-2025” |
| Treatment Duration: **Single partial dose (~35mL infused)** | `vial_contamination_sepsis.pdf` | `Page 1, Block 19` | `LEVEL_1_EXACT_VISUAL` | “3. THERAPY DATES 14-NOV-2025 (Single partial dose)” |
| Product Lot / Batch: **CX54831** | `vial_contamination_sepsis.pdf` | `Page 1, Block 15` | `LEVEL_1_EXACT_VISUAL` | “5. DESCRIBE EVENT OR PROBLEM (Include relevant tests, laboratory data, dates, and defect observat...” |
| Expiration Date: **08/2025** | `vial_contamination_sepsis.pdf` | `Page 2, Block 5` | `LEVEL_1_EXACT_VISUAL` | “PRODUCT: Cefatox 1g for Injection (20ml) LOT / BATCH: Lot #CX54831 (Exp 08/25) SECURITY QUARANTIN...” |
| Action Taken with Drug: **Infusion halted immediately** | `vial_contamination_sepsis.pdf` | `Page 1, Structured Table 1` | `LEVEL_2_PAGE_TEXT` | “| 1. CHECK ALL THAT APPLY: [ X ] ADVERSE EVENT [ X ] PRODUCT PROBLEM (e.g., defects / contaminati...” |
| Adverse Reaction: **Septic shock and severe hypotension** | `vial_contamination_sepsis.pdf` | `Page 1, Block 15` | `LEVEL_1_EXACT_VISUAL` | “5. DESCRIBE EVENT OR PROBLEM (Include relevant tests, laboratory data, dates, and defect observat...” |
| Reaction Onset Date: **14-NOV-2025** | `vial_contamination_sepsis.pdf` | `Page 1, Block 15` | `LEVEL_1_EXACT_VISUAL` | “5. DESCRIBE EVENT OR PROBLEM (Include relevant tests, laboratory data, dates, and defect observat...” |
| Clinical Outcome: **Patient remains in critical condition under ICU resuscitation** | `vial_contamination_sepsis.pdf` | `Page 1, Block 15` | `LEVEL_1_EXACT_VISUAL` | “5. DESCRIBE EVENT OR PROBLEM (Include relevant tests, laboratory data, dates, and defect observat...” |
| Seriousness Criteria: **Life-threatening, Hospitalization, Required Intervention to Prevent Damage, Other Medically Important Condition** | `vial_contamination_sepsis.pdf` | `Page 1, Block 12` | `LEVEL_1_EXACT_VISUAL` | “2. OUTCOMES ATTRIBUTED TO ADVERSE EVENT (Check all that apply): [   ] DEATH                      ...” |
| Inpatient Hospitalization: **Yes (Hospitalized)** | `vial_contamination_sepsis.pdf` | `Page 1, Block 12` | `LEVEL_1_EXACT_VISUAL` | “2. OUTCOMES ATTRIBUTED TO ADVERSE EVENT (Check all that apply): [   ] DEATH                      ...” |
| Hospital Admission Date: **14-NOV-2025** | `vial_contamination_sepsis.pdf` | `Page 1, Block 13` | `LEVEL_1_EXACT_VISUAL` | “3. DATE OF EVENT 14-NOV-2025” |
| Life Threatening: **Yes (Life Threatening)** | `vial_contamination_sepsis.pdf` | `Page 1, Block 12` | `LEVEL_1_EXACT_VISUAL` | “2. OUTCOMES ATTRIBUTED TO ADVERSE EVENT (Check all that apply): [   ] DEATH                      ...” |
| Medically Important: **Yes (Medically Important)** | `vial_contamination_sepsis.pdf` | `Page 1, Block 23` | `LEVEL_1_EXACT_VISUAL` | “7. EVENT ABATED AFTER STOPPING? [   ] Yes    [ X ] No (ICU shock ongoing)” |
| Dechallenge Outcome: **Negative (persisted)** | `imap_21.eml` | `PAGE 1` | `LEVEL_3_SNIPPET_ONLY` | “Within 45 minutes, patient developed acute rigors, temperature spike to 39.8°C (103.6°F), severe ...” |
| Rechallenge Outcome: **Not applicable** | `imap_21.eml` | `PAGE 1` | `LEVEL_3_SNIPPET_ONLY` | “Within 45 minutes, patient developed acute rigors, temperature spike to 39.8°C (103.6°F), severe ...” |
| Packaging Breached: **Yes (Closure Compromised)** | `imap_21.eml` | `PAGE 2` | `LEVEL_3_SNIPPET_ONLY` | “1. Closure Integrity Compromise: Close examination of the 20mL glass container reveals an irregul...” |

### 5. Reviewer Flags / Warnings
- ⚠️ **Mandatory Defect Photo Inspection** (`PHOTO_DEFECT_INSPECTION`): Close examination of the 20mL glass container reveals an irregular mechanical rupture/tear in the aluminum crimp collar securing the blue elastomeric stopper. Macroscopic dark particulate matter is clearly visible suspended throughout the reconstituted solution. [Action: *Inspect photo asset in viewer*]
- ⚠️ **Dual Regulatory Domain (Multi-Label)** (`CATEGORY_AMBIGUITY`): Submission contains elements for Safety Report (ICSR) AND Quality Complaint (PQC). Both regulatory flows must be evaluated. [Action: *Review dual regulatory obligations*]
- **Validation Gating Status:** `REVIEW_WITH_WARNINGS`

### 6. Human Review State
- **Current Intake Status:** `TRIAGED`
- **Review Urgency Priority:** `CRITICAL`
- **Confidence Score:** `100%`
- **Available Reviewer Primary Actions:** `[✓ Confirm AI Case]`, `[✎ Override / Edit]`, `[🚩 Flag for Escalation]`

### 7. Source Reference Section
- **Original Email File:** `test-data/emails/email_04.eml`
- **Original PDF Attachment(s):** `test-data/pdfs/.../vial_contamination_sepsis.pdf`
- **Original Image Asset(s):** `test-data/pdfs/.../contaminated_vial_photo.jpg`

**Source Email Excerpt:**
```text
URGENT: TO PHARMACOVIGILANCE AND QUALITY COMPLAINTS DEPARTMENTS,
I am submitting an emergency dual-category report involving both an immediate Product Quality Complaint (PQC) and a life-threatening Serious Adverse Event (ICSR).
Earlier today in our ICU, patient Arthur Pendelton (71yo male) developed septic shock and severe hypotension (BP 72/40) shortly after receiving an intravenous infusion of Cefatox 1g (cefatoxime sodium, Lot #CX54831, Exp 08/2025).
Upon inspecting the medication vial, bedside staff discovered that the aluminum crimp collar on the rubber stopper was cracked open, and dark foreign particulate matter was visibly floating in the solution.
We have quarantined all 48 remaining vials of Lot #CX54831 in our central pharmacy. The patient is currently on norepinephrine vasopressor support in critical condition.
Attached is our official completed FDA Form 3500A report with Exhibit 1 (photographic evidence record of the contaminated vial).
...
```

**Source PDF Excerpt (`vial_contamination_sepsis.pdf`):**
```text
DEPARTMENT OF HEALTH AND HUMAN SERVICES — FOOD AND DRUG ADMINISTRATION
MEDWATCH: THE FDA SAFETY INFORMATION AND ADVERSE EVENT REPORTING PROGRAM
FORM FDA 3500A (10/15) — MANDATORY ADVERSE EVENT & PRODUCT PROBLEM REPORTING
OMB Control No. 0910-0291  |  For use by User-Facilities, Distributors, and Manufacturers
SECTION A: PATIENT INFORMATION
1. PATIENT IDENTIFIER
A.P. (Arthur Pendelton)
2. AGE AT TIME OF
...
```

---

## CASE-05

### 1. Case Identification
- **Case ID:** `CASE-005`
- **Email Subject:** URGENTE: Notificación de Reacción Adversa Grave - Necrólisis Epidérmica Tóxica con Lamotrigina (Pt C.O.)
- **Sender:** Dra. Elena Morales (clinevo.test.inbox12@gmail.com)
- **Date:** Sat Nov 15 15:50:00 IST 2025
- **Attachment Filenames:** notificacion_ram_madrid.pdf
- **Primary Category:** `Safety Report (ICSR)`
- **All Categories / Labels:** ['Safety Report (ICSR)']
- **Multi-Label Status:** `No`
- **AI Confidence:** `100%`
- **Clinical Urgency / Clock:** `EXPEDITED`

### 2. Reviewer-Facing Summary
> This urgent medical communication from Dra. Elena Morales at Hospital Universitario La Paz transmits an official Spanish pharmacovigilance Yellow Card notification regarding a life-threatening serious adverse drug reaction. The patient, a 29-year-old female (C.O.), developed Toxic Epidermal Necrolysis (TEN / Lyell's syndrome) with greater than 35% body surface area detachment and severe mucosal involvement following three weeks of treatment with Lamotrigine 100 mg/day for myoclonic epilepsy. The clinical presentation includes confluent erythematous macular rash, high fever, positive Nikolsky sign, and pseudomembranous stomatitis and conjunctivitis, necessitating emergency admission to the Critical Burns Unit. The suspect medication has been permanently discontinued, and the patient remains in a critical, unrecovered state. From a regulatory standpoint, this case fulfills all ICSR reporting criteria due to the presence of an identifiable reporter, an identifiable patient, a suspect medicinal product (Lamotrigine), and a medically significant, life-threatening adverse event outcome. Immediate intake into the global safety database, expedited regulatory submission to health authorities as a Serious Unexpected Suspected Adverse Reaction (SUSAR) or expedited spontaneous report, and urgent medical review are strictly required.

### 3. Structured Review Content
#### Section: Patient Demographics & Medical History (Scope: `ICSR` | Type: `GRID`)
| Parameter | Rendered Value | Status |
|:---|:---|:---|
| Patient Identifier | C.O. (Carmen Ortiz) | `CONFIRMED` |
| Date of Birth | 22-MAR-1996 | `CONFIRMED` |
| Patient Age | 29 AÑOS | `CONFIRMED` |
| Sex / Gender | MUJER | `CONFIRMED` |
| Patient Weight | 54 kg | `CONFIRMED` |
| Country | España | `CONFIRMED` |
| Medical History | Not stated | `NOT_STATED` |

#### Section: Healthcare Professional & Primary Reporter (Scope: `ICSR` | Type: `GRID`)
| Parameter | Rendered Value | Status |
|:---|:---|:---|
| Reporter Name | Dra. Elena Morales | `CONFIRMED` |
| Qualification / Role | Physician | `CONFIRMED` |
| Medical Specialty | Dermatología | `CONFIRMED` |
| Health Professional | Yes (HCP Confirmed) | `CONFIRMED` |
| Institution / Clinic | Hospital Universitario La Paz — Servicio de Dermatología | `CONFIRMED` |
| Country | España | `CONFIRMED` |
| Contact Information | Tel: +34 91 555 0244 | Email: emorales@hospitallapaz.es | `CONFIRMED` |

#### Section: Suspect Product & Administration Regimen (Scope: `ICSR` | Type: `GRID`)
| Parameter | Rendered Value | Status |
|:---|:---|:---|
| Suspect Product | Lamotrigina (Lamictal) | `CONFIRMED` |
| Dosage Formulation | 100 mg | `CONFIRMED` |
| Administered Dose | 100 mg/día | `CONFIRMED` |
| Dosing Frequency | Diaria | `CONFIRMED` |
| Route of Administration | vía oral | `CONFIRMED` |
| Therapeutic Indication | Epilepsia mioclónica | `CONFIRMED` |
| Therapy Start Date | 20-OCT-2025 | `CONFIRMED` |
| Therapy Stop Date | 11-NOV-2025 | `CONFIRMED` |
| Treatment Duration | A las 3 semanas de tratamiento | `CONFIRMED` |
| Lot / Batch Number | Lote #LM-9941 | `CONFIRMED` |
| Expiration Date | 05/2027 | `CONFIRMED` |
| Action Taken with Drug | Retirada definitiva | `CONFIRMED` |

#### Section: Adverse Event & Seriousness Profile (Scope: `ICSR` | Type: `GRID`)
| Parameter | Rendered Value | Status |
|:---|:---|:---|
| Adverse Reaction | Necrólisis Epidérmica Tóxica (NET / Síndrome de Lyell) | `CONFIRMED` |
| Reaction Onset Date | 11-NOV-2025 | `CONFIRMED` |
| Clinical Outcome | No recuperado (Estado crítico en UCI Quemados) | `CONFIRMED` |
| Dechallenge Outcome | Positive (resolved/improved upon discontinuation) | `CONFIRMED` |
| Rechallenge Outcome | Not stated | `NOT_STATED` |
| Seriousness Criteria | Hospitalization, Life-threatening, Other Medically Important Condition | `CONFIRMED` |
| Inpatient Hospitalization | Yes (Hospitalized) | `CONFIRMED` |
| Hospital Admission Date | 11-NOV-2025 | `CONFIRMED` |
| Life Threatening | Yes (Life Threatening) | `CONFIRMED` |
| Medically Important | Yes (Medically Important) | `CONFIRMED` |

#### Section: Clinical Chronological Narrative (Scope: `ICSR` | Type: `NARRATIVE`)
**Narrative Text:**

Paciente mujer de 29 años, con antecedentes de epilepsia mioclónica tratada con Lamotrigina (Lamictal) 100 mg/día vía oral desde el 20 de octubre de 2025. A las 3 semanas de tratamiento (11 de noviembre de 2025), presenta exantema macular eritematoso confluente y fiebre de 39,2 °C. En 48 horas evoluciona a un cuadro clínico con desprendimiento dermoepidérmico extenso en láminas afectando cara, tronco y extremidades (>35% de la superficie corporal total), signo de Nikolsky positivo, estomatitis pseudomembranosa grave y conjuntivitis pseudomembranosa bilateral con queratitis. Mediante diagnóstico clínico y biopsia cutánea se confirma Necrólisis Epidérmica Tóxica (NET / Síndrome de Lyell) inducida por Lamotrigina. La paciente fue ingresada de urgencia en la Unidad de Quemados Críticos del Hospital Universitario La Paz. El fármaco sospechoso fue suspendido de forma definitiva el 11 de noviembre de 2025. Al momento del informe, el desenlace es no recuperado y la paciente permanece en estado crítico en la UCI de Quemados.

#### Section: Regulatory & Manufacturer Processing Metadata (Scope: `ICSR` | Type: `GRID`)
| Parameter | Rendered Value | Status |
|:---|:---|:---|
| Report Classification | Spontaneous | `CONFIRMED` |

### 4. Evidence Shown to Reviewer
| Displayed Fact | Source Document | Page / Location | Anchor Level | Displayed Evidence Snippet |
|:---|:---|:---|:---|:---|
| Patient Identifier: **C.O. (Carmen Ortiz)** | `notificacion_ram_madrid.pdf` | `Page 1, Block 4` | `LEVEL_1_EXACT_VISUAL` | “1. INICIALES: C.O. (Carmen Ortiz)” |
| Date of Birth: **22-MAR-1996** | `notificacion_ram_madrid.pdf` | `Page 1, Block 5` | `LEVEL_1_EXACT_VISUAL` | “2. FECHA NACIMIENTO: 22-MAR-1996 2a. EDAD: 29 AÑOS 3. SEXO: MUJER 4. PESO: 54 kg” |
| Patient Age: **29 AÑOS** | `notificacion_ram_madrid.pdf` | `Page 1, Block 5` | `LEVEL_1_EXACT_VISUAL` | “2. FECHA NACIMIENTO: 22-MAR-1996 2a. EDAD: 29 AÑOS 3. SEXO: MUJER 4. PESO: 54 kg” |
| Sex / Gender: **MUJER** | `notificacion_ram_madrid.pdf` | `Page 1, Block 5` | `LEVEL_1_EXACT_VISUAL` | “2. FECHA NACIMIENTO: 22-MAR-1996 2a. EDAD: 29 AÑOS 3. SEXO: MUJER 4. PESO: 54 kg” |
| Patient Weight: **54 kg** | `notificacion_ram_madrid.pdf` | `Page 1, Block 5` | `LEVEL_1_EXACT_VISUAL` | “2. FECHA NACIMIENTO: 22-MAR-1996 2a. EDAD: 29 AÑOS 3. SEXO: MUJER 4. PESO: 54 kg” |
| Patient Country: **España** | `notificacion_ram_madrid.pdf` | `Page 1, Block 12` | `LEVEL_1_EXACT_VISUAL` | “NOMBRE: Dra. Elena Morales  |  PROFESIÓN: Médico Especialista (Dermatología) CENTRO SANITARIO: Ho...” |
| Reporter Name: **Dra. Elena Morales** | `notificacion_ram_madrid.pdf` | `Page 1, Block 12` | `LEVEL_1_EXACT_VISUAL` | “NOMBRE: Dra. Elena Morales  |  PROFESIÓN: Médico Especialista (Dermatología) CENTRO SANITARIO: Ho...” |
| Reporter Qualification: **Physician** | `imap_22.eml` | `PAGE 1` | `LEVEL_3_SNIPPET_ONLY` | “NOMBRE: Dra. Elena Morales  |  PROFESIÓN: Médico Especialista (Dermatología) CENTRO SANITARIO: Ho...” |
| Medical Specialty: **Dermatología** | `notificacion_ram_madrid.pdf` | `Page 1, Block 12` | `LEVEL_1_EXACT_VISUAL` | “NOMBRE: Dra. Elena Morales  |  PROFESIÓN: Médico Especialista (Dermatología) CENTRO SANITARIO: Ho...” |
| Health Professional: **Yes (HCP Confirmed)** | `imap_22.eml` | `PAGE 1` | `LEVEL_3_SNIPPET_ONLY` | “NOMBRE: Dra. Elena Morales  |  PROFESIÓN: Médico Especialista (Dermatología) CENTRO SANITARIO: Ho...” |
| Institution / Clinic: **Hospital Universitario La Paz — Servicio de Dermatología** | `notificacion_ram_madrid.pdf` | `Page 1, Block 12` | `LEVEL_1_EXACT_VISUAL` | “NOMBRE: Dra. Elena Morales  |  PROFESIÓN: Médico Especialista (Dermatología) CENTRO SANITARIO: Ho...” |
| Country: **España** | `notificacion_ram_madrid.pdf` | `Page 1, Block 12` | `LEVEL_1_EXACT_VISUAL` | “NOMBRE: Dra. Elena Morales  |  PROFESIÓN: Médico Especialista (Dermatología) CENTRO SANITARIO: Ho...” |
| Contact Information: **Tel: +34 91 555 0244 | Email: emorales@hospitallapaz.es** | `notificacion_ram_madrid.pdf` | `Page 1, Block 12` | `LEVEL_1_EXACT_VISUAL` | “NOMBRE: Dra. Elena Morales  |  PROFESIÓN: Médico Especialista (Dermatología) CENTRO SANITARIO: Ho...” |
| Suspect Product: **Lamotrigina (Lamictal)** | `notificacion_ram_madrid.pdf` | `Page 1, Block 7` | `LEVEL_1_EXACT_VISUAL` | “DESCRIPCIÓN CLÍNICA: Paciente de 29 años tratada con Lamotrigina (Lamictal) 100 mg/día por epilep...” |
| Dosage Formulation: **100 mg** | `notificacion_ram_madrid.pdf` | `Page 1, Block 7` | `LEVEL_1_EXACT_VISUAL` | “DESCRIPCIÓN CLÍNICA: Paciente de 29 años tratada con Lamotrigina (Lamictal) 100 mg/día por epilep...” |
| Administered Dose: **100 mg/día** | `notificacion_ram_madrid.pdf` | `Page 1, Block 7` | `LEVEL_1_EXACT_VISUAL` | “DESCRIPCIÓN CLÍNICA: Paciente de 29 años tratada con Lamotrigina (Lamictal) 100 mg/día por epilep...” |
| Dosing Frequency: **Diaria** | `imap_22.eml` | `PAGE 1` | `LEVEL_3_SNIPPET_ONLY` | “MEDICAMENTO: Lamotrigina (Lamictal) 100 mg | DOSIS / VÍA: 100 mg/día vía oral | INDICACIÓN: Epile...” |
| Route of Administration: **vía oral** | `notificacion_ram_madrid.pdf` | `Page 1, Block 9` | `LEVEL_1_EXACT_VISUAL` | “MEDICAMENTO: Lamotrigina (Lamictal) 100 mg DOSIS / VÍA: 100 mg/día vía oral INDICACIÓN: Epilepsia...” |
| Therapy Start Date: **20-OCT-2025** | `notificacion_ram_madrid.pdf` | `Page 1, Block 10` | `LEVEL_1_EXACT_VISUAL` | “FECHAS: 20-OCT-2025 al 11-NOV-2025 LOTE: Lote #LM-9941 (Caducidad: 05/2027) MEDIDA: [ X ] Retirad...” |
| Therapy Stop Date: **11-NOV-2025** | `notificacion_ram_madrid.pdf` | `Page 1, Block 7` | `LEVEL_1_EXACT_VISUAL` | “DESCRIPCIÓN CLÍNICA: Paciente de 29 años tratada con Lamotrigina (Lamictal) 100 mg/día por epilep...” |
| Treatment Duration: **A las 3 semanas de tratamiento** | `notificacion_ram_madrid.pdf` | `Page 1, Block 7` | `LEVEL_1_EXACT_VISUAL` | “DESCRIPCIÓN CLÍNICA: Paciente de 29 años tratada con Lamotrigina (Lamictal) 100 mg/día por epilep...” |
| Product Lot / Batch: **Lote #LM-9941** | `notificacion_ram_madrid.pdf` | `Page 1, Block 10` | `LEVEL_1_EXACT_VISUAL` | “FECHAS: 20-OCT-2025 al 11-NOV-2025 LOTE: Lote #LM-9941 (Caducidad: 05/2027) MEDIDA: [ X ] Retirad...” |
| Therapeutic Indication: **Epilepsia mioclónica** | `notificacion_ram_madrid.pdf` | `Page 1, Block 9` | `LEVEL_1_EXACT_VISUAL` | “MEDICAMENTO: Lamotrigina (Lamictal) 100 mg DOSIS / VÍA: 100 mg/día vía oral INDICACIÓN: Epilepsia...” |
| Action Taken with Drug: **Retirada definitiva** | `notificacion_ram_madrid.pdf` | `Page 1, Block 10` | `LEVEL_1_EXACT_VISUAL` | “FECHAS: 20-OCT-2025 al 11-NOV-2025 LOTE: Lote #LM-9941 (Caducidad: 05/2027) MEDIDA: [ X ] Retirad...” |
| Adverse Reaction: **Necrólisis Epidérmica Tóxica (NET / Síndrome de Lyell)** | `notificacion_ram_madrid.pdf` | `Page 1, Block 7` | `LEVEL_1_EXACT_VISUAL` | “DESCRIPCIÓN CLÍNICA: Paciente de 29 años tratada con Lamotrigina (Lamictal) 100 mg/día por epilep...” |
| Reaction Onset Date: **11-NOV-2025** | `notificacion_ram_madrid.pdf` | `Page 1, Block 7` | `LEVEL_1_EXACT_VISUAL` | “DESCRIPCIÓN CLÍNICA: Paciente de 29 años tratada con Lamotrigina (Lamictal) 100 mg/día por epilep...” |
| Clinical Outcome: **No recuperado (Estado crítico en UCI Quemados)** | `notificacion_ram_madrid.pdf` | `Page 1, Block 7` | `LEVEL_1_EXACT_VISUAL` | “DESCRIPCIÓN CLÍNICA: Paciente de 29 años tratada con Lamotrigina (Lamictal) 100 mg/día por epilep...” |
| Seriousness Criteria: **Hospitalization, Life-threatening, Other Medically Important Condition** | `imap_22.eml` | `PAGE 1` | `LEVEL_3_SNIPPET_ONLY` | “Diagnóstico clínico y biopsia cutánea: Necrólisis Epidérmica Tóxica (NET / Síndrome de Lyell) ind...” |
| Inpatient Hospitalization: **Yes (Hospitalized)** | `imap_22.eml` | `PAGE 1` | `LEVEL_3_SNIPPET_ONLY` | “Diagnóstico clínico y biopsia cutánea: Necrólisis Epidérmica Tóxica (NET / Síndrome de Lyell) ind...” |
| Hospital Admission Date: **11-NOV-2025** | `notificacion_ram_madrid.pdf` | `Page 1, Block 7` | `LEVEL_1_EXACT_VISUAL` | “DESCRIPCIÓN CLÍNICA: Paciente de 29 años tratada con Lamotrigina (Lamictal) 100 mg/día por epilep...” |
| Life Threatening: **Yes (Life Threatening)** | `imap_22.eml` | `PAGE 1` | `LEVEL_3_SNIPPET_ONLY` | “Diagnóstico clínico y biopsia cutánea: Necrólisis Epidérmica Tóxica (NET / Síndrome de Lyell) ind...” |
| Medically Important: **Yes (Medically Important)** | `imap_22.eml` | `PAGE 1` | `LEVEL_3_SNIPPET_ONLY` | “Diagnóstico clínico y biopsia cutánea: Necrólisis Epidérmica Tóxica (NET / Síndrome de Lyell) ind...” |
| Dechallenge Outcome: **Positive (resolved/improved upon discontinuation)** | `imap_22.eml` | `PAGE 1` | `LEVEL_3_SNIPPET_ONLY` | “Diagnóstico clínico y biopsia cutánea: Necrólisis Epidérmica Tóxica (NET / Síndrome de Lyell) ind...” |

### 5. Reviewer Flags / Warnings
- ⚠️ **Foreign Language Intake (Spanish)** (`MULTILINGUAL_TRANSLATION`): Document was submitted in Spanish. Verbatim source citations are preserved in the original language. [Action: *Verify verbatim non-English grounding*]
- **Validation Gating Status:** `REVIEW_WITH_WARNINGS`

### 6. Human Review State
- **Current Intake Status:** `TRIAGED`
- **Review Urgency Priority:** `EXPEDITED`
- **Confidence Score:** `100%`
- **Available Reviewer Primary Actions:** `[✓ Confirm AI Case]`, `[✎ Override / Edit]`, `[🚩 Flag for Escalation]`

### 7. Source Reference Section
- **Original Email File:** `test-data/emails/email_05.eml`
- **Original PDF Attachment(s):** `test-data/pdfs/.../notificacion_ram_madrid.pdf`

**Source Email Excerpt:**
```text
Estimado Departamento de Farmacovigilancia,
Remito notificación urgente de una reacción adversa grave con desenlace potencialmente mortal en una paciente de 29 años (Carmen Ortiz, C.O.) tratada con Lamotrigina 100 mg/día por epilepsia mioclónica.
La paciente ha desarrollado un cuadro clínico compatible con Necrólisis Epidérmica Tóxica (Síndrome de Lyell) con desprendimiento dermoepidérmico superior al 35% de la superficie corporal y afectación de mucosas oral y conjuntival. Ha sido ingresada de urgencia en la Unidad de Quemados Críticos del Hospital Universitario La Paz.
El fármaco sospechoso ha sido suspendido de forma inmediata. Adjunto el formulario oficial de notificación de la AEMPS debidamente cumplimentado.
Atentamente,
Dra. Elena Morales, FEA Dermatología
...
```

**Source PDF Excerpt (`notificacion_ram_madrid.pdf`):**
```text
SISTEMA ESPAÑOL DE FARMACOVIGILANCIA DE MEDICAMENTOS DE USO HUMANO (SEFV-H)
AGENCIA ESPAÑOLA DE MEDICAMENTOS Y PRODUCTOS SANITARIOS (AEMPS)
NOTIFICACIÓN DE SOSPECHA DE REACCIÓN ADVERSA A MEDICAMENTOS (TARJETA AMARILLA)
A. DATOS DEL PACIENTE
1. INICIALES: C.O. (Carmen Ortiz)
2. FECHA NACIMIENTO:
22-MAR-1996
2a. EDAD: 29 AÑOS
...
```

---

## CASE-06

### 1. Case Identification
- **Case ID:** `CASE-006`
- **Email Subject:** FOLLOW-UP REPORT #1: Case Ref CR-2025-US-00744 - Seizure Resolution s/p Neuroval Discontinuation
- **Sender:** Dr. Richard Vance, MD (clinevo.test.inbox12@gmail.com)
- **Date:** Mon Nov 17 02:35:12 IST 2025
- **Attachment Filenames:** fda_medwatch_followup.pdf
- **Primary Category:** `Safety Report (ICSR)`
- **All Categories / Labels:** ['Safety Report (ICSR)']
- **Multi-Label Status:** `No`
- **AI Confidence:** `100%`
- **Clinical Urgency / Clock:** `EXPEDITED`

### 2. Reviewer-Facing Summary
> This communication represents official follow-up report #1 (Case Ref: CR-2025-US-00744) submitted by attending neurologist Dr. Richard Vance from Columbia University Medical Center regarding patient David Miller, a 52-year-old male. The initial report documented an emergent ICU admission for a generalized tonic-clonic seizure following a dose escalation of Neuroval to 400 mg daily. This follow-up confirms clinical resolution, demonstrating that the patient has remained completely seizure-free for 14 consecutive days following the permanent discontinuation of Neuroval on November 2nd, 2025. Furthermore, repeat 24-hour ambulatory video EEG on November 14th showed complete normalization of cerebral background activity without epileptiform discharges, confirming a positive de-challenge. The accompanying MedWatch Form FDA 3500A provides verified clinical details, including suspect product lot information (Lot #NV-2025-110) and temporal therapy dates. Causality is assessed by the reporter as probable related to drug exposure, and the final clinical outcome is documented as fully recovered/resolved. From a regulatory perspective, this report must be processed expeditiously as a valid follow-up Individual Case Safety Report (ICSR) to update the global safety database and aggregate safety profiles. No product quality complaints or medical information inquiries were identified in this transmission. The documentation is complete, legally compliant, and requires no further immediate clarification from the reporter.

### 3. Structured Review Content
#### Section: Patient Demographics & Medical History (Scope: `ICSR` | Type: `GRID`)
| Parameter | Rendered Value | Status |
|:---|:---|:---|
| Patient Identifier | D.M. (David Miller) | `CONFIRMED` |
| Date of Birth | 11-FEB-1973 | `CONFIRMED` |
| Patient Age | 52 YRS | `CONFIRMED` |
| Sex / Gender | MALE | `CONFIRMED` |
| Patient Weight | 79 kg | `CONFIRMED` |
| Country | United States | `CONFIRMED` |
| Medical History | Not stated | `NOT_STATED` |

#### Section: Healthcare Professional & Primary Reporter (Scope: `ICSR` | Type: `GRID`)
| Parameter | Rendered Value | Status |
|:---|:---|:---|
| Reporter Name | Dr. Richard Vance | `CONFIRMED` |
| Qualification / Role | Physician | `CONFIRMED` |
| Medical Specialty | Attending Neurologist | `CONFIRMED` |
| Health Professional | Yes (HCP Confirmed) | `CONFIRMED` |
| Institution / Clinic | Columbia University Irving Medical Center, Department of Neurology | `CONFIRMED` |
| Country | United States | `CONFIRMED` |
| Contact Information | Tel: (212) 555-0199 | Email: rvance@columbia-neurology.org | `CONFIRMED` |

#### Section: Suspect Product & Administration Regimen (Scope: `ICSR` | Type: `GRID`)
| Parameter | Rendered Value | Status |
|:---|:---|:---|
| Suspect Product | Neuroval | `CONFIRMED` |
| Dosage Formulation | neuroval HCl | `CONFIRMED` |
| Administered Dose | 400 mg | `CONFIRMED` |
| Dosing Frequency | QD | `CONFIRMED` |
| Route of Administration | PO | `CONFIRMED` |
| Therapeutic Indication | neuropathic pain | `CONFIRMED` |
| Therapy Start Date | 15-OCT-2025 | `CONFIRMED` |
| Therapy Stop Date | 02-NOV-2025 | `CONFIRMED` |
| Lot / Batch Number | Lot #NV-2025-110 | `CONFIRMED` |
| Expiration Date | 09/27 | `CONFIRMED` |
| Action Taken with Drug | Drug permanently withdrawn | `CONFIRMED` |

#### Section: Adverse Event & Seriousness Profile (Scope: `ICSR` | Type: `GRID`)
| Parameter | Rendered Value | Status |
|:---|:---|:---|
| Adverse Reaction | generalized tonic-clonic seizure | `CONFIRMED` |
| Reaction Onset Date | Not stated | `NOT_STATED` |
| Clinical Outcome | Fully recovered / resolved | `CONFIRMED` |
| Dechallenge Outcome | Positive (resolved/improved upon discontinuation) | `CONFIRMED` |
| Rechallenge Outcome | Not stated | `NOT_STATED` |
| Seriousness Criteria | Hospitalization, Medically Significant | `CONFIRMED` |
| Inpatient Hospitalization | Yes (Hospitalized) | `CONFIRMED` |
| Hospital Admission Date | 02-NOV-2025 | `CONFIRMED` |
| Medically Important | Yes (Medically Important) | `CONFIRMED` |

#### Section: Laboratory & Diagnostic Investigations Matrix (Scope: `ICSR` | Type: `TABLE`)
| Test / Parameter | Date | Result | Unit | Normal Range | Interpretation |
|:---|:---|:---|:---|:---|:---|
| 24-hour ambulatory video EEG | 14-NOV-2025 | normalization of cerebral background activity with zero epileptiform spike-wave discharges | Not stated | Not stated | Normalization of background rhythms without epileptiform discharges |
| Brain MRI with contrast | Not stated | No structural epileptogenic focus | Not stated | Not stated | Normal |

#### Section: Clinical Chronological Narrative (Scope: `ICSR` | Type: `NARRATIVE`)
**Narrative Text:**

A 52-year-old male patient (David Miller) with neuropathic pain initiated treatment with Neuroval on October 15, 2025. Following a rapid dose titration from 200 mg to 400 mg daily, the patient experienced a witnessed generalized tonic-clonic seizure 48 hours post-escalation. The patient was emergently admitted to the Columbia University Neurological ICU on November 2, 2025. Neuroval was permanently discontinued on November 2, 2025. Follow-up evaluation on November 16, 2025, confirmed that the patient has remained entirely seizure-free for 14 consecutive days without ongoing anticonvulsant therapy. A repeat 24-hour ambulatory video EEG on November 14, 2025, demonstrated normalization of cerebral background activity with zero epileptiform spike-wave discharges, and a brain MRI with contrast revealed no structural epileptogenic focus. Dechallenge is positive, and the case outcome is fully recovered/resolved.

#### Section: Regulatory & Manufacturer Processing Metadata (Scope: `ICSR` | Type: `GRID`)
| Parameter | Rendered Value | Status |
|:---|:---|:---|
| Report Classification | FOLLOW-UP REPORT #1 | `CONFIRMED` |

### 4. Evidence Shown to Reviewer
| Displayed Fact | Source Document | Page / Location | Anchor Level | Displayed Evidence Snippet |
|:---|:---|:---|:---|:---|
| Patient Identifier: **D.M. (David Miller)** | `fda_medwatch_followup.pdf` | `Page 1, Block 5` | `LEVEL_1_EXACT_VISUAL` | “1. PATIENT IDENTIFIER: D.M. (David Miller) 2. AGE: 52 YRS 2a. DOB: 11-FEB-1973 3. SEX: MALE 4. WE...” |
| Date of Birth: **11-FEB-1973** | `fda_medwatch_followup.pdf` | `Page 1, Block 5` | `LEVEL_1_EXACT_VISUAL` | “1. PATIENT IDENTIFIER: D.M. (David Miller) 2. AGE: 52 YRS 2a. DOB: 11-FEB-1973 3. SEX: MALE 4. WE...” |
| Patient Age: **52 YRS** | `fda_medwatch_followup.pdf` | `Page 1, Block 5` | `LEVEL_1_EXACT_VISUAL` | “1. PATIENT IDENTIFIER: D.M. (David Miller) 2. AGE: 52 YRS 2a. DOB: 11-FEB-1973 3. SEX: MALE 4. WE...” |
| Sex / Gender: **MALE** | `fda_medwatch_followup.pdf` | `Page 1, Block 5` | `LEVEL_1_EXACT_VISUAL` | “1. PATIENT IDENTIFIER: D.M. (David Miller) 2. AGE: 52 YRS 2a. DOB: 11-FEB-1973 3. SEX: MALE 4. WE...” |
| Patient Weight: **79 kg** | `fda_medwatch_followup.pdf` | `Page 1, Block 5` | `LEVEL_1_EXACT_VISUAL` | “1. PATIENT IDENTIFIER: D.M. (David Miller) 2. AGE: 52 YRS 2a. DOB: 11-FEB-1973 3. SEX: MALE 4. WE...” |
| Patient Country: **United States** | `imap_23.eml` | `SECTION A` | `LEVEL_3_SNIPPET_ONLY` | “1. PATIENT IDENTIFIER: D.M. (David Miller) 2. AGE: 52 YRS 2a. DOB: 11-FEB-1973 3. SEX: MALE 4. WE...” |
| Reporter Name: **Dr. Richard Vance** | `fda_medwatch_followup.pdf` | `Page 1, Block 14` | `LEVEL_1_EXACT_VISUAL` | “REPORTER: Dr. Richard Vance, MD, PhD (Attending Neurologist) Department of Neurology, Columbia Un...” |
| Reporter Qualification: **Physician** | `imap_23.eml` | `SECTION E` | `LEVEL_3_SNIPPET_ONLY` | “REPORTER: Dr. Richard Vance, MD, PhD (Attending Neurologist) Department of Neurology, Columbia Un...” |
| Medical Specialty: **Attending Neurologist** | `fda_medwatch_followup.pdf` | `Page 1, Block 14` | `LEVEL_1_EXACT_VISUAL` | “REPORTER: Dr. Richard Vance, MD, PhD (Attending Neurologist) Department of Neurology, Columbia Un...” |
| Health Professional: **Yes (HCP Confirmed)** | `fda_medwatch_followup.pdf` | `Page 1, Block 12` | `LEVEL_1_EXACT_VISUAL` | “DECHALLENGE: [ X ] YES — Event abated after withdrawal RECHALLENGE: [ X ] NOT DONE” |
| Institution / Clinic: **Columbia University Irving Medical Center, Department of Neurology** | `fda_medwatch_followup.pdf` | `Page 1, Block 14` | `LEVEL_1_EXACT_VISUAL` | “REPORTER: Dr. Richard Vance, MD, PhD (Attending Neurologist) Department of Neurology, Columbia Un...” |
| Country: **United States** | `imap_23.eml` | `SECTION E` | `LEVEL_3_SNIPPET_ONLY` | “REPORTER: Dr. Richard Vance, MD, PhD (Attending Neurologist) Department of Neurology, Columbia Un...” |
| Contact Information: **Tel: (212) 555-0199 | Email: rvance@columbia-neurology.org** | `fda_medwatch_followup.pdf` | `Page 1, Block 14` | `LEVEL_1_EXACT_VISUAL` | “REPORTER: Dr. Richard Vance, MD, PhD (Attending Neurologist) Department of Neurology, Columbia Un...” |
| Suspect Product: **Neuroval** | `fda_medwatch_followup.pdf` | `Page 1, Block 10` | `LEVEL_1_EXACT_VISUAL` | “PRODUCT: Neuroval (neuroval HCl) 200mg/400mg DOSE: Titrated to 400 mg PO QD LOT #: Lot #NV-2025-1...” |
| Dosage Formulation: **neuroval HCl** | `fda_medwatch_followup.pdf` | `Page 1, Block 10` | `LEVEL_1_EXACT_VISUAL` | “PRODUCT: Neuroval (neuroval HCl) 200mg/400mg DOSE: Titrated to 400 mg PO QD LOT #: Lot #NV-2025-1...” |
| Administered Dose: **400 mg** | `fda_medwatch_followup.pdf` | `Page 1, Block 10` | `LEVEL_1_EXACT_VISUAL` | “PRODUCT: Neuroval (neuroval HCl) 200mg/400mg DOSE: Titrated to 400 mg PO QD LOT #: Lot #NV-2025-1...” |
| Dosing Frequency: **QD** | `fda_medwatch_followup.pdf` | `Page 1, Block 10` | `LEVEL_1_EXACT_VISUAL` | “PRODUCT: Neuroval (neuroval HCl) 200mg/400mg DOSE: Titrated to 400 mg PO QD LOT #: Lot #NV-2025-1...” |
| Route of Administration: **PO** | `fda_medwatch_followup.pdf` | `Page 1, Block 10` | `LEVEL_1_EXACT_VISUAL` | “PRODUCT: Neuroval (neuroval HCl) 200mg/400mg DOSE: Titrated to 400 mg PO QD LOT #: Lot #NV-2025-1...” |
| Therapy Start Date: **15-OCT-2025** | `fda_medwatch_followup.pdf` | `Page 1, Block 11` | `LEVEL_1_EXACT_VISUAL` | “THERAPY DATES: 15-OCT-2025 to 02-NOV-2025” |
| Therapy Stop Date: **02-NOV-2025** | `fda_medwatch_followup.pdf` | `Page 1, Block 7` | `LEVEL_1_EXACT_VISUAL` | “FOLLOW-UP CLINICAL COURSE (14-DAY POST-DISCONTINUATION REVIEW): Initial report dated 02-NOV-2025 ...” |
| Product Lot / Batch: **Lot #NV-2025-110** | `fda_medwatch_followup.pdf` | `Page 1, Block 10` | `LEVEL_1_EXACT_VISUAL` | “PRODUCT: Neuroval (neuroval HCl) 200mg/400mg DOSE: Titrated to 400 mg PO QD LOT #: Lot #NV-2025-1...” |
| Expiration Date: **09/27** | `fda_medwatch_followup.pdf` | `Page 1, Block 10` | `LEVEL_1_EXACT_VISUAL` | “PRODUCT: Neuroval (neuroval HCl) 200mg/400mg DOSE: Titrated to 400 mg PO QD LOT #: Lot #NV-2025-1...” |
| Action Taken with Drug: **Drug permanently withdrawn** | `fda_medwatch_followup.pdf` | `Page 1, Block 8` | `LEVEL_1_EXACT_VISUAL` | “DECHALLENGE CONFIRMATION: Neuroval was permanently withdrawn on 02-NOV-2025. Follow-up evaluation...” |
| Adverse Reaction: **generalized tonic-clonic seizure** | `fda_medwatch_followup.pdf` | `Page 1, Block 7` | `LEVEL_1_EXACT_VISUAL` | “FOLLOW-UP CLINICAL COURSE (14-DAY POST-DISCONTINUATION REVIEW): Initial report dated 02-NOV-2025 ...” |
| Seriousness Criteria: **Hospitalization, Medically Significant** | `imap_23.eml` | `SECTION B` | `LEVEL_3_SNIPPET_ONLY` | “Initial report dated 02-NOV-2025 documented a witnessed generalized tonic-clonic seizure occurrin...” |
| Inpatient Hospitalization: **Yes (Hospitalized)** | `fda_medwatch_followup.pdf` | `Page 1, Block 12` | `LEVEL_1_EXACT_VISUAL` | “DECHALLENGE: [ X ] YES — Event abated after withdrawal RECHALLENGE: [ X ] NOT DONE” |
| Hospital Admission Date: **02-NOV-2025** | `fda_medwatch_followup.pdf` | `Page 1, Block 7` | `LEVEL_1_EXACT_VISUAL` | “FOLLOW-UP CLINICAL COURSE (14-DAY POST-DISCONTINUATION REVIEW): Initial report dated 02-NOV-2025 ...” |
| Medically Important: **Yes (Medically Important)** | `fda_medwatch_followup.pdf` | `Page 1, Block 12` | `LEVEL_1_EXACT_VISUAL` | “DECHALLENGE: [ X ] YES — Event abated after withdrawal RECHALLENGE: [ X ] NOT DONE” |
| Dechallenge Outcome: **Positive (resolved/improved upon discontinuation)** | `fda_medwatch_followup.pdf` | `Page 1, Block 8` | `LEVEL_1_EXACT_VISUAL` | “DECHALLENGE CONFIRMATION: Neuroval was permanently withdrawn on 02-NOV-2025. Follow-up evaluation...” |
| Rechallenge Outcome: **Not stated** | `fda_medwatch_followup.pdf` | `Page 1, Block 12` | `LEVEL_1_EXACT_VISUAL` | “DECHALLENGE: [ X ] YES — Event abated after withdrawal RECHALLENGE: [ X ] NOT DONE” |

### 5. Reviewer Flags / Warnings
- ✓ **Clean Processing State:** Structural and evidence-integrity checks passed. No conflicting evidence, handwriting ambiguities, or unstated critical parameters detected.
- **Validation Gating Status:** `READY_FOR_REVIEW`

### 6. Human Review State
- **Current Intake Status:** `TRIAGED`
- **Review Urgency Priority:** `EXPEDITED`
- **Confidence Score:** `100%`
- **Available Reviewer Primary Actions:** `[✓ Confirm AI Case]`, `[✎ Override / Edit]`, `[🚩 Flag for Escalation]`

### 7. Source Reference Section
- **Original Email File:** `test-data/emails/email_06.eml`
- **Original PDF Attachment(s):** `test-data/pdfs/.../fda_medwatch_followup.pdf`

**Source Email Excerpt:**
```text
Dear Pharmacovigilance Team,
This is follow-up report #1 to our initial safety report (Case Ref: CR-2025-US-00744) regarding patient David Miller (52yo male) who experienced a generalized tonic-clonic seizure 48 hours following dose escalation of Neuroval to 400 mg daily.
I am pleased to report that following complete discontinuation of Neuroval on November 2nd, the patient has remained completely seizure-free for 14 consecutive days. Repeat 24-hour video EEG showed normalization of background rhythms without epileptiform discharges. Positive de-challenge is clinically confirmed.
Attached is the updated FDA Form 3500A with Section B and C marked for follow-up resolution.
Sincerely,
Dr. Richard Vance, MD
...
```

**Source PDF Excerpt (`fda_medwatch_followup.pdf`):**
```text
DEPARTMENT OF HEALTH AND HUMAN SERVICES — FOOD AND DRUG ADMINISTRATION
MEDWATCH: FORM FDA 3500A (10/15) — MANDATORY ADVERSE EVENT REPORTING
FOLLOW-UP REPORT #1 (CLINICAL RESOLUTION & DECHALLENGE CONFIRMATION)
Original Case Reference: CR-2025-US-00744  |  OMB Control No. 0910-0291
SECTION A: PATIENT IDENTIFIER
1. PATIENT IDENTIFIER: D.M. (David Miller)
2. AGE: 52 YRS
2a. DOB: 11-FEB-1973
...
```

---

## CASE-07

### 1. Case Identification
- **Case ID:** `CASE-007`
- **Email Subject:** PRODUCT QUALITY COMPLAINT: Compromised Blister Foil & Oxidized Tablets (Lot #BL-8802)
- **Sender:** Robert Vance, PharmD (clinevo.test.inbox12@gmail.com)
- **Date:** Mon Nov 17 20:00:00 IST 2025
- **Attachment Filenames:** packaging_defect_report.pdf
- **Primary Category:** `Quality Complaint (PQC)`
- **All Categories / Labels:** ['Quality Complaint (PQC)']
- **Multi-Label Status:** `No`
- **AI Confidence:** `100%`
- **Clinical Urgency / Clock:** `STANDARD`

### 2. Reviewer-Facing Summary
> This incoming medical communication comprises an official Product Quality Complaint and attached inspection form submitted by Dr. Robert Vance, Director of Pharmacy Operations at MetroHealth Medical Center. The report identifies significant physical defects involving Cardioril 10mg Film-Coated Tablets from Lot #BL-8802 (Expiration Date: 11/2026). Specifically, pharmacy technicians discovered widespread packaging integrity failures where the aluminum lidding foil was unsealed and peeling away from the PVC blister cavities. As a direct result of this exposure to ambient humidity, the enclosed tablets exhibit severe surface degradation, including dark yellowish-brown speckling, chemical oxidation, softening, edge chipping, and friability breakdown. A rigorous patient impact assessment confirms that zero units from this compromised lot were dispensed to patients or hospital wards, and no adverse clinical reactions or events occurred. All 12 affected wholesale boxes, totaling 360 blister strips and 3,600 tablets, have been successfully intercepted and placed into secure locked quarantine under Quarantine Seal #Q-2025-094. The pharmacy has requested immediate product replacement and return shipping instructions from the manufacturer. From a regulatory and pharmacovigilance triage standpoint, this communication requires classification strictly as a Product Quality Complaint due to the absence of patient exposure or adverse events. The enterprise quality assurance team must immediately log this incident into the PQC tracking system, initiate a formal root cause investigation with manufacturing and packaging plants, and coordinate inventory retrieval and replacement with the complainant. No expedited ICSR safety reporting to regulatory authorities is warranted at this time, but standard PQC investigation timelines and batch history reviews must be strictly enforced.

### 3. Structured Review Content
#### Section: Product Quality Complaint Parameters (Scope: `PQC` | Type: `GRID`)
| Parameter | Rendered Value | Status |
|:---|:---|:---|
| Defective Product | Cardioril 10mg Film-Coated Tablets | `CONFIRMED` |
| Lot / Batch Number | BL-8802 | `CONFIRMED` |
| Physical Defect Classification | Packaging Integrity Failure & Chemical Oxidation / Degradation | `CONFIRMED` |
| Container Closure Integrity | Breached (Integrity Compromised) | `CONFIRMED` |
| Defect Narrative Description | Aluminum lidding foil was unsealed and peeling away from the clear PVC/PVDC thermoformed cavities along the top margin of multiple blister strips. Enclosed 10mg tablets exposed to ambient humidity exhibited severe surface degradation: dark yellowish-brown speckling/oxidation, softening, edge chipping, and friability breakdown. | `CONFIRMED` |

#### Section: Physical Defect Visual Assessment (Scope: `PQC` | Type: `GRID`)
| Parameter | Rendered Value | Status |
|:---|:---|:---|
| Physical Photo Evidence | No Photo Attached | `CONFIRMED` |
| Quality Review Status | Standard Ingestion | `CONFIRMED` |

### 4. Evidence Shown to Reviewer
| Displayed Fact | Source Document | Page / Location | Anchor Level | Displayed Evidence Snippet |
|:---|:---|:---|:---|:---|
| Packaging Breached: **Yes (Closure Compromised)** | `imap_24.eml` | `Page 1` | `LEVEL_3_SNIPPET_ONLY` | “During automated inventory intake inspection, pharmacy technicians noted widespread packaging sea...” |

### 5. Reviewer Flags / Warnings
- ✓ **Clean Processing State:** Structural and evidence-integrity checks passed. No conflicting evidence, handwriting ambiguities, or unstated critical parameters detected.
- **Validation Gating Status:** `READY_FOR_REVIEW`

### 6. Human Review State
- **Current Intake Status:** `TRIAGED`
- **Review Urgency Priority:** `STANDARD`
- **Confidence Score:** `100%`
- **Available Reviewer Primary Actions:** `[✓ Confirm AI Case]`, `[✎ Override / Edit]`, `[🚩 Flag for Escalation]`

### 7. Source Reference Section
- **Original Email File:** `test-data/emails/email_07.eml`
- **Original PDF Attachment(s):** `test-data/pdfs/.../packaging_defect_report.pdf`

**Source Email Excerpt:**
```text
To Quality Assurance & Complaints Investigation,
Our central pharmacy is filing an official Product Quality Complaint regarding Cardioril 10mg blister packs, Lot #BL-8802, Expiration Date: 11/2026.
During routine unit-dose dispensing, pharmacy technicians identified multiple cartons where the aluminum foil backing was unsealed and peeling away from the PVC blister cavities. The enclosed tablets display dark discoloration, surface oxidation, and severe crumbling.
No medication from this shipment was dispensed to patients; zero adverse events have occurred. All 12 boxes (360 blister strips) from Lot #BL-8802 have been quarantined in our pharmacy quarantine cage.
Please find our internal Pharmacy Defect Inspection Form attached. We request immediate replacement and return shipping instructions.
Robert Vance, PharmD, BCPS
...
```

**Source PDF Excerpt (`packaging_defect_report.pdf`):**
```text
METROHEALTH MEDICAL CENTER — CENTRAL PHARMACY OPERATIONS
PHARMACEUTICAL PRODUCT QUALITY COMPLAINT & DEFECT LOG
Standard Operating Procedure QA-PHARM-402 — Mandatory Supplier Incident Notification
1. COMPLAINT & PRODUCT IDENTIFICATION
COMPLAINT ID: PQC-MH-2025-088
DATE LOGGED: 17-NOV-2025
DISCOVERY AREA: Central Inpatient Unit-Dose
Packager
...
```

---

## CASE-08

### 1. Case Identification
- **Case ID:** `CASE-008`
- **Email Subject:** Urgent Quality Notice: Suspected Counterfeit Packaging - Lipocur 20mg (Lot #LP-44109)
- **Sender:** Karen Patel, RPh (clinevo.test.inbox12@gmail.com)
- **Date:** Tue Nov 18 20:45:45 IST 2025
- **Attachment Filenames:** None
- **Primary Category:** `Quality Complaint (PQC)`
- **All Categories / Labels:** ['Quality Complaint (PQC)']
- **Multi-Label Status:** `No`
- **AI Confidence:** `100%`
- **Clinical Urgency / Clock:** `CRITICAL`

### 2. Reviewer-Facing Summary
> This urgent communication originates from Karen Patel, RPh, Pharmacist-in-Charge at Apex Care Pharmacy in Boston, MA, reporting a critical product quality issue regarding Lipocur 20mg tablets, Lot #LP-44109. The pharmacy identified three distinct physical packaging anomalies during routine intake inspection of a recent wholesale delivery. Specifically, the bottles lack the standard induction inner heat-seal, display misaligned expiration date typography with a missing 2D data matrix barcode, and feature an aberrant darker blue bottle cap color compared to authentic commercial stock. The reporting pharmacist has exercised appropriate professional diligence by immediately quarantining all ten affected bottles within the pharmacy vault to prevent any inadvertent dispensing. Crucially, the communication explicitly confirms that no units have been sold to consumers and zero patients have ingested the suspected counterfeit medication. Consequently, there is no associated adverse event or patient harm, precluding the necessity for an Individual Case Safety Report (ICSR). The primary clinical and regulatory concern centers on supply chain integrity, falsified medicines, and potential lack of sterility or active ingredient integrity. The sender is actively requesting instructions for a formal chain-of-custody pickup to facilitate laboratory authentication and forensic investigation by the manufacturer. Regulatory triage requires immediate forwarding of this notification to the Quality Assurance and Global Supply Security divisions to initiate a high-priority counterfeit investigation and coordinate product retrieval. The enterprise must also evaluate whether a broader distribution recall or regulatory agency notification is warranted based on the lot verification.

### 3. Structured Review Content
#### Section: Product Quality Complaint Parameters (Scope: `PQC` | Type: `GRID`)
| Parameter | Rendered Value | Status |
|:---|:---|:---|
| Defective Product | Lipocur 20mg tablets | `CONFIRMED` |
| Lot / Batch Number | LP-44109 | `CONFIRMED` |
| Physical Defect Classification | Suspected counterfeit or tampered packaging / Missing induction inner heat-seal, misaligned expiration date typography lacking 2D data matrix barcode, and off-shade darker blue bottle cap | `CONFIRMED` |
| Container Closure Integrity | Breached (Integrity Compromised) | `CONFIRMED` |
| Defect Narrative Description | Upon physical inspection, three packaging defects were observed: (1) The bottle neck lacks the standard induction inner heat-seal. (2) The expiration date typography on the bottle label does not match usual commercial stock (font is misaligned and lacks the 2D data matrix barcode). (3) The bottle cap color is a noticeably darker shade of blue than official product packaging. | `CONFIRMED` |

#### Section: Physical Defect Visual Assessment (Scope: `PQC` | Type: `GRID`)
| Parameter | Rendered Value | Status |
|:---|:---|:---|
| Physical Photo Evidence | No Photo Attached | `CONFIRMED` |
| Quality Review Status | Mandatory Human Verification Required | `CONFIRMED` |

### 4. Evidence Shown to Reviewer
| Displayed Fact | Source Document | Page / Location | Anchor Level | Displayed Evidence Snippet |
|:---|:---|:---|:---|:---|
| Packaging Breached: **Yes (Closure Compromised)** | `imap_25.eml` | `Email Body` | `LEVEL_3_SNIPPET_ONLY` | “Upon physical inspection, we strongly suspect counterfeit or tampered packaging: 1. The bottle ne...” |

### 5. Reviewer Flags / Warnings
- ⚠️ **Mandatory Defect Photo Inspection** (`PHOTO_DEFECT_INSPECTION`): Not stated [Action: *Inspect photo asset in viewer*]
- **Validation Gating Status:** `REVIEW_WITH_WARNINGS`

### 6. Human Review State
- **Current Intake Status:** `TRIAGED`
- **Review Urgency Priority:** `CRITICAL`
- **Confidence Score:** `100%`
- **Available Reviewer Primary Actions:** `[✓ Confirm AI Case]`, `[✎ Override / Edit]`, `[🚩 Flag for Escalation]`

### 7. Source Reference Section
- **Original Email File:** `test-data/emails/email_08.eml`

**Source Email Excerpt:**
```text
Dear Quality Complaints Team,
I am writing as the Pharmacist-in-Charge at Apex Care Pharmacy in Boston, MA. We received a delivery yesterday from a secondary wholesaler containing 10 bottles of Lipocur 20mg tablets (Lot #LP-44109).
Upon physical inspection, we strongly suspect counterfeit or tampered packaging:
1. The bottle neck lacks the standard induction inner heat-seal.
2. The expiration date typography on the bottle label does not match our usual commercial stock (font is misaligned and lacks the 2D data matrix barcode).
3. The bottle cap color is a noticeably darker shade of blue than official product packaging.
...
```

---

## CASE-09

### 1. Case Identification
- **Case ID:** `CASE-009`
- **Email Subject:** Medical Information Request: Can Corzapan 10mg tablets be crushed for NG-tube administration?
- **Sender:** David Wu, BCPS (clinevo.test.inbox12@gmail.com)
- **Date:** Thu Nov 20 03:10:00 IST 2025
- **Attachment Filenames:** None
- **Primary Category:** `Medical Information (MI)`
- **All Categories / Labels:** ['Medical Information (MI)']
- **Multi-Label Status:** `No`
- **AI Confidence:** `100%`
- **Clinical Urgency / Clock:** `STANDARD`

### 2. Reviewer-Facing Summary
> The incoming communication is a professional medical inquiry submitted by Dr. David Wu, a clinical oncology pharmacist at UCSF Medical Center. The sender is requesting clinical pharmacology, pharmacokinetic, and stability data regarding the administration of Corzapan 10mg tablets via nasogastric (NG) feeding tubes. Specifically, the pharmacist asks whether the film-coated tablets can be safely crushed and suspended in sterile water for enteral delivery. Furthermore, the inquiry addresses potential drug adsorption onto polyurethane feeding tubes and compatibility issues with co-administered enteral nutrition formulas. The patient described is an elderly individual with severe dysphagia prescribed Corzapan 10mg for chronic hypertension. The communication explicitly notes that there is no patient adverse event, reaction, or product defect associated with this request. This is strictly a prospective, non-urgent clinical information inquiry regarding drug administration technique and product handling. No safety signals or quality complaints are triggered by this message. Therefore, the communication is classified exclusively under Medical Information. The recommended regulatory action is to route this inquiry directly to the Medical Affairs or Medical Information department for a standard evidence-based response regarding enteral administration guidelines for Corzapan.

### 3. Structured Review Content
#### Section: Medical Information Classification (Scope: `MI` | Type: `GRID`)
| Parameter | Rendered Value | Status |
|:---|:---|:---|
| Inquired Product / Subject | Corzapan 10mg tablets | `CONFIRMED` |
| Inquiry Classification | Route of administration, pharmacokinetic stability, and enteral feeding compatibility | `CONFIRMED` |
| Response Urgency | Standard | `CONFIRMED` |

#### Section: Inquired Medical & Scientific Questions (Scope: `MI` | Type: `TABLE`)
| Item | Clinical Question |
|:---|:---|
| #1 | Could your medical affairs team please provide any pharmacokinetic or stability data regarding: |
| #2 | Crushing Corzapan 10mg tablets for enteral administration. |
| #3 | Potential adsorption of the active substance to polyurethane enteral feeding tubes. |
| #4 | Co-administration with enteral nutrition formulas. |

### 4. Evidence Shown to Reviewer
| Displayed Fact | Source Document | Page / Location | Anchor Level | Displayed Evidence Snippet |
|:---|:---|:---|:---|:---|
| Inquired Product: **Corzapan 10mg tablets** | `imap_26.eml` | `Email Header` | `LEVEL_1_EXACT_VISUAL` | “From: David Wu, BCPS <clinevo.test.inbox12@gmail.com> Date: Wed, 19 Nov 2025 13:40:00 -0800 Subje...” |
| Inquiry Classification: **Route of administration, pharmacokinetic stability, and enteral feeding compatibility** | `imap_26.eml` | `Email Body` | `LEVEL_1_EXACT_VISUAL` | “Can Corzapan 10mg tablets be crushed for NG-tube administration? ... Could your medical affairs t...” |
| Inquiry Question: **Could your medical affairs team please provide any pharmacokinetic or stability data regarding: 1. Crushing Corzapan 10mg tablets for enteral administration. 2. Potential adsorption of the active substance to polyurethane enteral feeding tubes. 3. Co-administration with enteral nutrition formulas.** | `imap_26.eml` | `Email Body` | `LEVEL_1_EXACT_VISUAL` | “Can Corzapan 10mg tablets be crushed for NG-tube administration? ... Could your medical affairs t...” |

### 5. Reviewer Flags / Warnings
- ✓ **Clean Processing State:** Structural and evidence-integrity checks passed. No conflicting evidence, handwriting ambiguities, or unstated critical parameters detected.
- **Validation Gating Status:** `READY_FOR_REVIEW`

### 6. Human Review State
- **Current Intake Status:** `TRIAGED`
- **Review Urgency Priority:** `STANDARD`
- **Confidence Score:** `100%`
- **Available Reviewer Primary Actions:** `[✓ Confirm AI Case]`, `[✎ Override / Edit]`, `[🚩 Flag for Escalation]`

### 7. Source Reference Section
- **Original Email File:** `test-data/emails/email_09.eml`

**Source Email Excerpt:**
```text
Dear Medical Information Department,
I am a clinical oncology pharmacist at UCSF Medical Center caring for an elderly patient with severe dysphagia who has an active nasogastric (NG) feeding tube in place.
The patient has been prescribed Corzapan 10mg once daily for chronic hypertension. The package insert indicates film-coated tablets but does not explicitly state whether the tablets can be crushed and suspended in sterile water for enteral feeding tube delivery without altering bioavailability or causing tube occlusion.
Could your medical affairs team please provide any pharmacokinetic or stability data regarding:
1. Crushing Corzapan 10mg tablets for enteral administration.
2. Potential adsorption of the active substance to polyurethane enteral feeding tubes.
...
```

---

## CASE-10

### 1. Case Identification
- **Case ID:** `CASE-010`
- **Email Subject:** Early Bird Registration Open: 14th Annual Global AI in Pharmacovigilance & Drug Safety Summit
- **Sender:** PharmaTech Global Summit (clinevo.test.inbox12@gmail.com)
- **Date:** Thu Nov 20 13:30:00 IST 2025
- **Attachment Filenames:** None
- **Primary Category:** `Not Relevant`
- **All Categories / Labels:** ['Not Relevant']
- **Multi-Label Status:** `No`
- **AI Confidence:** `100%`
- **Clinical Urgency / Clock:** `STANDARD`

### 2. Reviewer-Facing Summary
> The incoming communication is an automated promotional email from PharmaTech Global Summit advertising the 14th Annual Global AI in Pharmacovigilance & Drug Safety Summit scheduled for March 2026. The message outlines key sessions related to artificial intelligence in Individual Case Safety Report (ICSR) intake automation, Good Vigilance Practice (GVP) module compliance, literature screening, and signal detection. It provides early bird registration details, discount codes, and promotional links for prospective attendees. No identifiable patient information, adverse event details, product quality defects, or specific medical inquiries are present within the correspondence. Consequently, the document carries zero clinical or regulatory safety reporting obligation. It represents standard commercial spam and vendor solicitation directed at pharmaceutical professionals. The recommended regulatory action is to classify the document as non-relevant and route it to administrative archiving without further pharmacovigilance triage.

### 3. Structured Review Content
#### Section: Triage Determination (Scope: `ALL` | Type: `GRID`)
| Parameter | Rendered Value | Status |
|:---|:---|:---|
| Exclusion Rationale | The incoming communication is an automated promotional email from PharmaTech Global Summit advertising the 14th Annual Global AI in Pharmacovigilance & Drug Safety Summit scheduled for March 2026. The message outlines key sessions related to artificial intelligence in Individual Case Safety Report (ICSR) intake automation, Good Vigilance Practice (GVP) module compliance, literature screening, and signal detection. It provides early bird registration details, discount codes, and promotional links for prospective attendees. No identifiable patient information, adverse event details, product quality defects, or specific medical inquiries are present within the correspondence. Consequently, the document carries zero clinical or regulatory safety reporting obligation. It represents standard commercial spam and vendor solicitation directed at pharmaceutical professionals. The recommended regulatory action is to classify the document as non-relevant and route it to administrative archiving without further pharmacovigilance triage. | `CONFIRMED` |
| Reportability Threshold | Below pharmacovigilance reportability threshold | `CONFIRMED` |

#### Section: Source Transmission Excerpt (Scope: `ALL` | Type: `NARRATIVE`)
**Narrative Text:**

Join 500+ global safety leaders, regulatory directors, and AI pioneers in Boston, MA on March 24–26, 2026!

Keynote sessions include:
• Generative AI & LLMs in ICSR Intake Automation
• GVP Module VI Inspection Readiness in 2026
• Automating Literature Screening with Multimodal AI
• Real-World Eviden

### 4. Evidence Shown to Reviewer
*(No discrete citation pins rendered for this case classification)*

### 5. Reviewer Flags / Warnings
- ✓ **Clean Processing State:** Structural and evidence-integrity checks passed. No conflicting evidence, handwriting ambiguities, or unstated critical parameters detected.
- **Validation Gating Status:** `READY_FOR_REVIEW`

### 6. Human Review State
- **Current Intake Status:** `TRIAGED`
- **Review Urgency Priority:** `STANDARD`
- **Confidence Score:** `100%`
- **Available Reviewer Primary Actions:** `[✓ Confirm AI Case]`, `[✎ Override / Edit]`, `[🚩 Flag for Escalation]`

### 7. Source Reference Section
- **Original Email File:** `test-data/emails/email_10.eml`
- **Original PDF Attachment(s):** `test-data/pdfs/.../pharmatech_conference_prospectus.pdf`

**Source Email Excerpt:**
```text
Join 500+ global safety leaders, regulatory directors, and AI pioneers in Boston, MA on March 24–26, 2026!
Keynote sessions include:
• Generative AI & LLMs in ICSR Intake Automation
• GVP Module VI Inspection Readiness in 2026
• Automating Literature Screening with Multimodal AI
• Real-World Evidence & Signal Detection Case Studies
...
```

**Source PDF Excerpt (`pharmatech_conference_prospectus.pdf`):**
```text
14TH ANNUAL GLOBAL PHARMACEUTICAL AI & COMPLIANCE SUMMIT 2026
SPONSORSHIP & EXHIBITOR PROSPECTUS — BOSTON CONVENTION CENTER, MARCH 24–26, 2026
WHY SPONSOR PHARMATECH 2026?
Connect with over 750 senior decision-makers from top 50 pharmaceutical enterprises, regulatory agencies, and AI technology vendors. Our
attendees represent VPs of Pharmacovigilance, Global Safety Directors, and Chief Digital Health Officers.
SPONSORSHIP PACKAGES:
Tier Package
Booth Space
...
```

---

## CASE-11

### 1. Case Identification
- **Case ID:** `CASE-011`
- **Email Subject:** Medical Information Request: In-Use Compatibility & Dilution Stability for Cefatox 1g in D5W
- **Sender:** Dr. Elena Rostova, PharmD, BCPS (clinevo.test.inbox12@gmail.com)
- **Date:** Fri Nov 21 19:45:00 IST 2025
- **Attachment Filenames:** None
- **Primary Category:** `Medical Information (MI)`
- **All Categories / Labels:** ['Medical Information (MI)']
- **Multi-Label Status:** `No`
- **AI Confidence:** `100%`
- **Clinical Urgency / Clock:** `STANDARD`

### 2. Reviewer-Facing Summary
> The incoming communication is an official clinical inquiry originating from Dr. Elena Rostova, a Senior Clinical Compounding Specialist at Massachusetts General Hospital. The inquiry is directed toward the Medical Information and Medical Affairs team regarding the pharmaceutical stability and compatibility parameters of Cefatox (cefatoxime sodium) 1g for Injection. Specifically, the hospital pharmacy team is seeking scientific documentation, monograph data, and formal guidance on chemical stability and potency retention exceeding 95% when reconstituted and diluted in 100 mL of Dextrose 5% in Water (D5W) under refrigerated storage conditions for up to 48 hours. Furthermore, the communication requests in-use stability data at controlled room temperature during a prolonged 4-hour intravenous infusion, as well as Y-site co-infusion compatibility data with standard 0.9% Sodium Chloride or Lactated Ringer's solutions. The stated purpose of this communication is to facilitate the standardization of hospital-wide intravenous infusion protocols for adult surgical prophylaxis. Crucially, the sender explicitly confirms that there are no adverse patient events, no clinical complications, no patient identifiers, and no physical product defects associated with the current product stock. Therefore, this communication lacks any criteria for a Safety Report (ICSR) or a Product Quality Complaint (PQC). The urgency is routine and operational, driven by institutional pharmacy workflow enhancements. The recommended regulatory action is to route this communication directly to the Medical Information department to provide standard-of-care, evidence-based responses, package insert details, and published stability literature in accordance with company standard operating procedures.

### 3. Structured Review Content
#### Section: Medical Information Classification (Scope: `MI` | Type: `GRID`)
| Parameter | Rendered Value | Status |
|:---|:---|:---|
| Inquired Product / Subject | Cefatox (cefotaxime sodium) 1g for Injection | `CONFIRMED` |
| Inquiry Classification | In-use stability, dilution stability, and Y-site compatibility inquiry | `CONFIRMED` |
| Response Urgency | Standard | `CONFIRMED` |

#### Section: Inquired Medical & Scientific Questions (Scope: `MI` | Type: `TABLE`)
| Item | Clinical Question |
|:---|:---|
| #1 | Could Medical Affairs please provide documentation or monograph data addressing: |
| #2 | Chemical stability and potency retention (>95%) of Cefatox 1g in 100 mL D5W at refrigerated temperatures (2 deg C to 8 deg C) for up to 48 hours. |
| #3 | In-use room temperature (20 deg C to 25 deg C) stability during a prolonged 4-hour intravenous infusion. |
| #4 | Compatibility with Y-site co-infusion of standard 0.9% Sodium Chloride or Lactated Ringer's solution. |

### 4. Evidence Shown to Reviewer
| Displayed Fact | Source Document | Page / Location | Anchor Level | Displayed Evidence Snippet |
|:---|:---|:---|:---|:---|
| Inquired Product: **Cefatox (cefotaxime sodium) 1g for Injection** | `imap_28.eml` | `Email Body, Paragraph 2` | `LEVEL_1_EXACT_VISUAL` | “I am writing on behalf of our inpatient pharmacy clinical operations team at Massachusetts Genera...” |
| Inquiry Classification: **In-use stability, dilution stability, and Y-site compatibility inquiry** | `imap_28.eml` | `Email Body, Paragraph 4` | `LEVEL_1_EXACT_VISUAL` | “Could Medical Affairs please provide documentation or monograph data addressing: 1. Chemical stab...” |
| Inquiry Question: **Could Medical Affairs please provide documentation or monograph data addressing: 1. Chemical stability and potency retention (>95%) of Cefatox 1g in 100 mL D5W at refrigerated temperatures (2 deg C to 8 deg C) for up to 48 hours. 2. In-use room temperature (20 deg C to 25 deg C) stability during a prolonged 4-hour intravenous infusion. 3. Compatibility with Y-site co-infusion of standard 0.9% Sodium Chloride or Lactated Ringer's solution.** | `imap_28.eml` | `Email Body, Paragraph 4` | `LEVEL_1_EXACT_VISUAL` | “Could Medical Affairs please provide documentation or monograph data addressing: 1. Chemical stab...” |

### 5. Reviewer Flags / Warnings
- ✓ **Clean Processing State:** Structural and evidence-integrity checks passed. No conflicting evidence, handwriting ambiguities, or unstated critical parameters detected.
- **Validation Gating Status:** `READY_FOR_REVIEW`

### 6. Human Review State
- **Current Intake Status:** `TRIAGED`
- **Review Urgency Priority:** `STANDARD`
- **Confidence Score:** `100%`
- **Available Reviewer Primary Actions:** `[✓ Confirm AI Case]`, `[✎ Override / Edit]`, `[🚩 Flag for Escalation]`

### 7. Source Reference Section
- **Original Email File:** `test-data/emails/email_11.eml`

**Source Email Excerpt:**
```text
Dear Medical Information Team,
I am writing on behalf of our inpatient pharmacy clinical operations team at Massachusetts General Hospital with a stability inquiry regarding Cefatox (cefatoxime sodium) 1g for Injection.
We are standardizing our hospital-wide intravenous infusion protocol for adult surgical prophylaxis in patients with normal renal function. The prescribed dose is 1g IV every 8 hours. Our cleanroom compounding protocol calls for reconstituting each 1g vial with 10 mL Sterile Water for Injection, followed by immediate dilution into a 100 mL Dextrose 5% in Water (D5W) IV infusion bag.
Could Medical Affairs please provide documentation or monograph data addressing:
1. Chemical stability and potency retention (>95%) of Cefatox 1g in 100 mL D5W at refrigerated temperatures (2 deg C to 8 deg C) for up to 48 hours.
2. In-use room temperature (20 deg C to 25 deg C) stability during a prolonged 4-hour intravenous infusion.
...
```

---

## CASE-12

### 1. Case Identification
- **Case ID:** `CASE-012`
- **Email Subject:** URGENT: Adverse Drug Reaction Report - Acute Angioedema s/p Cardioril (Pt M.T.)
- **Sender:** Dr. Marcus Vance, MD (clinevo.test.inbox12@gmail.com)
- **Date:** Sun Dec 10 23:45:00 IST 2023
- **Attachment Filenames:** urgent_care_clinic_note.pdf
- **Primary Category:** `Safety Report (ICSR)`
- **All Categories / Labels:** ['Safety Report (ICSR)']
- **Multi-Label Status:** `No`
- **AI Confidence:** `100%`
- **Clinical Urgency / Clock:** `EXPEDITED`

### 2. Reviewer-Facing Summary
> This urgent medical communication from Dr. Marcus Vance details a serious adverse drug reaction experienced by a 47-year-old male patient, M.T., who developed acute angioedema of the perioral area and tongue, diffuse maculopapular rash, and dyspnea. These life-threatening symptoms manifested approximately 90 minutes following the administration of his eighth morning dose of Cardioril (cardioril hydrochloride) 20 mg. The patient presented to the Metro Urgent Care Center in acute distress and required immediate emergency stabilization. Treatment interventions administered at the bedside included intravenous methylprednisolone, intravenous diphenhydramine, nebulized albuterol, and intravenous fluid resuscitation. Due to the severity and anaphylactoid nature of the presentation, Cardioril was permanently discontinued. Following initial stabilization, the patient was transferred to the hospital Observation Unit for continuous airway monitoring and clinical observation. An attached scanned handwritten clinical encounter note further documents the acute bedside evaluation. The communication contains all four core elements required for regulatory intake: an identifiable patient, an identifiable reporter, a suspect medicinal product, and a serious adverse medical outcome. Consequently, this case must be processed immediately as an expedited Individual Case Safety Report (ICSR) in compliance with global pharmacovigilance reporting standards. Regulatory triage teams should log this event into the safety database, verify product batch details if available, and ensure timely submission to health authorities within expedited timeframes.

### 3. Structured Review Content
#### Section: Patient Demographics & Medical History (Scope: `ICSR` | Type: `GRID`)
| Parameter | Rendered Value | Status |
|:---|:---|:---|
| Patient Identifier | M.T. | `CONFIRMED` |
| Date of Birth | 11/04/1978 | `CONFIRMED` |
| Patient Age | 47 | `CONFIRMED` |
| Sex / Gender | M | `CONFIRMED` |
| Patient Weight | 82 kg | `CONFIRMED` |
| Country | United States | `CONFIRMED` |
| Medical History | Mild hypertension (x 2 yrs), seasonal allergic rhinitis. No prior adverse drug reactions. | `CONFIRMED` |

#### Section: Healthcare Professional & Primary Reporter (Scope: `ICSR` | Type: `GRID`)
| Parameter | Rendered Value | Status |
|:---|:---|:---|
| Reporter Name | Dr. Marcus Vance, MD | `CONFIRMED` |
| Qualification / Role | Physician | `CONFIRMED` |
| Medical Specialty | Urgent Care Physician | `CONFIRMED` |
| Health Professional | Yes (HCP Confirmed) | `CONFIRMED` |
| Institution / Clinic | Metro Urgent Care Center | `CONFIRMED` |
| Country | United States | `CONFIRMED` |
| Contact Information | NPI: 4491823055 | Email: m.vance@metrourgentcare.org | `CONFIRMED` |

#### Section: Suspect Product & Administration Regimen (Scope: `ICSR` | Type: `GRID`)
| Parameter | Rendered Value | Status |
|:---|:---|:---|
| Suspect Product | Cardioril (cardioril hydrochloride) | `CONFIRMED` |
| Administered Dose | 20 mg | `CONFIRMED` |
| Dosing Frequency | Once daily | `CONFIRMED` |
| Route of Administration | PO | `CONFIRMED` |
| Therapeutic Indication | Essential hypertension | `CONFIRMED` |
| Therapy Start Date | 02-DEC-2023 | `CONFIRMED` |
| Therapy Stop Date | 10-DEC-2023 | `CONFIRMED` |
| Treatment Duration | 8 days | `CONFIRMED` |
| Lot / Batch Number | Not stated | `NOT_STATED` |
| Expiration Date | Not stated | `NOT_STATED` |
| Action Taken with Drug | Drug permanently withdrawn | `CONFIRMED` |

#### Section: Adverse Event & Seriousness Profile (Scope: `ICSR` | Type: `GRID`)
| Parameter | Rendered Value | Status |
|:---|:---|:---|
| Adverse Reaction | Acute angioedema (perioral and tongue) with rash and dyspnea | `CONFIRMED` |
| Reaction Onset Date | 10-DEC-2023 | `CONFIRMED` |
| Clinical Outcome | Recovering / Resolving (Transferred to Observation Unit) | `CONFIRMED` |
| Dechallenge Outcome | Positive (resolved/improved upon discontinuation) | `CONFIRMED` |
| Rechallenge Outcome | Not applicable | `CONFIRMED` |
| Seriousness Criteria | Hospitalization, Life-threatening, Medically Significant | `CONFIRMED` |
| Inpatient Hospitalization | Yes (Hospitalized) | `CONFIRMED` |
| Hospital Admission Date | 10-DEC-2023 | `CONFIRMED` |
| Life Threatening | Yes (Life Threatening) | `CONFIRMED` |
| Medically Important | Yes (Medically Important) | `CONFIRMED` |

#### Section: Laboratory & Diagnostic Investigations Matrix (Scope: `ICSR` | Type: `TABLE`)
| Test / Parameter | Date | Result | Unit | Normal Range | Interpretation |
|:---|:---|:---|:---|:---|:---|
| Peak Flow | 10-DEC-2023 | 320 | L/min | baseline ~500 | Decreased / Impaired airflow |

#### Section: Clinical Chronological Narrative (Scope: `ICSR` | Type: `NARRATIVE`)
**Narrative Text:**

On 10-DEC-2023 at 11:40 am, a 47-year-old male patient (M.T.) was evaluated by Dr. Marcus Vance at Metro Urgent Care Center for facial swelling and rash. The patient had been taking Cardioril (cardioril hydrochloride) 20 mg PO once daily since 02-DEC-2023 for essential hypertension. Approximately 90 minutes after taking his 8th morning dose (~9:00 am), he developed perioral and tongue swelling, difficulty swallowing, rash, and shortness of breath. On arrival, exam revealed an alert but anxious patient speaking in short phrases, marked perioral and tongue swelling, diffuse erythematous maculopapular rash, and wheezing on auscultation. Vital signs: BP 96/62 mmHg, HR 106 bpm, RR 22/min, SpO2 93% on room air, Temp 36.8°C, and Peak Flow 320 L/min (baseline ~500). He received emergency bedside management comprising IV methylprednisolone 125 mg, IV diphenhydramine 50 mg, nebulized albuterol 2.5 mg, and IV Normal Saline 1000 mL bolus. Cardioril was permanently discontinued. The patient stabilized after treatment with improvement in swelling and rash within ~4 hours, and was transferred to the hospital Observation Unit for continued airway monitoring.

#### Section: Regulatory & Manufacturer Processing Metadata (Scope: `ICSR` | Type: `GRID`)
| Parameter | Rendered Value | Status |
|:---|:---|:---|
| Report Classification | Initial | `CONFIRMED` |

### 4. Evidence Shown to Reviewer
| Displayed Fact | Source Document | Page / Location | Anchor Level | Displayed Evidence Snippet |
|:---|:---|:---|:---|:---|
| Patient Identifier: **M.T.** | `imap_29.eml` | `Email Body, Paragraph 2` | `LEVEL_1_EXACT_VISUAL` | “I am urgently submitting an initial adverse drug reaction report concerning a 47-year-old male pa...” |
| Date of Birth: **11/04/1978** | `imap_29.eml` | `Email Body, Paragraph 2` | `LEVEL_1_EXACT_VISUAL` | “I am urgently submitting an initial adverse drug reaction report concerning a 47-year-old male pa...” |
| Patient Age: **47** | `imap_29.eml` | `Email Body, Paragraph 2` | `LEVEL_1_EXACT_VISUAL` | “I am urgently submitting an initial adverse drug reaction report concerning a 47-year-old male pa...” |
| Sex / Gender: **M** | `imap_29.eml` | `Email Body, Paragraph 2` | `LEVEL_1_EXACT_VISUAL` | “I am urgently submitting an initial adverse drug reaction report concerning a 47-year-old male pa...” |
| Patient Weight: **82 kg** | `imap_29.eml` | `Page 1 / Email Body` | `LEVEL_3_SNIPPET_ONLY` | “Patient: M. T. DOB: 11/04/1978 (age 47) Sex: M Wt: 82 kg Ht: 178 cm 47y/o M with hx of mild hyper...” |
| Patient Country: **United States** | `imap_29.eml` | `Page 1 / Email Body` | `LEVEL_3_SNIPPET_ONLY` | “Patient: M. T. DOB: 11/04/1978 (age 47) Sex: M Wt: 82 kg Ht: 178 cm 47y/o M with hx of mild hyper...” |
| Medical History: **Mild hypertension (x 2 yrs), seasonal allergic rhinitis. No prior adverse drug reactions.** | `imap_29.eml` | `Email Body, Paragraph 2` | `LEVEL_1_EXACT_VISUAL` | “I am urgently submitting an initial adverse drug reaction report concerning a 47-year-old male pa...” |
| Reporter Name: **Dr. Marcus Vance, MD** | `imap_29.eml` | `Email Header` | `LEVEL_1_EXACT_VISUAL` | “From: Dr. Marcus Vance, MD <clinevo.test.inbox12@gmail.com> Date: Sun, 10 Dec 2023 12:15:00 -0600...” |
| Reporter Qualification: **Physician** | `imap_29.eml` | `Email Body, Paragraph 5` | `LEVEL_1_EXACT_VISUAL` | “Sincerely, Dr. Marcus Vance, MD Urgent Care Physician, Metro Urgent Care Center, Chicago, IL N...” |
| Medical Specialty: **Urgent Care Physician** | `imap_29.eml` | `Email Body, Paragraph 5` | `LEVEL_1_EXACT_VISUAL` | “Sincerely, Dr. Marcus Vance, MD Urgent Care Physician, Metro Urgent Care Center, Chicago, IL N...” |
| Health Professional: **Yes (HCP Confirmed)** | `imap_29.eml` | `Page 1 / Email Body` | `LEVEL_3_SNIPPET_ONLY` | “Attending: Dr. Marcus Vance, MD Urgent Care Physician Metro Urgent Care Center Chicago, IL NPI: 4...” |
| Institution / Clinic: **Metro Urgent Care Center** | `imap_29.eml` | `Email Body, Paragraph 2` | `LEVEL_1_EXACT_VISUAL` | “I am urgently submitting an initial adverse drug reaction report concerning a 47-year-old male pa...” |
| Country: **United States** | `imap_29.eml` | `Page 1 / Email Body` | `LEVEL_3_SNIPPET_ONLY` | “Attending: Dr. Marcus Vance, MD Urgent Care Physician Metro Urgent Care Center Chicago, IL NPI: 4...” |
| Contact Information: **NPI: 4491823055 | Email: m.vance@metrourgentcare.org** | `imap_29.eml` | `Email Body, Paragraph 5` | `LEVEL_1_EXACT_VISUAL` | “Sincerely, Dr. Marcus Vance, MD Urgent Care Physician, Metro Urgent Care Center, Chicago, IL N...” |
| Suspect Product: **Cardioril (cardioril hydrochloride)** | `imap_29.eml` | `Email Body, Paragraph 2` | `LEVEL_1_EXACT_VISUAL` | “I am urgently submitting an initial adverse drug reaction report concerning a 47-year-old male pa...” |
| Administered Dose: **20 mg** | `imap_29.eml` | `Email Body, Paragraph 2` | `LEVEL_1_EXACT_VISUAL` | “I am urgently submitting an initial adverse drug reaction report concerning a 47-year-old male pa...” |
| Dosing Frequency: **Once daily** | `imap_29.eml` | `Page 1 / Email Body` | `LEVEL_3_SNIPPET_ONLY` | “Started Cardioril (cardioril hydrochloride) 20 mg PO once daily on 02-DEC-2023 for essential hype...” |
| Route of Administration: **PO** | `imap_29.eml` | `Email Body, Paragraph 2` | `LEVEL_1_EXACT_VISUAL` | “I am urgently submitting an initial adverse drug reaction report concerning a 47-year-old male pa...” |
| Therapy Start Date: **02-DEC-2023** | `imap_29.eml` | `Page 1 / Email Body` | `LEVEL_3_SNIPPET_ONLY` | “Started Cardioril (cardioril hydrochloride) 20 mg PO once daily on 02-DEC-2023 for essential hype...” |
| Therapy Stop Date: **10-DEC-2023** | `imap_29.eml` | `Page 1 / Email Body` | `LEVEL_3_SNIPPET_ONLY` | “Started Cardioril (cardioril hydrochloride) 20 mg PO once daily on 02-DEC-2023 for essential hype...” |
| Treatment Duration: **8 days** | `imap_29.eml` | `Page 1 / Email Body` | `LEVEL_3_SNIPPET_ONLY` | “Started Cardioril (cardioril hydrochloride) 20 mg PO once daily on 02-DEC-2023 for essential hype...” |
| Action Taken with Drug: **Drug permanently withdrawn** | `imap_29.eml` | `Email Header` | `LEVEL_1_EXACT_VISUAL` | “From: Dr. Marcus Vance, MD <clinevo.test.inbox12@gmail.com> Date: Sun, 10 Dec 2023 12:15:00 -0600...” |
| Adverse Reaction: **Acute angioedema (perioral and tongue) with rash and dyspnea** | `imap_29.eml` | `Email Body, Paragraph 2` | `LEVEL_1_EXACT_VISUAL` | “I am urgently submitting an initial adverse drug reaction report concerning a 47-year-old male pa...” |
| Seriousness Criteria: **Hospitalization, Life-threatening, Medically Significant** | `imap_29.eml` | `Page 1 / Email Body` | `LEVEL_3_SNIPPET_ONLY` | “About 90 minutes later, developed swelling of tongue and lips, difficulty swallowing, rash, and s...” |
| Inpatient Hospitalization: **Yes (Hospitalized)** | `imap_29.eml` | `Page 1 / Email Body` | `LEVEL_3_SNIPPET_ONLY` | “About 90 minutes later, developed swelling of tongue and lips, difficulty swallowing, rash, and s...” |
| Hospital Admission Date: **10-DEC-2023** | `imap_29.eml` | `Page 1 / Email Body` | `LEVEL_3_SNIPPET_ONLY` | “About 90 minutes later, developed swelling of tongue and lips, difficulty swallowing, rash, and s...” |
| Life Threatening: **Yes (Life Threatening)** | `imap_29.eml` | `Page 1 / Email Body` | `LEVEL_3_SNIPPET_ONLY` | “About 90 minutes later, developed swelling of tongue and lips, difficulty swallowing, rash, and s...” |
| Medically Important: **Yes (Medically Important)** | `imap_29.eml` | `Page 1 / Email Body` | `LEVEL_3_SNIPPET_ONLY` | “About 90 minutes later, developed swelling of tongue and lips, difficulty swallowing, rash, and s...” |
| Dechallenge Outcome: **Positive (resolved/improved upon discontinuation)** | `imap_29.eml` | `Page 1 / Email Body` | `LEVEL_3_SNIPPET_ONLY` | “About 90 minutes later, developed swelling of tongue and lips, difficulty swallowing, rash, and s...” |
| Rechallenge Outcome: **Not applicable** | `imap_29.eml` | `Page 1 / Email Body` | `LEVEL_3_SNIPPET_ONLY` | “About 90 minutes later, developed swelling of tongue and lips, difficulty swallowing, rash, and s...” |

### 5. Reviewer Flags / Warnings
- ✓ **Clean Processing State:** Structural and evidence-integrity checks passed. No conflicting evidence, handwriting ambiguities, or unstated critical parameters detected.
- **Validation Gating Status:** `READY_FOR_REVIEW`

### 6. Human Review State
- **Current Intake Status:** `TRIAGED`
- **Review Urgency Priority:** `EXPEDITED`
- **Confidence Score:** `100%`
- **Available Reviewer Primary Actions:** `[✓ Confirm AI Case]`, `[✎ Override / Edit]`, `[🚩 Flag for Escalation]`

### 7. Source Reference Section
- **Original Email File:** `test-data/emails/email_12.eml`
- **Original PDF Attachment(s):** `test-data/pdfs/.../urgent_care_clinic_note.pdf`
- **Original Image Asset(s):** `test-data/pdfs/.../urgent_care_clinic_photo.jpg`

**Source Email Excerpt:**
```text
Dear Pharmacovigilance Department,
I am urgently submitting an initial adverse drug reaction report concerning a 47-year-old male patient (M.T., DOB: 11/04/1978) who presented to Metro Urgent Care Center in acute distress with perioral and tongue angioedema, diffuse maculopapular rash, and dyspnea approximately 90 minutes after taking his 8th morning dose of Cardioril (cardioril hydrochloride) 20 mg.
The patient received emergency bedside stabilization including IV methylprednisolone, IV diphenhydramine, nebulized albuterol, and IV fluids. Cardioril has been permanently discontinued, and the patient has been transferred to the hospital Observation Unit for airway monitoring.
Attached is the bedside clinical encounter note completed during evaluation.
Sincerely,
Dr. Marcus Vance, MD
...
```

---

# REVIEW SCOPE

- 12 cases included
- frontend reviewer-facing content captured
- source emails/attachments referenced
- no code/data changes made
