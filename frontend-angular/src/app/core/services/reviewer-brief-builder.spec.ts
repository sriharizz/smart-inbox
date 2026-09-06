import { describe, it, expect } from 'vitest';
import { ReviewerBriefBuilder } from './reviewer-brief-builder';
import { IntakeMessage } from '../models/message.model';

describe('ReviewerBriefBuilder', () => {
  const baseMessage: IntakeMessage = {
    id: 1,
    messageId: 'msg-001',
    sender: 'Dr. John Watson',
    senderEmail: 'jwatson@stbarts.nhs.uk',
    subject: 'ADR: Severe Angioedema following Cardioril',
    receivedDate: '2026-03-01 09:30:00',
    rawBody: 'Patient developed severe facial swelling after 20mg Cardioril.',
    status: 'TRIAGED',
    primaryCategory: 'Safety Report (ICSR)',
    confidence: 0.96,
    isMultiLabel: false,
    createdAt: '2026-03-01T09:30:00Z',
    updatedAt: '2026-03-01T09:35:00Z',
    attachments: [
      {
        id: 101,
        filename: 'cioms_form.pdf',
        contentType: 'application/pdf',
        sizeBytes: 154000,
        flavor: 'digital_form'
      }
    ],
    icsrReport: {
      patientIdentifier: 'J.D.',
      patientAge: '58 years',
      patientSex: 'MALE',
      patientWeight: '82 kg',
      patientHistory: 'Hypertension',
      reporterName: 'Dr. John Watson',
      reporterRole: 'Physician',
      reporterInstitution: "St. Bart's Hospital",
      reporterCountry: 'UK',
      reporterContact: 'jwatson@stbarts.nhs.uk',
      productName: 'Cardioril',
      productDose: '20mg oral daily',
      productFrequency: 'Once daily',
      productRoute: 'Oral',
      productLot: 'B-9921',
      productExpiry: '12/2027',
      productIndication: 'Hypertension',
      adverseEvent: 'Severe Angioedema',
      eventOnset: '2026-03-01',
      eventOutcome: 'Recovering',
      seriousnessCriteria: 'Hospitalization',
      dechallenge: 'Positive',
      rechallenge: 'Not done',
      clinicalNarrative: '58-year-old male presented with acute angioedema after Cardioril administration.',
      sourceCitationsJson: JSON.stringify({
        patient: { source_type: 'pdf', page_or_location: 'Page 1, Box 1', verbatim_snippet: 'Patient J.D., 58 yo male' },
        reaction: { source_type: 'pdf', page_or_location: 'Page 1, Box 22', verbatim_snippet: 'Developed severe angioedema' }
      })
    }
  };

  it('correctly maps a canonical ICSR case into ReviewerBrief', () => {
    const brief = ReviewerBriefBuilder.buildFromMessage(baseMessage);

    expect(brief.caseId).toBe('CASE-001');
    expect(brief.primaryCategory).toBe('Safety Report (ICSR)');
    expect(brief.urgency).toBe('EXPEDITED'); // ICSR has 15-day regulatory clock
    expect(brief.validationGating).toBe('READY_FOR_REVIEW');
    expect(brief.confidence).toBe(0.96);
    expect(brief.facts.length).toBeGreaterThan(10);
    expect(brief.factStats.confirmedCount).toBeGreaterThan(10);
    expect(brief.factStats.conflictCount).toBe(0);
  });

  it('correctly handles NOT_STATED values without hallucinations', () => {
    const msgWithMissing: IntakeMessage = {
      ...baseMessage,
      icsrReport: {
        ...baseMessage.icsrReport!,
        productDose: 'Not stated',
        patientWeight: 'null',
        productExpiry: '-'
      }
    };

    const brief = ReviewerBriefBuilder.buildFromMessage(msgWithMissing);
    const doseFact = brief.facts.find(f => f.field === 'productDose');
    const weightFact = brief.facts.find(f => f.field === 'patientWeight');

    expect(doseFact).toBeDefined();
    expect(doseFact?.status).toBe('NOT_STATED');
    expect(doseFact?.value).toBe('Not stated');

    expect(weightFact).toBeDefined();
    expect(weightFact?.status).toBe('NOT_STATED');

    // Missing critical field should surface in review focus items and trigger warnings
    const missingFocus = brief.reviewFocus.find(f => f.fieldAffected === 'productDose');
    expect(missingFocus).toBeDefined();
    expect(brief.validationGating).toBe('REVIEW_WITH_WARNINGS');
  });

  it('correctly handles Multi-Label case with ICSR and PQC (Case 04 pattern)', () => {
    const multiLabelMsg: IntakeMessage = {
      ...baseMessage,
      id: 4,
      subject: 'Severe sepsis following cloudy infusion vial',
      primaryCategory: 'Safety Report (ICSR) + Quality Complaint (PQC)',
      isMultiLabel: true,
      pqcReport: {
        productName: 'InfuCillin',
        lotNumber: 'LOT-9988',
        defectType: 'Particulate Contamination',
        defectDescription: 'Dark particulate suspension observed in reconstituted vial',
        packagingBreached: false,
        photoDetected: true,
        photoDescription: 'Cloudy vial photo attached showing grey particulate settlement',
        requiresHumanReview: true,
        sourceCitationsJson: JSON.stringify({
          defect: { source_type: 'photo', page_or_location: 'vial_photo.jpg', verbatim_snippet: 'Particulate suspension in vial' }
        })
      }
    };

    const brief = ReviewerBriefBuilder.buildFromMessage(multiLabelMsg);

    expect(brief.isMultiLabel).toBe(true);
    expect(brief.urgency).toBe('CRITICAL'); // PQC photo review + multi-label
    expect(brief.allCategories).toContain('Safety Report (ICSR)');
    expect(brief.allCategories).toContain('Quality Complaint (PQC)');

    // Verify photo inspection focus item
    const photoFocus = brief.reviewFocus.find(f => f.category === 'PHOTO_DEFECT_INSPECTION');
    expect(photoFocus).toBeDefined();
    expect(photoFocus?.headline).toContain('Defect Photo Inspection');
    expect(brief.pqcDetails).toBeDefined();
    expect(brief.pqcDetails?.requiresHumanReview).toBe(true);
  });

  it('correctly maps a Medical Information (MI) inquiry case', () => {
    const miMsg: IntakeMessage = {
      ...baseMessage,
      id: 9,
      primaryCategory: 'Medical Information Request (MI)',
      subject: 'Stability inquiry: Can Cardioril be refrigerated after dilution?',
      icsrReport: undefined,
      medicalInfo: {
        productName: 'Cardioril',
        inquiryType: 'Storage & Stability',
        inquirySummary: 'Can Cardioril 20mg solution be refrigerated at 2-8°C for 48 hours after reconstitution?',
        responseUrgency: 'Standard'
      }
    };

    const brief = ReviewerBriefBuilder.buildFromMessage(miMsg);

    expect(brief.primaryCategory).toBe('Medical Information Request (MI)');
    expect(brief.urgency).toBe('STANDARD');
    expect(brief.miDetails).toBeDefined();
    expect(brief.miDetails?.questions.length).toBeGreaterThan(0);
    expect(brief.miDetails?.questions[0]).toContain('refrigerated');
  });

  it('correctly maps a Not Relevant case without clinical forms', () => {
    const notRelevantMsg: IntakeMessage = {
      ...baseMessage,
      id: 10,
      primaryCategory: 'Not Relevant',
      subject: 'Annual Medical Conference Invitation 2026',
      rawBody: 'You are invited to the 2026 Cardiology Expo in Munich.',
      icsrReport: undefined,
      pqcReport: undefined,
      medicalInfo: undefined
    };

    const brief = ReviewerBriefBuilder.buildFromMessage(notRelevantMsg);

    expect(brief.primaryCategory).toBe('Not Relevant');
    expect(brief.notRelevantDetails).toBeDefined();
    expect(brief.facts.length).toBe(0);
  });

  it('correctly flags foreign language (Spanish) submissions', () => {
    const spanishMsg: IntakeMessage = {
      ...baseMessage,
      id: 5,
      subject: 'Notificación de sospecha de reacción adversa',
      rawBody: 'Notificación de sospecha: el paciente presentó erupción cutánea grave.',
      attachments: [
        {
          id: 105,
          filename: 'notificacion_farmacovigilancia.pdf',
          contentType: 'application/pdf',
          sizeBytes: 85000,
          flavor: 'non_english',
          language: 'Spanish'
        }
      ]
    };

    const brief = ReviewerBriefBuilder.buildFromMessage(spanishMsg);
    const langFocus = brief.reviewFocus.find(f => f.category === 'MULTILINGUAL_TRANSLATION');
    expect(langFocus).toBeDefined();
    expect(langFocus?.headline).toContain('Spanish');
  });
});
