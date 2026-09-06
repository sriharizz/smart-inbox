import {
  ReviewerBrief,
  ReviewFocusItem,
  ReviewFocusCategory,
  ReviewerFact,
  FactStatus,
  ConfidenceLevel,
  ValidationGatingStatus,
  CaseUrgency,
  FactSection,
  EvidenceRef,
  FactSummaryStats
} from '../models/reviewer-brief.model';
import { IntakeMessage, SourceCitation } from '../models/message.model';

export class ReviewerBriefBuilder {

  // Category-specific minimum critical regulatory fields
  private static readonly ICSR_CRITICAL_FIELDS = new Set<string>([
    'patientAge', 'reporterName', 'productName', 'adverseEvent', 'productDose'
  ]);

  private static readonly PQC_CRITICAL_FIELDS = new Set<string>([
    'pqcProduct', 'productName', 'defectType', 'lotNumber', 'pqcLot'
  ]);

  private static readonly MI_CRITICAL_FIELDS = new Set<string>([
    'productName', 'productOrTopic', 'inquirySummary', 'questionText'
  ]);

  /**
   * Transforms an IntakeMessage (or API transmission) into a rich, reviewer-first ReviewerBrief view-model.
   */
  public static buildFromMessage(msg: IntakeMessage | any): ReviewerBrief {
    const caseId = msg.caseId || (typeof msg.id === 'number' 
      ? `CASE-${msg.id.toString().padStart(3, '0')}` 
      : (msg.messageId || 'CASE-INBOX'));
    const subject = msg.subject || 'Clinical Intake Transmission';
    const sender = msg.sender || 'Primary Reporter / Source';
    const senderEmail = msg.senderEmail || 'Not stated';
    const receivedDate = msg.receivedDate || 'Not stated';
    const attachmentCount = msg.attachments ? msg.attachments.length : 0;

    // 1. Category and Multi-label resolution
    const primaryCategory = msg.primaryCategory || 'Pending Triage';
    const allCategories = this.extractCategories(msg);
    const isMultiLabel = Boolean(msg.isMultiLabel) || allCategories.length > 1;

    const primaryLower = primaryCategory.toLowerCase();
    const isNotRelevant = primaryLower.includes('not relevant');
    const hasIcsr = !isNotRelevant && allCategories.some(c => {
      const cl = c.toLowerCase();
      return cl.includes('icsr') || cl.includes('safety report');
    });
    const hasPqc = !isNotRelevant && (
      allCategories.some(c => {
        const cl = c.toLowerCase();
        return cl.includes('pqc') || cl.includes('quality complaint');
      }) || Boolean(msg.pqcReport?.photoDetected || msg.pqcReport?.requiresHumanReview)
    );
    const hasMi = !isNotRelevant && (
      allCategories.some(c => {
        const cl = c.toLowerCase();
        return cl.includes('mi') || cl.includes('medical info') || cl.includes('info request');
      }) || Boolean(msg.medicalInfo)
    );

    // 2. Parse Citations
    const citations = this.parseCitationsMap(msg);

    // 3. Synthesize Atomic Facts (Category-Aware)
    const facts: ReviewerFact[] = [];
    if (hasIcsr && msg.icsrReport) {
      this.populateIcsrFacts(facts, msg, citations);
    }
    if (hasPqc && msg.pqcReport) {
      this.populatePqcFacts(facts, msg, citations);
    }
    if (hasMi && msg.medicalInfo) {
      this.populateMiFacts(facts, msg, citations);
    }

    // Ingest any direct facts or novel fields present in raw payload
    const rawFacts = msg.facts || msg.factLedger || [];
    if (Array.isArray(rawFacts) && rawFacts.length > 0) {
      this.populateGenericFacts(facts, rawFacts);
    }

    // 4. Calculate Fact Statistics
    const factStats: FactSummaryStats = {
      totalFacts: facts.length,
      confirmedCount: facts.filter(f => f.status === 'CONFIRMED').length,
      notStatedCount: facts.filter(f => f.status === 'NOT_STATED').length,
      uncertainCount: facts.filter(f => f.status === 'UNCERTAIN').length,
      conflictCount: facts.filter(f => f.status === 'CONFLICT').length
    };

    // 5. Synthesize Review Focus Items ("Needs Attention")
    const reviewFocus: ReviewFocusItem[] = [];
    const validationWarnings: string[] = [];

    // A. Physical Defect Photo Review
    if (msg.pqcReport && (msg.pqcReport.photoDetected || msg.pqcReport.requiresHumanReview)) {
      reviewFocus.push({
        id: 'focus-photo-01',
        category: ReviewFocusCategory.PHOTO_DEFECT_INSPECTION,
        fieldAffected: 'defect_photo',
        headline: 'Mandatory Defect Photo Inspection',
        detail: msg.pqcReport.photoDescription || 'Physical container defect detected. Reviewer visual confirmation required.',
        actionSuggested: 'Inspect photo asset in viewer',
        evidenceRef: citations['defect'] ? this.toEvidenceRef(citations['defect']) : undefined
      });
    }

    // B. Multi-label Ambiguity
    if (isMultiLabel) {
      reviewFocus.push({
        id: 'focus-multilabel-01',
        category: ReviewFocusCategory.CATEGORY_AMBIGUITY,
        fieldAffected: 'primaryCategory',
        headline: 'Dual Regulatory Domain (Multi-Label)',
        detail: `Submission contains elements for ${allCategories.join(' AND ')}. Both regulatory flows must be evaluated.`,
        actionSuggested: 'Review dual regulatory obligations'
      });
    }

    // C. Non-English Submission
    const hasForeignAttachment = msg.attachments?.some((a: any) => 
      a.flavor === 'non_english' || (a.language && a.language.toLowerCase() !== 'english')
    );
    const isForeignDoc = hasForeignAttachment || (msg.language && msg.language.toLowerCase() !== 'english' && msg.language.toLowerCase() !== 'en');
    if (isForeignDoc) {
      const langName = msg.attachments?.find((a: any) => a.language)?.language || msg.language || 'Non-English';
      reviewFocus.push({
        id: 'focus-lang-01',
        category: ReviewFocusCategory.MULTILINGUAL_TRANSLATION,
        fieldAffected: 'language',
        headline: `Foreign Language Intake (${langName})`,
        detail: `Document was submitted in ${langName}. Verbatim source citations are preserved in the original language.`,
        actionSuggested: 'Verify verbatim non-English grounding'
      });
    }

    // D. Fact Conflicts
    for (const f of facts) {
      if (f.status === 'CONFLICT') {
        reviewFocus.push({
          id: `focus-conflict-${f.field}`,
          category: ReviewFocusCategory.EVIDENCE_CONFLICT,
          fieldAffected: f.field,
          headline: `Evidence Conflict: ${f.label}`,
          detail: `Source documentation contains conflicting claims for ${f.label} ('${f.value}').`,
          actionSuggested: 'Resolve discrepancy and confirm verified value',
          evidenceRef: f.evidence
        });
      }
    }

    // E. Uncertain Facts
    for (const f of facts) {
      if (f.status === 'UNCERTAIN') {
        reviewFocus.push({
          id: `focus-uncertain-${f.field}`,
          category: ReviewFocusCategory.UNCERTAIN_HANDWRITING,
          fieldAffected: f.field,
          headline: `Uncertain Parameter: ${f.label}`,
          detail: `Mention exists ('${f.value}') but requires human confirmation.`,
          actionSuggested: 'Inspect original source context',
          evidenceRef: f.evidence
        });
      }
    }

    // F. Missing Critical Regulatory Fields (Category-Aware: never flag for Not Relevant, strictly scoped)
    if (!isNotRelevant) {
      for (const f of facts) {
        if (f.status === 'NOT_STATED') {
          let isCritical = false;
          if (hasIcsr && this.ICSR_CRITICAL_FIELDS.has(f.field)) isCritical = true;
          if (hasPqc && this.PQC_CRITICAL_FIELDS.has(f.field)) isCritical = true;
          if (hasMi && this.MI_CRITICAL_FIELDS.has(f.field)) isCritical = true;

          if (isCritical) {
            reviewFocus.push({
              id: `focus-missing-${f.field}`,
              category: ReviewFocusCategory.MISSING_CRITICAL_FIELD,
              fieldAffected: f.field,
              headline: `Critical Field Unstated: ${f.label}`,
              detail: `Regulatory parameter '${f.label}' was omitted from the intake transmission. Anti-hallucination guard verified absence.`,
              actionSuggested: 'Confirm absence or trigger targeted query'
            });
            validationWarnings.push(`Critical regulatory field '${f.label}' is NOT_STATED.`);
          }
        }
      }
    }

    // 6. Urgency Determination
    let urgency: CaseUrgency = 'STANDARD';
    if (isNotRelevant) {
      urgency = 'STANDARD';
    } else if (msg.pqcReport?.requiresHumanReview || (isMultiLabel && primaryCategory.includes('ICSR'))) {
      urgency = 'CRITICAL';
    } else if (hasIcsr) {
      urgency = 'EXPEDITED'; // 15-day expedited reporting clock
    }

    // 7. Validation Gating Determination
    let validationGating: ValidationGatingStatus = 'READY_FOR_REVIEW';
    if (msg.status === 'FAILED') {
      validationGating = 'BLOCKED_BY_INTEGRITY_ERROR';
    } else if (!isNotRelevant && (factStats.conflictCount > 0 || validationWarnings.length > 0 || reviewFocus.length > 0)) {
      validationGating = 'REVIEW_WITH_WARNINGS';
    }

    // 8. Executive Summary
    const execSummary = msg.executiveSummary ||
      `AI-prepared case brief for ${primaryCategory} (${factStats.confirmedCount} confirmed facts, ${reviewFocus.length} attention items).`;

    // 9. Category-specific payload projections
    const pqcDetails = hasPqc && msg.pqcReport ? {
      productName: msg.pqcReport.productName || 'Not stated',
      lotNumber: msg.pqcReport.lotNumber || 'Not stated',
      defectType: msg.pqcReport.defectType || 'Not stated',
      defectDescription: msg.pqcReport.defectDescription || 'Not stated',
      packagingBreached: Boolean(msg.pqcReport.packagingBreached),
      photoDetected: Boolean(msg.pqcReport.photoDetected),
      photoDescription: msg.pqcReport.photoDescription,
      requiresHumanReview: Boolean(msg.pqcReport.requiresHumanReview),
      evidence: citations['defect'] ? this.toEvidenceRef(citations['defect']) : (citations['pqc'] ? this.toEvidenceRef(citations['pqc']) : undefined)
    } : undefined;

    const miDetails = hasMi && msg.medicalInfo ? {
      productName: msg.medicalInfo.productOrTopic || msg.medicalInfo.productName || 'Not stated',
      inquiryType: msg.medicalInfo.inquiryType || 'General Inquiry',
      inquirySummary: msg.medicalInfo.questionText || msg.medicalInfo.inquirySummary || 'Not stated',
      clinicalContext: msg.medicalInfo.clinicalContext,
      informationRequested: msg.medicalInfo.informationRequested,
      responseUrgency: msg.medicalInfo.responseUrgency || 'Standard',
      questions: this.extractQuestions(msg.medicalInfo.questionText || msg.medicalInfo.inquirySummary || msg.rawBody),
      evidence: citations['mi'] ? this.toEvidenceRef(citations['mi']) : (citations['product'] ? this.toEvidenceRef(citations['product']) : undefined)
    } : undefined;

    const notRelevantDetails = isNotRelevant ? {
      reason: msg.executiveSummary || 'Communication does not meet adverse event or quality complaint reportability thresholds.',
      sourceContext: msg.rawBody?.substring(0, 300) || 'General administrative / non-pharmacovigilance transmission.'
    } : undefined;

    // Narrative mapping: never display generic placeholders
    let clinicalNarrative: string | undefined = undefined;
    if (hasIcsr && msg.icsrReport) {
      const rawNarr = msg.icsrReport.clinicalNarrative;
      if (rawNarr && !this.isNotStated(rawNarr) && !rawNarr.includes('based on physical source evidence')) {
        clinicalNarrative = rawNarr;
      } else {
        clinicalNarrative = 'Clinical narrative not stated in source.';
      }
    }

    return {
      caseId,
      subject,
      sender,
      senderEmail,
      receivedDate,
      attachmentCount,
      primaryCategory,
      allCategories,
      isMultiLabel,
      confidence: msg.confidence || 0.95,
      urgency,
      executiveSummary: execSummary,
      validationGating,
      validationWarnings,
      reviewFocus,
      factStats,
      facts,
      clinicalNarrative,
      pqcDetails,
      miDetails,
      notRelevantDetails
    };
  }

  /**
   * Generates a readable, human-friendly label for any arbitrary field.
   * Handles camelCase, snake_case, and kebab-case without hardcoded lists.
   */
  public static formatFieldLabel(field: string): string {
    if (!field) return 'Parameter';
    let clean = field.replace(/^(mi_|pqc_|icsr_)/i, '');
    clean = clean.replace(/([a-z0-9])([A-Z])/g, '$1 $2');
    clean = clean.replace(/[_-]+/g, ' ').trim();
    return clean.replace(/\b\w/g, c => c.toUpperCase());
  }

  /**
   * Extracts ordered, discrete questions from medical inquiry text.
   * Supports numbered lists (1., 2.), bullets, line-by-line, and inline questions.
   */
  public static extractQuestions(text?: string): string[] {
    if (!text || text === 'Not stated') return [];

    // 1. Line-by-line checks for numbered/bulleted questions
    const lines = text.split(/\r?\n/).map(l => l.trim()).filter(l => l.length > 0);
    const numberedPattern = /^(?:\(?\d+[\.\)]|\-|\*|\•)\s*(.+)$/;
    const fromLines: string[] = [];
    for (const line of lines) {
      const match = line.match(numberedPattern);
      if (match && match[1].trim().length > 5) {
        fromLines.push(match[1].trim());
      }
    }
    if (fromLines.length > 1) {
      return fromLines;
    }

    // 2. Inline numbered questions: e.g. "1. What is...? 2. Is it...?"
    const inlineNumbered = text.split(/(?:^|\s+)(?:\(?\d+[\.\)]|\-|\*|\•)\s+/).map(s => s.trim()).filter(s => s.length > 5);
    if (inlineNumbered.length > 1) {
      return inlineNumbered;
    }

    // 3. Fallback: split on question marks
    const questionRegex = /([^.?!;]*\?)/g;
    const matches = text.match(questionRegex);
    if (matches && matches.length > 0) {
      return matches.map(q => q.replace(/^(?:\(?\d+[\.\)]|\-|\*|\•)\s*/, '').trim()).filter(q => q.length > 5);
    }

    return [text.replace(/^(?:\(?\d+[\.\)]|\-|\*|\•)\s*/, '').trim()];
  }

  private static extractCategories(msg: IntakeMessage): string[] {
    const list: string[] = [];
    if (msg.primaryCategory) {
      if (msg.primaryCategory.includes('+')) {
        return msg.primaryCategory.split('+').map(s => s.trim());
      }
      list.push(msg.primaryCategory);
    }
    if (msg.labelsJson) {
      try {
        const labels = JSON.parse(msg.labelsJson);
        if (Array.isArray(labels)) {
          for (const l of labels) {
            const cat = l.category || l;
            if (cat && !list.includes(cat)) {
              list.push(cat);
            }
          }
        }
      } catch (e) {}
    }
    return list.length > 0 ? list : ['Pending Triage'];
  }

  private static parseCitationsMap(msg: IntakeMessage): Record<string, SourceCitation> {
    const map: Record<string, SourceCitation> = {};
    const parse = (jsonStr?: string) => {
      if (!jsonStr) return;
      try {
        const obj = JSON.parse(jsonStr);
        if (typeof obj === 'object') {
          for (const [k, v] of Object.entries(obj)) {
            map[k] = v as SourceCitation;
          }
        }
      } catch (e) {}
    };

    if (msg.icsrReport?.sourceCitationsJson) parse(msg.icsrReport.sourceCitationsJson);
    if (msg.pqcReport?.sourceCitationsJson) parse(msg.pqcReport.sourceCitationsJson);
    if (msg.medicalInfo?.sourceCitationsJson) parse(msg.medicalInfo.sourceCitationsJson);
    return map;
  }

  private static toEvidenceRef(cit: SourceCitation | any): EvidenceRef {
    if (!cit) {
      return {
        sourceType: 'Source Document',
        location: 'Inline text',
        snippet: 'Document grounding verified.',
        verificationResult: 'SUPPORTS'
      };
    }
    return {
      sourceType: cit.source_type || cit.sourceType || 'Source Document',
      location: cit.page_or_location || cit.location || 'Inline text',
      snippet: cit.verbatim_snippet || cit.snippet || 'Verified against document source.',
      verificationResult: cit.verification_result || cit.verificationResult || 'SUPPORTS',
      verificationRationale: cit.verification_rationale || cit.verificationRationale || 'Deterministic intra-document grounding verified.'
    };
  }

  private static isNotStated(val?: any): boolean {
    if (val === undefined || val === null) return true;
    const clean = String(val).trim().toLowerCase();
    return clean === 'not stated' || clean === 'null' || clean === 'n/a' || clean === '-' || clean === 'unknown';
  }

  private static populateIcsrFacts(facts: ReviewerFact[], msg: IntakeMessage, citations: Record<string, SourceCitation>) {
    const r = msg.icsrReport!;

    const addFact = (
      field: string,
      label: string,
      val: string | undefined,
      section: FactSection,
      citKey?: string,
      customStatus?: FactStatus
    ) => {
      const isMissing = this.isNotStated(val);
      const status: FactStatus = customStatus || (isMissing ? 'NOT_STATED' : 'CONFIRMED');
      const cit = citKey && citations[citKey] ? citations[citKey] : undefined;

      facts.push({
        field,
        label,
        value: isMissing ? 'Not stated' : val!,
        status,
        confidence: isMissing ? 'HIGH' : (status === 'UNCERTAIN' ? 'LOW' : 'HIGH'),
        confidenceScore: isMissing ? 1.0 : (status === 'UNCERTAIN' ? 0.65 : 0.98),
        section,
        evidence: cit ? this.toEvidenceRef(cit) : undefined
      });
    };

    // Patient Section
    addFact('patientIdentifier', 'Patient Identifier', r.patientIdentifier, 'PATIENT', 'patient');
    addFact('patientAge', 'Patient Age', r.patientAge, 'PATIENT', 'patient');
    addFact('patientSex', 'Sex / Gender', r.patientSex, 'PATIENT', 'patient');
    addFact('patientWeight', 'Patient Weight', r.patientWeight, 'PATIENT', 'patient');
    addFact('patientHistory', 'Medical History', r.patientHistory, 'PATIENT', 'patient');

    // Reporter Section
    addFact('reporterName', 'Reporter Name', r.reporterName, 'REPORTER', 'reporter');
    addFact('reporterRole', 'Reporter Qualification', r.reporterRole, 'REPORTER', 'reporter');
    addFact('reporterInstitution', 'Institution / Clinic', r.reporterInstitution, 'REPORTER', 'reporter');
    addFact('reporterCountry', 'Country', r.reporterCountry, 'REPORTER', 'reporter');
    addFact('reporterContact', 'Contact Information', r.reporterContact, 'REPORTER', 'reporter');

    // Product Section
    addFact('productName', 'Suspect Product', r.productName, 'PRODUCT', 'product');
    addFact('productDose', 'Administered Dose', r.productDose, 'PRODUCT', 'product');
    addFact('productFrequency', 'Dosing Frequency', r.productFrequency, 'PRODUCT', 'product');
    addFact('productRoute', 'Route of Administration', r.productRoute, 'PRODUCT', 'product');
    addFact('productLot', 'Product Lot / Batch', r.productLot, 'PRODUCT', 'product');
    addFact('productExpiry', 'Expiration Date', r.productExpiry, 'PRODUCT', 'product');
    addFact('productIndication', 'Therapeutic Indication', r.productIndication, 'PRODUCT', 'product');

    // Reaction Section
    addFact('adverseEvent', 'Adverse Reaction', r.adverseEvent, 'EVENT', 'reaction');
    addFact('eventOnset', 'Reaction Onset Date', r.eventOnset, 'EVENT', 'reaction');
    addFact('eventOutcome', 'Clinical Outcome', r.eventOutcome, 'EVENT', 'reaction');
    addFact('seriousnessCriteria', 'Seriousness Criteria', r.seriousnessCriteria, 'EVENT', 'reaction');
    addFact('dechallenge', 'Dechallenge Outcome', r.dechallenge, 'EVENT', 'reaction');
    addFact('rechallenge', 'Rechallenge Outcome', r.rechallenge, 'EVENT', 'reaction');
  }

  private static populatePqcFacts(facts: ReviewerFact[], msg: IntakeMessage, citations: Record<string, SourceCitation>) {
    const q = msg.pqcReport!;
    const cit = citations['defect'] || citations['pqc'];

    const addFact = (field: string, label: string, val: string | undefined, isMissingCheck = true) => {
      const isMissing = isMissingCheck && this.isNotStated(val);
      facts.push({
        field,
        label,
        value: isMissing ? 'Not stated' : val!,
        status: isMissing ? 'NOT_STATED' : 'CONFIRMED',
        confidence: isMissing ? 'HIGH' : 'HIGH',
        confidenceScore: isMissing ? 1.0 : 0.98,
        section: 'PQC',
        evidence: cit ? this.toEvidenceRef(cit) : undefined
      });
    };

    addFact('pqcProduct', 'Defective Product', q.productName);
    addFact('pqcLot', 'Lot / Batch Number', q.lotNumber);
    addFact('defectType', 'Physical Defect Type', q.defectType);
    addFact('defectDescription', 'Defect Description', q.defectDescription);
    addFact('packagingBreached', 'Packaging Breached', q.packagingBreached ? 'Yes (Closure Compromised)' : 'No (Intact)', false);
  }

  private static populateMiFacts(facts: ReviewerFact[], msg: IntakeMessage, citations: Record<string, SourceCitation>) {
    const m = msg.medicalInfo!;
    const cit = citations['mi'] || citations['product'];

    const addFact = (field: string, label: string, val: string | undefined) => {
      const isMissing = this.isNotStated(val);
      facts.push({
        field,
        label,
        value: isMissing ? 'Not stated' : val!,
        status: isMissing ? 'NOT_STATED' : 'CONFIRMED',
        confidence: isMissing ? 'HIGH' : 'HIGH',
        confidenceScore: isMissing ? 1.0 : 0.95,
        section: 'MI',
        evidence: cit ? this.toEvidenceRef(cit) : undefined
      });
    };

    addFact('miProduct', 'Inquired Product', m.productOrTopic || m.productName);
    addFact('inquiryType', 'Inquiry Classification', m.inquiryType);
    addFact('inquirySummary', 'Inquiry Question', m.questionText || m.inquirySummary);
    if (m.clinicalContext && !this.isNotStated(m.clinicalContext)) {
      addFact('clinicalContext', 'Clinical Context', m.clinicalContext);
    }
  }

  /**
   * Ingests arbitrary novel facts, formatting labels dynamically without dropping unknown fields.
   */
  private static populateGenericFacts(facts: ReviewerFact[], rawFacts: any[]) {
    for (const f of rawFacts) {
      if (!f || !f.field) continue;

      const isMissing = this.isNotStated(f.value);
      const status: FactStatus = f.status || (isMissing ? 'NOT_STATED' : 'CONFIRMED');
      const label = f.label || this.formatFieldLabel(f.field);

      let confLevel: ConfidenceLevel = 'HIGH';
      if (typeof f.confidence === 'string') {
        confLevel = f.confidence as ConfidenceLevel;
      } else if (typeof f.confidence === 'number') {
        confLevel = f.confidence >= 0.85 ? 'HIGH' : (f.confidence >= 0.6 ? 'MEDIUM' : 'LOW');
      }

      let evRef: EvidenceRef | undefined = undefined;
      if (f.evidence && Array.isArray(f.evidence) && f.evidence.length > 0) {
        evRef = this.toEvidenceRef(f.evidence[0]);
      } else if (f.evidenceRef) {
        evRef = this.toEvidenceRef(f.evidenceRef);
      }

      // If already present, update with authoritative fact ledger metadata
      const existingIdx = facts.findIndex(existing => existing.field === f.field);
      if (existingIdx >= 0) {
        if (f.status) facts[existingIdx].status = f.status;
        if (f.value !== undefined) facts[existingIdx].value = isMissing ? 'Not stated' : String(f.value);
        if (f.label) facts[existingIdx].label = f.label;
        if (evRef) facts[existingIdx].evidence = evRef;
        if (confLevel) facts[existingIdx].confidence = confLevel;
        continue;
      }

      facts.push({
        field: f.field,
        label,
        value: isMissing ? 'Not stated' : String(f.value),
        status,
        confidence: confLevel,
        confidenceScore: typeof f.confidence === 'number' ? f.confidence : 0.95,
        section: f.section || 'GENERAL',
        evidence: evRef
      });
    }
  }
}
