import { SourceCitation } from './message.model';

export interface PatientCase {
  patient_id?: string;
  case_id?: string;
  patient_demographics?: string;
  suspected_product?: string;
  adverse_reaction?: string;
  seriousness?: string;
  source_location?: string;
  verbatim_evidence?: string;
  patient?: {
    identifier?: string;
    dob?: string;
    age?: string;
    sex?: string;
    weight?: string;
    country?: string;
    medical_history?: string;
    citation?: SourceCitation;
  };
  reporter?: {
    name?: string;
    role?: string;
    specialty?: string;
    institution?: string;
    country?: string;
    email_or_phone?: string;
    health_professional?: string;
    citation?: SourceCitation;
  };
  product?: {
    product_name?: string;
    formulation?: string;
    dose?: string;
    frequency?: string;
    route?: string;
    lot_number?: string;
    expiry_date?: string;
    indication?: string;
    start_date?: string;
    stop_date?: string;
    duration?: string;
    action_taken?: string;
    citation?: SourceCitation;
  };
  reaction?: {
    reaction_pt?: string;
    adverse_event?: string;
    onset_date?: string;
    outcome?: string;
    is_serious?: boolean;
    seriousness_criteria?: string[];
    hospitalization?: boolean;
    admission_date?: string;
    life_threatening?: boolean;
    death?: boolean;
    medically_important?: boolean;
    dechallenge?: string;
    rechallenge?: string;
    citation?: SourceCitation;
  };
  lab_tests?: Array<{
    test_name: string;
    value: string;
    unit?: string;
    reference_range?: string;
    interpretation?: string;
    citation?: SourceCitation;
  }>;
  narrative?: string;
  citations?: Record<string, SourceCitation>;
  processing_time_ms?: number;
}

export interface LiteratureArticle {
  id: number;
  filename: string;
  articleTitle?: string;
  authors?: string;
  journal?: string;
  publicationYear?: string;
  isReportable: boolean;
  exclusionReason?: string;
  studyType?: string;
  patientCasesCount: number;
  screeningSummary?: string;
  casesJson?: string;
  reviewStatus?: string;
  reviewedBy?: string;
  reviewedAt?: string;
  reviewerComments?: string;
  createdAt: string;
}

export interface LiteratureScreenResult {
  id?: number;
  filename?: string;
  article_title?: string;
  authors?: string;
  journal?: string;
  publication_year?: string;
  is_reportable: boolean;
  exclusion_reason?: string;
  study_type?: string;
  patient_cases_count: number;
  screening_summary?: string;
  individual_cases?: PatientCase[];
  review_status?: string;
  reviewed_by?: string;
  reviewed_at?: string;
  reviewer_comments?: string;
}

export interface LiteratureReviewRequest {
  action: 'ACCEPT' | 'OVERRIDE';
  reviewerUsername: string;
  comments: string;
  overrideIsReportable?: boolean;
  overrideCasesCount?: number;
}

