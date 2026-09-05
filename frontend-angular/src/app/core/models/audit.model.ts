export interface AuditEvent {
  id: number;
  messageId?: number;
  timestamp: string;
  reviewerUsername?: string;
  reviewer?: string;
  action: string;
  targetField?: string;
  fieldChanged?: string;
  originalValue?: string;
  oldValue?: string;
  newValue?: string;
  reviewerComments?: string;
  justification?: string;
  isImmutable?: boolean;
}

export interface ReviewerAcceptRequest {
  reviewerUsername: string;
  comments?: string;
}

export interface ReviewerOverrideRequest {
  reviewerUsername: string;
  newCategory?: string;
  justification: string;
  fieldEdits?: Record<string, string>;
}
