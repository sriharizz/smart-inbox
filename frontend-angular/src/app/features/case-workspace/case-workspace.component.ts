import { Component, inject, OnInit, ChangeDetectorRef, ElementRef, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';
import { MessageService } from '../../core/services/message.service';
import { AuditService } from '../../core/services/audit.service';
import { IntakeMessage, Attachment, SourceCitation } from '../../core/models/message.model';
import { resolveCaseId } from '../../core/utils/case-id.util';
import { AuditEvent } from '../../core/models/audit.model';
import {
  ReviewerBrief,
  ReviewerFact,
  ReviewFocusItem,
  FactStatus,
  EvidenceRef,
  BoundingBoxRef,
  ReviewerSection,
  FieldDatum,
  RepeatedGroup,
  TableRow
} from '../../core/models/reviewer-brief.model';
import { ReviewerBriefBuilder } from '../../core/services/reviewer-brief-builder';
import * as pdfjsLib from 'pdfjs-dist';

// Initialize PDF.js worker
if (typeof window !== 'undefined') {
  try {
    pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.10.38/pdf.worker.min.mjs';
  } catch (e) {}
}

export interface EmailSegment {
  text: string;
  isHighlighted: boolean;
}

export interface ActiveEvidenceContext extends EvidenceRef {
  fieldKey: string;
  fieldLabel: string;
  factValue: string;
}

export interface PdfHighlightBox {
  x: number;
  y: number;
  w: number;
  h: number;
}

@Component({
  selector: 'app-case-workspace',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './case-workspace.component.html',
  styleUrls: ['./case-workspace.component.scss']
})
export class CaseWorkspaceComponent implements OnInit {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private messageService = inject(MessageService);
  private auditService = inject(AuditService);
  private sanitizer = inject(DomSanitizer);
  private cdr = inject(ChangeDetectorRef);

  messageId!: number;
  message?: IntakeMessage;
  brief?: ReviewerBrief;
  auditEvents: AuditEvent[] = [];
  isLoading = true;
  errorMessage = '';

  // Left Source Panel State
  activeTab: 'EMAIL' | number = 'EMAIL'; // 'EMAIL' or attachment ID
  activeAttachment?: Attachment;
  safeAttachmentUrl?: SafeResourceUrl;
  zoomLevel = 100;
  activePageNumber = 1;

  // PDF.js Canvas & Coordinate Overlay State
  @ViewChild('pdfCanvas') pdfCanvasRef?: ElementRef<HTMLCanvasElement>;
  pdfHighlightBox: PdfHighlightBox | null = null;
  pdfCanvasWidth = 0;
  pdfCanvasHeight = 0;
  isRenderingPdf = false;
  pdfRenderError = false;
  pdfTotalPages = 1;
  private currentPdfDoc: any = null;
  private currentPdfAttachmentId: number | null = null;

  // Safe Email Segmentation & Highlighting State
  emailSegments: EmailSegment[] = [];
  emailHighlightStatus: 'NONE' | 'EXACT' | 'MULTIPLE_OCCURRENCES' | 'NOT_FOUND' = 'NONE';

  // Active Evidence Inspection & Selection State
  activeEvidence?: ActiveEvidenceContext;
  selectedFact?: ReviewerFact;

  // Fact Filtering & Category Tabs
  selectedCategoryTab: 'ALL' | 'ICSR' | 'PQC' | 'MI' = 'ALL';
  selectedFactStatusFilter: 'ALL' | 'ATTENTION' | 'CONFIRMED' | 'NOT_STATED' = 'ALL';

  // Human Review & Override State
  isEditing = false;
  overrideCategory = '';
  overrideJustification = '';
  overrideFieldEdits: Record<string, string> = {};
  isSubmittingAction = false;
  actionSuccessMessage = '';
  isFlaggedForEscalation = false;

  // Collapsible Panels
  showAuditTrail = false;
  showExecutiveSummary = true;
  isExecutiveSummaryExpanded = false;

  toggleExecutiveSummary(): void {
    this.isExecutiveSummaryExpanded = !this.isExecutiveSummaryExpanded;
  }

  get factSummaryLine(): string {
    if (!this.brief?.factStats) return '';
    return this.brief.factStatsSummary || ReviewerBriefBuilder.formatFactStats(this.brief.factStats);
  }

  ngOnInit() {
    this.route.paramMap.subscribe(params => {
      const id = params.get('id');
      if (id) {
        this.messageId = +id;
        this.loadCaseData(this.messageId);
      }
    });
  }

  loadCaseData(id: number) {
    this.isLoading = true;
    this.errorMessage = '';
    this.messageService.getMessage(id).subscribe({
      next: (data) => {
        this.message = data;
        this.overrideCategory = data.primaryCategory;

        // Build synthesized ReviewerBrief
        this.brief = ReviewerBriefBuilder.buildFromMessage(data);

        // Initialize override field edits
        this.initializeFieldEdits();

        // Initialize email segments with raw email text
        if (data.rawBody) {
          this.emailSegments = [{ text: data.rawBody, isHighlighted: false }];
        }

        // Default to first PDF or image attachment if present, otherwise Email
        if (data.attachments && data.attachments.length > 0) {
          this.selectAttachmentTab(data.attachments[0]);
        } else {
          this.selectEmailTab();
        }

        this.loadAuditTrail(id);
        this.isLoading = false;
        this.cdr.markForCheck();
      },
      error: (err) => {
        this.errorMessage = `Failed to load case details: ${err.message || 'Server error'}`;
        this.isLoading = false;
        this.cdr.markForCheck();
      }
    });
  }

  loadAuditTrail(id: number) {
    this.auditService.getAuditEvents(id).subscribe({
      next: (events) => {
        this.auditEvents = events;
        this.cdr.markForCheck();
      },
      error: () => {}
    });
  }

  initializeFieldEdits() {
    if (!this.brief) return;
    this.overrideFieldEdits = {};
    for (const f of this.brief.facts) {
      this.overrideFieldEdits[f.field] = f.value;
    }
  }

  // Left Viewer Controls
  selectEmailTab() {
    this.activeTab = 'EMAIL';
    this.activeAttachment = undefined;
    this.safeAttachmentUrl = undefined;
    this.pdfHighlightBox = null;
    this.resetEmailHighlight();
  }

  selectAttachmentTab(att: Attachment, pageNumber?: number) {
    this.activeTab = att.id;
    this.activeAttachment = att;
    this.activePageNumber = pageNumber || 1;
    this.pdfHighlightBox = null;
    this.resetEmailHighlight();

    let rawUrl = this.messageService.getAttachmentDownloadUrl(att.id);
    if (pageNumber && this.isPdfAttachment(att)) {
      rawUrl += `#page=${pageNumber}`;
    }
    this.safeAttachmentUrl = this.sanitizer.bypassSecurityTrustResourceUrl(rawUrl);

    if (this.isPdfAttachment(att)) {
      const bbox = (this.activeEvidence && (this.activeEvidence.pageNumber === undefined || this.activeEvidence.pageNumber === this.activePageNumber))
        ? this.activeEvidence.boundingBox
        : undefined;
      this.loadAndRenderPdfPage(att.id, this.activePageNumber, bbox);
    }
  }

  isImageAttachment(att?: Attachment): boolean {
    if (!att) return false;
    const name = att.filename.toLowerCase();
    return name.endsWith('.jpg') || name.endsWith('.jpeg') || name.endsWith('.png');
  }

  isPdfAttachment(att?: Attachment): boolean {
    if (!att) return false;
    return att.filename.toLowerCase().endsWith('.pdf');
  }

  zoomIn() {
    if (this.zoomLevel < 180) {
      this.zoomLevel += 15;
      if (this.activeAttachment && this.isPdfAttachment(this.activeAttachment)) {
        this.loadAndRenderPdfPage(this.activeAttachment.id, this.activePageNumber, this.activeEvidence?.boundingBox);
      }
    }
  }

  zoomOut() {
    if (this.zoomLevel > 60) {
      this.zoomLevel -= 15;
      if (this.activeAttachment && this.isPdfAttachment(this.activeAttachment)) {
        this.loadAndRenderPdfPage(this.activeAttachment.id, this.activePageNumber, this.activeEvidence?.boundingBox);
      }
    }
  }

  resetZoom() {
    this.zoomLevel = 100;
    if (this.activeAttachment && this.isPdfAttachment(this.activeAttachment)) {
      this.loadAndRenderPdfPage(this.activeAttachment.id, this.activePageNumber, this.activeEvidence?.boundingBox);
    }
  }

  // PDF.js Canvas Page Rendering with Coordinate Highlight Overlay
  async loadAndRenderPdfPage(attachmentId: number, pageNumber: number, bbox?: BoundingBoxRef) {
    this.isRenderingPdf = true;
    this.pdfRenderError = false;
    this.pdfHighlightBox = null;
    this.activePageNumber = pageNumber;
    this.cdr.markForCheck();

    try {
      if (this.currentPdfAttachmentId !== attachmentId || !this.currentPdfDoc) {
        const downloadUrl = this.messageService.getAttachmentDownloadUrl(attachmentId);
        const baseUrl = (typeof window !== 'undefined' && window.location?.origin && window.location.origin !== 'null')
          ? window.location.origin
          : 'http://localhost:8081';
        const fullUrl = downloadUrl.startsWith('http') ? downloadUrl : `${baseUrl}${downloadUrl}`;
        const res = await fetch(fullUrl);
        if (!res.ok) throw new Error(`HTTP ${res.status} fetching PDF`);
        const arrayBuffer = await res.arrayBuffer();
        const loadingTask = pdfjsLib.getDocument({ data: new Uint8Array(arrayBuffer) });
        this.currentPdfDoc = await loadingTask.promise;
        this.currentPdfAttachmentId = attachmentId;
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

        // Position overlay if bounding box exists for this page
        if (bbox && (bbox.pageNumber === undefined || bbox.pageNumber === safePageNum)) {
          const x = bbox.x0 * baseScale;
          const y = bbox.y0 * baseScale;
          const w = (bbox.x1 - bbox.x0) * baseScale;
          const h = (bbox.y1 - bbox.y0) * baseScale;
          this.pdfHighlightBox = {
            x: Math.max(0, x),
            y: Math.max(0, y),
            w: Math.max(4, w),
            h: Math.max(4, h)
          };
          this.scrollPdfTargetIntoView();
        } else {
          this.pdfHighlightBox = null;
        }

        this.isRenderingPdf = false;
        this.cdr.markForCheck();
      }, 50);

    } catch (err) {
      console.warn('PDF.js rendering fallback to native iframe:', err);
      this.pdfRenderError = true;
      this.isRenderingPdf = false;
      this.cdr.markForCheck();
    }
  }

  prevPdfPage() {
    if (this.activePageNumber > 1 && this.activeAttachment) {
      const targetPage = this.activePageNumber - 1;
      const bbox = (this.activeEvidence?.pageNumber === targetPage) ? this.activeEvidence.boundingBox : undefined;
      this.loadAndRenderPdfPage(this.activeAttachment.id, targetPage, bbox);
    }
  }

  nextPdfPage() {
    if (this.activePageNumber < this.pdfTotalPages && this.activeAttachment) {
      const targetPage = this.activePageNumber + 1;
      const bbox = (this.activeEvidence?.pageNumber === targetPage) ? this.activeEvidence.boundingBox : undefined;
      this.loadAndRenderPdfPage(this.activeAttachment.id, targetPage, bbox);
    }
  }

  scrollPdfTargetIntoView() {
    setTimeout(() => {
      const el = document.getElementById('pdf-evidence-target');
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }, 80);
  }

  // Dynamic Adaptive Reviewer Sections Filter
  get visibleSections(): ReviewerSection[] {
    if (!this.brief || !this.brief.sections) return [];
    if (this.selectedCategoryTab === 'ALL') {
      return this.brief.sections.filter(s => s.visible);
    }
    return this.brief.sections.filter(s => {
      if (!s.visible) return false;
      if (!s.categoryScope || s.categoryScope === 'ALL') return true;
      return s.categoryScope === this.selectedCategoryTab;
    });
  }

  getRowSummary(row: TableRow): string {
    if (!row || !row.cells) return '';
    const vals = Object.values(row.cells);
    return vals.length > 0 ? String(vals[0]) : '';
  }

  // Generic Datum Evidence Inspection
  onViewEvidenceForDatum(
    evidence: EvidenceRef | undefined,
    fieldKey: string,
    fieldLabel: string,
    factValue: string
  ) {
    if (!evidence) return;
    this.deselectAllFacts();
    this.activeEvidence = {
      fieldKey: fieldKey || 'datum',
      fieldLabel: fieldLabel || 'Parameter',
      factValue: factValue || '',
      ...evidence
    };
    this.pdfHighlightBox = null;
    this.navigateViewerForEvidence(evidence);
    this.cdr.markForCheck();
  }

  // Evidence Inspection UX
  onViewEvidence(fact: ReviewerFact) {
    if (!fact || !fact.evidence) return;

    // 1. Maintain exclusive fact selection
    this.selectedFact = fact;
    if (this.brief) {
      for (const f of this.brief.facts) {
        f.isSelected = (f.field === fact.field);
      }
    }

    // 2. Set active evidence context
    this.activeEvidence = {
      fieldKey: fact.field,
      fieldLabel: fact.label,
      factValue: fact.value,
      ...fact.evidence
    };

    // 3. Clear previous highlight states
    this.pdfHighlightBox = null;

    // 4. Navigate viewer and highlight source
    this.navigateViewerForEvidence(fact.evidence);
    this.cdr.markForCheck();
  }

  openEvidenceForFact(fact: ReviewerFact) {
    this.onViewEvidence(fact);
  }

  openEvidenceForFocusItem(item: ReviewFocusItem) {
    this.deselectAllFacts();

    if (item.evidenceRef) {
      this.activeEvidence = {
        fieldKey: item.fieldAffected || 'focus_item',
        fieldLabel: item.headline,
        factValue: item.detail,
        ...item.evidenceRef
      };
    }

    if (item.category === 'PHOTO_DEFECT_INSPECTION') {
      // Support BOTH:
      // a. Standalone image attachment
      // b. Image embedded inside a PDF (do not require attachment itself to have .jpg/.png extension)
      const photoAtt = this.message?.attachments?.find(a => this.isImageAttachment(a));
      if (photoAtt) {
        this.selectAttachmentTab(photoAtt);
      } else {
        const targetPdf = (item.evidenceRef ? this.findMatchingAttachment(item.evidenceRef) : undefined)
          || this.message?.attachments?.find(a => this.isPdfAttachment(a));
        if (targetPdf) {
          const targetPage = item.evidenceRef?.pageNumber || 2;
          this.selectAttachmentTab(targetPdf, targetPage);
        }
      }
    } else if (item.evidenceRef) {
      this.navigateViewerForEvidence(item.evidenceRef);
    }
  }

  openEvidenceForMi(mi: any) {
    if (!mi || !mi.evidence) return;
    this.deselectAllFacts();
    this.activeEvidence = {
      fieldKey: 'mi_inquiry',
      fieldLabel: 'Medical Information Inquiry',
      factValue: mi.inquirySummary || mi.productName,
      ...mi.evidence
    };
    this.navigateViewerForEvidence(mi.evidence);
  }

  openEvidenceForPqc(pqc: any) {
    if (!pqc || !pqc.evidence) return;
    this.deselectAllFacts();
    this.activeEvidence = {
      fieldKey: 'pqc_defect',
      fieldLabel: 'Product Quality Defect',
      factValue: pqc.defectDescription || pqc.defectType,
      ...pqc.evidence
    };
    this.navigateViewerForEvidence(pqc.evidence);
  }

  closeEvidence() {
    this.activeEvidence = undefined;
    this.selectedFact = undefined;
    this.pdfHighlightBox = null;
    this.deselectAllFacts();
    this.resetEmailHighlight();
    this.cdr.markForCheck();
  }

  private deselectAllFacts() {
    this.selectedFact = undefined;
    if (this.brief) {
      for (const f of this.brief.facts) {
        f.isSelected = false;
      }
    }
  }

  // Source-First Routing strictly by identity
  private navigateViewerForEvidence(evidence: EvidenceRef) {
    const st = (evidence.sourceType || '').toLowerCase();
    const sId = (evidence.sourceId || evidence.sourceName || '').toLowerCase();

    // Check if matching attachment by filename
    const attMatch = this.findMatchingAttachment(evidence);

    // 1. Authoritative routing by sourceType: IMAGE / PHOTO
    if (st.includes('image') || st.includes('photo')) {
      // Image citations must NEVER be routed to email even if sourceId contains 'email'
      if (attMatch) {
        if (this.isImageAttachment(attMatch)) {
          this.selectAttachmentTab(attMatch);
        } else if (this.isPdfAttachment(attMatch)) {
          this.selectAttachmentTab(attMatch, evidence.pageNumber || 1);
        }
      } else {
        const pdfBySourceId = this.message?.attachments?.find(a =>
          this.isPdfAttachment(a) && (a.filename.toLowerCase() === sId || sId.includes(a.filename.toLowerCase()) || a.filename.toLowerCase().includes(sId))
        );
        const firstImg = this.message?.attachments?.find(a => this.isImageAttachment(a));
        const firstPdf = this.message?.attachments?.find(a => this.isPdfAttachment(a));

        if (pdfBySourceId) {
          this.selectAttachmentTab(pdfBySourceId, evidence.pageNumber || 1);
        } else if (firstImg) {
          this.selectAttachmentTab(firstImg);
        } else if (firstPdf) {
          this.selectAttachmentTab(firstPdf, evidence.pageNumber || 1);
        }
      }
      return;
    }

    // 2. Authoritative routing by sourceType: PDF
    if (st.includes('pdf')) {
      if (attMatch && this.isPdfAttachment(attMatch)) {
        this.selectAttachmentTab(attMatch, evidence.pageNumber);
      } else {
        const firstPdf = this.message?.attachments?.find(a => this.isPdfAttachment(a));
        if (firstPdf) {
          this.selectAttachmentTab(firstPdf, evidence.pageNumber);
        } else {
          this.selectEmailTab();
          this.applyEmailHighlight(evidence);
        }
      }
      return;
    }

    // 3. Authoritative routing by sourceType: EMAIL
    if (st.includes('email')) {
      this.selectEmailTab();
      this.applyEmailHighlight(evidence);
      return;
    }

    // 4. Fallback when sourceType is ambiguous / unstated
    if (attMatch) {
      if (this.isImageAttachment(attMatch)) {
        this.selectAttachmentTab(attMatch);
      } else if (this.isPdfAttachment(attMatch)) {
        this.selectAttachmentTab(attMatch, evidence.pageNumber);
      }
    } else if (sId.endsWith('.pdf')) {
      const firstPdf = this.message?.attachments?.find(a => this.isPdfAttachment(a));
      if (firstPdf) {
        this.selectAttachmentTab(firstPdf, evidence.pageNumber);
      } else {
        this.selectEmailTab();
        this.applyEmailHighlight(evidence);
      }
    } else if (sId.includes('email')) {
      this.selectEmailTab();
      this.applyEmailHighlight(evidence);
    } else {
      const firstPdf = this.message?.attachments?.find(a => this.isPdfAttachment(a));
      if (firstPdf && evidence.pageNumber) {
        this.selectAttachmentTab(firstPdf, evidence.pageNumber);
      } else {
        this.selectEmailTab();
        this.applyEmailHighlight(evidence);
      }
    }
  }

  private findMatchingAttachment(evidence: EvidenceRef): Attachment | undefined {
    if (!this.message?.attachments || this.message.attachments.length === 0) return undefined;
    const atts = this.message.attachments;

    const searchName = (evidence.sourceName || evidence.sourceId || '').toLowerCase();
    if (searchName && searchName !== 'email' && searchName !== 'default') {
      const match = atts.find(a => {
        const fn = a.filename.toLowerCase();
        return fn === searchName || fn.includes(searchName) || searchName.includes(fn);
      });
      if (match) return match;
    }
    return undefined;
  }

  // Safe 5-Tier Non-Ambiguous Email Anchoring Hierarchy
  private applyEmailHighlight(evidence: EvidenceRef) {
    const raw = this.message?.rawBody || '';
    if (!raw) {
      this.emailSegments = [];
      this.emailHighlightStatus = 'NONE';
      return;
    }

    const snippet = (evidence.snippet || '').trim();
    if (!snippet || this.isNotStatedSnippet(snippet)) {
      this.emailSegments = [{ text: raw, isHighlighted: false }];
      this.emailHighlightStatus = 'NONE';
      return;
    }

    // Tier a: Valid char_start / char_end
    if (
      typeof evidence.charStart === 'number' &&
      typeof evidence.charEnd === 'number' &&
      evidence.charStart >= 0 &&
      evidence.charEnd > evidence.charStart &&
      evidence.charEnd <= raw.length
    ) {
      const candidate = raw.substring(evidence.charStart, evidence.charEnd);
      const normCand = candidate.replace(/\s+/g, ' ').toLowerCase();
      const normSnip = snippet.replace(/\s+/g, ' ').toLowerCase();
      if (
        normCand.includes(normSnip.substring(0, Math.min(15, normSnip.length))) ||
        normSnip.includes(normCand.substring(0, Math.min(15, normCand.length)))
      ) {
        this.sliceEmailSegments(raw, evidence.charStart, evidence.charEnd);
        this.emailHighlightStatus = 'EXACT';
        this.scrollEmailTargetIntoView();
        return;
      }
    }

    // Tier b: Exact snippet match (case-insensitive)
    const lowerRaw = raw.toLowerCase();
    const lowerSnippet = snippet.toLowerCase();
    const firstIdx = lowerRaw.indexOf(lowerSnippet);

    if (firstIdx !== -1) {
      const lastIdx = lowerRaw.lastIndexOf(lowerSnippet);
      if (firstIdx === lastIdx) {
        // Unique exact match
        this.sliceEmailSegments(raw, firstIdx, firstIdx + snippet.length);
        this.emailHighlightStatus = 'EXACT';
        this.scrollEmailTargetIntoView();
        return;
      } else {
        // Ambiguous: occurs multiple times without unique coordinates!
        // Strict requirement: Never highlight an arbitrary occurrence.
        this.emailSegments = [{ text: raw, isHighlighted: false }];
        this.emailHighlightStatus = 'MULTIPLE_OCCURRENCES';
        return;
      }
    }

    // Tier c: Whitespace-normalized snippet match
    const normMatch = this.findUniqueNormalizedMatch(raw, snippet);
    if (normMatch.status === 'EXACT') {
      this.sliceEmailSegments(raw, normMatch.start, normMatch.end);
      this.emailHighlightStatus = 'EXACT';
      this.scrollEmailTargetIntoView();
      return;
    } else if (normMatch.status === 'MULTIPLE_OCCURRENCES') {
      this.emailSegments = [{ text: raw, isHighlighted: false }];
      this.emailHighlightStatus = 'MULTIPLE_OCCURRENCES';
      return;
    }

    // Tier d: Uniquely identifiable sentence/clause match
    const clauseMatch = this.findUniqueClauseMatch(raw, snippet);
    if (clauseMatch.status === 'EXACT') {
      this.sliceEmailSegments(raw, clauseMatch.start, clauseMatch.end);
      this.emailHighlightStatus = 'EXACT';
      this.scrollEmailTargetIntoView();
      return;
    } else if (clauseMatch.status === 'MULTIPLE_OCCURRENCES') {
      this.emailSegments = [{ text: raw, isHighlighted: false }];
      this.emailHighlightStatus = 'MULTIPLE_OCCURRENCES';
      return;
    }

    // Tier e: If still ambiguous or not found: NO arbitrary highlight
    this.emailSegments = [{ text: raw, isHighlighted: false }];
    this.emailHighlightStatus = 'NOT_FOUND';
  }

  private sliceEmailSegments(raw: string, start: number, end: number) {
    const before = raw.substring(0, start);
    const match = raw.substring(start, end);
    const after = raw.substring(end);
    this.emailSegments = [
      { text: before, isHighlighted: false },
      { text: match, isHighlighted: true },
      { text: after, isHighlighted: false }
    ];
  }

  private findUniqueNormalizedMatch(raw: string, snippet: string): { status: 'EXACT' | 'MULTIPLE_OCCURRENCES' | 'NOT_FOUND'; start: number; end: number } {
    const normSnippet = snippet.replace(/\s+/g, ' ').trim().toLowerCase();
    if (normSnippet.length < 10) return { status: 'NOT_FOUND', start: 0, end: 0 };

    let normRaw = '';
    const indexMap: number[] = [];
    let inWs = false;

    for (let i = 0; i < raw.length; i++) {
      const ch = raw[i];
      if (/\s/.test(ch)) {
        if (!inWs) {
          normRaw += ' ';
          indexMap.push(i);
          inWs = true;
        }
      } else {
        normRaw += ch.toLowerCase();
        indexMap.push(i);
        inWs = false;
      }
    }

    const first = normRaw.indexOf(normSnippet);
    if (first === -1) return { status: 'NOT_FOUND', start: 0, end: 0 };

    const last = normRaw.lastIndexOf(normSnippet);
    if (first !== last) {
      return { status: 'MULTIPLE_OCCURRENCES', start: 0, end: 0 };
    }

    const rawStart = indexMap[first];
    const rawEnd = indexMap[first + normSnippet.length - 1] + 1;
    return { status: 'EXACT', start: rawStart, end: rawEnd };
  }

  private findUniqueClauseMatch(raw: string, snippet: string): { status: 'EXACT' | 'MULTIPLE_OCCURRENCES' | 'NOT_FOUND'; start: number; end: number } {
    const clauses = snippet.split(/[.;\n]+/)
      .map(c => c.trim())
      .filter(c => c.length >= 20);

    if (clauses.length === 0) return { status: 'NOT_FOUND', start: 0, end: 0 };

    const lowerRaw = raw.toLowerCase();
    let bestMatch: { start: number; end: number } | null = null;
    let foundAmbiguous = false;

    for (const clause of clauses) {
      const lc = clause.toLowerCase();
      const first = lowerRaw.indexOf(lc);
      if (first !== -1) {
        const last = lowerRaw.lastIndexOf(lc);
        if (first === last) {
          if (!bestMatch) {
            bestMatch = { start: first, end: first + clause.length };
          }
        } else {
          foundAmbiguous = true;
        }
      }
    }

    if (bestMatch) {
      return { status: 'EXACT', start: bestMatch.start, end: bestMatch.end };
    }
    if (foundAmbiguous) {
      return { status: 'MULTIPLE_OCCURRENCES', start: 0, end: 0 };
    }
    return { status: 'NOT_FOUND', start: 0, end: 0 };
  }

  private scrollEmailTargetIntoView() {
    setTimeout(() => {
      const el = document.getElementById('email-evidence-target');
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }, 60);
  }

  private resetEmailHighlight() {
    const raw = this.message?.rawBody || '';
    this.emailSegments = raw ? [{ text: raw, isHighlighted: false }] : [];
    this.emailHighlightStatus = 'NONE';
  }

  private isNotStatedSnippet(snippet: string): boolean {
    const s = snippet.toLowerCase();
    return s === 'not stated' || s === 'document grounding verified.' || s === 'verified against document source.';
  }

  isTechnicalBoilerplate(text?: string): boolean {
    if (!text) return true;
    const lower = text.toLowerCase();
    return lower.includes('deterministic') || lower.includes('intra-document') || lower.includes('grounding verified');
  }

  // Source Type Labeling (Mandatory strict format)
  formatSourceBadge(evidence?: EvidenceRef): string {
    if (!evidence) return 'Source Document';
    const st = (evidence.sourceType || '').toLowerCase();
    const loc = (evidence.location || '').toLowerCase();

    if (st.includes('email') || loc.includes('email')) {
      return 'Email body'; // Strictly NO page number for email!
    }
    if (st.includes('image') || loc.includes('photo') || loc.includes('image')) {
      const filename = evidence.sourceName || this.activeAttachment?.filename || 'Exhibit Image';
      const pageStr = (evidence.pageNumber && filename.toLowerCase().endsWith('.pdf')) ? ` · Page ${evidence.pageNumber}` : '';
      return `Image · ${filename}${pageStr}`;
    }
    // PDF
    const filename = evidence.sourceName || this.activeAttachment?.filename || 'Document.pdf';
    const pageStr = evidence.pageNumber ? ` · Page ${evidence.pageNumber}` : '';
    return `PDF · ${filename}${pageStr}`;
  }

  formatAnchorLevelBadge(level?: string): string {
    switch (level) {
      case 'LEVEL_1_EXACT_VISUAL':
        return 'Level 1 · Exact Visual Anchor';
      case 'LEVEL_2_PAGE_TEXT':
        return 'Level 2 · Page & Text Anchored';
      case 'LEVEL_3_SNIPPET_ONLY':
      default:
        return 'Level 3 · Source Snippet Only';
    }
  }

  // Category Filtering
  setCategoryTab(tab: 'ALL' | 'ICSR' | 'PQC' | 'MI') {
    this.selectedCategoryTab = tab;
  }

  // Fact Status Filtering
  setStatusFilter(filter: 'ALL' | 'ATTENTION' | 'CONFIRMED' | 'NOT_STATED') {
    this.selectedFactStatusFilter = filter;
  }

  get filteredFacts(): ReviewerFact[] {
    if (!this.brief) return [];
    return this.brief.facts.filter(f => {
      // Category filter
      if (this.selectedCategoryTab === 'ICSR') {
        if (!['PATIENT', 'REPORTER', 'PRODUCT', 'EVENT'].includes(f.section)) return false;
      } else if (this.selectedCategoryTab === 'PQC') {
        if (f.section !== 'PQC') return false;
      } else if (this.selectedCategoryTab === 'MI') {
        if (f.section !== 'MI') return false;
      }

      // Status filter
      if (this.selectedFactStatusFilter === 'ATTENTION') {
        return f.status === 'UNCERTAIN' || f.status === 'CONFLICT';
      } else if (this.selectedFactStatusFilter === 'CONFIRMED') {
        return f.status === 'CONFIRMED';
      } else if (this.selectedFactStatusFilter === 'NOT_STATED') {
        return f.status === 'NOT_STATED';
      }

      return true;
    });
  }

  // Human Review Actions
  onAcceptAiResult() {
    if (!this.message) return;
    this.isSubmittingAction = true;
    this.messageService.acceptMessage(this.message.id, {
      reviewerUsername: 'safety.reviewer@clinevo.com',
      comments: 'Safety reviewer verified case brief, atomic fact ledger, and evidence grounding.'
    }).subscribe({
      next: (updated) => {
        this.message = updated;
        if (this.brief) {
          this.brief.validationGating = 'READY_FOR_REVIEW';
        }
        this.isSubmittingAction = false;
        this.actionSuccessMessage = 'Case successfully confirmed by reviewer and marked as REVIEWED.';
        this.loadAuditTrail(this.message.id);
        this.cdr.markForCheck();
        setTimeout(() => {
          this.actionSuccessMessage = '';
          this.cdr.markForCheck();
        }, 5000);
      },
      error: (err) => {
        this.isSubmittingAction = false;
        this.cdr.markForCheck();
        alert(`Failed to accept case: ${err.message}`);
      }
    });
  }

  onFlagCase() {
    this.isFlaggedForEscalation = !this.isFlaggedForEscalation;
    if (this.isFlaggedForEscalation) {
      this.actionSuccessMessage = 'Case flagged for senior medical officer escalation.';
      setTimeout(() => {
        this.actionSuccessMessage = '';
        this.cdr.markForCheck();
      }, 4000);
    }
  }

  onStartOverride() {
    this.isEditing = true;
    this.overrideJustification = '';
    this.cdr.markForCheck();
  }

  onCancelOverride() {
    this.isEditing = false;
    this.initializeFieldEdits();
    this.cdr.markForCheck();
  }

  onSubmitOverride() {
    if (!this.message) return;
    if (!this.overrideJustification.trim()) {
      alert('A clinical justification is strictly required to record an override in the audit trail.');
      return;
    }

    this.isSubmittingAction = true;
    this.cdr.markForCheck();
    this.messageService.overrideMessage(this.message.id, {
      reviewerUsername: 'safety.reviewer@clinevo.com',
      newCategory: this.overrideCategory !== this.message.primaryCategory ? this.overrideCategory : undefined,
      justification: this.overrideJustification,
      fieldEdits: this.overrideFieldEdits
    }).subscribe({
      next: (updated) => {
        this.message = updated;
        this.brief = ReviewerBriefBuilder.buildFromMessage(updated);
        this.isEditing = false;
        this.isSubmittingAction = false;
        this.actionSuccessMessage = 'Reviewer corrections committed and logged to audit history.';
        this.loadAuditTrail(this.message.id);
        this.cdr.markForCheck();
        setTimeout(() => {
          this.actionSuccessMessage = '';
          this.cdr.markForCheck();
        }, 5000);
      },
      error: (err) => {
        this.isSubmittingAction = false;
        this.cdr.markForCheck();
        alert(`Failed to commit override: ${err.message}`);
      }
    });
  }

  // Format Helpers
  formatCaseId(item?: any): string {
    if (this.message) return resolveCaseId(this.message);
    if (item && typeof item === 'object') return resolveCaseId(item);
    return resolveCaseId({ id: typeof item === 'number' ? item : undefined });
  }

  isNotStated(val?: string): boolean {
    if (!val) return true;
    const clean = val.trim().toLowerCase();
    return clean === 'not stated' || clean === 'null' || clean === 'n/a' || clean === '-';
  }
}
