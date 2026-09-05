import { Routes } from '@angular/router';
import { ReviewQueueComponent } from './features/review-queue/review-queue.component';
import { CaseWorkspaceComponent } from './features/case-workspace/case-workspace.component';
import { LiteratureScreeningComponent } from './features/literature-screening/literature-screening.component';
import { AuditTrailComponent } from './features/audit-trail/audit-trail.component';

export const routes: Routes = [
  { path: '', redirectTo: 'queue', pathMatch: 'full' },
  { path: 'queue', component: ReviewQueueComponent },
  { path: 'cases/:id', component: CaseWorkspaceComponent },
  { path: 'literature', component: LiteratureScreeningComponent },
  { path: 'audit', component: AuditTrailComponent },
  { path: '**', redirectTo: 'queue' }
];
