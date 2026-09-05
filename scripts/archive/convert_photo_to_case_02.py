import os
import shutil
from PIL import Image
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

src_img = r"C:\Users\BTSRIHARI\.gemini\antigravity-ide\brain\c4b1c911-34dc-476f-8860-a648f92d7a93\handwritten_clinic_form_1788512074041.jpg"
dest_dir = r"c:\projects\SmartInbox\test-data\pdfs\scanned_handwritten"
dest_img = os.path.join(dest_dir, "handwritten_clinic_photo.jpg")
dest_pdf = os.path.join(dest_dir, "urgent_care_intake_handwritten.pdf")
eml_out = r"c:\projects\SmartInbox\test-data\emails\email_02.eml"

# 1. Copy the raw photo to the project directory
shutil.copy2(src_img, dest_img)
print(f"[OK] Copied raw photo to: {dest_img}")

# 2. Convert the real photograph directly to PDF
img = Image.open(dest_img).convert("RGB")
img.save(dest_pdf, "PDF", resolution=200.0)
print(f"[OK] Saved photograph-as-PDF to: {dest_pdf}")

# 3. Update email_02.eml with the real handwritten case
msg = MIMEMultipart("mixed")
msg["From"] = '"Dr. A. Peterson, MD" <a.peterson@stmarys-hospital.org>'
msg["To"] = '"Clinevo Drug Safety Mailbox" <drugsafety@clinevotech.com>'
msg["Date"] = "Sun, 10 Dec 2023 15:30:00 -0500"
msg["Subject"] = "URGENT: Adverse Drug Event Report - Acute Anaphylaxis s/p InjectaPen (Pt Jane Doe)"
msg["Message-ID"] = "<20231210.153000.apeterson@stmarys-hospital.org>"
msg["X-Priority"] = "1"

body_text = (
    "Dear Pharmacovigilance Department,\n\n"
    "I am urgently submitting an initial adverse event report for a 33-year-old female patient (Jane Doe, DOB: 05/18/1990) "
    "who presented to St. Mary's Emergency Department in severe acute anaphylactic shock 20 minutes following self-injection of InjectaPen.\n\n"
    "Patient presented with generalized urticaria, marked lip and perioral angioedema, inspiratory stridor, and profound hypotension (BP 85/50, HR 128). "
    "Immediate emergency intervention was initiated: Epinephrine 0.3 mg IM, high-flow oxygen, IV fluid resuscitation, and admission to the emergency unit.\n\n"
    "Attached is the photograph of our emergency intake and triage record completed at bedside.\n\n"
    "Sincerely,\n"
    "Dr. A. Peterson, MD\n"
    "Emergency Department, St. Mary's General Hospital\n"
    "NPI: 9876543210 | Email: a.peterson@stmarys-hospital.org\n"
)
msg.attach(MIMEText(body_text, "plain", "utf-8"))

with open(dest_pdf, "rb") as f:
    pdf_part = MIMEApplication(f.read(), _subtype="pdf")
    pdf_part.add_header("Content-Disposition", "attachment", filename="urgent_care_intake_handwritten.pdf")
    msg.attach(pdf_part)

with open(eml_out, "wb") as f:
    f.write(msg.as_bytes())

print(f"[OK] Generated Case 02 Email: {eml_out}")
