import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { LiteratureArticle, LiteratureScreenResult } from '../models/literature.model';

@Injectable({
  providedIn: 'root'
})
export class LiteratureService {
  private http = inject(HttpClient);
  private baseUrl = '/api/literature';

  getArticles(): Observable<LiteratureArticle[]> {
    return this.http.get<LiteratureArticle[]>(this.baseUrl);
  }

  uploadAndScreen(file: File): Observable<LiteratureScreenResult> {
    const formData = new FormData();
    formData.append('file', file, file.name);
    return this.http.post<LiteratureScreenResult>(`${this.baseUrl}/upload`, formData);
  }
}
