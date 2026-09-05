"""
Generate Case 01:
- Digital CIOMS-I PDF with structured clinical laboratory tables
- Valid RFC 5322 MIME .eml email with the PDF attached
"""

import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Frame, PageTemplate
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

def create_case_01_pdf(pdf_path: str):
    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
    
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    header_title_style = ParagraphStyle(
        'DocTitle',
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#1A365D')
    )
    
    header_sub_style = ParagraphStyle(
        'DocSubTitle',
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#4A5568')
    )
    
    box_header_style = ParagraphStyle(
        'BoxHeader',
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=colors.HexColor('#1A202C')
    )
    
    cell_bold_style = ParagraphStyle(
        'CellBold',
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor('#2D3748')
    )
    
    cell_text_style = ParagraphStyle(
        'CellText',
        fontName='Helvetica',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor('#1A202C')
    )
    
    narrative_style = ParagraphStyle(
        'Narrative',
        fontName='Helvetica',
        fontSize=8,
        leading=10.5,
        textColor=colors.HexColor('#1A202C')
    )
    
    story = []
    
    # Title Banner
    story.append(Paragraph("CIOMS FORM I", header_title_style))
    story.append(Paragraph("SUSPECT ADVERSE REACTION REPORT (INTERNATIONAL REPORTING FORMAT)", header_sub_style))
    story.append(Spacer(1, 8))
    
    # Grid 1: Patient & Reaction Info
    p_info = [
        [
            Paragraph("<b>1. PATIENT INITIALS:</b> M.K.", cell_text_style),
            Paragraph("<b>1a. COUNTRY:</b> United States", cell_text_style),
            Paragraph("<b>2. DATE OF BIRTH:</b> 14-MAY-1967", cell_text_style),
            Paragraph("<b>2a. AGE:</b> 58 YRS", cell_text_style),
            Paragraph("<b>3. SEX:</b> FEMALE", cell_text_style),
            Paragraph("<b>3a. WT:</b> 68 kg", cell_text_style),
        ],
        [
            Paragraph("<b>4. REACTION ONSET DATE:</b><br/>08-NOV-2025", cell_text_style),
            Paragraph("<b>5. TODAY'S DATE:</b><br/>12-NOV-2025", cell_text_style),
            Paragraph("<b>8–12. CHECK ALL APPROPRIATE TO ADVERSE REACTION:</b><br/>"
                      "[X] PATIENT DIED: NO<br/>"
                      "[X] INVOLVED OR PROLONGED INPATIENT HOSPITALIZATION: <b>YES</b> (Admitted: 10-NOV-2025)<br/>"
                      "[X] LIFE-THREATENING: NO<br/>"
                      "[X] PERSISTENT/SIGNIFICANT DISABILITY: NO", cell_text_style),
            "", "", ""
        ]
    ]
    
    t1 = Table(
        [
            p_info[0],
            [p_info[1][0], p_info[1][1], p_info[1][2], "", "", ""]
        ],
        colWidths=[90, 85, 95, 70, 75, 125]
    )
    t1.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#A0AEC0')),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F7FAFC')),
        ('SPAN', (2, 1), (5, 1)),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t1)
    story.append(Spacer(1, 6))
    
    # Section 2: Clinical Reaction Description
    story.append(Paragraph("<b>6. DESCRIBE REACTION(S) (Including relevant medical history, signs, and symptoms):</b>", box_header_style))
    story.append(Spacer(1, 3))
    
    reaction_desc = (
        "58-year-old female patient (M.K.) with known medical history of essential hypertension (5 years) and "
        "type 2 diabetes mellitus initiated therapy with Cardioril (cardioril hydrochloride) 20 mg once daily on 15-Oct-2025. "
        "Approximately 3 weeks later (08-Nov-2025), patient developed progressive severe fatigue, generalized pruritus, "
        "dark amber urine, and obvious scleral icterus with painless jaundice. Outpatient lab draw revealed transaminases >9x ULN "
        "with total bilirubin 4.8 mg/dL. Admitted emergently to MetroHealth Inpatient Gastroenterology Unit on 10-Nov-2025 for acute "
        "drug-induced liver injury (DILI). Viral hepatitis serologies (anti-HAV IgM, HBsAg, anti-HCV, anti-HEV) were non-reactive. "
        "Right upper quadrant ultrasound showed no cholelithiasis or intra/extrahepatic biliary ductal dilatation. Cardioril was "
        "immediately discontinued on admission. Trend shows initial biochemical improvement by 12-Nov-2025."
    )
    
    t_desc = Table([[Paragraph(reaction_desc, narrative_style)]], colWidths=[540])
    t_desc.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#A0AEC0')),
        ('BACKGROUND', (0,0), (-1,-1), colors.white),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_desc)
    story.append(Spacer(1, 6))
    
    # Section 3: Suspect Drug Details
    story.append(Paragraph("<b>II. SUSPECT DRUG(S) INFORMATION</b>", box_header_style))
    story.append(Spacer(1, 3))
    
    drug_data = [
        [
            Paragraph("<b>14. SUSPECT DRUG NAME:</b><br/>Cardioril (cardioril HCl)", cell_text_style),
            Paragraph("<b>15. DAILY DOSE(S):</b><br/>20 mg once daily (QD)", cell_text_style),
            Paragraph("<b>16. ROUTE:</b><br/>Oral (tablet)", cell_text_style),
            Paragraph("<b>17. INDICATION:</b><br/>Essential Hypertension", cell_text_style),
        ],
        [
            Paragraph("<b>18. THERAPY DATES:</b><br/>Start: 15-OCT-2025<br/>Stop: 10-NOV-2025", cell_text_style),
            Paragraph("<b>19. THERAPY DURATION:</b><br/>26 Days", cell_text_style),
            Paragraph("<b>20. LOT / BATCH NUMBER:</b><br/>Lot #CR-2025-0981 (Exp: 08/2027)", cell_text_style),
            Paragraph("<b>21. ACTION TAKEN:</b><br/>Drug Permanently Discontinued", cell_text_style),
        ]
    ]
    t_drug = Table(drug_data, colWidths=[140, 130, 130, 140])
    t_drug.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#A0AEC0')),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F7FAFC')),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_drug)
    story.append(Spacer(1, 6))
    
    # Section 4: Concomitant Drugs
    story.append(Paragraph("<b>22. CONCOMITANT DRUGS AND MEDICAL HISTORY:</b>", box_header_style))
    story.append(Spacer(1, 3))
    concomitant_text = (
        "<b>Concomitant Medications:</b> Metformin 500 mg BID oral (T2DM, ongoing 4 yrs); Amlodipine 5 mg QD oral (HTN, ongoing 2 yrs). "
        "No herbal supplements or OTC NSAIDs reported.<br/>"
        "<b>Relevant Medical History:</b> Essential hypertension, Type 2 Diabetes Mellitus. No alcohol abuse, no prior hepatic dysfunction."
    )
    t_concomitant = Table([[Paragraph(concomitant_text, cell_text_style)]], colWidths=[540])
    t_concomitant.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#A0AEC0')),
        ('BACKGROUND', (0,0), (-1,-1), colors.white),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_concomitant)
    story.append(Spacer(1, 6))
    
    # Section 5: Structured Lab Data Table (Crucial for Section 3.B Table Extraction)
    story.append(Paragraph("<b>23. RELEVANT TESTS / LABORATORY CHEMISTRY PANEL:</b>", box_header_style))
    story.append(Spacer(1, 3))
    
    lab_table_data = [
        [
            Paragraph("<b>Laboratory Test</b>", cell_bold_style),
            Paragraph("<b>Result</b>", cell_bold_style),
            Paragraph("<b>Units</b>", cell_bold_style),
            Paragraph("<b>Reference Range</b>", cell_bold_style),
            Paragraph("<b>Clinical Flag</b>", cell_bold_style),
            Paragraph("<b>Collection Date</b>", cell_bold_style),
        ],
        [
            Paragraph("Alanine Aminotransferase (ALT/SGPT)", cell_text_style),
            Paragraph("<b>540</b>", cell_text_style),
            Paragraph("U/L", cell_text_style),
            Paragraph("7 – 56", cell_text_style),
            Paragraph("<font color='red'><b>CRITICAL HIGH (&gt;9x ULN)</b></font>", cell_text_style),
            Paragraph("10-NOV-2025", cell_text_style),
        ],
        [
            Paragraph("Aspartate Aminotransferase (AST/SGOT)", cell_text_style),
            Paragraph("<b>420</b>", cell_text_style),
            Paragraph("U/L", cell_text_style),
            Paragraph("10 – 40", cell_text_style),
            Paragraph("<font color='red'><b>CRITICAL HIGH (&gt;10x ULN)</b></font>", cell_text_style),
            Paragraph("10-NOV-2025", cell_text_style),
        ],
        [
            Paragraph("Total Bilirubin", cell_text_style),
            Paragraph("<b>4.8</b>", cell_text_style),
            Paragraph("mg/dL", cell_text_style),
            Paragraph("0.1 – 1.2", cell_text_style),
            Paragraph("<font color='red'><b>CRITICAL HIGH (Hy's Law)</b></font>", cell_text_style),
            Paragraph("10-NOV-2025", cell_text_style),
        ],
        [
            Paragraph("Alkaline Phosphatase (ALP)", cell_text_style),
            Paragraph("<b>210</b>", cell_text_style),
            Paragraph("U/L", cell_text_style),
            Paragraph("44 – 147", cell_text_style),
            Paragraph("<font color='#D69E2E'><b>ELEVATED</b></font>", cell_text_style),
            Paragraph("10-NOV-2025", cell_text_style),
        ],
        [
            Paragraph("Serum Creatinine", cell_text_style),
            Paragraph("0.9", cell_text_style),
            Paragraph("mg/dL", cell_text_style),
            Paragraph("0.6 – 1.2", cell_text_style),
            Paragraph("Normal", cell_text_style),
            Paragraph("10-NOV-2025", cell_text_style),
        ],
        [
            Paragraph("Viral Hepatitis Screen (A, B, C)", cell_text_style),
            Paragraph("Non-reactive", cell_text_style),
            Paragraph("-", cell_text_style),
            Paragraph("Negative", cell_text_style),
            Paragraph("Normal", cell_text_style),
            Paragraph("11-NOV-2025", cell_text_style),
        ],
    ]
    
    t_labs = Table(lab_table_data, colWidths=[170, 50, 45, 85, 120, 70])
    t_labs.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')),
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#EDF2F7')),
        ('BACKGROUND', (0,1), (-1,3), colors.HexColor('#FFF5F5')), # Highlight critical rows
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_labs)
    story.append(Spacer(1, 6))
    
    # Section 6: Reporter Information
    story.append(Paragraph("<b>III. REPORTER INFORMATION</b>", box_header_style))
    story.append(Spacer(1, 3))
    
    reporter_data = [
        [
            Paragraph("<b>24a. NAME AND ADDRESS:</b><br/>"
                      "Dr. Sarah Jenkins, MD, FACP<br/>"
                      "MetroHealth Medical Center — Division of Gastroenterology<br/>"
                      "2500 MetroHealth Dr, Chicago, IL 60609, USA", cell_text_style),
            Paragraph("<b>24b. HEALTH PROFESSIONAL?</b><br/><b>YES (Physician / Gastroenterologist)</b>", cell_text_style),
            Paragraph("<b>24c. TELEPHONE & EMAIL:</b><br/>"
                      "Tel: (312) 555-0188<br/>"
                      "Email: sjenkins@metrohealth-chicago.org", cell_text_style),
        ]
    ]
    t_reporter = Table(reporter_data, colWidths=[240, 150, 150])
    t_reporter.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#A0AEC0')),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F7FAFC')),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_reporter)
    
    doc.build(story)
    print(f"[OK] Generated Case 01 PDF: {pdf_path}")

def create_case_01_email(eml_path: str, pdf_path: str):
    os.makedirs(os.path.dirname(eml_path), exist_ok=True)
    
    msg = MIMEMultipart('mixed')
    msg['From'] = '"Dr. Sarah Jenkins, MD" <sjenkins@metrohealth-chicago.org>'
    msg['To'] = '"Clinevo Safety Mailbox" <drugsafety@clinevotech.com>'
    msg['Date'] = 'Wed, 12 Nov 2025 14:22:10 -0600'
    msg['Subject'] = 'URGENT: Individual Case Safety Report (ICSR) - Suspect DILI with Cardioril (Pt M.K.)'
    msg['Message-ID'] = '<20251112.142210.sjenkins@metrohealth-chicago.org>'
    msg['X-Priority'] = '1' # High Priority
    
    body_text = (
        "Dear Pharmacovigilance Team,\n\n"
        "I am submitting an urgent spontaneous adverse drug reaction report concerning a 58-year-old female "
        "patient (M.K.) under my care who developed acute drug-induced liver injury (DILI) and jaundice "
        "following treatment with Cardioril 20 mg once daily.\n\n"
        "The patient required acute hospital admission on November 10, 2025 due to significantly elevated "
        "transaminases (>9x ULN) and hyperbilirubinemia (Total Bili: 4.8 mg/dL) meeting Hy's law criteria. "
        "Viral hepatitis serologies and abdominal ultrasound were negative for biliary obstruction.\n\n"
        "Cardioril was promptly discontinued on admission, and liver transaminases are beginning to trend down. "
        "Please find attached the fully completed CIOMS-I reporting form along with the structured hepatic chemistry "
        "laboratory panel for your expedited safety evaluation.\n\n"
        "Please acknowledge receipt of this regulatory submission.\n\n"
        "Sincerely,\n"
        "Sarah Jenkins, MD, FACP\n"
        "Department of Gastroenterology, MetroHealth Medical Center\n"
        "2500 MetroHealth Dr, Chicago, IL 60609\n"
        "Tel: (312) 555-0188 | Email: sjenkins@metrohealth-chicago.org\n"
    )
    msg.attach(MIMEText(body_text, 'plain', 'utf-8'))
    
    # Attach PDF
    with open(pdf_path, 'rb') as f:
        pdf_part = MIMEApplication(f.read(), _subtype='pdf')
        pdf_filename = os.path.basename(pdf_path)
        pdf_part.add_header('Content-Disposition', 'attachment', filename=pdf_filename)
        msg.attach(pdf_part)
        
    with open(eml_path, 'wb') as f:
        f.write(msg.as_bytes())
        
    print(f"[OK] Generated Case 01 Email: {eml_path}")

if __name__ == '__main__':
    base_dir = r'c:\projects\SmartInbox\test-data'
    pdf_out = os.path.join(base_dir, 'pdfs', 'digital_forms', 'cioms_form_MK_Cardioril.pdf')
    eml_out = os.path.join(base_dir, 'emails', 'email_01.eml')
    
    create_case_01_pdf(pdf_out)
    create_case_01_email(eml_out, pdf_out)
