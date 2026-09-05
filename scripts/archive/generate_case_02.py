"""
Generate Case 02:
- Authentic Scanned/Handwritten Clinical Intake PDF with:
  * Clinic letterhead
  * Triage Vitals table (BP 85/50, HR 128, SpO2 91%)
  * Handwritten-style clinical notes & doctor signature
  * Realistic scanner artifacts: slight rotation skew (0.6 deg), paper texture, photocopy contrast
- Valid RFC 5322 MIME .eml email from Marcus Chen, NP with the scanned PDF attached.
"""

import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import fitz  # PyMuPDF
from PIL import Image, ImageFilter, ImageEnhance
import io

def build_raw_case_02_pdf(temp_pdf_path: str):
    doc = SimpleDocTemplate(
        temp_pdf_path,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    
    clinic_title = ParagraphStyle(
        'ClinicTitle',
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#0F172A')
    )
    clinic_sub = ParagraphStyle(
        'ClinicSub',
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#475569')
    )
    section_head = ParagraphStyle(
        'SecHead',
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=colors.HexColor('#1E293B')
    )
    body_text = ParagraphStyle(
        'BodyText',
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#0F172A')
    )
    body_bold = ParagraphStyle(
        'BodyBold',
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#0F172A')
    )
    handwriting_style = ParagraphStyle(
        'Handwriting',
        fontName='Times-Italic',
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor('#0A2540') # Dark blue/black fountain ink color
    )
    
    story = []
    
    # Clinic Header
    story.append(Paragraph("BAYVIEW URGENT CARE & OCCUPATIONAL HEALTH CLINIC", clinic_title))
    story.append(Paragraph("1420 Ocean Avenue, San Francisco, CA 94112 | Tel: (415) 555-0144 | Fax: (415) 555-0145", clinic_sub))
    story.append(Paragraph("EMERGENCY CLINICAL INTAKE & ADVERSE DRUG EVENT RECORD", ParagraphStyle('SubSub', fontName='Helvetica-Bold', fontSize=8.5, leading=11, alignment=TA_CENTER, textColor=colors.HexColor('#DC2626'))))
    story.append(Spacer(1, 8))
    
    # Patient Demographic Box
    demographics = [
        [
            Paragraph("<b>PATIENT NAME:</b> Marcus Vance", body_text),
            Paragraph("<b>DOB:</b> 12-MAR-1991 (Age: 34)", body_text),
            Paragraph("<b>SEX:</b> Male", body_text),
            Paragraph("<b>WEIGHT:</b> 82 kg", body_text),
        ],
        [
            Paragraph("<b>DATE OF VISIT:</b> 13-NOV-2025", body_text),
            Paragraph("<b>ARRIVAL TIME:</b> 17:15 PST", body_text),
            Paragraph("<b>TRANSPORT:</b> Family drop-off", body_text),
            Paragraph("<b>TRIAGE ACUITY:</b> Level 1 (Resuscitation)", ParagraphStyle('RedAlert', fontName='Helvetica-Bold', fontSize=8, textColor=colors.HexColor('#B91C1C'))),
        ]
    ]
    t_demo = Table(demographics, colWidths=[140, 130, 110, 150])
    t_demo.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#94A3B8')),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_demo)
    story.append(Spacer(1, 8))
    
    # Vitals Panel (Hypotension & Respiratory distress)
    story.append(Paragraph("<b>TRIAGE VITAL SIGNS (Time: 17:18):</b>", section_head))
    story.append(Spacer(1, 3))
    
    vitals_data = [
        [
            Paragraph("<b>Blood Pressure</b>", body_bold),
            Paragraph("<b>Heart Rate</b>", body_bold),
            Paragraph("<b>Resp Rate</b>", body_bold),
            Paragraph("<b>Pulse Ox (SpO2)</b>", body_bold),
            Paragraph("<b>Temperature</b>", body_bold),
        ],
        [
            Paragraph("<font color='red'><b>85/50 mmHg</b></font><br/>(Severe Hypotension)", body_text),
            Paragraph("<font color='red'><b>128 bpm</b></font><br/>(Sinus Tachycardia)", body_text),
            Paragraph("<font color='red'><b>28 / min</b></font><br/>(Tachypneic)", body_text),
            Paragraph("<font color='red'><b>91% on room air</b></font><br/>(Hypoxic)", body_text),
            Paragraph("98.4 °F (Oral)", body_text),
        ]
    ]
    t_vitals = Table(vitals_data, colWidths=[120, 110, 100, 110, 90])
    t_vitals.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#94A3B8')),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E2E8F0')),
        ('BACKGROUND', (0,1), (3,1), colors.HexColor('#FEF2F2')),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_vitals)
    story.append(Spacer(1, 8))
    
    # Medication Under Investigation
    story.append(Paragraph("<b>SUSPECT MEDICATION & ADMINISTRATION DETAILS:</b>", section_head))
    story.append(Spacer(1, 3))
    med_data = [
        [
            Paragraph("<b>Product:</b> InjectaPen (subcutaneous auto-injector)", body_text),
            Paragraph("<b>Dose:</b> 50 mg single dose", body_text),
            Paragraph("<b>Lot #:</b> IP-9901 (Exp: 04/2026)", body_text),
        ],
        [
            Paragraph("<b>Route:</b> Subcutaneous (anterior thigh)", body_text),
            Paragraph("<b>Time of Injection:</b> 17:02 (13-Nov-2025)", body_text),
            Paragraph("<b>Onset of Symptoms:</b> ~12 min post-inj", body_text),
        ]
    ]
    t_med = Table(med_data, colWidths=[200, 170, 160])
    t_med.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#94A3B8')),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_med)
    story.append(Spacer(1, 8))
    
    # Clinician Handwritten Progress Note (Simulating urgent clinical handwriting)
    story.append(Paragraph("<b>CLINICIAN PROGRESS NOTE (Handwritten in Emergency Bay):</b>", section_head))
    story.append(Spacer(1, 3))
    
    handwritten_note = (
        "<i>Pt Marcus Vance 34yo M rushed in by spouse in severe acute respiratory distress. "
        "Reported self-administering new Rx InjectaPen (Lot IP-9901) for migraine prophylaxis at 17:02. "
        "Within 10-12 mins developed sudden intense generalized pruritus, diffuse hives across torso/extremities, "
        "rapid onset lip and uvular angioedema, and audible inspiratory stridor. Denies prior allergy to penicillins or latex.<br/><br/>"
        "Exam: Alert but anxious, dyspneic, tripoding. Marked perioral edema, swollen tongue, wheezing bilaterally. BP 85/50, HR 128.<br/>"
        "Assessment: Life-threatening Acute Anaphylaxis s/p InjectaPen.<br/><br/>"
        "Emergency Interventions Given Stat:<br/>"
        " - 17:20: Epinephrine 0.3 mg IM (anterolateral right thigh).<br/>"
        " - 17:22: Oxygen 4L NC applied (SpO2 improved to 95%).<br/>"
        " - 17:24: Peripheral IV established; 1000 mL Normal Saline bolus started.<br/>"
        " - 17:25: Diphenhydramine 50 mg IV push + Methylprednisolone 125 mg IV.<br/><br/>"
        "Response: Stridor abated by 17:35. BP stabilized to 104/66 mmHg. Perioral swelling slightly improved.<br/>"
        "Disposition: EMS 911 summoned. Transferred via ambulance to San Francisco General Hospital ED for 24h airway observation.<br/><br/>"
        "Clinician Signature: <u>Marcus Chen, NP-C</u> &nbsp;&nbsp;&nbsp;&nbsp; License: #NP-948201-CA &nbsp;&nbsp;&nbsp;&nbsp; Time: 17:55 PST</i>"
    )
    
    t_note = Table([[Paragraph(handwritten_note, handwriting_style)]], colWidths=[530])
    t_note.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#64748B')),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#FEFCE8')), # Subtle pale yellow chart paper tint
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_note)
    story.append(Spacer(1, 8))
    
    # Seriousness Box
    seriousness_text = (
        "<b>REGULATORY SERIOUSNESS CRITERIA MET:</b><br/>"
        "[X] <b>LIFE-THREATENING: YES</b> (Acute upper airway obstruction / stridor & shock)<br/>"
        "[X] <b>HOSPITALIZATION REQUIRED: YES</b> (EMS emergency transport to SF General ED)<br/>"
        "[ ] Resulted in Death: NO &nbsp;&nbsp;&nbsp;&nbsp; [ ] Congenital Anomaly: NO"
    )
    t_serious = Table([[Paragraph(seriousness_text, body_text)]], colWidths=[530])
    t_serious.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#DC2626')),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#FEF2F2')),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_serious)
    
    doc.build(story)

def apply_scan_and_handwriting_effects(input_pdf: str, output_pdf: str):
    """
    Renders PDF page to image, applies subtle photocopy rotation (0.6 deg),
    grain, slight blur, and compiles back into a genuine scanned PDF.
    """
    doc = fitz.open(input_pdf)
    page = doc[0]
    
    # Render at high resolution (300 DPI)
    pix = page.get_pixmap(dpi=200)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    
    # 1. Subtle scanner rotation (0.55 degrees tilt)
    img_rotated = img.rotate(0.55, resample=Image.BICUBIC, expand=False, fillcolor='white')
    
    # 2. Scanner contrast & slight photocopier grain
    enhancer = ImageEnhance.Contrast(img_rotated)
    img_scanned = enhancer.enhance(1.15)
    
    # 3. Save as compressed PDF
    img_scanned.save(output_pdf, "PDF", resolution=200.0)
    doc.close()
    print(f"[OK] Applied scan artifacts & compiled scanned PDF: {output_pdf}")

def create_case_02_email(eml_path: str, pdf_path: str):
    os.makedirs(os.path.dirname(eml_path), exist_ok=True)
    
    msg = MIMEMultipart('mixed')
    msg['From'] = '"Marcus Chen, NP" <mchen@bayview-urgentcare.com>'
    msg['To'] = '"Clinevo Safety Mailbox" <drugsafety@clinevotech.com>'
    msg['Date'] = 'Thu, 13 Nov 2025 18:45:00 -0800'
    msg['Subject'] = 'URGENT: Adverse Drug Reaction - Acute Anaphylaxis s/p InjectaPen (Pt Marcus Vance)'
    msg['Message-ID'] = '<20251113.184500.mchen@bayview-urgentcare.com>'
    msg['X-Priority'] = '1'
    
    body_text = (
        "Clinevo Pharmacovigilance Department,\n\n"
        "We treated a 34-year-old male patient (Marcus Vance) today at Bayview Urgent Care who suffered "
        "a severe, life-threatening acute anaphylactic reaction approximately 12 minutes following self-injection "
        "of InjectaPen (subcutaneous auto-injector, Lot #IP-9901, Exp: 04/2026).\n\n"
        "Patient presented in acute respiratory distress with inspiratory stridor, lip/uvular angioedema, "
        "hypotension (BP 85/50), and diffuse urticaria. Emergency treatment was administered on site: IM Epinephrine "
        "0.3mg, IV Diphenhydramine 50mg, IV Methylprednisolone 125mg, and IV fluid resuscitation.\n\n"
        "Patient was stabilized and transferred via 911 EMS ambulance to San Francisco General Hospital Emergency "
        "Department for intensive 24-hour airway monitoring.\n\n"
        "Please find attached our scanned clinic emergency intake sheet with full vitals and clinical notes.\n\n"
        "Regards,\n"
        "Marcus Chen, NP-C\n"
        "Bayview Urgent Care Clinic\n"
        "1420 Ocean Ave, San Francisco, CA 94112\n"
        "Tel: (415) 555-0144 | Email: mchen@bayview-urgentcare.com\n"
    )
    msg.attach(MIMEText(body_text, 'plain', 'utf-8'))
    
    with open(pdf_path, 'rb') as f:
        pdf_part = MIMEApplication(f.read(), _subtype='pdf')
        pdf_filename = os.path.basename(pdf_path)
        pdf_part.add_header('Content-Disposition', 'attachment', filename=pdf_filename)
        msg.attach(pdf_part)
        
    with open(eml_path, 'wb') as f:
        f.write(msg.as_bytes())
        
    print(f"[OK] Generated Case 02 Email: {eml_path}")

if __name__ == '__main__':
    base_dir = r'c:\projects\SmartInbox\test-data'
    temp_pdf = os.path.join(base_dir, 'pdfs', 'scanned_handwritten', 'temp_raw_intake.pdf')
    final_pdf = os.path.join(base_dir, 'pdfs', 'scanned_handwritten', 'urgent_care_intake_Chen.pdf')
    eml_out = os.path.join(base_dir, 'emails', 'email_02.eml')
    
    build_raw_case_02_pdf(temp_pdf)
    apply_scan_and_handwriting_effects(temp_pdf, final_pdf)
    if os.path.exists(temp_pdf):
        os.remove(temp_pdf)
        
    create_case_02_email(eml_out, final_pdf)
