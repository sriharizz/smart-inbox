import time
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path
from PIL import Image

from app.core.config import settings
from app.parsers.email_parser import EmailParser, ParsedEmail
from app.parsers.pdf_parser import PDFParser, ParsedPDF
from app.schemas.case_envelope import CaseEnvelope
from app.schemas.extraction_schema import ExtractionResult
from app.schemas.legacy_adapter import envelope_to_legacy
from app.schemas.literature_schema import LiteratureScreenResult
from app.services.triage_service import triage_service
from app.services.icsr_extractor import icsr_extractor
from app.services.literature_service import literature_service
from app.services.evidence_retriever import evidence_retriever
from app.services.evidence_verifier import evidence_verifier
from app.services.consistency_validator import consistency_validator
from app.services.reviewer_brief_builder import reviewer_brief_builder

logger = logging.getLogger("smartinbox.orchestrator")

class DocumentOrchestrator:
    @staticmethod
    def process_eml_envelope(eml_bytes: bytes, filename: str = "email.eml") -> CaseEnvelope:
        """
        Canonical ingestion path for RFC 5322 EML communications.
        Produces a category-aware CaseEnvelope with atomic Fact ledger and Evidence objects.
        """
        start_time = time.time()
        
        # 1. Parse RFC 5322 EML
        parsed_email = EmailParser.parse_eml_bytes(eml_bytes)
        
        # 2. Process any attached PDFs / images
        combined_text_parts = [
            f"[EMAIL METADATA]\nFrom: {parsed_email.sender} <{parsed_email.sender_email}>\nDate: {parsed_email.date}\nSubject: {parsed_email.subject}\nMessage-ID: {parsed_email.message_id}",
            f"\n[EMAIL BODY]\n{parsed_email.body_text}"
        ]
        
        candidate_images: List[Image.Image] = []
        
        for att in parsed_email.attachments:
            fname = att["filename"].lower()
            if fname.endswith(".pdf"):
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
            elif fname.endswith((".jpg", ".jpeg", ".png")):
                import io
                try:
                    img = Image.open(io.BytesIO(att["bytes"]))
                    candidate_images.append(img)
                    combined_text_parts.append(f"\n[ATTACHED DEFECT PHOTO: {att['filename']}]")
                except Exception as e:
                    logger.warning(f"Could not open image attachment {att['filename']}: {e}")

        full_context_text = "\n\n".join(combined_text_parts)

        # 3. Triage Classification
        triage_result = triage_service.classify_text(full_context_text, context_label=f"Email: {parsed_email.subject}")

        # 4. Canonical CaseEnvelope Extraction
        envelope = icsr_extractor.extract_envelope(
            document_text=full_context_text,
            triage_result=triage_result,
            images=candidate_images,
            source_filename=filename,
            message_id=parsed_email.message_id or filename
        )
        envelope.received_date = parsed_email.date
        envelope.metadata["attachment_filenames"] = [att["filename"] for att in parsed_email.attachments]

        # 5. Intra-Document Evidence Retrieval (Step 4)
        try:
            evidence_index = evidence_retriever.build_index_for_email(parsed_email, filename=filename)
            envelope = evidence_retriever.retrieve_for_envelope(envelope, evidence_index)
        except Exception as e:
            logger.warning(f"Intra-document evidence retrieval encountered an error: {e}. Preserving extraction evidence.")

        # 6. Semantic Evidence Verification (Step 5)
        try:
            envelope = evidence_verifier.verify_envelope(envelope, document_context=full_context_text)
        except Exception as e:
            logger.warning(f"Semantic evidence verification encountered an error: {e}. Preserving unverified evidence.")

        # 7. Consistency & Integrity Validation (Step 6)
        try:
            val_report = consistency_validator.validate_envelope(envelope)
            envelope.validation_report = val_report
            envelope.metadata["validation_gating"] = val_report.gating_status.value
        except Exception as e:
            logger.warning(f"Consistency and integrity validation encountered an error: {e}.")

        # 8. Reviewer Brief Synthesis (Step 7)
        try:
            envelope.reviewer_brief = reviewer_brief_builder.build_brief(envelope)
        except Exception as e:
            logger.warning(f"Reviewer brief synthesis encountered an error: {e}.")

        envelope.processing_time_ms = int((time.time() - start_time) * 1000)

        return envelope

    @staticmethod
    def process_eml(eml_bytes: bytes, filename: str = "email.eml") -> ExtractionResult:
        """Legacy compatibility wrapper for process_eml returning ExtractionResult."""
        envelope = DocumentOrchestrator.process_eml_envelope(eml_bytes, filename=filename)
        return envelope_to_legacy(envelope)

    @staticmethod
    def process_pdf_envelope(pdf_bytes: bytes, filename: str = "document.pdf") -> CaseEnvelope:
        """
        Canonical ingestion path for standalone PDF documents.
        Produces a category-aware CaseEnvelope with atomic Fact ledger and Evidence objects.
        """
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

        # 2. Triage Classification
        triage_result = triage_service.classify_text(full_content, context_label=f"PDF: {filename} ({parsed_pdf.flavor})")

        # 3. Canonical CaseEnvelope Extraction
        envelope = icsr_extractor.extract_envelope(
            document_text=full_content,
            triage_result=triage_result,
            images=candidate_images,
            source_filename=filename,
            message_id=filename
        )

        # 4. Intra-Document Evidence Retrieval (Step 4)
        try:
            evidence_index = evidence_retriever.build_index_for_pdf(parsed_pdf, filename=filename)
            envelope = evidence_retriever.retrieve_for_envelope(envelope, evidence_index)
        except Exception as e:
            logger.warning(f"Intra-document evidence retrieval encountered an error: {e}. Preserving extraction evidence.")

        # 5. Semantic Evidence Verification (Step 5)
        try:
            envelope = evidence_verifier.verify_envelope(envelope, document_context=full_content)
        except Exception as e:
            logger.warning(f"Semantic evidence verification encountered an error: {e}. Preserving unverified evidence.")

        envelope.metadata["page_count"] = parsed_pdf.page_count

        # 6. Consistency & Integrity Validation (Step 6)
        try:
            val_report = consistency_validator.validate_envelope(envelope)
            envelope.validation_report = val_report
            envelope.metadata["validation_gating"] = val_report.gating_status.value
        except Exception as e:
            logger.warning(f"Consistency and integrity validation encountered an error: {e}.")

        # 7. Reviewer Brief Synthesis (Step 7)
        try:
            envelope.reviewer_brief = reviewer_brief_builder.build_brief(envelope)
        except Exception as e:
            logger.warning(f"Reviewer brief synthesis encountered an error: {e}.")

        envelope.processing_time_ms = int((time.time() - start_time) * 1000)
        return envelope

    @staticmethod
    def process_pdf(pdf_bytes: bytes, filename: str = "document.pdf") -> ExtractionResult:
        """Legacy compatibility wrapper for process_pdf returning ExtractionResult."""
        envelope = DocumentOrchestrator.process_pdf_envelope(pdf_bytes, filename=filename)
        return envelope_to_legacy(envelope)

    @staticmethod
    def screen_literature_pdf(pdf_bytes: bytes, filename: str = "article.pdf") -> LiteratureScreenResult:
        parsed_pdf = PDFParser.parse_pdf_bytes(pdf_bytes, filename=filename)
        return literature_service.screen_and_split(parsed_pdf.full_text, filename=filename)

orchestrator = DocumentOrchestrator()
