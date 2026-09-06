export type FactStatus = 'CONFIRMED' | 'NOT_STATED' | 'UNCERTAIN' | 'CONFLICT';
export type ConfidenceLevel = 'HIGH' | 'MEDIUM' | 'LOW';
export type ValidationGatingStatus = 'READY_FOR_REVIEW' | 'REVIEW_WITH_WARNINGS' | 'BLOCKED_BY_INTEGRITY_ERROR';
export type CaseUrgency = 'CRITICAL' | 'EXPEDITED' | 'STANDARD';
export type FactSection = 'PATIENT' | 'REPORTER' | 'PRODUCT' | 'EVENT' | 'PQC' | 'MI' | 'GENERAL';

export enum ReviewFocusCategory {
  UNCERTAIN_HANDWRITING = 'UNCERTAIN_HANDWRITING',
  PHOTO_DEFECT_INSPECTION = 'PHOTO_DEFECT_INSPECTION',
  EVIDENCE_CONFLICT = 'EVIDENCE_CONFLICT',
  MISSING_CRITICAL_FIELD = 'MISSING_CRITICAL_FIELD',
  MULTILINGUAL_TRANSLATION = 'MULTILINGUAL_TRANSLATION',
  EXPEDITED_15_DAY_CLOCK = 'EXPEDITED_15_DAY_CLOCK',
  CATEGORY_AMBIGUITY = 'CATEGORY_AMBIGUITY',
  VALIDATION_WARNING = 'VALIDATION_WARNING'
}

export interface EvidenceRef {
  sourceType: string;
  location: string;
  snippet: string;
  verificationResult?: 'SUPPORTS' | 'CONTRADICTS' | 'INSUFFICIENT';
  verificationRationale?: string;
}

export interface ReviewFocusItem {
  id: string;
  category: ReviewFocusCategory;
  fieldAffected?: string;
  headline: string;
  detail: string;
  actionSuggested: string;
  evidenceRef?: EvidenceRef;
}

export interface FactSummaryStats {
  totalFacts: number;
  confirmedCount: number;
  notStatedCount: number;
  uncertainCount: number;
  conflictCount: number;
}

export interface ReviewerFact {
  field: string;
  label: string;
  value: string;
  status: FactStatus;
  confidence: ConfidenceLevel;
  confidenceScore?: number;
  section: FactSection;
  evidence?: EvidenceRef;
  isEditing?: boolean;
  editValue?: string;
}

export interface PqcBriefDetails {
  productName: string;
  lotNumber: string;
  defectType: string;
  defectDescription: string;
  packagingBreached: boolean;
  photoDetected: boolean;
  photoDescription?: string;
  requiresHumanReview: boolean;
}

export interface MiBriefDetails {
  productName: string;
  inquiryType: string;
  inquirySummary: string;
  responseUrgency: string;
  questions: string[];
}

export interface NotRelevantBriefDetails {
  reason: string;
  sourceContext: string;
}

export interface ReviewerBrief {
  caseId: string;
  subject: string;
  sender: string;
  senderEmail: string;
  receivedDate: string;
  attachmentCount: number;
  primaryCategory: string;
  allCategories: string[];
  isMultiLabel: boolean;
  confidence: number;
  urgency: CaseUrgency;
  executiveSummary: string;
  validationGating: ValidationGatingStatus;
  validationWarnings: string[];
  reviewFocus: ReviewFocusItem[];
  factStats: FactSummaryStats;
  facts: ReviewerFact[];
  clinicalNarrative?: string;
  pqcDetails?: PqcBriefDetails;
  miDetails?: MiBriefDetails;
  notRelevantDetails?: NotRelevantBriefDetails;
}
