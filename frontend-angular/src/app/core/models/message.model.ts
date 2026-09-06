export interface SourceCitation {
  source_type?: string;
  page_or_location?: string;
  verbatim_snippet?: string;
}

export interface Attachment {
  id: number;
  filename: string;
  contentType: string;
  sizeBytes: number;
  flavor?: string; // digital_form, scanned_handwritten, literature_article, non_english
  language?: string;
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
  productName: string;
  inquiryType: string;
  inquirySummary: string;
  responseUrgency: string;
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
  createdAt: string;
  updatedAt: string;
  attachments: Attachment[];
  icsrReport?: IcsrReport;
  pqcReport?: PqcReport;
  medicalInfo?: MedicalInfo;
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
