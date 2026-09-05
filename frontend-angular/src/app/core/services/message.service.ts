import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, map } from 'rxjs';
import { IntakeMessage, MessageSummary, SourceCitation } from '../models/message.model';
import { ReviewerAcceptRequest, ReviewerOverrideRequest } from '../models/audit.model';

@Injectable({
  providedIn: 'root'
})
export class MessageService {
  private http = inject(HttpClient);
  private baseUrl = '/api/messages';

  // Configurable prototype review threshold (not a hard-coded clinical standard)
  public confidenceReviewThreshold = 0.85;

  getMessages(): Observable<MessageSummary[]> {
    return this.http.get<MessageSummary[]>(this.baseUrl).pipe(
      map(messages => messages.map(m => this.enrichWithFlags(m)))
    );
  }

  getMessage(id: number): Observable<IntakeMessage> {
    return this.http.get<IntakeMessage>(`${this.baseUrl}/${id}`);
  }

  acceptMessage(id: number, request?: ReviewerAcceptRequest): Observable<IntakeMessage> {
    return this.http.post<IntakeMessage>(`${this.baseUrl}/${id}/accept`, request || {
      reviewerUsername: 'safety.reviewer@clinevo.com',
      comments: 'Reviewer confirmed AI triage & extracted facts.'
    });
  }

  overrideMessage(id: number, request: ReviewerOverrideRequest): Observable<IntakeMessage> {
    return this.http.post<IntakeMessage>(`${this.baseUrl}/${id}/override`, request);
  }

  triggerIngest(): Observable<{ status: string; newMessagesIngested: number; message: string }> {
    return this.http.post<{ status: string; newMessagesIngested: number; message: string }>(
      `${this.baseUrl}/ingest`,
      {}
    );
  }

  getAttachmentDownloadUrl(attachmentId: number): string {
    return `${this.baseUrl}/attachments/${attachmentId}/download`;
  }

  parseCitations(citationsJson?: string): Record<string, SourceCitation> {
    if (!citationsJson) return {};
    try {
      return JSON.parse(citationsJson);
    } catch {
      return {};
    }
  }

  private enrichWithFlags(m: MessageSummary): MessageSummary {
    const isLowConf = m.confidence > 0 && m.confidence < this.confidenceReviewThreshold;
    const isImageReview = m.requiresHumanReview;
    const isConflict = m.isMultiLabel && m.primaryCategory.includes('ICSR') && m.primaryCategory.includes('PQC');
    
    // Model review flags distinctly from status
    m.flags = {
      lowConfidence: isLowConf,
      evidenceConflict: isConflict,
      imageReviewRequired: isImageReview,
      missingRequiredInfo: false
    };

    // Calculate clinical urgency priority
    if (m.requiresHumanReview || (m.isMultiLabel && m.primaryCategory.includes('ICSR'))) {
      m.priority = 'CRITICAL';
    } else if (m.primaryCategory.includes('ICSR')) {
      m.priority = 'EXPEDITED'; // 15-day regulatory clock
    } else {
      m.priority = 'STANDARD';
    }

    return m;
  }
}
