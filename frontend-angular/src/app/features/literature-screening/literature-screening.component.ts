import { Component, inject, OnInit, ChangeDetectorRef, ElementRef, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { DomSanitizer } from '@angular/platform-browser';
import { LiteratureService } from '../../core/services/literature.service';
import { LiteratureArticle, LiteratureScreenResult, PatientCase } from '../../core/models/literature.model';
import { SourceCitation } from '../../core/models/message.model';
import * as pdfjsLib from 'pdfjs-dist';

// Initialize PDF.js worker
if (typeof window !== 'undefined') {
  try {
    pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.10.38/pdf.worker.min.mjs';
  } catch (e) {}
}

export interface PdfHighlightBox {
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface ActiveEvidenceContext {
  fieldLabel: string;
  factValue: string;
  pageNumber: number;
  verbatimSnippet: string;
  anchorLevel: string;
  boundingBox?: any;
}

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
  private sanitizer = inject(DomSanitizer);
  private cdr = inject(ChangeDetectorRef);

  screenedArticles: LiteratureArticle[] = [];
  currentResult?: LiteratureScreenResult;
  currentArticleName = '';
  
  isScreening = false;
  isLoadingHistory = true;
  errorMessage = '';
  successMessage = '';

  // Multi-Case Navigation
  selectedCaseIndex = 0;

  // PDF.js Canvas & Coordinate Overlay State
  @ViewChild('pdfCanvas') pdfCanvasRef?: ElementRef<HTMLCanvasElement>;
  pdfHighlightBox: PdfHighlightBox | null = null;
  pdfCanvasWidth = 0;
  pdfCanvasHeight = 0;
  isRenderingPdf = false;
  pdfRenderError = false;
  pdfTotalPages = 1;
  activePageNumber = 1;
  zoomLevel = 100;
  private currentPdfDoc: any = null;
  private currentPdfData: Uint8Array | null = null;

  // Active Evidence Inspection State
  activeEvidenceContext: ActiveEvidenceContext | null = null;

  // All 7 Official Literature Benchmark Articles
  sampleArticles = [
    {
      name: 'article_01_dili_case.pdf',
      label: 'LIT-01 — Single Case: DILI (Cardioril)',
      description: 'Single identifiable patient with drug-induced liver injury; Table 1 diagnostic LFTs (ALT, AST, Total Bilirubin).'
    },
    {
      name: 'article_02_sjs_case.pdf',
      label: 'LIT-02 — Single Case: SJS (Neuroval)',
      description: 'Single identifiable patient with severe Stevens-Johnson Syndrome requiring burn ICU admission.'
    },
    {
      name: 'article_03_multicase_series.pdf',
      label: 'LIT-03 — Multi-Case Series: 3 Patients (A.J., B.L., C.M.)',
      description: 'Clinical case series requiring multi-case splitting into 3 isolated ICSR records with case matrix Table 1.'
    },
    {
      name: 'article_04_preclinical_review.pdf',
      label: 'LIT-04 — Preclinical Study: Negative Control (In-Vitro)',
      description: 'In-vitro rat hepatocyte metabolic clearance. Zero human patients (ICH E2B exempt non-reportable).'
    },
    {
      name: 'article_05_meta_analysis_review.pdf',
      label: 'LIT-05 — Systematic Review: Negative Control (34 RCTs)',
      description: 'Meta-analysis of 12,450 aggregate patients. No individual clinical course (ICH E2B exempt non-reportable).'
    },
    {
      name: 'article_06_buried_case_study.pdf',
      label: 'LIT-06 — Buried Case Study: Patient H.L. (Myocarditis)',
      description: 'Individual patient buried in literature reprint; narrative on Page 1 links to cardiac biomarker Table 1 on Page 2.'
    },
    {
      name: 'article_07_complex_screening_case.pdf',
      label: 'LIT-07 — Complex Screening: 420-Patient Cohort + 2 Cases',
      description: 'Observational registry background (420 pts, non-ICSR) combined with 2 distinct reportable cases (T.K. & M.S.).'
    }
  ];

  ngOnInit() {
    this.loadHistory();
  }

  loadHistory() {
    this.isLoadingHistory = true;
    this.cdr.markForCheck();
    this.literatureService.getArticles().subscribe({
      next: (articles) => {
        this.screenedArticles = articles;
        this.isLoadingHistory = false;
        this.cdr.markForCheck();
      },
      error: () => {
        this.isLoadingHistory = false;
        this.cdr.markForCheck();
      }
    });
  }

  onFileSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      const file = input.files[0];
      this.currentArticleName = file.name;
      this.isScreening = true;
      this.errorMessage = '';
      this.pdfHighlightBox = null;
      this.activeEvidenceContext = null;
      this.selectedCaseIndex = 0;

      file.arrayBuffer().then((buffer) => {
        this.currentPdfData = new Uint8Array(buffer);
        this.literatureService.uploadAndScreen(file).subscribe({
          next: (result) => {
            this.currentResult = result;
            this.isScreening = false;
            this.successMessage = `Screening complete for ${file.name}.`;
            this.currentPdfDoc = null;
            this.loadAndRenderPdfPage(1);
            this.loadHistory();
            this.cdr.markForCheck();
            setTimeout(() => {
              this.successMessage = '';
              this.cdr.markForCheck();
            }, 6000);
          },
          error: (err) => {
            this.isScreening = false;
            this.errorMessage = `Screening failed: ${err.message || 'Server error'}`;
            this.cdr.markForCheck();
          }
        });
      }).catch((err) => {
        this.isScreening = false;
        this.errorMessage = `Could not read file buffer: ${err.message}`;
        this.cdr.markForCheck();
      });
    }
  }

  screenSample(sampleName: string) {
    this.isScreening = true;
    this.errorMessage = '';
    this.currentArticleName = sampleName;
    this.pdfHighlightBox = null;
    this.activeEvidenceContext = null;
    this.selectedCaseIndex = 0;

    // Fetch sample PDF from backend
    this.http.get(`/api/literature/sample-pdf?filename=${encodeURIComponent(sampleName)}`, { responseType: 'arraybuffer' }).subscribe({
      next: (buffer) => {
        this.currentPdfData = new Uint8Array(buffer);
        const file = new File([buffer], sampleName, { type: 'application/pdf' });

        this.literatureService.uploadAndScreen(file).subscribe({
          next: (result) => {
            this.currentResult = result;
            this.isScreening = false;
            this.successMessage = `Screening complete for ${sampleName}.`;
            this.currentPdfDoc = null;
            this.loadAndRenderPdfPage(1);
            this.loadHistory();
            this.cdr.markForCheck();
            setTimeout(() => {
              this.successMessage = '';
              this.cdr.markForCheck();
            }, 6000);
          },
          error: (err) => {
            this.isScreening = false;
            this.errorMessage = `Screening failed: ${err.message || 'Server error'}`;
            this.cdr.markForCheck();
          }
        });
      },
      error: (err) => {
        this.isScreening = false;
        this.errorMessage = `Could not load sample PDF: ${err.message || 'Network error'}`;
        this.cdr.markForCheck();
      }
    });
  }

  openArchivedArticle(item: LiteratureArticle) {
    this.currentArticleName = item.filename;
    this.pdfHighlightBox = null;
    this.activeEvidenceContext = null;
    this.selectedCaseIndex = 0;
    
    let individualCases: PatientCase[] = [];
    if (item.casesJson) {
      try {
        individualCases = JSON.parse(item.casesJson);
      } catch (e) {}
    }

    this.currentResult = {
      id: item.id,
      filename: item.filename,
      article_title: item.articleTitle,
      authors: item.authors,
      journal: item.journal,
      publication_year: item.publicationYear,
      is_reportable: item.isReportable,
      exclusion_reason: item.exclusionReason,
      study_type: item.studyType,
      patient_cases_count: item.patientCasesCount,
      screening_summary: item.screeningSummary,
      individual_cases: individualCases,
      review_status: item.reviewStatus,
      reviewed_by: item.reviewedBy,
      reviewed_at: item.reviewedAt,
      reviewer_comments: item.reviewerComments
    };

    // Load PDF bytes from endpoint
    this.http.get(`/api/literature/${item.id}/pdf`, { responseType: 'arraybuffer' }).subscribe({
      next: (buffer) => {
        this.currentPdfData = new Uint8Array(buffer);
        this.currentPdfDoc = null;
        this.loadAndRenderPdfPage(1);
        this.cdr.markForCheck();
      },
      error: () => {
        // Fallback to sample-pdf
        this.http.get(`/api/literature/sample-pdf?filename=${encodeURIComponent(item.filename)}`, { responseType: 'arraybuffer' }).subscribe({
          next: (buf) => {
            this.currentPdfData = new Uint8Array(buf);
            this.currentPdfDoc = null;
            this.loadAndRenderPdfPage(1);
            this.cdr.markForCheck();
          }
        });
      }
    });
  }

  // Multi-Case Selection
  selectCase(index: number) {
    this.selectedCaseIndex = index;
    this.pdfHighlightBox = null;
    this.activeEvidenceContext = null;
    this.cdr.markForCheck();
  }

  get selectedCase(): PatientCase | undefined {
    if (!this.currentResult?.individual_cases || this.currentResult.individual_cases.length === 0) {
      return undefined;
    }
    return this.currentResult.individual_cases[this.selectedCaseIndex] || this.currentResult.individual_cases[0];
  }

  getCaseLabel(c: PatientCase, index: number): string {
    const ptId = c.patient?.identifier || c.patient_id || c.case_id;
    if (ptId && ptId !== 'Not stated' && ptId !== 'Unknown') {
      return `Case ${index + 1} — ${ptId}`;
    }
    const ptDemo = [c.patient?.age ? `${c.patient.age}yo` : '', c.patient?.sex].filter(Boolean).join(' ');
    if (ptDemo) {
      return `Case ${index + 1} — ${ptDemo}`;
    }
    return `Case ${index + 1}`;
  }

  // Generic Aggregate Background Separation
  get aggregateBackgroundInfo(): { present: boolean; count?: string; description?: string } {
    if (!this.currentResult) return { present: false };
    const text = (this.currentResult.screening_summary || '') + ' ' + (this.currentResult.study_type || '');
    const match = text.match(/(\d+)[-\s]patient\s+(?:cohort|registry|population|study)|cohort of\s+(\d+)\s+patients/i);
    if (match && this.currentResult.individual_cases && this.currentResult.individual_cases.length > 0) {
      const count = match[1] || match[2];
      return {
        present: true,
        count: count,
        description: `Aggregate observational cohort of ${count} patients serves as clinical background and is excluded from single-case ICSR ingestion.`
      };
    }
    return { present: false };
  }

  // PDF.js Canvas Page Rendering with Coordinate Highlight Overlay
  async loadAndRenderPdfPage(pageNumber: number, bbox?: any) {
    this.isRenderingPdf = true;
    this.pdfRenderError = false;
    this.activePageNumber = pageNumber;
    this.cdr.markForCheck();

    try {
      if (!this.currentPdfDoc) {
        if (!this.currentPdfData) {
          this.isRenderingPdf = false;
          return;
        }
        const loadingTask = pdfjsLib.getDocument({ data: this.currentPdfData });
        this.currentPdfDoc = await loadingTask.promise;
        this.pdfTotalPages = this.currentPdfDoc.numPages;
      }

      const safePageNum = Math.max(1, Math.min(pageNumber, this.pdfTotalPages));
      const page = await this.currentPdfDoc.getPage(safePageNum);

      setTimeout(async () => {
        const canvas = this.pdfCanvasRef?.nativeElement;
        if (!canvas) {
          this.isRenderingPdf = false;
          return;
        }

        const baseScale = 1.333333 * (this.zoomLevel / 100);
        const viewport = page.getViewport({ scale: baseScale });
        const dpr = typeof window !== 'undefined' ? (window.devicePixelRatio || 1) : 1;

        canvas.width = Math.floor(viewport.width * dpr);
        canvas.height = Math.floor(viewport.height * dpr);
        canvas.style.width = Math.floor(viewport.width) + 'px';
        canvas.style.height = Math.floor(viewport.height) + 'px';
        this.pdfCanvasWidth = Math.floor(viewport.width);
        this.pdfCanvasHeight = Math.floor(viewport.height);

        const ctx = canvas.getContext('2d');
        if (!ctx) {
          this.isRenderingPdf = false;
          return;
        }
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

        await page.render({ canvasContext: ctx, viewport }).promise;

        if (bbox) {
          this.applyBoundingBoxHighlight(bbox);
        } else {
          this.pdfHighlightBox = null;
        }

        this.isRenderingPdf = false;
        this.cdr.markForCheck();
      }, 40);

    } catch (err) {
      console.warn('PDF.js rendering error:', err);
      this.pdfRenderError = true;
      this.isRenderingPdf = false;
      this.cdr.markForCheck();
    }
  }

  // Coordinate Highlight Box Positioning
  applyBoundingBoxHighlight(bbox?: any) {
    if (!bbox) {
      this.pdfHighlightBox = null;
      this.cdr.markForCheck();
      return;
    }
    const baseScale = 1.333333 * (this.zoomLevel / 100);
    const x0 = bbox.x0 !== undefined ? bbox.x0 : bbox.x;
    const y0 = bbox.y0 !== undefined ? bbox.y0 : bbox.y;
    const x1 = bbox.x1 !== undefined ? bbox.x1 : (bbox.x + (bbox.w || bbox.width || 0));
    const y1 = bbox.y1 !== undefined ? bbox.y1 : (bbox.y + (bbox.h || bbox.height || 0));

    this.pdfHighlightBox = {
      x: Math.max(0, x0 * baseScale),
      y: Math.max(0, y0 * baseScale),
      w: Math.max(8, (x1 - x0) * baseScale),
      h: Math.max(8, (y1 - y0) * baseScale)
    };
    this.cdr.markForCheck();
    this.scrollPdfTargetIntoView();
  }

  scrollPdfTargetIntoView() {
    setTimeout(() => {
      const el = document.getElementById('pdf-evidence-target');
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }, 60);
  }

  // Evidence Click Navigation
  onEvidenceClick(citation?: SourceCitation, fieldLabel?: string, factValue?: string) {
    if (!citation) return;
    const pageNum = citation.page_number || citation.pageNumber || 1;
    const bbox = citation.bounding_box || citation.boundingBox;

    this.activeEvidenceContext = {
      fieldLabel: fieldLabel || 'Clinical Fact',
      factValue: factValue || '',
      pageNumber: pageNum,
      verbatimSnippet: citation.verbatim_snippet || citation.snippet || citation['verbatim_quote'] || 'Source passage highlighted in document',
      anchorLevel: citation.anchor_level || 'LEVEL_1_EXACT_VISUAL',
      boundingBox: bbox
    };

    if (pageNum !== this.activePageNumber) {
      this.loadAndRenderPdfPage(pageNum, bbox);
    } else {
      this.applyBoundingBoxHighlight(bbox);
    }
  }

  isElevatedLab(lab: any): boolean {
    if (!lab || !lab.interpretation) return false;
    const interp = String(lab.interpretation).toLowerCase();
    return interp.includes('elevated') || interp.includes('high');
  }

  clearActiveEvidence() {
    this.activeEvidenceContext = null;
    this.pdfHighlightBox = null;
    this.cdr.markForCheck();
  }

  // Zoom & Page Navigation Controls
  zoomIn() {
    if (this.zoomLevel < 180) {
      this.zoomLevel += 15;
      this.loadAndRenderPdfPage(this.activePageNumber, this.activeEvidenceContext?.boundingBox);
    }
  }

  zoomOut() {
    if (this.zoomLevel > 65) {
      this.zoomLevel -= 15;
      this.loadAndRenderPdfPage(this.activePageNumber, this.activeEvidenceContext?.boundingBox);
    }
  }

  resetZoom() {
    this.zoomLevel = 100;
    this.loadAndRenderPdfPage(this.activePageNumber, this.activeEvidenceContext?.boundingBox);
  }

  prevPdfPage() {
    if (this.activePageNumber > 1) {
      this.loadAndRenderPdfPage(this.activePageNumber - 1);
    }
  }

  nextPdfPage() {
    if (this.activePageNumber < this.pdfTotalPages) {
      this.loadAndRenderPdfPage(this.activePageNumber + 1);
    }
  }

  // Fact Evidence Extractors
  getCitation(caseItem?: PatientCase, field?: string): SourceCitation | undefined {
    if (!caseItem) return undefined;
    if (caseItem.citations && field && caseItem.citations[field]) {
      return caseItem.citations[field];
    }
    if (field === 'identifier' || field === 'age' || field === 'sex' || field === 'weight' || field === 'medical_history') {
      return caseItem.patient?.citation;
    }
    if (field === 'product_name' || field === 'dose' || field === 'route' || field === 'indication') {
      return caseItem.product?.citation;
    }
    if (field === 'adverse_event' || field === 'seriousness' || field === 'outcome') {
      return caseItem.reaction?.citation;
    }
    return undefined;
  }

  getSeriousnessDisplay(c?: PatientCase): string {
    if (!c) return 'Non-Serious';
    if (c.seriousness && c.seriousness !== 'Non-Serious' && c.seriousness !== 'Unknown') {
      return c.seriousness;
    }
    const rx = c.reaction;
    if (rx) {
      const validCriteria: string[] = (rx.seriousness_criteria || []).filter(
        (sc: string) => sc && !sc.toLowerCase().includes('non-serious') && !sc.toLowerCase().includes('unknown')
      );
      const isSerious = rx.hospitalization || rx.life_threatening || rx.death || rx.medically_important || validCriteria.length > 0;
      if (!isSerious) {
        return 'Non-Serious';
      }
      if (validCriteria.length > 0) {
        return `Serious (${validCriteria.join(' / ')})`;
      }
      if (rx.hospitalization) {
        return 'Serious (Hospitalization)';
      }
      if (rx.life_threatening) {
        return 'Serious (Life-threatening)';
      }
      if (rx.death) {
        return 'Serious (Death/Fatal)';
      }
      if (rx.medically_important) {
        return 'Serious (Medically Significant)';
      }
      return 'Serious';
    }
    return 'Non-Serious';
  }
}
