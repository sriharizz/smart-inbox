import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { AuditEvent } from '../models/audit.model';

@Injectable({
  providedIn: 'root'
})
export class AuditService {
  private http = inject(HttpClient);
  private baseUrl = '/api/audit-log';

  getAuditEvents(messageId?: number): Observable<AuditEvent[]> {
    let params = new HttpParams();
    if (messageId) {
      params = params.set('messageId', messageId.toString());
    }
    return this.http.get<AuditEvent[]>(this.baseUrl, { params });
  }
}
