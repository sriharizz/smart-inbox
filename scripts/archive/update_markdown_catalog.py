import os

MD_PATH = r"c:\projects\SmartInbox\test-data\TEST_CASES_AND_EMAILS.md"

content = """# CLINEVO SMART INBOX — CLINICAL TEST CASES & EMAIL CATALOG
> **Purpose**: Complete reference catalog of all 11 synthetic intake emails and their associated regulatory documents (20 physical PDFs, 2 image assets, benchmark.json, manifest.json).  
> **Review Ready**: Can be shared directly with ChatGPT, Claude, or clinical domain experts for evaluation.

---

## Summary Matrix of the 11 Test Intake Cases

| Case | Category Bucket | Document Flavor & Attachment | Clinical Scenario | Key Test Objectives |
| :---: | :--- | :--- | :--- | :--- |
| **01** | **Safety Report (ICSR)** | **Flavor 1: Digital PDF** (`cioms_form_MK_Cardioril.pdf`) | Hospital physician reporting severe Drug-Induced Liver Injury (DILI) in a 58F patient. | Official monochrome CIOMS Form I layout; structured lab chemistry table (ALT, AST, Bilirubin); Hy's Law; serious = hospitalization. |
| **02** | **Safety Report (ICSR)** | **Flavor 2: Scanned/Handwritten** (`urgent_care_intake_handwritten.pdf`) | Emergency doctor reporting acute anaphylaxis following InjectaPen auto-injector dose. | Real photograph of a handwritten emergency triage sheet; pen strokes; vital signs table (hypotension/shock); zero-hallucination policy (dose = `"Not stated"`). |
| **03** | **Safety Report (ICSR)** | **No Attachment (Pure Email Text)** | Consumer reporting sudden severe tachycardia (154 bpm) and palpitations after starting Corzapan 10mg. | Tests extraction directly from informal consumer email text without PDF; tests zero-hallucination policy (missing lot/weight = `"Not stated"`). |
| **04** | **Multi-Bucket: Safety + Quality (ICSR + PQC)** | **Flavor 1: Digital PDF + Photo** (`vial_contamination_sepsis.pdf`) | ICU Director reporting contaminated Cefatox 1g vial with particulate that caused septic shock in a 71M patient. | Multi-label classification (both ICSR and PQC); official 2-page FDA Form 3500A; Exhibit 1 cleanroom defect photo; flagging meaningful images for human review. |
| **05** | **Safety Report (ICSR)** | **Flavor 4: Non-English (Spanish)** (`notificacion_ram_madrid.pdf`) | Madrid hospital physician reporting Toxic Epidermal Necrolysis (TEN) caused by Lamotrigine in a 29F patient. | Language detection (`es`); English translation of medical terms; preserving links back to original Spanish text; official Spanish AEMPS RAM form. |
| **06** | **Safety Report (ICSR Follow-up)** | **Flavor 1: Digital PDF** (`fda_medwatch_followup.pdf`) | Neurologist follow-up report confirming seizure episode resolved after anti-epileptic discontinuation. | Follow-up report linking; official FDA Form 3500A grid; positive de-challenge outcome documentation. |
| **07** | **Quality Complaint Only (PQC)** | **Flavor 1: Digital PDF** (`packaging_defect_report.pdf`) | Central pharmacy manager reporting Lot #BL-8802 blister packs have breached foil seals with oxidized crumbling tablets. | Pure PQC (no patient exposed, zero adverse reactions); extracting Lot #, defect description, photo reference. |
| **08** | **Quality Complaint Only (PQC)** | **No Attachment (Pure Email Text)** | Retail pharmacist reporting suspected counterfeit packaging (misaligned typography and missing tamper-evident seal). | Extracting product quality complaint details from pure email body text with zero attachments. |
| **09** | **Medical Information (MI)** | **No Attachment (Pure Email Text)** | Clinical oncology pharmacist inquiring whether oral tablets can be crushed for feeding tube administration in an elderly patient. | Pure MI inquiry #1 (hypothetical product inquiry; zero adverse reactions; zero defects); prevents false-positive ICSR tagging. |
| **10** | **Not Relevant (Marketing / Spam)** | **No Attachment (Pure Email Text)** | Commercial promotional newsletter invitation for the "Global Pharma Compliance & AI Innovation Summit 2026". | Pure spam/marketing; model must classify as `Not Relevant` with high confidence ($>0.95$) and extract zero clinical entities. |
| **11** | **Medical Information (MI)** | **No Attachment (Pure Email Text)** | Hospital compounding specialist inquiring regarding Cefatox 1g stability and compatibility in D5W IV infusion bags. | Pure MI inquiry #2 (reconstitution, refrigerated stability, room temp infusion kinetics; zero adverse reactions; zero defects). |

---

## Detailed Clinical Specifications per Case

### Case 01: Acute Drug-Induced Liver Injury (ICSR)
- **Category**: `Safety Report (ICSR)` (Confidence: ~0.98)
- **Attached Document**: `cioms_form_MK_Cardioril.pdf` (Official CIOMS Form I, Digital PDF)
- **Email File**: `test-data/emails/email_01.eml`

```email
From: "Dr. Sarah Jenkins, MD" <sjenkins@metrohealth-chicago.org>
To: "Clinevo Safety Mailbox" <drugsafety@clinevotech.com>
Date: Wed, 12 Nov 2025 14:22:10 -0600
Subject: URGENT: Individual Case Safety Report (ICSR) - Suspect DILI with Cardioril (Pt M.K.)
Message-ID: <20251112.142210.sjenkins@metrohealth-chicago.org>
X-Priority: 1

Dear Pharmacovigilance Team,

I am submitting an urgent spontaneous adverse drug reaction report concerning a 58-year-old female 
patient (M.K.) under my care who developed acute drug-induced liver injury (DILI) and jaundice 
following treatment with Cardioril 20 mg once daily.

The patient required acute hospital admission on November 10, 2025 due to significantly elevated 
transaminases (>9x ULN) and hyperbilirubinemia (Total Bili: 4.8 mg/dL) meeting Hy's law criteria. 
Viral hepatitis serologies and abdominal ultrasound were negative for biliary obstruction.

Cardioril was promptly discontinued on admission, and liver transaminases are beginning to trend down. 
Please find attached the completed official CIOMS-I reporting form along with the structured hepatic chemistry 
laboratory panel for your expedited safety evaluation.

Please acknowledge receipt of this regulatory submission.

Sincerely,
Sarah Jenkins, MD, FACP
Department of Gastroenterology, MetroHealth Medical Center
2500 MetroHealth Dr, Chicago, IL 60609
Tel: (312) 555-0188 | Email: sjenkins@metrohealth-chicago.org
```

**Expected AI Extraction**:
- Patient: Age `58`, Sex `Female`, History: `Essential Hypertension, T2DM`.
- Suspect Drug: `Cardioril 20mg once daily`, Lot `#CR-2025-0981`, Oral.
- Adverse Reaction: `Acute Drug-Induced Liver Injury / Jaundice`, Onset: `08-NOV-2025`.
- Laboratory Matrix: ALT `540 U/L`, AST `420 U/L`, Total Bilirubin `4.8 mg/dL`, ALP `210 U/L`.
- Seriousness: `Hospitalization: YES`, `Life-Threatening: NO`, `Death: NO`.
- Sourcing: Citations linked to `cioms_form_MK_Cardioril.pdf, Page 1, Box 1, Box 7, Box 13, Box 24`.

---

### Case 02: Acute Anaphylaxis (Scanned Handwritten Intake)
- **Category**: `Safety Report (ICSR)` (Confidence: ~0.82 due to handwritten text)
- **Attached Document**: `urgent_care_intake_handwritten.pdf` (Real photograph of emergency clinical record)
- **Email File**: `test-data/emails/email_02.eml`

```email
From: "Dr. A. Peterson, MD" <a.peterson@stmarys-hospital.org>
To: "Clinevo Drug Safety Mailbox" <drugsafety@clinevotech.com>
Date: Sun, 10 Dec 2023 15:30:00 -0500
Subject: URGENT: Adverse Drug Event Report - Acute Anaphylaxis s/p InjectaPen (Pt Jane Doe)
Message-ID: <20231210.153000.apeterson@stmarys-hospital.org>
X-Priority: 1

Dear Pharmacovigilance Department,

I am urgently submitting an initial adverse event report for a 33-year-old female patient (Jane Doe, DOB: 05/18/1990) 
who presented to St. Mary's Emergency Department in severe acute anaphylactic shock 20 minutes following self-injection of InjectaPen.

Patient presented with generalized urticaria, marked lip and perioral angioedema, inspiratory stridor, and profound hypotension (BP 85/50, HR 128). 
Immediate emergency intervention was initiated: Epinephrine 0.3 mg IM, high-flow oxygen, IV fluid resuscitation, and admission to the emergency unit.

Attached is the photograph of our emergency intake and triage record completed at bedside.

Sincerely,
Dr. A. Peterson, MD
Emergency Department, St. Mary's General Hospital
NPI: 9876543210 | Email: a.peterson@stmarys-hospital.org
```

**Expected AI Extraction (Zero-Hallucination Verified)**:
- Patient: Name `Jane Doe`, DOB `05/18/1990`, Age `33`, Sex `Female`, Weight: `"Not stated"`.
- Suspect Drug: Name `InjectaPen`, Dose: `"Not stated"`, Lot: `"Not stated"`. *(Crucial test: Suspect product dose is not on the triage sheet and must NOT be hallucinated as 50mg).*
- Emergency Treatment: `Epinephrine 0.3 mg IM, high-flow oxygen, IV fluid resuscitation` *(Separately documented from suspect product).*
- Adverse Reaction: `Acute Anaphylaxis (Grade 3)`, `Generalized Urticaria / Hives`, `Facial & Perioral Angioedema`, `Inspiratory Stridor`.
- Triage Vitals: BP `85/50`, HR `128 bpm`, SpO2 `91%`.
- Seriousness: `Life-Threatening: YES`, `Hospitalization: YES`, `Death: NO`.
- Sourcing: Citations linked to `urgent_care_intake_handwritten.pdf, Page 1`.

---

### Case 03: Consumer Palpitations & Tachycardia (Pure Email ICSR)
- **Category**: `Safety Report (ICSR)` (Confidence: ~0.90)
- **Attached Document**: None (Pure Email Text)
- **Email File**: `test-data/emails/email_03.eml`

```email
From: "Emily Watson" <emily.watson82@gmail.com>
To: "Clinevo Patient Safety" <drugsafety@clinevotech.com>
Date: Mon, 17 Nov 2025 09:14:22 -0500
Subject: Adverse Reaction to Corzapan 10mg - Severe Heart Racing
Message-ID: <CABe-watson-20251117@mail.gmail.com>

Hello,

I am writing to report a very scary reaction I had after taking Corzapan 10mg tablets. 
My doctor prescribed it for mild hypertension. I took my first tablet this morning at 7:30 AM.

Around 8:15 AM, my heart started pounding uncontrollably. My Apple Watch recorded my heart rate 
jumping from 72 bpm to 154 bpm while I was just sitting at my desk. I felt severe palpitations, 
lightheadedness, and felt like I was going to pass out. 

I called my cardiologist's emergency line, and they instructed me not to take any more doses and to rest. 
The racing lasted about 3 hours before gradually slowing down.

I am a 42-year-old female with no prior history of heart rhythm disorders. 
I have the box with me if you need the lot number. Please let me know if this is an expected side effect.

Emily Watson
Atlanta, GA | Phone: (404) 555-0149
```

**Expected AI Extraction**:
- Patient: Name `Emily Watson`, Age `42`, Sex `Female`, Weight: `"Not stated"`.
- Suspect Drug: `Corzapan 10mg tablets`, Dose: `10mg once daily`, Lot: `"Not stated"`.
- Adverse Reaction: `Tachycardia (154 bpm)`, `Palpitations`, `Lightheadedness`, `Near-syncope`.
- Seriousness: `Hospitalization: NO`, `Life-Threatening: NO`, `Death: NO`.
- Sourcing: `emails/email_03.eml:Body`.

---

### Case 04: Contaminated Vial Causing Septic Shock (Multi-Bucket: ICSR + PQC)
- **Category**: `Safety Report (ICSR)` AND `Quality Complaint (PQC)` (Multi-Label, Confidence: ~0.92)
- **Attached Document**: `vial_contamination_sepsis.pdf` (Official 2-Page FDA Form 3500A + Cleanroom Defect Photo Exhibit)
- **Email File**: `test-data/emails/email_04.eml`

```email
From: "Dr. Robert Sterling, MD" <rsterling@nm-icu.org>
To: "Clinevo Drug Safety & Quality" <quality-safety@clinevotech.com>
Date: Tue, 18 Nov 2025 11:05:00 -0600
Subject: CRITICAL: Defective Product & Life-Threatening Sepsis - Cefatox 1g (Lot CX54831)
Message-ID: <20251118.110500.rsterling@nm-icu.org>
X-Priority: 1

URGENT PHARMACOVIGILANCE & QUALITY COMPLAINT

I am reporting a catastrophic product defect and associated life-threatening adverse event in an ICU patient.

Patient: Arthur Pendelton (71yo male, MRN #ICU-99201)
Suspect Product: Cefatox (cefatoxime sodium) 1g for Injection
Lot Number: CX54831 | Expiration: 08/2025

On Nov 17 at 18:00, during routine reconstitution, nursing staff observed that the aluminum crimp seal 
was cracked and the rubber stopper compromised. Upon reconstitution with sterile water, visible black 
foreign particulate was observed floating in the solution. 

Tragically, a prior vial from the same hospital batch had been administered to Mr. Pendelton 6 hours earlier. 
At 22:30, the patient developed acute distributive septic shock, profound hypotension (BP 72/40), 
fever of 39.8 C, and blood cultures grew Bacillus cereus. The patient is currently intubated in our ICU 
on dual vasopressor support.

Attached is FDA Form 3500A and Exhibit 1 high-resolution cleanroom photography of the defective vial.

Dr. Robert Sterling, MD
Director, Medical Intensive Care Unit, Northwestern Memorial Hospital, Chicago, IL
```

**Expected AI Extraction**:
- Multi-label: Categories `["Safety Report (ICSR)", "Quality Complaint (PQC)"]`.
- Quality Complaint: Product `Cefatox 1g for Inj.`, Lot `CX54831`, Expiry `08/2025`, Defect: `Cracked crimp seal, compromised stopper, visible particulate`.
- Meaningful Image Flag: `photo_present: true`, `photo_requires_human_review: true`.
- Patient: `Arthur Pendelton (A.P.)`, Age `71`, Sex `Male`, Weight `74 kg`.
- Adverse Reaction: `Severe Acute Bacteremia / Distributive Septic Shock`, Serious: `Life-Threatening: YES`, `Hospitalization: YES`.
- Sourcing: Citations linked to `vial_contamination_sepsis.pdf:Page1:SectionB (ICSR)`, `SectionC (PQC)`, `Page2:Exhibit1 (Photo)`.

---

### Case 05: Spanish Toxic Epidermal Necrolysis (Non-English ICSR)
- **Category**: `Safety Report (ICSR)` (Confidence: ~0.92)
- **Language**: Spanish (`es`) -> Auto-translated to English with original language preserved
- **Attached Document**: `notificacion_ram_madrid.pdf` (Official Spanish AEMPS Yellow Card / RAM Form)
- **Email File**: `test-data/emails/email_05.eml`

```email
From: "Dra. Elena Gomez Prado" <egomez@hulp-salud.madrid.org>
To: "Farmacovigilancia Clinevo" <farmacovigilancia@clinevotech.com>
Date: Mon, 10 Nov 2025 16:45:12 +0100
Subject: URGENTE: Notificacion de Reaccion Adversa Grave - Lamotrigina NET (C.O.)
Message-ID: <20251110.164512.egomez@hulp-salud.madrid.org>
X-Priority: 1

Estimado Departamento de Farmacovigilancia,

Adjunto remito formulario oficial de notificacion de reaccion adversa a medicamentos (Tarjeta Amarilla AEMPS) 
correspondiente a una reaccion adversa muy grave y con amenaza vital observada en nuestro hospital.

Paciente: C.O., mujer de 29 anos.
Medicamento sospechoso: Lamotrigina (Lamictal) 100 mg/dia oral, Lote LM-9941.
Diagnostico clinico: Necrolisis Epidermica Toxica (NET / Sindrome de Lyell) con desprendimiento epidermico 
superior al 35% de la superficie corporal, afectacion mucosa oral, ocular y genital grave.

La paciente ha sido ingresada en la Unidad de Grandes Quemados de nuestro centro.

Atentamente,
Dra. Elena Gomez Prado
Servicio de Dermatologia, Hospital Universitario La Paz, Madrid, Espana
```

**Expected AI Extraction**:
- Detected Language: `es` (Spanish).
- Category: `Safety Report (ICSR)`.
- Patient: `Carmen Ortiz (C.O.)`, Age `29 AÑOS`, Sex `MUJER`, Weight `54 kg`.
- Suspect Drug: `Lamotrigina 100 mg/día`, Lot `LM-9941`.
- Translated Adverse Reaction: `Toxic Epidermal Necrolysis (TEN / Lyell Syndrome) with epidermal detachment >35% BSA`.
- Seriousness: `Life-Threatening: YES`, `Hospitalization: YES`.
- Sourcing: `notificacion_ram_madrid.pdf:Page1`.

---

### Case 06: Follow-up De-challenge Report (FDA Form 3500A ICSR)
- **Category**: `Safety Report (ICSR)` (Follow-up, Confidence: ~0.95)
- **Attached Document**: `fda_medwatch_followup.pdf` (Official FDA Form 3500A Follow-up)
- **Email File**: `test-data/emails/email_06.eml`

```email
From: "Dr. Richard Vance, MD" <rvance@cumc.columbia.edu>
To: "Clinevo Global Drug Safety" <drugsafety@clinevotech.com>
Date: Fri, 14 Nov 2025 10:15:00 -0500
Subject: FOLLOW-UP REPORT #1: Seizure Resolution s/p Neuroval Discontinuation (Pt D.M.)
Message-ID: <20251114.101500.rvance@cumc.columbia.edu>

Dear Pharmacovigilance Team,

Please find attached Follow-up Report #1 (FDA Form 3500A) for patient David Miller (D.M., 52M), 
who previously suffered generalized seizures following dose escalation of Neuroval (Lot NV-2025-110).

I am pleased to report that following complete discontinuation of Neuroval on Nov 3, 2025, the patient 
has remained completely seizure-free for 11 consecutive days. Post-ictal confusion fully cleared within 
24 hours. Follow-up 72-hour continuous video-EEG demonstrated normalization of background cerebral rhythms 
without epileptiform discharges. This confirms a positive de-challenge outcome.

Sincerely,
Dr. Richard Vance, MD
Department of Neurology, Columbia University Medical Center, New York, NY
```

**Expected AI Extraction**:
- Category: `Safety Report (ICSR)`.
- Report Type: `Follow-up Report`.
- Patient: `David Miller (D.M.)`, Age `52 YRS`, Sex `MALE`, Weight `79 kg`.
- Suspect Drug: `Neuroval 400mg PO QD`, Lot `NV-2025-110`, Action: `Permanently Discontinued`.
- Clinical Outcome: `Seizures resolved, EEG normalized; Positive de-challenge confirmed`.
- Sourcing: `fda_medwatch_followup.pdf:Page1`.

---

### Case 07: Blister Foil Breach Defect (Quality Complaint Only)
- **Category**: `Quality Complaint (PQC)` ONLY (Confidence: ~0.95)
- **Attached Document**: `packaging_defect_report.pdf` (Digital Defect Log)
- **Email File**: `test-data/emails/email_07.eml`

```email
From: "Patricia Morales, RPh" <pmorales@ahn-pharmacy.org>
To: "Product Quality Complaints" <quality@clinevotech.com>
Date: Mon, 17 Nov 2025 14:00:00 -0500
Subject: Product Quality Complaint: Defective Blister Packaging - Cardioril 20mg (Lot BL-8802)
Message-ID: <20251117.140000.pmorales@ahn-pharmacy.org>

Dear Quality Assurance Team,

I am logging a formal product quality complaint regarding Cardioril 20mg blister packs (10x10 tablets).

Product: Cardioril (cardioril hydrochloride) 20mg Tablets
Lot Number: BL-8802 | Expiration: 11/2027

During routine dispensing inspection, our pharmacy technicians discovered that multiple blister cavities 
have incomplete foil-to-PVC heat sealing. In 14 of 50 cartons inspected (28% defect rate), the aluminum backing 
is peeling away, allowing ambient air and moisture ingress. Several exposed tablets exhibit discoloration, 
crumbling edges, and signs of chemical oxidation.

All affected inventory from Lot BL-8802 has been immediately quarantined in our secure pharmacy vault. 
No defective tablets were dispensed to patients; there are zero adverse patient reactions.

Attached is our hospital pharmacy defect investigation form and photos.

Patricia Morales, RPh
Pharmacy Operations Manager, Allegheny General Hospital, Pittsburgh, PA
```

**Expected AI Extraction**:
- Category: `Quality Complaint (PQC)` ONLY.
- Patient / Adverse Event: `None / Not Applicable` (Explicitly verified as zero patient exposure).
- Defect: `Breached blister foil seal, moisture ingress, oxidized crumbling tablets`, Lot `BL-8802`.
- Sourcing: `packaging_defect_report.pdf:Page1`.

---

### Case 08: Suspected Counterfeit Packaging (Pure Email PQC)
- **Category**: `Quality Complaint (PQC)` ONLY (Confidence: ~0.95)
- **Attached Document**: None (Pure Email Text)
- **Email File**: `test-data/emails/email_08.eml`

```email
From: "Thomas Albright, PharmD" <talbright@greenwood-rx.com>
To: "Product Quality Complaints" <quality@clinevotech.com>
Date: Tue, 18 Nov 2025 15:30:00 -0600
Subject: Suspected Counterfeit / Packaging Defect - Corzapan 10mg (Lot CZ-9021)
Message-ID: <20251118.153000.talbright@greenwood-rx.com>

Dear Quality Control Department,

I am writing to alert your security and quality division regarding suspect counterfeit inventory 
received through secondary wholesale channels.

Product: Corzapan 10mg, 30-tablet bottles
Lot Number: CZ-9021 | Expiry: 05/2027

Upon receiving shipment #WH-4482, our staff noticed that the packaging exterior exhibits blurred typography, 
misaligned manufacturer logos, and is completely missing the holographic tamper-evident seal on the bottle neck. 
The tablets inside have an abnormal chalky texture and lack the standard debossed 'CZ10' imprint.

We have quarantined all 120 bottles. No units were sold to customers. Zero patient harm has occurred.

Thomas Albright, PharmD
Pharmacy Manager, Greenwood Apothecary, Austin, TX | Tel: (512) 555-0177
```

**Expected AI Extraction**:
- Category: `Quality Complaint (PQC)` ONLY.
- Defect: `Suspected counterfeit packaging, blurred typography, missing holographic seal, abnormal chalky texture`, Lot `CZ-9021`.
- Patient / Adverse Event: `None / Not Applicable`.
- Sourcing: `emails/email_08.eml:Body`.

---

### Case 09: Feeding Tube Crushing Inquiry (Pure Email MI #1)
- **Category**: `Medical Information (MI)` ONLY (Confidence: ~0.97)
- **Attached Document**: None (Pure Email Text)
- **Email File**: `test-data/emails/email_09.eml`

```email
From: "David Wu, BCPS" <david.wu@ucsf-clinical.edu>
To: "Clinevo Medical Information Department" <medinfo@clinevotech.com>
Date: Wed, 19 Nov 2025 13:40:00 -0800
Subject: Medical Information Request: Can Corzapan 10mg tablets be crushed for NG-tube administration?
Message-ID: <20251119.134000.dwu@ucsf-clinical.edu>

Dear Medical Information Department,

I am a clinical oncology pharmacist at UCSF Medical Center caring for an elderly patient with severe dysphagia 
who has an active nasogastric (NG) feeding tube in place.

The patient has been prescribed Corzapan 10mg once daily for chronic hypertension. The package insert indicates 
film-coated tablets but does not explicitly state whether the tablets can be crushed and suspended in sterile water 
for enteral feeding tube delivery without altering bioavailability or causing tube occlusion.

Could your medical affairs team please provide any pharmacokinetic or stability data regarding:
1. Crushing Corzapan 10mg tablets for enteral administration.
2. Potential adsorption of the active substance to polyurethane enteral feeding tubes.
3. Co-administration with enteral nutrition formulas.

There is currently no patient adverse event or product defect. This is purely a prospective clinical inquiry.

Best regards,
David Wu, PharmD, BCPS
Clinical Pharmacy Specialist, UCSF Health, San Francisco, CA | Tel: (415) 555-0198
```

**Expected AI Extraction**:
- Category: `Medical Information (MI)` ONLY.
- Product: `Corzapan 10mg tablets`.
- Question Asked: `Can tablets be crushed for nasogastric (NG) enteral feeding tube administration? Enteral stability and tube adsorption data requested`.
- Adverse Reaction / Product Defect: `None / Not Applicable`.
- Sourcing: `emails/email_09.eml:Body`.

---

### Case 10: Pharmaceutical Conference Marketing (Not Relevant / Spam)
- **Category**: `Not Relevant` ONLY (Confidence: ~0.99)
- **Attached Document**: None (Pure Email Text)
- **Email File**: `test-data/emails/email_10.eml`

```email
From: "PharmaTech Global Summit" <events@pharmasummit-global2026.com>
To: "Drug Safety Department" <drugsafety@clinevotech.com>
Date: Thu, 20 Nov 2025 08:00:00 +0000
Subject: Early Bird Registration Open: 14th Annual Global AI in Pharmacovigilance & Drug Safety Summit
Message-ID: <20251120.080000.events@pharmasummit-global2026.com>

Join 500+ global safety leaders, regulatory directors, and AI pioneers in Boston, MA on March 24–26, 2026!

Keynote sessions include:
• Generative AI & LLMs in ICSR Intake Automation
• GVP Module VI Inspection Readiness in 2026
• Automating Literature Screening with Multimodal AI
• Real-World Evidence & Signal Detection Case Studies

Register before December 15th to save $400 with our Early Bird Discount code: SAFETYAI2026.
Group discounts available for teams of 3 or more.

Click here to reserve your delegate pass: https://www.pharmasummit-global2026.com/register
To unsubscribe from future event notifications, click here.
```

**Expected AI Extraction**:
- Category: `Not Relevant` ONLY.
- AI Reason: *"Commercial marketing advertisement for an industry conference. Contains zero patient safety data, zero product quality defects, and zero clinical product questions."*
- Extracted Entities: All empty / `"Not stated"`.
- Sourcing: `emails/email_10.eml:Body`.

---

### Case 11: Cefatox IV Dilution & Stability Inquiry (Pure Email MI #2)
- **Category**: `Medical Information (MI)` ONLY (Confidence: ~0.98)
- **Attached Document**: None (Pure Email Text)
- **Email File**: `test-data/emails/email_11.eml`

```email
From: "Dr. Elena Rostova, PharmD, BCPS" <e.rostova@massgeneral-pharmacy.org>
To: "Clinevo Medical Information Service" <medinfo@clinevotech.com>
Date: Fri, 21 Nov 2025 09:15:00 -0500
Subject: Medical Information Request: In-Use Compatibility & Dilution Stability for Cefatox 1g in D5W
Message-ID: <20251121.091500.erostova@massgeneral-pharmacy.org>

Dear Medical Information Team,

I am writing on behalf of our inpatient pharmacy clinical operations team at Massachusetts General Hospital 
with a stability inquiry regarding Cefatox (cefatoxime sodium) 1g for Injection.

We are standardizing our hospital-wide intravenous infusion protocol for adult surgical prophylaxis in patients 
with normal renal function. The prescribed dose is 1g IV every 8 hours. Our cleanroom compounding protocol calls 
for reconstituting each 1g vial with 10 mL Sterile Water for Injection, followed by immediate dilution into a 100 mL 
Dextrose 5% in Water (D5W) IV infusion bag.

Could Medical Affairs please provide documentation or monograph data addressing:
1. Chemical stability and potency retention (>95%) of Cefatox 1g in 100 mL D5W at refrigerated temperatures (2 deg C to 8 deg C) for up to 48 hours.
2. In-use room temperature (20 deg C to 25 deg C) stability during a prolonged 4-hour intravenous infusion.
3. Compatibility with Y-site co-infusion of standard 0.9% Sodium Chloride or Lactated Ringer's solution.

Please note: There is no adverse patient event, no clinical complication, and no physical defect in our product stock. 
This inquiry is solely for hospital protocol formulation and compounding guidance.

Thank you for your assistance.

Sincerely,
Dr. Elena Rostova, PharmD, BCPS
Senior Clinical Compounding Specialist
Department of Pharmacy Services, Massachusetts General Hospital, Boston, MA
Tel: (617) 555-0144 | Email: e.rostova@massgeneral-pharmacy.org
```

**Expected AI Extraction**:
- Category: `Medical Information (MI)` ONLY.
- Product: `Cefatox 1g for Injection`.
- Questions Asked: `Refrigerated stability in D5W (48h), room-temp infusion stability (4h), and Y-site compatibility with normal saline or Lactated Ringer's`.
- Adverse Reaction / Product Defect: `None / Not Applicable`.
- Sourcing: `emails/email_11.eml:Body`.

---

## PART II: Published Medical Literature Articles (LIT-01 to LIT-07)
> **Regulatory Context**: Literature screening engine evaluates medical journal reprints (EMA GVP Module VI Section VI.B.1 & FDA 21 CFR 314.80).  
> **Key Objective**: Filter non-reportable review articles, accurately extract clinical cases from multi-column layouts, and split multi-case clinical series into separate individual ICSR records (**+30% Bonus Requirement**).

### LIT-01: Severe Drug-Induced Autoimmune Hepatitis (Single Case)
- **Document File**: `test-data/pdfs/literature_articles/article_01_dili_case.pdf`
- **Format**: 2-Column Academic Journal Layout (NEJM / Lancet style, 1 page)
- **Citation**: *Journal of Clinical Hepatology & Pharmacovigilance*, Vol 42, No 4, DOI: `10.1016/j.jchpv.2025.04.012`
- **Authors**: Julian Montgomery, MD, PhD; Evelyn Vance, MD; Kenneth Ross, MD (Princeton Academic Medical Center, NJ)
- **Category**: `Safety Report (ICSR)` (Reportable: YES — Identifiable single patient)
- **Clinical Summary**:
  - Patient: 61-year-old Caucasian male, 10-year refractory hypertension.
  - Drug: Cardioril 40 mg PO QD for 42 days.
  - Reaction: Idiosyncratic drug-induced autoimmune-like hepatitis, jaundice, dark urine, fatigue.
  - Labs: ALT 680 U/L (>12x ULN), AST 510 U/L (>12x ULN), Total Bilirubin 6.2 mg/dL, ANA titer 1:640, liver biopsy showing interface hepatitis with bridging necrosis.
  - De-challenge: Cardioril discontinued; oral prednisone taper; transaminases normalized in 6 weeks.
- **Expected AI Extraction**:
  - `category`: `["Safety Report (ICSR)"]`
  - `patient`: `{"age": "61 YRS", "sex": "MALE", "history": "Refractory hypertension, hyperlipidemia"}`
  - `product`: `{"name": "Cardioril (cardioril hydrochloride)", "dose": "40 mg PO QD", "latency": "42 days"}`
  - `reaction`: `{"terms": ["Drug-Induced Autoimmune Hepatitis", "Jaundice", "Hyperbilirubinemia"], "serious": true, "hospitalization": true}`
  - `source_citation`: `"article_01_dili_case.pdf:Page1"`

---

### LIT-02: Stevens-Johnson Syndrome with Neuroval (Single Case)
- **Document File**: `test-data/pdfs/literature_articles/article_02_sjs_case.pdf`
- **Format**: 2-Column Academic Journal Layout (1 page)
- **Citation**: *British Journal of Clinical Dermatology*, Case Reports, DOI: `10.1111/bjcd.2025.10921`
- **Authors**: Sanjay Gupta, MD; Priya Sharma, MD (Johns Hopkins Bayview Medical Center)
- **Category**: `Safety Report (ICSR)` (Reportable: YES — Identifiable single patient)
- **Clinical Summary**:
  - Patient: 24-year-old female with idiopathic trigeminal neuralgia.
  - Drug: Neuroval (neuroval HCl) 150 mg daily for 18 days.
  - Reaction: Stevens-Johnson syndrome (SJS), high fever (39.5°C), purpuric targetoid macules, 8% BSA epidermal detachment, lip hemorrhagic crusting, bilateral purulent conjunctivitis.
  - Outcome: ICU burn unit admission; IVIG (1 g/kg/day for 3 days); complete re-epithelialization by day 21. Serious: YES (Life-Threatening & Hospitalization).
- **Expected AI Extraction**:
  - `category`: `["Safety Report (ICSR)"]`
  - `patient`: `{"age": "24 YRS", "sex": "FEMALE", "indication": "Trigeminal neuralgia"}`
  - `product`: `{"name": "Neuroval (neuroval HCl)", "dose": "150 mg daily", "latency": "18 days"}`
  - `reaction`: `{"terms": ["Stevens-Johnson Syndrome (SJS)", "Epidermal Detachment 8% BSA", "Mucosal Crusting"], "serious": true, "life_threatening": true, "hospitalization": true}`
  - `source_citation`: `"article_02_sjs_case.pdf:Page1"`

---

### LIT-03: Cutaneous Adverse Reactions Series — 3 Distinct Patients (+30% Bonus Test Asset)
- **Document File**: `test-data/pdfs/literature_articles/article_03_multicase_series.pdf`
- **Format**: 2-Column Academic Journal Layout (Clinical Case Series, 1 page)
- **Citation**: *The Lancet Regional Health — Europe*, DOI: `10.1016/j.lanepe.2025.100984`
- **Authors**: Marcus Sterling, MD, FRCP; Alistair Finch, MBChB; Eleanor Vance, MD (Royal Free Hospital & Guy's and St Thomas' NHS Trust, London)
- **Category**: `Safety Report (ICSR)` — **MULTI-CASE CLINICAL SERIES**
- **Crucial Engine Requirement (+30% Bonus)**: Literature engine must recognize this document describes **3 separate independent patients** and split it into **3 distinct ICSR records** rather than aggregating them into 1 record.
- **Patient Case Breakdown**:
  1. **Patient 1 (A.J.)**: 45-year-old male, weight 81 kg. Drug: Cardioril 20 mg QD (onset day 22). Reaction: Severe Erythema Multiforme Major. Serious: YES (Hospitalization).
  2. **Patient 2 (B.L.)**: 62-year-old female, weight 64 kg. Drug: Corzapan 10 mg daily (onset 8 weeks). Reaction: Subacute Cutaneous Lupus Erythematosus (SCLE), Anti-Ro/SSA >240 U/mL. Serious: NO.
  3. **Patient 3 (C.M.)**: 38-year-old female, weight 59 kg. Drug: Cardioril 10 mg daily (onset 90 min). Reaction: Acute Urticaria and Periorbital Angioedema. Serious: YES (Life-Threatening / Emergency IM epinephrine).
- **Expected AI Extraction**:
  - `multicase_detected`: `true`, `cases_extracted_count`: `3`
  - `split_records`: 3 independent ICSR records with individual patient facts.
  - `source_citation`: `"article_03_multicase_series.pdf:Page1:Col1-Col2"`

---

### LIT-04: Preclinical In-Vitro & Animal Metabolism (Non-Reportable Negative Review)
- **Document File**: `test-data/pdfs/literature_articles/article_04_preclinical_review.pdf`
- **Format**: 2-Column Academic Journal Layout (1 page)
- **Citation**: *European Journal of Pharmaceutical Sciences*, DOI: `10.1016/j.ejps.2025.105412`
- **Authors**: Heinrich Mueller, PhD; Klaus Schmidt, PhD (Technical University of Munich)
- **Category**: `Not Relevant` / `Literature: Non-Reportable`
- **Clinical Context**: In-vitro metabolic clearance and CYP450 interaction assays in Sprague-Dawley rat hepatocytes and human liver microsomes. Zero human subjects, zero clinical cases.
- **Expected AI Decision**:
  - `reportable_to_health_authority`: `false`
  - `exclusion_reason`: *"Exclusively preclinical animal/in-vitro laboratory study without identifiable human clinical cases (GVP Module VI Section VI.B.1 exempt)."*

---

### LIT-05: Meta-Analysis & Systematic Review (Non-Reportable Negative Review)
- **Document File**: `test-data/pdfs/literature_articles/article_05_meta_analysis_review.pdf`
- **Format**: 2-Column Academic Journal Layout (1 page)
- **Citation**: *International Journal of Cardiology Reviews*, DOI: `10.1016/j.ijcard.2025.110294`
- **Authors**: Catherine Tremblay, MD; Jean-Luc Moreau, MD (Montreal Heart Institute & McGill University)
- **Category**: `Not Relevant` / `Literature: Non-Reportable`
- **Clinical Context**: Systematic review of 34 RCTs (28,450 aggregate participants). Reports pooled odds ratios. Zero individual identifiable patient reports.
- **Expected AI Decision**:
  - `reportable_to_health_authority`: `false`
  - `exclusion_reason`: *"Aggregate epidemiological review and statistical meta-analysis without individual identifiable patient case reports."*

---

### LIT-06: Delayed Fulminant Myocarditis (2-Page Buried Clinical Case)
- **Document File**: `test-data/pdfs/literature_articles/article_06_buried_case_study.pdf`
- **Format**: 2-Page Two-Column Academic Journal Layout (Dense, realistic multi-page paper)
- **Citation**: *Journal of Clinical Oncology & Immunotherapy*, Vol 18, No 3, DOI: `10.1200/JCOI.2025.18.3.412`
- **Authors**: Robert H. Caldwell, MD; Danielle M. Zhang, MD, PhD; Christopher Owens, MD (Dana-Farber Cancer Institute & Harvard Medical School)
- **Category**: `Safety Report (ICSR)` (Reportable: YES — Identifiable single patient buried after heavy background discussion)
- **Clinical Summary**:
  - Page 1: Abstract, extensive background on checkpoint inhibitor biology (PD-1 / CTLA-4 axis), epidemiological incidence rates from WHO VigiBase registries.
  - Case Presentation (buried across Page 1 & Page 2): 68-year-old female (Patient H.L., 62 kg) with metastatic melanoma receiving Nivolumab (Opdivo) 240 mg IV q2w + Ipilimumab (Yervoy) 1 mg/kg IV q6w. Developed severe acute fulminant myocarditis on day 44 (cycle 3), complete 3rd-degree AV block, troponin-T 1.84 ng/mL, LVEF decline to 32%, CICU admission, temporary transvenous pacing, pulse methylprednisolone 1,000mg/day, and plasmapheresis.
- **Expected AI Extraction**:
  - `category`: `["Safety Report (ICSR)"]`
  - `patient`: `{"identifier": "Patient H.L.", "age": "68 YRS", "sex": "FEMALE", "weight": "62 kg"}`
  - `product`: `{"name": "Nivolumab (Opdivo) + Ipilimumab (Yervoy)", "latency": "Day 44 (Cycle 3)"}`
  - `reaction`: `{"terms": ["Fulminant Immune-Mediated Myocarditis", "Complete AV Heart Block", "Cardiogenic Shock / LVEF Decline to 32%"], "serious": true, "life_threatening": true, "hospitalization": true}`
  - `source_citation`: `"article_06_buried_case_study.pdf:Page1:Col2 to Page2:Col1"`

---

### LIT-07: Drug-Induced Interstitial Lung Disease (2-Page Multi-Case + Registry Screening)
- **Document File**: `test-data/pdfs/literature_articles/article_07_complex_screening_case.pdf`
- **Format**: 2-Page Two-Column Academic Journal Layout
- **Citation**: *American Journal of Respiratory and Critical Care Medicine*, DOI: `10.1164/rccm.2025.09.1182`
- **Authors**: Samantha Reed, MD; Tariq Al-Mansoor, MD; Fiona Gallagher, MD (Johns Hopkins University School of Medicine)
- **Category**: `Safety Report (ICSR)` — **MULTI-CASE SCREENING (2 Patients + Non-Case Registry Filtering)**
- **Clinical Summary**:
  - Contains a distracting section describing a 420-patient non-case observational registry cohort (must be filtered out as non-reportable background).
  - Patient 1: 54-year-old male (Patient T.K., 75 kg) with rheumatoid arthritis receiving Infliximab (Remicade) 5 mg/kg IV infusions. Developed acute severe interstitial pneumonitis, bilateral ground-glass opacities, hypoxemia (PaO2 54 mmHg). Serious: YES (MICU, mechanical ventilation).
  - Patient 2: 41-year-old female (Patient M.S., 58 kg) with psoriatic arthritis receiving Leflunomide (Arava) 20 mg PO QD. Developed Cryptogenic Organizing Pneumonia (COP / BOOP), DLCO decline 28%. Serious: YES (Hospitalized, recovered after cholestyramine washout and prednisone).
- **Expected AI Extraction**:
  - `multicase_detected`: `true`, `total_cases_extracted`: `2`
  - `non_case_cohort_filtered`: `true` (420-patient cohort ignored)
  - `split_records`: 2 independent ICSR records.
  - `source_citation`: `"article_07_complex_screening_case.pdf:Page1-Page2"`

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
- **Role**: Structured catalog indexing all 28 assets in the test suite with cleanly scoped statistics:
  - `email_statistics`: 11 emails (6 ICSR, 2 PQC, 2 MI, 1 Not Relevant, 1 Multi-label)
  - `document_statistics`: 20 physical documents (5 Digital, 1 Scanned, 7 Literature, 2 Non-English, 2 Quality, 2 Medical Info, 1 Irrelevant)
  - `literature_statistics`: 7 articles (5 case-bearing, 2 non-reportable negative, 8 extractable patient cases, 2 multi-page articles)
  - `deferred_requirements`: Explicitly tracking the 2nd handwritten PDF reserved for live user sheet.

### 2. `benchmark.json` — Ground Truth Evaluation Key
- **Location**: [`test-data/ground_truth/benchmark.json`](file:///c:/projects/SmartInbox/test-data/ground_truth/benchmark.json)
- **Role**: 27 comprehensive gold-standard ground truth cases for automated precision/recall grading:
  - Covers every single physical asset on disk.
  - Zero-hallucination verified: Case 02 dose is strictly `"Not stated"`.
  - Full source citations mapping each extracted value to document page and section.

---

## PART V: Final Minimum Assignment Requirements & Compliance Audit Checklist

### Physical File Audit Against Clinevo Assignment Requirements

| Data / Test Asset | Minimum Required | Target to Create | Current Physical Status | Audit Result | Remaining |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Intake `.eml` emails** | 10 | 10–11 | **11 files on disk** (`email_01.eml` to `email_11.eml`) | **PASS** | **0** |
| **Safety Report (ICSR) examples** | Covered in emails | 6+ | **6 emails + 10 PDFs** | **PASS** | **0** |
| **Quality Complaint (PQC)-only examples** | 2 | 2 | **2 emails** (Case 07, 08) + **2 PDFs** | **PASS** | **0** |
| **Medical Information (MI)-only examples** | 2 | 2 | **2 emails** (Case 09, 11) + **2 PDFs** (MED-01, 02) | **PASS** | **0** |
| **Not Relevant / Marketing examples** | 1 | 1+ | **1 email** (Case 10) + **1 PDF** (IRR-01) | **PASS** | **0** |
| **Multi-label ICSR + PQC example** | At least 1 | 1+ | **1 case** (Case 04 MedWatch + contaminated vial) | **PASS** | **0** |
| **Normal digital PDFs** | 5 | 5+ | **5 files on disk** (`digital_forms/*.pdf`) + 5 others | **PASS** | **0** |
| **Scanned / handwritten PDFs** | 2 | 2 | **1 file on disk** (`urgent_care_intake_handwritten.pdf`) | **DEFERRED** | **1** |
| **Case-bearing article PDFs** | 5 | 5 | **5 files on disk** (Articles 01, 02, 03, 06, 07) | **PASS** | **0** |
| **Non-reportable negative article PDFs**| Recommended | 2 | **2 files on disk** (Articles 04, 05) | **PASS** | **0** |
| **Total Literature Articles** | 5 | 7 | **7 files on disk** (`literature_articles/*.pdf`) | **PASS** | **0** |
| **Non-English PDFs** | 2 | 2 | **2 files on disk** (`notificacion_ram_madrid.pdf`, `bericht_uaw_charite_berlin.pdf`) | **PASS** | **0** |
| **PDF containing structured table(s)** | Required | 2+ | **8 PDFs on disk** (CIOMS labs, MedWatch grids, dosing tables) | **PASS** | **0** |
| **PDF containing meaningful image(s)** | Required | 2+ | **2 PDFs on disk** (handwritten intake, vial contamination) | **PASS** | **0** |
| **Image requiring human-review flag** | Required | 1+ | **1 photo exhibit** (cracked crimp seal with particulate) | **PASS** | **0** |
| **Documents with deliberately missing fields**| Required | 2+ | **Cases 02, 03, 08, 09** (testing `"Not stated"`) | **PASS** | **0** |
| **Field-level source/page traceability** | Required | All docs | **Full ground truth citations** in `benchmark.json` | **PASS** | **0** |
| **Machine-readable ground truth JSON** | Required | 1 file | **1 file on disk** (`benchmark.json` covering all 27 cases) | **PASS** | **0** |
| **Dataset manifest** | Recommended | 1 file | **1 file on disk** (`manifest.json` indexing 28 assets) | **PASS** | **0** |
| **Total Physical PDFs Verified** | 19 | 20 | **20 files on disk** (21st deferred for user photo) | **95% PASS** | **1** |

---

### Required PDF Flavor Coverage

| PDF Flavor | Minimum Required | Current Physical Count | Verification Location | Status |
| :--- | :---: | :---: | :--- | :---: |
| **Digital structured PDF** | 5 | **5** | `test-data/pdfs/digital_forms/` | **PASS** |
| **Scanned / handwritten** | 2 | **1** | `test-data/pdfs/scanned_handwritten/` | **1 DEFERRED (User Form)** |
| **Case-bearing medical articles** | 5 | **5** | `test-data/pdfs/literature_articles/` | **PASS** |
| **Non-reportable negative articles**| Recommended | **2** | `test-data/pdfs/literature_articles/` | **PASS** |
| **Non-English (Spanish & German)** | 2 | **2** | `test-data/pdfs/non_english/` | **PASS** |
| **Quality complaint specific** | 2 | **2** | `test-data/pdfs/quality_complaints/` | **PASS** |
| **Medical info specific** | 2 | **2** | `test-data/pdfs/medical_info/` | **PASS** |
| **Irrelevant / marketing** | 1 | **1** | `test-data/pdfs/irrelevant/` | **PASS** |
"""

with open(MD_PATH, "w", encoding="utf-8") as f:
    f.write(content)

print(f"[SUCCESS] Updated {MD_PATH}. Total bytes: {len(content)}")
