import os
import json

BASE_DIR = r"c:\projects\SmartInbox\test-data"
GT_DIR = os.path.join(BASE_DIR, "ground_truth")
os.makedirs(GT_DIR, exist_ok=True)

# -------------------------------------------------------------
# 1. BUILD COMPLETE BENCHMARK.JSON
# -------------------------------------------------------------
benchmark_data = {
  "version": "2.0.0",
  "description": "Comprehensive Ground Truth benchmark answers covering all 11 emails and 20 physical document assets for automated evaluation of Smart Inbox AI pipeline",
  "audit_rules": {
    "zero_hallucination": "Unstated fields MUST be returned strictly as 'Not stated' rather than guessed",
    "source_traceability": "All extracted facts must map to exact document name and section/page",
    "multi_label_support": "Documents with both ICSR and PQC elements must return both categories"
  },
  "cases": {
    # ------------------ INBOX EMAILS ------------------
    "CASE-01": {
      "type": "email_intake",
      "email_file": "emails/email_01.eml",
      "attachment_file": "pdfs/digital_forms/cioms_form_MK_Cardioril.pdf",
      "categories": ["Safety Report (ICSR)"],
      "confidence_threshold": 0.95,
      "patient": {
        "age": "58 YRS",
        "sex": "FEMALE",
        "initials": "M.K.",
        "weight": "68 kg",
        "medical_history": "Essential Hypertension, Type 2 Diabetes Mellitus"
      },
      "product": {
        "name": "Cardioril (cardioril hydrochloride)",
        "dose": "20 mg once daily (QD)",
        "route": "Oral (tablet)",
        "lot": "CR-2025-0981"
      },
      "reaction": {
        "terms": ["Acute Drug-Induced Liver Injury (DILI)", "Jaundice", "Scleral Icterus"],
        "onset": "08-NOV-2025",
        "serious": True,
        "hospitalization": True,
        "life_threatening": False,
        "death": False
      },
      "lab_tests": {
        "ALT": "540 U/L",
        "AST": "420 U/L",
        "Total_Bilirubin": "4.8 mg/dL",
        "Alkaline_Phosphatase": "210 U/L"
      },
      "reporter": {
        "name": "Dr. Sarah Jenkins, MD, FACP",
        "institution": "MetroHealth Medical Center, Chicago, IL",
        "email": "sjenkins@metrohealth-chicago.org"
      },
      "source_citations": {
        "patient": "cioms_form_MK_Cardioril.pdf:Page1:Box1",
        "drug": "cioms_form_MK_Cardioril.pdf:Page1:Box14",
        "reaction": "cioms_form_MK_Cardioril.pdf:Page1:Box6",
        "labs": "cioms_form_MK_Cardioril.pdf:Page1:Box23",
        "reporter": "cioms_form_MK_Cardioril.pdf:Page1:Box24"
      }
    },
    "CASE-02": {
      "type": "email_intake",
      "email_file": "emails/email_02.eml",
      "attachment_file": "pdfs/scanned_handwritten/urgent_care_intake_handwritten.pdf",
      "categories": ["Safety Report (ICSR)"],
      "confidence_threshold": 0.82,
      "patient": {
        "name": "Jane Doe",
        "dob": "05/18/1990",
        "age": "33",
        "sex": "F",
        "weight": "Not stated"
      },
      "product": {
        "name": "InjectaPen",
        "dose": "Not stated",
        "lot": "Not stated"
      },
      "reaction": {
        "terms": [
          "Acute Anaphylaxis (Grade 3)",
          "Generalized Urticaria / Hives",
          "Facial & Perioral Angioedema",
          "Inspiratory Stridor"
        ],
        "serious": True,
        "life_threatening": True,
        "hospitalization": True,
        "death": False
      },
      "treatment": {
        "emergency_intervention": "Epinephrine 0.3 mg IM, high-flow oxygen, IV fluid resuscitation"
      },
      "vitals": {
        "BP": "85/50",
        "HR": "128 bpm",
        "SpO2": "91%"
      },
      "reporter": {
        "name": "Dr. A. Peterson, MD",
        "institution": "St. Mary's General Hospital Emergency Department",
        "email": "a.peterson@stmarys-hospital.org"
      },
      "source_citations": {
        "all": "urgent_care_intake_handwritten.pdf:Page1"
      }
    },
    "CASE-03": {
      "type": "email_intake",
      "email_file": "emails/email_03.eml",
      "attachment_file": None,
      "categories": ["Safety Report (ICSR)"],
      "confidence_threshold": 0.90,
      "patient": {
        "name": "Emily Watson",
        "age": "42 years old",
        "sex": "Female",
        "weight": "Not stated"
      },
      "product": {
        "name": "Corzapan 10mg tablets",
        "dose": "10mg once daily",
        "lot": "Not stated"
      },
      "reaction": {
        "terms": [
          "Tachycardia (154 bpm)",
          "Palpitations",
          "Lightheadedness",
          "Near-syncope"
        ],
        "serious": False,
        "hospitalization": False,
        "life_threatening": False
      },
      "reporter": {
        "name": "Emily Watson (Consumer / Patient)",
        "email": "emily.watson82@gmail.com"
      },
      "source_citations": {
        "all": "emails/email_03.eml:Body"
      }
    },
    "CASE-04": {
      "type": "email_intake",
      "email_file": "emails/email_04.eml",
      "attachment_file": "pdfs/quality_complaints/vial_contamination_sepsis.pdf",
      "categories": ["Safety Report (ICSR)", "Quality Complaint (PQC)"],
      "confidence_threshold": 0.92,
      "quality_complaint": {
        "product": "Cefatox (cefatoxime sodium) 1g for Inj.",
        "lot": "CX54831",
        "expiry": "08/2025",
        "defect": "Cracked aluminum crimp collar, compromised rubber stopper closure, visible black particulate contamination",
        "photo_present": True,
        "photo_requires_human_review": True
      },
      "safety_report": {
        "patient": {
          "identifier": "Arthur Pendelton (A.P.)",
          "age": "71 YRS",
          "sex": "MALE",
          "weight": "74 kg"
        },
        "reaction": {
          "terms": [
            "Severe Acute Bacteremia",
            "Distributive Septic Shock",
            "Hypotension (BP 72/40)",
            "Hyperthermia (39.8 C)"
          ],
          "serious": True,
          "life_threatening": True,
          "hospitalization": True,
          "death": False
        }
      },
      "reporter": {
        "name": "Dr. Robert Sterling, MD (ICU Director)",
        "institution": "Northwestern Memorial Hospital, Chicago, IL",
        "email": "rsterling@nm-icu.org"
      },
      "source_citations": {
        "pqc": "vial_contamination_sepsis.pdf:Page1:SectionC",
        "photo": "vial_contamination_sepsis.pdf:Page2:Exhibit1",
        "safety": "vial_contamination_sepsis.pdf:Page1:SectionB"
      }
    },
    "CASE-05": {
      "type": "email_intake",
      "email_file": "emails/email_05.eml",
      "attachment_file": "pdfs/non_english/notificacion_ram_madrid.pdf",
      "categories": ["Safety Report (ICSR)"],
      "confidence_threshold": 0.92,
      "language": "es",
      "translated": True,
      "patient": {
        "initials": "Carmen Ortiz (C.O.)",
        "age": "29 AÑOS",
        "sex": "MUJER",
        "weight": "54 kg"
      },
      "product": {
        "name": "Lamotrigina (Lamictal) 100 mg",
        "dose": "100 mg/día vía oral",
        "lot": "LM-9941"
      },
      "reaction": {
        "original_terms": ["Necrólisis Epidérmica Tóxica (NET / Síndrome de Lyell)", "Desprendimiento dermoepidérmico >35% SC"],
        "translated_terms": ["Toxic Epidermal Necrolysis (TEN / Lyell Syndrome)", "Epidermal detachment >35% body surface area"],
        "serious": True,
        "life_threatening": True,
        "hospitalization": True,
        "death": False
      },
      "reporter": {
        "name": "Dra. Elena Gómez Prado (Dermatología)",
        "institution": "Hospital Universitario La Paz, Madrid, España",
        "email": "egomez@hulp-salud.madrid.org"
      },
      "source_citations": {
        "all": "notificacion_ram_madrid.pdf:Page1"
      }
    },
    "CASE-06": {
      "type": "email_intake",
      "email_file": "emails/email_06.eml",
      "attachment_file": "pdfs/digital_forms/fda_medwatch_followup.pdf",
      "categories": ["Safety Report (ICSR)"],
      "confidence_threshold": 0.95,
      "report_type": "Follow-up Report (Documentation of De-challenge)",
      "patient": {
        "identifier": "David Miller (D.M.)",
        "age": "52 YRS",
        "sex": "MALE",
        "weight": "79 kg"
      },
      "product": {
        "name": "Neuroval (neuroval HCl) 400mg PO QD",
        "lot": "NV-2025-110",
        "action_taken": "Permanently Discontinued"
      },
      "reaction": {
        "terms": ["Generalized Tonic-Clonic Seizures - Resolved", "Post-ictal State - Resolved"],
        "outcome": "Recovered / Resolved without permanent neurological sequelae",
        "dechallenge": "Positive (Seizures ceased after Neuroval cessation)",
        "serious": True,
        "hospitalization": True
      },
      "reporter": {
        "name": "Dr. Richard Vance, MD",
        "institution": "Department of Neurology, Columbia University Medical Center, NY",
        "email": "rvance@cumc.columbia.edu"
      },
      "source_citations": {
        "all": "fda_medwatch_followup.pdf:Page1"
      }
    },
    "CASE-07": {
      "type": "email_intake",
      "email_file": "emails/email_07.eml",
      "attachment_file": "pdfs/quality_complaints/packaging_defect_report.pdf",
      "categories": ["Quality Complaint (PQC)"],
      "confidence_threshold": 0.95,
      "patient": None,
      "quality_complaint": {
        "product": "Cardioril 20mg Blister Packs (10x10)",
        "lot": "BL-8802",
        "expiry": "11/2027",
        "defect": "Breached blister foil seal, moisture ingress, oxidized crumbling discolored tablets",
        "quantity_affected": "14 of 50 blister cartons (28% sample defect rate)",
        "photo_attached": True
      },
      "reporter": {
        "name": "Patricia Morales, RPh (Pharmacy Operations Manager)",
        "institution": "Allegheny General Hospital, Pittsburgh, PA",
        "email": "pmorales@ahn-pharmacy.org"
      },
      "source_citations": {
        "all": "packaging_defect_report.pdf:Page1"
      }
    },
    "CASE-08": {
      "type": "email_intake",
      "email_file": "emails/email_08.eml",
      "attachment_file": None,
      "categories": ["Quality Complaint (PQC)"],
      "confidence_threshold": 0.95,
      "patient": None,
      "quality_complaint": {
        "product": "Corzapan 10mg commercial packaging",
        "lot": "CZ-9021",
        "defect": "Suspected counterfeit product, blurred misaligned typography on packaging, missing holographic tamper-evident seal, abnormal chalky texture",
        "quarantine_status": "Quarantined in pharmacy vault"
      },
      "reporter": {
        "name": "Thomas Albright, PharmD",
        "institution": "Greenwood Apothecary & Retail Pharmacy, Austin, TX",
        "email": "talbright@greenwood-rx.com"
      },
      "source_citations": {
        "all": "emails/email_08.eml:Body"
      }
    },
    "CASE-09": {
      "type": "email_intake",
      "email_file": "emails/email_09.eml",
      "attachment_file": None,
      "categories": ["Medical Information (MI)"],
      "confidence_threshold": 0.97,
      "patient": None,
      "medical_inquiry": {
        "product": "Corzapan 10mg film-coated tablets",
        "questions": [
          "Can Corzapan 10mg tablets be crushed and suspended for nasogastric (NG) enteral feeding tube administration?",
          "Does active substance adsorb to polyurethane enteral feeding tubes?",
          "Compatibility with concurrent enteral nutrition formulas?"
        ],
        "clinical_context": "Elderly patient with severe dysphagia requiring enteral administration"
      },
      "adverse_event_present": False,
      "product_defect_present": False,
      "reporter": {
        "name": "David Wu, PharmD, BCPS",
        "institution": "UCSF Health, San Francisco, CA",
        "email": "david.wu@ucsf-clinical.edu"
      },
      "source_citations": {
        "all": "emails/email_09.eml:Body"
      }
    },
    "CASE-10": {
      "type": "email_intake",
      "email_file": "emails/email_10.eml",
      "attachment_file": None,
      "categories": ["Not Relevant"],
      "confidence_threshold": 0.99,
      "reason": "Commercial marketing advertisement newsletter for an industry conference (Global AI in Pharmacovigilance & Drug Safety Summit 2026). Contains zero patient safety data, zero product quality defects, and zero clinical inquiries.",
      "extracted_entities": {},
      "reporter": {
        "name": "PharmaTech Global Summit",
        "email": "events@pharmasummit-global2026.com"
      },
      "source_citations": {
        "all": "emails/email_10.eml:Body"
      }
    },
    "CASE-11": {
      "type": "email_intake",
      "email_file": "emails/email_11.eml",
      "attachment_file": None,
      "categories": ["Medical Information (MI)"],
      "confidence_threshold": 0.98,
      "patient": None,
      "medical_inquiry": {
        "product": "Cefatox (cefatoxime sodium) 1g for Injection",
        "questions": [
          "Chemical stability and potency retention (>95%) of Cefatox 1g in 100 mL D5W at refrigerated temperatures (2-8 deg C) for up to 48 hours?",
          "In-use room temperature (20-25 deg C) stability during prolonged 4-hour intravenous infusion?",
          "Compatibility with Y-site co-infusion of 0.9% Sodium Chloride or Lactated Ringer's solution?"
        ],
        "clinical_context": "Hospital compounding standardization protocol for surgical prophylaxis"
      },
      "adverse_event_present": False,
      "product_defect_present": False,
      "reporter": {
        "name": "Dr. Elena Rostova, PharmD, BCPS",
        "institution": "Department of Pharmacy Services, Massachusetts General Hospital, Boston, MA",
        "email": "e.rostova@massgeneral-pharmacy.org"
      },
      "source_citations": {
        "all": "emails/email_11.eml:Body"
      }
    },

    # ------------------ PUBLISHED LITERATURE ARTICLES ------------------
    "LIT-01": {
      "type": "literature_screening",
      "pdf_file": "pdfs/literature_articles/article_01_dili_case.pdf",
      "journal": "Journal of Clinical Hepatology & Pharmacovigilance",
      "categories": ["Safety Report (ICSR)"],
      "reportable": True,
      "total_cases_extracted": 1,
      "patient": {
        "age": "61 YRS",
        "sex": "MALE",
        "ethnicity": "Caucasian",
        "history": "10-year refractory hypertension, hyperlipidemia"
      },
      "product": {
        "name": "Cardioril (cardioril hydrochloride)",
        "dose": "40 mg PO QD",
        "latency": "42 days"
      },
      "reaction": {
        "terms": ["Drug-Induced Autoimmune-Like Hepatitis", "Jaundice", "Scleral Icterus", "Interface Hepatitis with Bridging Necrosis"],
        "serious": True,
        "hospitalization": True,
        "life_threatening": False
      },
      "labs": {
        "ALT": "680 U/L",
        "AST": "510 U/L",
        "Total_Bilirubin": "6.2 mg/dL",
        "Alkaline_Phosphatase": "240 U/L",
        "ANA": "1:640 (speckled)",
        "IgG": "2,100 mg/dL"
      },
      "authors": "Julian Montgomery, MD, PhD; Evelyn Vance, MD; Kenneth Ross, MD",
      "source_citations": {
        "all": "article_01_dili_case.pdf:Page1"
      }
    },
    "LIT-02": {
      "type": "literature_screening",
      "pdf_file": "pdfs/literature_articles/article_02_sjs_case.pdf",
      "journal": "British Journal of Clinical Dermatology",
      "categories": ["Safety Report (ICSR)"],
      "reportable": True,
      "total_cases_extracted": 1,
      "patient": {
        "age": "24 YRS",
        "sex": "FEMALE",
        "indication": "Idiopathic trigeminal neuralgia"
      },
      "product": {
        "name": "Neuroval (neuroval HCl)",
        "dose": "150 mg daily",
        "latency": "18 days"
      },
      "reaction": {
        "terms": [
          "Stevens-Johnson Syndrome (SJS)",
          "Purpuric Targetoid Macules with Epidermal Detachment 8% BSA",
          "Lip Hemorrhagic Crusting",
          "Bilateral Purulent Conjunctivitis"
        ],
        "serious": True,
        "life_threatening": True,
        "hospitalization": True
      },
      "authors": "Sanjay Gupta, MD; Priya Sharma, MD",
      "source_citations": {
        "all": "article_02_sjs_case.pdf:Page1"
      }
    },
    "LIT-03": {
      "type": "literature_screening",
      "pdf_file": "pdfs/literature_articles/article_03_multicase_series.pdf",
      "journal": "The Lancet Regional Health — Europe",
      "categories": ["Safety Report (ICSR)"],
      "reportable": True,
      "multicase": True,
      "total_cases_extracted": 3,
      "split_cases": [
        {
          "case_no": 1,
          "patient": {"initials": "A.J.", "age": "45 YRS", "sex": "MALE", "weight": "81 kg"},
          "product": {"name": "Cardioril", "dose": "20 mg once daily", "latency": "Day 22"},
          "reaction": {"terms": ["Erythema Multiforme Major", "Target Lesions with Blistering", "Oral Mucosal Erosions"], "serious": True, "hospitalization": True}
        },
        {
          "case_no": 2,
          "patient": {"initials": "B.L.", "age": "62 YRS", "sex": "FEMALE", "weight": "64 kg"},
          "product": {"name": "Corzapan", "dose": "10 mg daily", "latency": "8 weeks"},
          "reaction": {"terms": ["Drug-Induced Subacute Cutaneous Lupus Erythematosus (SCLE)", "Anti-Ro/SSA >240 U/mL", "ANA 1:320"], "serious": False, "hospitalization": False}
        },
        {
          "case_no": 3,
          "patient": {"initials": "C.M.", "age": "38 YRS", "sex": "FEMALE", "weight": "59 kg"},
          "product": {"name": "Cardioril", "dose": "10 mg daily", "latency": "90 minutes"},
          "reaction": {"terms": ["Acute Generalized Urticaria", "Periorbital Angioedema", "Dysphonia"], "serious": True, "life_threatening": True, "hospitalization": False}
        }
      ],
      "authors": "Marcus Sterling, MD, FRCP; Alistair Finch, MBChB; Eleanor Vance, MD",
      "source_citations": {
        "case_1": "article_03_multicase_series.pdf:Page1:Col1",
        "case_2": "article_03_multicase_series.pdf:Page1:Col1",
        "case_3": "article_03_multicase_series.pdf:Page1:Col2"
      }
    },
    "LIT-04": {
      "type": "literature_screening",
      "pdf_file": "pdfs/literature_articles/article_04_preclinical_review.pdf",
      "journal": "European Journal of Pharmaceutical Sciences",
      "categories": ["Not Relevant"],
      "reportable": False,
      "total_cases_extracted": 0,
      "exclusion_reason": "Preclinical in-vitro and rat hepatocyte metabolic clearance study. Contains zero human subjects and zero clinical cases (GVP Module VI Section VI.B.1 exempt).",
      "authors": "Heinrich Mueller, PhD; Klaus Schmidt, PhD",
      "source_citations": {
        "all": "article_04_preclinical_review.pdf:Page1"
      }
    },
    "LIT-05": {
      "type": "literature_screening",
      "pdf_file": "pdfs/literature_articles/article_05_meta_analysis_review.pdf",
      "journal": "International Journal of Cardiology Reviews",
      "categories": ["Not Relevant"],
      "reportable": False,
      "total_cases_extracted": 0,
      "exclusion_reason": "Systematic review and meta-analysis of 34 clinical trials (28,450 aggregate patients). Reports pooled odds ratios without individual identifiable patient case reports.",
      "authors": "Catherine Tremblay, MD; Jean-Luc Moreau, MD",
      "source_citations": {
        "all": "article_05_meta_analysis_review.pdf:Page1"
      }
    },
    "LIT-06": {
      "type": "literature_screening",
      "pdf_file": "pdfs/literature_articles/article_06_buried_case_study.pdf",
      "journal": "Journal of Clinical Oncology & Immunotherapy",
      "categories": ["Safety Report (ICSR)"],
      "reportable": True,
      "pages_count": 2,
      "total_cases_extracted": 1,
      "patient": {
        "identifier": "Patient H.L.",
        "age": "68 YRS",
        "sex": "FEMALE",
        "weight": "62 kg",
        "indication": "BRAF wild-type stage IV metastatic cutaneous melanoma"
      },
      "product": {
        "name": "Nivolumab (Opdivo) 240 mg IV q2w + Ipilimumab (Yervoy) 1 mg/kg IV q6w",
        "latency": "Day 44 post-initiation (Cycle 3)"
      },
      "reaction": {
        "terms": [
          "Delayed Immune-Mediated Fulminant Myocarditis",
          "Complete (Third-Degree) AV Heart Block with Junctional Escape Rhythm",
          "Acute LVEF Decline to 32% (Biventricular Hypokinesis)",
          "Cardiogenic Shock"
        ],
        "serious": True,
        "life_threatening": True,
        "hospitalization": True
      },
      "diagnostics": {
        "Troponin_T": "1.84 ng/mL (ref <0.014)",
        "NT_proBNP": "4,820 pg/mL",
        "Biopsy": "Dense lymphocytic infiltration (CD4+/CD8+) with multifocal cardiomyocyte necrosis"
      },
      "authors": "Robert H. Caldwell, MD; Danielle M. Zhang, MD, PhD; Christopher Owens, MD",
      "source_citations": {
        "all": "article_06_buried_case_study.pdf:Page1:Col2 to Page2:Col1"
      }
    },
    "LIT-07": {
      "type": "literature_screening",
      "pdf_file": "pdfs/literature_articles/article_07_complex_screening_case.pdf",
      "journal": "American Journal of Respiratory and Critical Care Medicine",
      "categories": ["Safety Report (ICSR)"],
      "reportable": True,
      "pages_count": 2,
      "multicase": True,
      "total_cases_extracted": 2,
      "non_case_cohort_filtered": "420-patient observational registry cohort correctly filtered out as non-case background",
      "split_cases": [
        {
          "case_no": 1,
          "patient": {"identifier": "Patient T.K.", "age": "54 YRS", "sex": "MALE", "weight": "75 kg", "history": "Seropositive rheumatoid arthritis"},
          "product": {"name": "Infliximab (Remicade)", "dose": "5 mg/kg IV infusions", "latency": "12 days post 4th infusion"},
          "reaction": {
            "terms": ["Acute Drug-Induced Interstitial Pneumonitis", "Hypoxemic Respiratory Failure (PaO2 54 mmHg)", "Diffuse Bilateral Ground-Glass Opacities"],
            "serious": True,
            "life_threatening": True,
            "hospitalization": True
          }
        },
        {
          "case_no": 2,
          "patient": {"identifier": "Patient M.S.", "age": "41 YRS", "sex": "FEMALE", "weight": "58 kg", "history": "Psoriatic arthritis"},
          "product": {"name": "Leflunomide (Arava)", "dose": "20 mg PO QD", "latency": "12 weeks"},
          "reaction": {
            "terms": ["Cryptogenic Organizing Pneumonia (COP / BOOP)", "DLCO decline by 28%", "Peribronchovascular consolidations"],
            "serious": True,
            "hospitalization": True,
            "life_threatening": False
          }
        }
      ],
      "authors": "Samantha Reed, MD; Tariq Al-Mansoor, MD; Fiona Gallagher, MD",
      "source_citations": {
        "case_1": "article_07_complex_screening_case.pdf:Page1:Col1-Col2",
        "case_2": "article_07_complex_screening_case.pdf:Page1:Col2 to Page2:Col1"
      }
    },

    # ------------------ NON-ENGLISH STANDALONE REPORTS ------------------
    "NON-ENG-01": {
      "type": "regulatory_form",
      "pdf_file": "pdfs/non_english/notificacion_ram_madrid.pdf",
      "origin": "Agencia Española de Medicamentos y Productos Sanitarios (AEMPS) - Madrid, España",
      "language": "es",
      "categories": ["Safety Report (ICSR)"],
      "patient": {"initials": "Carmen Ortiz (C.O.)", "age": "29 AÑOS", "sex": "MUJER", "weight": "54 kg"},
      "product": {"name": "Lamotrigina (Lamictal) 100 mg", "dose": "100 mg/día vía oral", "lot": "LM-9941"},
      "reaction": {
        "terms": ["Toxic Epidermal Necrolysis", "Necrólisis Epidérmica Tóxica"],
        "serious": True,
        "life_threatening": True,
        "hospitalization": True
      },
      "source_citations": {"all": "notificacion_ram_madrid.pdf:Page1"}
    },
    "NON-ENG-02": {
      "type": "regulatory_form",
      "pdf_file": "pdfs/non_english/bericht_uaw_charite_berlin.pdf",
      "origin": "Bundesinstitut für Arzneimittel und Medizinprodukte (BfArM) / Charité Berlin, Deutschland",
      "language": "de",
      "categories": ["Safety Report (ICSR)"],
      "patient": {
        "name": "Hans Schneider (H.S.)",
        "dob": "04.08.1962",
        "age": "63 JAHRE",
        "sex": "MÄNNLICH",
        "weight": "88 kg"
      },
      "product": {
        "name": "Cardioril (Cardioril-HCl) 20 mg",
        "dose": "20 mg 1x täglich p.o.",
        "lot": "CR-2025-0814",
        "action_taken": "Dauerhaft abgesetzt"
      },
      "reaction": {
        "original_terms": ["Akutes Angioödem von Lippen, Zunge und Pharynx", "Schwere Dyspnoe", "Inspiratorischer Stridor", "Diffuses Urtikaria-Exanthem"],
        "translated_terms": ["Acute Angioedema of Lips, Tongue, and Pharynx", "Severe Dyspnea", "Inspiratory Stridor", "Diffuse Urticaria"],
        "serious": True,
        "life_threatening": True,
        "hospitalization": True
      },
      "reporter": {
        "name": "Dr. med. Wolfgang Becker",
        "institution": "Charité – Universitätsmedizin Berlin, Campus Virchow-Klinikum",
        "email": "w.becker@charite.de"
      },
      "source_citations": {"all": "bericht_uaw_charite_berlin.pdf:Page1"}
    },

    # ------------------ DIGITAL CIOMS / MEDWATCH FORMS ------------------
    "DIG-03": {
      "type": "regulatory_form",
      "pdf_file": "pdfs/digital_forms/cioms_pediatric_oncology.pdf",
      "categories": ["Safety Report (ICSR)"],
      "special_population": "Pediatric",
      "patient": {
        "name": "Lucas Torres (L.T.)",
        "age": "8 YRS",
        "dob": "14-JUL-2017",
        "sex": "MALE",
        "weight": "26 kg",
        "indication": "Acute Lymphoblastic Leukemia (ALL) maintenance"
      },
      "product": {
        "name": "OncoShield (peg-oncoshield)",
        "dose": "50mg/m2 IV",
        "lot": "OS-2025-771",
        "expiry": "04/2026"
      },
      "reaction": {
        "terms": ["Acute Cytokine Release Syndrome / Severe Infusion Reaction", "Severe Rigors", "High Fever (40.1 C)", "Hypoxemia (SpO2 88%)"],
        "serious": True,
        "life_threatening": True,
        "hospitalization": True
      },
      "reporter": {
        "name": "Dr. Amanda Bennett, MD, FAAP",
        "institution": "Children's Memorial Hospital, Boston, MA",
        "email": "abennett@childrens-boston.org"
      },
      "source_citations": {"all": "cioms_pediatric_oncology.pdf:Page1"}
    },
    "DIG-04": {
      "type": "regulatory_form",
      "pdf_file": "pdfs/digital_forms/fda_medwatch_initial_neuroval.pdf",
      "categories": ["Safety Report (ICSR)"],
      "report_type": "Initial Report",
      "patient": {
        "identifier": "David Miller (D.M.)",
        "age": "52 YRS",
        "sex": "MALE",
        "weight": "79 kg"
      },
      "product": {
        "name": "Neuroval (neuroval HCl)",
        "dose": "400mg PO QD",
        "lot": "NV-2025-110"
      },
      "reaction": {
        "terms": ["Witnessed New-Onset Generalized Tonic-Clonic Seizure (3.5 min)", "Post-ictal Confusion (20 min)"],
        "serious": True,
        "life_threatening": True,
        "hospitalization": True
      },
      "reporter": {
        "name": "Dr. Richard Vance, MD",
        "institution": "Columbia University Medical Center, NY",
        "email": "rvance@cumc.columbia.edu"
      },
      "source_citations": {"all": "fda_medwatch_initial_neuroval.pdf:Page1"}
    },
    "DIG-05": {
      "type": "regulatory_form",
      "pdf_file": "pdfs/digital_forms/cioms_form_renal_injury.pdf",
      "categories": ["Safety Report (ICSR)"],
      "patient": {
        "initials": "George Taylor (G.T.)",
        "age": "67 YRS",
        "sex": "MALE",
        "weight": "76 kg"
      },
      "product": {
        "name": "Renotril",
        "dose": "30 mg PO QD",
        "lot": "RN-2025-412"
      },
      "reaction": {
        "terms": ["KDIGO Stage 3 Acute Kidney Injury", "Oliguria (<400 mL/day)", "Peripheral Edema", "Hyperkalemia (5.6 mEq/L)"],
        "serious": True,
        "hospitalization": True,
        "life_threatening": False
      },
      "labs": {
        "Baseline_Creatinine": "1.0 mg/dL",
        "Peak_Creatinine": "4.2 mg/dL",
        "BUN": "68 mg/dL",
        "Potassium": "5.6 mEq/L"
      },
      "reporter": {
        "name": "Dr. Keith Miller, MD (Nephrology)",
        "institution": "Vanderbilt University Medical Center, Nashville, TN",
        "email": "kmiller@vumc-nephrology.org"
      },
      "source_citations": {"all": "cioms_form_renal_injury.pdf:Page1"}
    },

    # ------------------ QUALITY COMPLAINT & MEDICAL INFO & IRRELEVANT PDFS ------------------
    "PQC-02": {
      "type": "quality_complaint_document",
      "pdf_file": "pdfs/quality_complaints/packaging_defect_report.pdf",
      "categories": ["Quality Complaint (PQC)"],
      "quality_complaint": {
        "product": "Cardioril 20mg Blister Packs (10x10)",
        "lot": "BL-8802",
        "expiry": "11/2027",
        "defect": "Breached blister foil seal, moisture ingress, oxidized crumbling discolored tablets"
      },
      "patient": None,
      "source_citations": {"all": "packaging_defect_report.pdf:Page1"}
    },
    "MED-01": {
      "type": "medical_info_document",
      "pdf_file": "pdfs/medical_info/cardioril_clinical_monograph_dosing.pdf",
      "categories": ["Medical Information (MI)"],
      "content_summary": "Clinical pharmacology reference monograph outlining Cardioril dosing recommendations stratified by renal function (Normal, Mild, CKD 3, CKD 4/5, ESRD hemodialysis) and dialysis clearance kinetics.",
      "patient": None,
      "adverse_event": None,
      "quality_defect": None,
      "source_citations": {"all": "cardioril_clinical_monograph_dosing.pdf:Page1"}
    },
    "MED-02": {
      "type": "medical_info_document",
      "pdf_file": "pdfs/medical_info/corzapan_drug_interaction_guide.pdf",
      "categories": ["Medical Information (MI)"],
      "content_summary": "Medical affairs formulation guide detailing Corzapan 10mg enteral tube crushing protocols across NG, G-tube, and J-tube administration, and CYP3A4/CYP2C9 pharmacokinetic interaction tables.",
      "patient": None,
      "adverse_event": None,
      "quality_defect": None,
      "source_citations": {"all": "corzapan_drug_interaction_guide.pdf:Page1"}
    },
    "IRR-01": {
      "type": "irrelevant_document",
      "pdf_file": "pdfs/irrelevant/pharmatech_conference_prospectus.pdf",
      "categories": ["Not Relevant"],
      "content_summary": "Commercial event sponsorship prospectus for PharmaTech Global AI Summit 2026. Contains sponsorship pricing tiers ($45k Diamond, $28k Platinum, $15k Gold) and booth layouts. Zero patient safety data.",
      "extracted_entities": {},
      "source_citations": {"all": "pharmatech_conference_prospectus.pdf:Page1"}
    }
  }
}

benchmark_path = os.path.join(GT_DIR, "benchmark.json")
with open(benchmark_path, "w", encoding="utf-8") as f:
    json.dump(benchmark_data, f, indent=2)
print(f"[OK] Generated Complete Benchmark Key: {benchmark_path} (Total cases documented: {len(benchmark_data['cases'])})")

# -------------------------------------------------------------
# 2. BUILD CLEAN SCOPED MANIFEST.JSON
# -------------------------------------------------------------
manifest_data = {
  "dataset_name": "Clinevo Smart Inbox Synthetic Pharmacovigilance Test Suite",
  "version": "2.0.0",
  "author": "Forward Deployment / GenAI Integration Engineering Candidate",
  "created_date": "2026-09-05",
  "compliance_notes": "100% Synthetic / Fictional data complying strictly with Section 3.E (No real patient data).",
  "statistics": {
    "email_statistics": {
      "total_emails": 11,
      "categories": {
        "Safety_Report_ICSR": 6,
        "Quality_Complaint_PQC": 2,
        "Medical_Information_MI": 2,
        "Not_Relevant": 1,
        "Multi_Label_ICSR_PQC": 1
      },
      "attachment_bearing_emails": 6,
      "pure_text_emails": 5
    },
    "document_statistics": {
      "total_documents": 20,
      "flavors": {
        "Digital_PDF": 5,
        "Scanned_Handwritten": 1,
        "Published_Article": 7,
        "Non_English": 2,
        "Quality_Complaint_PDF": 2,
        "Medical_Info_PDF": 2,
        "Irrelevant_PDF": 1
      },
      "documents_with_tables": 8,
      "documents_with_images": 2,
      "image_requiring_human_review_flag": 1,
      "languages": {
        "English_en": 17,
        "Spanish_es": 1,
        "German_de": 1
      }
    },
    "literature_statistics": {
      "total_articles": 7,
      "case_bearing_articles": 5,
      "non_reportable_negative_articles": 2,
      "total_extractable_patient_cases": 8,
      "multicase_series_articles": 2,
      "multipage_articles": 2
    },
    "deferred_requirements": {
      "second_scanned_handwritten_pdf": "DEFERRED — second scanned/handwritten PDF reserved for live user physical form"
    }
  },
  "inventory": [
    # Emails 01 to 11
    {"id": "CASE-01", "type": "email", "file": "emails/email_01.eml", "attachment": "pdfs/digital_forms/cioms_form_MK_Cardioril.pdf", "category": ["ICSR"], "flavor": "Digital_PDF", "language": "en", "ground_truth_id": "CASE-01"},
    {"id": "CASE-02", "type": "email", "file": "emails/email_02.eml", "attachment": "pdfs/scanned_handwritten/urgent_care_intake_handwritten.pdf", "category": ["ICSR"], "flavor": "Scanned_Handwritten", "language": "en", "ground_truth_id": "CASE-02"},
    {"id": "CASE-03", "type": "email", "file": "emails/email_03.eml", "attachment": None, "category": ["ICSR"], "flavor": "Pure_Text_Email", "language": "en", "ground_truth_id": "CASE-03"},
    {"id": "CASE-04", "type": "email", "file": "emails/email_04.eml", "attachment": "pdfs/quality_complaints/vial_contamination_sepsis.pdf", "category": ["ICSR", "PQC"], "flavor": "Digital_PDF", "language": "en", "ground_truth_id": "CASE-04"},
    {"id": "CASE-05", "type": "email", "file": "emails/email_05.eml", "attachment": "pdfs/non_english/notificacion_ram_madrid.pdf", "category": ["ICSR"], "flavor": "Non_English", "language": "es", "ground_truth_id": "CASE-05"},
    {"id": "CASE-06", "type": "email", "file": "emails/email_06.eml", "attachment": "pdfs/digital_forms/fda_medwatch_followup.pdf", "category": ["ICSR"], "flavor": "Digital_PDF", "language": "en", "ground_truth_id": "CASE-06"},
    {"id": "CASE-07", "type": "email", "file": "emails/email_07.eml", "attachment": "pdfs/quality_complaints/packaging_defect_report.pdf", "category": ["PQC"], "flavor": "Digital_PDF", "language": "en", "ground_truth_id": "CASE-07"},
    {"id": "CASE-08", "type": "email", "file": "emails/email_08.eml", "attachment": None, "category": ["PQC"], "flavor": "Pure_Text_Email", "language": "en", "ground_truth_id": "CASE-08"},
    {"id": "CASE-09", "type": "email", "file": "emails/email_09.eml", "attachment": None, "category": ["MI"], "flavor": "Pure_Text_Email", "language": "en", "ground_truth_id": "CASE-09"},
    {"id": "CASE-10", "type": "email", "file": "emails/email_10.eml", "attachment": None, "category": ["Not Relevant"], "flavor": "Pure_Text_Email", "language": "en", "ground_truth_id": "CASE-10"},
    {"id": "CASE-11", "type": "email", "file": "emails/email_11.eml", "attachment": None, "category": ["MI"], "flavor": "Pure_Text_Email", "language": "en", "ground_truth_id": "CASE-11"},

    # Literature Articles 01 to 07
    {"id": "LIT-01", "type": "literature", "file": "pdfs/literature_articles/article_01_dili_case.pdf", "category": ["ICSR"], "flavor": "Published_Article", "cases_count": 1, "pages": 1, "language": "en", "ground_truth_id": "LIT-01"},
    {"id": "LIT-02", "type": "literature", "file": "pdfs/literature_articles/article_02_sjs_case.pdf", "category": ["ICSR"], "flavor": "Published_Article", "cases_count": 1, "pages": 1, "language": "en", "ground_truth_id": "LIT-02"},
    {"id": "LIT-03", "type": "literature", "file": "pdfs/literature_articles/article_03_multicase_series.pdf", "category": ["ICSR"], "flavor": "Published_Article", "cases_count": 3, "pages": 1, "language": "en", "multicase_bonus": True, "ground_truth_id": "LIT-03"},
    {"id": "LIT-04", "type": "literature", "file": "pdfs/literature_articles/article_04_preclinical_review.pdf", "category": ["Not Relevant"], "flavor": "Published_Article", "cases_count": 0, "pages": 1, "language": "en", "reportable": False, "ground_truth_id": "LIT-04"},
    {"id": "LIT-05", "type": "literature", "file": "pdfs/literature_articles/article_05_meta_analysis_review.pdf", "category": ["Not Relevant"], "flavor": "Published_Article", "cases_count": 0, "pages": 1, "language": "en", "reportable": False, "ground_truth_id": "LIT-05"},
    {"id": "LIT-06", "type": "literature", "file": "pdfs/literature_articles/article_06_buried_case_study.pdf", "category": ["ICSR"], "flavor": "Published_Article", "cases_count": 1, "pages": 2, "language": "en", "ground_truth_id": "LIT-06"},
    {"id": "LIT-07", "type": "literature", "file": "pdfs/literature_articles/article_07_complex_screening_case.pdf", "category": ["ICSR"], "flavor": "Published_Article", "cases_count": 2, "pages": 2, "language": "en", "multicase_bonus": True, "ground_truth_id": "LIT-07"},

    # Non-English Documents
    {"id": "NON-ENG-01", "type": "document", "file": "pdfs/non_english/notificacion_ram_madrid.pdf", "category": ["ICSR"], "flavor": "Non_English", "language": "es", "ground_truth_id": "NON-ENG-01"},
    {"id": "NON-ENG-02", "type": "document", "file": "pdfs/non_english/bericht_uaw_charite_berlin.pdf", "category": ["ICSR"], "flavor": "Non_English", "language": "de", "ground_truth_id": "NON-ENG-02"},

    # Additional Digital Forms
    {"id": "DIG-03", "type": "document", "file": "pdfs/digital_forms/cioms_pediatric_oncology.pdf", "category": ["ICSR"], "flavor": "Digital_PDF", "language": "en", "ground_truth_id": "DIG-03"},
    {"id": "DIG-04", "type": "document", "file": "pdfs/digital_forms/fda_medwatch_initial_neuroval.pdf", "category": ["ICSR"], "flavor": "Digital_PDF", "language": "en", "ground_truth_id": "DIG-04"},
    {"id": "DIG-05", "type": "document", "file": "pdfs/digital_forms/cioms_form_renal_injury.pdf", "category": ["ICSR"], "flavor": "Digital_PDF", "language": "en", "ground_truth_id": "DIG-05"},

    # Quality Complaint Documents
    {"id": "PQC-01", "type": "document", "file": "pdfs/quality_complaints/vial_contamination_sepsis.pdf", "category": ["ICSR", "PQC"], "flavor": "Digital_PDF", "language": "en", "ground_truth_id": "CASE-04"},
    {"id": "PQC-02", "type": "document", "file": "pdfs/quality_complaints/packaging_defect_report.pdf", "category": ["PQC"], "flavor": "Digital_PDF", "language": "en", "ground_truth_id": "PQC-02"},

    # Medical Information Documents
    {"id": "MED-01", "type": "document", "file": "pdfs/medical_info/cardioril_clinical_monograph_dosing.pdf", "category": ["MI"], "flavor": "Medical_Info_PDF", "language": "en", "ground_truth_id": "MED-01"},
    {"id": "MED-02", "type": "document", "file": "pdfs/medical_info/corzapan_drug_interaction_guide.pdf", "category": ["MI"], "flavor": "Medical_Info_PDF", "language": "en", "ground_truth_id": "MED-02"},

    # Irrelevant Document
    {"id": "IRR-01", "type": "document", "file": "pdfs/irrelevant/pharmatech_conference_prospectus.pdf", "category": ["Not Relevant"], "flavor": "Irrelevant_PDF", "language": "en", "ground_truth_id": "IRR-01"}
  ]
}

manifest_path = os.path.join(BASE_DIR, "manifest.json")
with open(manifest_path, "w", encoding="utf-8") as f:
    json.dump(manifest_data, f, indent=2)
print(f"[OK] Generated Clean Scoped Manifest: {manifest_path} (Total inventory items: {len(manifest_data['inventory'])})")
