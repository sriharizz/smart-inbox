export type FactStatus = 'CONFIRMED' | 'NOT_STATED' | 'UNCERTAIN' | 'CONFLICT';
export type ConfidenceLevel = 'HIGH' | 'MEDIUM' | 'LOW' | '—' | 'N/A';
export type ValidationGatingStatus = 'READY_FOR_REVIEW' | 'REVIEW_WITH_WARNINGS' | 'BLOCKED_BY_INTEGRITY_ERROR';
export type CaseUrgency = 'CRITICAL' | 'EXPEDITED' | 'STANDARD';
export type FactSection = 'PATIENT' | 'REPORTER' | 'PRODUCT' | 'EVENT' | 'PQC' | 'MI' | 'GENERAL' | string;

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

export type AnchorLevel = 'LEVEL_1_EXACT_VISUAL' | 'LEVEL_2_PAGE_TEXT' | 'LEVEL_3_SNIPPET_ONLY';

export interface BoundingBoxRef {
  x0: number;
  y0: number;
  x1: number;
  y1: number;
  pageNumber?: number;
}

export interface EvidenceRef {
  sourceType: string;
  location: string;
  snippet: string;
  sourceId?: string;
  sourceName?: string;
  pageNumber?: number;
  boundingBox?: BoundingBoxRef;
  charStart?: number;
  charEnd?: number;
  anchorLevel?: AnchorLevel;
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
  confidence?: ConfidenceLevel;
  confidenceScore?: number;
  section: FactSection;
  evidence?: EvidenceRef;
  relatedFacts?: string[];
  isSelected?: boolean;
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
  evidence?: EvidenceRef;
}

export interface MiBriefDetails {
  productName: string;
  inquiryType: string;
  inquirySummary: string;
  clinicalContext?: string;
  informationRequested?: string;
  responseUrgency: string;
  questions: string[];
  evidence?: EvidenceRef;
}

export interface NotRelevantBriefDetails {
  reason: string;
  sourceContext: string;
}

export type SectionPresentationType = 'GRID' | 'TABLE' | 'NARRATIVE';

export interface FieldDatum {
  key: string;
  label: string;
  value: string;
  datatype?: 'string' | 'number' | 'date' | 'boolean' | 'badge';
  status: FactStatus;
  confidence?: ConfidenceLevel;
  evidence?: EvidenceRef;
  evidenceList?: EvidenceRef[];
  displayHints?: {
    isSeriousnessCritical?: boolean;
    isPrimaryId?: boolean;
    colSpan?: number;
    badgeVariant?: 'success' | 'warning' | 'danger' | 'info';
  };
}

export interface TableColumn {
  key: string;
  label: string;
  width?: string;
}

export interface TableRow {
  id?: string;
  cells: { [columnKey: string]: string };
  evidence?: EvidenceRef;
}

export interface RepeatedGroup {
  key: string;
  title: string;
  columns: TableColumn[];
  rows: TableRow[];
}

export interface ReviewerSection {
  key: string;
  title: string;
  order: number;
  icon?: string;
  presentationType: SectionPresentationType;
  categoryScope?: string; // 'ICSR' | 'PQC' | 'MI' | 'ALL' etc.
  visible: boolean;
  fields?: FieldDatum[];
  repeatedGroup?: RepeatedGroup;
  narrativeText?: string;
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
  factStatsSummary?: string;
  facts: ReviewerFact[];
  clinicalNarrative?: string;
  pqcDetails?: PqcBriefDetails;
  miDetails?: MiBriefDetails;
  notRelevantDetails?: NotRelevantBriefDetails;
  sections?: ReviewerSection[];
  reviewerAttention?: string[];
}
