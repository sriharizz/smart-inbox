import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { LiteratureArticle, LiteratureScreenResult, LiteratureReviewRequest } from '../models/literature.model';
import { AuditEvent } from '../models/audit.model';

@Injectable({
  providedIn: 'root'
})
export class LiteratureService {
  private http = inject(HttpClient);
  private baseUrl = '/api/literature';

  getArticles(): Observable<LiteratureArticle[]> {
    return this.http.get<LiteratureArticle[]>(this.baseUrl);
  }

  getArticleById(id: number): Observable<LiteratureArticle> {
    return this.http.get<LiteratureArticle>(`${this.baseUrl}/${id}`);
  }

  uploadAndScreen(file: File): Observable<LiteratureScreenResult> {
    const formData = new FormData();
    formData.append('file', file, file.name);
    return this.http.post<LiteratureScreenResult>(`${this.baseUrl}/upload`, formData);
  }

  reviewArticle(id: number, request: LiteratureReviewRequest): Observable<LiteratureArticle> {
    return this.http.post<LiteratureArticle>(`${this.baseUrl}/${id}/review`, request);
  }

  getArticleAuditTrail(id: number): Observable<AuditEvent[]> {
    return this.http.get<AuditEvent[]>(`${this.baseUrl}/${id}/audit`);
  }

  getArticlePdfUrl(id: number): string {
    return `${this.baseUrl}/${id}/pdf`;
  }

  getSamplePdfUrl(filename: string): string {
    return `${this.baseUrl}/sample-pdf?filename=${encodeURIComponent(filename)}`;
  }
}

