import os
import email
from email import policy
import fitz

base_dir = r"c:\projects\SmartInbox\test-data"
emails_dir = os.path.join(base_dir, "emails")
pdfs_dir = os.path.join(base_dir, "pdfs")

print("================ PHYSICAL EMAILS DUMP ================")
for i in range(1, 12):
    fname = f"email_{i:02d}.eml"
    fpath = os.path.join(emails_dir, fname)
    if not os.path.exists(fpath):
        print(f"*** {fname} NOT FOUND ***")
        continue
    with open(fpath, "rb") as f:
        msg = email.message_from_binary_file(f, policy=policy.default)
    print(f"\n=================== {fname} ===================")
    print(f"From: {msg.get('From')}")
    print(f"To: {msg.get('To')}")
    print(f"Date: {msg.get('Date')}")
    print(f"Subject: {msg.get('Subject')}")
    print(f"Message-ID: {msg.get('Message-ID')}")
    
    body = msg.get_body(preferencelist=('plain', 'html'))
    body_text = body.get_content() if body else ''
    print(f"--- Full Body ---\n{body_text.strip()}")
    
    atts = [p.get_filename() for p in msg.iter_attachments()]
    print(f"Attachments: {atts}")

print("\n================ PHYSICAL PDFS DUMP ================")
for root, dirs, files in os.walk(pdfs_dir):
    for f in sorted(files):
        if f.endswith(".pdf"):
            full_p = os.path.join(root, f)
            rel_p = os.path.relpath(full_p, base_dir)
            doc = fitz.open(full_p)
            print(f"\n=================== {rel_p} ({len(doc)} pages) ===================")
            for page_num in range(len(doc)):
                text = doc[page_num].get_text()
                print(f"--- PAGE {page_num+1} ({len(text)} chars) ---")
                print(text[:600].strip())
                if len(text) > 600:
                    print("... [truncated] ...")
            doc.close()
