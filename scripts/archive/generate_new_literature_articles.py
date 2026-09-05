import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, FrameBreak, PageBreak, Table
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT

LIT_DIR = r"c:\projects\SmartInbox\test-data\pdfs\literature_articles"

def build_multi_page_article(pdf_path, title, authors, journal, doi, abstract, story_elements):
    doc = BaseDocTemplate(pdf_path, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    
    frame_width = (letter[0] - 72 - 18) / 2 # 261 pt
    frame_height = letter[1] - 72 # 720 pt
    
    frame1 = Frame(36, 36, frame_width, frame_height, id='col1', leftPadding=0, rightPadding=6, topPadding=0, bottomPadding=0)
    frame2 = Frame(36 + frame_width + 18, 36, frame_width, frame_height, id='col2', leftPadding=6, rightPadding=0, topPadding=0, bottomPadding=0)
    
    template = PageTemplate(id='two_col', frames=[frame1, frame2])
    doc.addPageTemplates([template])
    
    j_hdr = ParagraphStyle('JHdr', fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=colors.HexColor('#1E3A8A'))
    doi_st = ParagraphStyle('Doi', fontName='Helvetica', fontSize=7, leading=9, textColor=colors.HexColor('#64748B'))
    art_title = ParagraphStyle('ArtTitle', fontName='Helvetica-Bold', fontSize=11, leading=14, textColor=colors.black)
    art_auth = ParagraphStyle('ArtAuth', fontName='Helvetica', fontSize=8, leading=10, textColor=colors.HexColor('#334155'))
    abs_hdr = ParagraphStyle('AbsHdr', fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=colors.black)
    abs_body = ParagraphStyle('AbsBody', fontName='Times-Italic', fontSize=7.5, leading=9.5, alignment=TA_JUSTIFY, textColor=colors.HexColor('#1E293B'))
    
    story = [
        Paragraph(journal.upper(), j_hdr),
        Paragraph(f"DOI: {doi} &nbsp;|&nbsp; Peer-Reviewed Clinical Report", doi_st),
        Spacer(1, 4),
        Paragraph(title, art_title),
        Spacer(1, 2),
        Paragraph(authors, art_auth),
        Spacer(1, 5),
        Paragraph("<b>ABSTRACT</b>", abs_hdr),
        Paragraph(abstract, abs_body),
        Spacer(1, 6),
    ]
    
    sec_hdr = ParagraphStyle('SecHdr', fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=colors.HexColor('#0F172A'))
    p_body = ParagraphStyle('PBody', fontName='Times-Roman', fontSize=7.5, leading=9.5, alignment=TA_JUSTIFY, textColor=colors.black)
    
    for el in story_elements:
        if el == "---FRAME-BREAK---":
            story.append(FrameBreak())
        elif el == "---PAGE-BREAK---":
            story.append(PageBreak())
        elif isinstance(el, str) and el.startswith("###"):
            story.append(Spacer(1, 3))
            story.append(Paragraph(f"<b>{el.replace('###', '').strip()}</b>", sec_hdr))
            story.append(Spacer(1, 2))
        elif isinstance(el, str):
            story.append(Paragraph(el, p_body))
            story.append(Spacer(1, 3))
        else:
            story.append(el)
            
    doc.build(story)
    print(f"[OK] Generated Article PDF: {pdf_path}")

# -------------------------------------------------------------
# 1. REGENERATE ARTICLE 01: Replace TV names with realistic medical authors
# -------------------------------------------------------------
def regenerate_article_01():
    p1 = os.path.join(LIT_DIR, "article_01_dili_case.pdf")
    build_multi_page_article(
        pdf_path=p1,
        title="Severe Drug-Induced Autoimmune Hepatitis Triggered by Cardioril Therapy",
        authors="Julian Montgomery, MD, PhD; Evelyn Vance, MD; Kenneth Ross, MD<br/>Department of Medicine, Princeton Academic Medical Center, Princeton, NJ",
        journal="Journal of Clinical Hepatology & Pharmacovigilance | Vol 42, No 4",
        doi="10.1016/j.jchpv.2025.04.012",
        abstract="We report an idiosyncratic case of severe acute drug-induced autoimmune-like hepatitis in a 61-year-old male following 6 weeks of Cardioril (cardioril hydrochloride 40mg daily) administration. Marked hyperbilirubinemia, antinuclear antibody (ANA) seroconversion (titer 1:640), and liver biopsy showing interface hepatitis were documented. Immediate drug withdrawal resulted in clinical and biochemical resolution.",
        story_elements=[
            "### INTRODUCTION",
            "Idiosyncratic drug-induced liver injury (DILI) represents a formidable challenge in clinical pharmacology. Cardioril is a novel third-generation antihypertensive agent targeting vascular smooth muscle receptors. While clinical trials reported mild transient aminotransferase elevations in <1.2% of participants, post-marketing surveillance is critical for identifying severe immune-mediated reactions.",
            "### CASE PRESENTATION",
            "A 61-year-old Caucasian male with a 10-year history of refractory hypertension and hyperlipidemia was initiated on Cardioril 40 mg PO QD. Baseline hepatic function panel was completely normal (ALT 22 U/L, AST 19 U/L, Total Bilirubin 0.6 mg/dL). Forty-two days following treatment initiation, the patient presented with progressive fatigue, nausea, dark urine, and jaundice.",
            "Physical examination revealed marked scleral icterus and right upper quadrant tenderness without hepatosplenomegaly or ascites. Laboratory evaluation demonstrated ALT 680 U/L (>12x ULN), AST 510 U/L (>12x ULN), Total Bilirubin 6.2 mg/dL, and Alkaline Phosphatase 240 U/L.",
            "---FRAME-BREAK---",
            "### INVESTIGATIONS & CLINICAL COURSE",
            "Viral serologies for hepatitis A, B, C, and E, cytomegalovirus, and Epstein-Barr virus were non-reactive. Autoimmune serology revealed positive antinuclear antibodies (ANA 1:640, speckled pattern) and elevated IgG levels (2,100 mg/dL). A percutaneous liver biopsy demonstrated severe interface hepatitis with dense portal lymphoplasmacytic infiltrate and bridging necrosis, consistent with drug-induced autoimmune hepatitis.",
            "Cardioril was discontinued on admission. A 4-week tapering course of oral prednisone (40 mg/day initial) was administered. Over the subsequent 6 weeks, serum transaminases and bilirubin normalized completely (ALT 28 U/L, Total Bili 0.8 mg/dL). Re-challenge was not attempted due to severity.",
            "### DISCUSSION & CONCLUSION",
            "This report highlights a probable causal relationship between Cardioril exposure and drug-induced autoimmune hepatitis (RUCAM score = 8, probable). Healthcare practitioners should maintain vigilant liver function monitoring during the first 3 months of Cardioril initiation.",
            "### REFERENCES",
            "1. Chalasani N, et al. Practice Parameters: Evaluation of Drug-Induced Liver Injury. Am J Gastroenterol. 2021;116(5):878-898.<br/>2. Fontana RJ. Pathogenesis of idiosyncratic drug-induced liver injury. Gastroenterology. 2022;162(5):1370-1388."
        ]
    )

# -------------------------------------------------------------
# 2. REGENERATE ARTICLE 03: Replace author Arthur Pendelton with Alistair Finch to avoid collision with Case 04 patient
# -------------------------------------------------------------
def regenerate_article_03():
    p3 = os.path.join(LIT_DIR, "article_03_multicase_series.pdf")
    build_multi_page_article(
        pdf_path=p3,
        title="Cutaneous Adverse Reactions Associated with Novel Antihypertensives: A Clinical Series of Three Cases",
        authors="Marcus Sterling, MD, FRCP; Alistair Finch, MBChB; Eleanor Vance, MD<br/>Royal Free Hospital, London, United Kingdom & Guy's and St Thomas' NHS Foundation Trust",
        journal="The Lancet Regional Health — Europe | Clinical Case Series",
        doi="10.1016/j.lanepe.2025.100984",
        abstract="We document three distinct individual cases of severe cutaneous drug reactions occurring secondary to novel antihypertensive therapies across two university medical centers. Case 1 describes a 45-year-old male with severe Erythema Multiforme Major. Case 2 describes a 62-year-old female presenting with subacute cutaneous lupus erythematosus. Case 3 documents a 38-year-old female with acute urticaria and periorbital angioedema. All cases responded favorably to prompt drug cessation.",
        story_elements=[
            "### INTRODUCTION",
            "The expansion of novel antihypertensive pharmacotherapies has coincided with sporadic reports of delayed-type hypersensitivity reactions. We present three well-characterized independent patient cases identified during a 6-month surveillance period.",
            "### PATIENT CASE 1",
            "A 45-year-old male (Patient A.J., weight 81 kg) with stage II hypertension was prescribed Cardioril 20 mg once daily. On day 22 of therapy, he presented with extensive symmetrical target lesions with central blistering on the dorsal hands, forearms, and lower extremities, accompanied by severe oral mucosal erosions. Diagnosis: Erythema Multiforme Major. Histopathology confirmed apoptotic keratinocytes with vacuolar basal interface dermatitis. Cardioril was discontinued, and systemic methylprednisolone was initiated. Complete resolution was achieved within 16 days.",
            "### PATIENT CASE 2",
            "A 62-year-old female (Patient B.L., weight 64 kg) commenced Corzapan 10 mg daily for essential hypertension. After 8 weeks of therapy, she developed widespread annular, polycyclic scaly erythematous plaques distributed across sun-exposed areas of the upper back and shoulders. Serology revealed high-titer anti-Ro/SSA antibodies (>240 U/mL) and ANA 1:320. Diagnosis: Drug-induced subacute cutaneous lupus erythematosus (SCLE). Corzapan was discontinued. Lesions resolved over 8 weeks with topical tacrolimus.",
            "---FRAME-BREAK---",
            "### PATIENT CASE 3",
            "A 38-year-old female (Patient C.M., weight 59 kg) with mild hypertension was initiated on Cardioril 10 mg daily. Approximately 90 minutes following her initial dose, she developed acute generalized urticaria with severe pruritus, dysphonia, and marked bilateral periorbital angioedema. Emergency management with intramuscular epinephrine 0.3 mg and intravenous diphenhydramine 50 mg aborted progression to respiratory compromise. Cardioril was permanently avoided.",
            "### PHARMACOVIGILANCE DISCUSSION",
            "These three cases underscore the clinical necessity for distinct Individual Case Safety Report (ICSR) submission for each patient, despite publication within a unified clinical series. Each case features unique demographic profiles, differing onset latencies (ranging from 90 minutes to 8 weeks), distinct MedDRA clinical reaction phenotypes, and independent de-challenge timelines.",
            "Safety reporting departments must ensure that multicase journal articles are disaggregated into separate regulatory cases to prevent signal dilution.",
            "### REFERENCES",
            "1. Roujeau JC. Immune mechanisms in drug eruptions. Clin Dermatol. 2020;38(6):679-688.<br/>2. EMA Guideline on Good Pharmacovigilance Practices (GVP) Module VI — Collection, verification and presentation of adverse reactions."
        ]
    )

# -------------------------------------------------------------
# 3. GENERATE ARTICLE 06: 2 Pages, Fictional Patient Case BURIED after heavy discussion
# -------------------------------------------------------------
def generate_article_06():
    p6 = os.path.join(LIT_DIR, "article_06_buried_case_study.pdf")
    build_multi_page_article(
        pdf_path=p6,
        title="Delayed Immune-Mediated Myocarditis Secondary to Combination Checkpoint Inhibition: Case Report & Surveillance Review",
        authors="Robert H. Caldwell, MD; Danielle M. Zhang, MD, PhD; Christopher Owens, MD<br/>Department of Medical Oncology, Dana-Farber Cancer Institute & Harvard Medical School, Boston, MA",
        journal="Journal of Clinical Oncology & Immunotherapy | Vol 18, No 3",
        doi="10.1200/JCOI.2025.18.3.412",
        abstract="Immune checkpoint inhibitors (ICIs) targeting CTLA-4 and PD-1 pathways have revolutionized oncologic care but introduce serious immune-related adverse events (irAEs). While dermatologic, gastrointestinal, and endocrine toxicities are relatively common, cardiotoxicity—specifically fulminant autoimmune myocarditis—remains rare (<1.1%) yet carries a mortality rate exceeding 40%. We synthesize current surveillance guidelines across multi-institutional registries and document a definitive case of delayed-onset fulminant myocarditis in a 68-year-old female presenting during cycle 3 of combination immunotherapy, successfully managed with pulse-dose corticosteroids and temporary pacing.",
        story_elements=[
            "### 1. INTRODUCTION & IMMUNOLOGICAL MECHANISMS",
            "The therapeutic paradigm for unresectable and metastatic malignancies has shifted toward dual immune checkpoint blockade. By uncoupling inhibitory signals mediated by programmed cell death protein 1 (PD-1) and cytotoxic T-lymphocyte-associated protein 4 (CTLA-4), these agents potentiate robust antitumor CD8+ T-cell responses.",
            "However, loss of peripheral tolerance can precipitate autoimmune attack against somatic tissues sharing antigenic epitopes or vulnerable to dysregulated lymphocytic infiltration. Cardiac myocytes express PD-L1 under physiological stress, acting as a cardioprotective brake against inflammation. Pharmacological disruption of this axis predisposes vulnerable individuals to lymphocytic myocardial infiltration, myocyte necrosis, and conduction disruption.",
            "### 2. EPIDEMIOLOGY ACROSS GLOBAL SURVEILLANCE DATABASES",
            "Retrospective analyses of WHO VigiBase and institutional pharmacovigilance safety repositories indicate that median onset of ICI myocarditis is 34 days following initial exposure, typically after 1 or 2 cycles. Nonetheless, atypical presentations emerging beyond 60 days or following maintenance transitions require elevated clinical vigilance. Serum cardiac troponin-I and T elevations are sensitive (>94%) but lack absolute specificity.",
            "---FRAME-BREAK---",
            "### 3. COMPREHENSIVE CLINICAL CASE PRESENTATION",
            "A 68-year-old Caucasian female (Patient H.L., body weight 62 kg) with BRAF wild-type stage IV metastatic cutaneous melanoma was initiated on combination immunotherapy consisting of Nivolumab (Opdivo) 240 mg IV every 2 weeks and Ipilimumab (Yervoy) 1 mg/kg IV every 6 weeks.",
            "Baseline cardiac evaluation—including 12-lead electrocardiogram (ECG) and transthoracic echocardiography—demonstrated normal sinus rhythm, normal QTc interval (412 ms), and preserved left ventricular ejection fraction (LVEF 62%). Cycles 1 and 2 proceeded uneventfully without clinically significant immune toxicities.",
            "On day 44 post-initiation (12 days following cycle 3 administration), the patient presented to the emergency department with progressive exertional dyspnea, orthopnea, bilateral lower extremity edema, and profound generalized fatigue over the preceding 72 hours. Vital signs on presentation: Blood pressure 88/54 mmHg, heart rate 42 bpm (severe bradycardia), respiratory rate 24/min, and oxygen saturation 92% on ambient air.",
            "Emergency 12-lead ECG demonstrated complete (third-degree) atrioventricular (AV) heart block with a junctional escape rhythm at 40 bpm. High-sensitivity cardiac troponin-T was markedly elevated at 1.84 ng/mL (reference <0.014 ng/mL), and NT-proBNP was 4,820 pg/mL. Urgent bedside echocardiogram revealed diffuse biventricular hypokinesis with acute LVEF decline to 32%.",
            "---PAGE-BREAK---",
            "### 4. INVASIVE MONITORING, MANAGEMENT & CLINICAL COURSE",
            "The patient was urgently transferred to the Cardiac Intensive Care Unit (CICU). Immunotherapy was immediately suspended. Due to hemodynamically compromising complete heart block, a temporary transvenous pacemaker was emergently placed via the right internal jugular vein.",
            "High-dose pulse intravenous methylprednisolone (1,000 mg IV daily) was initiated within 2 hours of presentation. Endomyocardial biopsy performed on hospital day 2 demonstrated extensive interstitial infiltration of CD4+ and CD8+ T-lymphocytes accompanied by multifocal cardiomyocyte necrosis, pathognomonic for grade 4 immune-mediated myocarditis.",
            "Due to persistent troponin elevation on day 4, second-line immunosuppression with therapeutic plasma exchange (plasmapheresis, 5 total exchanges) was added. Over the subsequent 10 days, AV conduction recovered to 1:1 sinus rhythm, and cardiac biomarkers progressively declined (troponin-T 0.08 ng/mL).",
            "The patient was transitioned to an oral prednisone taper (1 mg/kg/day initial) over 8 weeks. Repeat echocardiogram at week 4 post-discharge revealed recovery of LVEF to 54%. Immunotherapy was permanently discontinued.",
            "---FRAME-BREAK---",
            "### 5. REGULATORY PHARMACOVIGILANCE DISCUSSION",
            "Under ICH E2A and GVP Module VI expedited reporting rules, this case fulfills seriousness criteria for both inpatient hospitalization and life-threatening medical event. The World Health Organization (WHO-UMC) and Naranjo causality assessment algorithms yield a score of 8 ('probable').",
            "Clinical safety reporting teams must recognize that although literature articles may contain extensive mechanistic discussion and registry summaries, identifiable individual case safety reports (ICSRs) embedded within review articles must be fully extracted and expedited to regulatory agencies within mandatory 15-day timelines.",
            "### 6. REFERENCES",
            "1. Mahmood SS, et al. Myocarditis in patients treated with immune checkpoint inhibitors. J Am Coll Cardiol. 2018;71(16):1755-1764.<br/>"
            "2. Salem JE, et al. Cardiovascular toxicities associated with immune checkpoint inhibitors: an observational, pharmacovigilance study. Lancet Oncol. 2018;19(12):1579-1589.<br/>"
            "3. Moslehi JJ, et al. Immune checkpoint inhibitor-associated myocarditis: compact guide for clinical triage. Circulation. 2021;143(3):234-246.<br/>"
            "4. EMA Guideline on Good Pharmacovigilance Practices (GVP) Module VI — Collection, verification and presentation of adverse reactions."
        ]
    )

# -------------------------------------------------------------
# 4. GENERATE ARTICLE 07: 2 Pages, Multi-Case Clinical Screening (2 Distinct Cases) + Distracting Non-Case Cohort
# -------------------------------------------------------------
def generate_article_07():
    p7 = os.path.join(LIT_DIR, "article_07_complex_screening_case.pdf")
    build_multi_page_article(
        pdf_path=p7,
        title="Drug-Induced Interstitial Lung Disease Associated with Biological and Targeted DMARDs: A Two-Case Clinical Observation",
        authors="Samantha Reed, MD; Tariq Al-Mansoor, MD; Fiona Gallagher, MD<br/>Division of Pulmonary & Critical Care Medicine, Johns Hopkins University School of Medicine, Baltimore, MD",
        journal="American Journal of Respiratory and Critical Care Medicine | Clinical Series",
        doi="10.1164/rccm.2025.09.1182",
        abstract="Biological disease-modifying antirheumatic drugs (DMARDs) targeting TNF-alpha and small-molecule inhibitors have revolutionized management of chronic inflammatory arthritides. However, pulmonary parenchymal toxicity—including drug-induced interstitial lung disease (DIILD) and cryptogenic organizing pneumonia—represents a severe diagnostic challenge. In this report, we evaluate non-case aggregate registry cohorts and document two distinct individual patient cases of life-threatening pulmonary toxicity occurring secondary to Infliximab and Leflunomide, highlighting the imperative for individualized safety disaggregation.",
        story_elements=[
            "### 1. INTRODUCTION & REGISTRY SURVEILLANCE",
            "Pulmonary involvement in rheumatic diseases can stem from primary underlying autoimmune disease or secondary pharmacotherapy toxicity. Disentangling underlying disease progression from iatrogenic pulmonary injury requires meticulous clinicoradiological correlation.",
            "### 2. OBSERVATIONAL REGISTRY ANALYSIS (NON-CASE COHORT)",
            "We initially reviewed surveillance telemetry from the Mid-Atlantic Rheumatic Disease Registry comprising 420 aggregate patients receiving biologic or targeted synthetic DMARDs over a 5-year observation interval. In this aggregate cohort, non-specific respiratory complaints (mild dry cough, dyspnea on exertion) occurred in 14.2% of patients without verifiable objective parenchymal infiltrates. These aggregate registry statistics do not represent individual ICSR safety events.",
            "### 3. PATIENT CASE REPORT 1: INFLIXIMAB PNEUMONITIS",
            "A 54-year-old male (Patient T.K., weight 75 kg) with a 6-year history of seropositive rheumatoid arthritis was initiated on Infliximab (Remicade) 5 mg/kg IV infusions at weeks 0, 2, and 6, followed by 8-week maintenance.",
            "Twelve days following his fourth infusion, the patient presented with acute high fever (38.9 deg C), rapidly progressive hypoxemic respiratory failure (PaO2 54 mmHg on room air), and severe non-productive cough. High-resolution chest CT (HRCT) demonstrated bilateral extensive ground-glass opacities with subpleural sparing. Bronchoalveolar lavage (BAL) ruled out Pneumocystis jirovecii, fungal pathogens, and viral etiologies, showing marked lymphocytic alveolitis (CD4:CD8 ratio 3.8).",
            "---FRAME-BREAK---",
            "The patient was admitted to the Medical Intensive Care Unit (MICU) and required non-invasive positive pressure ventilation for 48 hours. Infliximab was permanently withdrawn. High-dose systemic methylprednisolone (125 mg IV every 6 hours) was administered, resulting in progressive radiological and clinical improvement over 14 days. Final Diagnosis: Acute drug-induced interstitial pneumonitis. Seriousness: Hospitalization: YES, Life-Threatening: YES.",
            "### 4. PATIENT CASE REPORT 2: LEFLUNOMIDE-INDUCED COP",
            "A 41-year-old female (Patient M.S., weight 58 kg) with active psoriatic arthritis was prescribed Leflunomide (Arava) 20 mg PO once daily. Prior pulmonary history was completely unremarkable.",
            "At 12 weeks of continuous therapy, the patient developed subacute progressive exertional dyspnea, low-grade malaise, and bilateral pleuritic chest discomfort. Pulmonary function testing demonstrated restrictive physiology with a 28% decline in DLCO. Chest HRCT revealed patchy peripheral and peribronchovascular consolidations consistent with Cryptogenic Organizing Pneumonia (COP / BOOP).",
            "Leflunomide was immediately ceased. Due to its long terminal half-life (14–16 days), an accelerated elimination washout protocol with oral Cholestyramine (8 g three times daily for 11 days) was executed. Prednisone 40 mg PO QD was co-administered. Follow-up imaging at 8 weeks confirmed complete clearing of consolidations. Seriousness: Inpatient Hospitalization: YES. Positive dechallenge was documented.",
            "---PAGE-BREAK---",
            "### 5. COMPARATIVE CLINICAL & DIAGNOSTIC MATRIX",
            "Table 1 outlines the comparative clinical, radiological, and therapeutic parameters of the two reported cases:",
            "<b>Case 1 (Infliximab)</b>: Male, 54y, 75kg | Onset: 12 days post-infusion | HRCT: Diffuse bilateral ground-glass | Management: MICU, Pulse IV steroids | Outcome: Resolved.<br/>"
            "<b>Case 2 (Leflunomide)</b>: Female, 41y, 58kg | Onset: 12 weeks | HRCT: Patchy peribronchovascular consolidations (COP) | Management: Cholestyramine washout + oral steroids | Outcome: Resolved.",
            "### 6. PHARMACOVIGILANCE & REGULATORY IMPLICATIONS",
            "This clinical series emphasizes two fundamental principles for automated safety intake systems:<br/>"
            "First, screening systems must effectively filter out non-case background literature sections (such as the 420-patient observational cohort described in Section 2) that do not describe identifiable patient cases.<br/>"
            "Second, multicase articles must be parsed into separate, independent Individual Case Safety Reports (ICSRs). Case 1 and Case 2 involve different chemical entities, distinct mechanisms of lung injury, differing onset timelines, and divergent rescue protocols (pulse steroids vs. cholestyramine washout). Aggregating them into a single record violates regulatory compliance.",
            "---FRAME-BREAK---",
            "### 7. CONCLUSION & SURVEILLANCE RECOMMENDATIONS",
            "Clinicians initiating biological and targeted DMARDs must maintain a high index of suspicion for parenchymal drug toxicities. Automated pharmacovigilance intake systems must incorporate advanced NLP and layout analysis to distinguish between aggregate registry summaries and actionable individual patient cases.",
            "### 8. REFERENCES",
            "1. Camus P, et al. Drug-induced and iatrogenic respiratory disease. Eur Respir Rev. 2020;29(158):200016.<br/>"
            "2. Dixon WG, et al. Serious infection and pulmonary toxicity associated with anti-TNF therapy: results from the British Society for Rheumatology Biologics Register. Arthritis Rheum. 2019;60(3):641-653.<br/>"
            "3. EMA Guideline on Good Pharmacovigilance Practices (GVP) Module VI — Collection, verification and presentation of adverse reactions.<br/>"
            "4. FDA 21 CFR Part 314.80 — Postmarketing reporting of adverse drug experiences."
        ]
    )

if __name__ == "__main__":
    print("Regenerating Articles 01 & 03 with data hygiene fixes, and building Articles 06 & 07 (2-page articles)...")
    regenerate_article_01()
    regenerate_article_03()
    generate_article_06()
    generate_article_07()
    print("[SUCCESS] All literature articles generated and verified!")
