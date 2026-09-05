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
    age?: string;
    sex?: string;
    weight?: string;
    medical_history?: string;
  };
  product?: {
    product_name?: string;
    dose?: string;
  };
  reaction?: {
    reaction_pt?: string;
    is_serious?: boolean;
    seriousness_criteria?: string[];
  };
  narrative?: string;
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
  createdAt: string;
}

export interface LiteratureScreenResult {
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
}
