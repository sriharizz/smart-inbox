import time
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from pydantic import BaseModel

from app.core.config import settings
from app.schemas.triage_schema import TriageResult
from app.schemas.extraction_schema import ExtractionResult
from app.schemas.case_envelope import CaseEnvelope
from app.schemas.literature_schema import LiteratureScreenResult
from app.services.triage_service import triage_service
from app.services.icsr_extractor import icsr_extractor
from app.services.orchestrator import orchestrator
from app.services.cache_service import cache_service

api_router = APIRouter()

class TextTriageRequest(BaseModel):
    text: str
    context_label: Optional[str] = "Document"

class TextExtractionRequest(BaseModel):
    text: str
    triage: TriageResult
    source_filename: Optional[str] = "document.txt"

@api_router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "primary_model": settings.MODEL_NAME,
        "fallback_model": settings.FALLBACK_MODEL_NAME,
        "cache_enabled": settings.USE_LOCAL_CACHE,
        "indexed_cases": len(cache_service.benchmark_data)
    }

@api_router.post("/triage", response_model=TriageResult)
def triage_text(payload: TextTriageRequest):
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")
    return triage_service.classify_text(payload.text, context_label=payload.context_label)

# -------------------------------------------------------------
# Canonical CaseEnvelope Endpoints
# -------------------------------------------------------------

@api_router.post("/extract-envelope", response_model=CaseEnvelope)
def extract_envelope(payload: TextExtractionRequest):
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")
    return icsr_extractor.extract_envelope(
        document_text=payload.text,
        triage_result=payload.triage,
        source_filename=payload.source_filename
    )

@api_router.post("/process-eml-envelope", response_model=CaseEnvelope)
async def process_eml_envelope_file(file: UploadFile = File(...), fresh: bool = Query(default=True)):
    if not file.filename.lower().endswith((".eml", ".msg")):
        raise HTTPException(status_code=400, detail="Only .eml files are accepted for this endpoint.")
    eml_bytes = await file.read()
    return orchestrator.process_eml_envelope(eml_bytes, filename=file.filename, fresh_processing=fresh)

@api_router.post("/process-pdf-envelope", response_model=CaseEnvelope)
async def process_pdf_envelope_file(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only .pdf files are accepted for this endpoint.")
    pdf_bytes = await file.read()
    return orchestrator.process_pdf_envelope(pdf_bytes, filename=file.filename)

# -------------------------------------------------------------
# Legacy Compatibility Endpoints
# -------------------------------------------------------------

@api_router.post("/extract", response_model=ExtractionResult)
def extract_facts(payload: TextExtractionRequest):
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")
    return icsr_extractor.extract_facts(
        document_text=payload.text,
        triage_result=payload.triage,
        source_filename=payload.source_filename
    )

@api_router.post("/process-eml", response_model=ExtractionResult)
async def process_eml_file(file: UploadFile = File(...), fresh: bool = Query(default=True)):
    if not file.filename.lower().endswith((".eml", ".msg")):
        raise HTTPException(status_code=400, detail="Only .eml files are accepted for this endpoint.")
    eml_bytes = await file.read()
    return orchestrator.process_eml(eml_bytes, filename=file.filename, fresh_processing=fresh)

@api_router.post("/process-pdf", response_model=ExtractionResult)
async def process_pdf_file(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only .pdf files are accepted for this endpoint.")
    pdf_bytes = await file.read()
    return orchestrator.process_pdf(pdf_bytes, filename=file.filename)

@api_router.post("/literature/screen-and-split", response_model=LiteratureScreenResult)
async def screen_and_split_literature(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only .pdf files are accepted for literature screening.")
    pdf_bytes = await file.read()
    return orchestrator.screen_literature_pdf(pdf_bytes, filename=file.filename)
