"""
Generate Case 03:
- Pure Email Text (No PDF Attachment)
- Informal consumer/patient spontaneous adverse event report
- Tests extracting clinical facts from email body alone, parsing non-technical language,
  and properly assigning "Not stated" to missing fields (like weight, lab numbers, lot number).
"""

import os
from email.mime.text import MIMEText

def create_case_03_email(eml_path: str):
    os.makedirs(os.path.dirname(eml_path), exist_ok=True)
    
    body_text = (
        "Hello Drug Safety Team,\n\n"
        "I am writing this email to report a really scary reaction I just experienced after taking Corzapan 10mg tablets. "
        "My doctor prescribed this to me four days ago for mild hypertension and work-related anxiety.\n\n"
        "Yesterday morning (November 13th), about an hour after taking my fourth pill, my heart started pounding uncontrollably "
        "like it was going to jump right out of my chest. I felt extremely lightheaded, broke out into a cold sweat, and almost "
        "passed out on my kitchen floor. My smartwatch alerted me that my resting pulse shot up to 154 bpm while I was just sitting down. "
        "I also felt tight in my chest and had trouble catching my breath for nearly two hours.\n\n"
        "My husband drove me to our family doctor (Dr. Robert Hayes at Denver Family Medicine) who examined me and told me to "
        "immediately stop taking Corzapan. He said it was an acute drug-induced tachycardia and palpitations episode.\n\n"
        "I am still feeling fatigued today, but my heart rate has calmed down to 78 bpm. I wanted to report this so other patients are warned. "
        "I threw the prescription bottle away, so I don't know the exact batch number, but it was filled last week at the Walgreens on Colfax.\n\n"
        "Patient Information:\n"
        "Name: Emily Watson\n"
        "Age: 42 years old\n"
        "Sex: Female\n"
        "Location: Denver, Colorado, USA\n"
        "Phone: (303) 555-0192\n"
        "Email: emily.watson92@consumer-mail.com\n\n"
        "Please confirm you received this report."
    )
    
    msg = MIMEText(body_text, 'plain', 'utf-8')
    msg['From'] = '"Emily Watson" <emily.watson92@consumer-mail.com>'
    msg['To'] = '"Clinevo Drug Safety Intake" <drugsafety@clinevotech.com>'
    msg['Date'] = 'Fri, 14 Nov 2025 09:14:22 -0700'
    msg['Subject'] = 'Terrible heart palpitations and dizzy spells after taking Corzapan 10mg'
    msg['Message-ID'] = '<20251114.091422.ewatson@consumer-mail.com>'
    
    with open(eml_path, 'wb') as f:
        f.write(msg.as_bytes())
        
    print(f"[OK] Generated Case 03 Email (Pure Text, No Attachment): {eml_path}")

if __name__ == '__main__':
    eml_out = r'c:\projects\SmartInbox\test-data\emails\email_03.eml'
    create_case_03_email(eml_out)
