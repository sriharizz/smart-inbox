import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';
import { MessageService } from '../../core/services/message.service';
import { AuditService } from '../../core/services/audit.service';
import { IntakeMessage, Attachment, SourceCitation } from '../../core/models/message.model';
import { AuditEvent } from '../../core/models/audit.model';

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

  messageId!: number;
  message?: IntakeMessage;
  auditEvents: AuditEvent[] = [];
  isLoading = true;
  errorMessage = '';

  // Left Source Panel State
  activeTab: 'EMAIL' | number = 'EMAIL'; // 'EMAIL' or attachment ID
  activeAttachment?: Attachment;
  safeAttachmentUrl?: SafeResourceUrl;
  zoomLevel = 100;

  // Active Source Citation Inspection
  activeCitation?: {
    fieldKey: string;
    fieldLabel: string;
    sourceType?: string;
    location?: string;
    snippet?: string;
  };

  // Human Review & Override State
  isEditing = false;
  overrideCategory = '';
  overrideJustification = '';
  overrideFieldEdits: Record<string, string> = {};
  isSubmittingAction = false;
  actionSuccessMessage = '';

  // Collapsible Panels
  showAuditTrail = true;
  showExecutiveSummary = true;

  // Parsed Citations
  citations: Record<string, SourceCitation> = {};

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
        
        // Parse citations if available
        if (data.icsrReport?.sourceCitationsJson) {
          this.citations = this.messageService.parseCitations(data.icsrReport.sourceCitationsJson);
        } else if (data.pqcReport?.sourceCitationsJson) {
          this.citations = this.messageService.parseCitations(data.pqcReport.sourceCitationsJson);
        }

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
      },
      error: (err) => {
        this.errorMessage = `Failed to load case details: ${err.message || 'Server error'}`;
        this.isLoading = false;
      }
    });
  }

  loadAuditTrail(id: number) {
    this.auditService.getAuditEvents(id).subscribe({
      next: (events) => {
        this.auditEvents = events;
      },
      error: () => {}
    });
  }

  initializeFieldEdits() {
    if (!this.message?.icsrReport) return;
    const r = this.message.icsrReport;
    this.overrideFieldEdits = {
      patientAge: r.patientAge || 'Not stated',
      patientSex: r.patientSex || 'Not stated',
      patientWeight: r.patientWeight || 'Not stated',
      reporterName: r.reporterName || 'Not stated',
      productName: r.productName || 'Not stated',
      productDose: r.productDose || 'Not stated',
      productLot: r.productLot || 'Not stated',
      adverseEvent: r.adverseEvent || 'Not stated'
    };
  }

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

  // Citation Traceability UX
  inspectCitation(fieldKey: string, fieldLabel: string) {
    const cit = this.citations[fieldKey];
    if (!cit) return;

    this.activeCitation = {
      fieldKey,
      fieldLabel,
      sourceType: cit.source_type,
      location: cit.page_or_location,
      snippet: cit.verbatim_snippet
    };

    // Auto-navigate left viewer to the matching attachment or email
    if (cit.source_type === 'email_body' || (cit.source_type && cit.source_type.includes('email'))) {
      this.selectEmailTab();
    } else if (this.message?.attachments && this.message.attachments.length > 0) {
      // Find PDF or photo attachment
      const targetAtt = this.message.attachments.find(a => 
        (cit.page_or_location && cit.page_or_location.toLowerCase().includes('pdf') && this.isPdfAttachment(a)) ||
        (cit.source_type && cit.source_type.includes('photo') && this.isImageAttachment(a))
      ) || this.message.attachments[0];
      
      this.selectAttachmentTab(targetAtt);
    }
  }

  clearCitation() {
    this.activeCitation = undefined;
  }

  // Human Review Actions
  onAcceptAiResult() {
    if (!this.message) return;
    this.isSubmittingAction = true;
    this.messageService.acceptMessage(this.message.id, {
      reviewerUsername: 'safety.reviewer@clinevo.com',
      comments: 'Safety reviewer confirmed automated triage and extracted ICH E2B parameters.'
    }).subscribe({
      next: (updated) => {
        this.message = updated;
        this.isSubmittingAction = false;
        this.actionSuccessMessage = 'Case successfully accepted and marked as REVIEWED.';
        this.loadAuditTrail(this.message.id);
        setTimeout(() => this.actionSuccessMessage = '', 4000);
      },
      error: (err) => {
        this.isSubmittingAction = false;
        alert(`Failed to accept case: ${err.message}`);
      }
    });
  }

  onStartOverride() {
    this.isEditing = true;
    this.overrideJustification = '';
  }

  onCancelOverride() {
    this.isEditing = false;
    this.initializeFieldEdits();
  }

  onSubmitOverride() {
    if (!this.message) return;
    if (!this.overrideJustification.trim()) {
      alert('A clinical justification is strictly required to record an override in the audit trail.');
      return;
    }

    this.isSubmittingAction = true;
    this.messageService.overrideMessage(this.message.id, {
      reviewerUsername: 'safety.reviewer@clinevo.com',
      newCategory: this.overrideCategory !== this.message.primaryCategory ? this.overrideCategory : undefined,
      justification: this.overrideJustification,
      fieldEdits: this.overrideFieldEdits
    }).subscribe({
      next: (updated) => {
        this.message = updated;
        this.isEditing = false;
        this.isSubmittingAction = false;
        this.actionSuccessMessage = 'Reviewer override committed and logged to immutable audit trail.';
        this.loadAuditTrail(this.message.id);
        setTimeout(() => this.actionSuccessMessage = '', 4000);
      },
      error: (err) => {
        this.isSubmittingAction = false;
        alert(`Failed to commit override: ${err.message}`);
      }
    });
  }

  formatCaseId(id: number): string {
    return `CASE-${id.toString().padStart(3, '0')}`;
  }

  isNotStated(val?: string): boolean {
    if (!val) return true;
    const clean = val.trim().toLowerCase();
    return clean === 'not stated' || clean === 'null' || clean === 'n/a' || clean === '-';
  }
}
