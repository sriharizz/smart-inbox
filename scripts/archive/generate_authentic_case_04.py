"""
Generate 100% Authentic FDA Form 3500A (MedWatch) for Case 04:
- Official Federal Government styling: Monochrome, OMB control header, standard form grid.
- Page 1: Official FDA Form 3500A (Sections A, B, C, E) checking BOTH [X] Adverse Event and [X] Product Problem.
- Page 2: Official Hospital Risk Management Exhibit 1 (Physical Evidence Photo of the contaminated vial with evidence tracking stamp).
- Updates email_04.eml with the new authentic 2-page PDF.
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image as RLImage
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

def create_authentic_fda_3500a_pdf(pdf_path: str, photo_path: str):
    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
    
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    fed_header = ParagraphStyle('FedHdr', fontName='Helvetica-Bold', fontSize=9.5, leading=12, alignment=TA_CENTER, textColor=colors.black)
    fed_sub = ParagraphStyle('FedSub', fontName='Helvetica', fontSize=7.5, leading=9.5, alignment=TA_CENTER, textColor=colors.black)
    sec_hdr = ParagraphStyle('SecHdr', fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=colors.black)
    lbl = ParagraphStyle('Lbl', fontName='Helvetica-Bold', fontSize=6.5, leading=8, textColor=colors.black)
    val = ParagraphStyle('Val', fontName='Helvetica', fontSize=7.5, leading=9.5, textColor=colors.black)
    val_narr = ParagraphStyle('ValNarr', fontName='Helvetica', fontSize=7.5, leading=9.5, textColor=colors.black)
    
    story = []
    
    # --- PAGE 1: FORM FDA 3500A ---
    story.append(Paragraph("DEPARTMENT OF HEALTH AND HUMAN SERVICES — FOOD AND DRUG ADMINISTRATION", fed_sub))
    story.append(Paragraph("MEDWATCH: THE FDA SAFETY INFORMATION AND ADVERSE EVENT REPORTING PROGRAM", fed_header))
    story.append(Paragraph("<b>FORM FDA 3500A (10/15) — MANDATORY ADVERSE EVENT & PRODUCT PROBLEM REPORTING</b>", ParagraphStyle('FormCode', fontName='Helvetica-Bold', fontSize=8, leading=10, alignment=TA_CENTER)))
    story.append(Paragraph("OMB Control No. 0910-0291 &nbsp;|&nbsp; For use by User-Facilities, Distributors, and Manufacturers", fed_sub))
    story.append(Spacer(1, 4))
    
    # SECTION A: Patient Info
    story.append(Paragraph("<b>SECTION A: PATIENT INFORMATION</b>", sec_hdr))
    a_row = [
        Paragraph("<b>1. PATIENT IDENTIFIER</b><br/>A.P. (Arthur Pendelton)", val),
        Paragraph("<b>2. AGE AT TIME OF EVENT</b><br/>71 YRS", val),
        Paragraph("<b>2a. DATE OF BIRTH</b><br/>19-AUG-1954", val),
        Paragraph("<b>3. SEX</b><br/>MALE", val),
        Paragraph("<b>4. WEIGHT</b><br/>74 kg (163 lbs)", val),
    ]
    t_a = Table([a_row], colWidths=[150, 100, 100, 80, 110])
    t_a.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.75, colors.black),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_a)
    story.append(Spacer(1, 4))
    
    # SECTION B: Adverse Event, Product Problem
    story.append(Paragraph("<b>SECTION B: ADVERSE EVENT, PRODUCT PROBLEM OR ERROR</b>", sec_hdr))
    
    b_checks = (
        "<b>1. CHECK ALL THAT APPLY:</b><br/>"
        "<b>[ X ] ADVERSE EVENT</b> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
        "<b>[ X ] PRODUCT PROBLEM (e.g., defects / contaminations)</b>"
    )
    b_outcomes = (
        "<b>2. OUTCOMES ATTRIBUTED TO ADVERSE EVENT (Check all that apply):</b><br/>"
        "[ &nbsp; ] DEATH &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
        "<b>[ X ] LIFE-THREATENING: YES (Septic Shock / MAP 45)</b><br/>"
        "<b>[ X ] HOSPITALIZATION — PROLONGED / CRITICAL CARE ICU</b><br/>"
        "[ &nbsp; ] DISABILITY OR PERMANENT DAMAGE &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
        "[ &nbsp; ] CONGENITAL ANOMALY &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
        "<b>[ X ] REQUIRED INTERVENTION TO PREVENT DAMAGE</b>"
    )
    b_dates = [
        Paragraph("<b>3. DATE OF EVENT</b><br/>14-NOV-2025", val),
        Paragraph("<b>4. DATE OF THIS REPORT</b><br/>14-NOV-2025", val),
    ]
    
    t_b1 = Table([
        [Paragraph(b_checks, val), Paragraph("<b>REPORT TYPE:</b> Mandatory 15-Day Alert", val)],
        [Paragraph(b_outcomes, val), Table([b_dates], colWidths=[90, 90])],
    ], colWidths=[360, 180])
    t_b1.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.75, colors.black),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_b1)
    
    # Section B5: Event Description
    b5_text = (
        "<b>5. DESCRIBE EVENT OR PROBLEM (Include relevant tests, laboratory data, dates, and defect observations):</b><br/>"
        "At 11:30 on 14-NOV-2025, in Medical ICU (Northwestern Memorial Hospital), patient Arthur Pendelton (71M, post-op pneumonia) "
        "was initiated on an intravenous infusion of Cefatox 1g. After ~35mL infused, the bedside nurse noted visible turbidity and dark "
        "particulate matter inside the piggyback container. Infusion halted immediately. Within 45 minutes, patient developed acute rigors, "
        "temperature spike to 39.8°C (103.6°F), severe hypotension (BP 72/40 mmHg, MAP 50), and signs of distributive septic shock. "
        "Vasopressor therapy (Norepinephrine infusion titrated to 0.14 mcg/kg/min) and broad-spectrum empiric coverage initiated. "
        "<b>PRODUCT DEFECT EXAMINATION:</b> Visual inspection of vial Lot #CX54831 (Exp 08/25) confirmed a cracked aluminum crimp collar "
        "compromising container closure integrity, with visible black particulate matter floating in solution. "
        "Central pharmacy placed all 48 hospital vials of Lot #CX54831 into immediate quarantine. "
        "<b>PHOTOGRAPHIC EVIDENCE:</b> Detailed photographic evidence of compromised vial stopper and particulate matter is recorded in "
        "EXHIBIT 1 on Page 2 of this mandatory submission. Patient remains in critical condition under ICU resuscitation."
    )
    t_b5 = Table([[Paragraph(b5_text, val_narr)]], colWidths=[540])
    t_b5.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.75, colors.black),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_b5)
    story.append(Spacer(1, 4))
    
    # SECTION C: Suspect Product
    story.append(Paragraph("<b>SECTION C: SUSPECT PRODUCT(S) INFORMATION</b>", sec_hdr))
    c_data = [
        [
            Paragraph("<b>1. NAME, STRENGTH, MANUFACTURER</b><br/>Cefatox (cefatoxime sodium) 1g for Inj.", val),
            Paragraph("<b>2. DOSE, FREQUENCY & ROUTE</b><br/>1g IV piggyback once", val),
            Paragraph("<b>3. THERAPY DATES</b><br/>14-NOV-2025 (Single partial dose)", val),
        ],
        [
            Paragraph("<b>4. DIAGNOSIS FOR USE</b><br/>Post-operative Aspiration Pneumonia", val),
            Paragraph("<b>5. LOT / BATCH NUMBER</b><br/>Lot #CX54831", ParagraphStyle('BldLot', fontName='Helvetica-Bold', fontSize=8, textColor=colors.black)),
            Paragraph("<b>6. EXPIRATION DATE</b><br/>08/2025", val),
        ],
        [
            Paragraph("<b>7. EVENT ABATED AFTER STOPPING?</b><br/>[ &nbsp; ] Yes &nbsp;&nbsp; [ X ] No (ICU shock ongoing)", val),
            Paragraph("<b>8. REAPPEARED AFTER REINTRODUCTION?</b><br/>[ &nbsp; ] Yes &nbsp;&nbsp; [ &nbsp; ] No &nbsp;&nbsp; [ X ] N/A", val),
            Paragraph("<b>9. PRODUCT DEFECT CONFIRMED?</b><br/><b>[ X ] YES (Cracked seal & particulate)</b>", val),
        ]
    ]
    t_c = Table(c_data, colWidths=[200, 170, 170])
    t_c.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.75, colors.black),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_c)
    story.append(Spacer(1, 4))
    
    # SECTION E: Initial Reporter
    story.append(Paragraph("<b>SECTION E: INITIAL REPORTER INFORMATION</b>", sec_hdr))
    e_data = [
        [
            Paragraph("<b>1. NAME AND ADDRESS OF REPORTER</b><br/>"
                      "Robert Lang, MD, FCCM (Director of Critical Care Medicine)<br/>"
                      "Northwestern Memorial Hospital — Medical ICU<br/>"
                      "251 E Huron St, Chicago, IL 60611, USA", val),
            Paragraph("<b>2. HEALTH PROFESSIONAL?</b><br/><b>[ X ] YES</b> &nbsp;&nbsp; [ &nbsp; ] NO<br/><br/>"
                      "<b>3. OCCUPATION:</b> Physician / Intensivist", val),
            Paragraph("<b>4. CONTACT TELEPHONE & EMAIL:</b><br/>"
                      "Tel: (312) 555-0320<br/>"
                      "Email: rlang@nmh-icu.org", val),
        ]
    ]
    t_e = Table(e_data, colWidths=[240, 150, 150])
    t_e.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.75, colors.black),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_e)
    
    # --- PAGE BREAK: EXHIBIT 1 ---
    story.append(PageBreak())
    
    # PAGE 2: EXHIBIT 1 EVIDENCE RECORD
    story.append(Paragraph("NORTHWESTERN MEMORIAL HOSPITAL — DEPARTMENT OF PHARMACY", fed_sub))
    story.append(Paragraph("RISK MANAGEMENT & QUALITY ASSURANCE ATTACHMENT", fed_header))
    story.append(Paragraph("<b>EXHIBIT 1: PHYSICAL EVIDENCE PHOTO LOG (QUARANTINED VIAL)</b>", ParagraphStyle('ExhTitle', fontName='Helvetica-Bold', fontSize=10, leading=12, alignment=TA_CENTER)))
    story.append(Spacer(1, 8))
    
    # Exhibit Metadata Box
    exh_meta = [
        [
            Paragraph("<b>HOSPITAL INCIDENT REF:</b> NMH-ICU-2025-449", val),
            Paragraph("<b>EVIDENCE CUSTODIAN:</b> Central Pharmacy QA", val),
            Paragraph("<b>DATE PHOTOGRAPHED:</b> 14-NOV-2025 12:15 CST", val),
        ],
        [
            Paragraph("<b>PRODUCT:</b> Cefatox 1g for Injection (20ml)", val),
            Paragraph("<b>LOT / BATCH:</b> Lot #CX54831 (Exp 08/25)", ParagraphStyle('ExhLot', fontName='Helvetica-Bold', fontSize=7.5)),
            Paragraph("<b>SECURITY QUARANTINE SEAL:</b> #NMH-Q-94821", val),
        ]
    ]
    t_exh_meta = Table(exh_meta, colWidths=[180, 180, 180])
    t_exh_meta.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.75, colors.black),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_exh_meta)
    story.append(Spacer(1, 10))
    
    # Large Clear Evidence Photo
    img_element = RLImage(photo_path, width=4.5*inch, height=3.375*inch)
    story.append(Table([[img_element]], colWidths=[540], style=[
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('BOX', (0,0), (-1,-1), 1, colors.black),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(Spacer(1, 8))
    
    # Evidence Findings Narrative
    evidence_desc = (
        "<b>PHYSICAL EVIDENCE INSPECTION FINDINGS:</b><br/>"
        "1. <b>Closure Integrity Compromise:</b> Close examination of the 20mL glass container reveals an irregular mechanical rupture / tear "
        "in the aluminum crimp collar securing the blue elastomeric stopper. The seal was breached prior to reconstitution.<br/>"
        "2. <b>Foreign Particulate Contamination:</b> Macroscopic particulate matter (multiple dark, black/brown foreign fragments and flakes) "
        "is clearly visible suspended throughout the reconstituted solution under 2000-lux ambient cleanroom inspection lighting.<br/>"
        "3. <b>Regulatory Status:</b> Immediate manufacturer product quality alert issued; all 48 inventory units placed in locked quarantine.<br/>"
        "<i>Investigator Note: Photograph entered into FDA Form 3500A Section B documentation as primary defect evidence.</i>"
    )
    t_ev_desc = Table([[Paragraph(evidence_desc, val_narr)]], colWidths=[540])
    t_ev_desc.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.75, colors.black),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_ev_desc)
    
    doc.build(story)
    print(f"[OK] Generated Authentic 2-Page FDA Form 3500A PDF: {pdf_path}")

def update_email_04(eml_path: str, pdf_path: str):
    msg = MIMEMultipart('mixed')
    msg['From'] = '"Dr. Robert Lang, MD" <rlang@nmh-icu.org>'
    msg['To'] = '"Clinevo Safety & Quality Intake" <drugsafety@clinevotech.com>'
    msg['Date'] = 'Fri, 14 Nov 2025 14:10:00 -0600'
    msg['Subject'] = 'CRITICAL ALERT: Sepsis caused by Contaminated Cefatox 1g Vial (Lot #CX54831) - FDA Form 3500A Attached'
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
        "Attached is our official completed FDA Form 3500A report with Exhibit 1 (photographic evidence record of the contaminated vial).\n\n"
        "Sincerely,\n"
        "Robert Lang, MD, FCCM\n"
        "Director, Medical Intensive Care Unit\n"
        "Northwestern Memorial Hospital, Chicago, IL\n"
        "Tel: (312) 555-0320 | Email: rlang@nmh-icu.org\n"
    )
    msg.attach(MIMEText(body_text, 'plain', 'utf-8'))
    
    with open(pdf_path, 'rb') as f:
        pdf_part = MIMEApplication(f.read(), _subtype='pdf')
        pdf_part.add_header('Content-Disposition', 'attachment', filename='vial_contamination_sepsis.pdf')
        msg.attach(pdf_part)
        
    with open(eml_path, 'wb') as f:
        f.write(msg.as_bytes())
        
    print(f"[OK] Updated Case 04 Email: {eml_path}")

if __name__ == '__main__':
    base_dir = r'c:\projects\SmartInbox\test-data'
    pdf_out = os.path.join(base_dir, 'pdfs', 'quality_complaints', 'vial_contamination_sepsis.pdf')
    photo_path = os.path.join(base_dir, 'pdfs', 'quality_complaints', 'contaminated_vial_photo.jpg')
    eml_out = os.path.join(base_dir, 'emails', 'email_04.eml')
    
    create_authentic_fda_3500a_pdf(pdf_out, photo_path)
    update_email_04(eml_out, pdf_out)
