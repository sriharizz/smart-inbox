import email
from email import policy
from email.parser import BytesParser
from typing import List, Dict, Any, Optional
from pathlib import Path

class ParsedEmail:
    def __init__(
        self,
        message_id: str,
        date: str,
        sender: str,
        sender_email: str,
        recipient: str,
        subject: str,
        body_text: str,
        attachments: List[Dict[str, Any]]
    ):
        self.message_id = message_id
        self.date = date
        self.sender = sender
        self.sender_email = sender_email
        self.recipient = recipient
        self.subject = subject
        self.body_text = body_text
        self.attachments = attachments

    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_id": self.message_id,
            "date": self.date,
            "sender": self.sender,
            "sender_email": self.sender_email,
            "recipient": self.recipient,
            "subject": self.subject,
            "body_text": self.body_text,
            "attachment_names": [a["filename"] for a in self.attachments]
        }

class EmailParser:
    @staticmethod
    def parse_eml_bytes(data: bytes) -> ParsedEmail:
        msg = BytesParser(policy=policy.default).parsebytes(data)
        
        message_id = str(msg.get("Message-ID", "")).strip("<>")
        date_str = str(msg.get("Date", ""))
        from_str = str(msg.get("From", ""))
        to_str = str(msg.get("To", ""))
        subject = str(msg.get("Subject", ""))
        
        sender_name = ""
        sender_email = ""
        if "<" in from_str and ">" in from_str:
            parts = from_str.split("<")
            sender_name = parts[0].strip().strip('"')
            sender_email = parts[1].strip(">").strip()
        else:
            sender_name = from_str
            sender_email = from_str

        # Extract plain text body
        body_text = ""
        attachments = []

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))
                filename = part.get_filename()

                if filename:
                    file_bytes = part.get_payload(decode=True)
                    if file_bytes:
                        attachments.append({
                            "filename": filename,
                            "content_type": content_type,
                            "size": len(file_bytes),
                            "bytes": file_bytes
                        })
                elif content_type == "text/plain" and "attachment" not in content_disposition:
                    charset = part.get_content_charset() or "utf-8"
                    payload = part.get_payload(decode=True)
                    if payload:
                        body_text += payload.decode(charset, errors="replace") + "\n"
                elif content_type == "text/html" and not body_text and "attachment" not in content_disposition:
                    # Fallback if no plain text
                    charset = part.get_content_charset() or "utf-8"
                    payload = part.get_payload(decode=True)
                    if payload:
                        html = payload.decode(charset, errors="replace")
                        # Basic tag stripper
                        import re
                        clean = re.sub("<[^<]+?>", " ", html)
                        body_text += clean + "\n"
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or "utf-8"
                body_text = payload.decode(charset, errors="replace")

        return ParsedEmail(
            message_id=message_id,
            date=date_str,
            sender=sender_name,
            sender_email=sender_email,
            recipient=to_str,
            subject=subject,
            body_text=body_text.strip(),
            attachments=attachments
        )

    @staticmethod
    def parse_eml_file(file_path: Path) -> ParsedEmail:
        with open(file_path, "rb") as f:
            return EmailParser.parse_eml_bytes(f.read())
