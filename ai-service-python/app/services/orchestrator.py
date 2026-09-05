import time
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path
from PIL import Image

from app.core.config import settings
from app.parsers.email_parser import EmailParser, ParsedEmail
from app.parsers.pdf_parser import PDFParser, ParsedPDF
from app.schemas.extraction_schema import ExtractionResult
from app.schemas.literature_schema import LiteratureScreenResult
from app.services.triage_service import triage_service
from app.services.icsr_extractor import icsr_extractor
from app.services.literature_service import literature_service

logger = logging.getLogger("smartinbox.orchestrator")

class DocumentOrchestrator:
    @staticmethod
    def process_eml(eml_bytes: bytes, filename: str = "email.eml") -> ExtractionResult:
        start_time = time.time()
        
        # 1. Parse RFC 5322 EML
        parsed_email = EmailParser.parse_eml_bytes(eml_bytes)
        
        # 3. Process any attached PDFs
        combined_text_parts = [
            f"[EMAIL METADATA]\nFrom: {parsed_email.sender} <{parsed_email.sender_email}>\nDate: {parsed_email.date}\nSubject: {parsed_email.subject}\nMessage-ID: {parsed_email.message_id}",
            f"\n[EMAIL BODY]\n{parsed_email.body_text}"
        ]
        
        candidate_images: List[Image.Image] = []
        
        for att in parsed_email.attachments:
            if att["filename"].lower().endswith(".pdf"):
                pdf_res = PDFParser.parse_pdf_bytes(att["bytes"], filename=att["filename"])
                combined_text_parts.append(f"\n[ATTACHED PDF: {att['filename']} (Flavor: {pdf_res.flavor})]\n{pdf_res.full_content_with_tables}")
                for img_info in pdf_res.images:
                    candidate_images.append(img_info["pil_image"])
                
                # If scanned/handwritten, render page 1 as high-res image
                if pdf_res.flavor == "scanned_handwritten":
                    try:
                        candidate_images.append(pdf_res.render_page_image(1))
                    except Exception:
                        pass

        full_context_text = "\n\n".join(combined_text_parts)

        # 4. Triage Classification
        triage_result = triage_service.classify_text(full_context_text, context_label=f"Email: {parsed_email.subject}")

        # 5. Entity Extraction
        extraction = icsr_extractor.extract_facts(
            document_text=full_context_text,
            triage_result=triage_result,
            images=candidate_images,
            source_filename=filename
        )

        extraction.processing_time_ms = int((time.time() - start_time) * 1000)

        return extraction

    @staticmethod
    def process_pdf(pdf_bytes: bytes, filename: str = "document.pdf") -> ExtractionResult:
        start_time = time.time()

        # 1. Parse PDF layout
        parsed_pdf = PDFParser.parse_pdf_bytes(pdf_bytes, filename=filename)
        
        candidate_images: List[Image.Image] = []
        for img_info in parsed_pdf.images:
            candidate_images.append(img_info["pil_image"])
        
        if parsed_pdf.flavor == "scanned_handwritten":
            try:
                candidate_images.append(parsed_pdf.render_page_image(1))
            except Exception:
                pass

        full_content = parsed_pdf.full_content_with_tables

        # 3. Triage
        triage_result = triage_service.classify_text(full_content, context_label=f"PDF: {filename} ({parsed_pdf.flavor})")

        # 4. Extraction
        extraction = icsr_extractor.extract_facts(
            document_text=full_content,
            triage_result=triage_result,
            images=candidate_images,
            source_filename=filename
        )

        extraction.processing_time_ms = int((time.time() - start_time) * 1000)
        return extraction

    @staticmethod
    def screen_literature_pdf(pdf_bytes: bytes, filename: str = "article.pdf") -> LiteratureScreenResult:
        parsed_pdf = PDFParser.parse_pdf_bytes(pdf_bytes, filename=filename)
        return literature_service.screen_and_split(parsed_pdf.full_text, filename=filename)

orchestrator = DocumentOrchestrator()
