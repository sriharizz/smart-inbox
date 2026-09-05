import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

eml_dir = r"c:\projects\SmartInbox\test-data\emails"
eml_path = os.path.join(eml_dir, "email_11.eml")

msg = MIMEMultipart("alternative")
msg["From"] = '"Dr. Elena Rostova, PharmD, BCPS" <e.rostova@massgeneral-pharmacy.org>'
msg["To"] = '"Clinevo Medical Information Service" <medinfo@clinevotech.com>'
msg["Date"] = "Fri, 21 Nov 2025 09:15:00 -0500"
msg["Subject"] = "Medical Information Request: In-Use Compatibility & Dilution Stability for Cefatox 1g in D5W"
msg["Message-ID"] = "<20251121.091500.erostova@massgeneral-pharmacy.org>"

body_text = """Dear Medical Information Team,

I am writing on behalf of our inpatient pharmacy clinical operations team at Massachusetts General Hospital with a stability inquiry regarding Cefatox (cefatoxime sodium) 1g for Injection.

We are standardizing our hospital-wide intravenous infusion protocol for adult surgical prophylaxis in patients with normal renal function. The prescribed dose is 1g IV every 8 hours. Our cleanroom compounding protocol calls for reconstituting each 1g vial with 10 mL Sterile Water for Injection, followed by immediate dilution into a 100 mL Dextrose 5% in Water (D5W) IV infusion bag.

Could Medical Affairs please provide documentation or monograph data addressing:
1. Chemical stability and potency retention (>95%) of Cefatox 1g in 100 mL D5W at refrigerated temperatures (2 deg C to 8 deg C) for up to 48 hours.
2. In-use room temperature (20 deg C to 25 deg C) stability during a prolonged 4-hour intravenous infusion.
3. Compatibility with Y-site co-infusion of standard 0.9% Sodium Chloride or Lactated Ringer's solution.

Please note: There is no adverse patient event, no clinical complication, and no physical defect in our product stock. This inquiry is solely for hospital protocol formulation and compounding guidance.

Thank you for your assistance.

Sincerely,
Dr. Elena Rostova, PharmD, BCPS
Senior Clinical Compounding Specialist
Department of Pharmacy Services, Massachusetts General Hospital
55 Fruit Street, Boston, MA 02114
Tel: (617) 555-0144 | Email: e.rostova@massgeneral-pharmacy.org
"""

msg.attach(MIMEText(body_text, "plain", "utf-8"))

with open(eml_path, "wb") as f:
    f.write(msg.as_bytes())

print(f"[OK] Generated Case 11 MI Email: {eml_path} ({os.path.getsize(eml_path)} bytes)")
