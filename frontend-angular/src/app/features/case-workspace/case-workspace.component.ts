import { Component, inject, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';
import { MessageService } from '../../core/services/message.service';
import { AuditService } from '../../core/services/audit.service';
import { IntakeMessage, Attachment, SourceCitation } from '../../core/models/message.model';
import { AuditEvent } from '../../core/models/audit.model';
import {
  ReviewerBrief,
  ReviewerFact,
  ReviewFocusItem,
  FactStatus,
  EvidenceRef
} from '../../core/models/reviewer-brief.model';
import { ReviewerBriefBuilder } from '../../core/services/reviewer-brief-builder';

interface ActiveEvidenceContext extends EvidenceRef {
  fieldKey: string;
  fieldLabel: string;
  factValue: string;
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

  // Active Evidence Inspection Drawer
  activeEvidence?: ActiveEvidenceContext;

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
  }

  selectAttachmentTab(att: Attachment) {
    this.activeTab = att.id;
    this.activeAttachment = att;
    const rawUrl = this.messageService.getAttachmentDownloadUrl(att.id);
    this.safeAttachmentUrl = this.sanitizer.bypassSecurityTrustResourceUrl(rawUrl);
    this.zoomLevel = 100;
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
    if (this.zoomLevel < 180) this.zoomLevel += 15;
  }

  zoomOut() {
    if (this.zoomLevel > 60) this.zoomLevel -= 15;
  }

  resetZoom() {
    this.zoomLevel = 100;
  }

  // Evidence Inspection UX
  openEvidenceForFact(fact: ReviewerFact) {
    if (!fact.evidence) return;
    this.activeEvidence = {
      fieldKey: fact.field,
      fieldLabel: fact.label,
      factValue: fact.value,
      ...fact.evidence
    };

    // Auto-navigate left viewer to relevant attachment or email
    this.navigateViewerForEvidence(fact.evidence);
  }

  openEvidenceForFocusItem(item: ReviewFocusItem) {
    if (item.category === 'PHOTO_DEFECT_INSPECTION') {
      // Find photo attachment
      const photoAtt = this.message?.attachments?.find(a => this.isImageAttachment(a));
      if (photoAtt) {
        this.selectAttachmentTab(photoAtt);
      }
    }

    if (item.evidenceRef) {
      this.activeEvidence = {
        fieldKey: item.fieldAffected || 'focus_item',
        fieldLabel: item.headline,
        factValue: item.detail,
        ...item.evidenceRef
      };
      this.navigateViewerForEvidence(item.evidenceRef);
    }
  }

  closeEvidence() {
    this.activeEvidence = undefined;
  }

  private navigateViewerForEvidence(evidence: EvidenceRef) {
    const loc = (evidence.location || '').toLowerCase();
    const type = (evidence.sourceType || '').toLowerCase();

    if (type.includes('email') || loc.includes('email')) {
      this.selectEmailTab();
    } else if (this.message?.attachments && this.message.attachments.length > 0) {
      const pdfAtt = this.message.attachments.find(a => this.isPdfAttachment(a));
      const imgAtt = this.message.attachments.find(a => this.isImageAttachment(a));

      if (loc.includes('photo') || type.includes('photo') || type.includes('image')) {
        if (imgAtt) this.selectAttachmentTab(imgAtt);
      } else if (pdfAtt) {
        this.selectAttachmentTab(pdfAtt);
      }
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
        this.actionSuccessMessage = 'Reviewer corrections committed and logged to immutable audit trail.';
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
  formatCaseId(id: number): string {
    return `CASE-${id.toString().padStart(3, '0')}`;
  }

  isNotStated(val?: string): boolean {
    if (!val) return true;
    const clean = val.trim().toLowerCase();
    return clean === 'not stated' || clean === 'null' || clean === 'n/a' || clean === '-';
  }
}
