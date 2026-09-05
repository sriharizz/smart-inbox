import os
import email

base = r"c:\projects\SmartInbox\test-data\emails"
files = sorted(os.listdir(base))
print(f"Total Emails in {base}: {len(files)}")
for f in files:
    full = os.path.join(base, f)
    with open(full, "rb") as fp:
        msg = email.message_from_binary_file(fp)
    attachments = [p.get_filename() for p in msg.walk() if p.get_filename()]
    att_str = f"[Attached: {attachments[0]}]" if attachments else "[No Attachment - Text Only]"
    sub = msg.get("Subject", "")[:60]
    sender = msg.get("From", "")
    print(f" - {f}: {sub} | {sender} | {att_str}")
