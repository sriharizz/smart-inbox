"""
Generate Case 04:
- Multi-Bucket Report: Both Safety Report (ICSR) AND Quality Complaint (PQC)
- Digital PDF containing a meaningful image (photograph of contaminated vial with particulate & cracked seal)
- Valid RFC 5322 MIME .eml email from ICU Director Dr. Robert Lang
- Tests:
  1. Multi-label classification (tags both ICSR and PQC with confidence & reasons)
  2. Meaningful image description and flagging for human review
  3. Quality complaint fields: Product (Cefatox), Lot # (CX5483), Defect (cracked stopper, particulate), Photo mentioned (YES)
  4. Safety fields: Patient (71M), Drug (Cefatox), Reaction (Septic shock / bacteremia), Seriousness (Life-threatening / ICU).
"""

import os
import shutil
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

def generate_case_04(src_photo_path: str, dest_dir: str, email_dir: str):
    os.makedirs(dest_dir, exist_ok=True)
    os.makedirs(email_dir, exist_ok=True)
    
    # 1. Copy photo
    dest_photo = os.path.join(dest_dir, 'contaminated_vial_photo.jpg')
    shutil.copy2(src_photo_path, dest_photo)
    print(f"[OK] Copied defect photo to: {dest_photo}")
    
    # 2. Build PDF Incident Report
    pdf_out = os.path.join(dest_dir, 'vial_contamination_sepsis.pdf')
    doc = SimpleDocTemplate(
        pdf_out,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#7F1D1D') # Dark Red
    )
    sub_style = ParagraphStyle(
        'DocSub',
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#475569')
    )
    sec_style = ParagraphStyle(
        'SecHead',
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=colors.HexColor('#0F172A')
    )
    body_style = ParagraphStyle(
        'Body',
        fontName='Helvetica',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor('#1E293B')
    )
    bold_style = ParagraphStyle(
        'Bold',
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor('#1E293B')
    )
    
    story = []
    
    # Header
    story.append(Paragraph("NORTHWESTERN MEMORIAL HOSPITAL — MEDICAL INCIDENT REPORT", title_style))
    story.append(Paragraph("COMBINED PRODUCT QUALITY COMPLAINT (PQC) & SERIOUS ADVERSE EVENT (SAE)", sub_style))
    story.append(Spacer(1, 8))
    
    # Case Overview Grid
    overview_data = [
        [
            Paragraph("<b>REPORT DATE:</b> 14-NOV-2025", body_style),
            Paragraph("<b>INCIDENT ID:</b> NMH-ICU-2025-449", body_style),
            Paragraph("<b>DEPT:</b> Medical Intensive Care Unit", body_style),
            Paragraph("<b>STATUS:</b> Critical Alert / Quarantine", ParagraphStyle('Alert', fontName='Helvetica-Bold', fontSize=7.5, textColor=colors.HexColor('#DC2626'))),
        ],
        [
            Paragraph("<b>PATIENT:</b> Arthur Pendelton", body_style),
            Paragraph("<b>MRN / DOB:</b> 19-AUG-1954 (Age: 71)", body_style),
            Paragraph("<b>SEX:</b> Male (Weight: 74 kg)", body_style),
            Paragraph("<b>PRIMARY ADMISSION:</b> Post-op pneumonia", body_style),
        ]
    ]
    t_over = Table(overview_data, colWidths=[135, 135, 135, 135])
    t_over.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#94A3B8')),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#FEF2F2')),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_over)
    story.append(Spacer(1, 6))
    
    # Product Quality Defect Section
    story.append(Paragraph("<b>PART A: PRODUCT QUALITY COMPLAINT (PQC) INVESTIGATION</b>", sec_style))
    story.append(Spacer(1, 3))
    
    pqc_data = [
        [
            Paragraph("<b>PRODUCT NAME:</b> Cefatox (cefatoxime sodium) 1g for Injection", body_style),
            Paragraph("<b>LOT / BATCH:</b> Lot #CX54831", ParagraphStyle('Lot', fontName='Helvetica-Bold', fontSize=7.5, textColor=colors.HexColor('#B91C1C'))),
            Paragraph("<b>EXPIRY:</b> 08/2025", body_style),
        ],
        [
            Paragraph("<b>DEFECT TYPE:</b> Packaging Compromise & Particulate Contamination", body_style),
            Paragraph("<b>SAMPLE RETAINED?</b> YES (In Pharmacy Safe)", body_style),
            Paragraph("<b>PHOTO INCLUDED:</b> YES (See Figure 1 below)", ParagraphStyle('Photo', fontName='Helvetica-Bold', fontSize=7.5, textColor=colors.HexColor('#1D4ED8'))),
        ]
    ]
    t_pqc = Table(pqc_data, colWidths=[240, 150, 150])
    t_pqc.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#94A3B8')),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_pqc)
    story.append(Spacer(1, 6))
    
    # Defect Photo & Description (Directly tests Section 3.B Meaningful Image Requirement)
    img_element = RLImage(dest_photo, width=2.4*inch, height=1.8*inch)
    defect_desc = (
        "<b>FIGURE 1: PHYSICAL EVIDENCE PHOTO (QUARANTINED VIAL):</b><br/>"
        "Visual examination of vial (Lot #CX54831, Exp 08/25) demonstrates a ruptured/cracked aluminum crimp seal "
        "at the collar of the blue rubber stopper. Upon reconstitution with 20mL sterile water, prominent black/brown "
        "foreign particulate matter and suspended flakes were immediately observed floating throughout the liquid. "
        "Container integrity was compromised prior to unboxing. Entire hospital supply of Lot #CX54831 (48 vials) "
        "has been immediately placed in pharmacy quarantine pending manufacturer investigation.<br/><br/>"
        "<i>[AI Document Flag: Meaningful Defect Photo Detected — Requires Quality Reviewer Confirmation]</i>"
    )
    t_img = Table([
        [img_element, Paragraph(defect_desc, body_style)]
    ], colWidths=[185, 355])
    t_img.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#DC2626')),
        ('BACKGROUND', (0,0), (-1,-1), colors.white),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_img)
    story.append(Spacer(1, 6))
    
    # Clinical Adverse Event Section (The ICSR half of the case)
    story.append(Paragraph("<b>PART B: INDIVIDUAL CASE SAFETY REPORT (ICSR) CLINICAL NARRATIVE</b>", sec_style))
    story.append(Spacer(1, 3))
    
    clinical_narrative = (
        "At 11:30 on 14-Nov-2025, patient Arthur Pendelton (71M) in Bed ICU-04 was administered approximately 35mL of "
        "reconstituted Cefatox 1g IV piggyback prior to the bedside nurse noticing cloudiness and black particles inside the "
        "infusion bag. Infusion was halted immediately. Within 45 minutes of administration, the patient experienced sudden "
        "rigors, temperature spike to 39.8°C (103.6°F), severe rigors, and acute drop in mean arterial pressure (BP 72/40 mmHg). "
        "Diagnosis: Severe acute bacteremia and septic shock secondary to contaminated intravenous infusion.<br/><br/>"
        "<b>Emergency Resuscitation:</b> Central line placed, norepinephrine infusion initiated at 0.12 mcg/kg/min to maintain MAP &gt; 65 mmHg, "
        "intravenous vancomycin and meropenem commenced empirically. Blood cultures drawn from line and periphery.<br/>"
        "<b>Outcome / Severity:</b> Life-threatening septic shock requiring intensive vasoactive support and prolonged ICU stay. Patient remains in critical condition."
    )
    t_clin = Table([[Paragraph(clinical_narrative, body_style)]], colWidths=[540])
    t_clin.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#94A3B8')),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_clin)
    story.append(Spacer(1, 6))
    
    # Reporter Details
    reporter_text = (
        "<b>REPORTING CLINICIAN:</b> Dr. Robert Lang, MD, FCCM &nbsp;|&nbsp; <b>TITLE:</b> Director of Critical Care Medicine<br/>"
        "<b>HOSPITAL:</b> Northwestern Memorial Hospital, 251 E Huron St, Chicago, IL 60611 &nbsp;|&nbsp; "
        "<b>PHONE:</b> (312) 555-0320 &nbsp;|&nbsp; <b>EMAIL:</b> rlang@nmh-icu.org"
    )
    t_rep = Table([[Paragraph(reporter_text, body_style)]], colWidths=[540])
    t_rep.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#94A3B8')),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#EDF2F7')),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_rep)
    
    doc.build(story)
    print(f"[OK] Generated Case 04 PDF: {pdf_out}")
    
    # 3. Build Email 04
    eml_out = os.path.join(email_dir, 'email_04.eml')
    msg = MIMEMultipart('mixed')
    msg['From'] = '"Dr. Robert Lang, MD" <rlang@nmh-icu.org>'
    msg['To'] = '"Clinevo Safety & Quality Intake" <drugsafety@clinevotech.com>'
    msg['Date'] = 'Fri, 14 Nov 2025 14:10:00 -0600'
    msg['Subject'] = 'CRITICAL ALERT: Sepsis caused by Contaminated Cefatox 1g Vial (Lot #CX54831) - Photo Attached'
    msg['Message-ID'] = '<20251114.141000.rlang@nmh-icu.org>'
    msg['X-Priority'] = '1'
    
    body_text = (
        "URGENT: TO PHARMACOVIGILANCE AND QUALITY COMPLAINTS DEPARTMENTS,\n\n"
        "I am submitting an emergency dual-category report involving both an immediate Product Quality Complaint (PQC) "
        "and a life-threatening Serious Adverse Event (ICSR).\n\n"
        "Earlier today in our ICU, patient Arthur Pendelton (71yo male) developed septic shock and severe hypotension (BP 72/40) "
        "shortly after receiving an intravenous infusion of Cefatox 1g (cefatoxime sodium, Lot #CX54831, Exp 08/2025).\n\n"
        "Upon inspecting the medication vial, bedside staff discovered that the aluminum crimp collar on the rubber stopper was "
        "cracked open, and dark foreign particulate matter was visibly floating in the solution.\n\n"
        "We have quarantined all 48 remaining vials of Lot #CX54831 in our central pharmacy. The patient is currently on "
        "norepinephrine vasopressor support in critical condition.\n\n"
        "Attached is our formal incident investigation report containing high-resolution photographs of the defective vial and "
        "the patient's clinical resuscitation timeline.\n\n"
        "Sincerely,\n"
        "Robert Lang, MD, FCCM\n"
        "Director, Medical Intensive Care Unit\n"
        "Northwestern Memorial Hospital, Chicago, IL\n"
        "Tel: (312) 555-0320 | Email: rlang@nmh-icu.org\n"
    )
    msg.attach(MIMEText(body_text, 'plain', 'utf-8'))
    
    with open(pdf_out, 'rb') as f:
        pdf_part = MIMEApplication(f.read(), _subtype='pdf')
        pdf_part.add_header('Content-Disposition', 'attachment', filename='vial_contamination_sepsis.pdf')
        msg.attach(pdf_part)
        
    with open(eml_out, 'wb') as f:
        f.write(msg.as_bytes())
        
    print(f"[OK] Generated Case 04 Email: {eml_out}")

if __name__ == '__main__':
    src_photo = r'C:\Users\BTSRIHARI\.gemini\antigravity-ide\brain\c4b1c911-34dc-476f-8860-a648f92d7a93\contaminated_vial_photo_1788514940115.jpg'
    dest_dir = r'c:\projects\SmartInbox\test-data\pdfs\quality_complaints'
    email_dir = r'c:\projects\SmartInbox\test-data\emails'
    
    generate_case_04(src_photo, dest_dir, email_dir)
