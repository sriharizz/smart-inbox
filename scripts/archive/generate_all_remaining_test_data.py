"""
Master Generator for All Remaining Test Data Assets:
1. 5 Published Medical Literature Articles (2-column layout, including multi-case series for +30% bonus & negative reviews)
2. 1 German Non-English Report (BfArM UAW standard from Charité Berlin)
3. 2 Medical Information PDFs (Product monographs & dosing guides)
4. 3 Additional Digital CIOMS/MedWatch Forms (reaching 5 total)
5. 1 Irrelevant Marketing Prospectus PDF
6. test-data/manifest.json (Complete dataset inventory)
7. test-data/ground_truth/benchmark.json (Machine-readable evaluation benchmark)
"""

import os
import json
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Frame, PageTemplate, BaseDocTemplate
)
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT

BASE_DIR = r"c:\projects\SmartInbox\test-data"
PDF_DIR = os.path.join(BASE_DIR, "pdfs")
DIGITAL_DIR = os.path.join(PDF_DIR, "digital_forms")
LIT_DIR = os.path.join(PDF_DIR, "literature_articles")
NON_ENG_DIR = os.path.join(PDF_DIR, "non_english")
MED_INFO_DIR = os.path.join(PDF_DIR, "medical_info")
IRR_DIR = os.path.join(PDF_DIR, "irrelevant")
GT_DIR = os.path.join(BASE_DIR, "ground_truth")

for d in [DIGITAL_DIR, LIT_DIR, NON_ENG_DIR, MED_INFO_DIR, IRR_DIR, GT_DIR]:
    os.makedirs(d, exist_ok=True)

# -------------------------------------------------------------
# HELPER: Two-Column Medical Journal Template (NEJM / Lancet style)
# -------------------------------------------------------------
def build_two_column_article(pdf_path, title, authors, journal, doi, abstract, col1_text, col2_text):
    doc = BaseDocTemplate(pdf_path, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    
    # 2 Frames for 2 columns
    frame_width = (letter[0] - 72 - 18) / 2 # 261 pt
    frame_height = letter[1] - 72 # 720 pt
    
    frame1 = Frame(36, 36, frame_width, frame_height, id='col1', leftPadding=0, rightPadding=6, topPadding=0, bottomPadding=0)
    frame2 = Frame(36 + frame_width + 18, 36, frame_width, frame_height, id='col2', leftPadding=6, rightPadding=0, topPadding=0, bottomPadding=0)
    
    template = PageTemplate(id='two_col', frames=[frame1, frame2])
    doc.addPageTemplates([template])
    
    j_hdr = ParagraphStyle('JHdr', fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=colors.HexColor('#1E3A8A'))
    doi_st = ParagraphStyle('Doi', fontName='Helvetica', fontSize=7, leading=9, textColor=colors.HexColor('#64748B'))
    art_title = ParagraphStyle('ArtTitle', fontName='Helvetica-Bold', fontSize=12, leading=15, textColor=colors.black)
    art_auth = ParagraphStyle('ArtAuth', fontName='Helvetica', fontSize=8, leading=10, textColor=colors.HexColor('#334155'))
    abs_hdr = ParagraphStyle('AbsHdr', fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=colors.black)
    abs_body = ParagraphStyle('AbsBody', fontName='Times-Italic', fontSize=7.5, leading=10, alignment=TA_JUSTIFY, textColor=colors.HexColor('#1E293B'))
    sec_hdr = ParagraphStyle('SecHdr', fontName='Helvetica-Bold', fontSize=8.5, leading=11, textColor=colors.HexColor('#0F172A'))
    p_body = ParagraphStyle('PBody', fontName='Times-Roman', fontSize=7.5, leading=9.5, alignment=TA_JUSTIFY, textColor=colors.black)
    
    story = [
        Paragraph(journal.upper(), j_hdr),
        Paragraph(f"DOI: {doi} &nbsp;|&nbsp; Published Online: 12-Nov-2025 &nbsp;|&nbsp; Clinical Case Report", doi_st),
        Spacer(1, 4),
        Paragraph(title, art_title),
        Spacer(1, 2),
        Paragraph(authors, art_auth),
        Spacer(1, 6),
        Paragraph("<b>ABSTRACT</b>", abs_hdr),
        Paragraph(abstract, abs_body),
        Spacer(1, 6),
    ]
    
    for block in col1_text:
        if block.startswith("###"):
            story.append(Spacer(1, 4))
            story.append(Paragraph(f"<b>{block.replace('###', '').strip()}</b>", sec_hdr))
            story.append(Spacer(1, 2))
        else:
            story.append(Paragraph(block, p_body))
            story.append(Spacer(1, 3))
            
    # Force jump to Column 2
    story.append(FrameBreak())
    
    for block in col2_text:
        if block.startswith("###"):
            story.append(Spacer(1, 4))
            story.append(Paragraph(f"<b>{block.replace('###', '').strip()}</b>", sec_hdr))
            story.append(Spacer(1, 2))
        else:
            story.append(Paragraph(block, p_body))
            story.append(Spacer(1, 3))
            
    doc.build(story)
    print(f"[OK] Generated Article PDF: {pdf_path}")

from reportlab.platypus import FrameBreak

# -------------------------------------------------------------
# 1. GENERATE THE 5 LITERATURE ARTICLES
# -------------------------------------------------------------
def generate_literature_articles():
    # Article 1: Single Case (DILI)
    p1 = os.path.join(LIT_DIR, "article_01_dili_case.pdf")
    build_two_column_article(
        pdf_path=p1,
        title="Severe Drug-Induced Autoimmune Hepatitis Triggered by Cardioril Therapy",
        authors="Gregory House, MD, PhD; Lisa Cuddy, MD; James Wilson, MD<br/>Department of Medicine, Princeton-Plainsboro Teaching Hospital, NJ",
        journal="Journal of Clinical Hepatology & Pharmacovigilance | Vol 42, No 4",
        doi="10.1016/j.jchpv.2025.04.012",
        abstract="We report an idiosyncratic case of severe acute drug-induced autoimmune-like hepatitis in a 61-year-old male following 6 weeks of Cardioril (cardioril hydrochloride 40mg daily) administration. Marked hyperbilirubinemia, antinuclear antibody (ANA) seroconversion (titer 1:640), and liver biopsy showing interface hepatitis were documented. Immediate drug withdrawal resulted in clinical and biochemical resolution.",
        col1_text=[
            "### INTRODUCTION",
            "Idiosyncratic drug-induced liver injury (DILI) represents a formidable challenge in clinical pharmacology. Cardioril is a novel third-generation antihypertensive agent targeting vascular smooth muscle receptors. While clinical trials reported mild transient aminotransferase elevations in <1.2% of participants, post-marketing surveillance is critical for identifying severe immune-mediated reactions.",
            "### CASE PRESENTATION",
            "A 61-year-old Caucasian male with a 10-year history of refractory hypertension and hyperlipidemia was initiated on Cardioril 40 mg PO QD. Baseline hepatic function panel was completely normal (ALT 22 U/L, AST 19 U/L, Total Bilirubin 0.6 mg/dL). Forty-two days following treatment initiation, the patient presented with progressive fatigue, nausea, dark urine, and jaundice.",
            "Physical examination revealed marked scleral icterus and right upper quadrant tenderness without hepatosplenomegaly or ascites. Laboratory evaluation demonstrated ALT 680 U/L (>12x ULN), AST 510 U/L (>12x ULN), Total Bilirubin 6.2 mg/dL, and Alkaline Phosphatase 240 U/L.",
        ],
        col2_text=[
            "### INVESTIGATIONS & CLINICAL COURSE",
            "Viral serologies for hepatitis A, B, C, and E, cytomegalovirus, and Epstein-Barr virus were non-reactive. Autoimmune serology revealed positive antinuclear antibodies (ANA 1:640, speckled pattern) and elevated IgG levels (2,100 mg/dL). A percutaneous liver biopsy demonstrated severe interface hepatitis with dense portal lymphoplasmacytic infiltrate and bridging necrosis, consistent with drug-induced autoimmune hepatitis.",
            "Cardioril was discontinued on admission. A 4-week tapering course of oral prednisone (40 mg/day initial) was administered. Over the subsequent 6 weeks, serum transaminases and bilirubin normalized completely (ALT 28 U/L, Total Bili 0.8 mg/dL). Re-challenge was not attempted due to severity.",
            "### DISCUSSION & CONCLUSION",
            "This report highlights a probable causal relationship between Cardioril exposure and drug-induced autoimmune hepatitis (Roussel Uclaf Causality Assessment Method score = 8, probable). Healthcare practitioners should maintain vigilant liver function monitoring during the first 3 months of Cardioril initiation.",
            "### REFERENCES",
            "1. Chalasani N, et al. Practice Parameters: Evaluation of Drug-Induced Liver Injury. Am J Gastroenterol. 2021;116(5):878-898.<br/>2. Fontana RJ. Pathogenesis of idiosyncratic drug-induced liver injury. Gastroenterology. 2022;162(5):1370-1388."
        ]
    )
    
    # Article 2: Single Case (SJS)
    p2 = os.path.join(LIT_DIR, "article_02_sjs_case.pdf")
    build_two_column_article(
        pdf_path=p2,
        title="Stevens-Johnson Syndrome Associated with Neuroval Administration in a Young Adult",
        authors="Sanjay Gupta, MD; Priya Sharma, MD<br/>Department of Dermatology, Johns Hopkins Bayview Medical Center, Baltimore, MD",
        journal="British Journal of Clinical Dermatology | Case Reports",
        doi="10.1111/bjcd.2025.10921",
        abstract="Stevens-Johnson syndrome (SJS) is a rare, life-threatening mucocutaneous reaction characterized by epidermal necrosis and extensive mucosal detachment. We describe a definitive case in a 24-year-old female presenting 18 days after initiating Neuroval (neuroval HCl 150mg daily) for trigeminal neuralgia. The patient achieved full recovery following drug cessation and intravenous immunoglobulin therapy.",
        col1_text=[
            "### INTRODUCTION",
            "Neuroval is an emerging neuroactive medication utilized for neuropathic pain syndromes and treatment-resistant focal seizures. Serious adverse cutaneous drug reactions (SCAR) represent rare but devastating immunological complications. Rapid identification and withdrawal of the causative agent remain paramount to patient survival.",
            "### CASE PRESENTATION",
            "A 24-year-old female with newly diagnosed idiopathic trigeminal neuralgia commenced Neuroval at 150 mg daily. Eighteen days later, she presented to the emergency department with high fevers (39.5°C), burning sensation in both eyes, photophobia, and an excruciating painful rash across the face and upper chest.",
            "On examination, widespread purpuric macules with atypical targetoid morphology were noted across the face, neck, and trunk. Extensive epidermal detachment involved approximately 8% of total body surface area (BSA). Severe mucosal involvement was evident with hemorrhagic crusting of the lips and bilateral purulent conjunctivitis.",
        ],
        col2_text=[
            "### CLINICAL MANAGEMENT & OUTCOME",
            "The patient was admitted to the intensive care burn unit. Neuroval was immediately withdrawn. High-dose intravenous immunoglobulin (IVIG, 1 g/kg/day for 3 days) and intensive ocular lubrication with topical corticosteroids were initiated.",
            "Re-epithelialization commenced on hospital day 6 and was complete by day 21 without permanent visual sequelae. ALDEN (Algorithm of Drug Causality in Epidermal Necrolysis) score was calculated at 6, indicating Neuroval as the 'very probable' culprit agent.",
            "### CONCLUSION",
            "Prescribers must educate patients initiating Neuroval to immediately cease medication and seek urgent care upon the development of fever, mucosal burning, or cutaneous erythema.",
            "### REFERENCES",
            "1. Mockenhaupt M. The current understanding of Stevens-Johnson syndrome and toxic epidermal necrolysis. Expert Rev Clin Immunol. 2021;7(6):803-815."
        ]
    )

    # Article 3 (CRUCIAL FOR +30% BONUS): Multi-Case Clinical Report (3 Distinct Patients)
    p3 = os.path.join(LIT_DIR, "article_03_multicase_series.pdf")
    build_two_column_article(
        pdf_path=p3,
        title="Cutaneous Adverse Reactions Associated with Novel Antihypertensives: A Clinical Series of Three Cases",
        authors="Marcus Sterling, MD, FRCP; Arthur Pendelton, MBChB; Eleanor Vance, MD<br/>Royal Free Hospital, London, United Kingdom & Guy's and St Thomas' NHS Foundation Trust",
        journal="The Lancet Regional Health — Europe | Clinical Case Series",
        doi="10.1016/j.lanepe.2025.100984",
        abstract="We document three distinct individual cases of severe cutaneous drug reactions occurring secondary to novel antihypertensive therapies across two university medical centers. Case 1 describes a 45-year-old male with severe Erythema Multiforme Major. Case 2 describes a 62-year-old female presenting with subacute cutaneous lupus erythematosus. Case 3 documents a 38-year-old female with acute urticaria and periorbital angioedema. All cases responded favorably to prompt drug cessation.",
        col1_text=[
            "### INTRODUCTION",
            "The expansion of novel antihypertensive pharmacotherapies has coincided with sporadic reports of delayed-type hypersensitivity reactions. We present three well-characterized independent patient cases identified during a 6-month surveillance period.",
            "### PATIENT CASE 1",
            "A 45-year-old male (Patient A.J., weight 81 kg) with stage II hypertension was prescribed Cardioril 20 mg once daily. On day 22 of therapy, he presented with extensive symmetrical target lesions with central blistering on the dorsal hands, forearms, and lower extremities, accompanied by severe oral mucosal erosions. Diagnosis: Erythema Multiforme Major. Histopathology confirmed apoptotic keratinocytes with vacuolar basal interface dermatitis. Cardioril was discontinued, and systemic methylprednisolone was initiated. Complete resolution was achieved within 16 days.",
            "### PATIENT CASE 2",
            "A 62-year-old female (Patient B.L., weight 64 kg) commenced Corzapan 10 mg daily for essential hypertension. After 8 weeks of therapy, she developed widespread annular, polycyclic scaly erythematous plaques distributed across sun-exposed areas of the upper back and shoulders. Serology revealed high-titer anti-Ro/SSA antibodies (>240 U/mL) and ANA 1:320. Diagnosis: Drug-induced subacute cutaneous lupus erythematosus (SCLE). Corzapan was discontinued. Lesions resolved over 8 weeks with topical tacrolimus.",
        ],
        col2_text=[
            "### PATIENT CASE 3",
            "A 38-year-old female (Patient C.M., weight 59 kg) with mild hypertension was initiated on Cardioril 10 mg daily. Approximately 90 minutes following her initial dose, she developed acute generalized urticaria with severe pruritus, dysphonia, and marked bilateral periorbital angioedema. Emergency management with intramuscular epinephrine 0.3 mg and intravenous diphenhydramine 50 mg aborted progression to respiratory compromise. Cardioril was permanently avoided.",
            "### PHARMACOVIGILANCE DISCUSSION",
            "These three cases underscore the clinical necessity for distinct Individual Case Safety Report (ICSR) submission for each patient, despite publication within a unified clinical series. Each case features unique demographic profiles, differing onset latencies (ranging from 90 minutes to 8 weeks), distinct MedDRA clinical reaction phenotypes, and independent de-challenge timelines.",
            "Safety reporting departments must ensure that multicase journal articles are disaggregated into separate regulatory cases to prevent signal dilution.",
            "### REFERENCES",
            "1. Roujeau JC. Immune mechanisms in drug eruptions. Clin Dermatol. 2020;38(6):679-688.<br/>2. EMA Guideline on Good Pharmacovigilance Practices (GVP) Module VI — Collection, verification and presentation of adverse reactions.",
        ]
    )

    # Article 4: Preclinical In-Vitro/Rat Study (NON-REPORTABLE - NO HUMAN PATIENTS)
    p4 = os.path.join(LIT_DIR, "article_04_preclinical_review.pdf")
    build_two_column_article(
        pdf_path=p4,
        title="Preclinical In-Vitro Metabolic Clearance and Hepatic Cytochrome P450 Interactions of Cardioril",
        authors="Heinrich Mueller, PhD; Klaus Schmidt, PhD<br/>Institute of Molecular Pharmacology, Technical University of Munich, Germany",
        journal="European Journal of Pharmaceutical Sciences | Preclinical Research",
        doi="10.1016/j.ejps.2025.105412",
        abstract="The hepatic metabolic pathway of Cardioril was investigated in human liver microsomes (HLM) and Sprague-Dawley rat hepatocytes. Cardioril undergoes extensive oxidative metabolism predominantly mediated by CYP3A4 and CYP2C9 enzymes. In-vitro inhibition assays demonstrated an IC50 > 50 µM for CYP2D6 and CYP1A2, indicating low potential for metabolic drug-drug interactions in animal models.",
        col1_text=[
            "### INTRODUCTION",
            "Assessment of metabolic clearance and cytochrome P450 (CYP) inhibition kinetics is fundamental during early drug characterization. In the present investigation, we delineate the metabolic fate of Cardioril using cryopreserved human and rodent hepatocytes. This study contains no human clinical trials or individual patient case reports.",
            "### METHODS & EXPERIMENTAL PROCEDURES",
            "In-vitro incubation of Cardioril (1–100 µM) was performed using pooled human liver microsomes (Corning Gentest) in the presence of NADPH-generating systems. Metabolite profiling was conducted via high-performance liquid chromatography coupled with tandem mass spectrometry (LC-MS/MS). Rat hepatocyte viability was monitored via trypan blue exclusion.",
        ],
        col2_text=[
            "### RESULTS & DISCUSSION",
            "Cardioril demonstrated rapid hepatic extraction with an intrinsic clearance (CLint) of 42.5 µL/min/mg protein in rat microsomes. No direct cytotoxic effects were observed in rodent hepatocytes up to 100 µM concentrations over 24-hour continuous exposure.",
            "### PHARMACOVIGILANCE ASSESSMENT",
            "As this paper represents exclusively non-clinical in-vitro and animal laboratory research without identifiable human subjects, it does not meet regulatory criteria for ICSR submission under GVP Module VI Section VI.B.1. It is categorized as non-reportable literature.",
            "### REFERENCES",
            "1. Houston JB. Utility of in vitro drug metabolism data in predicting in vivo metabolic clearance. Biochem Pharmacol. 2019;47:1469-1479."
        ]
    )

    # Article 5: Epidemiological Review Article (NON-REPORTABLE - NO INDIVIDUAL CASES)
    p5 = os.path.join(LIT_DIR, "article_05_meta_analysis_review.pdf")
    build_two_column_article(
        pdf_path=p5,
        title="Contemporary Pharmacotherapy for Resistant Hypertension: A Systematic Literature Review and Meta-Analysis",
        authors="Catherine Tremblay, MD; Jean-Luc Moreau, MD<br/>Department of Cardiology, Montreal Heart Institute & McGill University, Canada",
        journal="International Journal of Cardiology Reviews | Systematic Review",
        doi="10.1016/j.ijcard.2025.110294",
        abstract="Resistant hypertension affects an estimated 10-15% of treated hypertensive populations globally. We systematically reviewed 34 randomized clinical trials comprising 28,450 total participants to evaluate the comparative blood pressure lowering efficacy and aggregate class adverse event rates of third-generation vasodilators. No new individual clinical safety cases are reported.",
        col1_text=[
            "### INTRODUCTION & OBJECTIVES",
            "Resistant hypertension remains an independent risk factor for adverse cardiovascular events, heart failure, and renal disease progression. Multiple pharmaceutical classes, including mineralocorticoid receptor antagonists and novel smooth muscle relaxants, have emerged. This review synthesizes aggregate population-level evidence.",
            "### METHODOLOGY",
            "Systematic electronic searches of MEDLINE, Embase, and the Cochrane Central Register of Controlled Trials were executed from January 2015 to October 2025. Studies reporting aggregate clinical outcomes were pooled using random-effects meta-analytic models.",
        ],
        col2_text=[
            "### SUMMARY OF FINDINGS",
            "Overall pooled analysis demonstrated a weighted mean reduction in systolic blood pressure of 8.4 mmHg (95% CI: 6.2–10.6). Across all pooled cohorts, aggregate adverse event frequencies for dizziness, headache, and peripheral edema were comparable to placebo controls. No individual patient-level identifiers or novel safety signals were identified in the literature sample.",
            "### REGULATORY TRIAGE NOTE",
            "Systematic reviews and aggregate meta-analyses devoid of individual identifiable patient case reports do not constitute ICSR-reportable sources under global pharmacovigilance regulations.",
            "### REFERENCES",
            "1. Carey RM, et al. Resistant Hypertension: Detection, Evaluation, and Management. Hypertension. 2020;72:e53-e90."
        ]
    )

# -------------------------------------------------------------
# 2. GENERATE GERMAN NON-ENGLISH PDF: BfArM UAW Form
# -------------------------------------------------------------
def generate_german_pdf():
    pdf_path = os.path.join(NON_ENG_DIR, "bericht_uaw_charite_berlin.pdf")
    doc = SimpleDocTemplate(pdf_path, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    
    title_st = ParagraphStyle('DeTitle', fontName='Helvetica-Bold', fontSize=10.5, leading=13, alignment=TA_CENTER)
    sub_st = ParagraphStyle('DeSub', fontName='Helvetica', fontSize=7.5, leading=9.5, alignment=TA_CENTER)
    sec_st = ParagraphStyle('DeSec', fontName='Helvetica-Bold', fontSize=8, leading=10)
    val_st = ParagraphStyle('DeVal', fontName='Helvetica', fontSize=7.5, leading=9.5)
    
    story = [
        Paragraph("BUNDESINSTITUT FÜR ARZNEIMITTEL UND MEDIZINPRODUKTE (BfArM)", sub_st),
        Paragraph("ARZNEIMITTELKOMMISSION DER DEUTSCHEN ÄRZTESCHAFT (AkdÄ)", sub_st),
        Paragraph("<b>BERICHT ÜBER UNERWÜNSCHTE ARZNEIMITTELWIRKUNGEN (UAW-BOGEN)</b>", title_st),
        Paragraph("Offizieller Meldebogen gemäß § 63b Arzneimittelgesetz (AMG) — Spontanerregung", sub_st),
        Spacer(1, 4),
        Paragraph("<b>1. PATIENTENDATEN</b>", sec_st)
    ]
    
    row1 = [
        Paragraph("<b>INITIALEN:</b> H.S. (Hans Schneider)", val_st),
        Paragraph("<b>GEBURTSDATUM:</b> 04.08.1962", val_st),
        Paragraph("<b>ALTER:</b> 63 JAHRE", val_st),
        Paragraph("<b>GESCHLECHT:</b> MÄNNLICH", val_st),
        Paragraph("<b>GEWICHT:</b> 88 kg", val_st),
    ]
    t1 = Table([row1], colWidths=[150, 100, 90, 90, 110], style=[
        ('GRID', (0,0), (-1,-1), 0.75, colors.black),
        ('TOPPADDING', (0,0), (-1,-1), 3), ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 4), ('RIGHTPADDING', (0,0), (-1,-1), 4)
    ])
    story.append(t1)
    story.append(Spacer(1, 4))
    
    # Section 2: UAW Beschreibung
    story.append(Paragraph("<b>2. BESCHREIBUNG DER UNERWÜNSCHTEN WIRKUNG (DIAGNOSE & VERLAUF)</b>", sec_st))
    b_text = (
        "<b>KLINISCHE BESCHREIBUNG:</b> 63-jähriger Patient mit arterieller Hypertonie und chronischer KHK. "
        "Initiale Gabe von Cardioril 20 mg oral morgens. Am 15. Tag der Therapie entwickelte der Patient akutes Angioödem "
        "mit starker Schwellung von Lippen, Zunge und Pharynx, begleitet von ausgeprägter Dyspnoe, inspiratorischem Stridor "
        "und diffusem Urtikaria-Exanthem am Rumpf. Notfallmäßige Einweisung durch Notarzt in die Notaufnahme der Charité.<br/>"
        "<b>BEHANDLUNG:</b> Intravenöse Gabe von 250 mg Prednisolon, 8 mg Dimetinden, Inhalation mit Adrenalin. "
        "Stationäre Aufnahme auf die Internistische Intensivstation zur 48-stündigen Überwachung der Atemwege.<br/>"
        "<b>SCHWEREGRAD DER REAKTION:</b><br/>"
        "[ X ] Lebensbedrohlich: JA &nbsp;&nbsp;&nbsp;&nbsp; [ X ] Krankenhausaufenthalt erforderlich / verlängert: JA (Intensivstation)<br/>"
        "[ &nbsp; ] Tod: NEIN &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; [ &nbsp; ] Bleibende Behinderung: NEIN<br/>"
        "<b>BEGINN DER UAW:</b> 12.11.2025 &nbsp;|&nbsp; <b>AUSGANG:</b> Wiederhergestellt / Abgeklungen nach Absetzen (Positive Dechallenge)."
    )
    t_b = Table([[Paragraph(b_text, val_st)]], colWidths=[540], style=[
        ('GRID', (0,0), (-1,-1), 0.75, colors.black),
        ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 4), ('RIGHTPADDING', (0,0), (-1,-1), 4)
    ])
    story.append(t_b)
    story.append(Spacer(1, 4))
    
    # Section 3: Verdächtiges Arzneimittel
    story.append(Paragraph("<b>3. VERDÄCHTIGES ARZNEIMITTEL</b>", sec_st))
    c_data = [
        [
            Paragraph("<b>HANDELSNAME / WIRKSTOFF:</b> Cardioril (Cardioril-HCl) 20 mg", val_st),
            Paragraph("<b>DOSIERUNG:</b> 20 mg 1x täglich p.o.", val_st),
            Paragraph("<b>INDIKATION:</b> Essenzielle Hypertonie", val_st),
        ],
        [
            Paragraph("<b>DAUER DER BEHANDLUNG:</b> 28.10.2025 bis 12.11.2025", val_st),
            Paragraph("<b>CHARGEN-NUMMER:</b> Ch.-B.: CR-2025-0814 (Verf. 09/2027)", val_st),
            Paragraph("<b>MASSNAHME:</b> [ X ] Arzneimittel dauerhaft abgesetzt", val_st),
        ]
    ]
    t_c = Table(c_data, colWidths=[200, 170, 170], style=[
        ('GRID', (0,0), (-1,-1), 0.75, colors.black),
        ('TOPPADDING', (0,0), (-1,-1), 3), ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 4), ('RIGHTPADDING', (0,0), (-1,-1), 4)
    ])
    story.append(t_c)
    story.append(Spacer(1, 4))
    
    # Section 4: Meldender Arzt
    story.append(Paragraph("<b>4. ANGABEN ZUR MELDENDEN PERSON</b>", sec_st))
    d_text = (
        "<b>NAME DES ARZTES:</b> Dr. med. Wolfgang Becker (Facharzt für Kardiologie & Notfallmedizin)<br/>"
        "<b>KLINIK:</b> Charité – Universitätsmedizin Berlin, Campus Virchow-Klinikum, Medizinische Klinik für Kardiologie<br/>"
        "Augustenburger Platz 1, 13353 Berlin, Deutschland | Tel: +49 30 555-0821 | Email: w.becker@charite.de"
    )
    t_d = Table([[Paragraph(d_text, val_st)]], colWidths=[540], style=[
        ('GRID', (0,0), (-1,-1), 0.75, colors.black),
        ('TOPPADDING', (0,0), (-1,-1), 3), ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 4), ('RIGHTPADDING', (0,0), (-1,-1), 4)
    ])
    story.append(t_d)
    
    doc.build(story)
    print(f"[OK] Generated German Non-English PDF: {pdf_path}")

# -------------------------------------------------------------
# 3. GENERATE THE 2 MEDICAL INFORMATION (MI) PDFs
# -------------------------------------------------------------
def generate_medical_info_pdfs():
    # MI PDF 1: Clinical Dosing Monograph
    p1 = os.path.join(MED_INFO_DIR, "cardioril_clinical_monograph_dosing.pdf")
    doc1 = SimpleDocTemplate(p1, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    st = getSampleStyleSheet()
    title = ParagraphStyle('MITitle', fontName='Helvetica-Bold', fontSize=11, leading=14, alignment=TA_CENTER)
    sec = ParagraphStyle('MISec', fontName='Helvetica-Bold', fontSize=8.5, leading=11)
    val = ParagraphStyle('MIVal', fontName='Helvetica', fontSize=7.5, leading=9.5)
    
    story1 = [
        Paragraph("CLINICAL PHARMACOLOGY & MEDICAL INFORMATION REFERENCE MONOGRAPH", ParagraphStyle('Sub', fontName='Helvetica', fontSize=8, leading=10, alignment=TA_CENTER)),
        Paragraph("<b>CARDIORIL (cardioril hydrochloride) TABLETS — DOSING IN RENAL IMPAIRMENT</b>", title),
        Paragraph("Document Ref: MEDINFO-CARD-2025-019 &nbsp;|&nbsp; Target: Healthcare Professional Inquiries Only", ParagraphStyle('DRef', fontName='Helvetica', fontSize=7, leading=9, alignment=TA_CENTER)),
        Spacer(1, 6),
        Paragraph("<b>1. CLINICAL DOSING RECOMMENDATIONS BY RENAL FUNCTION</b>", sec),
        Spacer(1, 2)
    ]
    
    dosing_rows = [
        [Paragraph("<b>Renal Function Category</b>", sec), Paragraph("<b>eGFR (mL/min/1.73m²)</b>", sec), Paragraph("<b>Initial Dose</b>", sec), Paragraph("<b>Maximum Recommended Dose</b>", sec)],
        [Paragraph("Normal Renal Function", val), Paragraph("≥ 90", val), Paragraph("20 mg once daily", val), Paragraph("40 mg once daily", val)],
        [Paragraph("Mild Renal Impairment", val), Paragraph("60 – 89", val), Paragraph("20 mg once daily", val), Paragraph("40 mg once daily", val)],
        [Paragraph("Moderate Impairment (CKD 3)", val), Paragraph("30 – 59", val), Paragraph("10 mg once daily", val), Paragraph("20 mg once daily", val)],
        [Paragraph("Severe Impairment (CKD 4/5)", val), Paragraph("< 30 (non-dialysis)", val), Paragraph("5 mg once daily", val), Paragraph("10 mg once daily (titrate slowly)", val)],
        [Paragraph("End-Stage Renal Disease (ESRD)", val), Paragraph("Hemodialysis dependent", val), Paragraph("Contraindicated", val), Paragraph("Not Recommended", val)],
    ]
    t_dosing = Table(dosing_rows, colWidths=[160, 110, 130, 140], style=[
        ('GRID', (0,0), (-1,-1), 0.75, colors.black),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F1F5F9')),
        ('TOPPADDING', (0,0), (-1,-1), 3), ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 4), ('RIGHTPADDING', (0,0), (-1,-1), 4)
    ])
    story1.append(t_dosing)
    story1.append(Spacer(1, 6))
    story1.append(Paragraph("<b>2. PHARMACOKINETICS & DIALYSIS CLEARANCE</b>", sec))
    pk_text = (
        "Cardioril is 78% protein-bound. Renal clearance accounts for 42% of systemic drug elimination, with 58% cleared via fecal/biliary "
        "pathways. Due to high volume of distribution (Vd = 180 L), Cardioril is not significantly cleared by conventional 4-hour high-flux "
        "hemodialysis. Supplementary dosing post-dialysis is not required. Routine serum potassium monitoring is recommended in patients "
        "with baseline eGFR < 45 mL/min.<br/><br/>"
        "<i>Regulatory Notice: This medical information document contains zero patient-specific clinical data, zero adverse drug reactions, "
        "and zero product quality complaints. It is classified exclusively under Medical Information (MI).</i>"
    )
    story1.append(Table([[Paragraph(pk_text, val)]], colWidths=[540], style=[
        ('GRID', (0,0), (-1,-1), 0.75, colors.black),
        ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 4), ('RIGHTPADDING', (0,0), (-1,-1), 4)
    ]))
    doc1.build(story1)
    print(f"[OK] Generated Medical Info PDF 1: {p1}")

    # MI PDF 2: Drug Interaction & Enteral Tube Guide
    p2 = os.path.join(MED_INFO_DIR, "corzapan_drug_interaction_guide.pdf")
    doc2 = SimpleDocTemplate(p2, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    story2 = [
        Paragraph("MEDICAL INFORMATION MONOGRAPH — FORMULATION COMPATIBILITY", ParagraphStyle('Sub2', fontName='Helvetica', fontSize=8, leading=10, alignment=TA_CENTER)),
        Paragraph("<b>CORZAPAN (corzapan sodium) 10mg — ENTERAL TUBE STABILITY & CYP INTERACTIONS</b>", title),
        Paragraph("Document Ref: MEDINFO-CORZ-2025-084 &nbsp;|&nbsp; Professional Inquiry Service", ParagraphStyle('DRef2', fontName='Helvetica', fontSize=7, leading=9, alignment=TA_CENTER)),
        Spacer(1, 6),
        Paragraph("<b>1. TUBE CRUSHING & SUSPENSION STABILITY GUIDELINES</b>", sec),
        Spacer(1, 2)
    ]
    interact_rows = [
        [Paragraph("<b>Enteral Tube Type</b>", sec), Paragraph("<b>Compatibility</b>", sec), Paragraph("<b>Flush Volume</b>", sec), Paragraph("<b>Occlusion Risk</b>", sec)],
        [Paragraph("Polyurethane Nasogastric (NG)", val), Paragraph("Compatible (crush & disperse in 20mL sterile water)", val), Paragraph("20 mL sterile water flush", val), Paragraph("Low (< 0.5%)", val)],
        [Paragraph("Silicone Gastrostomy (G-tube)", val), Paragraph("Compatible (French size ≥ 14Fr)", val), Paragraph("30 mL sterile water flush", val), Paragraph("Minimal", val)],
        [Paragraph("Jejunostomy (J-tube)", val), Paragraph("Not Recommended (site of absorption bypass)", val), Paragraph("N/A", val), Paragraph("Moderate", val)],
    ]
    t_interact = Table(interact_rows, colWidths=[150, 170, 110, 110], style=[
        ('GRID', (0,0), (-1,-1), 0.75, colors.black),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F1F5F9')),
        ('TOPPADDING', (0,0), (-1,-1), 3), ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 4), ('RIGHTPADDING', (0,0), (-1,-1), 4)
    ])
    story2.append(t_interact)
    story2.append(Spacer(1, 6))
    story2.append(Paragraph("<b>2. CYP3A4 & CYP2C9 DRUG-DRUG INTERACTION SUMMARY</b>", sec))
    ddi_text = (
        "Co-administration of Corzapan with potent CYP3A4 inhibitors (e.g. ketoconazole, clarithromycin) results in a 1.8-fold increase "
        "in Corzapan AUC0-inf. Dose reduction to 5 mg once daily is recommended. Strong CYP3A4 inducers (e.g. rifampin, carbamazepine) decrease "
        "systemic exposure by 45%. Therapeutic drug monitoring is advised during concurrent antiepileptic therapy.<br/><br/>"
        "<i>Regulatory Note: Clinical pharmacology guidance inquiry. Zero patient exposure, zero adverse events reported. Category: Medical Information.</i>"
    )
    story2.append(Table([[Paragraph(ddi_text, val)]], colWidths=[540], style=[
        ('GRID', (0,0), (-1,-1), 0.75, colors.black),
        ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 4), ('RIGHTPADDING', (0,0), (-1,-1), 4)
    ]))
    doc2.build(story2)
    print(f"[OK] Generated Medical Info PDF 2: {p2}")

# -------------------------------------------------------------
# 4. GENERATE THE 3 ADDITIONAL DIGITAL FORMS (Reaching >= 5 total)
# -------------------------------------------------------------
def generate_additional_digital_forms():
    # Digital Form 3: CIOMS Pediatric Oncology Report
    p3 = os.path.join(DIGITAL_DIR, "cioms_pediatric_oncology.pdf")
    doc3 = SimpleDocTemplate(p3, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    val_st = ParagraphStyle('DVal', fontName='Helvetica', fontSize=7.5, leading=9.5)
    sec_st = ParagraphStyle('DSec', fontName='Helvetica-Bold', fontSize=8, leading=10)
    
    story3 = [
        Paragraph("CIOMS FORM I — PEDIATRIC SPECIAL POPULATION SAFETY REPORT", ParagraphStyle('PHdr', fontName='Helvetica-Bold', fontSize=10, leading=12, alignment=TA_CENTER)),
        Paragraph("Council for International Organizations of Medical Sciences &nbsp;|&nbsp; Case Ref: CIOMS-PEDS-2025-081", ParagraphStyle('PSub', fontName='Helvetica', fontSize=7.5, leading=9.5, alignment=TA_CENTER)),
        Spacer(1, 4),
        Paragraph("<b>I. REACTION INFORMATION (PEDIATRIC PATIENT)</b>", sec_st)
    ]
    p_row = [
        Paragraph("<b>1. INITIALS:</b> L.T. (Lucas Torres)", val_st),
        Paragraph("<b>2. AGE:</b> 8 YRS", val_st),
        Paragraph("<b>2a. DOB:</b> 14-JUL-2017", val_st),
        Paragraph("<b>3. SEX:</b> MALE", val_st),
        Paragraph("<b>4. WEIGHT:</b> 26 kg", val_st),
    ]
    story3.append(Table([p_row], colWidths=[150, 90, 100, 80, 120], style=[
        ('GRID', (0,0), (-1,-1), 0.75, colors.black),
        ('TOPPADDING', (0,0), (-1,-1), 3), ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 4), ('RIGHTPADDING', (0,0), (-1,-1), 4)
    ]))
    story3.append(Spacer(1, 4))
    
    react_text = (
        "<b>DESCRIBE REACTION(S):</b> 8-year-old male with acute lymphoblastic leukemia (ALL) in maintenance phase received intravenous "
        "infusion of OncoShield 50mg/m² (Lot #OS-2025-771). Within 30 minutes, developed severe shaking rigors, high-grade fever (40.1°C / 104.2°F), "
        "hypoxemia (SpO2 88% on room air), and confluent macular rash. Admitted emergently to Pediatric Intensive Care Unit (PICU) for "
        "acute cytokine release syndrome / severe infusion reaction. Managed with high-flow oxygen, IV hydrocortisone, and acetaminophen. "
        "<b>Seriousness: [ X ] Life-Threatening: YES &nbsp;|&nbsp; [ X ] Hospitalization: YES.</b> Outcome: Recovered over 48 hours."
    )
    story3.append(Table([[Paragraph(react_text, val_st)]], colWidths=[540], style=[
        ('GRID', (0,0), (-1,-1), 0.75, colors.black),
        ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 4), ('RIGHTPADDING', (0,0), (-1,-1), 4)
    ]))
    story3.append(Spacer(1, 4))
    
    # Drug & Reporter
    drug_text = (
        "<b>SUSPECT DRUG:</b> OncoShield (peg-oncoshield) 50mg/m² IV &nbsp;|&nbsp; <b>LOT:</b> Lot #OS-2025-771 (Exp: 04/2026)<br/>"
        "<b>REPORTER:</b> Dr. Amanda Bennett, MD, FAAP (Pediatric Hematologist-Oncologist), Children's Memorial Hospital, Boston, MA<br/>"
        "Tel: (617) 555-0811 | Email: abennett@childrens-boston.org"
    )
    story3.append(Table([[Paragraph(drug_text, val_st)]], colWidths=[540], style=[
        ('GRID', (0,0), (-1,-1), 0.75, colors.black),
        ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 4), ('RIGHTPADDING', (0,0), (-1,-1), 4)
    ]))
    doc3.build(story3)
    print(f"[OK] Generated Digital Form 3: {p3}")

    # Digital Form 4: Initial FDA 3500A Report for Neuroval Seizures
    p4 = os.path.join(DIGITAL_DIR, "fda_medwatch_initial_neuroval.pdf")
    doc4 = SimpleDocTemplate(p4, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    story4 = [
        Paragraph("FORM FDA 3500A — INITIAL SERIOUS ADVERSE EVENT REPORT", ParagraphStyle('FInitHdr', fontName='Helvetica-Bold', fontSize=10, leading=12, alignment=TA_CENTER)),
        Paragraph("Department of Health and Human Services — Food and Drug Administration &nbsp;|&nbsp; Initial Submission", ParagraphStyle('FInitSub', fontName='Helvetica', fontSize=7.5, leading=9.5, alignment=TA_CENTER)),
        Spacer(1, 4),
        Paragraph("<b>SECTION A: PATIENT INFORMATION</b>", sec_st)
    ]
    p4_row = [
        Paragraph("<b>PATIENT IDENTIFIER:</b> D.M. (David Miller)", val_st),
        Paragraph("<b>AGE:</b> 52 YRS", val_st),
        Paragraph("<b>SEX:</b> MALE", val_st),
        Paragraph("<b>WEIGHT:</b> 79 kg", val_st),
    ]
    story4.append(Table([p4_row], colWidths=[180, 100, 100, 160], style=[
        ('GRID', (0,0), (-1,-1), 0.75, colors.black),
        ('TOPPADDING', (0,0), (-1,-1), 3), ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 4), ('RIGHTPADDING', (0,0), (-1,-1), 4)
    ]))
    story4.append(Spacer(1, 4))
    
    b4_text = (
        "<b>DESCRIBE EVENT OR PROBLEM (INITIAL ONSET):</b> 52-year-old male prescribed Neuroval (neuroval HCl) for neuropathic pain. "
        "Dose was escalated from 200mg to 400mg daily on 31-OCT-2025. On 02-NOV-2025 (~48h post dose increase), patient suffered a witnessed "
        "new-onset generalized tonic-clonic seizure lasting 3.5 minutes followed by 20 minutes of post-ictal confusion. Admitted to Neurological ICU. "
        "<b>OUTCOMES: [ X ] Hospitalization: YES &nbsp;|&nbsp; [ X ] Life-Threatening: YES.</b> "
        "Suspect Drug: Neuroval 400mg PO, Lot #NV-2025-110. Reporter: Dr. Richard Vance, MD, Columbia University Medical Center."
    )
    story4.append(Table([[Paragraph(b4_text, val_st)]], colWidths=[540], style=[
        ('GRID', (0,0), (-1,-1), 0.75, colors.black),
        ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 4), ('RIGHTPADDING', (0,0), (-1,-1), 4)
    ]))
    doc4.build(story4)
    print(f"[OK] Generated Digital Form 4: {p4}")

    # Digital Form 5: CIOMS Nephrotoxicity Report
    p5 = os.path.join(DIGITAL_DIR, "cioms_form_renal_injury.pdf")
    doc5 = SimpleDocTemplate(p5, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    story5 = [
        Paragraph("CIOMS FORM I — ACUTE KIDNEY INJURY SPONTANEOUS REPORT", ParagraphStyle('CRenHdr', fontName='Helvetica-Bold', fontSize=10, leading=12, alignment=TA_CENTER)),
        Paragraph("International Reporting of Adverse Drug Reactions &nbsp;|&nbsp; Case Ref: CIOMS-RENAL-2025-099", ParagraphStyle('CRenSub', fontName='Helvetica', fontSize=7.5, leading=9.5, alignment=TA_CENTER)),
        Spacer(1, 4),
        Paragraph("<b>I. REACTION INFORMATION</b>", sec_st)
    ]
    p5_row = [
        Paragraph("<b>1. PATIENT INITIALS:</b> G.T. (George Taylor)", val_st),
        Paragraph("<b>2. AGE:</b> 67 YRS", val_st),
        Paragraph("<b>3. SEX:</b> MALE", val_st),
        Paragraph("<b>4. WEIGHT:</b> 76 kg", val_st),
        Paragraph("<b>5. COUNTRY:</b> USA", val_st),
    ]
    story5.append(Table([p5_row], colWidths=[140, 90, 80, 110, 120], style=[
        ('GRID', (0,0), (-1,-1), 0.75, colors.black),
        ('TOPPADDING', (0,0), (-1,-1), 3), ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 4), ('RIGHTPADDING', (0,0), (-1,-1), 4)
    ]))
    story5.append(Spacer(1, 4))
    
    renal_text = (
        "<b>6. DESCRIBE REACTION:</b> 67-year-old male with chronic osteoarthritis initiated Renotril 30 mg PO QD. Baseline Serum Creatinine: 1.0 mg/dL "
        "(eGFR 78 mL/min). On day 14 of treatment, patient presented with oliguria (<400 mL/day) and peripheral edema. Laboratory chemistry revealed "
        "Serum Creatinine spiked to 4.2 mg/dL (KDIGO Stage 3 Acute Kidney Injury) with BUN 68 mg/dL and potassium 5.6 mEq/L. "
        "Renotril permanently withdrawn. Patient hospitalized for 5 days with aggressive IV hydration. Renal function recovered to baseline (Cr 1.1 mg/dL) "
        "at 3 weeks post-discharge.<br/>"
        "<b>Seriousness: [ X ] Inpatient Hospitalization: YES.</b> Suspect Drug: Renotril 30mg, Lot #RN-2025-412. "
        "Reporter: Dr. Keith Miller, MD (Nephrology), Vanderbilt University Medical Center."
    )
    story5.append(Table([[Paragraph(renal_text, val_st)]], colWidths=[540], style=[
        ('GRID', (0,0), (-1,-1), 0.75, colors.black),
        ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 4), ('RIGHTPADDING', (0,0), (-1,-1), 4)
    ]))
    doc5.build(story5)
    print(f"[OK] Generated Digital Form 5: {p5}")

# -------------------------------------------------------------
# 5. GENERATE THE IRRELEVANT PDF: Conference Prospectus
# -------------------------------------------------------------
def generate_irrelevant_pdf():
    pdf_path = os.path.join(IRR_DIR, "pharmatech_conference_prospectus.pdf")
    doc = SimpleDocTemplate(pdf_path, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    
    t_st = ParagraphStyle('SpamTitle', fontName='Helvetica-Bold', fontSize=14, leading=17, alignment=TA_CENTER, textColor=colors.HexColor('#1E3A8A'))
    sub_st = ParagraphStyle('SpamSub', fontName='Helvetica', fontSize=9, leading=12, alignment=TA_CENTER, textColor=colors.HexColor('#475569'))
    b_st = ParagraphStyle('SpamBody', fontName='Helvetica', fontSize=8, leading=11, textColor=colors.black)
    
    story = [
        Paragraph("14TH ANNUAL GLOBAL PHARMACEUTICAL AI & COMPLIANCE SUMMIT 2026", t_st),
        Paragraph("SPONSORSHIP & EXHIBITOR PROSPECTUS — BOSTON CONVENTION CENTER, MARCH 24–26, 2026", sub_st),
        Spacer(1, 10),
        Paragraph("<b>WHY SPONSOR PHARMATECH 2026?</b>", ParagraphStyle('Bld', fontName='Helvetica-Bold', fontSize=9.5, leading=12)),
        Paragraph("Connect with over 750 senior decision-makers from top 50 pharmaceutical enterprises, regulatory agencies, and AI technology vendors. "
                  "Our attendees represent VPs of Pharmacovigilance, Global Safety Directors, and Chief Digital Health Officers.", b_st),
        Spacer(1, 6),
        Paragraph("<b>SPONSORSHIP PACKAGES:</b>", ParagraphStyle('Bld2', fontName='Helvetica-Bold', fontSize=9, leading=11)),
        Spacer(1, 3)
    ]
    
    pkgs = [
        [Paragraph("<b>Tier Package</b>", b_st), Paragraph("<b>Booth Space</b>", b_st), Paragraph("<b>Keynote Slot</b>", b_st), Paragraph("<b>Delegate Passes</b>", b_st), Paragraph("<b>Investment</b>", b_st)],
        [Paragraph("Diamond Sponsor", b_st), Paragraph("20x20 ft Island", b_st), Paragraph("45-min Mainstage Keynote", b_st), Paragraph("10 VIP Passes", b_st), Paragraph("$45,000", b_st)],
        [Paragraph("Platinum Sponsor", b_st), Paragraph("10x20 ft Prime", b_st), Paragraph("30-min Track Keynote", b_st), Paragraph("6 VIP Passes", b_st), Paragraph("$28,000", b_st)],
        [Paragraph("Gold Sponsor", b_st), Paragraph("10x10 ft Standard", b_st), Paragraph("Panel Participation", b_st), Paragraph("4 Standard Passes", b_st), Paragraph("$15,000", b_st)],
    ]
    story.append(Table(pkgs, colWidths=[120, 110, 150, 90, 70], style=[
        ('GRID', (0,0), (-1,-1), 0.75, colors.HexColor('#94A3B8')),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#EDF2F7')),
        ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 4), ('RIGHTPADDING', (0,0), (-1,-1), 4)
    ]))
    story.append(Spacer(1, 8))
    story.append(Paragraph("<b>CONTACT EXHIBITOR RELATIONS:</b> sales@pharmasummit-global2026.com | Tel: +1 (800) 555-EXPO<br/>"
                           "<i>Notice: Commercial marketing flyer. Contains zero clinical patient safety data. Category: Not Relevant.</i>", b_st))
    doc.build(story)
    print(f"[OK] Generated Irrelevant Marketing PDF: {pdf_path}")

# -------------------------------------------------------------
# 6. GENERATE MANIFEST.JSON & BENCHMARK.JSON
# -------------------------------------------------------------
def generate_metadata_artifacts():
    # Manifest
    manifest_data = {
        "dataset_name": "Clinevo Smart Inbox Synthetic Pharmacovigilance Test Suite",
        "version": "1.0.0",
        "author": "Forward Deployment / GenAI Integration Engineering Candidate",
        "created_date": "2026-09-04",
        "compliance_notes": "100% Synthetic / Fictional data complying strictly with Section 3.E (No real patient data).",
        "statistics": {
            "total_emails": 10,
            "total_pdfs": 18, # 18 generated, 1 reserved for user paper mock form = 19
            "categories": {
                "Safety_Report_ICSR": 6,
                "Quality_Complaint_PQC": 3,
                "Medical_Information_MI": 2,
                "Not_Relevant": 1,
                "Multi_Label": 1
            },
            "pdf_flavors": {
                "Digital_PDF": 5,
                "Scanned_Handwritten": 1, # + 1 user paper form = 2
                "Published_Article": 5,
                "Non_English": 2,
                "Quality_Complaint_PDF": 2,
                "Medical_Info_PDF": 2,
                "Irrelevant_PDF": 1
            }
        },
        "inventory": [
            {"id": "CASE-01", "email": "email_01.eml", "pdf": "digital_forms/cioms_form_MK_Cardioril.pdf", "category": ["ICSR"], "flavor": "Digital_PDF", "has_table": True, "has_image": False, "language": "en"},
            {"id": "CASE-02", "email": "email_02.eml", "pdf": "scanned_handwritten/urgent_care_intake_handwritten.pdf", "category": ["ICSR"], "flavor": "Scanned_Handwritten", "has_table": True, "has_image": True, "language": "en"},
            {"id": "CASE-03", "email": "email_03.eml", "pdf": None, "category": ["ICSR"], "flavor": "Pure_Text_Email", "has_table": False, "has_image": False, "language": "en"},
            {"id": "CASE-04", "email": "email_04.eml", "pdf": "quality_complaints/vial_contamination_sepsis.pdf", "category": ["ICSR", "PQC"], "flavor": "Digital_PDF", "has_table": True, "has_image": True, "language": "en"},
            {"id": "CASE-05", "email": "email_05.eml", "pdf": "non_english/notificacion_ram_madrid.pdf", "category": ["ICSR"], "flavor": "Non_English", "has_table": True, "has_image": False, "language": "es"},
            {"id": "CASE-06", "email": "email_06.eml", "pdf": "digital_forms/fda_medwatch_followup.pdf", "category": ["ICSR"], "flavor": "Digital_PDF", "has_table": True, "has_image": False, "language": "en"},
            {"id": "CASE-07", "email": "email_07.eml", "pdf": "quality_complaints/packaging_defect_report.pdf", "category": ["PQC"], "flavor": "Digital_PDF", "has_table": True, "has_image": False, "language": "en"},
            {"id": "CASE-08", "email": "email_08.eml", "pdf": None, "category": ["PQC"], "flavor": "Pure_Text_Email", "has_table": False, "has_image": False, "language": "en"},
            {"id": "CASE-09", "email": "email_09.eml", "pdf": None, "category": ["MI"], "flavor": "Pure_Text_Email", "has_table": False, "has_image": False, "language": "en"},
            {"id": "CASE-10", "email": "email_10.eml", "pdf": None, "category": ["Not Relevant"], "flavor": "Pure_Text_Email", "has_table": False, "has_image": False, "language": "en"},
            {"id": "LIT-01", "email": None, "pdf": "literature_articles/article_01_dili_case.pdf", "category": ["ICSR"], "flavor": "Published_Article", "cases_count": 1, "has_table": False, "has_image": False, "language": "en"},
            {"id": "LIT-02", "email": None, "pdf": "literature_articles/article_02_sjs_case.pdf", "category": ["ICSR"], "flavor": "Published_Article", "cases_count": 1, "has_table": False, "has_image": False, "language": "en"},
            {"id": "LIT-03", "email": None, "pdf": "literature_articles/article_03_multicase_series.pdf", "category": ["ICSR"], "flavor": "Published_Article", "cases_count": 3, "has_table": False, "has_image": False, "language": "en", "multicase_bonus": True},
            {"id": "LIT-04", "email": None, "pdf": "literature_articles/article_04_preclinical_review.pdf", "category": ["Not Relevant"], "flavor": "Published_Article", "cases_count": 0, "has_table": False, "has_image": False, "language": "en", "reportable": False},
            {"id": "LIT-05", "email": None, "pdf": "literature_articles/article_05_meta_analysis_review.pdf", "category": ["Not Relevant"], "flavor": "Published_Article", "cases_count": 0, "has_table": False, "has_image": False, "language": "en", "reportable": False},
            {"id": "DE-01", "email": None, "pdf": "non_english/bericht_uaw_charite_berlin.pdf", "category": ["ICSR"], "flavor": "Non_English", "has_table": True, "has_image": False, "language": "de"},
            {"id": "MI-01", "email": None, "pdf": "medical_info/cardioril_clinical_monograph_dosing.pdf", "category": ["MI"], "flavor": "Medical_Info_PDF", "has_table": True, "has_image": False, "language": "en"},
            {"id": "MI-02", "email": None, "pdf": "medical_info/corzapan_drug_interaction_guide.pdf", "category": ["MI"], "flavor": "Medical_Info_PDF", "has_table": True, "has_image": False, "language": "en"},
            {"id": "DIG-03", "email": None, "pdf": "digital_forms/cioms_pediatric_oncology.pdf", "category": ["ICSR"], "flavor": "Digital_PDF", "has_table": True, "has_image": False, "language": "en"},
            {"id": "DIG-04", "email": None, "pdf": "digital_forms/fda_medwatch_initial_neuroval.pdf", "category": ["ICSR"], "flavor": "Digital_PDF", "has_table": True, "has_image": False, "language": "en"},
            {"id": "DIG-05", "email": None, "pdf": "digital_forms/cioms_form_renal_injury.pdf", "category": ["ICSR"], "flavor": "Digital_PDF", "has_table": True, "has_image": False, "language": "en"},
            {"id": "IRR-01", "email": None, "pdf": "irrelevant/pharmatech_conference_prospectus.pdf", "category": ["Not Relevant"], "flavor": "Irrelevant_PDF", "has_table": True, "has_image": False, "language": "en"}
        ]
    }
    
    manifest_path = os.path.join(BASE_DIR, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)
    print(f"[OK] Generated Dataset Manifest: {manifest_path}")

    # Benchmark Ground Truth
    benchmark_data = {
        "version": "1.0.0",
        "description": "Ground Truth benchmark answers for automated precision/recall evaluation of Smart Inbox AI pipeline",
        "cases": {
            "CASE-01": {
                "categories": ["Safety Report (ICSR)"],
                "confidence_threshold": 0.90,
                "patient": {"age": "58 YRS", "sex": "FEMALE", "initials": "M.K.", "weight": "68 kg"},
                "product": {"name": "Cardioril (cardioril hydrochloride)", "dose": "20 mg once daily (QD)", "route": "Oral (tablet)", "lot": "CR-2025-0981"},
                "reaction": {"terms": ["Acute Drug-Induced Liver Injury (DILI)", "Jaundice", "Scleral Icterus"], "onset": "08-NOV-2025", "serious": True, "hospitalization": True},
                "lab_tests": {"ALT": "540 U/L", "AST": "420 U/L", "Total_Bilirubin": "4.8 mg/dL", "Alkaline_Phosphatase": "210 U/L"},
                "source_citations": {"patient": "cioms_form_MK_Cardioril.pdf:Page1:Box1", "drug": "cioms_form_MK_Cardioril.pdf:Page1:Box14", "reaction": "cioms_form_MK_Cardioril.pdf:Page1:Box6", "labs": "cioms_form_MK_Cardioril.pdf:Page1:Box23"}
            },
            "CASE-02": {
                "categories": ["Safety Report (ICSR)"],
                "confidence_threshold": 0.80,
                "patient": {"name": "Jane Doe", "dob": "05/18/1990", "age": "33", "sex": "F"},
                "product": {"name": "InjectaPen", "dose": "50 mg", "lot": "Not stated"},
                "reaction": {"terms": ["Acute Anaphylaxis (Grade 3)", "Generalized Hives", "Facial Angioedema", "Inspiratory Stridor"], "serious": True, "life_threatening": True, "hospitalization": True},
                "vitals": {"BP": "85/50", "HR": "128 bpm", "SpO2": "91%"},
                "source_citations": {"all": "urgent_care_intake_handwritten.pdf:Page1"}
            },
            "CASE-03": {
                "categories": ["Safety Report (ICSR)"],
                "confidence_threshold": 0.90,
                "patient": {"name": "Emily Watson", "age": "42 years old", "sex": "Female", "weight": "Not stated"},
                "product": {"name": "Corzapan 10mg tablets", "dose": "10mg once daily", "lot": "Not stated"},
                "reaction": {"terms": ["Tachycardia (154 bpm)", "Palpitations", "Lightheadedness", "Near-syncope"], "serious": False},
                "source_citations": {"all": "email_03.eml:Body"}
            },
            "CASE-04": {
                "categories": ["Safety Report (ICSR)", "Quality Complaint (PQC)"],
                "confidence_threshold": 0.90,
                "quality_complaint": {
                    "product": "Cefatox (cefatoxime sodium) 1g for Inj.",
                    "lot": "CX54831",
                    "expiry": "08/2025",
                    "defect": "Cracked aluminum crimp collar, compromised rubber stopper closure, visible black particulate contamination",
                    "photo_mentioned": True,
                    "photo_flag": True
                },
                "safety_report": {
                    "patient": {"identifier": "Arthur Pendelton (A.P.)", "age": "71 YRS", "sex": "MALE", "weight": "74 kg"},
                    "reaction": {"terms": ["Severe Acute Bacteremia", "Distributive Septic Shock", "Hypotension (BP 72/40)", "Hyperthermia (39.8 C)"], "serious": True, "life_threatening": True, "hospitalization": True}
                },
                "source_citations": {"pqc": "vial_contamination_sepsis.pdf:Page1:SectionC", "photo": "vial_contamination_sepsis.pdf:Page2:Exhibit1", "safety": "vial_contamination_sepsis.pdf:Page1:SectionB"}
            },
            "CASE-05": {
                "categories": ["Safety Report (ICSR)"],
                "language": "es",
                "translated": True,
                "patient": {"initials": "Carmen Ortiz (C.O.)", "age": "29 AÑOS", "sex": "MUJER", "weight": "54 kg"},
                "product": {"name": "Lamotrigina (Lamictal) 100 mg", "dose": "100 mg/día vía oral", "lot": "LM-9941"},
                "reaction": {"terms": ["Necrólisis Epidérmica Tóxica (NET / Síndrome de Lyell)", "Toxic Epidermal Necrolysis", "Desprendimiento dermoepidérmico >35% SC"], "serious": True, "life_threatening": True, "hospitalization": True},
                "source_citations": {"all": "notificacion_ram_madrid.pdf:Page1"}
            },
            "LIT-03": {
                "categories": ["Safety Report (ICSR)"],
                "multicase": True,
                "total_cases_extracted": 3,
                "split_cases": [
                    {"case_no": 1, "patient": "A.J., 45M, 81kg", "drug": "Cardioril 20mg QD", "reaction": "Erythema Multiforme Major", "serious": True},
                    {"case_no": 2, "patient": "B.L., 62F, 64kg", "drug": "Corzapan 10mg daily", "reaction": "Subacute Cutaneous Lupus Erythematosus (SCLE)", "serious": False},
                    {"case_no": 3, "patient": "C.M., 38F, 59kg", "drug": "Cardioril 10mg daily", "reaction": "Acute Urticaria, Periorbital Angioedema", "serious": True}
                ],
                "source_citations": {"all": "article_03_multicase_series.pdf:Page1-Page2"}
            }
        }
    }
    
    benchmark_path = os.path.join(GT_DIR, "benchmark.json")
    with open(benchmark_path, "w", encoding="utf-8") as f:
        json.dump(benchmark_data, f, indent=2)
    print(f"[OK] Generated Ground Truth Benchmark: {benchmark_path}")

if __name__ == '__main__':
    print("Starting generation of all remaining test data assets...")
    generate_literature_articles()
    generate_german_pdf()
    generate_medical_info_pdfs()
    generate_additional_digital_forms()
    generate_irrelevant_pdf()
    generate_metadata_artifacts()
    print("\n[SUCCESS] All remaining test data assets generated successfully!")
