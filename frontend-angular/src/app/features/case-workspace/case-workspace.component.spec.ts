import { describe, it, expect, beforeEach, vi } from 'vitest';
import { getTestBed, ComponentFixture, TestBed } from '@angular/core/testing';
import { BrowserTestingModule, platformBrowserTesting } from '@angular/platform-browser/testing';
import { ActivatedRoute, Router } from '@angular/router';
import { of } from 'rxjs';
import { CaseWorkspaceComponent } from './case-workspace.component';
import { MessageService } from '../../core/services/message.service';
import { AuditService } from '../../core/services/audit.service';
import { IntakeMessage } from '../../core/models/message.model';

// Ensure Angular TestBed environment is initialized for Vitest runner
const ANGULAR_TESTBED_SETUP = Symbol.for('@angular/cli/testbed-setup');
if (!(globalThis as any)[ANGULAR_TESTBED_SETUP]) {
  (globalThis as any)[ANGULAR_TESTBED_SETUP] = true;
  getTestBed().initTestEnvironment(BrowserTestingModule, platformBrowserTesting());
}

describe('CaseWorkspaceComponent', () => {
  let component: CaseWorkspaceComponent;
  let fixture: ComponentFixture<CaseWorkspaceComponent>;

  const mockMessage: IntakeMessage = {
    id: 4,
    messageId: 'msg-004',
    sender: 'Nurse practitioner',
    senderEmail: 'nurse@clinic.org',
    subject: 'Contaminated infusion vial with septic shock',
    receivedDate: '2026-03-02 11:15:00',
    rawBody: 'Infusion vial had dark particles; patient developed septic shock.',
    status: 'TRIAGED',
    primaryCategory: 'Safety Report (ICSR) + Quality Complaint (PQC)',
    confidence: 0.94,
    isMultiLabel: true,
    createdAt: '2026-03-02T11:15:00Z',
    updatedAt: '2026-03-02T11:20:00Z',
    attachments: [
      { id: 401, filename: 'vial_photo.jpg', contentType: 'image/jpeg', sizeBytes: 520000 },
      { id: 402, filename: 'clinic_report.pdf', contentType: 'application/pdf', sizeBytes: 210000 }
    ],
    icsrReport: {
      patientIdentifier: 'M.K.',
      patientAge: '68 years',
      patientSex: 'FEMALE',
      patientWeight: '60 kg',
      patientHistory: 'Type 2 Diabetes',
      reporterName: 'Nurse Jackie',
      reporterRole: 'Nurse',
      reporterInstitution: 'City Clinic',
      reporterCountry: 'USA',
      reporterContact: 'nurse@clinic.org',
      productName: 'InfuCillin',
      productDose: '1g IV infusion',
      productFrequency: 'Single dose',
      productRoute: 'Intravenous',
      productLot: 'LOT-9988',
      productExpiry: '06/2027',
      productIndication: 'Sepsis prophylaxis',
      adverseEvent: 'Septic Shock',
      eventOnset: '2026-03-02',
      eventOutcome: 'Recovering in ICU',
      seriousnessCriteria: 'Life-threatening',
      dechallenge: 'Positive',
      rechallenge: 'Not done',
      clinicalNarrative: 'Patient developed acute hypotension and septic shock within 30 minutes of InfuCillin infusion.',
      sourceCitationsJson: JSON.stringify({
        patient: { source_type: 'pdf', page_or_location: 'Page 1, Box 1', verbatim_snippet: 'M.K., 68F' },
        reaction: { source_type: 'pdf', page_or_location: 'Page 1, Box 22', verbatim_snippet: 'Septic shock with MAP < 55' },
        defect: { source_type: 'photo', page_or_location: 'vial_photo.jpg', verbatim_snippet: 'Visible dark flakes in vial' }
      })
    },
    pqcReport: {
      productName: 'InfuCillin',
      lotNumber: 'LOT-9988',
      defectType: 'Particulate Contamination',
      defectDescription: 'Dark suspended particles observed inside unopened vial.',
      packagingBreached: false,
      photoDetected: true,
      photoDescription: 'Grey particulate settlement observed in solution.',
      requiresHumanReview: true,
      sourceCitationsJson: JSON.stringify({
        defect: { source_type: 'photo', page_or_location: 'vial_photo.jpg', verbatim_snippet: 'Visible dark flakes in vial' }
      })
    }
  };

  const mockMessageService = {
    getMessage: vi.fn().mockReturnValue(of(mockMessage)),
    acceptMessage: vi.fn().mockReturnValue(of({ ...mockMessage, status: 'REVIEWED' })),
    overrideMessage: vi.fn().mockReturnValue(of(mockMessage)),
    getAttachmentDownloadUrl: vi.fn().mockReturnValue('/api/messages/attachments/401/download')
  };

  const mockAuditService = {
    getAuditEvents: vi.fn().mockReturnValue(of([]))
  };

  const mockActivatedRoute = {
    paramMap: of({
      get: (key: string) => (key === 'id' ? '4' : null)
    })
  };

  const mockRouter = {
    navigate: vi.fn()
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CaseWorkspaceComponent],
      providers: [
        { provide: MessageService, useValue: mockMessageService },
        { provide: AuditService, useValue: mockAuditService },
        { provide: ActivatedRoute, useValue: mockActivatedRoute },
        { provide: Router, useValue: mockRouter }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(CaseWorkspaceComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('initializes and synthesizes a ReviewerBrief for Case 04', () => {
    expect(component.message).toBeDefined();
    expect(component.brief).toBeDefined();
    expect(component.brief?.caseId).toBe('CASE-004');
    expect(component.brief?.urgency).toBe('CRITICAL');
    expect(component.brief?.isMultiLabel).toBe(true);
  });

  it('renders attention items including photo defect and multi-label focus', () => {
    expect(component.brief?.reviewFocus.length).toBeGreaterThan(0);
    const photoFocus = component.brief?.reviewFocus.find(f => f.category === 'PHOTO_DEFECT_INSPECTION');
    expect(photoFocus).toBeDefined();
    expect(photoFocus?.headline).toContain('Defect Photo Inspection');
  });

  it('opens and closes evidence inspection drawer', () => {
    const factWithEvidence = component.brief?.facts.find(f => f.evidence !== undefined);
    expect(factWithEvidence).toBeDefined();

    component.openEvidenceForFact(factWithEvidence!);
    expect(component.activeEvidence).toBeDefined();
    expect(component.activeEvidence?.fieldKey).toBe(factWithEvidence?.field);

    component.closeEvidence();
    expect(component.activeEvidence).toBeUndefined();
  });

  it('switches category domain tabs accurately', () => {
    component.setCategoryTab('PQC');
    expect(component.selectedCategoryTab).toBe('PQC');
    const pqcFacts = component.filteredFacts;
    expect(pqcFacts.every(f => f.section === 'PQC')).toBe(true);

    component.setCategoryTab('ICSR');
    expect(component.selectedCategoryTab).toBe('ICSR');
    const icsrFacts = component.filteredFacts;
    expect(icsrFacts.every(f => ['PATIENT', 'REPORTER', 'PRODUCT', 'EVENT'].includes(f.section))).toBe(true);
  });

  it('filters facts by certainty status', () => {
    component.setStatusFilter('CONFIRMED');
    expect(component.filteredFacts.every(f => f.status === 'CONFIRMED')).toBe(true);

    component.setStatusFilter('NOT_STATED');
    expect(component.filteredFacts.every(f => f.status === 'NOT_STATED')).toBe(true);
  });

  it('handles Accept AI Case workflow and updates status to REVIEWED', () => {
    component.onAcceptAiResult();
    expect(mockMessageService.acceptMessage).toHaveBeenCalled();
    expect(component.message?.status).toBe('REVIEWED');
  });

  it('handles escalation flagging toggle', () => {
    expect(component.isFlaggedForEscalation).toBe(false);
    component.onFlagCase();
    expect(component.isFlaggedForEscalation).toBe(true);
    component.onFlagCase();
    expect(component.isFlaggedForEscalation).toBe(false);
  });
});
