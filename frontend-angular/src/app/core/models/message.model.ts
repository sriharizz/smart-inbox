export interface SourceCitation {
  source_type?: string;
  sourceType?: string;
  source_id?: string;
  sourceId?: string;
  source_name?: string;
  sourceName?: string;
  page_or_location?: string;
  location?: string;
  verbatim_snippet?: string;
  snippet?: string;
  page_number?: number | null;
  pageNumber?: number | null;
  bounding_box?: any;
  boundingBox?: any;
  char_start?: number | null;
  charStart?: number | null;
  char_end?: number | null;
  charEnd?: number | null;
  anchor_level?: any;
  anchorLevel?: any;
  verification_result?: any;
  verificationResult?: any;
  verification_rationale?: string;
  verificationRationale?: string;
  [key: string]: any;
}

export interface Attachment {
  id: number;
  filename: string;
  contentType: string;
  sizeBytes: number;
  flavor?: string; // digital_form, scanned_handwritten, literature_article, non_english
  language?: string;
  documentSummary?: string;
}


export interface IcsrReport {
  id?: number;
  caseIdentifier?: string;
  patientIdentifier?: string;
  patientAge: string;
  patientSex: string;
  patientWeight: string;
  patientHistory: string;
  reporterName: string;
  reporterRole: string;
  reporterInstitution: string;
  reporterCountry: string;
  reporterContact: string;
  productName: string;
  productDose: string;
  productFrequency: string;
  productRoute: string;
  productLot: string;
  productExpiry: string;
  productIndication: string;
  adverseEvent: string;
  eventOnset: string;
  eventOutcome: string;
  seriousnessCriteria?: string;
  dechallenge: string;
  rechallenge: string;
  labTestsJson?: string;
  clinicalNarrative: string;
  sourceCitationsJson?: string;
}

export interface PqcReport {
  id?: number;
  productName: string;
  lotNumber: string;
  defectType: string;
  defectDescription: string;
  packagingBreached: boolean;
  photoDetected: boolean;
  photoDescription: string;
  requiresHumanReview: boolean;
  sourceCitationsJson?: string;
}

export interface MedicalInfo {
  id?: number;
  productOrTopic?: string;
  productName?: string;
  inquiryType?: string;
  questionText?: string;
  inquirySummary?: string;
  clinicalContext?: string;
  informationRequested?: string;
  responseUrgency?: string;
  sourceCitationsJson?: string;
}

export interface IntakeMessage {
  id: number;
  messageId: string;
  sender: string;
  senderEmail: string;
  recipient?: string;
  subject: string;
  receivedDate: string;
  rawBody: string;
  status: string; // RECEIVED, PROCESSING, TRIAGED, REVIEWED, OVERRIDDEN, FAILED
  primaryCategory: string;
  confidence: number;
  isMultiLabel: boolean;
  labelsJson?: string;
  executiveSummary?: string;
  language?: string;
  createdAt: string;
  updatedAt: string;
  sourceFilename?: string;
  attachments: Attachment[];
  icsrReport?: IcsrReport;
  pqcReport?: PqcReport;
  medicalInfo?: MedicalInfo;
  facts?: any[];
  factLedger?: any[];
}

export interface MessageSummary {
  id: number;
  messageId: string;
  sender: string;
  senderEmail: string;
  subject: string;
  receivedDate: string;
  status: string;
  primaryCategory: string;
  confidence: number;
  isMultiLabel: boolean;
  executiveSummary?: string;
  attachmentCount: number;
  requiresHumanReview: boolean;
  
  // Explicit Review Flags (Modeled separately from review status)
  flags?: {
    lowConfidence: boolean;
    evidenceConflict: boolean;
    imageReviewRequired: boolean;
    missingRequiredInfo: boolean;
  };
  priority?: 'CRITICAL' | 'EXPEDITED' | 'STANDARD';
}
