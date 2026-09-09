import { Component, inject, OnInit, OnDestroy, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { MessageService } from '../../core/services/message.service';
import { MessageSummary } from '../../core/models/message.model';
import { resolveCaseId } from '../../core/utils/case-id.util';

@Component({
  selector: 'app-review-queue',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './review-queue.component.html',
  styleUrls: ['./review-queue.component.scss']
})
export class ReviewQueueComponent implements OnInit, OnDestroy {
  private messageService = inject(MessageService);
  private router = inject(Router);
  private cdr = inject(ChangeDetectorRef);

  messages: MessageSummary[] = [];
  filteredMessages: MessageSummary[] = [];
  isLoading = true;
  errorMessage = '';
  private pollInterval?: any;

  // Filter State
  selectedCategory = 'ALL';
  selectedStatus = 'ALL';
  filterFlag: 'ALL' | 'CRITICAL' | 'LOW_CONFIDENCE' | 'PHOTO_REVIEW' = 'ALL';
  searchQuery = '';

  // Configurable review threshold (displayed in tooltip/hint)
  get confidenceThreshold(): number {
    return this.messageService.confidenceReviewThreshold;
  }

  ngOnInit() {
    this.loadQueue();
    this.pollInterval = setInterval(() => {
      this.refreshSilently();
    }, 10000);
  }

  ngOnDestroy() {
    if (this.pollInterval) {
      clearInterval(this.pollInterval);
    }
  }

  refreshSilently() {
    this.messageService.getMessages().subscribe({
      next: (data) => {
        if (data && (data.length !== this.messages.length || data.some((m, idx) => m.status !== this.messages[idx]?.status))) {
          this.messages = data;
          this.applyFilters();
          this.cdr.markForCheck();
        }
      },
      error: () => {}
    });
  }

  loadQueue() {
    this.isLoading = true;
    this.errorMessage = '';
    this.cdr.markForCheck();
    this.messageService.getMessages().subscribe({
      next: (data) => {
        this.messages = data;
        this.applyFilters();
        this.isLoading = false;
        this.cdr.markForCheck();
      },
      error: (err) => {
        this.errorMessage = 'Unable to connect to Spring Boot backend. Please verify backend service.';
        this.isLoading = false;
        this.cdr.markForCheck();
      }
    });
  }

  applyFilters() {
    let result = [...this.messages];

    // Category filter
    if (this.selectedCategory !== 'ALL') {
      result = result.filter(m => {
        const cat = m.primaryCategory.toUpperCase();
        if (this.selectedCategory === 'ICSR') return cat.includes('ICSR') || cat.includes('SAFETY');
        if (this.selectedCategory === 'PQC') return cat.includes('PQC') || cat.includes('QUALITY');
        if (this.selectedCategory === 'MI') return cat.includes('MI') || cat.includes('MEDICAL');
        if (this.selectedCategory === 'NOT_RELEVANT') return cat.includes('NOT RELEVANT') || cat.includes('IRRELEVANT');
        return true;
      });
    }

    // Status filter
    if (this.selectedStatus !== 'ALL') {
      result = result.filter(m => {
        if (this.selectedStatus === 'NEEDS_REVIEW') {
          return m.status === 'RECEIVED' || m.status === 'TRIAGED';
        }
        return m.status === this.selectedStatus;
      });
    }

    // Special Flag Filter
    if (this.filterFlag === 'CRITICAL') {
      result = result.filter(m => m.priority === 'CRITICAL');
    } else if (this.filterFlag === 'LOW_CONFIDENCE') {
      result = result.filter(m => m.flags?.lowConfidence);
    } else if (this.filterFlag === 'PHOTO_REVIEW') {
      result = result.filter(m => m.flags?.imageReviewRequired);
    }

    // Search query filter
    if (this.searchQuery.trim()) {
      const q = this.searchQuery.toLowerCase().trim();
      result = result.filter(m => 
        m.sender.toLowerCase().includes(q) ||
        m.senderEmail.toLowerCase().includes(q) ||
        m.subject.toLowerCase().includes(q) ||
        this.formatCaseId(m).toLowerCase().includes(q) ||
        (m.executiveSummary && m.executiveSummary.toLowerCase().includes(q))
      );
    }

    this.filteredMessages = result;
  }

  setCategoryFilter(cat: string) {
    this.selectedCategory = cat;
    this.applyFilters();
  }

  setStatusFilter(status: string) {
    this.selectedStatus = status;
    this.applyFilters();
  }

  setFlagFilter(flag: 'ALL' | 'CRITICAL' | 'LOW_CONFIDENCE' | 'PHOTO_REVIEW') {
    this.filterFlag = flag;
    this.applyFilters();
  }

  openCase(id: number) {
    this.router.navigate(['/cases', id]);
  }

  formatCaseId(item: any): string {
    return resolveCaseId(item);
  }

  formatConfidence(conf: number): string {
    if (!conf || conf <= 0) return 'Pending';
    const pct = Math.round(conf * 100);
    return `${pct >= 100 ? 98 : pct}%`;
  }

  getStatusBadgeClass(status: string): string {
    switch (status) {
      case 'REVIEWED': return 'badge-confirm';
      case 'OVERRIDDEN': return 'badge-brand';
      case 'RECEIVED':
      case 'TRIAGED': return 'badge-attention';
      default: return 'badge-neutral';
    }
  }

  getStatusLabel(status: string): string {
    switch (status) {
      case 'REVIEWED': return 'Reviewed';
      case 'OVERRIDDEN': return 'Overridden';
      case 'RECEIVED':
      case 'TRIAGED': return 'Needs Review';
      default: return status;
    }
  }
}
