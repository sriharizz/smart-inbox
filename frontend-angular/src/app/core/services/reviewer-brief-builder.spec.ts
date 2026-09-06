import { describe, it, expect } from 'vitest';
import { ReviewerBriefBuilder } from './reviewer-brief-builder';
import { IntakeMessage } from '../models/message.model';
import { ReviewFocusCategory } from '../models/reviewer-brief.model';

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

  // =========================================================================
  // =========================================================================
  // STEP 7 HARDENING / ARBITRARY EMAIL ADAPTATION SPECIFIC TESTS (16 CHECKS)
  // =========================================================================

  it('1. MI with actual product/questions: exposes structured topic, context, and requested details', () => {
    const miMessage: IntakeMessage = {
      ...baseMessage,
      id: 901,
      subject: 'Inquiry regarding Cefatox reconstitution',
      sender: 'Dr. Marcus Vance',
      senderEmail: 'mvance@clinic.org',
      receivedDate: '2026-09-07T00:00:00Z',
      primaryCategory: 'Medical Information Request (MI)',
      confidence: 0.94,
      status: 'PROCESSED',
      icsrReport: undefined,
      pqcReport: undefined,
      medicalInfo: {
        productOrTopic: 'Cefatox 1 g',
        inquiryType: 'Preparation & Dilution',
        questionText: 'What is the stability after dilution in D5W under refrigerated conditions?',
        clinicalContext: 'Adult surgical prophylaxis / hospital compounding',
        informationRequested: 'Refrigerated stability curves and compatibility with PVC infusion bags.',
        responseUrgency: 'Priority'
      }
    };

    const brief = ReviewerBriefBuilder.buildFromMessage(miMessage);
    expect(brief.miDetails).toBeDefined();
    expect(brief.miDetails?.productName).toBe('Cefatox 1 g');
    expect(brief.miDetails?.inquiryType).toBe('Preparation & Dilution');
    expect(brief.miDetails?.clinicalContext).toBe('Adult surgical prophylaxis / hospital compounding');
    expect(brief.miDetails?.informationRequested).toBe('Refrigerated stability curves and compatibility with PVC infusion bags.');
    expect(brief.miDetails?.questions.length).toBe(1);
    expect(brief.miDetails?.questions[0]).toContain('stability after dilution');
  });

  it('2. multiple MI questions: preserves ordering and extracts each discrete question separately', () => {
    const multiQuestionText = 
      '1. What is the stability after dilution in D5W under refrigerated conditions?\n' +
      '2. What is the in-use room-temperature stability?\n' +
      '3. Is Y-site co-infusion compatible with heparin?';

    const questions = ReviewerBriefBuilder.extractQuestions(multiQuestionText);
    expect(questions.length).toBe(3);
    expect(questions[0]).toBe('What is the stability after dilution in D5W under refrigerated conditions?');
    expect(questions[1]).toBe('What is the in-use room-temperature stability?');
    expect(questions[2]).toBe('Is Y-site co-infusion compatible with heparin?');
  });

  it('3. MI with no clinical fact ledger: maps MI inquiry details without fabricating fake clinical facts', () => {
    const miOnly: IntakeMessage = {
      ...baseMessage,
      id: 902,
      subject: 'Dosing clarification for paediatric patient',
      sender: 'PharmD Specialist',
      primaryCategory: 'Medical Information Request (MI)',
      icsrReport: undefined,
      pqcReport: undefined,
      medicalInfo: {
        productOrTopic: 'Neuroclene Oral Solution',
        inquiryType: 'Dosing Guidelines',
        questionText: 'Can this product be administered via nasogastric tube?'
      }
    };

    const brief = ReviewerBriefBuilder.buildFromMessage(miOnly);
    // Should NOT have patientAge, adverseEvent, or other fake ICSR facts
    const hasIcsrFact = brief.facts.some(f => f.field === 'adverseEvent' || f.field === 'patientAge');
    expect(hasIcsrFact).toBe(false);
    expect(brief.clinicalNarrative).toBeUndefined();
    // Only category-appropriate facts or inquiry details
    expect(brief.miDetails?.productName).toBe('Neuroclene Oral Solution');
  });

  it('4. ICSR with actual narrative: renders authentic synthesis and rejects generic placeholders', () => {
    const authenticNarrative = 'A 62-year-old female patient developed acute onset generalized urticaria and dyspnea 25 minutes after first infusion.';
    const icsrMsg: IntakeMessage = {
      ...baseMessage,
      icsrReport: {
        ...baseMessage.icsrReport!,
        clinicalNarrative: authenticNarrative
      }
    };

    const brief = ReviewerBriefBuilder.buildFromMessage(icsrMsg);
    expect(brief.clinicalNarrative).toBe(authenticNarrative);
    expect(brief.clinicalNarrative).not.toContain('based on physical source evidence');
  });

  it('5. missing narrative: provides neutral honest message rather than fake content', () => {
    const noNarrativeMsg: IntakeMessage = {
      ...baseMessage,
      icsrReport: {
        ...baseMessage.icsrReport!,
        clinicalNarrative: 'Not stated'
      }
    };

    const brief = ReviewerBriefBuilder.buildFromMessage(noNarrativeMsg);
    expect(brief.clinicalNarrative).toBe('Clinical narrative not stated in source.');
  });

  it('6. PQC with arbitrary new field: renders novel parameters without hardcoded field mappings', () => {
    const pqcArbitraryMsg: IntakeMessage = {
      ...baseMessage,
      id: 701,
      subject: 'Vial stopper integrity defect',
      primaryCategory: 'Quality Complaint (PQC)',
      icsrReport: undefined,
      pqcReport: {
        productName: 'BioVial 50mg',
        lotNumber: 'LOT-XYZ-99',
        defectType: 'Corer / Stopper Fragmentation',
        defectDescription: 'Elastomeric particles shed into solution upon needle entry',
        packagingBreached: true,
        photoDetected: false,
        photoDescription: '',
        requiresHumanReview: false
      },
      facts: [
        { field: 'vial_seal_integrity', value: 'Compromised', confidence: 0.98, section: 'PQC' },
        { field: 'sterilityAssuranceLevel', value: 'Exceeded Threshold', confidence: 0.91, section: 'PQC' }
      ]
    };

    const brief = ReviewerBriefBuilder.buildFromMessage(pqcArbitraryMsg);
    const sealFact = brief.facts.find(f => f.field === 'vial_seal_integrity');
    const sterilityFact = brief.facts.find(f => f.field === 'sterilityAssuranceLevel');

    expect(sealFact).toBeDefined();
    expect(sealFact?.label).toBe('Vial Seal Integrity');
    expect(sealFact?.value).toBe('Compromised');

    expect(sterilityFact).toBeDefined();
    expect(sterilityFact?.label).toBe('Sterility Assurance Level');
  });

  it('7. Not Relevant with no clinical payload: minimal, no spurious warnings, no fake fact tables', () => {
    const nrMsg: IntakeMessage = {
      ...baseMessage,
      id: 888,
      subject: 'Holiday Office Closure Notice',
      primaryCategory: 'Not Relevant',
      rawBody: 'Our offices will be closed on December 25th for the winter holiday.',
      icsrReport: undefined,
      pqcReport: undefined,
      medicalInfo: undefined
    };

    const brief = ReviewerBriefBuilder.buildFromMessage(nrMsg);
    expect(brief.primaryCategory).toBe('Not Relevant');
    expect(brief.facts.length).toBe(0);
    expect(brief.reviewFocus.length).toBe(0); // Zero spurious missing-field warnings
    expect(brief.validationWarnings.length).toBe(0);
    expect(brief.clinicalNarrative).toBeUndefined();
    expect(brief.notRelevantDetails).toBeDefined();
    expect(brief.validationGating).toBe('READY_FOR_REVIEW');
  });

  it('8. multi-label: correctly projects both ICSR and PQC domains simultaneously', () => {
    const multiMsg: IntakeMessage = {
      ...baseMessage,
      id: 401,
      subject: 'Contaminated injection leading to anaphylaxis',
      primaryCategory: 'Safety Report (ICSR) + Quality Complaint (PQC)',
      isMultiLabel: true,
      pqcReport: {
        productName: 'Cardioril',
        lotNumber: 'LOT-MULTI',
        defectType: 'Turbidity',
        defectDescription: 'Visible cloudiness with sediment',
        packagingBreached: false,
        photoDetected: true,
        photoDescription: 'Cloudy vial with sediment',
        requiresHumanReview: true
      }
    };

    const brief = ReviewerBriefBuilder.buildFromMessage(multiMsg);
    expect(brief.isMultiLabel).toBe(true);
    expect(brief.allCategories.length).toBe(2);
    expect(brief.pqcDetails).toBeDefined();
    expect(brief.facts.some(f => f.section === 'PQC')).toBe(true);
    expect(brief.facts.some(f => f.section === 'EVENT')).toBe(true);
  });

  it('9. unknown/extra fact field: formatFieldLabel dynamically converts camel, snake, kebab cases', () => {
    expect(ReviewerBriefBuilder.formatFieldLabel('biomarker_her2_expression')).toBe('Biomarker Her2 Expression');
    expect(ReviewerBriefBuilder.formatFieldLabel('patientBodyMassIndex')).toBe('Patient Body Mass Index');
    expect(ReviewerBriefBuilder.formatFieldLabel('custom-lot-subbatch-code')).toBe('Custom Lot Subbatch Code');
    expect(ReviewerBriefBuilder.formatFieldLabel('mi_storage_temperature_range')).toBe('Storage Temperature Range');
    expect(ReviewerBriefBuilder.formatFieldLabel('pqc_defect_root_cause')).toBe('Defect Root Cause');
  });

  it('10. missing optional values: resilient to null, undefined, empty fields without throwing', () => {
    const sparseMsg: any = {
      id: 999,
      subject: undefined,
      sender: undefined,
      primaryCategory: 'Safety Report (ICSR)',
      icsrReport: {
        productName: 'MinimalDrug'
      }
    };

    expect(() => {
      const brief = ReviewerBriefBuilder.buildFromMessage(sparseMsg);
      expect(brief.caseId).toBe('CASE-999');
      expect(brief.subject).toBe('Clinical Intake Transmission');
      expect(brief.sender).toBe('Primary Reporter / Source');
    }).not.toThrow();
  });

  it('11. conflict/warning focus item: automatically surfaces conflicting facts for human review', () => {
    const msgWithConflict: IntakeMessage = {
      ...baseMessage,
      facts: [
        {
          field: 'eventOnset',
          label: 'Reaction Onset Date',
          value: '2026-08-10 vs 2026-08-15',
          status: 'CONFLICT',
          confidence: 'HIGH',
          section: 'EVENT',
          evidence: [{ sourceType: 'Email', location: 'Body', snippet: 'Patient took drug on 10th but recorded 15th on discharge form.' }]
        }
      ]
    };

    const brief = ReviewerBriefBuilder.buildFromMessage(msgWithConflict);
    const conflictFocus = brief.reviewFocus.find(f => f.category === ReviewFocusCategory.EVIDENCE_CONFLICT);
    expect(conflictFocus).toBeDefined();
    expect(conflictFocus?.headline).toContain('Reaction Onset Date');
    expect(brief.validationGating).toBe('REVIEW_WITH_WARNINGS');
  });

  it('12. evidence rendering: transforms citations to human-readable verification references without internal scores', () => {
    const msgWithCitation: IntakeMessage = {
      ...baseMessage,
      icsrReport: {
        ...baseMessage.icsrReport!,
        sourceCitationsJson: JSON.stringify({
          product: {
            source_type: 'pdf',
            page_or_location: 'Page 3, Paragraph 2',
            verbatim_snippet: 'Prescribed Cardioril 20mg daily for mild hypertension.',
            verification_result: 'SUPPORTS',
            verification_rationale: 'Exact verbatim match with dosage guidelines'
          }
        })
      }
    };

    const brief = ReviewerBriefBuilder.buildFromMessage(msgWithCitation);
    const prodFact = brief.facts.find(f => f.field === 'productName');
    expect(prodFact?.evidence).toBeDefined();
    expect(prodFact?.evidence?.sourceType).toBe('pdf');
    expect(prodFact?.evidence?.location).toBe('Page 3, Paragraph 2');
    expect(prodFact?.evidence?.snippet).toContain('Prescribed Cardioril 20mg');
    expect(prodFact?.evidence?.verificationResult).toBe('SUPPORTS');
    // Ensure raw score is not in the presentation object
    expect((prodFact?.evidence as any).similarity_score).toBeUndefined();
  });

  it('13. validation wording: adheres to truthful human-review requirements without clinical infallibility claims', () => {
    const brief = ReviewerBriefBuilder.buildFromMessage(baseMessage);
    // Executive summary and validation state must not claim full clinical correctness
    expect(brief.executiveSummary).not.toContain('All critical regulatory parameters verified');
    expect(brief.executiveSummary).not.toContain('100% hallucination free');
  });

  it('14. arbitrary unseen email presentation: adapts seamlessly to an unknown email structure', () => {
    const novelSyntheticEmail: any = {
      ...baseMessage,
      id: 5544,
      caseId: 'CUSTOM-SYNTHETIC-NOVEL-01',
      subject: 'Veterinary compounding inquiry for equines',
      sender: 'Dr. Gregory House, DVM',
      senderEmail: 'ghouse@veterinary-clinic.org',
      receivedDate: '2026-09-07T08:30:00Z',
      primaryCategory: 'Medical Information Request (MI)',
      confidence: 0.91,
      status: 'PROCESSED',
      rawBody: 'Inquiring about off-label reconstitution of Cefatox for equine administration.',
      icsrReport: undefined,
      pqcReport: undefined,
      medicalInfo: {
        productOrTopic: 'Cefatox Injectable',
        inquiryType: 'Special Population / Off-label',
        questionText: 'Is there stability data for sterile reconstitution in sterile water for injection stored in glass vials for 7 days at 4°C?',
        clinicalContext: 'Equine respiratory infection protocol',
        informationRequested: 'Stability assays and particulate formation data.',
        responseUrgency: 'Standard'
      }
    };

    const brief = ReviewerBriefBuilder.buildFromMessage(novelSyntheticEmail);
    expect(brief.caseId).toBe('CUSTOM-SYNTHETIC-NOVEL-01');
    expect(brief.primaryCategory).toBe('Medical Information Request (MI)');
    expect(brief.urgency).toBe('STANDARD');
    expect(brief.miDetails).toBeDefined();
    expect(brief.miDetails?.productName).toBe('Cefatox Injectable');
    expect(brief.miDetails?.clinicalContext).toBe('Equine respiratory infection protocol');
    expect(brief.miDetails?.questions.length).toBe(1);
    expect(brief.facts.some(f => f.field === 'adverseEvent')).toBe(false);
  });

  it('15. empty category payload: handles empty report objects gracefully', () => {
    const emptyPayloadMsg: any = {
      ...baseMessage,
      id: 111,
      subject: 'Incomplete Transmission',
      primaryCategory: 'Quality Complaint (PQC)',
      icsrReport: undefined,
      pqcReport: {}
    };

    expect(() => {
      const brief = ReviewerBriefBuilder.buildFromMessage(emptyPayloadMsg);
      expect(brief.pqcDetails).toBeDefined();
      expect(brief.pqcDetails?.productName).toBe('Not stated');
    }).not.toThrow();
  });

  it('16. no hardcoded case ID behavior: behaves identically for arbitrary case IDs', () => {
    const arbitraryIdMsg: IntakeMessage = {
      ...baseMessage,
      id: 12345,
      subject: 'Adverse event with novel identifier'
    };

    const brief = ReviewerBriefBuilder.buildFromMessage(arbitraryIdMsg);
    expect(brief.caseId).toBe('CASE-12345');
    expect(brief.primaryCategory).toBe('Safety Report (ICSR)');
    expect(brief.facts.length).toBeGreaterThan(5);
  });
});

