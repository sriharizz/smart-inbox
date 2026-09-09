import { Component, inject, OnInit, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { AuditService } from '../../core/services/audit.service';
import { AuditEvent } from '../../core/models/audit.model';
import { resolveCaseId } from '../../core/utils/case-id.util';

@Component({
  selector: 'app-audit-trail',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './audit-trail.component.html',
  styleUrls: ['./audit-trail.component.scss']
})
export class AuditTrailComponent implements OnInit {
  private auditService = inject(AuditService);
  private cdr = inject(ChangeDetectorRef);

  events: AuditEvent[] = [];
  filteredEvents: AuditEvent[] = [];
  isLoading = true;
  errorMessage = '';

  // Filter State
  selectedAction = 'ALL';
  searchQuery = '';

  ngOnInit() {
    this.loadAuditEvents();
  }

  loadAuditEvents() {
    this.isLoading = true;
    this.errorMessage = '';
    this.cdr.markForCheck();
    this.auditService.getAuditEvents().subscribe({
      next: (data) => {
        this.events = data;
        this.applyFilters();
        this.isLoading = false;
        this.cdr.markForCheck();
      },
      error: (err) => {
        this.errorMessage = `Failed to load audit events: ${err.message || 'Server error'}`;
        this.isLoading = false;
        this.cdr.markForCheck();
      }
    });
  }

  applyFilters() {
    let list = [...this.events];

    if (this.selectedAction !== 'ALL') {
      list = list.filter(e => e.action === this.selectedAction);
    }

    if (this.searchQuery.trim()) {
      const q = this.searchQuery.toLowerCase().trim();
      list = list.filter(e => {
        const rev = (e.reviewerUsername || e.reviewer || '').toLowerCase();
        const fld = (e.targetField || e.fieldChanged || '').toLowerCase();
        const oldV = (e.originalValue || e.oldValue || '').toLowerCase();
        const newV = (e.newValue || '').toLowerCase();
        const just = (e.reviewerComments || e.justification || '').toLowerCase();
        const act = (e.action || '').toLowerCase();
        const cid = e.messageId ? `case-${e.messageId}`.toLowerCase() : '';
        return act.includes(q) || rev.includes(q) || fld.includes(q) || oldV.includes(q) || newV.includes(q) || just.includes(q) || cid.includes(q);
      });
    }

    this.filteredEvents = list;
  }

  onActionFilterChange(action: string) {
    this.selectedAction = action;
    this.applyFilters();
  }

  formatCaseId(messageId: number): string {
    return resolveCaseId({ id: messageId });
  }

  getActionBadgeClass(action: string): string {
    switch (action) {
      case 'REVIEWER_CONFIRM':
      case 'ACCEPT': return 'badge-accept';
      case 'OVERRIDE_CATEGORY':
      case 'OVERRIDE_FIELD':
      case 'OVERRIDE': return 'badge-override';
      case 'INGESTION': return 'badge-ingest';
      case 'TRIAGE_COMPLETE': return 'badge-triage';
      default: return 'badge-neutral';
    }
  }

  getActionLabel(action: string): string {
    switch (action) {
      case 'REVIEWER_CONFIRM':
      case 'ACCEPT': return 'Confirmed by Reviewer';
      case 'OVERRIDE_CATEGORY': return 'Category Override';
      case 'OVERRIDE_FIELD': return 'Field Override';
      case 'OVERRIDE': return 'Reviewer Override';
      case 'INGESTION': return 'System Ingested';
      case 'TRIAGE_COMPLETE': return 'AI Triage Complete';
      default: return action;
    }
  }
}
