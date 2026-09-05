import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { LiteratureService } from '../../core/services/literature.service';
import { LiteratureArticle, LiteratureScreenResult, PatientCase } from '../../core/models/literature.model';

@Component({
  selector: 'app-literature-screening',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './literature-screening.component.html',
  styleUrls: ['./literature-screening.component.scss']
})
export class LiteratureScreeningComponent implements OnInit {
  private literatureService = inject(LiteratureService);
  private http = inject(HttpClient);

  screenedArticles: LiteratureArticle[] = [];
  currentResult?: LiteratureScreenResult;
  currentArticleName = '';
  
  isScreening = false;
  isLoadingHistory = true;
  errorMessage = '';
  successMessage = '';

  sampleArticles = [
    {
      name: 'article_03_multicase_series.pdf',
      label: 'Article 03 (Multi-Case Series: Cardioril / Corzapan)',
      description: 'The Lancet Regional Health — 3 identifiable individual patient cases requiring ICSR splitting.'
    },
    {
      name: 'article_04_preclinical_review.pdf',
      label: 'Article 04 (Preclinical Study — Negative Control)',
      description: 'Eur J Pharm Sci — In-vitro rat hepatocyte metabolic clearance. Zero human patients (exempt).'
    },
    {
      name: 'article_02_sjs_case.pdf',
      label: 'Article 02 (Single Case Report: Stevens-Johnson Syndrome)',
      description: 'Br J Clin Dermatol — Single patient with severe Stevens-Johnson Syndrome from Neuroval.'
    }
  ];

  ngOnInit() {
    this.loadHistory();
  }

  loadHistory() {
    this.isLoadingHistory = true;
    this.literatureService.getArticles().subscribe({
      next: (articles) => {
        this.screenedArticles = articles;
        this.isLoadingHistory = false;
      },
      error: () => {
        this.isLoadingHistory = false;
      }
    });
  }

  onFileSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      const file = input.files[0];
      this.screenFile(file);
    }
  }

  screenSample(sampleName: string) {
    this.isScreening = true;
    this.errorMessage = '';
    this.currentArticleName = sampleName;

    // Fetch sample PDF from test-data or backend and screen
    this.http.get(`/api/literature/sample-pdf?filename=${encodeURIComponent(sampleName)}`, { responseType: 'blob' }).subscribe({
      next: (blob) => {
        const file = new File([blob], sampleName, { type: 'application/pdf' });
        this.screenFile(file);
      },
      error: () => {
        // Fallback: send synthetic PDF blob or screen directly
        const file = new File([new Blob(['%PDF-1.4 simulated literature reprint'], { type: 'application/pdf' })], sampleName, { type: 'application/pdf' });
        this.screenFile(file);
      }
    });
  }

  private screenFile(file: File) {
    this.isScreening = true;
    this.errorMessage = '';
    this.currentArticleName = file.name;

    this.literatureService.uploadAndScreen(file).subscribe({
      next: (result) => {
        this.currentResult = result;
        this.isScreening = false;
        this.successMessage = `Screening complete for ${file.name}.`;
        this.loadHistory();
        setTimeout(() => this.successMessage = '', 5000);
      },
      error: (err) => {
        this.isScreening = false;
        this.errorMessage = `Screening failed: ${err.message || 'Server error'}`;
      }
    });
  }

  getPatientDemographics(c: PatientCase): string {
    if (c.patient_demographics) return c.patient_demographics;
    if (c.patient) {
      const parts = [c.patient.age, c.patient.sex, c.patient.weight].filter(Boolean);
      return parts.join(', ') || 'Not stated';
    }
    return 'Not stated';
  }

  getSuspectProduct(c: PatientCase): string {
    if (c.suspected_product) return c.suspected_product;
    if (c.product) {
      return [c.product.product_name, c.product.dose].filter(Boolean).join(' ') || 'Not stated';
    }
    return 'Not stated';
  }

  getAdverseReaction(c: PatientCase): string {
    if (c.adverse_reaction) return c.adverse_reaction;
    if (c.reaction) {
      return c.reaction.reaction_pt || 'Not stated';
    }
    return 'Not stated';
  }

  getSeriousness(c: PatientCase): string {
    if (c.seriousness) return c.seriousness;
    if (c.reaction) {
      return c.reaction.is_serious ? 'Serious (Hospitalization / Medically Significant)' : 'Non-Serious';
    }
    return 'Non-Serious';
  }
}
