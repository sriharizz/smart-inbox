import pytest
from typing import List, Optional

from app.schemas.fact_contract import (
    Fact, Evidence, FactStatus, VerificationResult, EvidenceType,
    BoundingBox, LocationReference
)
from app.schemas.case_envelope import CaseEnvelope
from app.schemas.triage_schema import TriageResult, CategoryEnum
from app.schemas.category_payloads import IcsrPayload, IcsrPatient, IcsrProduct, IcsrReaction, IcsrReporter
from app.services.evidence_retriever import (
    DocumentChunk, DocumentEvidenceIndex, DocumentChunker,
    EmbeddingProvider, DeterministicEmbeddingProvider, EvidenceRetriever
)
from app.parsers.email_parser import ParsedEmail
from app.parsers.pdf_parser import ParsedPDF


# ============================================================================
# TEST FIXTURES & MOCKS
# ============================================================================

class FlakyFailingEmbeddingProvider(EmbeddingProvider):
    """Mock embedding provider that simulates an API timeout / 429 quota exhaustion."""
    def embed_text(self, text: str) -> Optional[List[float]]:
        return None

    def embed_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        return [None] * len(texts)


@pytest.fixture
def sample_deterministic_provider():
    return DeterministicEmbeddingProvider(dimension=64)


@pytest.fixture
def sample_document_chunks():
    return [
        DocumentChunk(
            chunk_id="doc1:header",
            source_id="email_01.eml",
            source_type=EvidenceType.EMAIL_HEADER,
            page_or_location="Email Header",
            text="From: Dr. Sarah Jenkins, MD <sjenkins@metrohealth.org> | Subject: Suspect DILI with Cardioril",
            location=LocationReference(page_number=1, section="Header", char_start=0, char_end=88)
        ),
        DocumentChunk(
            chunk_id="doc1:p1",
            source_id="email_01.eml",
            source_type=EvidenceType.EMAIL_BODY,
            page_or_location="Email Body, Paragraph 1",
            text="Patient M.K., a 58-year-old female, presented with severe jaundice and scleral icterus after starting Cardioril.",
            location=LocationReference(page_number=1, section="Paragraph 1", char_start=90, char_end=202)
        ),
        DocumentChunk(
            chunk_id="doc1:p2",
            source_id="email_01.eml",
            source_type=EvidenceType.EMAIL_BODY,
            page_or_location="Email Body, Paragraph 2",
            text="The patient was taking Cardioril 20 mg once daily (QD), Lot #CR-2025-0981, Exp 08/2027.",
            location=LocationReference(page_number=1, section="Paragraph 2", char_start=205, char_end=292)
        ),
        DocumentChunk(
            chunk_id="doc1:p3",
            source_id="email_01.eml",
            source_type=EvidenceType.EMAIL_BODY,
            page_or_location="Email Body, Paragraph 3",
            text="Primary clinical diagnosis: Acute Drug-Induced Liver Injury (DILI) with total bilirubin of 6.8 mg/dL.",
            location=LocationReference(page_number=1, section="Paragraph 3", char_start=295, char_end=396)
        ),
        DocumentChunk(
            chunk_id="doc1:table1",
            source_id="cioms_form.pdf",
            source_type=EvidenceType.TABLE_CELL,
            page_or_location="Page 1, Structured Table 1",
            text="| Test Name | Result | Normal Range |\n| ALT | 480 U/L | 7-56 U/L |\n| AST | 390 U/L | 10-40 U/L |",
            location=LocationReference(page_number=1, section="Table 1", table_row=1, table_col=2),
            metadata={"is_table": True}
        )
    ]


# ============================================================================
# 1. EXACT LEXICAL MATCH RETRIEVAL
# ============================================================================

def test_exact_lexical_match_retrieval(sample_document_chunks, sample_deterministic_provider):
    index = DocumentEvidenceIndex(
        document_id="email_01.eml",
        chunks=sample_document_chunks,
        embedding_provider=sample_deterministic_provider
    )

    # Fact: Lot number
    lot_fact = Fact(
        field="lot_number",
        value="CR-2025-0981",
        status=FactStatus.CONFIRMED
    )

    candidates = index.retrieve_candidates(lot_fact, top_k=3)
    assert len(candidates) > 0
    top_candidate = candidates[0]

    assert "CR-2025-0981" in top_candidate.verbatim_snippet
    assert top_candidate.page_or_location == "Email Body, Paragraph 2"
    assert top_candidate.source_id == "email_01.eml"
    assert top_candidate.retrieval_metadata["lexical_score"] >= 0.85
    assert top_candidate.retrieval_metadata["rank"] == 1


# ============================================================================
# 2. SEMANTIC RETRIEVAL FOR PARAPHRASED EVIDENCE
# ============================================================================

def test_semantic_retrieval_for_paraphrased_evidence(sample_deterministic_provider):
    # Chunks with clinical paraphrase of a condition
    chunks = [
        DocumentChunk(
            chunk_id="chk1",
            source_id="case_note.pdf",
            source_type=EvidenceType.PDF_TEXT,
            page_or_location="Page 1, Block 2",
            text="Routine postoperative recovery with normal ambulation and baseline vitals.",
            location=LocationReference(page_number=1, section="Block 2")
        ),
        DocumentChunk(
            chunk_id="chk2",
            source_id="case_note.pdf",
            source_type=EvidenceType.PDF_TEXT,
            page_or_location="Page 1, Block 3",
            text="Widespread epidermal detachment and epidermal necrosis involving erythematous bullous lesions.",
            location=LocationReference(page_number=1, section="Block 3")
        )
    ]
    index = DocumentEvidenceIndex(
        document_id="case_note.pdf",
        chunks=chunks,
        embedding_provider=sample_deterministic_provider
    )

    # Fact uses formal MedDRA PT term: "Toxic Epidermal Necrolysis"
    ten_fact = Fact(
        field="adverse_event",
        value="Toxic Epidermal Necrolysis",
        status=FactStatus.CONFIRMED
    )

    candidates = index.retrieve_candidates(ten_fact, top_k=2)
    assert len(candidates) > 0
    # Top candidate should be chk2 (epidermal necrosis / detachment) rather than routine recovery
    assert candidates[0].retrieval_metadata["chunk_id"] == "chk2"
    assert candidates[0].retrieval_metadata["semantic_score"] > 0.0


# ============================================================================
# 3. HYBRID RANKING (EXACT MATCH PREFERRED)
# ============================================================================

def test_hybrid_ranking_favors_exact_match(sample_document_chunks, sample_deterministic_provider):
    index = DocumentEvidenceIndex(
        document_id="email_01.eml",
        chunks=sample_document_chunks,
        embedding_provider=sample_deterministic_provider
    )

    age_fact = Fact(
        field="patient_age",
        value="58-year-old",
        normalized_value=58,
        status=FactStatus.CONFIRMED
    )

    candidates = index.retrieve_candidates(age_fact, top_k=2)
    assert len(candidates) > 0
    top = candidates[0]
    assert "58-year-old" in top.verbatim_snippet
    assert "hybrid" in top.retrieval_metadata["retrieval_strategy"]
    assert top.retrieval_metadata["relevance_score"] >= 0.70


# ============================================================================
# 4. SOURCE ISOLATION BETWEEN DOCUMENTS / CASES
# ============================================================================

def test_source_isolation_prevents_cross_contamination(sample_deterministic_provider):
    # Case A chunks
    chunks_case_a = [
        DocumentChunk(
            chunk_id="caseA:p1",
            source_id="case_A.eml",
            source_type=EvidenceType.EMAIL_BODY,
            page_or_location="Email Body",
            text="Patient Arthur Pendelton experienced severe anaphylaxis with Renotril.",
            location=LocationReference(page_number=1, section="Body")
        )
    ]
    # Case B chunks (completely different case)
    chunks_case_b = [
        DocumentChunk(
            chunk_id="caseB:p1",
            source_id="case_B.eml",
            source_type=EvidenceType.EMAIL_BODY,
            page_or_location="Email Body",
            text="Patient Maria Garcia experienced acute liver failure with Cardioril.",
            location=LocationReference(page_number=1, section="Body")
        )
    ]

    index_a = DocumentEvidenceIndex("case_A.eml", chunks_case_a, sample_deterministic_provider)
    index_b = DocumentEvidenceIndex("case_B.eml", chunks_case_b, sample_deterministic_provider)

    fact_a = Fact(field="patient_identifier", value="Arthur Pendelton", status=FactStatus.CONFIRMED)
    
    # Searching within index A retrieves Case A evidence
    cands_a = index_a.retrieve_candidates(fact_a)
    assert len(cands_a) == 1
    assert cands_a[0].source_id == "case_A.eml"

    # Searching within index B for Fact A NEVER returns Case A evidence
    cands_b = index_b.retrieve_candidates(fact_a)
    assert len(cands_b) == 0  # Zero cross-case contamination!


# ============================================================================
# 5. PAGE / LOCATION PROVENANCE & TABLE CONTEXT PRESERVATION
# ============================================================================

def test_table_and_location_provenance_preservation(sample_document_chunks, sample_deterministic_provider):
    index = DocumentEvidenceIndex(
        document_id="email_01.eml",
        chunks=sample_document_chunks,
        embedding_provider=sample_deterministic_provider
    )

    lab_fact = Fact(
        field="lab_test",
        value="ALT 480 U/L",
        status=FactStatus.CONFIRMED
    )

    candidates = index.retrieve_candidates(lab_fact, top_k=1)
    assert len(candidates) == 1
    cand = candidates[0]
    assert cand.source_type == EvidenceType.TABLE_CELL
    assert cand.page_or_location == "Page 1, Structured Table 1"
    assert cand.location is not None
    assert cand.location.page_number == 1
    assert cand.location.section == "Table 1"
    assert "ALT" in cand.verbatim_snippet


# ============================================================================
# 6. EXISTING EXTRACTION EVIDENCE IS NOT LOST AND DEDUPLICATED
# ============================================================================

def test_existing_evidence_retention_and_enrichment(sample_document_chunks, sample_deterministic_provider):
    index = DocumentEvidenceIndex("email_01.eml", sample_document_chunks, sample_deterministic_provider)

    # Fact already has extraction-generated evidence with the same snippet
    existing_ev = Evidence(
        source_id="email_01.eml",
        source_type=EvidenceType.EMAIL_BODY,
        page_or_location="Email Body, Paragraph 2",
        verbatim_snippet="The patient was taking Cardioril 20 mg once daily (QD), Lot #CR-2025-0981, Exp 08/2027.",
        retrieval_metadata={"source": "extraction"}
    )
    prod_fact = Fact(
        field="product_dose",
        value="20 mg once daily",
        evidence=[existing_ev],
        status=FactStatus.CONFIRMED
    )

    EvidenceRetriever.enrich_fact_evidence(prod_fact, index, top_k=2)

    # Should retain the evidence and enrich it without creating a duplicate
    assert len(prod_fact.evidence) >= 1
    matched = [e for e in prod_fact.evidence if "CR-2025-0981" in e.verbatim_snippet]
    assert len(matched) == 1  # Deduplicated!
    # Enriched with retrieval relevance score
    assert matched[0].retrieval_metadata.get("relevance_score") is not None


# ============================================================================
# 7. EMBEDDING FAILURE FALLBACK TO LEXICAL RETRIEVAL
# ============================================================================

def test_embedding_failure_fallback_to_lexical(sample_document_chunks):
    # Uses provider that raises/fails
    failing_provider = FlakyFailingEmbeddingProvider()
    index = DocumentEvidenceIndex(
        document_id="email_01.eml",
        chunks=sample_document_chunks,
        embedding_provider=failing_provider
    )

    dili_fact = Fact(
        field="adverse_event",
        value="Acute Drug-Induced Liver Injury (DILI)",
        status=FactStatus.CONFIRMED
    )

    # Should gracefully fall back to exact lexical retrieval without crashing
    candidates = index.retrieve_candidates(dili_fact, top_k=2)
    assert len(candidates) > 0
    top = candidates[0]
    assert "Acute Drug-Induced Liver Injury" in top.verbatim_snippet
    assert top.retrieval_metadata["retrieval_strategy"] == "exact_lexical"
    assert top.retrieval_metadata["semantic_score"] == 0.0


# ============================================================================
# 8. RETRIEVAL METADATA IS RECORDED
# ============================================================================

def test_retrieval_metadata_fields_recorded(sample_document_chunks, sample_deterministic_provider):
    index = DocumentEvidenceIndex("email_01.eml", sample_document_chunks, sample_deterministic_provider)
    fact = Fact(field="reporter_name", value="Dr. Sarah Jenkins", status=FactStatus.CONFIRMED)

    candidates = index.retrieve_candidates(fact, top_k=1)
    assert len(candidates) == 1
    meta = candidates[0].retrieval_metadata

    assert "retrieval_strategy" in meta
    assert "relevance_score" in meta
    assert "lexical_score" in meta
    assert "rank" in meta
    assert meta["rank"] == 1
    assert meta["source"] == "retrieval"


# ============================================================================
# 9. RETRIEVAL DOES NOT SET SUPPORTS OR CONTRADICTS
# ============================================================================

def test_retrieval_does_not_set_supports_or_contradicts(sample_document_chunks, sample_deterministic_provider):
    index = DocumentEvidenceIndex("email_01.eml", sample_document_chunks, sample_deterministic_provider)
    fact = Fact(field="suspect_product", value="Cardioril", status=FactStatus.CONFIRMED)

    candidates = index.retrieve_candidates(fact, top_k=2)
    assert len(candidates) > 0
    for cand in candidates:
        # Step 4 MUST leave verification_result as INSUFFICIENT
        assert cand.verification_result == VerificationResult.INSUFFICIENT
        assert cand.verification_result != VerificationResult.SUPPORTS
        assert cand.verification_result != VerificationResult.CONTRADICTS


# ============================================================================
# 10. NOT_STATED FACTS DO NOT INVENT EVIDENCE
# ============================================================================

def test_not_stated_facts_never_invent_evidence(sample_document_chunks, sample_deterministic_provider):
    index = DocumentEvidenceIndex("email_01.eml", sample_document_chunks, sample_deterministic_provider)
    
    # Fact explicitly NOT_STATED
    not_stated_fact = Fact(
        field="product_frequency",
        value="Not stated",
        status=FactStatus.NOT_STATED,
        evidence=[]
    )

    candidates = index.retrieve_candidates(not_stated_fact)
    assert len(candidates) == 0

    # Enriching fact must keep evidence empty
    EvidenceRetriever.enrich_fact_evidence(not_stated_fact, index)
    assert len(not_stated_fact.evidence) == 0


# ============================================================================
# 11. FULL CASE ENVELOPE RETRIEVAL INTEGRATION
# ============================================================================

def test_retrieve_for_envelope_enriches_all_facts(sample_document_chunks, sample_deterministic_provider):
    index = DocumentEvidenceIndex("email_01.eml", sample_document_chunks, sample_deterministic_provider)

    pt_fact = Fact(field="patient_age", value="58-year-old", status=FactStatus.CONFIRMED)
    prod_fact = Fact(field="suspect_product", value="Cardioril 20 mg", status=FactStatus.CONFIRMED)
    rx_fact = Fact(field="adverse_event", value="Acute Drug-Induced Liver Injury", status=FactStatus.CONFIRMED)
    rep_fact = Fact(field="reporter_name", value="Dr. Sarah Jenkins", status=FactStatus.CONFIRMED)
    unstated_fact = Fact(field="treatment_stop_date", value="Not stated", status=FactStatus.NOT_STATED)

    all_facts = [pt_fact, prod_fact, rx_fact, rep_fact, unstated_fact]

    patient = IcsrPatient(age="58-year-old", facts=[pt_fact])
    product = IcsrProduct(product_name="Cardioril 20 mg", facts=[prod_fact])
    reaction = IcsrReaction(adverse_event="Acute Drug-Induced Liver Injury", facts=[rx_fact])
    reporter = IcsrReporter(name="Dr. Sarah Jenkins", facts=[rep_fact])

    icsr = IcsrPayload(
        patient=patient,
        product=product,
        reaction=reaction,
        reporter=reporter,
        facts=all_facts
    )

    envelope = CaseEnvelope(
        envelope_id="env-test-01",
        message_id="<test@clinevo.com>",
        source_filename="email_01.eml",
        received_date="2025-11-12",
        language_detected="English",
        triage=TriageResult(
            is_multi_label=False,
            primary_category=CategoryEnum.SAFETY_REPORT_ICSR,
            labels=[],
            executive_summary="Test summary"
        ),
        document_summary="Test document summary",
        reviewer_summary="Reviewer brief",
        icsr=icsr,
        facts=all_facts
    )

    enriched_envelope = EvidenceRetriever.retrieve_for_envelope(envelope, index, top_k=2)

    # Verify that facts now have candidate evidence attached
    assert len(pt_fact.evidence) > 0
    assert len(prod_fact.evidence) > 0
    assert len(rx_fact.evidence) > 0
    assert len(rep_fact.evidence) > 0
    # Unstated fact strictly remains empty
    assert len(unstated_fact.evidence) == 0

    # Verify evidence provenance
    assert pt_fact.evidence[0].source_id == "email_01.eml"
    assert "58-year-old" in pt_fact.evidence[0].verbatim_snippet
    assert pt_fact.evidence[0].verification_result == VerificationResult.INSUFFICIENT
