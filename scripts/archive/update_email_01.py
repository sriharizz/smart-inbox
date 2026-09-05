import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

base_dir = r"c:\projects\SmartInbox\test-data"
pdf_path = os.path.join(base_dir, "pdfs", "digital_forms", "cioms_form_MK_Cardioril.pdf")
eml_path = os.path.join(base_dir, "emails", "email_01.eml")

msg = MIMEMultipart("mixed")
msg["From"] = '"Dr. Sarah Jenkins, MD" <sjenkins@metrohealth-chicago.org>'
msg["To"] = '"Clinevo Safety Mailbox" <drugsafety@clinevotech.com>'
msg["Date"] = "Wed, 12 Nov 2025 14:22:10 -0600"
msg["Subject"] = "URGENT: Individual Case Safety Report (ICSR) - Suspect DILI with Cardioril (Pt M.K.)"
msg["Message-ID"] = "<20251112.142210.sjenkins@metrohealth-chicago.org>"
msg["X-Priority"] = "1"

body_text = (
    "Dear Pharmacovigilance Team,\n\n"
    "I am submitting an urgent spontaneous adverse drug reaction report concerning a 58-year-old female "
    "patient (M.K.) under my care who developed acute drug-induced liver injury (DILI) and jaundice "
    "following treatment with Cardioril 20 mg once daily.\n\n"
    "The patient required acute hospital admission on November 10, 2025 due to significantly elevated "
    "transaminases (>9x ULN) and hyperbilirubinemia (Total Bili: 4.8 mg/dL) meeting Hy's law criteria. "
    "Viral hepatitis serologies and abdominal ultrasound were negative for biliary obstruction.\n\n"
    "Cardioril was promptly discontinued on admission, and liver transaminases are beginning to trend down. "
    "Please find attached the completed official CIOMS-I reporting form along with the structured hepatic chemistry "
    "laboratory panel for your expedited safety evaluation.\n\n"
    "Please acknowledge receipt of this regulatory submission.\n\n"
    "Sincerely,\n"
    "Sarah Jenkins, MD, FACP\n"
    "Department of Gastroenterology, MetroHealth Medical Center\n"
    "2500 MetroHealth Dr, Chicago, IL 60609\n"
    "Tel: (312) 555-0188 | Email: sjenkins@metrohealth-chicago.org\n"
)
msg.attach(MIMEText(body_text, "plain", "utf-8"))

with open(pdf_path, "rb") as f:
    pdf_part = MIMEApplication(f.read(), _subtype="pdf")
    pdf_part.add_header("Content-Disposition", "attachment", filename="cioms_form_MK_Cardioril.pdf")
    msg.attach(pdf_part)

with open(eml_path, "wb") as f:
    f.write(msg.as_bytes())

print("[OK] Updated email_01.eml with authentic CIOMS-I PDF!")
