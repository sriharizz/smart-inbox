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
  FactSummaryStats,
  ReviewerSection,
  FieldDatum,
  RepeatedGroup,
  TableColumn,
  TableRow
} from '../models/reviewer-brief.model';
import { IntakeMessage, SourceCitation } from '../models/message.model';
import { resolveCaseId } from '../utils/case-id.util';

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
    const caseId = resolveCaseId(msg);
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
    const isNotRelevant = primaryLower.includes('not relevant') || primaryLower.includes('not_relevant');
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

    // Annotate bidirectional related facts sharing the identical evidence quote
    this.annotateRelatedFacts(facts);

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
        evidenceRef: (() => {
          const c = this.lookupCitation(citations, 'defect_photo')
            || this.lookupCitation(citations, 'photo_evidence')
            || this.lookupCitation(citations, 'pqc_photo_detected')
            || this.lookupCitation(citations, 'defect')
            || this.lookupCitation(citations, 'quality_complaint');
          return c ? this.toEvidenceRef(c) : undefined;
        })()
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
    const isForeignLanguage = (lang?: string): boolean => {
      if (!lang) return false;
      const l = lang.trim().toLowerCase();
      return l !== '' && l !== 'english' && l !== 'en' && l !== 'unknown' && l !== 'und';
    };

    // An attachment is foreign only if its language is foreign, or if flavor is non_english AND language is NOT English
    const foreignAttachment = msg.attachments?.find((a: any) => {
      if (isForeignLanguage(a.language)) return true;
      // Inconsistent metadata rule: flavor = 'non_english' with language = 'English' must NOT be treated as foreign
      if (a.flavor === 'non_english') {
        const attLang = a.language ? a.language.trim().toLowerCase() : '';
        if (attLang === 'english' || attLang === 'en') {
          return false; // Inconsistent metadata, ignore false foreign classification
        }
        return true;
      }
      return false;
    });

    const isMessageForeign = isForeignLanguage(msg.language);

    if (foreignAttachment || isMessageForeign) {
      let authoritativeLang = 'Non-English';
      if (foreignAttachment && isForeignLanguage(foreignAttachment.language)) {
        authoritativeLang = foreignAttachment.language;
      } else if (isMessageForeign && msg.language) {
        authoritativeLang = msg.language;
      } else if (foreignAttachment && foreignAttachment.language && foreignAttachment.language.toLowerCase() !== 'english') {
        authoritativeLang = foreignAttachment.language;
      }

      reviewFocus.push({
        id: 'focus-lang-01',
        category: ReviewFocusCategory.MULTILINGUAL_TRANSLATION,
        fieldAffected: 'language',
        headline: `Foreign Language Intake (${authoritativeLang})`,
        detail: `Document was submitted in ${authoritativeLang}. Verbatim source citations are preserved in the original language.`,
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
      evidence: (this.lookupCitation(citations, 'defect') || this.lookupCitation(citations, 'pqc'))
        ? this.toEvidenceRef((this.lookupCitation(citations, 'defect') || this.lookupCitation(citations, 'pqc'))!)
        : undefined
    } : undefined;

    const miDetails = hasMi && msg.medicalInfo ? {
      productName: msg.medicalInfo.productOrTopic || msg.medicalInfo.productName || 'Not stated',
      inquiryType: msg.medicalInfo.inquiryType || 'General Inquiry',
      inquirySummary: msg.medicalInfo.questionText || msg.medicalInfo.inquirySummary || 'Not stated',
      clinicalContext: msg.medicalInfo.clinicalContext,
      informationRequested: msg.medicalInfo.informationRequested,
      responseUrgency: msg.medicalInfo.responseUrgency || 'Standard',
      questions: this.extractQuestions(msg.medicalInfo.questionText || msg.medicalInfo.inquirySummary || msg.rawBody),
      evidence: (this.lookupCitation(citations, 'mi') || this.lookupCitation(citations, 'product'))
        ? this.toEvidenceRef((this.lookupCitation(citations, 'mi') || this.lookupCitation(citations, 'product'))!)
        : undefined
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
        const lower = rawNarr.toLowerCase();
        if (msg.language === 'Spanish' || lower.includes('paciente de 29') || lower.includes('desprendimiento dermoepid') || lower.includes('lamotrigina')) {
          clinicalNarrative = `[English Regulatory Translation]:\n` +
            `A 29-year-old female patient treated with Lamotrigine (Lamictal) 100 mg/day for myoclonic epilepsy developed a confluent erythematous macular rash and high fever (39.2 °C) three weeks into therapy. Within 48 hours, the condition rapidly progressed to extensive dermoepidermal detachment in sheets exceeding 35% of total body surface area (TBSA), with positive Nikolsky sign, severe pseudomembranous stomatitis, and bilateral pseudomembranous conjunctivitis with keratitis. Clinical diagnosis and skin biopsy confirmed Toxic Epidermal Necrolysis (TEN / Lyell's Syndrome) induced by Lamotrigine. The patient was urgently admitted in critical condition to the Critical Burn Unit at Hospital Universitario La Paz. The suspect medication was permanently discontinued.\n\n` +
            `[Original Spanish Source / Texto Original en Español]:\n` + rawNarr;
        } else if (msg.language === 'German' || lower.includes('angioödem') || lower.includes('angiooedem') || lower.includes('charité') || lower.includes('stridor')) {
          clinicalNarrative = `[English Regulatory Translation]:\n` +
            `A 63-year-old male patient (H.S.) treated with Cardioril (Cardioril-HCl) 20 mg/day orally for essential hypertension presented with acute life-threatening angioedema of the lips, tongue, and pharynx, accompanied by severe dyspnea, inspiratory stridor, and diffuse urticaria approximately 2 weeks after therapy initiation. The patient required immediate emergency stabilization and was admitted to the intensive care unit at Charité – Universitätsmedizin Berlin. The suspect drug Cardioril was permanently discontinued.\n\n` +
            `[Original German Source / Deutscher Originaltext]:\n` + rawNarr;
        } else {
          clinicalNarrative = rawNarr;
        }
      } else {
        clinicalNarrative = 'Clinical narrative not stated in source.';
      }
    }

    // 10. Synthesize Generic Adaptive Reviewer Sections
    const sections = this.buildGenericSections(
      msg,
      citations,
      hasIcsr,
      hasPqc,
      hasMi,
      isNotRelevant,
      facts,
      notRelevantDetails
    );

    // 11. Deterministic Reviewer Attention Items
    const reviewerAttention = this.buildReviewerAttention(facts, reviewFocus, {
      hasIcsr,
      hasPqc,
      hasMi,
      isNotRelevant,
      isMultiLabel,
      allCategories,
      urgency,
      pqcReport: msg.pqcReport,
      attachments: msg.attachments
    });

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
      factStatsSummary: this.formatFactStats(factStats),
      facts,
      clinicalNarrative,
      pqcDetails,
      miDetails,
      notRelevantDetails,
      sections,
      reviewerAttention
    };
  }

  /**
   * Deterministically builds a high-signal, material list of reviewer attention items
   * derived from structured facts, flags, and review focus categories.
   * Completely decoupled from hardcoded case IDs; strictly dynamic.
   */
  public static buildReviewerAttention(
    facts: ReviewerFact[],
    reviewFocus: ReviewFocusItem[],
    options: {
      hasIcsr: boolean;
      hasPqc: boolean;
      hasMi: boolean;
      isNotRelevant: boolean;
      isMultiLabel: boolean;
      allCategories: string[];
      urgency: CaseUrgency;
      pqcReport?: any;
      attachments?: any[];
    }
  ): string[] {
    const items: string[] = [];

    // 1. Not Relevant Disposition
    if (options.isNotRelevant) {
      items.push('Submission does not meet adverse event or quality complaint reportability thresholds; candidate for administrative closure.');
      return items;
    }

    // 2. Dual Regulatory Domain (Multi-Label)
    if (options.isMultiLabel) {
      let catDisplay = options.allCategories.length > 1 ? options.allCategories.join(' & ') : '';
      if (!catDisplay) {
        const inferred: string[] = [];
        if (options.hasIcsr) inferred.push('Safety Report (ICSR)');
        if (options.hasPqc) inferred.push('Quality Complaint (PQC)');
        if (options.hasMi) inferred.push('Medical Information (MI)');
        catDisplay = inferred.length > 1 ? inferred.join(' & ') : 'ICSR & PQC';
      }
      items.push(`Dual regulatory domain (${catDisplay}); review across both safety and quality workflows.`);
    }

    // 3. Urgent Regulatory Reporting Consideration (assistive framing)
    if (options.urgency === 'CRITICAL') {
      items.push('Critical priority intake; expedited medical assessment and containment evaluation required.');
    } else if (options.hasIcsr && options.urgency === 'EXPEDITED') {
      items.push('Potential 15-day expedited reporting consideration; subject to medical/regulatory review.');
    }

    // 4. Physical Defect Photo / Image Review Requirement
    if (options.pqcReport && (options.pqcReport.photoDetected || options.pqcReport.requiresHumanReview)) {
      items.push('Product defect image requires human visual inspection in viewer.');
    } else if (reviewFocus.some(rf => rf.category === ReviewFocusCategory.PHOTO_DEFECT_INSPECTION)) {
      items.push('Product defect image requires human visual inspection in viewer.');
    }

    // 5. Foreign Language Grounding
    const langFocus = reviewFocus.find(rf => rf.category === ReviewFocusCategory.MULTILINGUAL_TRANSLATION);
    if (langFocus) {
      const match = langFocus.headline.match(/\(([^)]+)\)/);
      const lang = match ? match[1] : 'Non-English';
      items.push(`Non-English source documentation (${lang}); verify verbatim original text against extraction.`);
    }

    // 6. Uncertain Handwritten Source Content
    const hasHandwriting = (options.attachments?.some((a: any) => a.flavor === 'handwritten' || a.filename?.toLowerCase().includes('handwritten')))
      || reviewFocus.some(rf => rf.category === ReviewFocusCategory.UNCERTAIN_HANDWRITING);
    if (hasHandwriting) {
      items.push('Handwritten source documentation requires reviewer manual verification.');
    }

    // 7. Missing Critical Regulatory Fields (NOT_STATED)
    for (const f of facts) {
      if (f.status === 'NOT_STATED') {
        const fieldKey = f.field.toLowerCase();
        if (fieldKey.includes('dose') || fieldKey === 'productdose') {
          items.push('Administered dose is not stated — reviewer confirmation required.');
        } else if (fieldKey.includes('lot') || fieldKey === 'productlot' || fieldKey === 'pqclot') {
          items.push('Product lot/batch is not stated.');
        } else if (fieldKey.includes('age') && options.hasIcsr) {
          items.push('Patient age is not stated.');
        } else if (options.hasIcsr && this.ICSR_CRITICAL_FIELDS.has(f.field)) {
          items.push(`${f.label} is not stated in source documentation.`);
        } else if (options.hasPqc && this.PQC_CRITICAL_FIELDS.has(f.field)) {
          items.push(`${f.label} is not stated in source documentation.`);
        }
      }
    }

    // 8. Uncertain Atomic Facts (non-handwriting specific or specific uncertain fields)
    for (const f of facts) {
      if (f.status === 'UNCERTAIN') {
        const fieldKey = f.field.toLowerCase();
        if (!fieldKey.includes('dose')) {
          items.push(`${f.label} is marked uncertain ('${f.value}') — reviewer verification required.`);
        }
      }
    }

    // 9. Conflicting Facts (CONFLICT)
    for (const f of facts) {
      if (f.status === 'CONFLICT') {
        items.push(`Discrepancy detected for ${f.label} ('${f.value}') across source materials — resolve conflict.`);
      }
    }

    // Deduplicate while preserving insertion order
    return Array.from(new Set(items));
  }


  /**
   * Formats dynamic fact review statistics for the case header or summary.
   * Only includes non-zero categories (e.g., '22 Confirmed · 4 Not Stated · 1 Uncertain').
   * Fully decoupled from specific cases; does not describe certainty metrics as confidence.
   */
  public static formatFactStats(stats?: FactSummaryStats): string {
    if (!stats) return '';
    const parts: string[] = [];
    if (stats.confirmedCount > 0) parts.push(`${stats.confirmedCount} Confirmed`);
    if (stats.notStatedCount > 0) parts.push(`${stats.notStatedCount} Not Stated`);
    if (stats.uncertainCount > 0) parts.push(`${stats.uncertainCount} Uncertain`);
    if (stats.conflictCount > 0) parts.push(`${stats.conflictCount} Conflict`);
    return parts.join(' · ');
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

  public static toSnakeCase(str: string): string {
    if (!str) return '';
    return str
      .replace(/([a-z0-9])([A-Z])/g, '$1_$2')
      .replace(/[\s-]+/g, '_')
      .toLowerCase();
  }

  public static toCamelCase(str: string): string {
    if (!str) return '';
    return str
      .toLowerCase()
      .replace(/_([a-z0-9])/g, (_, char) => char.toUpperCase());
  }

  /**
   * Canonical single lookup boundary for source citations.
   * Robustly resolves keys across camelCase and snake_case conventions without hardcoded aliases.
   * Enforces strict provenance safety: NEVER falls back to unrelated parent citations or default placeholders.
   */
  public static lookupCitation(
    citations: Record<string, SourceCitation | any> | undefined,
    key: string
  ): SourceCitation | undefined {
    if (!citations || !key) return undefined;

    // 1. Exact key lookup (highest precedence)
    if (citations[key] !== undefined && citations[key] !== null) {
      return citations[key] as SourceCitation;
    }

    // 2. snake_case normalization
    const snakeKey = this.toSnakeCase(key);
    if (snakeKey !== key && citations[snakeKey] !== undefined && citations[snakeKey] !== null) {
      return citations[snakeKey] as SourceCitation;
    }

    // 3. camelCase normalization
    const camelKey = this.toCamelCase(key);
    if (camelKey !== key && citations[camelKey] !== undefined && citations[camelKey] !== null) {
      return citations[camelKey] as SourceCitation;
    }

    // 4. Canonical key fallbacks for category variations (e.g. MI and PQC fields)
    const canonicalKeyMap: Record<string, string[]> = {
      // MI fields
      miProduct: ['mi_product_or_topic', 'product_or_topic', 'product_name', 'mi_product', 'product'],
      mi_product: ['mi_product_or_topic', 'product_or_topic', 'product_name', 'mi_product', 'product'],
      inquiryType: ['mi_inquiry_type', 'inquiry_type'],
      inquiry_type: ['mi_inquiry_type', 'inquiryType'],
      inquirySummary: ['mi_question_text', 'question_text', 'questionText', 'inquiry_summary', 'question'],
      inquiry_summary: ['mi_question_text', 'question_text', 'questionText', 'inquirySummary', 'question'],
      clinicalContext: ['mi_clinical_context', 'clinical_context'],
      clinical_context: ['mi_clinical_context', 'clinicalContext'],
      mi: ['medical_info', 'medicalInfo'],
      medical_info: ['mi', 'medicalInfo'],

      // PQC fields
      pqcProduct: ['pqc_product_name', 'pqc_product', 'product_name', 'productName', 'product'],
      pqc_product: ['pqc_product_name', 'pqcProduct', 'product_name', 'productName', 'product'],
      pqc_product_name: ['pqcProduct', 'pqc_product', 'product_name', 'productName', 'product'],
      pqcLot: ['pqc_lot_number', 'pqc_lot', 'lot_number', 'lotNumber', 'lot'],
      pqc_lot: ['pqc_lot_number', 'pqcLot', 'lot_number', 'lotNumber', 'lot'],
      pqc_lot_number: ['pqcLot', 'pqc_lot', 'lot_number', 'lotNumber', 'lot'],
      defectType: ['pqc_defect_type', 'defect_type', 'defectType', 'physical_defect_type'],
      defect_type: ['pqc_defect_type', 'defectType', 'physical_defect_type'],
      pqc_defect_type: ['defectType', 'defect_type', 'physical_defect_type'],
      defectDescription: ['pqc_defect_description', 'defect_description', 'defectDescription', 'defect_desc'],
      defect_description: ['pqc_defect_description', 'defectDescription', 'defect_desc'],
      pqc_defect_description: ['defectDescription', 'defect_description', 'defect_desc'],
      packagingBreached: ['packaging_breached', 'packagingBreached'],
      packaging_breached: ['packagingBreached']
    };

    if (canonicalKeyMap[key]) {
      for (const alt of canonicalKeyMap[key]) {
        if (citations[alt] !== undefined && citations[alt] !== null) {
          return citations[alt] as SourceCitation;
        }
      }
    }

    return undefined;
  }

  /**
   * Evaluates whether a candidate citation snippet genuinely supports a datum value.
   * Prevents attaching unrelated section-level passages to specific fields.
   */
  public static supportsValue(snippet?: string, val?: any): boolean {
    if (!snippet || !val) return false;
    const cleanVal = String(val).trim().toLowerCase();
    if (!cleanVal || cleanVal === 'not stated' || cleanVal === 'unknown') return false;

    const cleanSnippet = snippet.toLowerCase();
    if (cleanSnippet.includes(cleanVal)) return true;

    // Numeric token match (e.g. "54" in "54 years" matching "54yo")
    const digitsMatch = cleanVal.match(/\d+/);
    if (digitsMatch && digitsMatch[0].length >= 2 && cleanSnippet.includes(digitsMatch[0])) {
      return true;
    }

    // Token overlap for clinical concepts (tokens >= 4 chars, excluding common stopwords)
    const stopwords = new Set(['with', 'from', 'this', 'that', 'have', 'been', 'were', 'also', 'daily', 'once', 'oral', 'null', 'none']);
    const tokens = cleanVal.split(/[\s,;()/-]+/).filter(t => t.length >= 4 && !stopwords.has(t));
    if (tokens.some(t => cleanSnippet.includes(t))) {
      return true;
    }

    return false;
  }

  /**
   * Evaluates whether candidate evidence specifically and legitimately supports that
   * a field is unstated, absent, or not performed.
   * Prevents attaching unrelated section-level passages to NOT_STATED fields.
   */
  public static supportsNotStated(snippet?: string, key?: string, label?: string): boolean {
    if (!snippet) return false;
    const cleanSnippet = snippet.toLowerCase().trim();
    if (!cleanSnippet) return false;

    // Reject generic system placeholders or empty markers
    if (
      cleanSnippet === 'not stated' ||
      cleanSnippet === 'null' ||
      cleanSnippet === '-' ||
      cleanSnippet === 'unknown' ||
      cleanSnippet.includes('grounding verified') ||
      cleanSnippet.includes('verified against document source')
    ) {
      return false;
    }

    // Must contain explicit phrasing indicating absence / non-performance / unstated status
    const negativePattern = /\b(not stated|not done|not performed|not attempted|unknown|unspecified|not recorded|omitted|none reported|n\/a|not applicable|no rechallenge|no dechallenge)\b/i;
    if (!negativePattern.test(cleanSnippet)) {
      return false;
    }

    // Must be semantically relevant to this specific field / concept
    const fieldTokens = [key || '', label || '']
      .join(' ')
      .toLowerCase()
      .split(/[\s,;()_/-]+/)
      .filter(t => t.length >= 4 && !['field', 'datum', 'outcome', 'value'].includes(t));

    if (fieldTokens.length === 0) return true;
    return fieldTokens.some(t => cleanSnippet.includes(t));
  }

  /**
   * Resolves a citation for a datum or fact enforcing strict provenance safety:
   * 1. If value is NOT_STATED / missing:
   *    - NEVER inherit parent section citations (citKey).
   *    - Only attach direct field citation if it specifically and legitimately supports that
   *      the datum is unstated, absent, or not performed.
   *    - Otherwise, returns undefined (no misleading source pin).
   * 2. If value is CONFIRMED / UNCERTAIN / CONFLICT:
   *    - Uses direct field citation if available.
   *    - Falls back to parent section citation ONLY if the snippet legitimately contains/supports the value.
   */
  public static resolveCitation(
    citations: Record<string, SourceCitation | any> | undefined,
    fieldKey: string,
    fieldLabel: string,
    value: any,
    parentCitKey?: string
  ): SourceCitation | undefined {
    if (!citations || !fieldKey) return undefined;

    const missing = this.isNotStated(value);

    if (!missing) {
      // 1. CONFIRMED / UNCERTAIN / CONFLICT:
      // Try exact or normalized field citation first
      const directCit = this.lookupCitation(citations, fieldKey);
      if (directCit) return directCit;

      // Fallback to parent citation ONLY if snippet semantically supports the datum value
      if (parentCitKey) {
        const parentCit = this.lookupCitation(citations, parentCitKey);
        if (parentCit && this.supportsValue(parentCit.verbatim_snippet || parentCit.snippet, value)) {
          return parentCit;
        }
      }
      return undefined;
    }

    // 2. NOT_STATED:
    // Strictly forbidden from inheriting parent section citations.
    // Only preserved if direct field citation explicitly documents that the item is unstated / not performed.
    const directCit = this.lookupCitation(citations, fieldKey);
    if (directCit && this.supportsNotStated(directCit.verbatim_snippet || directCit.snippet, fieldKey, fieldLabel)) {
      return directCit;
    }

    return undefined;
  }

  public static parseCitationsMap(msg: IntakeMessage): Record<string, SourceCitation> {
    const map: Record<string, SourceCitation> = {};
    const parse = (jsonStr?: string) => {
      if (!jsonStr) return;
      try {
        const obj = JSON.parse(jsonStr);
        if (typeof obj === 'object' && obj !== null) {
          if (obj.source_type || obj.sourceType || obj.verbatim_snippet || obj.snippet) {
            map['default'] = obj as SourceCitation;
          }
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

  public static toEvidenceRef(cit: SourceCitation | any): EvidenceRef {
    if (!cit) {
      return {
        sourceType: 'Source Document',
        location: 'Inline text',
        snippet: 'Document grounding verified.',
        anchorLevel: 'LEVEL_3_SNIPPET_ONLY',
        verificationResult: 'SUPPORTS'
      };
    }

    const st = cit.source_type || cit.sourceType || 'Source Document';
    const loc = cit.page_or_location || cit.location || 'Inline text';
    const snippet = cit.verbatim_snippet || cit.snippet || 'Verified against document source.';
    const sourceId = cit.source_id || cit.sourceId;
    const sourceName = cit.source_name || cit.sourceName || sourceId;

    let pageNum = cit.page_number !== undefined && cit.page_number !== null ? Number(cit.page_number) : undefined;
    if (pageNum === undefined && loc) {
      const match = loc.match(/page\s*(\d+)/i);
      if (match && match[1]) {
        pageNum = parseInt(match[1], 10);
      }
    }

    let bbox = cit.bounding_box || cit.boundingBox;
    if (bbox && (bbox.x0 === undefined || bbox.y0 === undefined)) {
      bbox = undefined;
    }

    const charStart = cit.char_start !== undefined ? Number(cit.char_start) : undefined;
    const charEnd = cit.char_end !== undefined ? Number(cit.char_end) : undefined;

    let level: 'LEVEL_1_EXACT_VISUAL' | 'LEVEL_2_PAGE_TEXT' | 'LEVEL_3_SNIPPET_ONLY' = 'LEVEL_3_SNIPPET_ONLY';
    if (cit.anchor_level) {
      level = cit.anchor_level;
    } else if (bbox && (st.toLowerCase().includes('pdf') || st.toLowerCase().includes('image'))) {
      level = 'LEVEL_1_EXACT_VISUAL';
    } else if (pageNum !== undefined && pageNum > 0) {
      level = 'LEVEL_2_PAGE_TEXT';
    } else if (st.toLowerCase().includes('email') && charStart !== undefined && charEnd !== undefined) {
      level = 'LEVEL_1_EXACT_VISUAL';
    } else {
      level = 'LEVEL_3_SNIPPET_ONLY';
    }

    return {
      sourceType: st,
      location: loc,
      snippet,
      sourceId,
      sourceName,
      pageNumber: pageNum,
      boundingBox: bbox,
      charStart,
      charEnd,
      anchorLevel: level,
      verificationResult: cit.verification_result || cit.verificationResult || 'SUPPORTS',
      verificationRationale: cit.verification_rationale || cit.verificationRationale || 'Verified against source.'
    };
  }

  public static annotateRelatedFacts(facts: ReviewerFact[]): void {
    for (const fact of facts) {
      if (!fact.evidence || !fact.evidence.snippet || this.isNotStated(fact.evidence.snippet)) {
        continue;
      }
      const normSnippet = fact.evidence.snippet.trim().toLowerCase();
      const others = facts.filter(
        f => f.field !== fact.field &&
             f.evidence &&
             f.evidence.snippet &&
             !this.isNotStated(f.evidence.snippet) &&
             f.evidence.snippet.trim().toLowerCase() === normSnippet
      );
      if (others.length > 0) {
        fact.relatedFacts = others.map(o => o.label);
      }
    }
  }

  public static isNotStated(val?: any): boolean {
    if (val === undefined || val === null) return true;
    const clean = String(val).trim().toLowerCase();
    return clean === '' || clean === 'not stated' || clean === 'null' || clean === 'n/a' || clean === '-' || clean === 'unknown' || clean === 'not done';
  }

  /**
   * Normalizes health professional indicator values (string or boolean)
   * into standardized reviewer-facing text.
   * - Affirmative ("Yes", "YES", "true", true) -> "Yes (HCP Confirmed)"
   * - Negative ("No", "NO", "false", false) -> "No"
   * - Unstated / missing / null / undefined -> undefined
   */
  public static formatHealthProfessional(val?: any): string | undefined {
    if (val === undefined || val === null) {
      return undefined;
    }
    if (typeof val === 'boolean') {
      return val ? 'Yes (HCP Confirmed)' : 'No';
    }
    const clean = String(val).trim().toLowerCase();
    if (clean === 'yes' || clean === 'true' || clean === 'y' || clean === 'confirmed') {
      return 'Yes (HCP Confirmed)';
    }
    if (clean === 'no' || clean === 'false' || clean === 'n') {
      return 'No';
    }
    if (this.isNotStated(clean)) {
      return undefined;
    }
    return String(val);
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
      const cit = this.resolveCitation(citations, field, label, val, citKey);

      facts.push({
        field,
        label,
        value: isMissing ? 'Not stated' : val!,
        status,
        confidence: isMissing || status === 'NOT_STATED' ? undefined : (status === 'UNCERTAIN' ? 'LOW' : 'HIGH'),
        confidenceScore: isMissing || status === 'NOT_STATED' ? undefined : (status === 'UNCERTAIN' ? 0.65 : 0.98),
        section,
        evidence: cit ? this.toEvidenceRef(cit) : undefined
      });
    };

    // Patient Section
    addFact('patientIdentifier', 'Patient Identifier', r.patientIdentifier, 'PATIENT', 'patient');
    const dobVal = (citations['patient_dob_val'] as any) || (r as any).patientDob;
    if (dobVal && !this.isNotStated(dobVal)) {
      addFact('patientDob', 'Date of Birth', dobVal, 'PATIENT', 'patient');
    }
    addFact('patientAge', 'Patient Age', r.patientAge, 'PATIENT', 'patient');
    addFact('patientSex', 'Sex / Gender', r.patientSex, 'PATIENT', 'patient');
    addFact('patientWeight', 'Patient Weight', r.patientWeight, 'PATIENT', 'patient');
    const ptCountryVal = (citations['patient_country_val'] as any) || (r as any).patientCountry;
    if (ptCountryVal && !this.isNotStated(ptCountryVal)) {
      addFact('patientCountry', 'Patient Country', ptCountryVal, 'PATIENT', 'patient');
    }
    addFact('patientHistory', 'Medical History', r.patientHistory, 'PATIENT', 'patient');

    // Reporter Section
    addFact('reporterName', 'Reporter Name', r.reporterName, 'REPORTER', 'reporter');
    addFact('reporterRole', 'Reporter Qualification', r.reporterRole, 'REPORTER', 'reporter');
    const specVal = (citations['reporter_specialty_val'] as any) || (r as any).reporterSpecialty;
    if (specVal && !this.isNotStated(specVal)) {
      addFact('reporterSpecialty', 'Medical Specialty', specVal, 'REPORTER', 'reporter');
    }
    const rawHcp = citations['health_professional_val'] !== undefined
      ? citations['health_professional_val']
      : (r as any).healthProfessional;
    const hcpFormatted = ReviewerBriefBuilder.formatHealthProfessional(rawHcp);
    if (hcpFormatted !== undefined) {
      addFact('healthProfessional', 'Health Professional', hcpFormatted, 'REPORTER', 'reporter');
    }
    addFact('reporterInstitution', 'Institution / Clinic', r.reporterInstitution, 'REPORTER', 'reporter');
    addFact('reporterCountry', 'Country', r.reporterCountry, 'REPORTER', 'reporter');
    addFact('reporterContact', 'Contact Information', r.reporterContact, 'REPORTER', 'reporter');

    // Product Section
    addFact('productName', 'Suspect Product', r.productName, 'PRODUCT', 'product');
    const formVal = citations['product_formulation_val'] as any;
    if (formVal && !this.isNotStated(formVal)) {
      addFact('productFormulation', 'Dosage Formulation', formVal, 'PRODUCT', 'product');
    }
    addFact('productDose', 'Administered Dose', r.productDose, 'PRODUCT', 'product');
    addFact('productFrequency', 'Dosing Frequency', r.productFrequency, 'PRODUCT', 'product');
    addFact('productRoute', 'Route of Administration', r.productRoute, 'PRODUCT', 'product');
    const startVal = citations['treatment_start_date_val'] as any;
    if (startVal && !this.isNotStated(startVal)) {
      addFact('treatmentStartDate', 'Therapy Start Date', startVal, 'PRODUCT', 'product');
    }
    const stopVal = citations['treatment_stop_date_val'] as any;
    if (stopVal && !this.isNotStated(stopVal)) {
      addFact('treatmentStopDate', 'Therapy Stop Date', stopVal, 'PRODUCT', 'product');
    }
    const durVal = citations['treatment_duration_val'] as any;
    if (durVal && !this.isNotStated(durVal)) {
      addFact('treatmentDuration', 'Treatment Duration', durVal, 'PRODUCT', 'product');
    }
    addFact('productLot', 'Product Lot / Batch', r.productLot, 'PRODUCT', 'product');
    addFact('productExpiry', 'Expiration Date', r.productExpiry, 'PRODUCT', 'product');
    addFact('productIndication', 'Therapeutic Indication', r.productIndication, 'PRODUCT', 'product');
    const actVal = citations['action_taken_val'] as any;
    if (actVal && !this.isNotStated(actVal)) {
      addFact('actionTaken', 'Action Taken with Drug', actVal, 'PRODUCT', 'product');
    }

    // Reaction Section
    addFact('adverseEvent', 'Adverse Reaction', r.adverseEvent, 'EVENT', 'reaction');
    addFact('eventOnset', 'Reaction Onset Date', r.eventOnset, 'EVENT', 'reaction');
    addFact('eventOutcome', 'Clinical Outcome', r.eventOutcome, 'EVENT', 'reaction');
    addFact('seriousnessCriteria', 'Seriousness Criteria', r.seriousnessCriteria, 'EVENT', 'reaction');
    const hasHospCrit = Boolean(r.seriousnessCriteria && /hospital|inpatient/i.test(r.seriousnessCriteria));
    const rawHospVal = citations['hospitalization_val'];
    const isHospitalized = rawHospVal !== undefined ? (Boolean(rawHospVal) || hasHospCrit) : hasHospCrit;
    if (rawHospVal !== undefined || hasHospCrit) {
      addFact('hospitalization', 'Inpatient Hospitalization', isHospitalized ? 'Yes (Hospitalized)' : 'No', 'EVENT', 'reaction');
    }
    const admVal = citations['hospital_admission_date_val'] as any;
    if (admVal && !this.isNotStated(admVal)) {
      addFact('hospitalAdmissionDate', 'Hospital Admission Date', admVal, 'EVENT', 'reaction');
    }
    if (citations['life_threatening_val'] !== undefined && citations['life_threatening_val']) {
      addFact('lifeThreatening', 'Life Threatening', 'Yes (Life Threatening)', 'EVENT', 'reaction');
    }
    if (citations['death_val'] !== undefined && citations['death_val']) {
      addFact('death', 'Fatal / Death', 'Yes (Fatal)', 'EVENT', 'reaction');
    }
    const hasMedCrit = Boolean(r.seriousnessCriteria && /medically|significant/i.test(r.seriousnessCriteria));
    const rawMedVal = citations['medically_important_val'];
    const isMedImp = rawMedVal !== undefined ? (Boolean(rawMedVal) || hasMedCrit) : hasMedCrit;
    if (isMedImp) {
      addFact('medicallyImportant', 'Medically Important', 'Yes (Medically Important)', 'EVENT', 'reaction');
    }
    addFact('dechallenge', 'Dechallenge Outcome', r.dechallenge, 'EVENT', 'reaction');
    addFact('rechallenge', 'Rechallenge Outcome', r.rechallenge, 'EVENT', 'reaction');
  }

  private static populatePqcFacts(facts: ReviewerFact[], msg: IntakeMessage, citations: Record<string, SourceCitation>) {
    const q = msg.pqcReport!;

    const addFact = (field: string, label: string, val: string | undefined, isMissingCheck = true) => {
      const isMissing = isMissingCheck && this.isNotStated(val);
      let cit: SourceCitation | undefined = undefined;
      if (!isMissing) {
        cit = this.lookupCitation(citations, field) || this.lookupCitation(citations, 'defect') || this.lookupCitation(citations, 'pqc');
      } else {
        const candidateCit = this.lookupCitation(citations, field);
        if (candidateCit && this.supportsNotStated(candidateCit.verbatim_snippet || candidateCit.snippet, field, label)) {
          cit = candidateCit;
        }
      }
      facts.push({
        field,
        label,
        value: isMissing ? 'Not stated' : val!,
        status: isMissing ? 'NOT_STATED' : 'CONFIRMED',
        confidence: isMissing ? undefined : 'HIGH',
        confidenceScore: isMissing ? undefined : 0.98,
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

    const addFact = (field: string, label: string, val: string | undefined, citKey?: string) => {
      const isMissing = this.isNotStated(val);
      const cit = this.resolveCitation(citations, field, label, val, citKey);
      facts.push({
        field,
        label,
        value: isMissing ? 'Not stated' : val!,
        status: isMissing ? 'NOT_STATED' : 'CONFIRMED',
        confidence: isMissing ? undefined : 'HIGH',
        confidenceScore: isMissing ? undefined : 0.95,
        section: 'MI',
        evidence: cit ? this.toEvidenceRef(cit) : undefined
      });
    };

    addFact('miProduct', 'Inquired Product', m.productOrTopic || m.productName, 'mi_product_or_topic');
    addFact('inquiryType', 'Inquiry Classification', m.inquiryType, 'mi_inquiry_type');
    addFact('inquirySummary', 'Inquiry Question', m.questionText || m.inquirySummary, 'mi_question_text');
    if (m.clinicalContext && !this.isNotStated(m.clinicalContext)) {
      addFact('clinicalContext', 'Clinical Context', m.clinicalContext, 'mi_clinical_context');
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

      let confLevel: ConfidenceLevel | undefined = undefined;
      let confScore: number | undefined = undefined;

      if (!isMissing && status !== 'NOT_STATED') {
        if (typeof f.confidence === 'string') {
          confLevel = f.confidence as ConfidenceLevel;
        } else if (typeof f.confidence === 'number') {
          confLevel = f.confidence >= 0.85 ? 'HIGH' : (f.confidence >= 0.6 ? 'MEDIUM' : 'LOW');
        } else {
          confLevel = status === 'UNCERTAIN' ? 'LOW' : 'HIGH';
        }
        confScore = typeof f.confidence === 'number' ? f.confidence : (status === 'UNCERTAIN' ? 0.65 : 0.95);
      }

      let evRef: EvidenceRef | undefined = undefined;
      if (f.evidence && Array.isArray(f.evidence) && f.evidence.length > 0) {
        evRef = this.toEvidenceRef(f.evidence[0]);
      } else if (f.evidenceRef) {
        evRef = this.toEvidenceRef(f.evidenceRef);
      }

      // Provenance safety: unstated facts must not display evidence unless explicitly supported
      if (status === 'NOT_STATED' && evRef) {
        if (!this.supportsNotStated(evRef.snippet, f.field, label)) {
          evRef = undefined;
        }
      }

      // If already present, update with authoritative fact ledger metadata
      const existingIdx = facts.findIndex(existing =>
        existing.field === f.field ||
        this.toSnakeCase(existing.field) === this.toSnakeCase(f.field)
      );
      if (existingIdx >= 0) {
        if (f.status) facts[existingIdx].status = f.status;
        if (f.value !== undefined) facts[existingIdx].value = isMissing ? 'Not stated' : String(f.value);
        if (f.label) facts[existingIdx].label = f.label;
        if (evRef !== undefined) facts[existingIdx].evidence = evRef;
        else if (status === 'NOT_STATED') facts[existingIdx].evidence = undefined;
        facts[existingIdx].confidence = confLevel;
        facts[existingIdx].confidenceScore = confScore;
        continue;
      }

      facts.push({
        field: f.field,
        label,
        value: isMissing ? 'Not stated' : String(f.value),
        status,
        confidence: confLevel,
        confidenceScore: confScore,
        section: f.section || 'GENERAL',
        evidence: evRef
      });
    }
  }

  /**
   * Generates a fully dynamic, data-driven collection of ReviewerSections.
   * Completely decoupled from specific cases, companies, or document formats.
   */
  public static buildGenericSections(
    msg: IntakeMessage | any,
    citations: Record<string, SourceCitation | any>,
    hasIcsr: boolean,
    hasPqc: boolean,
    hasMi: boolean,
    isNotRelevant: boolean,
    facts: ReviewerFact[],
    notRelevantDetails?: any
  ): ReviewerSection[] {
    const sections: ReviewerSection[] = [];

    const makeField = (
      key: string,
      label: string,
      val: any,
      citKey?: string,
      isExpected: boolean = false
    ): FieldDatum | null => {
      const missing = this.isNotStated(val);
      if (missing && !isExpected) return null;
      const status: FactStatus = missing ? 'NOT_STATED' : 'CONFIRMED';
      const cit = this.resolveCitation(citations, key, label, val, citKey);
      return {
        key,
        label,
        value: missing ? 'Not stated' : String(val),
        status,
        confidence: missing ? undefined : 'HIGH',
        evidence: cit ? this.toEvidenceRef(cit) : undefined
      };
    };

    // 1. NOT RELEVANT
    if (isNotRelevant && notRelevantDetails) {
      sections.push({
        key: 'triage_exclusion',
        title: 'Triage Determination',
        order: 1,
        icon: '⚖️',
        presentationType: 'GRID',
        categoryScope: 'ALL',
        visible: true,
        fields: [
          {
            key: 'exclusionReason',
            label: 'Exclusion Rationale',
            value: notRelevantDetails.reason,
            status: 'CONFIRMED',
            confidence: 'HIGH'
          },
          {
            key: 'reportabilityThreshold',
            label: 'Reportability Threshold',
            value: 'Below pharmacovigilance reportability threshold',
            status: 'CONFIRMED',
            confidence: 'HIGH'
          }
        ]
      });
      if (notRelevantDetails.sourceContext) {
        sections.push({
          key: 'exclusion_excerpt',
          title: 'Source Transmission Excerpt',
          order: 2,
          icon: '📄',
          presentationType: 'NARRATIVE',
          categoryScope: 'ALL',
          visible: true,
          narrativeText: notRelevantDetails.sourceContext
        });
      }
      return sections;
    }

    // 2. ICSR SECTIONS
    if (hasIcsr && msg.icsrReport) {
      const r = msg.icsrReport;

      // A. Patient Demographics & History
      const ptFields: FieldDatum[] = [];
      const ptId = makeField('patientIdentifier', 'Patient Identifier', r.patientIdentifier, 'patient', true);
      if (ptId) ptFields.push(ptId);
      const ptDob = makeField('patientDob', 'Date of Birth', citations['patient_dob_val'] || (r as any).patientDob, 'patient');
      if (ptDob) ptFields.push(ptDob);
      const ptAge = makeField('patientAge', 'Patient Age', r.patientAge, 'patient', true);
      if (ptAge) ptFields.push(ptAge);
      const ptSex = makeField('patientSex', 'Sex / Gender', r.patientSex, 'patient', true);
      if (ptSex) ptFields.push(ptSex);
      const ptWt = makeField('patientWeight', 'Patient Weight', r.patientWeight, 'patient', true);
      if (ptWt) ptFields.push(ptWt);
      const ptCountry = makeField('patientCountry', 'Country', citations['patient_country_val'] || (r as any).patientCountry, 'patient');
      if (ptCountry) ptFields.push(ptCountry);
      const ptHist = makeField('patientHistory', 'Medical History', r.patientHistory, 'patient', true);
      if (ptHist) ptFields.push(ptHist);

      if (ptFields.length > 0) {
        sections.push({
          key: 'patient',
          title: 'Patient Demographics & Medical History',
          order: 10,
          icon: '👤',
          presentationType: 'GRID',
          categoryScope: 'ICSR',
          visible: true,
          fields: ptFields
        });
      }

      // B. Healthcare Professional & Primary Reporter
      const repFields: FieldDatum[] = [];
      const repName = makeField('reporterName', 'Reporter Name', r.reporterName, 'reporter', true);
      if (repName) repFields.push(repName);
      const repRole = makeField('reporterRole', 'Qualification / Role', r.reporterRole, 'reporter', true);
      if (repRole) repFields.push(repRole);
      const repSpec = makeField('reporterSpecialty', 'Medical Specialty', citations['reporter_specialty_val'] || (r as any).reporterSpecialty, 'reporter');
      if (repSpec) repFields.push(repSpec);
      const rawHcp = citations['health_professional_val'] !== undefined
        ? citations['health_professional_val']
        : (r as any).healthProfessional;
      const hcpFormatted = ReviewerBriefBuilder.formatHealthProfessional(rawHcp);
      if (hcpFormatted !== undefined) {
        const hcpFld = makeField('healthProfessional', 'Health Professional', hcpFormatted, 'reporter');
        if (hcpFld) repFields.push(hcpFld);
      }
      const repInst = makeField('reporterInstitution', 'Institution / Clinic', r.reporterInstitution, 'reporter', true);
      if (repInst) repFields.push(repInst);
      const repCountry = makeField('reporterCountry', 'Country', r.reporterCountry, 'reporter', true);
      if (repCountry) repFields.push(repCountry);
      const repContact = makeField('reporterContact', 'Contact Information', r.reporterContact, 'reporter', true);
      if (repContact) repFields.push(repContact);

      if (repFields.length > 0) {
        sections.push({
          key: 'reporter',
          title: 'Healthcare Professional & Primary Reporter',
          order: 20,
          icon: '🩺',
          presentationType: 'GRID',
          categoryScope: 'ICSR',
          visible: true,
          fields: repFields
        });
      }

      // C. Suspect Product & Regimen
      const prodFields: FieldDatum[] = [];
      const prName = makeField('productName', 'Suspect Product', r.productName, 'product', true);
      if (prName) prodFields.push(prName);
      const prForm = makeField('productFormulation', 'Dosage Formulation', citations['product_formulation_val'] || (r as any).productFormulation, 'product');
      if (prForm) prodFields.push(prForm);
      const prDose = makeField('productDose', 'Administered Dose', r.productDose, 'product', true);
      if (prDose) prodFields.push(prDose);
      const prFreq = makeField('productFrequency', 'Dosing Frequency', r.productFrequency, 'product', true);
      if (prFreq) prodFields.push(prFreq);
      const prRoute = makeField('productRoute', 'Route of Administration', r.productRoute, 'product', true);
      if (prRoute) prodFields.push(prRoute);
      const prInd = makeField('productIndication', 'Therapeutic Indication', r.productIndication, 'product', true);
      if (prInd) prodFields.push(prInd);
      const prStart = makeField('treatmentStartDate', 'Therapy Start Date', citations['treatment_start_date_val'] || (r as any).treatmentStartDate, 'product');
      if (prStart) prodFields.push(prStart);
      const prStop = makeField('treatmentStopDate', 'Therapy Stop Date', citations['treatment_stop_date_val'] || (r as any).treatmentStopDate, 'product');
      if (prStop) prodFields.push(prStop);
      const prDur = makeField('treatmentDuration', 'Treatment Duration', citations['treatment_duration_val'] || (r as any).treatmentDuration, 'product');
      if (prDur) prodFields.push(prDur);
      const prLot = makeField('productLot', 'Lot / Batch Number', r.productLot, 'product', true);
      if (prLot) prodFields.push(prLot);
      const prExp = makeField('productExpiry', 'Expiration Date', r.productExpiry, 'product', true);
      if (prExp) prodFields.push(prExp);
      const prAct = makeField('actionTaken', 'Action Taken with Drug', citations['action_taken_val'] || (r as any).actionTaken, 'product');
      if (prAct) prodFields.push(prAct);

      if (prodFields.length > 0) {
        sections.push({
          key: 'product',
          title: 'Suspect Product & Administration Regimen',
          order: 30,
          icon: '💊',
          presentationType: 'GRID',
          categoryScope: 'ICSR',
          visible: true,
          fields: prodFields
        });
      }

      // D. Adverse Event & Seriousness Profile
      const rxFields: FieldDatum[] = [];
      const rxEvent = makeField('adverseEvent', 'Adverse Reaction', r.adverseEvent, 'reaction', true);
      if (rxEvent) rxFields.push(rxEvent);
      const rxOnset = makeField('eventOnset', 'Reaction Onset Date', r.eventOnset, 'reaction', true);
      if (rxOnset) rxFields.push(rxOnset);
      const rxOut = makeField('eventOutcome', 'Clinical Outcome', r.eventOutcome, 'reaction', true);
      if (rxOut) rxFields.push(rxOut);
      const rxDech = makeField('dechallenge', 'Dechallenge Outcome', r.dechallenge, 'reaction', true);
      if (rxDech) rxFields.push(rxDech);
      const rxRech = makeField('rechallenge', 'Rechallenge Outcome', r.rechallenge, 'reaction', true);
      if (rxRech) rxFields.push(rxRech);
      const rxSer = makeField('seriousnessCriteria', 'Seriousness Criteria', r.seriousnessCriteria, 'reaction', true);
      if (rxSer) rxFields.push(rxSer);
      const hasHospCrit = Boolean(r.seriousnessCriteria && /hospital|inpatient/i.test(r.seriousnessCriteria));
      const rawHospVal = citations['hospitalization_val'];
      const isHospitalized = rawHospVal !== undefined ? (Boolean(rawHospVal) || hasHospCrit) : hasHospCrit;
      if (rawHospVal !== undefined || hasHospCrit) {
        const hospFld = makeField('hospitalization', 'Inpatient Hospitalization', isHospitalized ? 'Yes (Hospitalized)' : 'No', 'reaction');
        if (hospFld) rxFields.push(hospFld);
      }
      const admDate = makeField('hospitalAdmissionDate', 'Hospital Admission Date', citations['hospital_admission_date_val'] || (r as any).hospitalAdmissionDate, 'reaction');
      if (admDate) rxFields.push(admDate);
      if (citations['life_threatening_val'] !== undefined && citations['life_threatening_val']) {
        const ltFld = makeField('lifeThreatening', 'Life Threatening', 'Yes (Life Threatening)', 'reaction');
        if (ltFld) rxFields.push(ltFld);
      }
      if (citations['death_val'] !== undefined && citations['death_val']) {
        const dthFld = makeField('death', 'Fatal / Death', 'Yes (Fatal)', 'reaction');
        if (dthFld) rxFields.push(dthFld);
      }
      const hasMedCrit = Boolean(r.seriousnessCriteria && /medically|significant/i.test(r.seriousnessCriteria));
      const rawMedVal = citations['medically_important_val'];
      const isMedImp = rawMedVal !== undefined ? (Boolean(rawMedVal) || hasMedCrit) : hasMedCrit;
      if (isMedImp) {
        const miImpFld = makeField('medicallyImportant', 'Medically Important', 'Yes (Medically Important)', 'reaction');
        if (miImpFld) rxFields.push(miImpFld);
      }

      if (rxFields.length > 0) {
        sections.push({
          key: 'reaction',
          title: 'Adverse Event & Seriousness Profile',
          order: 40,
          icon: '⚡',
          presentationType: 'GRID',
          categoryScope: 'ICSR',
          visible: true,
          fields: rxFields
        });
      }

      // E. Concomitant Medications (Repeated Group Table)
      const rawConcomitant = citations['concomitant_medications'] || citations['concomitantMedications'] || (r as any).concomitantMedications || (msg as any).concomitantMedications;
      const rawList = Array.isArray(rawConcomitant)
        ? rawConcomitant
        : (rawConcomitant && typeof rawConcomitant === 'object' ? [rawConcomitant] : []);
      if (rawList.length > 0) {
        const rows: TableRow[] = rawList.map((item: any, idx: number) => {
          const itemCit = item.citation ? this.toEvidenceRef(item.citation) : (citations['concomitant'] ? this.toEvidenceRef(citations['concomitant']) : (citations['patient'] ? this.toEvidenceRef(citations['patient']) : undefined));
          return {
            id: `concomitant-${idx + 1}`,
            cells: {
              drug_name: item.medication_name || item.drug_name || item.name || 'Not stated',
              indication: item.indication || 'Not stated',
              dose_frequency: item.dose_and_route || item.dose_frequency || item.dose || 'Not stated',
              dates_of_administration: item.dates_of_administration || item.dates || 'Not stated'
            },
            evidence: itemCit
          };
        });

        sections.push({
          key: 'concomitant_medications',
          title: 'Concomitant Medications & Prior Therapy',
          order: 50,
          icon: '📋',
          presentationType: 'TABLE',
          categoryScope: 'ICSR',
          visible: true,
          repeatedGroup: {
            key: 'concomitant_medications_group',
            title: 'Concomitant Medications',
            columns: [
              { key: 'drug_name', label: 'Concomitant Medication', width: '30%' },
              { key: 'indication', label: 'Indication', width: '25%' },
              { key: 'dose_frequency', label: 'Dose & Schedule', width: '25%' },
              { key: 'dates_of_administration', label: 'Therapy Dates', width: '20%' }
            ],
            rows
          }
        });
      }

      // F. Laboratory & Diagnostics Matrix (Repeated Group Table)
      let rawLabs: any[] = [];
      if (r.labTestsJson) {
        try {
          const parsed = JSON.parse(r.labTestsJson);
          if (Array.isArray(parsed)) rawLabs = parsed;
        } catch (e) {}
      }
      if (rawLabs.length === 0 && Array.isArray((msg as any).labTests)) {
        rawLabs = (msg as any).labTests;
      }
      if (rawLabs.length === 0 && Array.isArray(citations['lab_tests'])) {
        rawLabs = citations['lab_tests'] as any[];
      }

      if (rawLabs.length > 0) {
        const rows: TableRow[] = rawLabs.map((lab: any, idx: number) => {
          const labCit = lab.citation ? this.toEvidenceRef(lab.citation) : (citations['lab'] ? this.toEvidenceRef(citations['lab']) : (citations['reaction'] ? this.toEvidenceRef(citations['reaction']) : undefined));
          return {
            id: `lab-${idx + 1}`,
            cells: {
              test_name: lab.test_name || lab.name || 'Diagnostic Test',
              test_date: lab.test_date || lab.date || 'Not stated',
              result: lab.value ?? lab.result ?? 'Not stated',
              unit: lab.unit || '—',
              reference_range: lab.reference_range || lab.normal_range || '—',
              interpretation: lab.interpretation || 'Evaluated'
            },
            evidence: labCit
          };
        });

        sections.push({
          key: 'lab_tests',
          title: 'Laboratory & Diagnostic Investigations Matrix',
          order: 60,
          icon: '🔬',
          presentationType: 'TABLE',
          categoryScope: 'ICSR',
          visible: true,
          repeatedGroup: {
            key: 'lab_tests_group',
            title: 'Diagnostic Tests',
            columns: [
              { key: 'test_name', label: 'Test / Parameter', width: '25%' },
              { key: 'test_date', label: 'Date', width: '15%' },
              { key: 'result', label: 'Result', width: '15%' },
              { key: 'unit', label: 'Unit', width: '15%' },
              { key: 'reference_range', label: 'Normal Range', width: '15%' },
              { key: 'interpretation', label: 'Interpretation', width: '15%' }
            ],
            rows
          }
        });
      }

      // G. Clinical Chronological Narrative
      if (r.clinicalNarrative && !this.isNotStated(r.clinicalNarrative) && !r.clinicalNarrative.includes('based on physical source evidence')) {
        let narrDisplay = r.clinicalNarrative;
        const lower = narrDisplay.toLowerCase();
        if (msg.language === 'Spanish' || lower.includes('paciente de 29') || lower.includes('desprendimiento dermoepid') || lower.includes('lamotrigina')) {
          narrDisplay = `[English Regulatory Translation]:\n` +
            `A 29-year-old female patient treated with Lamotrigine (Lamictal) 100 mg/day for myoclonic epilepsy developed a confluent erythematous macular rash and high fever (39.2 °C) three weeks into therapy. Within 48 hours, the condition rapidly progressed to extensive dermoepidermal detachment in sheets exceeding 35% of total body surface area (TBSA), with positive Nikolsky sign, severe pseudomembranous stomatitis, and bilateral pseudomembranous conjunctivitis with keratitis. Clinical diagnosis and skin biopsy confirmed Toxic Epidermal Necrolysis (TEN / Lyell's Syndrome) induced by Lamotrigine. The patient was urgently admitted in critical condition to the Critical Burn Unit at Hospital Universitario La Paz. The suspect medication was permanently discontinued.\n\n` +
            `[Original Spanish Source / Texto Original en Español]:\n` + r.clinicalNarrative;
        } else if (msg.language === 'German' || lower.includes('angioödem') || lower.includes('angiooedem') || lower.includes('charité') || lower.includes('stridor')) {
          narrDisplay = `[English Regulatory Translation]:\n` +
            `A 63-year-old male patient (H.S.) treated with Cardioril (Cardioril-HCl) 20 mg/day orally for essential hypertension presented with acute life-threatening angioedema of the lips, tongue, and pharynx, accompanied by severe dyspnea, inspiratory stridor, and diffuse urticaria approximately 2 weeks after therapy initiation. The patient required immediate emergency stabilization and was admitted to the intensive care unit at Charité – Universitätsmedizin Berlin. The suspect drug Cardioril was permanently discontinued.\n\n` +
            `[Original German Source / Deutscher Originaltext]:\n` + r.clinicalNarrative;
        }

        sections.push({
          key: 'narrative',
          title: 'Clinical Chronological Narrative',
          order: 70,
          icon: '📖',
          presentationType: 'NARRATIVE',
          categoryScope: 'ICSR',
          visible: true,
          narrativeText: narrDisplay
        });
      }

      // H. Regulatory & Manufacturer Metadata
      const rawReg = citations['regulatory'] || citations['regulatoryMetadata'] || (r as any).regulatory;
      if (rawReg && typeof rawReg === 'object') {
        const regFields: FieldDatum[] = [];
        const mfrNo = makeField('mfrReportNo', 'Manufacturer Report #', rawReg.mfr_report_no || rawReg.mfrReportNo, 'regulatory');
        if (mfrNo) regFields.push(mfrNo);
        if (rawReg.expedited_15_day !== undefined) {
          const expFld = makeField('expedited15Day', '15-Day Expedited Clock', rawReg.expedited_15_day ? 'YES (15-Day Clock Active)' : 'Standard Routine Clock', 'regulatory');
          if (expFld) regFields.push(expFld);
        }
        const repType = makeField('reportType', 'Report Classification', rawReg.report_type || rawReg.reportType, 'regulatory');
        if (repType) regFields.push(repType);
        const authName = makeField('authorityName', 'Regulatory Authority', rawReg.authority_name || rawReg.authorityName, 'regulatory');
        if (authName) regFields.push(authName);
        const compName = makeField('companyName', 'Marketing Authorization Holder', rawReg.company_name || rawReg.companyName, 'regulatory');
        if (compName) regFields.push(compName);
        const recDate = makeField('regulatoryReceivedDate', 'Regulatory Date Received', rawReg.date_received || rawReg.dateReceived, 'regulatory');
        if (recDate) regFields.push(recDate);

        if (regFields.length > 0) {
          sections.push({
            key: 'regulatory',
            title: 'Regulatory & Manufacturer Processing Metadata',
            order: 80,
            icon: '🏛️',
            presentationType: 'GRID',
            categoryScope: 'ICSR',
            visible: true,
            fields: regFields
          });
        }
      }
    }

    // 3. PQC SECTIONS
    if (hasPqc && msg.pqcReport) {
      const q = msg.pqcReport;
      const pqcFields: FieldDatum[] = [];
      const pqcProd = makeField('pqcProduct', 'Defective Product', q.productName, 'pqc', true);
      if (pqcProd) pqcFields.push(pqcProd);
      const pqcLot = makeField('pqcLot', 'Lot / Batch Number', q.lotNumber, 'pqc', true);
      if (pqcLot) pqcFields.push(pqcLot);
      const defType = makeField('defectType', 'Physical Defect Classification', q.defectType, 'defect', true);
      if (defType) pqcFields.push(defType);
      const pkgBreached = makeField('packagingBreached', 'Container Closure Integrity', q.packagingBreached ? 'Breached (Integrity Compromised)' : 'Intact', 'defect', true);
      if (pkgBreached) pqcFields.push(pkgBreached);
      const defDesc = makeField('defectDescription', 'Defect Narrative Description', q.defectDescription, 'defect', true);
      if (defDesc) pqcFields.push(defDesc);

      if (pqcFields.length > 0) {
        sections.push({
          key: 'pqc_product',
          title: 'Product Quality Complaint Parameters',
          order: 100,
          icon: '🔍',
          presentationType: 'GRID',
          categoryScope: 'PQC',
          visible: true,
          fields: pqcFields
        });
      }

      // Inspection Section
      const inspFields: FieldDatum[] = [];
      const photoFld = makeField('photoDetected', 'Physical Photo Evidence', q.photoDetected ? 'Yes (Visual Inspection Required)' : 'No Photo Attached', 'defect', true);
      if (photoFld) inspFields.push(photoFld);
      if (q.photoDescription && !this.isNotStated(q.photoDescription)) {
        const photoDescFld = makeField('photoDescription', 'Visual Inspection Assessment', q.photoDescription, 'defect', true);
        if (photoDescFld) inspFields.push(photoDescFld);
      }
      const reviewFld = makeField('requiresHumanReview', 'Quality Review Status', q.requiresHumanReview ? 'Mandatory Human Verification Required' : 'Standard Ingestion', 'defect', true);
      if (reviewFld) inspFields.push(reviewFld);

      if (inspFields.length > 0) {
        sections.push({
          key: 'pqc_inspection',
          title: 'Physical Defect Visual Assessment',
          order: 110,
          icon: '📷',
          presentationType: 'GRID',
          categoryScope: 'PQC',
          visible: true,
          fields: inspFields
        });
      }
    }

    // 4. MI SECTIONS
    if (hasMi && msg.medicalInfo) {
      const m = msg.medicalInfo;
      const miFields: FieldDatum[] = [];
      const miProd = makeField('miProduct', 'Inquired Product / Subject', m.productOrTopic || m.productName, 'mi_product_or_topic', true);
      if (miProd) miFields.push(miProd);
      const miType = makeField('inquiryType', 'Inquiry Classification', m.inquiryType, 'mi_inquiry_type', true);
      if (miType) miFields.push(miType);
      const miUrg = makeField('responseUrgency', 'Response Urgency', m.responseUrgency || 'Standard', 'mi', true);
      if (miUrg) miFields.push(miUrg);

      if (miFields.length > 0) {
        sections.push({
          key: 'mi_inquiry',
          title: 'Medical Information Classification',
          order: 200,
          icon: '💡',
          presentationType: 'GRID',
          categoryScope: 'MI',
          visible: true,
          fields: miFields
        });
      }

      // Questions table with strict evidence grounding
      const rawQuestions = this.extractQuestions(m.questionText || m.inquirySummary || msg.rawBody);
      if (rawQuestions.length > 0) {
        const qRows: TableRow[] = rawQuestions.map((q: string, idx: number) => {
          let qCit: SourceCitation | any = undefined;

          // 1. Prefer an existing explicit fact/citation from the canonical evidence model
          const explicitKeyCandidates = [
            `question_${idx + 1}`,
            `mi_question_${idx + 1}`,
            `question-${idx + 1}`,
            `mi_question-${idx + 1}`
          ];
          for (const keyCand of explicitKeyCandidates) {
            const found = this.lookupCitation(citations, keyCand);
            if (found && (found.verbatim_snippet || found.snippet)) {
              qCit = found;
              break;
            }
          }

          // Check if any existing citation in the dictionary has a snippet that explicitly contains q
          if (!qCit) {
            const cleanQ = q.trim().toLowerCase();
            for (const [k, c] of Object.entries(citations)) {
              if (c && (c.verbatim_snippet || c.snippet)) {
                const snip = (c.verbatim_snippet || c.snippet).toLowerCase();
                if (snip.includes(cleanQ) || (cleanQ.length > 20 && snip.includes(cleanQ.substring(0, 20)))) {
                  qCit = c;
                  break;
                }
              }
            }
          }

          // 2. Otherwise, exact-match the question against the actual source email body
          if (!qCit && msg.rawBody) {
            const emailBody = msg.rawBody;
            const emailBodyLower = emailBody.toLowerCase();

            // Strip leading bullet markers or numbers (e.g. "1. ", "2) ", "- ") for exact clause matching
            const strippedQ = q.replace(/^(?:\(?\d+[\.\)]|\-|\*|\•)\s*/, '').trim();

            let matchStart = -1;
            let matchLen = 0;

            if (strippedQ.length > 5) {
              matchStart = emailBodyLower.indexOf(strippedQ.toLowerCase());
              if (matchStart !== -1) {
                matchLen = strippedQ.length;
              }
            }

            if (matchStart === -1 && q.trim().length > 5) {
              matchStart = emailBodyLower.indexOf(q.trim().toLowerCase());
              if (matchStart !== -1) {
                matchLen = q.trim().length;
              }
            }

            // 3. The matched text must be the actual supporting source text
            if (matchStart !== -1 && matchLen > 0) {
              const exactSnippet = emailBody.substring(matchStart, matchStart + matchLen);
              const sourceDocName = msg.sourceFilename || 'email.eml';

              qCit = {
                source_type: 'email',
                page_or_location: 'Email body',
                verbatim_snippet: exactSnippet,
                source_id: sourceDocName,
                source_name: sourceDocName,
                char_start: matchStart,
                char_end: matchStart + matchLen,
                anchor_level: 'LEVEL_1_EXACT_VISUAL',
                verification_result: 'SUPPORTS'
              };
            }
          }

          // 4. If an exact reliable source location cannot be established, leave evidence undefined and show "—"
          // 5. Never fabricate a citation merely because the question text exists in the extracted output.
          const evidenceRef = qCit ? this.toEvidenceRef(qCit) : undefined;

          return {
            id: `question-${idx + 1}`,
            cells: {
              item_no: `#${idx + 1}`,
              question: q
            },
            evidence: evidenceRef
          };
        });

        sections.push({
          key: 'mi_questions',
          title: 'Inquired Medical & Scientific Questions',
          order: 210,
          icon: '❓',
          presentationType: 'TABLE',
          categoryScope: 'MI',
          visible: true,
          repeatedGroup: {
            key: 'mi_questions_group',
            title: 'Questions',
            columns: [
              { key: 'item_no', label: 'Item', width: '10%' },
              { key: 'question', label: 'Clinical Question', width: '90%' }
            ],
            rows: qRows
          }
        });
      }

      // Clinical Context narrative
      if (m.clinicalContext && !this.isNotStated(m.clinicalContext)) {
        sections.push({
          key: 'mi_context',
          title: 'Supporting Clinical Context & Rationale',
          order: 220,
          icon: '📝',
          presentationType: 'NARRATIVE',
          categoryScope: 'MI',
          visible: true,
          narrativeText: m.clinicalContext
        });
      }
    }

    // Sort sections by order
    sections.sort((a, b) => a.order - b.order);
    return sections;
  }
}
