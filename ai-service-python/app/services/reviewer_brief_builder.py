import time
from typing import Optional, List, Dict, Any, Set

from app.schemas.case_envelope import (
    CaseEnvelope, ReviewerBrief, ReviewFocusItem, ReviewFocusCategory, FactSummaryStats
)
from app.schemas.fact_contract import Fact, Evidence, FactStatus, VerificationResult
from app.schemas.validation_schema import ValidationGatingStatus, ValidationSeverity


class ReviewerBriefBuilder:
    """
    Step 7: Synthesizes a canonical CaseEnvelope into a reviewer-first decision brief (ReviewerBrief).
    Calculates attention focus items, certainty metrics, clinical urgency,
    and structured fact summaries to minimize reviewer cognitive load.
    """

    CRITICAL_FIELDS: Set[str] = {
        "suspect_product",
        "adverse_event",
        "patient_age",
        "reporter_name",
        "product_name",
        "defect_type",
        "lot_number",
        "question_text"
    }

    @classmethod
    def build_brief(cls, envelope: CaseEnvelope) -> ReviewerBrief:
        """Constructs a comprehensive, reviewer-focused ReviewerBrief from a CaseEnvelope."""
        # 1. Basic Metadata
        case_id = envelope.message_id or envelope.source_filename or envelope.envelope_id
        subject = envelope.document_summary[:80] if envelope.document_summary != "Not stated" else "Clinical Safety Intake"
        if envelope.icsr and envelope.icsr.patient and envelope.icsr.patient.identifier != "Not stated":
            subject = f"ICSR: {envelope.icsr.patient.identifier}"
            if envelope.icsr.reaction and envelope.icsr.reaction.adverse_event != "Not stated":
                subject += f" - {envelope.icsr.reaction.adverse_event}"

        sender = "Healthcare Provider / Consumer"
        if envelope.icsr and envelope.icsr.reporter and envelope.icsr.reporter.name != "Not stated":
            sender = envelope.icsr.reporter.name
            if envelope.icsr.reporter.institution != "Not stated":
                sender += f" ({envelope.icsr.reporter.institution})"

        received_date = envelope.received_date or "Not stated"

        # Categories
        primary_cat = envelope.triage.primary_category.value if hasattr(envelope.triage.primary_category, "value") else str(envelope.triage.primary_category)
        all_cats = [lbl.category.value for lbl in envelope.triage.labels] if envelope.triage.labels else [primary_cat]

        # 2. Fact Statistics & Audit
        stats = FactSummaryStats(
            total_facts=len(envelope.fact_ledger),
            confirmed_count=sum(1 for f in envelope.fact_ledger if f.status == FactStatus.CONFIRMED),
            not_stated_count=sum(1 for f in envelope.fact_ledger if f.status == FactStatus.NOT_STATED),
            uncertain_count=sum(1 for f in envelope.fact_ledger if f.status == FactStatus.UNCERTAIN),
            conflict_count=sum(1 for f in envelope.fact_ledger if f.status == FactStatus.CONFLICT)
        )

        # 3. Collect Unique Evidence Items
        evidence_ledger: List[Evidence] = []
        seen_ev_ids: Set[str] = set()
        for f in envelope.fact_ledger:
            for ev in f.evidence:
                if ev.evidence_id not in seen_ev_ids:
                    evidence_ledger.append(ev)
                    seen_ev_ids.add(ev.evidence_id)

        # 4. Synthesize Review Focus Items ("Needs Attention")
        review_focus: List[ReviewFocusItem] = []
        actionable_conflicts: List[str] = []
        missing_critical_fields: List[str] = []

        # A. Conflicts
        for f in envelope.fact_ledger:
            if f.status == FactStatus.CONFLICT:
                conflict_msg = f"Contradictory evidence detected for {f.field}: '{f.value}'"
                actionable_conflicts.append(conflict_msg)
                primary_ev = f.evidence[0] if f.evidence else None
                review_focus.append(ReviewFocusItem(
                    category=ReviewFocusCategory.EVIDENCE_CONFLICT,
                    field_affected=f.field,
                    headline=f"Evidence Conflict: {f.field}",
                    detail=f"Source documentation contains conflicting assertions for this parameter. Reviewer verification required.",
                    evidence_ref=primary_ev,
                    action_suggested="Resolve conflict and confirm true value"
                ))

        # B. Uncertain Facts
        for f in envelope.fact_ledger:
            if f.status == FactStatus.UNCERTAIN:
                primary_ev = f.evidence[0] if f.evidence else None
                review_focus.append(ReviewFocusItem(
                    category=ReviewFocusCategory.UNCERTAIN_HANDWRITING if "scanned" in envelope.source_filename.lower() else ReviewFocusCategory.CATEGORY_AMBIGUITY,
                    field_affected=f.field,
                    headline=f"Uncertain Extraction: {f.field}",
                    detail=f"Mention exists ('{f.value}') but cannot be confirmed with high confidence. Source verification recommended.",
                    evidence_ref=primary_ev,
                    action_suggested="Inspect source context and confirm"
                ))

        # C. Missing Critical Fields
        for f in envelope.fact_ledger:
            if f.status == FactStatus.NOT_STATED and f.field in cls.CRITICAL_FIELDS:
                missing_critical_fields.append(f.field)
                review_focus.append(ReviewFocusItem(
                    category=ReviewFocusCategory.MISSING_CRITICAL_FIELD,
                    field_affected=f.field,
                    headline=f"Critical Field Unstated: {f.field}",
                    detail=f"Regulatory parameter '{f.field}' was omitted from the intake transmission. Anti-hallucination guard verified absence.",
                    evidence_ref=None,
                    action_suggested="Confirm absence or initiate targeted follow-up query"
                ))

        # D. Physical Defect Photo Review
        if envelope.pqc and envelope.pqc.requires_human_review:
            photo_ev = envelope.pqc.photo_evidence
            review_focus.append(ReviewFocusItem(
                category=ReviewFocusCategory.PHOTO_DEFECT_INSPECTION,
                field_affected="defect_photo",
                headline="Mandatory Defect Photo Inspection",
                detail=f"Physical container defect photo detected: {photo_ev.observation if photo_ev else 'Visual verification required'}.",
                evidence_ref=photo_ev.evidence_ref if photo_ev else None,
                action_suggested="Visually inspect photo and confirm defect classification"
            ))

        # E. Multilingual Translation
        if envelope.language_detected.lower() not in ("english", "en", "unknown"):
            review_focus.append(ReviewFocusItem(
                category=ReviewFocusCategory.MULTILINGUAL_TRANSLATION,
                field_affected="language_detected",
                headline=f"Foreign Language Submission ({envelope.language_detected})",
                detail=f"Document was submitted in {envelope.language_detected}. Verbatim quotes are preserved in the original language.",
                evidence_ref=None,
                action_suggested="Verify verbatim non-English grounding"
            ))

        # F. Validation Gating Warnings/Errors
        if envelope.validation_report:
            for w in envelope.validation_report.warnings[:3]:
                review_focus.append(ReviewFocusItem(
                    category=ReviewFocusCategory.CATEGORY_AMBIGUITY,
                    field_affected=w.field,
                    headline=f"Validation Warning: {w.code}",
                    detail=w.message,
                    action_suggested="Review case integrity"
                ))

        # 5. Determine Urgency
        urgency = "STANDARD"
        if envelope.pqc and envelope.pqc.requires_human_review:
            urgency = "CRITICAL"
        elif any("ICSR" in c or "Safety Report" in c for c in all_cats):
            if envelope.triage.is_multi_label:
                urgency = "CRITICAL"
            else:
                urgency = "EXPEDITED"  # 15-day regulatory clock

        # 6. Executive Summary
        exec_summary = envelope.reviewer_summary
        if not exec_summary or exec_summary == "Not stated":
            exec_summary = envelope.document_summary
        if not exec_summary or exec_summary == "Not stated":
            exec_summary = f"AI-prepared case brief for {primary_cat} ({stats.confirmed_count} confirmed facts, {len(review_focus)} attention items)."

        triage_conf = envelope.triage.labels[0].confidence if envelope.triage.labels else 0.90
        brief = ReviewerBrief(
            case_id=case_id,
            subject=subject,
            sender=sender,
            received_date=received_date,
            primary_category=primary_cat,
            all_categories=all_cats,
            confidence=triage_conf,
            urgency=urgency,
            executive_summary=exec_summary,
            review_focus=review_focus,
            fact_stats=stats,
            facts=envelope.fact_ledger,
            evidence_ledger=evidence_ledger,
            actionable_conflicts=actionable_conflicts,
            missing_critical_fields=missing_critical_fields
        )

        return brief


reviewer_brief_builder = ReviewerBriefBuilder()
