import re
import math
import uuid
import hashlib
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

from app.core.config import settings
from app.core.gemini_client import gemini_client
from app.schemas.fact_contract import (
    Fact, Evidence, FactStatus, VerificationResult, EvidenceType,
    BoundingBox, LocationReference
)
from app.schemas.case_envelope import CaseEnvelope
from app.parsers.email_parser import ParsedEmail
from app.parsers.pdf_parser import ParsedPDF, PDFParser

logger = logging.getLogger("smartinbox.retrieval")

# ============================================================================
# 1. DOCUMENT CHUNK MODEL
# ============================================================================

@dataclass
class DocumentChunk:
    """
    Fine-grained, provenance-preserving unit of document text for intra-document retrieval.
    """
    chunk_id: str
    source_id: str
    source_type: EvidenceType
    page_or_location: str
    text: str
    location: Optional[LocationReference] = None
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# 2. EMBEDDING PROVIDER ABSTRACTION
# ============================================================================

class EmbeddingProvider(ABC):
    """
    Abstract embedding provider decoupling the retrieval engine from concrete embedding vendors.
    """
    @abstractmethod
    def embed_text(self, text: str) -> Optional[List[float]]:
        """Generate a dense vector for a single text. Returns None on failure."""
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """Generate dense vectors for multiple texts. Fails gracefully per item."""
        pass


class GeminiEmbeddingProvider(EmbeddingProvider):
    """
    Live Google GenAI embedding provider using gemini-embedding-001.
    Includes graceful error handling and fallback on rate limits or API failure.
    """
    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or settings.EMBEDDING_MODEL_NAME
        self._quota_exhausted: bool = False

    def embed_text(self, text: str) -> Optional[List[float]]:
        if self._quota_exhausted:
            return None
        clean_text = text.strip()
        if not clean_text:
            return None
        try:
            if not gemini_client._client:
                gemini_client._init_client()
            if not gemini_client._client:
                return None
            res = gemini_client._client.models.embed_content(
                model=self.model_name,
                contents=clean_text[:4000]
            )
            if hasattr(res, "embedding") and res.embedding and hasattr(res.embedding, "values"):
                return list(res.embedding.values)
            elif hasattr(res, "embeddings") and res.embeddings and len(res.embeddings) > 0:
                return list(res.embeddings[0].values)
            return None
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                self._quota_exhausted = True
                logger.warning("Gemini embedding quota exhausted. Circuit-breaker engaged; using lexical retrieval.")
            else:
                logger.warning(f"Gemini embedding failed for text snippet: {e}. Falling back to lexical retrieval.")
            return None

    def embed_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        results: List[Optional[List[float]]] = []
        for t in texts:
            if self._quota_exhausted:
                results.append(None)
            else:
                results.append(self.embed_text(t))
        return results


class DeterministicEmbeddingProvider(EmbeddingProvider):
    """
    Lightweight, deterministic embedding provider for offline testing and zero-API fallback.
    Uses character n-gram hashing and term frequency projected to a fixed-dimension unit sphere.
    """
    def __init__(self, dimension: int = 128):
        self.dimension = dimension

    def _hash_token(self, token: str) -> int:
        h = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
        return h % self.dimension

    def embed_text(self, text: str) -> Optional[List[float]]:
        clean_text = text.strip().lower()
        if not clean_text:
            return None
        vec = [0.0] * self.dimension
        tokens = re.findall(r"\b\w+\b", clean_text)
        if not tokens:
            return None
        
        # Word unigrams
        for t in tokens:
            idx = self._hash_token(t)
            vec[idx] += 1.0
            # Character n-grams for subword / morphological variation (e.g. necrolysis / necrosis)
            if len(t) >= 3:
                for n in (3, 4):
                    if len(t) >= n:
                        for i in range(len(t) - n + 1):
                            ngram = t[i:i+n]
                            vec[self._hash_token(ngram)] += 0.5
        
        # Word bigrams for local context
        for i in range(len(tokens) - 1):
            bigram = f"{tokens[i]}_{tokens[i+1]}"
            idx = self._hash_token(bigram)
            vec[idx] += 1.5

        # Normalize to unit length
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]
        return vec

    def embed_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        return [self.embed_text(t) for t in texts]


# ============================================================================
# 3. DOCUMENT CHUNKER
# ============================================================================

class DocumentChunker:
    """
    Deterministic chunking engine preserving page boundaries, visual coordinates, and tables.
    """
    @staticmethod
    def chunk_email(parsed_email: ParsedEmail, filename: str = "email.eml") -> List[DocumentChunk]:
        chunks: List[DocumentChunk] = []

        # 1. Header Metadata Chunk
        header_text = (
            f"From: {parsed_email.sender} <{parsed_email.sender_email}>\n"
            f"Date: {parsed_email.date}\n"
            f"Subject: {parsed_email.subject}\n"
            f"Message-ID: {parsed_email.message_id}"
        )
        chunks.append(DocumentChunk(
            chunk_id=f"{filename}:header",
            source_id=filename,
            source_type=EvidenceType.EMAIL_HEADER,
            page_or_location="Email Header",
            text=header_text,
            location=LocationReference(
                page_number=1,
                section="Email Header",
                char_start=0,
                char_end=len(header_text)
            )
        ))

        # 2. Body Text Paragraphs
        body = parsed_email.body_text or ""
        paragraphs = re.split(r"\n\s*\n", body)
        current_offset = 0

        for idx, para in enumerate(paragraphs):
            clean_para = para.strip()
            if not clean_para:
                continue
            
            p_start = body.find(clean_para, current_offset)
            if p_start == -1:
                p_start = current_offset
            p_end = p_start + len(clean_para)
            current_offset = p_end

            chunks.append(DocumentChunk(
                chunk_id=f"{filename}:body:p{idx+1}",
                source_id=filename,
                source_type=EvidenceType.EMAIL_BODY,
                page_or_location=f"Email Body, Paragraph {idx+1}",
                text=clean_para,
                location=LocationReference(
                    page_number=1,
                    section=f"Paragraph {idx+1}",
                    char_start=p_start,
                    char_end=p_end
                )
            ))

        # 3. Process Attached PDFs
        for att in parsed_email.attachments:
            att_name = att.get("filename", "attachment.pdf")
            att_bytes = att.get("bytes", b"")
            if att_name.lower().endswith(".pdf") and att_bytes:
                try:
                    pdf_parsed = PDFParser.parse_pdf_bytes(att_bytes, filename=att_name)
                    pdf_chunks = DocumentChunker.chunk_pdf(pdf_parsed, filename=att_name)
                    chunks.extend(pdf_chunks)
                except Exception as e:
                    logger.warning(f"Could not chunk attached PDF {att_name}: {e}")
            elif att_name.lower().endswith((".jpg", ".jpeg", ".png")):
                chunks.append(DocumentChunk(
                    chunk_id=f"{att_name}:image",
                    source_id=att_name,
                    source_type=EvidenceType.DEFECT_IMAGE,
                    page_or_location=f"Attached Defect Photo: {att_name}",
                    text=f"Photographic exhibit asset: {att_name}",
                    location=LocationReference(
                        page_number=1,
                        section="Exhibit Photo"
                    ),
                    metadata={"is_image": True}
                ))

        return chunks

    @staticmethod
    def chunk_pdf(parsed_pdf: ParsedPDF, filename: str = "document.pdf") -> List[DocumentChunk]:
        chunks: List[DocumentChunk] = []

        for p_num in range(1, parsed_pdf.page_count + 1):
            # A. Visual text blocks with coordinates
            blocks = parsed_pdf.blocks_by_page.get(p_num, [])
            if blocks:
                for b in blocks:
                    bbox = b.get("bbox")
                    b_no = b.get("block_no", 0)
                    b_text = b.get("text", "").strip()
                    if not b_text or len(b_text) < 3:
                        continue
                    
                    loc_ref = LocationReference(
                        page_number=p_num,
                        section=f"Block {b_no}",
                        bounding_box=BoundingBox(
                            x0=bbox[0],
                            y0=bbox[1],
                            x1=bbox[2],
                            y1=bbox[3],
                            page_number=p_num
                        ) if bbox else None
                    )

                    chunks.append(DocumentChunk(
                        chunk_id=f"{filename}:p{p_num}:b{b_no}",
                        source_id=filename,
                        source_type=EvidenceType.PDF_TEXT if parsed_pdf.flavor != "scanned_handwritten" else EvidenceType.SCANNED_PAGE,
                        page_or_location=f"Page {p_num}, Block {b_no}",
                        text=b_text,
                        location=loc_ref
                    ))
            else:
                # Fallback to plain text paragraphs on page
                page_raw = parsed_pdf.text_by_page.get(p_num, "")
                for idx, para in enumerate(re.split(r"\n\s*\n", page_raw)):
                    clean_para = para.strip()
                    if len(clean_para) < 3:
                        continue
                    chunks.append(DocumentChunk(
                        chunk_id=f"{filename}:p{p_num}:para{idx+1}",
                        source_id=filename,
                        source_type=EvidenceType.PDF_TEXT,
                        page_or_location=f"Page {p_num}, Paragraph {idx+1}",
                        text=clean_para,
                        location=LocationReference(page_number=p_num, section=f"Paragraph {idx+1}")
                    ))

            # B. Structured Tables on Page (Row-level chunks with exact bboxes + full table markdown)
            table_rows = parsed_pdf.table_rows_by_page.get(p_num, [])
            for r_info in table_rows:
                r_text = r_info.get("text", "").strip()
                if not r_text or len(r_text) < 3:
                    continue
                r_bbox = r_info.get("bbox")
                bbox_obj = None
                if r_bbox:
                    bbox_obj = BoundingBox(
                        x0=float(r_bbox[0]),
                        y0=float(r_bbox[1]),
                        x1=float(r_bbox[2]),
                        y1=float(r_bbox[3]),
                        page_number=p_num
                    )
                t_no = r_info.get("table_no", 0) + 1
                r_no = r_info.get("row_no", 0)
                chunks.append(DocumentChunk(
                    chunk_id=f"{filename}:p{p_num}:t{t_no}:r{r_no}",
                    source_id=filename,
                    source_type=EvidenceType.TABLE_CELL,
                    page_or_location=f"Page {p_num}, Table {t_no} Row {r_no}",
                    text=r_text,
                    location=LocationReference(
                        page_number=p_num,
                        section=f"Table {t_no} Row {r_no}",
                        bounding_box=bbox_obj
                    ),
                    metadata={"is_table_row": True, "table_no": t_no, "row_no": r_no}
                ))

            tables = parsed_pdf.tables_by_page.get(p_num, [])
            for t_idx, tbl_md in enumerate(tables):
                clean_tbl = tbl_md.strip()
                if not clean_tbl:
                    continue
                chunks.append(DocumentChunk(
                    chunk_id=f"{filename}:p{p_num}:tbl{t_idx+1}",
                    source_id=filename,
                    source_type=EvidenceType.TABLE_CELL,
                    page_or_location=f"Page {p_num}, Structured Table {t_idx+1}",
                    text=clean_tbl,
                    location=LocationReference(page_number=p_num, section=f"Table {t_idx+1}"),
                    metadata={"is_table": True}
                ))

            # C. Embedded Images on Page
            page_images = [img for img in parsed_pdf.images if img.get("page") == p_num]
            for img_idx, img_info in enumerate(page_images):
                raw_bbox = img_info.get("bbox")
                bbox_obj = None
                if raw_bbox:
                    bbox_obj = BoundingBox(
                        x0=float(raw_bbox[0]),
                        y0=float(raw_bbox[1]),
                        x1=float(raw_bbox[2]),
                        y1=float(raw_bbox[3]),
                        page_number=p_num
                    )
                chunks.append(DocumentChunk(
                    chunk_id=f"{filename}:p{p_num}:img{img_idx+1}",
                    source_id=filename,
                    source_type=EvidenceType.DEFECT_IMAGE,
                    page_or_location=f"Page {p_num}, Defect Photograph",
                    text=f"Embedded photographic exhibit asset on page {p_num} of {filename}: defect photograph",
                    location=LocationReference(
                        page_number=p_num,
                        section="Defect Photograph",
                        bounding_box=bbox_obj
                    ),
                    metadata={"is_image": True, "page": p_num}
                ))

        return chunks


# ============================================================================
# 4. INTRA-DOCUMENT EVIDENCE INDEX
# ============================================================================

class DocumentEvidenceIndex:
    """
    Strictly isolated per-document in-memory index.
    Searches ONLY within chunks of the same intake document package to prevent cross-case contamination.
    """
    def __init__(
        self,
        document_id: str,
        chunks: List[DocumentChunk],
        embedding_provider: Optional[EmbeddingProvider] = None
    ):
        self.document_id = document_id
        self.chunks = chunks
        self.embedding_provider = embedding_provider
        self._embeddings_computed = False

    def _ensure_chunk_embeddings(self):
        """Computes embeddings for chunks lazily if an embedding provider is active."""
        if self._embeddings_computed or not self.embedding_provider or not settings.ENABLE_SEMANTIC_RETRIEVAL:
            return
        
        texts_to_embed = [c.text for c in self.chunks]
        try:
            embs = self.embedding_provider.embed_batch(texts_to_embed)
            for c, emb in zip(self.chunks, embs):
                c.embedding = emb
            self._embeddings_computed = True
        except Exception as e:
            logger.warning(f"Batch embedding failed: {e}. Pure lexical retrieval will be used.")
            self._embeddings_computed = True

    @staticmethod
    def _cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        if not vec_a or not vec_b or len(vec_a) != len(vec_b):
            return 0.0
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))
        if norm_a <= 0 or norm_b <= 0:
            return 0.0
        return max(0.0, dot / (norm_a * norm_b))

    def _compute_lexical_score(self, fact: Fact, chunk: DocumentChunk) -> float:
        """
        Computes source-faithful lexical score between fact and chunk text.
        Awards bonuses for exact substring matches, normalized entity mentions, and field context.
        Prioritizes structured table-row evidence for structured facts (labs, biomarkers) when
        both analyte and value tokens are present.
        """
        val = str(fact.value).strip().lower()
        chunk_text = chunk.text.lower()
        score = 0.0

        # Detect structured fact and table candidate generically
        is_structured_fact = (
            fact.field.startswith(("lab_", "biomarker_", "diagnostic_", "test_"))
            or bool(fact.metadata and (fact.metadata.get("is_lab") or fact.metadata.get("is_structured")))
        )
        is_table_candidate = (
            chunk.source_type == EvidenceType.TABLE_CELL
            or bool(chunk.metadata and (chunk.metadata.get("is_table_row") or chunk.metadata.get("is_table")))
        )

        # 1. Exact verbatim substring match (strongest signal)
        if len(val) >= 3 and val in chunk_text:
            score = max(score, 0.90)

        # 2. Normalized value match (e.g. integer age 58, ISO date 2025-11-15)
        if fact.normalized_value is not None:
            norm_str = str(fact.normalized_value).strip().lower()
            if len(norm_str) >= 2 and norm_str in chunk_text:
                score = max(score, 0.80)

        # 3. Token overlap (Jaccard-like content word matching)
        stopwords = {
            "the", "a", "an", "and", "or", "in", "on", "at", "to", "for", "with",
            "is", "was", "are", "were", "of", "by", "as", "from", "it", "this",
            "patient", "level", "levels", "test", "tests", "value", "values"
        }
        val_tokens = set(re.findall(r"\b[a-zA-Z0-9\.\-\_]{2,}\b", val)) - stopwords
        chunk_tokens = set(re.findall(r"\b[a-zA-Z0-9\.\-\_]{2,}\b", chunk_text))

        if val_tokens:
            overlap = len(val_tokens & chunk_tokens) / len(val_tokens)
            score = max(score, overlap * 0.75)

        # 4. Field keyword context boost (only when there is some match on the value/entity)
        if score > 0.0:
            field_keywords = [
                kw for kw in fact.field.replace("_", " ").lower().split()
                if kw not in ("lab", "test", "biomarker", "diagnostic", "level", "levels") and len(kw) >= 2
            ]
            for kw in field_keywords:
                if len(kw) >= 2 and (kw in chunk_text or (len(kw) >= 4 and kw[:4] in chunk_text)):
                    score += 0.10
                    break

        # 5. Patient scope boost / isolation (crucial for multi-case documents)
        scope = fact.metadata.get("patient_scope") if fact.metadata else None
        has_other = False
        if scope and score > 0.0:
            scope_clean = str(scope).strip().lower()
            other_scopes = fact.metadata.get("other_scopes", [])
            has_other = any(str(o).strip().lower() in chunk_text for o in other_scopes if str(o).strip())
            
            if len(scope_clean) >= 2 and scope_clean in chunk_text:
                if not has_other:
                    # Pure single-patient chunk (e.g. specific case section or dedicated table row)
                    score += 0.40
                else:
                    # Multi-patient summary or abstract containing conflicting patients
                    score -= 0.20
            elif has_other:
                # Belongs exclusively to a different patient
                score -= 0.60

        # 6. Generic Structured-Table Evidence Priority for Labs / Biomarkers
        if is_structured_fact:
            if is_table_candidate:
                raw_field_tokens = [
                    tok for tok in re.findall(r"[a-zA-Z]+", fact.field.lower())
                    if tok not in ("lab", "test", "biomarker", "diagnostic", "level", "levels") and len(tok) >= 2
                ]
                non_num_val_tokens = [
                    tok for tok in re.findall(r"[a-zA-Z]+", val)
                    if tok not in stopwords and tok not in ("u/l", "mg/dl", "ng/ml", "pg/ml", "g/dl", "mmol/l", "iu/l", "fl", "iu", "ul", "l", "ml") and len(tok) >= 2
                ]
                analyte_tokens = set(raw_field_tokens + non_num_val_tokens)

                num_val_tokens = set(re.findall(r"\b\d+(?:\.\d+)?(?:\:\d+)?\b", val))
                if not num_val_tokens:
                    num_val_tokens = {tok for tok in val_tokens if any(c.isdigit() for c in tok)}

                has_analyte = any(
                    tok in chunk_text or (len(tok) >= 4 and tok[:4] in chunk_text)
                    for tok in analyte_tokens
                )
                has_value = any(tok in chunk_text for tok in num_val_tokens) if num_val_tokens else (score > 0.5)

                if has_analyte and has_value and not has_other:
                    score = max(score, 0.98)
            else:
                score = min(score, 0.88)

        return min(1.0, max(0.0, score))

    def retrieve_candidates(
        self,
        fact: Fact,
        top_k: int = 3,
        min_relevance: float = 0.15
    ) -> List[Evidence]:
        """
        Retrieves top-K candidate evidence passages from this document for the given Fact.
        Combines exact lexical and semantic embedding signals.
        Leaves verification_result as INSUFFICIENT (verification is strictly Step 5).
        """
        # RULE: NOT_STATED facts must never trigger evidence invention
        if fact.status == FactStatus.NOT_STATED or str(fact.value).strip().lower() in ["not stated", "none", "unknown"]:
            return []

        self._ensure_chunk_embeddings()

        # Generate query embedding if provider available
        query_text = f"{fact.field.replace('_', ' ')}: {fact.value}"
        query_emb = None
        if self.embedding_provider and settings.ENABLE_SEMANTIC_RETRIEVAL:
            query_emb = self.embedding_provider.embed_text(query_text)

        candidates: List[Tuple[float, float, float, str, DocumentChunk]] = []

        for chunk in self.chunks:
            lex_score = self._compute_lexical_score(fact, chunk)
            
            sem_score = 0.0
            if query_emb and chunk.embedding:
                sem_score = self._cosine_similarity(query_emb, chunk.embedding)

            # Hybrid ranking formulation
            if sem_score > 0.0:
                if lex_score >= 0.70:
                    # Strong lexical match prioritized
                    relevance = (0.65 * lex_score) + (0.35 * sem_score)
                    strat = "hybrid_lexical_lead"
                elif lex_score < 0.30 and sem_score >= 0.40:
                    # Semantic paraphrase match surfaced
                    relevance = (0.30 * lex_score) + (0.70 * sem_score)
                    strat = "hybrid_semantic_lead"
                elif lex_score > 0.0:
                    relevance = (0.50 * lex_score) + (0.50 * sem_score)
                    strat = "hybrid_balanced"
                else:
                    # lex_score == 0.0: only consider if semantic similarity is substantive (>= 0.40)
                    relevance = sem_score if sem_score >= 0.40 else 0.0
                    strat = "semantic"
            else:
                relevance = lex_score
                strat = "exact_lexical"

            if relevance >= min_relevance:
                candidates.append((relevance, lex_score, sem_score, strat, chunk))

        # Sort by relevance descending with structured table priority tie-breaking
        is_struct = fact.field.startswith(("lab_", "biomarker_", "diagnostic_", "test_")) or bool(
            fact.metadata and (fact.metadata.get("is_lab") or fact.metadata.get("is_structured"))
        )
        candidates.sort(
            key=lambda x: (
                x[0],
                1 if (is_struct and (x[4].source_type == EvidenceType.TABLE_CELL or x[4].metadata.get("is_table_row"))) else 0,
                1 if (x[4].location and x[4].location.bounding_box is not None) else 0
            ),
            reverse=True
        )
        top_candidates = candidates[:top_k]

        evidence_items: List[Evidence] = []
        for rank, (rel_score, l_score, s_score, strat, chk) in enumerate(top_candidates):
            evidence_items.append(Evidence(
                evidence_id=str(uuid.uuid4())[:8],
                source_id=chk.source_id,
                source_type=chk.source_type,
                page_or_location=chk.page_or_location,
                verbatim_snippet=chk.text,
                location=chk.location,
                retrieval_metadata={
                    "retrieval_strategy": strat,
                    "relevance_score": round(rel_score, 4),
                    "lexical_score": round(l_score, 4),
                    "semantic_score": round(s_score, 4),
                    "rank": rank + 1,
                    "chunk_id": chk.chunk_id,
                    "source": "retrieval",
                },
                verification_result=VerificationResult.INSUFFICIENT  # Step 5 responsibility
            ))

        return evidence_items


# ============================================================================
# 5. EVIDENCE RETRIEVER ORCHESTRATOR
# ============================================================================

class EvidenceRetriever:
    """
    Intra-document evidence retriever orchestrating chunk indexing and candidate association.
    """
    @staticmethod
    def get_default_provider() -> EmbeddingProvider:
        if settings.GEMINI_API_KEY and settings.ENABLE_SEMANTIC_RETRIEVAL:
            return GeminiEmbeddingProvider()
        return DeterministicEmbeddingProvider()

    @staticmethod
    def build_index_for_email(
        parsed_email: ParsedEmail,
        filename: str = "email.eml",
        provider: Optional[EmbeddingProvider] = None
    ) -> DocumentEvidenceIndex:
        chunks = DocumentChunker.chunk_email(parsed_email, filename=filename)
        prov = provider or EvidenceRetriever.get_default_provider()
        return DocumentEvidenceIndex(document_id=filename, chunks=chunks, embedding_provider=prov)

    @staticmethod
    def build_index_for_pdf(
        parsed_pdf: ParsedPDF,
        filename: str = "document.pdf",
        provider: Optional[EmbeddingProvider] = None
    ) -> DocumentEvidenceIndex:
        chunks = DocumentChunker.chunk_pdf(parsed_pdf, filename=filename)
        prov = provider or EvidenceRetriever.get_default_provider()
        return DocumentEvidenceIndex(document_id=filename, chunks=chunks, embedding_provider=prov)

    @staticmethod
    def enrich_fact_evidence(
        fact: Fact,
        index: DocumentEvidenceIndex,
        top_k: int = 3
    ) -> Fact:
        """
        Enriches a single Fact with candidate Evidence from the intra-document index.
        Preserves existing extraction evidence while deduplicating redundant snippets.
        """
        if fact.status == FactStatus.NOT_STATED:
            return fact

        retrieved_candidates = index.retrieve_candidates(fact, top_k=top_k)
        if not retrieved_candidates:
            return fact

        # Deduplicate and merge with existing extraction evidence
        existing_evidence = list(fact.evidence)
        new_evidence_list: List[Evidence] = []

        # Retain existing extraction evidence, annotating source
        for ev in existing_evidence:
            if "source" not in ev.retrieval_metadata:
                ev.retrieval_metadata["source"] = "extraction"
            new_evidence_list.append(ev)

        # Merge retrieved candidates if distinct from existing
        for cand in retrieved_candidates:
            is_dup = False
            cand_norm = re.sub(r"\s+", " ", cand.verbatim_snippet.strip().lower())
            for ex in new_evidence_list:
                ex_norm = re.sub(r"\s+", " ", ex.verbatim_snippet.strip().lower())
                # If exact duplicate or substantial substring match
                if ex.source_id == cand.source_id and (cand_norm in ex_norm or ex_norm in cand_norm):
                    # Enrich existing evidence with retrieval scores and location coordinates if missing
                    ex.retrieval_metadata["relevance_score"] = cand.retrieval_metadata.get("relevance_score")
                    ex.retrieval_metadata["rank"] = cand.retrieval_metadata.get("rank")
                    if not ex.location and cand.location:
                        ex.location = cand.location
                    is_dup = True
                    break
            
            if not is_dup:
                new_evidence_list.append(cand)

        fact.evidence = new_evidence_list
        return fact

    @staticmethod
    def retrieve_for_envelope(
        envelope: CaseEnvelope,
        index: DocumentEvidenceIndex,
        top_k: int = 3
    ) -> CaseEnvelope:
        """
        Intra-document evidence retrieval across all facts in a CaseEnvelope.
        Enriches the top-level Fact ledger as well as category-specific payload facts.
        """
        # 1. Enrich top-level Fact ledger
        facts_list = getattr(envelope, "fact_ledger", None) or getattr(envelope, "facts", [])
        for fact in facts_list:
            EvidenceRetriever.enrich_fact_evidence(fact, index, top_k=top_k)

        # 2. Synchronize category payloads
        if envelope.icsr:
            for f in envelope.icsr.facts:
                EvidenceRetriever.enrich_fact_evidence(f, index, top_k=top_k)
            for f in envelope.icsr.patient.facts:
                EvidenceRetriever.enrich_fact_evidence(f, index, top_k=top_k)
            for f in envelope.icsr.reporter.facts:
                EvidenceRetriever.enrich_fact_evidence(f, index, top_k=top_k)
            for f in envelope.icsr.product.facts:
                EvidenceRetriever.enrich_fact_evidence(f, index, top_k=top_k)
        pqc_payload = getattr(envelope, "pqc", None) or getattr(envelope, "quality_complaint", None)
        if pqc_payload and hasattr(pqc_payload, "facts"):
            for f in pqc_payload.facts:
                EvidenceRetriever.enrich_fact_evidence(f, index, top_k=top_k)

        mi_payload = getattr(envelope, "mi", None) or getattr(envelope, "medical_info", None)
        if mi_payload and hasattr(mi_payload, "facts"):
            for f in mi_payload.facts:
                EvidenceRetriever.enrich_fact_evidence(f, index, top_k=top_k)

        nr_payload = getattr(envelope, "not_relevant", None)
        if nr_payload and hasattr(nr_payload, "facts"):
            for f in nr_payload.facts:
                EvidenceRetriever.enrich_fact_evidence(f, index, top_k=top_k)

        return envelope

evidence_retriever = EvidenceRetriever()
