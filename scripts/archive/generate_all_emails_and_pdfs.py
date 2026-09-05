"""
Master Test Data Generator:
Compiles all 10 authentic RFC 5322 MIME emails into test-data/emails/
and generates the associated official regulatory PDFs:
- Case 05: notificacion_ram_madrid.pdf (Spanish AEMPS RAM form)
- Case 06: fda_medwatch_followup.pdf (FDA Form 3500A Follow-Up)
- Case 07: packaging_defect_report.pdf (Pharmacy Quality Defect Form)
- Attaches the PDFs to their corresponding emails.
"""

import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

# Directories
BASE_DIR = r"c:\projects\SmartInbox\test-data"
EMAIL_DIR = os.path.join(BASE_DIR, "emails")
PDF_DIGITAL = os.path.join(BASE_DIR, "pdfs", "digital_forms")
PDF_NON_ENG = os.path.join(BASE_DIR, "pdfs", "non_english")
PDF_PQC = os.path.join(BASE_DIR, "pdfs", "quality_complaints")

for d in [EMAIL_DIR, PDF_DIGITAL, PDF_NON_ENG, PDF_PQC]:
    os.makedirs(d, exist_ok=True)

# -------------------------------------------------------------
# 1. GENERATE CASE 05 PDF: Spanish AEMPS RAM Form
# -------------------------------------------------------------
def build_case_05_spanish_pdf(pdf_path: str):
    doc = SimpleDocTemplate(pdf_path, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    
    title_st = ParagraphStyle('EsTitle', fontName='Helvetica-Bold', fontSize=11, leading=13, alignment=TA_CENTER)
    sub_st = ParagraphStyle('EsSub', fontName='Helvetica', fontSize=8, leading=10, alignment=TA_CENTER)
    sec_st = ParagraphStyle('EsSec', fontName='Helvetica-Bold', fontSize=8, leading=10)
    val_st = ParagraphStyle('EsVal', fontName='Helvetica', fontSize=7.5, leading=9.5)
    
    story = [
        Paragraph("SISTEMA ESPAÑOL DE FARMACOVIGILANCIA DE MEDICAMENTOS DE USO HUMANO (SEFV-H)", sub_st),
        Paragraph("AGENCIA ESPAÑOLA DE MEDICAMENTOS Y PRODUCTOS SANITARIOS (AEMPS)", title_st),
        Paragraph("<b>NOTIFICACIÓN DE SOSPECHA DE REACCIÓN ADVERSA A MEDICAMENTOS (TARJETA AMARILLA)</b>", ParagraphStyle('EsHead', fontName='Helvetica-Bold', fontSize=8.5, leading=10.5, alignment=TA_CENTER)),
        Spacer(1, 4),
        Paragraph("<b>A. DATOS DEL PACIENTE</b>", sec_st)
    ]
    
    row_a = [
        Paragraph("<b>1. INICIALES:</b> C.O. (Carmen Ortiz)", val_st),
        Paragraph("<b>2. FECHA NACIMIENTO:</b> 22-MAR-1996", val_st),
        Paragraph("<b>2a. EDAD:</b> 29 AÑOS", val_st),
        Paragraph("<b>3. SEXO:</b> MUJER", val_st),
        Paragraph("<b>4. PESO:</b> 54 kg", val_st),
    ]
    t_a = Table([row_a], colWidths=[150, 110, 80, 80, 120], style=[
        ('GRID', (0,0), (-1,-1), 0.75, colors.black),
        ('TOPPADDING', (0,0), (-1,-1), 3), ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 4), ('RIGHTPADDING', (0,0), (-1,-1), 4)
    ])
    story.append(t_a)
    story.append(Spacer(1, 4))
    
    # Section B: Reacción Adversa
    story.append(Paragraph("<b>B. DESCRIPCIÓN DE LA REACCIÓN ADVERSA GRAVE</b>", sec_st))
    b_text = (
        "<b>DESCRIPCIÓN CLÍNICA:</b> Paciente de 29 años tratada con Lamotrigina (Lamictal) 100 mg/día por epilepsia mioclónica. "
        "A las 3 semanas de tratamiento inicia exantema macular eritematoso confluente y fiebre de 39,2 °C. En 48 horas evoluciona a "
        "desprendimiento dermoepidérmico extenso en láminas afectando cara, tronco y extremidades (>35% de la superficie corporal total, SC), "
        "con signo de Nikolsky positivo, estomatitis pseudomembranosa grave y conjuntivitis pseudomembranosa bilateral con queratitis. "
        "Diagnóstico clínico y biopsia cutánea: <b>Necrólisis Epidérmica Tóxica (NET / Síndrome de Lyell)</b> inducida por Lamotrigina. "
        "Ingresada de urgencia en la Unidad de Quemados Críticos del Hospital Universitario La Paz.<br/>"
        "<b>CRITERIOS DE GRAVEDAD:</b> [ X ] Mortalidad potencial / Amenaza vital &nbsp;&nbsp;&nbsp;&nbsp; [ X ] Hospitalización o prolongación<br/>"
        "<b>FECHA DE INICIO:</b> 11-NOV-2025 &nbsp;|&nbsp; <b>DESENLACE:</b> No recuperado (Estado crítico en UCI Quemados)."
    )
    t_b = Table([[Paragraph(b_text, val_st)]], colWidths=[540], style=[
        ('GRID', (0,0), (-1,-1), 0.75, colors.black),
        ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 4), ('RIGHTPADDING', (0,0), (-1,-1), 4)
    ])
    story.append(t_b)
    story.append(Spacer(1, 4))
    
    # Section C: Medicamento Sospechoso
    story.append(Paragraph("<b>C. MEDICAMENTO(S) SOSPECHOSO(S)</b>", sec_st))
    c_data = [
        [
            Paragraph("<b>MEDICAMENTO:</b> Lamotrigina (Lamictal) 100 mg", val_st),
            Paragraph("<b>DOSIS / VÍA:</b> 100 mg/día vía oral", val_st),
            Paragraph("<b>INDICACIÓN:</b> Epilepsia mioclónica", val_st),
        ],
        [
            Paragraph("<b>FECHAS:</b> 20-OCT-2025 al 11-NOV-2025", val_st),
            Paragraph("<b>LOTE:</b> Lote #LM-9941 (Caducidad: 05/2027)", val_st),
            Paragraph("<b>MEDIDA:</b> [ X ] Retirada definitiva", val_st),
        ]
    ]
    t_c = Table(c_data, colWidths=[200, 170, 170], style=[
        ('GRID', (0,0), (-1,-1), 0.75, colors.black),
        ('TOPPADDING', (0,0), (-1,-1), 3), ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 4), ('RIGHTPADDING', (0,0), (-1,-1), 4)
    ])
    story.append(t_c)
    story.append(Spacer(1, 4))
    
    # Section D: Notificador
    story.append(Paragraph("<b>D. DATOS DEL PROFESIONAL NOTIFICADOR</b>", sec_st))
    d_text = (
        "<b>NOMBRE:</b> Dra. Elena Morales &nbsp;|&nbsp; <b>PROFESIÓN:</b> Médico Especialista (Dermatología)<br/>"
        "<b>CENTRO SANITARIO:</b> Hospital Universitario La Paz — Servicio de Dermatología<br/>"
        "Paseo de la Castellana 261, 28046 Madrid, España | Tel: +34 91 555 0244 | Email: emorales@hospitallapaz.es"
    )
    t_d = Table([[Paragraph(d_text, val_st)]], colWidths=[540], style=[
        ('GRID', (0,0), (-1,-1), 0.75, colors.black),
        ('TOPPADDING', (0,0), (-1,-1), 3), ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 4), ('RIGHTPADDING', (0,0), (-1,-1), 4)
    ])
    story.append(t_d)
    
    doc.build(story)
    print(f"[OK] Generated Case 05 Spanish PDF: {pdf_path}")

# -------------------------------------------------------------
# 2. GENERATE CASE 06 PDF: FDA Form 3500A Follow-Up
# -------------------------------------------------------------
def build_case_06_followup_pdf(pdf_path: str):
    doc = SimpleDocTemplate(pdf_path, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    
    title_st = ParagraphStyle('FdaTitle', fontName='Helvetica-Bold', fontSize=10, leading=12, alignment=TA_CENTER)
    sub_st = ParagraphStyle('FdaSub', fontName='Helvetica', fontSize=7.5, leading=9.5, alignment=TA_CENTER)
    sec_st = ParagraphStyle('FdaSec', fontName='Helvetica-Bold', fontSize=8, leading=10)
    val_st = ParagraphStyle('FdaVal', fontName='Helvetica', fontSize=7.5, leading=9.5)
    
    story = [
        Paragraph("DEPARTMENT OF HEALTH AND HUMAN SERVICES — FOOD AND DRUG ADMINISTRATION", sub_st),
        Paragraph("MEDWATCH: FORM FDA 3500A (10/15) — MANDATORY ADVERSE EVENT REPORTING", title_st),
        Paragraph("<b>FOLLOW-UP REPORT #1 (CLINICAL RESOLUTION & DECHALLENGE CONFIRMATION)</b>", ParagraphStyle('FCode', fontName='Helvetica-Bold', fontSize=8.5, leading=10, alignment=TA_CENTER)),
        Paragraph("Original Case Reference: CR-2025-US-00744 &nbsp;|&nbsp; OMB Control No. 0910-0291", sub_st),
        Spacer(1, 4),
        Paragraph("<b>SECTION A: PATIENT IDENTIFIER</b>", sec_st)
    ]
    
    a_row = [
        Paragraph("<b>1. PATIENT IDENTIFIER:</b> D.M. (David Miller)", val_st),
        Paragraph("<b>2. AGE:</b> 52 YRS", val_st),
        Paragraph("<b>2a. DOB:</b> 11-FEB-1973", val_st),
        Paragraph("<b>3. SEX:</b> MALE", val_st),
        Paragraph("<b>4. WEIGHT:</b> 79 kg", val_st),
    ]
    t_a = Table([a_row], colWidths=[160, 80, 100, 70, 130], style=[
        ('GRID', (0,0), (-1,-1), 0.75, colors.black),
        ('TOPPADDING', (0,0), (-1,-1), 3), ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 4), ('RIGHTPADDING', (0,0), (-1,-1), 4)
    ])
    story.append(t_a)
    story.append(Spacer(1, 4))
    
    # Section B: Adverse Event Resolution
    story.append(Paragraph("<b>SECTION B: FOLLOW-UP EVENT DESCRIPTION & CLINICAL RESOLUTION</b>", sec_st))
    b_text = (
        "<b>FOLLOW-UP CLINICAL COURSE (14-DAY POST-DISCONTINUATION REVIEW):</b><br/>"
        "Initial report dated 02-NOV-2025 documented a witnessed generalized tonic-clonic seizure occurring 48 hours following "
        "rapid titration of Neuroval (neuroval hydrochloride) from 200 mg to 400 mg daily for neuropathic pain. "
        "Patient was admitted emergently to Columbia University Neurological ICU on 02-NOV-2025.<br/><br/>"
        "<b>DECHALLENGE CONFIRMATION:</b> Neuroval was permanently withdrawn on 02-NOV-2025. Follow-up evaluation on 16-NOV-2025 "
        "confirms the patient has remained entirely seizure-free for 14 consecutive days without requiring ongoing anticonvulsant therapy. "
        "Repeat 24-hour ambulatory video EEG completed on 14-NOV-2025 demonstrated normalization of cerebral background activity with zero "
        "epileptiform spike-wave discharges. Brain MRI with contrast showed no structural epileptogenic focus. "
        "<b>Final Case Outcome: FULLY RECOVERED / RESOLVED. Causality: Probable related to drug exposure.</b>"
    )
    t_b = Table([[Paragraph(b_text, val_st)]], colWidths=[540], style=[
        ('GRID', (0,0), (-1,-1), 0.75, colors.black),
        ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 4), ('RIGHTPADDING', (0,0), (-1,-1), 4)
    ])
    story.append(t_b)
    story.append(Spacer(1, 4))
    
    # Section C: Suspect Product
    story.append(Paragraph("<b>SECTION C: SUSPECT PRODUCT DETAILS</b>", sec_st))
    c_data = [
        [
            Paragraph("<b>PRODUCT:</b> Neuroval (neuroval HCl) 200mg/400mg", val_st),
            Paragraph("<b>DOSE:</b> Titrated to 400 mg PO QD", val_st),
            Paragraph("<b>LOT #:</b> Lot #NV-2025-110 (Exp 09/27)", val_st),
        ],
        [
            Paragraph("<b>THERAPY DATES:</b> 15-OCT-2025 to 02-NOV-2025", val_st),
            Paragraph("<b>DECHALLENGE:</b> [ X ] YES — Event abated after withdrawal", val_st),
            Paragraph("<b>RECHALLENGE:</b> [ X ] NOT DONE", val_st),
        ]
    ]
    t_c = Table(c_data, colWidths=[200, 180, 160], style=[
        ('GRID', (0,0), (-1,-1), 0.75, colors.black),
        ('TOPPADDING', (0,0), (-1,-1), 3), ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 4), ('RIGHTPADDING', (0,0), (-1,-1), 4)
    ])
    story.append(t_c)
    story.append(Spacer(1, 4))
    
    # Section E: Reporter
    story.append(Paragraph("<b>SECTION E: INITIAL / FOLLOW-UP REPORTER</b>", sec_st))
    e_text = (
        "<b>REPORTER:</b> Dr. Richard Vance, MD, PhD (Attending Neurologist)<br/>"
        "Department of Neurology, Columbia University Irving Medical Center<br/>"
        "710 W 168th St, New York, NY 10032 | Tel: (212) 555-0199 | Email: rvance@columbia-neurology.org"
    )
    t_e = Table([[Paragraph(e_text, val_st)]], colWidths=[540], style=[
        ('GRID', (0,0), (-1,-1), 0.75, colors.black),
        ('TOPPADDING', (0,0), (-1,-1), 3), ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 4), ('RIGHTPADDING', (0,0), (-1,-1), 4)
    ])
    story.append(t_e)
    
    doc.build(story)
    print(f"[OK] Generated Case 06 Follow-Up PDF: {pdf_path}")

# -------------------------------------------------------------
# 3. GENERATE CASE 07 PDF: Hospital Pharmacy Quality Defect Form
# -------------------------------------------------------------
def build_case_07_pqc_pdf(pdf_path: str):
    doc = SimpleDocTemplate(pdf_path, pagesize=letter, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    
    title_st = ParagraphStyle('PqcTitle', fontName='Helvetica-Bold', fontSize=11, leading=13, alignment=TA_CENTER)
    sub_st = ParagraphStyle('PqcSub', fontName='Helvetica', fontSize=8, leading=10, alignment=TA_CENTER)
    sec_st = ParagraphStyle('PqcSec', fontName='Helvetica-Bold', fontSize=8, leading=10)
    val_st = ParagraphStyle('PqcVal', fontName='Helvetica', fontSize=7.5, leading=9.5)
    
    story = [
        Paragraph("METROHEALTH MEDICAL CENTER — CENTRAL PHARMACY OPERATIONS", sub_st),
        Paragraph("PHARMACEUTICAL PRODUCT QUALITY COMPLAINT & DEFECT LOG", title_st),
        Paragraph("Standard Operating Procedure QA-PHARM-402 — Mandatory Supplier Incident Notification", sub_st),
        Spacer(1, 4),
        Paragraph("<b>1. COMPLAINT & PRODUCT IDENTIFICATION</b>", sec_st)
    ]
    
    p1 = [
        [
            Paragraph("<b>COMPLAINT ID:</b> PQC-MH-2025-088", val_st),
            Paragraph("<b>DATE LOGGED:</b> 17-NOV-2025", val_st),
            Paragraph("<b>DISCOVERY AREA:</b> Central Inpatient Unit-Dose Packager", val_st),
        ],
        [
            Paragraph("<b>PRODUCT NAME:</b> Cardioril 10mg Film-Coated Tablets", val_st),
            Paragraph("<b>LOT / BATCH:</b> Lot #BL-8802", ParagraphStyle('PqcLot', fontName='Helvetica-Bold', fontSize=7.5)),
            Paragraph("<b>EXPIRATION DATE:</b> 11/2026", val_st),
        ],
        [
            Paragraph("<b>PACKAGE TYPE:</b> 10-tablet push-through blister cards", val_st),
            Paragraph("<b>QUANTITY AFFECTED:</b> 12 cartons (360 strips / 3,600 tablets)", val_st),
            Paragraph("<b>DISPOSITION:</b> [ X ] 100% Stock Quarantined in Vault", val_st),
        ]
    ]
    t_p1 = Table(p1, colWidths=[180, 180, 180], style=[
        ('GRID', (0,0), (-1,-1), 0.75, colors.black),
        ('TOPPADDING', (0,0), (-1,-1), 3), ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 4), ('RIGHTPADDING', (0,0), (-1,-1), 4)
    ])
    story.append(t_p1)
    story.append(Spacer(1, 4))
    
    # Section 2: Defect Description
    story.append(Paragraph("<b>2. DEFECT INVESTIGATION & PHYSICAL FINDINGS</b>", sec_st))
    def_text = (
        "<b>DEFECT CATEGORY:</b> Packaging Integrity Failure & Chemical Oxidation / Degradation.<br/>"
        "<b>DETAILED DESCRIPTION:</b> During automated inventory intake inspection, pharmacy technicians noted widespread packaging "
        "seal failures in Lot #BL-8802. The aluminum lidding foil was unsealed and peeling away from the clear PVC/PVDC thermoformed cavities "
        "along the top margin of multiple blister strips. Enclosed 10mg tablets exposed to ambient humidity exhibited severe surface degradation: "
        "dark yellowish-brown speckling/oxidation, softening, edge chipping, and friability breakdown.<br/><br/>"
        "<b>PATIENT IMPACT ASSESSMENT:</b><br/>"
        "• Were any affected units dispensed to patients or wards? <b>NO (Zero patient exposure)</b>.<br/>"
        "• Adverse clinical reactions reported: <b>NONE / NOT APPLICABLE</b>.<br/>"
        "• Immediate Corrective Action: All 12 wholesale boxes immediately placed in locked quarantine under Quarantine Seal #Q-2025-094. "
        "Manufacturer alert dispatched requesting immediate replacement and return authorization."
    )
    t_def = Table([[Paragraph(def_text, val_st)]], colWidths=[540], style=[
        ('GRID', (0,0), (-1,-1), 0.75, colors.black),
        ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 4), ('RIGHTPADDING', (0,0), (-1,-1), 4)
    ])
    story.append(t_def)
    story.append(Spacer(1, 4))
    
    # Section 3: Reporter Information
    story.append(Paragraph("<b>3. COMPLAINANT / PHARMACY CONTACT</b>", sec_st))
    rep_text = (
        "<b>COMPLAINANT:</b> Robert Vance, PharmD, BCPS (Director of Pharmacy Operations)<br/>"
        "MetroHealth Medical Center — Department of Pharmacy<br/>"
        "2500 MetroHealth Dr, Chicago, IL 60609 | Tel: (312) 555-0140 | Email: rvance@metrohealth-pharmacy.org"
    )
    t_rep = Table([[Paragraph(rep_text, val_st)]], colWidths=[540], style=[
        ('GRID', (0,0), (-1,-1), 0.75, colors.black),
        ('TOPPADDING', (0,0), (-1,-1), 3), ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 4), ('RIGHTPADDING', (0,0), (-1,-1), 4)
    ])
    story.append(t_rep)
    
    doc.build(story)
    print(f"[OK] Generated Case 07 PQC PDF: {pdf_path}")

# -------------------------------------------------------------
# 4. COMPILE ALL 10 EMAILS
# -------------------------------------------------------------
def compile_all_ten_emails():
    # PDF references
    pdf_01 = os.path.join(PDF_DIGITAL, "cioms_form_MK_Cardioril.pdf")
    pdf_02 = os.path.join(BASE_DIR, "pdfs", "scanned_handwritten", "urgent_care_intake_handwritten.pdf")
    pdf_04 = os.path.join(PDF_PQC, "vial_contamination_sepsis.pdf")
    pdf_05 = os.path.join(PDF_NON_ENG, "notificacion_ram_madrid.pdf")
    pdf_06 = os.path.join(PDF_DIGITAL, "fda_medwatch_followup.pdf")
    pdf_07 = os.path.join(PDF_PQC, "packaging_defect_report.pdf")
    
    # Build PDFs 05, 06, 07
    build_case_05_spanish_pdf(pdf_05)
    build_case_06_followup_pdf(pdf_06)
    build_case_07_pqc_pdf(pdf_07)
    
    # Email 05
    eml_05 = os.path.join(EMAIL_DIR, "email_05.eml")
    msg_05 = MIMEMultipart('mixed')
    msg_05['From'] = '"Dra. Elena Morales" <emorales@hospitallapaz.es>'
    msg_05['To'] = '"Clinevo Safety Mailbox" <drugsafety@clinevotech.com>'
    msg_05['Date'] = 'Sat, 15 Nov 2025 11:20:00 +0100'
    msg_05['Subject'] = 'URGENTE: Notificación de Reacción Adversa Grave - Necrólisis Epidérmica Tóxica con Lamotrigina (Pt C.O.)'
    msg_05['Message-ID'] = '<20251115.112000.emorales@hospitallapaz.es>'
    msg_05['X-Priority'] = '1'
    msg_05.attach(MIMEText(
        "Estimado Departamento de Farmacovigilancia,\n\n"
        "Remito notificación urgente de una reacción adversa grave con desenlace potencialmente mortal "
        "en una paciente de 29 años (Carmen Ortiz, C.O.) tratada con Lamotrigina 100 mg/día por epilepsia mioclónica.\n\n"
        "La paciente ha desarrollado un cuadro clínico compatible con Necrólisis Epidérmica Tóxica (Síndrome de Lyell) "
        "con desprendimiento dermoepidérmico superior al 35% de la superficie corporal y afectación de mucosas oral y conjuntival. "
        "Ha sido ingresada de urgencia en la Unidad de Quemados Críticos del Hospital Universitario La Paz.\n\n"
        "El fármaco sospechoso ha sido suspendido de forma inmediata. Adjunto el formulario oficial de notificación de la AEMPS "
        "debidamente cumplimentado.\n\n"
        "Atentamente,\n"
        "Dra. Elena Morales, FEA Dermatología\n"
        "Hospital Universitario La Paz, Paseo de la Castellana 261, 28046 Madrid\n"
        "Tel: +34 91 555 0244 | Email: emorales@hospitallapaz.es\n", 'plain', 'utf-8'
    ))
    with open(pdf_05, 'rb') as f:
        part = MIMEApplication(f.read(), _subtype='pdf')
        part.add_header('Content-Disposition', 'attachment', filename='notificacion_ram_madrid.pdf')
        msg_05.attach(part)
    with open(eml_05, 'wb') as f:
        f.write(msg_05.as_bytes())
    print("[OK] Generated email_05.eml")

    # Email 06
    eml_06 = os.path.join(EMAIL_DIR, "email_06.eml")
    msg_06 = MIMEMultipart('mixed')
    msg_06['From'] = '"Dr. Richard Vance, MD" <rvance@columbia-neurology.org>'
    msg_06['To'] = '"Clinevo Safety Mailbox" <drugsafety@clinevotech.com>'
    msg_06['Date'] = 'Sun, 16 Nov 2025 16:05:12 -0500'
    msg_06['Subject'] = 'FOLLOW-UP REPORT #1: Case Ref CR-2025-US-00744 - Seizure Resolution s/p Neuroval Discontinuation'
    msg_06['Message-ID'] = '<20251116.160512.rvance@columbia-neurology.org>'
    msg_06.attach(MIMEText(
        "Dear Pharmacovigilance Team,\n\n"
        "This is follow-up report #1 to our initial safety report (Case Ref: CR-2025-US-00744) regarding patient "
        "David Miller (52yo male) who experienced a generalized tonic-clonic seizure 48 hours following dose escalation "
        "of Neuroval to 400 mg daily.\n\n"
        "I am pleased to report that following complete discontinuation of Neuroval on November 2nd, the patient has remained "
        "completely seizure-free for 14 consecutive days. Repeat 24-hour video EEG showed normalization of background rhythms "
        "without epileptiform discharges. Positive de-challenge is clinically confirmed.\n\n"
        "Attached is the updated FDA Form 3500A with Section B and C marked for follow-up resolution.\n\n"
        "Sincerely,\n"
        "Dr. Richard Vance, MD\n"
        "Department of Neurology, Columbia University Medical Center\n"
        "New York, NY 10032 | Tel: (212) 555-0199\n", 'plain', 'utf-8'
    ))
    with open(pdf_06, 'rb') as f:
        part = MIMEApplication(f.read(), _subtype='pdf')
        part.add_header('Content-Disposition', 'attachment', filename='fda_medwatch_followup.pdf')
        msg_06.attach(part)
    with open(eml_06, 'wb') as f:
        f.write(msg_06.as_bytes())
    print("[OK] Generated email_06.eml")

    # Email 07
    eml_07 = os.path.join(EMAIL_DIR, "email_07.eml")
    msg_07 = MIMEMultipart('mixed')
    msg_07['From'] = '"Robert Vance, PharmD" <rvance@metrohealth-pharmacy.org>'
    msg_07['To'] = '"Clinevo Product Quality Department" <qualitycomplaints@clinevotech.com>'
    msg_07['Date'] = 'Mon, 17 Nov 2025 08:30:00 -0600'
    msg_07['Subject'] = 'PRODUCT QUALITY COMPLAINT: Compromised Blister Foil & Oxidized Tablets (Lot #BL-8802)'
    msg_07['Message-ID'] = '<20251117.083000.rvance@metrohealth-pharmacy.org>'
    msg_07.attach(MIMEText(
        "To Quality Assurance & Complaints Investigation,\n\n"
        "Our central pharmacy is filing an official Product Quality Complaint regarding Cardioril 10mg blister packs, "
        "Lot #BL-8802, Expiration Date: 11/2026.\n\n"
        "During routine unit-dose dispensing, pharmacy technicians identified multiple cartons where the aluminum foil backing "
        "was unsealed and peeling away from the PVC blister cavities. The enclosed tablets display dark discoloration, surface "
        "oxidation, and severe crumbling.\n\n"
        "No medication from this shipment was dispensed to patients; zero adverse events have occurred. "
        "All 12 boxes (360 blister strips) from Lot #BL-8802 have been quarantined in our pharmacy quarantine cage.\n\n"
        "Please find our internal Pharmacy Defect Inspection Form attached. We request immediate replacement and return shipping instructions.\n\n"
        "Robert Vance, PharmD, BCPS\n"
        "Director of Pharmacy Operations, MetroHealth Medical Center\n"
        "Tel: (312) 555-0140 | Email: rvance@metrohealth-pharmacy.org\n", 'plain', 'utf-8'
    ))
    with open(pdf_07, 'rb') as f:
        part = MIMEApplication(f.read(), _subtype='pdf')
        part.add_header('Content-Disposition', 'attachment', filename='packaging_defect_report.pdf')
        msg_07.attach(part)
    with open(eml_07, 'wb') as f:
        f.write(msg_07.as_bytes())
    print("[OK] Generated email_07.eml")

    # Email 08 (Pure Text - PQC Counterfeit)
    eml_08 = os.path.join(EMAIL_DIR, "email_08.eml")
    msg_08 = MIMEText(
        "Dear Quality Complaints Team,\n\n"
        "I am writing as the Pharmacist-in-Charge at Apex Care Pharmacy in Boston, MA. "
        "We received a delivery yesterday from a secondary wholesaler containing 10 bottles of Lipocur 20mg tablets (Lot #LP-44109).\n\n"
        "Upon physical inspection, we strongly suspect counterfeit or tampered packaging:\n"
        "1. The bottle neck lacks the standard induction inner heat-seal.\n"
        "2. The expiration date typography on the bottle label does not match our usual commercial stock (font is misaligned and lacks the 2D data matrix barcode).\n"
        "3. The bottle cap color is a noticeably darker shade of blue than official product packaging.\n\n"
        "We have quarantined all 10 bottles in our pharmacy vault. No bottles have been sold to consumers, and no patients have ingested this stock. "
        "Please advise on chain-of-custody pickup for laboratory authentication.\n\n"
        "Karen Patel, RPh\n"
        "Apex Care Pharmacy #104, Boston, MA\n"
        "Tel: (617) 555-0166 | Email: kpatel@apex-care-pharmacy.com\n", 'plain', 'utf-8'
    )
    msg_08['From'] = '"Karen Patel, RPh" <kpatel@apex-care-pharmacy.com>'
    msg_08['To'] = '"Clinevo Product Quality Department" <qualitycomplaints@clinevotech.com>'
    msg_08['Date'] = 'Tue, 18 Nov 2025 10:15:45 -0500'
    msg_08['Subject'] = 'Urgent Quality Notice: Suspected Counterfeit Packaging - Lipocur 20mg (Lot #LP-44109)'
    msg_08['Message-ID'] = '<20251118.101545.kpatel@apex-care-pharmacy.com>'
    with open(eml_08, 'wb') as f:
        f.write(msg_08.as_bytes())
    print("[OK] Generated email_08.eml")

    # Email 09 (Pure Text - MI Feeding Tube)
    eml_09 = os.path.join(EMAIL_DIR, "email_09.eml")
    msg_09 = MIMEText(
        "Dear Medical Information Department,\n\n"
        "I am a clinical oncology pharmacist at UCSF Medical Center caring for an elderly patient with severe dysphagia "
        "who has an active nasogastric (NG) feeding tube in place.\n\n"
        "The patient has been prescribed Corzapan 10mg once daily for chronic hypertension. The package insert indicates "
        "film-coated tablets but does not explicitly state whether the tablets can be crushed and suspended in sterile water "
        "for enteral feeding tube delivery without altering bioavailability or causing tube occlusion.\n\n"
        "Could your medical affairs team please provide any pharmacokinetic or stability data regarding:\n"
        "1. Crushing Corzapan 10mg tablets for enteral administration.\n"
        "2. Potential adsorption of the active substance to polyurethane enteral feeding tubes.\n"
        "3. Co-administration with enteral nutrition formulas.\n\n"
        "There is currently no patient adverse event or product defect. This is purely a prospective clinical inquiry.\n\n"
        "Best regards,\n"
        "David Wu, PharmD, BCPS\n"
        "Clinical Pharmacy Specialist, UCSF Health\n"
        "San Francisco, CA | Tel: (415) 555-0198\n", 'plain', 'utf-8'
    )
    msg_09['From'] = '"David Wu, BCPS" <david.wu@ucsf-clinical.edu>'
    msg_09['To'] = '"Clinevo Medical Information Department" <medinfo@clinevotech.com>'
    msg_09['Date'] = 'Wed, 19 Nov 2025 13:40:00 -0800'
    msg_09['Subject'] = 'Medical Information Request: Can Corzapan 10mg tablets be crushed for NG-tube administration?'
    msg_09['Message-ID'] = '<20251119.134000.dwu@ucsf-clinical.edu>'
    with open(eml_09, 'wb') as f:
        f.write(msg_09.as_bytes())
    print("[OK] Generated email_09.eml")

    # Email 10 (Pure Text - Spam / Marketing)
    eml_10 = os.path.join(EMAIL_DIR, "email_10.eml")
    msg_10 = MIMEText(
        "Join 500+ global safety leaders, regulatory directors, and AI pioneers in Boston, MA on March 24–26, 2026!\n\n"
        "Keynote sessions include:\n"
        "• Generative AI & LLMs in ICSR Intake Automation\n"
        "• GVP Module VI Inspection Readiness in 2026\n"
        "• Automating Literature Screening with Multimodal AI\n"
        "• Real-World Evidence & Signal Detection Case Studies\n\n"
        "Register before December 15th to save $400 with our Early Bird Discount code: SAFETYAI2026.\n"
        "Group discounts available for teams of 3 or more.\n\n"
        "Click here to reserve your delegate pass: https://www.pharmasummit-global2026.com/register\n"
        "To unsubscribe from future event notifications, click here.\n", 'plain', 'utf-8'
    )
    msg_10['From'] = '"PharmaTech Global Summit" <events@pharmasummit-global2026.com>'
    msg_10['To'] = '"Drug Safety Department" <drugsafety@clinevotech.com>'
    msg_10['Date'] = 'Thu, 20 Nov 2025 08:00:00 +0000'
    msg_10['Subject'] = 'Early Bird Registration Open: 14th Annual Global AI in Pharmacovigilance & Drug Safety Summit'
    msg_10['Message-ID'] = '<20251120.080000.events@pharmasummit-global2026.com>'
    with open(eml_10, 'wb') as f:
        f.write(msg_10.as_bytes())
    print("[OK] Generated email_10.eml")

if __name__ == '__main__':
    compile_all_ten_emails()
