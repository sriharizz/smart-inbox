import math
import time
from typing import Optional, List, Dict, Set, Any, Tuple
import logging

from app.schemas.case_envelope import CaseEnvelope
from app.schemas.fact_contract import Fact, Evidence, FactStatus, VerificationResult, EvidenceType
from app.schemas.validation_schema import (
    ValidationSeverity,
    ValidationGatingStatus,
    ValidationIssue,
    ValidationReport,
)

logger = logging.getLogger("smartinbox.validator")


class ConsistencyValidator:
    """
    Step 6: Deterministic Consistency & Integrity Validation Layer.
    Audits the structural integrity, referential validity, status reconciliation,
    and anti-hallucination compliance of a CaseEnvelope without invoking an LLM.
    """

    def __init__(self, strict_reconciliation: bool = True):
        self.strict_reconciliation = strict_reconciliation

    @staticmethod
    def _is_valid_confidence(val: Any) -> bool:
        if not isinstance(val, (int, float)):
            return False
        if math.isnan(val) or math.isinf(val):
            return False
        return 0.0 <= float(val) <= 1.0

    def validate_fact_structure(self, fact: Fact) -> List[ValidationIssue]:
        """Validates the structural soundness of an individual Fact model."""
        issues: List[ValidationIssue] = []

        # 1. Identifier
        if not fact.fact_id or not str(fact.fact_id).strip():
            issues.append(ValidationIssue(
                code="FACT_MISSING_ID",
                severity=ValidationSeverity.ERROR,
                message="Fact is missing a valid non-empty fact_id.",
                object_type="Fact",
                field=fact.field
            ))

        # 2. Field Name
        if not fact.field or not str(fact.field).strip():
            issues.append(ValidationIssue(
                code="FACT_EMPTY_FIELD",
                severity=ValidationSeverity.ERROR,
                message="Fact field name is empty or missing.",
                object_type="Fact",
                object_id=fact.fact_id
            ))

        # 3. Status Enum
        if not isinstance(fact.status, FactStatus) and fact.status not in [s.value for s in FactStatus]:
            issues.append(ValidationIssue(
                code="FACT_INVALID_STATUS",
                severity=ValidationSeverity.ERROR,
                message=f"Fact status '{fact.status}' is not a legal FactStatus enum value.",
                object_type="Fact",
                object_id=fact.fact_id,
                field=fact.field
            ))

        # 4. Confidence Bounds & Finite Float Check
        if not self._is_valid_confidence(fact.confidence):
            issues.append(ValidationIssue(
                code="CONFIDENCE_OUT_OF_BOUNDS",
                severity=ValidationSeverity.ERROR,
                message=f"Fact extraction confidence {fact.confidence} is out of bounds or non-numeric (must be finite [0.0, 1.0]).",
                object_type="Fact",
                object_id=fact.fact_id,
                field=fact.field
            ))

        # 5. Value format
        if fact.value is None or not isinstance(fact.value, str):
            issues.append(ValidationIssue(
                code="FACT_INVALID_VALUE_TYPE",
                severity=ValidationSeverity.ERROR,
                message=f"Fact value must be a valid string, got {type(fact.value).__name__}.",
                object_type="Fact",
                object_id=fact.fact_id,
                field=fact.field
            ))

        # 6. Normalized Value structural check
        if fact.normalized_value is not None:
            if fact.field == "patient_age":
                if isinstance(fact.normalized_value, (int, float)):
                    if fact.normalized_value < 0 or fact.normalized_value > 130:
                        issues.append(ValidationIssue(
                            code="FACT_NORMALIZED_VALUE_IMPLAUSIBLE",
                            severity=ValidationSeverity.WARNING,
                            message=f"Normalized patient age {fact.normalized_value} is physiologically implausible.",
                            object_type="Fact",
                            object_id=fact.fact_id,
                            field=fact.field
                        ))

        return issues

    def validate_evidence_integrity(
        self,
        evidence: Evidence,
        fact: Fact,
        known_sources: Set[str],
        envelope_metadata: Dict[str, Any]
    ) -> List[ValidationIssue]:
        """Validates referential integrity, location sanity, and snippet presence of an Evidence item."""
        issues: List[ValidationIssue] = []

        # 1. Identifier
        if not evidence.evidence_id or not str(evidence.evidence_id).strip():
            issues.append(ValidationIssue(
                code="EVIDENCE_MISSING_ID",
                severity=ValidationSeverity.ERROR,
                message="Evidence item is missing a valid evidence_id.",
                object_type="Evidence",
                object_id=fact.fact_id,
                field=fact.field
            ))

        # 2. Source ID & Referential Integrity
        if not evidence.source_id or not str(evidence.source_id).strip():
            issues.append(ValidationIssue(
                code="EVIDENCE_EMPTY_SOURCE",
                severity=ValidationSeverity.ERROR,
                message="Evidence item source_id is missing or empty.",
                object_type="Evidence",
                object_id=evidence.evidence_id,
                field=fact.field
            ))
        elif known_sources:
            # Check if source_id matches any registered intake source
            normalized_src = evidence.source_id.strip().lower()
            matched = any(
                normalized_src == ks.strip().lower() or
                normalized_src in ks.strip().lower() or
                ks.strip().lower() in normalized_src
                for ks in known_sources
            )
            if not matched:
                issues.append(ValidationIssue(
                    code="EVIDENCE_DANGLING_SOURCE",
                    severity=ValidationSeverity.ERROR,
                    message=f"Evidence source '{evidence.source_id}' does not correspond to any known document in CaseEnvelope (known: {sorted(list(known_sources))}).",
                    object_type="Evidence",
                    object_id=evidence.evidence_id,
                    field=fact.field,
                    related_ids=[evidence.source_id]
                ))

        # 3. Source Type Validity
        if not isinstance(evidence.source_type, EvidenceType) and evidence.source_type not in [t.value for t in EvidenceType]:
            issues.append(ValidationIssue(
                code="EVIDENCE_INVALID_TYPE",
                severity=ValidationSeverity.ERROR,
                message=f"Evidence source_type '{evidence.source_type}' is not a valid EvidenceType.",
                object_type="Evidence",
                object_id=evidence.evidence_id,
                field=fact.field
            ))

        # 4. Verbatim Snippet Integrity
        if not evidence.verbatim_snippet or not str(evidence.verbatim_snippet).strip():
            issues.append(ValidationIssue(
                code="EVIDENCE_EMPTY_SNIPPET",
                severity=ValidationSeverity.ERROR,
                message="Evidence verbatim_snippet is empty or whitespace.",
                object_type="Evidence",
                object_id=evidence.evidence_id,
                field=fact.field
            ))

        # 5. Page and Location Verification
        loc = evidence.location
        if loc:
            if loc.page_number is not None:
                if loc.page_number < 1:
                    issues.append(ValidationIssue(
                        code="EVIDENCE_INVALID_PAGE",
                        severity=ValidationSeverity.ERROR,
                        message=f"Evidence page number {loc.page_number} must be a 1-indexed positive integer.",
                        object_type="Evidence",
                        object_id=evidence.evidence_id,
                        field=fact.field
                    ))
                page_count = envelope_metadata.get("page_count") or envelope_metadata.get("total_pages")
                if page_count and isinstance(page_count, int) and loc.page_number > page_count:
                    issues.append(ValidationIssue(
                        code="EVIDENCE_PAGE_EXCEEDS_TOTAL",
                        severity=ValidationSeverity.ERROR,
                        message=f"Evidence page {loc.page_number} exceeds known document page count ({page_count}).",
                        object_type="Evidence",
                        object_id=evidence.evidence_id,
                        field=fact.field
                    ))

            if loc.char_start is not None and loc.char_end is not None:
                if loc.char_start < 0 or loc.char_end < loc.char_start:
                    issues.append(ValidationIssue(
                        code="EVIDENCE_INVALID_OFFSETS",
                        severity=ValidationSeverity.ERROR,
                        message=f"Evidence character offsets [{loc.char_start}, {loc.char_end}] are invalid.",
                        object_type="Evidence",
                        object_id=evidence.evidence_id,
                        field=fact.field
                    ))

        return issues

    def validate_verification_integrity(self, fact: Fact, evidence: Evidence) -> List[ValidationIssue]:
        """Validates verification results and confidence metrics attached to an evidence candidate."""
        issues: List[ValidationIssue] = []

        # 1. Verification Result Enum
        if not isinstance(evidence.verification_result, VerificationResult) and evidence.verification_result not in [v.value for v in VerificationResult]:
            issues.append(ValidationIssue(
                code="VERIFICATION_UNKNOWN_RESULT",
                severity=ValidationSeverity.ERROR,
                message=f"Evidence verification_result '{evidence.verification_result}' is invalid.",
                object_type="Verification",
                object_id=evidence.evidence_id,
                field=fact.field
            ))

        # 2. Verification Confidence
        if not self._is_valid_confidence(evidence.verification_confidence):
            issues.append(ValidationIssue(
                code="CONFIDENCE_OUT_OF_BOUNDS",
                severity=ValidationSeverity.ERROR,
                message=f"Evidence verification_confidence {evidence.verification_confidence} is out of bounds or non-numeric (must be finite [0.0, 1.0]).",
                object_type="Verification",
                object_id=evidence.evidence_id,
                field=fact.field
            ))

        # 3. Safe Fallback Compliance
        meta = evidence.verification_metadata or {}
        if meta.get("verifier_method") == "fallback" and evidence.verification_result == VerificationResult.SUPPORTS:
            issues.append(ValidationIssue(
                code="VERIFICATION_FALLBACK_ILLEGAL_SUPPORT",
                severity=ValidationSeverity.ERROR,
                message="Evidence generated by fallback verifier was marked SUPPORTS, which violates safe failure invariants.",
                object_type="Verification",
                object_id=evidence.evidence_id,
                field=fact.field
            ))

        # 4. Missing Verification Warning
        if not meta and evidence.verification_result == VerificationResult.INSUFFICIENT and evidence.verification_confidence == 0.0:
            issues.append(ValidationIssue(
                code="VERIFICATION_UNVERIFIED_CANDIDATE",
                severity=ValidationSeverity.WARNING,
                message="Candidate evidence lacks execution metadata from the verification layer.",
                object_type="Verification",
                object_id=evidence.evidence_id,
                field=fact.field
            ))

        return issues

    def validate_not_stated(self, fact: Fact) -> List[ValidationIssue]:
        """Enforces the anti-hallucination contract for NOT_STATED facts."""
        issues: List[ValidationIssue] = []

        if fact.status == FactStatus.NOT_STATED:
            val_lower = str(fact.value).strip().lower()
            allowed_unassigned = {"not stated", "unknown", "none", "n/a", "not reported", ""}

            # Check if an unstated fact carries an affirmative fabricated claim
            if val_lower not in allowed_unassigned and fact.normalized_value is not None:
                issues.append(ValidationIssue(
                    code="FACT_NOT_STATED_INCONSISTENT_VALUE",
                    severity=ValidationSeverity.ERROR,
                    message=f"Fact marked NOT_STATED has concrete fabricated value: '{fact.value}' (normalized: {fact.normalized_value}).",
                    object_type="Fact",
                    object_id=fact.fact_id,
                    field=fact.field
                ))

            # A NOT_STATED fact must NEVER have supporting evidence
            for ev in fact.evidence:
                if ev.verification_result == VerificationResult.SUPPORTS:
                    issues.append(ValidationIssue(
                        code="FACT_NOT_STATED_HAS_SUPPORTING_EVIDENCE",
                        severity=ValidationSeverity.ERROR,
                        message=f"Fact marked NOT_STATED carries evidence claiming SUPPORTS (evidence_id: {ev.evidence_id}).",
                        object_type="Fact",
                        object_id=fact.fact_id,
                        field=fact.field,
                        related_ids=[ev.evidence_id]
                    ))

            # Overall verification state must remain INSUFFICIENT
            if fact.verification_state == VerificationResult.SUPPORTS:
                issues.append(ValidationIssue(
                    code="FACT_NOT_STATED_VERIFICATION_SUPPORTED",
                    severity=ValidationSeverity.ERROR,
                    message="Fact marked NOT_STATED has overall verification_state = SUPPORTS, violating anti-hallucination bounds.",
                    object_type="Fact",
                    object_id=fact.fact_id,
                    field=fact.field
                ))

        return issues

    def reconcile_fact_status(self, fact: Fact) -> Tuple[Fact, List[ValidationIssue]]:
        """
        Controlled deterministic reconciliation between extraction status,
        evidence availability, and verification results.
        """
        issues: List[ValidationIssue] = []

        # Rule 1: NOT_STATED is immutable truth
        if fact.status == FactStatus.NOT_STATED:
            return fact, issues

        has_contradict = any(e.verification_result == VerificationResult.CONTRADICTS for e in fact.evidence)
        has_support = any(e.verification_result == VerificationResult.SUPPORTS for e in fact.evidence)

        # Rule 2: Contradictory evidence escalates to CONFLICT
        if has_contradict:
            if fact.status != FactStatus.CONFLICT:
                old_status = fact.status.value if hasattr(fact.status, "value") else str(fact.status)
                fact.status = FactStatus.CONFLICT
                note_msg = f"Status reconciled from {old_status} to CONFLICT due to contradictory evidence."
                fact.notes = f"{fact.notes} | {note_msg}" if fact.notes else note_msg
                issues.append(ValidationIssue(
                    code="FACT_RECONCILED_TO_CONFLICT",
                    severity=ValidationSeverity.WARNING,
                    message=note_msg,
                    object_type="Fact",
                    object_id=fact.fact_id,
                    field=fact.field
                ))
            return fact, issues

        # Rule 3: Verified support confirms the fact
        if has_support:
            if fact.status == FactStatus.UNCERTAIN:
                fact.status = FactStatus.CONFIRMED
                note_msg = "Status reconciled from UNCERTAIN to CONFIRMED based on supporting evidence."
                fact.notes = f"{fact.notes} | {note_msg}" if fact.notes else note_msg
                issues.append(ValidationIssue(
                    code="FACT_RECONCILED_TO_CONFIRMED",
                    severity=ValidationSeverity.INFO,
                    message=note_msg,
                    object_type="Fact",
                    object_id=fact.fact_id,
                    field=fact.field
                ))
            return fact, issues

        # Rule 4: Unverified / Insufficient evidence cannot remain CONFIRMED
        # If fact is marked CONFIRMED but has NO supporting evidence, reconcile to UNCERTAIN
        if fact.status == FactStatus.CONFIRMED and not has_support:
            fact.status = FactStatus.UNCERTAIN
            note_msg = "Status reconciled from CONFIRMED to UNCERTAIN: candidate evidence is INSUFFICIENT to verify."
            fact.notes = f"{fact.notes} | {note_msg}" if fact.notes else note_msg
            issues.append(ValidationIssue(
                code="FACT_RECONCILED_TO_UNCERTAIN",
                severity=ValidationSeverity.WARNING,
                message=note_msg,
                object_type="Fact",
                object_id=fact.fact_id,
                field=fact.field
            ))

        return fact, issues

    def validate_duplicate_conflicts(self, facts: List[Fact]) -> List[ValidationIssue]:
        """Detects duplicate facts for the same canonical field and flags conflicting assertions."""
        issues: List[ValidationIssue] = []
        field_groups: Dict[str, List[Fact]] = {}

        for f in facts:
            key = str(f.field).strip().lower()
            field_groups.setdefault(key, []).append(f)

        for field_name, group in field_groups.items():
            if len(group) > 1:
                # Compare values across instances
                first_norm = group[0].normalized_value or group[0].value.strip().lower()
                has_conflict = False
                differing_ids = [group[0].fact_id]

                for other in group[1:]:
                    other_norm = other.normalized_value or other.value.strip().lower()
                    if first_norm != other_norm:
                        has_conflict = True
                        differing_ids.append(other.fact_id)

                if has_conflict:
                    issues.append(ValidationIssue(
                        code="DUPLICATE_CONFLICTING_FACT",
                        severity=ValidationSeverity.WARNING,
                        message=f"Multiple conflicting assertions detected for canonical field '{field_name}'.",
                        object_type="Fact",
                        field=field_name,
                        related_ids=differing_ids
                    ))
                else:
                    issues.append(ValidationIssue(
                        code="DUPLICATE_REDUNDANT_FACT",
                        severity=ValidationSeverity.INFO,
                        message=f"Multiple redundant entries detected for canonical field '{field_name}'.",
                        object_type="Fact",
                        field=field_name,
                        related_ids=[f.fact_id for f in group]
                    ))

        return issues

    def validate_category_payload_consistency(self, envelope: CaseEnvelope) -> List[ValidationIssue]:
        """Validates that triage categories and category domain payloads structurally agree."""
        issues: List[ValidationIssue] = []

        primary_cat = envelope.triage.primary_category.value if hasattr(envelope.triage.primary_category, "value") else str(envelope.triage.primary_category)
        all_cats = [lbl.category.value for lbl in envelope.triage.labels] if envelope.triage.labels else [primary_cat]

        is_icsr = any("Safety Report" in c or "ICSR" in c for c in all_cats)
        is_pqc = any("Quality Complaint" in c or "PQC" in c for c in all_cats)
        is_mi = any("Info Request" in c or "Medical Information" in c or "MI" in c for c in all_cats)
        is_not_relevant = any("Not Relevant" in c for c in all_cats)

        # 1. ICSR payload consistency
        if ("Safety Report" in primary_cat or "ICSR" in primary_cat) and envelope.icsr is None:
            issues.append(ValidationIssue(
                code="CATEGORY_PAYLOAD_MISMATCH",
                severity=ValidationSeverity.ERROR,
                message=f"Primary category is '{primary_cat}', but icsr payload is null.",
                object_type="Payload",
                field="icsr"
            ))

        # 2. PQC payload consistency
        if ("Quality Complaint" in primary_cat or "PQC" in primary_cat) and envelope.pqc is None:
            issues.append(ValidationIssue(
                code="CATEGORY_PAYLOAD_MISMATCH",
                severity=ValidationSeverity.ERROR,
                message=f"Primary category is '{primary_cat}', but pqc payload is null.",
                object_type="Payload",
                field="pqc"
            ))

        # 3. MI payload consistency
        if ("Info Request" in primary_cat or "Medical Information" in primary_cat or "MI" in primary_cat) and envelope.mi is None:
            issues.append(ValidationIssue(
                code="CATEGORY_PAYLOAD_MISMATCH",
                severity=ValidationSeverity.ERROR,
                message=f"Primary category is '{primary_cat}', but mi payload is null.",
                object_type="Payload",
                field="mi"
            ))

        # 4. Not Relevant payload consistency
        if "Not Relevant" in primary_cat and not envelope.triage.is_multi_label:
            if envelope.not_relevant is None:
                issues.append(ValidationIssue(
                    code="CATEGORY_PAYLOAD_MISMATCH",
                    severity=ValidationSeverity.ERROR,
                    message="Primary category is 'Not Relevant', but not_relevant payload is null.",
                    object_type="Payload",
                    field="not_relevant"
                ))
            # Contradictory clinical payload presence in purely irrelevant cases
            if envelope.icsr is not None or envelope.pqc is not None:
                issues.append(ValidationIssue(
                    code="CATEGORY_NOT_RELEVANT_POLLUTED",
                    severity=ValidationSeverity.ERROR,
                    message="Single-label Not Relevant communication carries an unexpected ICSR or PQC clinical payload.",
                    object_type="Payload",
                    field="icsr_or_pqc"
                ))

        return issues

    def validate_cross_object_referential_integrity(self, envelope: CaseEnvelope) -> List[ValidationIssue]:
        """Validates global envelope identifiers and prevents internal ID collisions."""
        issues: List[ValidationIssue] = []

        if not envelope.envelope_id or not str(envelope.envelope_id).strip():
            issues.append(ValidationIssue(
                code="ENVELOPE_MISSING_ID",
                severity=ValidationSeverity.ERROR,
                message="CaseEnvelope is missing a valid envelope_id.",
                object_type="CaseEnvelope"
            ))

        # Fact ID Uniqueness
        seen_fact_ids: Set[str] = set()
        for fact in envelope.fact_ledger:
            if fact.fact_id in seen_fact_ids:
                issues.append(ValidationIssue(
                    code="DUPLICATE_FACT_ID",
                    severity=ValidationSeverity.ERROR,
                    message=f"Duplicate fact_id '{fact.fact_id}' detected in fact ledger.",
                    object_type="Fact",
                    object_id=fact.fact_id,
                    field=fact.field
                ))
            seen_fact_ids.add(fact.fact_id)

        # Evidence ID Uniqueness
        seen_ev_ids: Set[str] = set()
        for fact in envelope.fact_ledger:
            for ev in fact.evidence:
                if ev.evidence_id in seen_ev_ids:
                    issues.append(ValidationIssue(
                        code="DUPLICATE_EVIDENCE_ID",
                        severity=ValidationSeverity.ERROR,
                        message=f"Duplicate evidence_id '{ev.evidence_id}' detected in evidence ledger.",
                        object_type="Evidence",
                        object_id=ev.evidence_id,
                        field=fact.field
                    ))
                seen_ev_ids.add(ev.evidence_id)

        return issues

    def validate_envelope(self, envelope: CaseEnvelope, reconcile: bool = True) -> ValidationReport:
        """
        Comprehensive Step 6 Validation Orchestration.
        Executes structural, referential, verification, category, and duplicate checks,
        performs deterministic fact reconciliation, and determines reviewer gating status.
        """
        errors: List[ValidationIssue] = []
        warnings: List[ValidationIssue] = []
        infos: List[ValidationIssue] = []

        # 1. Collect known source identifiers for referential integrity checks
        known_sources: Set[str] = set()
        if envelope.source_filename:
            known_sources.add(envelope.source_filename)
        if envelope.message_id and envelope.message_id != "Unknown":
            known_sources.add(envelope.message_id)
        if envelope.metadata:
            for att_fn in envelope.metadata.get("attachment_filenames", []):
                known_sources.add(att_fn)
            for src_fn in envelope.metadata.get("source_filenames", []):
                known_sources.add(src_fn)

        # 2. Envelope and cross-object referential integrity
        cross_issues = self.validate_cross_object_referential_integrity(envelope)
        for issue in cross_issues:
            if issue.severity == ValidationSeverity.ERROR:
                errors.append(issue)
            elif issue.severity == ValidationSeverity.WARNING:
                warnings.append(issue)
            else:
                infos.append(issue)

        # 3. Category & payload consistency
        cat_issues = self.validate_category_payload_consistency(envelope)
        for issue in cat_issues:
            if issue.severity == ValidationSeverity.ERROR:
                errors.append(issue)
            elif issue.severity == ValidationSeverity.WARNING:
                warnings.append(issue)
            else:
                infos.append(issue)

        # 4. Duplicate & conflicting fact checks
        dup_issues = self.validate_duplicate_conflicts(envelope.fact_ledger)
        for issue in dup_issues:
            if issue.severity == ValidationSeverity.ERROR:
                errors.append(issue)
            elif issue.severity == ValidationSeverity.WARNING:
                warnings.append(issue)
            else:
                infos.append(issue)

        # 5. Per-Fact validation and reconciliation
        total_facts = len(envelope.fact_ledger)
        total_evidence = 0
        total_verification = 0

        for fact in envelope.fact_ledger:
            # Structure check
            f_issues = self.validate_fact_structure(fact)
            for issue in f_issues:
                if issue.severity == ValidationSeverity.ERROR:
                    errors.append(issue)
                elif issue.severity == ValidationSeverity.WARNING:
                    warnings.append(issue)
                else:
                    infos.append(issue)

            # NOT_STATED anti-hallucination check
            ns_issues = self.validate_not_stated(fact)
            for issue in ns_issues:
                if issue.severity == ValidationSeverity.ERROR:
                    errors.append(issue)
                elif issue.severity == ValidationSeverity.WARNING:
                    warnings.append(issue)
                else:
                    infos.append(issue)

            # Per-Evidence checks
            for ev in fact.evidence:
                total_evidence += 1
                ev_issues = self.validate_evidence_integrity(ev, fact, known_sources, envelope.metadata)
                for issue in ev_issues:
                    if issue.severity == ValidationSeverity.ERROR:
                        errors.append(issue)
                    elif issue.severity == ValidationSeverity.WARNING:
                        warnings.append(issue)
                    else:
                        infos.append(issue)

                total_verification += 1
                v_issues = self.validate_verification_integrity(fact, ev)
                for issue in v_issues:
                    if issue.severity == ValidationSeverity.ERROR:
                        errors.append(issue)
                    elif issue.severity == ValidationSeverity.WARNING:
                        warnings.append(issue)
                    else:
                        infos.append(issue)

            # Fact Status Reconciliation
            if reconcile and self.strict_reconciliation:
                _, recon_issues = self.reconcile_fact_status(fact)
                for issue in recon_issues:
                    if issue.severity == ValidationSeverity.ERROR:
                        errors.append(issue)
                    elif issue.severity == ValidationSeverity.WARNING:
                        warnings.append(issue)
                    else:
                        infos.append(issue)

        # 6. Determine Deterministic Gating Status
        if len(errors) > 0:
            gating_status = ValidationGatingStatus.BLOCKED_BY_INTEGRITY_ERROR
            passed = False
        elif len(warnings) > 0:
            gating_status = ValidationGatingStatus.REVIEW_WITH_WARNINGS
            passed = True
        else:
            gating_status = ValidationGatingStatus.READY_FOR_REVIEW
            passed = True

        checked_counts = {
            "facts_checked": total_facts,
            "evidence_checked": total_evidence,
            "verification_checked": total_verification,
            "sources_checked": len(known_sources),
            "errors_count": len(errors),
            "warnings_count": len(warnings)
        }

        summary = (
            f"Integrity validation completed: Gating={gating_status.value} "
            f"({len(errors)} errors, {len(warnings)} warnings across {total_facts} facts and {total_evidence} evidence items)."
        )

        report = ValidationReport(
            envelope_id=envelope.envelope_id,
            passed=passed,
            gating_status=gating_status,
            errors=errors,
            warnings=warnings,
            infos=infos,
            checked_counts=checked_counts,
            summary=summary,
            timestamp=int(time.time())
        )

        return report


consistency_validator = ConsistencyValidator()
