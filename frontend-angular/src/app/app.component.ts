import { Component, inject, OnInit, ChangeDetectorRef } from '@angular/core';
import { RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';
import { CommonModule } from '@angular/common';
import { MessageService } from './core/services/message.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive, CommonModule],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent implements OnInit {
  private messageService = inject(MessageService);
  private cdr = inject(ChangeDetectorRef);

  pendingCount = 0;
  isIngesting = false;
  ingestNotification = '';

  ngOnInit() {
    this.refreshCounts();
  }

  refreshCounts() {
    this.messageService.getMessages().subscribe({
      next: (messages) => {
        this.pendingCount = messages.filter(m => m.status === 'RECEIVED' || m.status === 'TRIAGED').length;
        this.cdr.markForCheck();
      },
      error: () => {}
    });
  }

  onTriggerIngest() {
    this.isIngesting = true;
    this.ingestNotification = 'Ingesting synthetic email fixtures...';
    this.cdr.markForCheck();
    this.messageService.triggerIngest().subscribe({
      next: (res) => {
        this.isIngesting = false;
        this.ingestNotification = `Ingested ${res.newMessagesIngested} messages successfully.`;
        this.refreshCounts();
        this.cdr.markForCheck();
        setTimeout(() => {
          this.ingestNotification = '';
          this.cdr.markForCheck();
        }, 4000);
      },
      error: (err) => {
        this.isIngesting = false;
        this.ingestNotification = `Ingestion error: ${err.message || 'Check backend'}`;
        this.cdr.markForCheck();
        setTimeout(() => {
          this.ingestNotification = '';
          this.cdr.markForCheck();
        }, 4000);
      }
    });
  }
}
