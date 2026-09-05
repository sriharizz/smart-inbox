import os
import email
from email import policy
import fitz

base_dir = r"c:\projects\SmartInbox\test-data"
emails_dir = os.path.join(base_dir, "emails")
pdfs_dir = os.path.join(base_dir, "pdfs")
out_file = r"c:\projects\SmartInbox\scripts\physical_sources_dump.txt"

with open(out_file, "w", encoding="utf-8") as out:
    out.write("================ PHYSICAL EMAILS DUMP ================\n")
    for i in range(1, 12):
        fname = f"email_{i:02d}.eml"
        fpath = os.path.join(emails_dir, fname)
        if not os.path.exists(fpath):
            out.write(f"*** {fname} NOT FOUND ***\n")
            continue
        with open(fpath, "rb") as f:
            msg = email.message_from_binary_file(f, policy=policy.default)
        out.write(f"\n=================== {fname} ===================\n")
        out.write(f"From: {msg.get('From')}\n")
        out.write(f"To: {msg.get('To')}\n")
        out.write(f"Date: {msg.get('Date')}\n")
        out.write(f"Subject: {msg.get('Subject')}\n")
        out.write(f"Message-ID: {msg.get('Message-ID')}\n")
        
        body = msg.get_body(preferencelist=('plain', 'html'))
        body_text = body.get_content() if body else ''
        out.write(f"--- Full Body ---\n{body_text.strip()}\n")
        
        atts = [p.get_filename() for p in msg.iter_attachments()]
        out.write(f"Attachments: {atts}\n")

    out.write("\n================ PHYSICAL PDFS DUMP ================\n")
    for root, dirs, files in os.walk(pdfs_dir):
        for f in sorted(files):
            if f.endswith(".pdf"):
                full_p = os.path.join(root, f)
                rel_p = os.path.relpath(full_p, base_dir)
                doc = fitz.open(full_p)
                out.write(f"\n=================== {rel_p} ({len(doc)} pages) ===================\n")
                for page_num in range(len(doc)):
                    text = doc[page_num].get_text()
                    out.write(f"--- PAGE {page_num+1} ({len(text)} chars) ---\n")
                    out.write(text.strip() + "\n")
                doc.close()

print(f"[OK] Dumped physical sources to {out_file}")
