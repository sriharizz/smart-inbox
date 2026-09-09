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
    expect(langFocus?.headline).toBe('Foreign Language Intake (Spanish)');
    expect(langFocus?.detail).toContain('Document was submitted in Spanish.');
  });

  it('correctly handles second non-English language (German) using same generic mechanism', () => {
    const germanMsg: IntakeMessage = {
      ...baseMessage,
      id: 6,
      subject: 'Bericht über unerwünschte Arzneimittelwirkungen',
      rawBody: 'Charité Berlin UAW Meldung.',
      attachments: [
        {
          id: 106,
          filename: 'bericht_uaw_charite_berlin.pdf',
          contentType: 'application/pdf',
          sizeBytes: 92000,
          flavor: 'non_english',
          language: 'German'
        }
      ]
    };

    const brief = ReviewerBriefBuilder.buildFromMessage(germanMsg);
    const langFocus = brief.reviewFocus.find(f => f.category === 'MULTILINGUAL_TRANSLATION');
    expect(langFocus).toBeDefined();
    expect(langFocus?.headline).toBe('Foreign Language Intake (German)');
    expect(langFocus?.detail).toContain('Document was submitted in German.');
  });

  it('English PDF with normal/digital flavor produces NO foreign language warning', () => {
    const englishMsg: IntakeMessage = {
      ...baseMessage,
      id: 7,
      subject: 'Case report for Cardioril',
      language: 'English',
      attachments: [
        {
          id: 107,
          filename: 'cioms_form_MK_Cardioril.pdf',
          contentType: 'application/pdf',
          sizeBytes: 54000,
          flavor: 'digital_form',
          language: 'English'
        }
      ]
    };

    const brief = ReviewerBriefBuilder.buildFromMessage(englishMsg);
    const langFocus = brief.reviewFocus.find(f => f.category === 'MULTILINGUAL_TRANSLATION');
    expect(langFocus).toBeUndefined();
  });

  it('misleading English filename (packaging_defect_report.pdf) produces NO false foreign language warning', () => {
    const englishPqcMsg: IntakeMessage = {
      ...baseMessage,
      id: 25,
      subject: 'Damaged packaging report',
      language: 'English',
      attachments: [
        {
          id: 125,
          filename: 'packaging_defect_report.pdf',
          contentType: 'application/pdf',
          sizeBytes: 120000,
          flavor: 'digital_form',
          language: 'English'
        }
      ]
    };

    const brief = ReviewerBriefBuilder.buildFromMessage(englishPqcMsg);
    const langFocus = brief.reviewFocus.find(f => f.category === 'MULTILINGUAL_TRANSLATION');
    expect(langFocus).toBeUndefined();
  });

  it('inconsistent metadata (flavor = non_english with language = English) must NOT trigger foreign language warning', () => {
    const inconsistentMsg: IntakeMessage = {
      ...baseMessage,
      id: 26,
      subject: 'Packaging defect complaint',
      language: 'English',
      attachments: [
        {
          id: 126,
          filename: 'packaging_defect_report.pdf',
          contentType: 'application/pdf',
          sizeBytes: 120000,
          flavor: 'non_english', // Inconsistent with language = 'English'
          language: 'English'
        }
      ]
    };

    const brief = ReviewerBriefBuilder.buildFromMessage(inconsistentMsg);
    const langFocus = brief.reviewFocus.find(f => f.category === 'MULTILINGUAL_TRANSLATION');
    expect(langFocus).toBeUndefined();
  });

  it('English email + Spanish PDF: message language remains English, warning shows Spanish attachment language', () => {
    const mixedMsg: IntakeMessage = {
      ...baseMessage,
      id: 27,
      subject: 'Forwarding Spanish safety case from Madrid affiliate',
      rawBody: 'Please find attached the Spanish adverse reaction report received today.',
      language: 'English',
      attachments: [
        {
          id: 127,
          filename: 'notificacion_ram_madrid.pdf',
          contentType: 'application/pdf',
          sizeBytes: 85000,
          flavor: 'non_english',
          language: 'Spanish'
        }
      ]
    };

    const brief = ReviewerBriefBuilder.buildFromMessage(mixedMsg);
    // Message language is untouched
    expect(mixedMsg.language).toBe('English');

    // UI Foreign Language warning displays the attachment language (Spanish)
    const langFocus = brief.reviewFocus.find(f => f.category === 'MULTILINGUAL_TRANSLATION');
    expect(langFocus).toBeDefined();
    expect(langFocus?.headline).toBe('Foreign Language Intake (Spanish)');
    expect(langFocus?.detail).toContain('Document was submitted in Spanish.');
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

  it('17. complete data coverage: maps all extended canonical fields for Case 009 CIOMS dataset', () => {
    const case009Message: IntakeMessage = {
      ...baseMessage,
      id: 9,
      messageId: 'msg-009',
      primaryCategory: 'Safety Report (ICSR)',
      icsrReport: {
        ...baseMessage.icsrReport!,
        patientIdentifier: 'M.K.',
        patientAge: '68',
        patientSex: 'FEMALE',
        patientWeight: '68 kg',
        patientHistory: 'Hypertension, Hyperlipidemia',
        reporterName: 'Dr. Sarah Jenkins',
        reporterRole: 'Physician',
        productName: 'Cardioril',
        adverseEvent: 'Angioedema, Anaphylaxis',
        sourceCitationsJson: JSON.stringify({
          patient_dob_val: '1957-04-12',
          patient_country_val: 'United Kingdom',
          reporter_specialty_val: 'Cardiology',
          health_professional_val: true,
          product_formulation_val: 'Film-coated tablet',
          treatment_start_date_val: '2026-02-15',
          treatment_stop_date_val: '2026-03-01',
          treatment_duration_val: '14 days',
          action_taken_val: 'Drug withdrawn permanently',
          hospitalization_val: true,
          hospital_admission_date_val: '2026-03-01',
          life_threatening_val: true,
          concomitant_medications: [
            {
              drug_name: 'Metformin 500mg',
              indication: 'Type 2 Diabetes',
              dose_frequency: '500mg BID',
              dates_of_administration: '2020 to present',
              citation: { source_type: 'pdf', page_number: 1, verbatim_snippet: 'Metformin 500mg BID since 2020' }
            },
            {
              drug_name: 'Atorvastatin 20mg',
              indication: 'Hyperlipidemia',
              dose_frequency: '20mg QD',
              dates_of_administration: '2022 to present',
              citation: { source_type: 'pdf', page_number: 1, verbatim_snippet: 'Atorvastatin 20mg QD' }
            }
          ],
          lab_tests: [
            {
              test_name: 'Serum Tryptase',
              test_date: '2026-03-01',
              result: '48.5',
              unit: 'ug/L',
              reference_range: '< 11.4 ug/L',
              interpretation: 'Elevated (Consistent with severe mast cell degranulation)',
              citation: { source_type: 'pdf', page_number: 1, verbatim_snippet: 'Tryptase: 48.5 ug/L (normal < 11.4)' }
            }
          ],
          regulatory: {
            mfr_report_no: 'MFR-UK-2026-009',
            expedited_15_day: true,
            report_type: 'Initial Expedited',
            date_received: '2026-03-02',
            company_name: 'CardioPharma Ltd.'
          }
        })
      }
    };

    const brief = ReviewerBriefBuilder.buildFromMessage(case009Message);
    expect(brief.sections).toBeDefined();
    expect(brief.sections!.length).toBeGreaterThanOrEqual(7);

    // Verify sections exist
    const patientSec = brief.sections!.find(s => s.key === 'patient');
    const reporterSec = brief.sections!.find(s => s.key === 'reporter');
    const productSec = brief.sections!.find(s => s.key === 'product');
    const reactionSec = brief.sections!.find(s => s.key === 'reaction');
    const concomSec = brief.sections!.find(s => s.key === 'concomitant_medications');
    const labSec = brief.sections!.find(s => s.key === 'lab_tests');
    const regSec = brief.sections!.find(s => s.key === 'regulatory');

    expect(patientSec).toBeDefined();
    expect(patientSec?.fields?.some(f => f.key === 'patientDob' && f.value === '1957-04-12')).toBe(true);
    expect(patientSec?.fields?.some(f => f.key === 'patientCountry' && f.value === 'United Kingdom')).toBe(true);

    expect(reporterSec?.fields?.some(f => f.key === 'reporterSpecialty' && f.value === 'Cardiology')).toBe(true);
    expect(reporterSec?.fields?.some(f => f.key === 'healthProfessional' && f.value.includes('Yes'))).toBe(true);

    expect(productSec?.fields?.some(f => f.key === 'productFormulation' && f.value === 'Film-coated tablet')).toBe(true);
    expect(productSec?.fields?.some(f => f.key === 'treatmentDuration' && f.value === '14 days')).toBe(true);
    expect(productSec?.fields?.some(f => f.key === 'actionTaken' && f.value.includes('withdrawn'))).toBe(true);

    expect(reactionSec?.fields?.some(f => f.key === 'hospitalization' && f.value.includes('Hospitalized'))).toBe(true);
    expect(reactionSec?.fields?.some(f => f.key === 'lifeThreatening' && f.value.includes('Life Threatening'))).toBe(true);

    // Verify repeated groups
    expect(concomSec?.presentationType).toBe('TABLE');
    expect(concomSec?.repeatedGroup?.rows.length).toBe(2);
    expect(concomSec?.repeatedGroup?.rows[0].cells['drug_name']).toBe('Metformin 500mg');
    expect(concomSec?.repeatedGroup?.rows[0].evidence?.pageNumber).toBe(1);

    expect(labSec?.presentationType).toBe('TABLE');
    expect(labSec?.repeatedGroup?.rows.length).toBe(1);
    expect(labSec?.repeatedGroup?.rows[0].cells['test_name']).toBe('Serum Tryptase');
    expect(labSec?.repeatedGroup?.rows[0].cells['interpretation']).toContain('Consistent with severe mast cell');

    expect(regSec?.fields?.some(f => f.key === 'mfrReportNo' && f.value === 'MFR-UK-2026-009')).toBe(true);
    expect(regSec?.fields?.some(f => f.key === 'expedited15Day' && f.value.includes('YES'))).toBe(true);
  });

  it('18. category adaptability: PQC case produces only PQC sections and omits ICSR sections', () => {
    const pqcMessage: IntakeMessage = {
      ...baseMessage,
      id: 4,
      primaryCategory: 'Quality Complaint (PQC)',
      icsrReport: undefined,
      pqcReport: {
        productName: 'BioVial 50ml',
        lotNumber: 'LOT-BV-99',
        defectType: 'Particulate Contamination',
        defectDescription: 'Foreign glass particles inside sealed container',
        packagingBreached: false,
        photoDetected: true,
        photoDescription: 'Glass fragment visible at base of vial',
        requiresHumanReview: true
      }
    };

    const brief = ReviewerBriefBuilder.buildFromMessage(pqcMessage);
    expect(brief.sections).toBeDefined();
    expect(brief.sections!.some(s => s.key === 'pqc_product')).toBe(true);
    expect(brief.sections!.some(s => s.key === 'pqc_inspection')).toBe(true);
    expect(brief.sections!.some(s => s.key === 'patient')).toBe(false);
    expect(brief.sections!.some(s => s.key === 'concomitant_medications')).toBe(false);
    expect(brief.sections!.some(s => s.key === 'lab_tests')).toBe(false);
  });

  it('19. category adaptability: MI case produces only MI sections and omits ICSR/PQC sections', () => {
    const miMessage: IntakeMessage = {
      ...baseMessage,
      id: 2,
      primaryCategory: 'Medical Information Request (MI)',
      icsrReport: undefined,
      pqcReport: undefined,
      medicalInfo: {
        productOrTopic: 'RespiraVent 100mcg',
        inquiryType: 'Dosing & Administration',
        questionText: '1. Can RespiraVent be administered via ultrasonic nebulizer?\n2. What is the recommended pediatric dose?',
        clinicalContext: 'Severe acute pediatric asthma refractory to standard albuterol',
        responseUrgency: 'Expedited'
      }
    };

    const brief = ReviewerBriefBuilder.buildFromMessage(miMessage);
    expect(brief.sections).toBeDefined();
    expect(brief.sections!.some(s => s.key === 'mi_inquiry')).toBe(true);
    expect(brief.sections!.some(s => s.key === 'mi_questions')).toBe(true);
    expect(brief.sections!.some(s => s.key === 'mi_context')).toBe(true);

    const qSec = brief.sections!.find(s => s.key === 'mi_questions');
    expect(qSec?.repeatedGroup?.rows.length).toBe(2);
    expect(brief.sections!.some(s => s.key === 'patient')).toBe(false);
    expect(brief.sections!.some(s => s.key === 'pqc_product')).toBe(false);
  });

  it('20. category adaptability: Not Relevant case produces only triage determination & excerpt', () => {
    const notRelMessage: IntakeMessage = {
      ...baseMessage,
      id: 8,
      primaryCategory: 'Not Relevant',
      executiveSummary: 'General inquiry regarding company annual stock dividend.',
      rawBody: 'Dear customer relations, please send copy of 2025 financial shareholder report.'
    };

    const brief = ReviewerBriefBuilder.buildFromMessage(notRelMessage);
    expect(brief.sections).toBeDefined();
    expect(brief.sections!.length).toBe(2);
    expect(brief.sections![0].key).toBe('triage_exclusion');
    expect(brief.sections![1].key).toBe('exclusion_excerpt');
    expect(brief.sections!.some(s => s.key === 'patient')).toBe(false);
    expect(brief.sections!.some(s => s.key === 'pqc_product')).toBe(false);
  });

  it('21. unseen case adaptability: unseen company format dynamically populates sections without hardcoding', () => {
    const unseenCaseMessage: any = {
      id: 8888,
      messageId: 'NOVEL-UNSEEN-001',
      sender: 'Dr. Klaus Becker',
      senderEmail: 'kbecker@charite.de',
      subject: 'Novel Drug Product Adverse Event',
      primaryCategory: 'Safety Report (ICSR)',
      icsrReport: {
        patientIdentifier: 'UNSEEN-PT-9',
        patientAge: '42 years',
        patientSex: 'MALE',
        reporterName: 'Dr. Klaus Becker',
        reporterRole: 'Professor of Neurology',
        productName: 'NeuroCalm Ultra',
        adverseEvent: 'Severe Myasthenia Crisis',
        clinicalNarrative: 'Patient experienced myasthenia crisis within 48h of NeuroCalm Ultra initiation.',
        sourceCitationsJson: JSON.stringify({
          patient_dob_val: '1984-07-22',
          patient_country_val: 'Germany',
          reporter_specialty_val: 'Neurology',
          product_formulation_val: 'Sublingual Spray',
          treatment_duration_val: '3 days',
          concomitant_medications: [
            {
              drug_name: 'Pyridostigmine 60mg',
              indication: 'Myasthenia Gravis',
              dose_frequency: '60mg TID',
              dates_of_administration: '2019-ongoing'
            }
          ]
        })
      }
    };

    const brief = ReviewerBriefBuilder.buildFromMessage(unseenCaseMessage);
    expect(brief.caseId).toBe('CASE-8888');
    const ptSec = brief.sections?.find(s => s.key === 'patient');
    expect(ptSec?.fields?.some(f => f.value === 'UNSEEN-PT-9')).toBe(true);
    expect(ptSec?.fields?.some(f => f.value === '1984-07-22')).toBe(true);
    expect(ptSec?.fields?.some(f => f.value === 'Germany')).toBe(true);

    const prodSec = brief.sections?.find(s => s.key === 'product');
    expect(prodSec?.fields?.some(f => f.value === 'NeuroCalm Ultra')).toBe(true);
    expect(prodSec?.fields?.some(f => f.value === 'Sublingual Spray')).toBe(true);

    const concomSec = brief.sections?.find(s => s.key === 'concomitant_medications');
    expect(concomSec?.repeatedGroup?.rows[0].cells['drug_name']).toBe('Pyridostigmine 60mg');
  });

  it('22. absence of repeated groups: cases without concomitant medications or lab tests do not create phantom tables', () => {
    const cleanCaseMessage: IntakeMessage = {
      ...baseMessage,
      id: 50,
      icsrReport: {
        ...baseMessage.icsrReport!,
        sourceCitationsJson: JSON.stringify({
          patient: { source_type: 'email', page_or_location: 'body', verbatim_snippet: 'Patient 58yo' }
        })
      }
    };

    const brief = ReviewerBriefBuilder.buildFromMessage(cleanCaseMessage);
    expect(brief.sections?.some(s => s.key === 'concomitant_medications')).toBe(false);
    expect(brief.sections?.some(s => s.key === 'lab_tests')).toBe(false);
    expect(brief.sections?.some(s => s.key === 'regulatory')).toBe(false);
  });

  it('23. root cause 1: correctly maps canonical laboratory assay results from value property', () => {
    const case009WithCanonicalLabs: IntakeMessage = {
      ...baseMessage,
      id: 9,
      icsrReport: {
        ...baseMessage.icsrReport!,
        labTestsJson: JSON.stringify([
          {
            test_name: 'Alanine Aminotransferase (ALT / SGPT)',
            value: '540',
            unit: 'U/L',
            reference_range: '7 – 56',
            interpretation: 'Severe transaminitis (>9x ULN)',
            test_date: '10-NOV-2025',
            citation: {
              source_type: 'pdf',
              source_name: 'cioms_form_MK_Cardioril.pdf',
              page_number: 1,
              verbatim_snippet: 'ALT: 540 U/L (ref 7-56)'
            }
          },
          {
            test_name: 'Aspartate Aminotransferase (AST / SGOT)',
            value: '420',
            unit: 'U/L',
            reference_range: '10 – 40',
            interpretation: 'Severe hepatocellular injury (>10x ULN)',
            test_date: '10-NOV-2025',
            citation: {
              source_type: 'pdf',
              source_name: 'cioms_form_MK_Cardioril.pdf',
              page_number: 1,
              verbatim_snippet: 'AST: 420 U/L (ref 10-40)'
            }
          },
          {
            test_name: 'Total Bilirubin',
            value: '4.8',
            unit: 'mg/dL',
            reference_range: '0.1 – 1.2',
            interpretation: 'Profound hyperbilirubinemia meeting Hy\'s Law criteria',
            test_date: '10-NOV-2025',
            citation: {
              source_type: 'pdf',
              source_name: 'cioms_form_MK_Cardioril.pdf',
              page_number: 1,
              verbatim_snippet: 'Total Bilirubin: 4.8 mg/dL (ref 0.1-1.2)'
            }
          },
          {
            test_name: 'Alkaline Phosphatase (ALP)',
            value: '210',
            unit: 'U/L',
            reference_range: '44 – 147',
            interpretation: 'Moderate elevation (<2x ULN)',
            test_date: '10-NOV-2025',
            citation: {
              source_type: 'pdf',
              source_name: 'cioms_form_MK_Cardioril.pdf',
              page_number: 1,
              verbatim_snippet: 'ALP: 210 U/L (ref 44-147)'
            }
          },
          {
            test_name: 'Serum Creatinine',
            value: '0.9',
            unit: 'mg/dL',
            reference_range: '0.6 – 1.2',
            interpretation: 'Normal renal function',
            test_date: '10-NOV-2025',
            citation: {
              source_type: 'pdf',
              source_name: 'cioms_form_MK_Cardioril.pdf',
              page_number: 1,
              verbatim_snippet: 'Creatinine: 0.9 mg/dL'
            }
          },
          {
            test_name: 'Hepatitis A, B, C Serology (IgM, HBsAg, HCV-Ab)',
            value: 'Negative',
            unit: '—',
            reference_range: 'Negative',
            interpretation: 'Viral hepatitis excluded',
            test_date: '11-NOV-2025',
            citation: {
              source_type: 'pdf',
              source_name: 'cioms_form_MK_Cardioril.pdf',
              page_number: 1,
              verbatim_snippet: 'Viral serologies: Negative'
            }
          }
        ])
      }
    };

    const brief = ReviewerBriefBuilder.buildFromMessage(case009WithCanonicalLabs);
    const labSec = brief.sections?.find(s => s.key === 'lab_tests');
    expect(labSec).toBeDefined();
    expect(labSec?.presentationType).toBe('TABLE');

    const rows = labSec?.repeatedGroup?.rows;
    expect(rows).toBeDefined();
    expect(rows!.length).toBe(6);

    // ALT: 540 U/L
    expect(rows![0].cells['test_name']).toBe('Alanine Aminotransferase (ALT / SGPT)');
    expect(rows![0].cells['result']).toBe('540');
    expect(rows![0].cells['unit']).toBe('U/L');
    expect(rows![0].cells['reference_range']).toBe('7 – 56');
    expect(rows![0].cells['test_date']).toBe('10-NOV-2025');
    expect(rows![0].cells['interpretation']).toBe('Severe transaminitis (>9x ULN)');
    expect(rows![0].evidence?.sourceName).toBe('cioms_form_MK_Cardioril.pdf');
    expect(rows![0].evidence?.pageNumber).toBe(1);

    // AST: 420 U/L
    expect(rows![1].cells['test_name']).toBe('Aspartate Aminotransferase (AST / SGOT)');
    expect(rows![1].cells['result']).toBe('420');
    expect(rows![1].cells['unit']).toBe('U/L');
    expect(rows![1].cells['reference_range']).toBe('10 – 40');
    expect(rows![1].cells['test_date']).toBe('10-NOV-2025');
    expect(rows![1].cells['interpretation']).toBe('Severe hepatocellular injury (>10x ULN)');
    expect(rows![1].evidence?.pageNumber).toBe(1);

    // Total Bilirubin: 4.8 mg/dL
    expect(rows![2].cells['test_name']).toBe('Total Bilirubin');
    expect(rows![2].cells['result']).toBe('4.8');
    expect(rows![2].cells['unit']).toBe('mg/dL');
    expect(rows![2].cells['reference_range']).toBe('0.1 – 1.2');
    expect(rows![2].cells['interpretation']).toContain('Hy\'s Law');

    // ALP: 210 U/L
    expect(rows![3].cells['test_name']).toBe('Alkaline Phosphatase (ALP)');
    expect(rows![3].cells['result']).toBe('210');
    expect(rows![3].cells['unit']).toBe('U/L');
    expect(rows![3].cells['reference_range']).toBe('44 – 147');

    // Serum Creatinine: 0.9 mg/dL
    expect(rows![4].cells['test_name']).toBe('Serum Creatinine');
    expect(rows![4].cells['result']).toBe('0.9');
    expect(rows![4].cells['unit']).toBe('mg/dL');
    expect(rows![4].cells['reference_range']).toBe('0.6 – 1.2');

    // Hepatitis Serology: Negative
    expect(rows![5].cells['test_name']).toContain('Hepatitis A, B, C Serology');
    expect(rows![5].cells['result']).toBe('Negative');
    expect(rows![5].cells['reference_range']).toBe('Negative');
    expect(rows![5].cells['interpretation']).toBe('Viral hepatitis excluded');
  });

  it('Root Cause 2: resolves contradictory false hospitalization boolean deterministically against seriousness criteria', () => {
    // 1. Contradictory false hospitalization boolean with "Hospitalization, Medically Significant" in seriousness criteria
    const caseContradictory: IntakeMessage = {
      ...baseMessage,
      messageId: 'msg-hosp-contra',
      primaryCategory: 'Safety Report (ICSR)',
      icsrReport: {
        ...baseMessage.icsrReport!,
        adverseEvent: 'Acute Drug-Induced Liver Injury',
        seriousnessCriteria: 'Hospitalization, Medically Significant',
        sourceCitationsJson: JSON.stringify({
          hospitalization_val: false,
          hospital_admission_date_val: '10-NOV-2025',
          medically_important_val: false
        })
      }
    };

    const briefContra = ReviewerBriefBuilder.buildFromMessage(caseContradictory);
    const rxSecContra = briefContra.sections?.find(s => s.key === 'reaction');
    expect(rxSecContra).toBeDefined();

    const hospFieldContra = rxSecContra!.fields!.find(f => f.key === 'hospitalization');
    expect(hospFieldContra).toBeDefined();
    expect(hospFieldContra?.value).toBe('Yes (Hospitalized)');

    const admDateFieldContra = rxSecContra!.fields!.find(f => f.key === 'hospitalAdmissionDate');
    expect(admDateFieldContra).toBeDefined();
    expect(admDateFieldContra?.value).toBe('10-NOV-2025');

    const medImpFieldContra = rxSecContra!.fields!.find(f => f.key === 'medicallyImportant');
    expect(medImpFieldContra).toBeDefined();
    expect(medImpFieldContra?.value).toBe('Yes (Medically Important)');

    const factHospContra = briefContra.facts.find(f => f.field === 'hospitalization');
    expect(factHospContra?.value).toBe('Yes (Hospitalized)');

    // 2. Consistent false: hospitalization_val=false with no hospitalization criteria
    const caseConsistentFalse: IntakeMessage = {
      ...baseMessage,
      messageId: 'msg-hosp-false',
      primaryCategory: 'Safety Report (ICSR)',
      icsrReport: {
        ...baseMessage.icsrReport!,
        adverseEvent: 'Mild Rash',
        seriousnessCriteria: 'Medically Significant',
        sourceCitationsJson: JSON.stringify({
          hospitalization_val: false,
          medically_important_val: true
        })
      }
    };

    const briefFalse = ReviewerBriefBuilder.buildFromMessage(caseConsistentFalse);
    const rxSecFalse = briefFalse.sections?.find(s => s.key === 'reaction');
    const hospFieldFalse = rxSecFalse!.fields!.find(f => f.key === 'hospitalization');
    expect(hospFieldFalse).toBeDefined();
    expect(hospFieldFalse?.value).toBe('No');

    // 3. Case 009 canonical verification
    const case009: IntakeMessage = {
      ...baseMessage,
      messageId: 'msg-case-009',
      primaryCategory: 'Safety Report (ICSR)',
      icsrReport: {
        ...baseMessage.icsrReport!,
        adverseEvent: 'Acute Drug-Induced Liver Injury',
        seriousnessCriteria: 'Hospitalization, Medically Significant',
        sourceCitationsJson: JSON.stringify({
          hospitalization_val: true,
          hospital_admission_date_val: '10-NOV-2025',
          medically_important_val: true
        })
      }
    };

    const brief009 = ReviewerBriefBuilder.buildFromMessage(case009);
    const rxSec009 = brief009.sections?.find(s => s.key === 'reaction');
    expect(rxSec009!.fields!.find(f => f.key === 'hospitalization')?.value).toBe('Yes (Hospitalized)');
    expect(rxSec009!.fields!.find(f => f.key === 'hospitalAdmissionDate')?.value).toBe('10-NOV-2025');
    expect(rxSec009!.fields!.find(f => f.key === 'medicallyImportant')?.value).toBe('Yes (Medically Important)');
  });

  // =========================================================================
  // ROOT CAUSE 3: EVIDENCE CITATION KEY MISMATCH & LOOKUP BOUNDARY
  // =========================================================================
  describe('Root Cause 3: Citation Key Normalization & Provenance Safety', () => {
    it('1. camelCase datum key + snake_case citation -> correct citation returned', () => {
      const citations = {
        patient_weight: {
          source_type: 'pdf',
          source_id: 'cioms_form_MK_Cardioril.pdf',
          source_name: 'cioms_form_MK_Cardioril.pdf',
          page_number: 1,
          bounding_box: { x0: 450.0, y0: 92.44, x1: 502.91, y1: 113.39, page_number: 1 },
          verbatim_snippet: '3a. WEIGHT\n68 kg (150 lbs)',
          anchor_level: 'LEVEL_1_EXACT_VISUAL' as const
        }
      };

      const result = ReviewerBriefBuilder.lookupCitation(citations, 'patientWeight');
      expect(result).toBeDefined();
      expect(result?.source_id).toBe('cioms_form_MK_Cardioril.pdf');
      expect(result?.page_number).toBe(1);
      expect(result?.bounding_box).toEqual({ x0: 450.0, y0: 92.44, x1: 502.91, y1: 113.39, page_number: 1 });
    });

    it('2. snake_case datum key + snake_case citation -> correct citation returned', () => {
      const citations = {
        patient_weight: {
          source_type: 'pdf',
          source_id: 'cioms_form_MK_Cardioril.pdf',
          page_number: 1,
          verbatim_snippet: '3a. WEIGHT\n68 kg (150 lbs)'
        }
      };

      const result = ReviewerBriefBuilder.lookupCitation(citations, 'patient_weight');
      expect(result).toBeDefined();
      expect(result?.source_id).toBe('cioms_form_MK_Cardioril.pdf');
    });

    it('3. exact key exists -> exact key wins', () => {
      const citations = {
        patientWeight: {
          source_type: 'pdf',
          source_id: 'exact_key_doc.pdf',
          page_number: 2
        },
        patient_weight: {
          source_type: 'pdf',
          source_id: 'snake_key_doc.pdf',
          page_number: 1
        }
      };

      const result = ReviewerBriefBuilder.lookupCitation(citations, 'patientWeight');
      expect(result).toBeDefined();
      expect(result?.source_id).toBe('exact_key_doc.pdf');
      expect(result?.page_number).toBe(2);
    });

    it('4. requested specific citation missing -> DO NOT fall back to unrelated parent citation', () => {
      const msg: IntakeMessage = {
        ...baseMessage,
        icsrReport: {
          ...baseMessage.icsrReport!,
          patientWeight: '68 kg (150 lbs)',
          sourceCitationsJson: JSON.stringify({
            patient: {
              source_type: 'email',
              source_id: 'imap_9.eml',
              verbatim_snippet: 'Patient M.K., 58 yo female under my care with DILI'
            }
          })
        }
      };

      const brief = ReviewerBriefBuilder.buildFromMessage(msg);
      const ptSection = brief.sections?.find(s => s.key === 'patient');
      const wtField = ptSection?.fields?.find(f => f.key === 'patientWeight');
      const wtFact = brief.facts.find(f => f.field === 'patientWeight');

      // Crucial provenance safety: weight must NOT adopt unrelated parent patient email snippet
      expect(wtField?.evidence).toBeUndefined();
      expect(wtFact?.evidence).toBeUndefined();
    });

    it('5. PDF citation retains: source type, source ID, source name, page number, bounding box, snippet, anchor level', () => {
      const cit = {
        source_type: 'pdf',
        source_id: 'cioms_form_MK_Cardioril.pdf',
        source_name: 'cioms_form_MK_Cardioril.pdf',
        page_number: 1,
        page_or_location: 'Page 1, Box 3a',
        verbatim_snippet: '3a. WEIGHT\n68 kg (150 lbs)',
        bounding_box: { x0: 450.0, y0: 92.44, x1: 502.91, y1: 113.39, page_number: 1 },
        anchor_level: 'LEVEL_1_EXACT_VISUAL' as const,
        verification_result: 'SUPPORTS' as const,
        verification_rationale: 'Exact visual match in Box 3a'
      };

      const ev = ReviewerBriefBuilder.toEvidenceRef(cit);
      expect(ev.sourceType).toBe('pdf');
      expect(ev.sourceId).toBe('cioms_form_MK_Cardioril.pdf');
      expect(ev.sourceName).toBe('cioms_form_MK_Cardioril.pdf');
      expect(ev.pageNumber).toBe(1);
      expect(ev.boundingBox).toEqual({ x0: 450.0, y0: 92.44, x1: 502.91, y1: 113.39, page_number: 1 });
      expect(ev.snippet).toBe('3a. WEIGHT\n68 kg (150 lbs)');
      expect(ev.anchorLevel).toBe('LEVEL_1_EXACT_VISUAL');
    });

    it('6. Email citation still works with char_start/char_end', () => {
      const cit = {
        source_type: 'email',
        source_id: 'email_01.eml',
        source_name: 'email_01.eml',
        page_or_location: 'Email Body, Paragraph 1',
        verbatim_snippet: 'Patient developed acute drug-induced liver injury',
        char_start: 120,
        char_end: 168
      };

      const ev = ReviewerBriefBuilder.toEvidenceRef(cit);
      expect(ev.sourceType).toBe('email');
      expect(ev.charStart).toBe(120);
      expect(ev.charEnd).toBe(168);
      expect(ev.anchorLevel).toBe('LEVEL_1_EXACT_VISUAL');
    });

    it('7. Existing unrelated facts remain unaffected', () => {
      const msg: IntakeMessage = {
        ...baseMessage,
        icsrReport: {
          ...baseMessage.icsrReport!,
          patientAge: '58 years',
          patientWeight: '68 kg (150 lbs)',
          sourceCitationsJson: JSON.stringify({
            patient_weight: {
              source_type: 'pdf',
              source_id: 'cioms_form_MK_Cardioril.pdf',
              page_number: 1,
              bounding_box: { x0: 450.0, y0: 92.44, x1: 502.91, y1: 113.39, page_number: 1 },
              verbatim_snippet: '3a. WEIGHT 68 kg (150 lbs)'
            },
            patient_age: {
              source_type: 'pdf',
              source_id: 'cioms_form_MK_Cardioril.pdf',
              page_number: 1,
              bounding_box: { x0: 300.0, y0: 92.44, x1: 330.68, y1: 113.39, page_number: 1 },
              verbatim_snippet: '2a. AGE 58 YRS'
            }
          })
        }
      };

      const brief = ReviewerBriefBuilder.buildFromMessage(msg);
      const ptSection = brief.sections?.find(s => s.key === 'patient');
      const wtField = ptSection?.fields?.find(f => f.key === 'patientWeight');
      const ageField = ptSection?.fields?.find(f => f.key === 'patientAge');

      expect(wtField?.evidence?.sourceId).toBe('cioms_form_MK_Cardioril.pdf');
      expect(wtField?.evidence?.boundingBox?.x0).toBe(450.0);
      expect(ageField?.evidence?.sourceId).toBe('cioms_form_MK_Cardioril.pdf');
      expect(ageField?.evidence?.boundingBox?.x0).toBe(300.0);
    });
  });

  // =========================================================================
  // ROOT CAUSE 4: NOT_STATED VALUES MUST NOT RECEIVE UNRELATED EVIDENCE
  // =========================================================================
  describe('Root Cause 4: NOT_STATED Values Must Not Receive Unrelated Evidence', () => {
    it('1. NOT_STATED field + unrelated parent citation -> evidence undefined', () => {
      const msg: IntakeMessage = {
        ...baseMessage,
        icsrReport: {
          ...baseMessage.icsrReport!,
          rechallenge: 'Not stated',
          sourceCitationsJson: JSON.stringify({
            reaction: {
              source_type: 'pdf',
              source_id: 'hospital_admission_note.pdf',
              page_number: 1,
              verbatim_snippet: 'Acute dyspnea and tachycardia documented by ICU attending'
            }
          })
        }
      };

      const brief = ReviewerBriefBuilder.buildFromMessage(msg);
      const rxSection = brief.sections?.find(s => s.key === 'reaction');
      const rechallengeField = rxSection?.fields?.find(f => f.key === 'rechallenge');
      const rechallengeFact = brief.facts.find(f => f.field === 'rechallenge');

      expect(rechallengeField).toBeDefined();
      expect(rechallengeField?.value).toBe('Not stated');
      expect(rechallengeField?.status).toBe('NOT_STATED');
      // Must NOT inherit parent reaction citation!
      expect(rechallengeField?.evidence).toBeUndefined();
      expect(rechallengeFact?.evidence).toBeUndefined();
    });

    it('2. NOT_STATED field + no citation -> evidence undefined', () => {
      const msg: IntakeMessage = {
        ...baseMessage,
        icsrReport: {
          ...baseMessage.icsrReport!,
          rechallenge: 'Not stated',
          sourceCitationsJson: JSON.stringify({})
        }
      };

      const brief = ReviewerBriefBuilder.buildFromMessage(msg);
      const rxSection = brief.sections?.find(s => s.key === 'reaction');
      const rechallengeField = rxSection?.fields?.find(f => f.key === 'rechallenge');
      const rechallengeFact = brief.facts.find(f => f.field === 'rechallenge');

      expect(rechallengeField).toBeDefined();
      expect(rechallengeField?.value).toBe('Not stated');
      expect(rechallengeField?.status).toBe('NOT_STATED');
      expect(rechallengeField?.evidence).toBeUndefined();
      expect(rechallengeFact?.evidence).toBeUndefined();
    });

    it('3. CONFIRMED field + matching field citation -> evidence preserved', () => {
      const msg: IntakeMessage = {
        ...baseMessage,
        icsrReport: {
          ...baseMessage.icsrReport!,
          patientWeight: '68 kg (150 lbs)',
          sourceCitationsJson: JSON.stringify({
            patient_weight: {
              source_type: 'pdf',
              source_id: 'cioms_form_MK_Cardioril.pdf',
              source_name: 'cioms_form_MK_Cardioril.pdf',
              page_number: 1,
              bounding_box: { x0: 450.0, y0: 92.44, x1: 502.91, y1: 113.39, page_number: 1 },
              verbatim_snippet: '3a. WEIGHT\n68 kg (150 lbs)',
              anchor_level: 'LEVEL_1_EXACT_VISUAL'
            }
          })
        }
      };

      const brief = ReviewerBriefBuilder.buildFromMessage(msg);
      const ptSection = brief.sections?.find(s => s.key === 'patient');
      const wtField = ptSection?.fields?.find(f => f.key === 'patientWeight');
      const wtFact = brief.facts.find(f => f.field === 'patientWeight');

      expect(wtField).toBeDefined();
      expect(wtField?.status).toBe('CONFIRMED');
      expect(wtField?.evidence).toBeDefined();
      expect(wtField?.evidence?.sourceId).toBe('cioms_form_MK_Cardioril.pdf');
      expect(wtField?.evidence?.boundingBox?.x0).toBe(450.0);
      expect(wtField?.evidence?.anchorLevel).toBe('LEVEL_1_EXACT_VISUAL');

      expect(wtFact?.evidence).toBeDefined();
      expect(wtFact?.evidence?.sourceId).toBe('cioms_form_MK_Cardioril.pdf');
    });

    it('4. CONFIRMED field + valid parent citation that actually contains/supports the datum -> only preserve if semantically supported', () => {
      const msg: IntakeMessage = {
        ...baseMessage,
        icsrReport: {
          ...baseMessage.icsrReport!,
          patientAge: '58 years',
          patientWeight: '68 kg (150 lbs)',
          sourceCitationsJson: JSON.stringify({
            patient: {
              source_type: 'email',
              source_id: 'imap_9.eml',
              verbatim_snippet: 'Patient M.K., 58 yo female under my care with DILI'
            }
          })
        }
      };

      const brief = ReviewerBriefBuilder.buildFromMessage(msg);
      const ptSection = brief.sections?.find(s => s.key === 'patient');
      const ageField = ptSection?.fields?.find(f => f.key === 'patientAge');
      const wtField = ptSection?.fields?.find(f => f.key === 'patientWeight');

      // Age is in the parent snippet ('58 yo') -> semantically supported and preserved
      expect(ageField?.evidence).toBeDefined();
      expect(ageField?.evidence?.snippet).toContain('58 yo female');

      // Weight ('68 kg') is NOT in the parent snippet -> unsupported, must remain undefined!
      expect(wtField?.evidence).toBeUndefined();
    });

    it('5. Existing PDF and email evidence behavior remains unchanged', () => {
      const msg: IntakeMessage = {
        ...baseMessage,
        icsrReport: {
          ...baseMessage.icsrReport!,
          patientWeight: '68 kg (150 lbs)',
          reporterName: 'Dr. Sarah Jenkins',
          sourceCitationsJson: JSON.stringify({
            patient_weight: {
              source_type: 'pdf',
              source_id: 'cioms_form_MK_Cardioril.pdf',
              page_number: 1,
              bounding_box: { x0: 450.0, y0: 92.44, x1: 502.91, y1: 113.39, page_number: 1 },
              verbatim_snippet: '3a. WEIGHT: 68 kg (150 lbs)',
              anchor_level: 'LEVEL_1_EXACT_VISUAL'
            },
            reporter_name: {
              source_type: 'email',
              source_id: 'imap_9.eml',
              char_start: 32,
              char_end: 49,
              verbatim_snippet: 'Dr. Sarah Jenkins',
              anchor_level: 'LEVEL_1_EXACT_VISUAL'
            }
          })
        }
      };

      const brief = ReviewerBriefBuilder.buildFromMessage(msg);
      const ptSection = brief.sections?.find(s => s.key === 'patient');
      const repSection = brief.sections?.find(s => s.key === 'reporter');

      const wtField = ptSection?.fields?.find(f => f.key === 'patientWeight');
      const repField = repSection?.fields?.find(f => f.key === 'reporterName');

      // PDF Level-1 bounding box preserved intact
      expect(wtField?.evidence?.sourceType).toBe('pdf');
      expect(wtField?.evidence?.pageNumber).toBe(1);
      expect(wtField?.evidence?.boundingBox).toEqual({ x0: 450.0, y0: 92.44, x1: 502.91, y1: 113.39, page_number: 1 });
      expect(wtField?.evidence?.anchorLevel).toBe('LEVEL_1_EXACT_VISUAL');

      // Email Level-1 character offsets preserved intact
      expect(repField?.evidence?.sourceType).toBe('email');
      expect(repField?.evidence?.charStart).toBe(32);
      expect(repField?.evidence?.charEnd).toBe(49);
      expect(repField?.evidence?.anchorLevel).toBe('LEVEL_1_EXACT_VISUAL');
    });

    it('6. NOT_STATED field with specific legitimate negative citation -> evidence preserved', () => {
      const msg: IntakeMessage = {
        ...baseMessage,
        icsrReport: {
          ...baseMessage.icsrReport!,
          rechallenge: 'Not stated',
          sourceCitationsJson: JSON.stringify({
            rechallenge: {
              source_type: 'pdf',
              source_id: 'cioms_form_MK_Cardioril.pdf',
              page_number: 1,
              verbatim_snippet: '23. RECHALLENGE: Not done (rechallenge was not performed due to hepatotoxicity)'
            }
          })
        }
      };

      const brief = ReviewerBriefBuilder.buildFromMessage(msg);
      const rxSection = brief.sections?.find(s => s.key === 'reaction');
      const rechallengeField = rxSection?.fields?.find(f => f.key === 'rechallenge');

      expect(rechallengeField).toBeDefined();
      expect(rechallengeField?.value).toBe('Not stated');
      expect(rechallengeField?.status).toBe('NOT_STATED');
      // Because snippet specifically states rechallenge was not done/performed, legitimate evidence is preserved
      expect(rechallengeField?.evidence).toBeDefined();
      expect(rechallengeField?.evidence?.snippet).toContain('rechallenge was not performed');
    });
  });

  describe('Medical Information (MI) Evidence & Source Citation Propagation', () => {
    const miMessage: IntakeMessage = {
      id: 29,
      messageId: 'msg-mi-029',
      sender: 'David Wu, PharmD, BCPS',
      senderEmail: 'david.wu@ucsf-clinical.edu',
      subject: 'Medical Information Request: Can Corzapan 10mg tablets be crushed for NG-tube administration?',
      receivedDate: '2025-11-19 13:40:00',
      sourceFilename: 'email_09.eml',
      rawBody: [
        'Dear Medical Information Department,',
        'I am a clinical oncology pharmacist at UCSF Medical Center caring for an elderly patient with severe dysphagia who has an active nasogastric (NG) feeding tube in place.',
        'The patient has been prescribed Corzapan 10mg once daily for chronic hypertension. The package insert indicates film-coated tablets but does not explicitly state whether the tablets can be crushed and suspended in sterile water for enteral feeding tube delivery without altering bioavailability or causing tube occlusion.',
        'Could your medical affairs team please provide any pharmacokinetic or stability data regarding:',
        '1. Crushing Corzapan 10mg tablets for enteral administration.',
        '2. Potential adsorption of the active substance to polyurethane enteral feeding tubes.',
        '3. Co-administration with enteral nutrition formulas.',
        'There is currently no patient adverse event or product defect. This is purely a prospective clinical inquiry.',
        'Best regards,',
        'David Wu, PharmD, BCPS'
      ].join('\n\n'),
      status: 'TRIAGED',
      primaryCategory: 'Medical Information (MI)',
      confidence: 0.98,
      isMultiLabel: false,
      createdAt: '2025-11-19T13:40:00Z',
      updatedAt: '2025-11-19T13:45:00Z',
      medicalInfo: {
        productOrTopic: 'Corzapan 10mg',
        inquiryType: 'Enteral Administration / Crushing',
        questionText: 'Can Corzapan 10mg tablets be crushed for NG-tube administration?',
        clinicalContext: 'Elderly patient with severe dysphagia prescribed Corzapan 10mg once daily, active nasogastric (NG) enteral feeding tube',
        sourceCitationsJson: JSON.stringify({
          mi_product_or_topic: {
            source_type: 'email',
            page_or_location: 'Email Body, Paragraph 2',
            verbatim_snippet: 'The patient has been prescribed Corzapan 10mg once daily for chronic hypertension.',
            source_id: 'email_09.eml',
            char_start: 180,
            char_end: 260,
            anchor_level: 'LEVEL_1_EXACT_VISUAL',
            verification_result: 'SUPPORTS'
          },
          mi_inquiry_type: {
            source_type: 'email',
            page_or_location: 'Email Body, Paragraph 3',
            verbatim_snippet: 'Crushing Corzapan 10mg tablets for enteral administration.',
            source_id: 'email_09.eml',
            anchor_level: 'LEVEL_1_EXACT_VISUAL',
            verification_result: 'SUPPORTS'
          },
          mi_clinical_context: {
            source_type: 'email',
            page_or_location: 'Email Body, Paragraph 1',
            verbatim_snippet: 'elderly patient with severe dysphagia who has an active nasogastric (NG) feeding tube in place.',
            source_id: 'email_09.eml',
            anchor_level: 'LEVEL_1_EXACT_VISUAL',
            verification_result: 'SUPPORTS'
          },
          question_1: {
            source_type: 'email',
            page_or_location: 'Email Body, Question 1',
            verbatim_snippet: 'Crushing Corzapan 10mg tablets for enteral administration.',
            source_id: 'email_09.eml',
            anchor_level: 'LEVEL_1_EXACT_VISUAL',
            verification_result: 'SUPPORTS'
          }
        })
      },
      attachments: []
    };

    it('1. MI fact with direct email citation -> evidence is preserved in brief facts', () => {
      const brief = ReviewerBriefBuilder.buildFromMessage(miMessage);

      const prodFact = brief.facts.find(f => f.field === 'miProduct');
      expect(prodFact).toBeDefined();
      expect(prodFact?.value).toBe('Corzapan 10mg');
      expect(prodFact?.status).toBe('CONFIRMED');
      expect(prodFact?.evidence).toBeDefined();
      expect(prodFact?.evidence?.sourceType).toBe('email');
      expect(prodFact?.evidence?.snippet).toContain('Corzapan 10mg');
      expect(prodFact?.evidence?.charStart).toBe(180);

      const inqTypeFact = brief.facts.find(f => f.field === 'inquiryType');
      expect(inqTypeFact).toBeDefined();
      expect(inqTypeFact?.evidence).toBeDefined();
      expect(inqTypeFact?.evidence?.snippet).toContain('Crushing Corzapan 10mg');

      const ctxFact = brief.facts.find(f => f.field === 'clinicalContext');
      expect(ctxFact).toBeDefined();
      expect(ctxFact?.evidence).toBeDefined();
      expect(ctxFact?.evidence?.snippet).toContain('dysphagia');
    });

    it('2. MI question with direct email citation -> evidence is preserved in dossier questions table', () => {
      const brief = ReviewerBriefBuilder.buildFromMessage(miMessage);

      const questionsSection = brief.sections?.find(s => s.key === 'mi_questions');
      expect(questionsSection).toBeDefined();
      expect(questionsSection?.repeatedGroup).toBeDefined();

      const rows = questionsSection!.repeatedGroup!.rows;
      expect(rows.length).toBeGreaterThan(0);

      // Question 1 has explicit question_1 citation from evidence model
      const q1 = rows[0];
      expect(q1.evidence).toBeDefined();
      expect(q1.evidence?.sourceType).toBe('email');
      expect(q1.evidence?.snippet).toContain('Crushing Corzapan 10mg');
    });

    it('3. MI question without explicit citation exact-matches against source email body', () => {
      // Message with questions in questionText that are present in rawBody, but without question_2 / question_3 citations in JSON
      const msg: IntakeMessage = {
        ...miMessage,
        medicalInfo: {
          ...miMessage.medicalInfo!,
          questionText: [
            '1. Crushing Corzapan 10mg tablets for enteral administration.',
            '2. Potential adsorption of the active substance to polyurethane enteral feeding tubes.',
            '3. Co-administration with enteral nutrition formulas.'
          ].join('\n'),
          sourceCitationsJson: JSON.stringify({}) // Empty citation map
        }
      };

      const brief = ReviewerBriefBuilder.buildFromMessage(msg);
      const questionsSection = brief.sections?.find(s => s.key === 'mi_questions');
      expect(questionsSection).toBeDefined();

      const rows = questionsSection!.repeatedGroup!.rows;
      expect(rows.length).toBe(3);

      // All 3 questions exist verbatim in rawBody -> grounded with exact character offsets
      for (const row of rows) {
        expect(row.evidence).toBeDefined();
        expect(row.evidence?.sourceType).toBe('email');
        expect(row.evidence?.anchorLevel).toBe('LEVEL_1_EXACT_VISUAL');
        expect(row.evidence?.charStart).toBeGreaterThanOrEqual(0);
        expect(row.evidence?.charEnd).toBeGreaterThan(row.evidence!.charStart!);
        // Matched text in rawBody matches verbatim snippet
        const matchedText = msg.rawBody!.substring(row.evidence!.charStart!, row.evidence!.charEnd!);
        expect(matchedText.toLowerCase()).toBe(row.evidence!.snippet!.toLowerCase());
      }
    });

    it('4. MI question genuinely missing from source email body remains WITHOUT evidence', () => {
      const msg: IntakeMessage = {
        ...miMessage,
        medicalInfo: {
          ...miMessage.medicalInfo!,
          // Fabricated / hallucinated question not present in rawBody
          questionText: 'Can Corzapan be safely mixed with orange juice for pediatric administration?',
          sourceCitationsJson: JSON.stringify({})
        }
      };

      const brief = ReviewerBriefBuilder.buildFromMessage(msg);
      const questionsSection = brief.sections?.find(s => s.key === 'mi_questions');
      expect(questionsSection).toBeDefined();

      const rows = questionsSection!.repeatedGroup!.rows;
      expect(rows.length).toBe(1);

      // Never fabricate a citation when question is absent from source
      expect(rows[0].evidence).toBeUndefined();
    });

    it('5. MI unstated fact remains without evidence (NOT_STATED provenance safety)', () => {
      const msg: IntakeMessage = {
        ...miMessage,
        medicalInfo: {
          ...miMessage.medicalInfo!,
          productOrTopic: 'Not stated',
          inquiryType: 'Not stated',
          // Unrelated parent citation present in sourceCitationsJson
          sourceCitationsJson: JSON.stringify({
            medical_info: {
              source_type: 'email',
              verbatim_snippet: 'General email discussion without product details.'
            }
          })
        }
      };

      const brief = ReviewerBriefBuilder.buildFromMessage(msg);
      const prodFact = brief.facts.find(f => f.field === 'miProduct');
      expect(prodFact).toBeDefined();
      expect(prodFact?.status).toBe('NOT_STATED');
      // Unstated fact must NOT inherit parent citation
      expect(prodFact?.evidence).toBeUndefined();
    });

    it('6. Existing ICSR and PQC evidence behavior remains completely intact', () => {
      const icsrBrief = ReviewerBriefBuilder.buildFromMessage(baseMessage);
      const patientFact = icsrBrief.facts.find(f => f.field === 'patientIdentifier');
      expect(patientFact?.evidence).toBeDefined();
      expect(patientFact?.evidence?.sourceType).toBe('pdf');

      const pqcMessage: IntakeMessage = {
        id: 2,
        messageId: 'msg-pqc-002',
        sender: 'Nurse practitioner',
        senderEmail: 'nurse@clinic.org',
        subject: 'Defective Blister Pack',
        receivedDate: '2026-03-02 10:00:00',
        rawBody: 'Found cracked blister seal on Lot #BL-8802.',
        status: 'TRIAGED',
        primaryCategory: 'Quality Complaint (PQC)',
        confidence: 0.99,
        isMultiLabel: false,
        createdAt: '2026-03-02T10:00:00Z',
        updatedAt: '2026-03-02T10:00:00Z',
        attachments: [],
        pqcReport: {
          productName: 'Cardioril 10mg',
          lotNumber: 'BL-8802',
          defectType: 'Defective Blister Seal',
          defectDescription: 'Aluminum foil unsealed along top margin',
          packagingBreached: true,
          photoDetected: false,
          photoDescription: 'No photo provided',
          requiresHumanReview: false,
          sourceCitationsJson: JSON.stringify({
            pqcProduct: { source_type: 'email', verbatim_snippet: 'Cardioril 10mg blister' },
            pqcLot: { source_type: 'email', verbatim_snippet: 'Lot #BL-8802' }
          })
        }
      };

      const pqcBrief = ReviewerBriefBuilder.buildFromMessage(pqcMessage);
      const lotFact = pqcBrief.facts.find(f => f.field === 'pqcLot');
      expect(lotFact?.evidence).toBeDefined();
      expect(lotFact?.evidence?.snippet).toContain('BL-8802');
    });
  });

  describe('Priority 1: Health Professional & Reporter Qualification mapping', () => {
    it('1. health_professional = "No" -> displays "No" in both Fact Ledger and Overview Grid', () => {
      const msg: IntakeMessage = {
        ...baseMessage,
        icsrReport: {
          ...baseMessage.icsrReport!,
          reporterName: 'Emily Watson',
          reporterRole: 'Consumer / Patient',
          sourceCitationsJson: JSON.stringify({
            health_professional_val: 'No',
            health_professional: { source_type: 'email', verbatim_snippet: 'From: Emily Watson' }
          })
        }
      };

      const brief = ReviewerBriefBuilder.buildFromMessage(msg);

      // Fact Ledger check
      const hcpFact = brief.facts.find(f => f.field === 'healthProfessional');
      expect(hcpFact).toBeDefined();
      expect(hcpFact?.value).toBe('No');

      // Overview Grid check
      const reporterSection = brief.sections.find(s => s.key === 'reporter');
      const hcpField = reporterSection?.fields?.find(f => f.key === 'healthProfessional');
      expect(hcpField).toBeDefined();
      expect(hcpField?.value).toBe('No');

      // Unrelated reporter fields preserved
      const roleField = reporterSection?.fields?.find(f => f.key === 'reporterRole');
      expect(roleField?.value).toBe('Consumer / Patient');
      const nameField = reporterSection?.fields?.find(f => f.key === 'reporterName');
      expect(nameField?.value).toBe('Emily Watson');
    });

    it('2. health_professional = "Yes" -> displays "Yes (HCP Confirmed)" in both Fact Ledger and Overview Grid', () => {
      const msg: IntakeMessage = {
        ...baseMessage,
        icsrReport: {
          ...baseMessage.icsrReport!,
          reporterName: 'Dr. Sarah Jenkins',
          reporterRole: 'Physician',
          sourceCitationsJson: JSON.stringify({
            health_professional_val: 'Yes'
          })
        }
      };

      const brief = ReviewerBriefBuilder.buildFromMessage(msg);
      const hcpFact = brief.facts.find(f => f.field === 'healthProfessional');
      expect(hcpFact?.value).toBe('Yes (HCP Confirmed)');

      const reporterSection = brief.sections.find(s => s.key === 'reporter');
      const hcpField = reporterSection?.fields?.find(f => f.key === 'healthProfessional');
      expect(hcpField?.value).toBe('Yes (HCP Confirmed)');
    });

    it('3. health_professional = true (boolean) -> displays "Yes (HCP Confirmed)"', () => {
      const msg: IntakeMessage = {
        ...baseMessage,
        icsrReport: {
          ...baseMessage.icsrReport!,
          sourceCitationsJson: JSON.stringify({
            health_professional_val: true
          })
        }
      };

      const brief = ReviewerBriefBuilder.buildFromMessage(msg);
      const hcpFact = brief.facts.find(f => f.field === 'healthProfessional');
      expect(hcpFact?.value).toBe('Yes (HCP Confirmed)');

      const reporterSection = brief.sections.find(s => s.key === 'reporter');
      const hcpField = reporterSection?.fields?.find(f => f.key === 'healthProfessional');
      expect(hcpField?.value).toBe('Yes (HCP Confirmed)');
    });

    it('4. health_professional = false (boolean) -> displays "No"', () => {
      const msg: IntakeMessage = {
        ...baseMessage,
        icsrReport: {
          ...baseMessage.icsrReport!,
          sourceCitationsJson: JSON.stringify({
            health_professional_val: false
          })
        }
      };

      const brief = ReviewerBriefBuilder.buildFromMessage(msg);
      const hcpFact = brief.facts.find(f => f.field === 'healthProfessional');
      expect(hcpFact?.value).toBe('No');

      const reporterSection = brief.sections.find(s => s.key === 'reporter');
      const hcpField = reporterSection?.fields?.find(f => f.key === 'healthProfessional');
      expect(hcpField?.value).toBe('No');
    });

    it('5. missing / null / undefined -> preserves intended fallback behavior (field omitted)', () => {
      // 5a. undefined (missing from citations)
      const msgUndefined: IntakeMessage = {
        ...baseMessage,
        icsrReport: {
          ...baseMessage.icsrReport!,
          sourceCitationsJson: JSON.stringify({})
        }
      };
      const briefUndefined = ReviewerBriefBuilder.buildFromMessage(msgUndefined);
      expect(briefUndefined.facts.find(f => f.field === 'healthProfessional')).toBeUndefined();
      const repSecUndefined = briefUndefined.sections.find(s => s.key === 'reporter');
      expect(repSecUndefined?.fields?.find(f => f.key === 'healthProfessional')).toBeUndefined();

      // 5b. null
      const msgNull: IntakeMessage = {
        ...baseMessage,
        icsrReport: {
          ...baseMessage.icsrReport!,
          sourceCitationsJson: JSON.stringify({
            health_professional_val: null
          })
        }
      };
      const briefNull = ReviewerBriefBuilder.buildFromMessage(msgNull);
      expect(briefNull.facts.find(f => f.field === 'healthProfessional')).toBeUndefined();
      const repSecNull = briefNull.sections.find(s => s.key === 'reporter');
      expect(repSecNull?.fields?.find(f => f.key === 'healthProfessional')).toBeUndefined();
    });

    it('6. existing genuine physician cases (CASE-02 / CASE-04) remain "Yes (HCP Confirmed)"', () => {
      // Case-02 style
      const msgCase2: IntakeMessage = {
        ...baseMessage,
        id: 2,
        sender: 'Dr. med. Hans Becker',
        icsrReport: {
          ...baseMessage.icsrReport!,
          reporterName: 'Dr. med. Hans Becker',
          reporterRole: 'Physician',
          reporterInstitution: 'Universitätsklinikum Freiburg',
          sourceCitationsJson: JSON.stringify({
            health_professional_val: 'Yes'
          })
        }
      };
      const briefCase2 = ReviewerBriefBuilder.buildFromMessage(msgCase2);
      const hcpFact2 = briefCase2.facts.find(f => f.field === 'healthProfessional');
      expect(hcpFact2?.value).toBe('Yes (HCP Confirmed)');
      const hcpField2 = briefCase2.sections.find(s => s.key === 'reporter')?.fields?.find(f => f.key === 'healthProfessional');
      expect(hcpField2?.value).toBe('Yes (HCP Confirmed)');

      // Case-04 style
      const msgCase4: IntakeMessage = {
        ...baseMessage,
        id: 4,
        sender: 'Dr. Michael Vance, MD',
        icsrReport: {
          ...baseMessage.icsrReport!,
          reporterName: 'Dr. Michael Vance, MD',
          reporterRole: 'Physician',
          reporterInstitution: 'Northwestern Memorial Hospital',
          sourceCitationsJson: JSON.stringify({
            health_professional_val: 'YES'
          })
        }
      };
      const briefCase4 = ReviewerBriefBuilder.buildFromMessage(msgCase4);
      const hcpFact4 = briefCase4.facts.find(f => f.field === 'healthProfessional');
      expect(hcpFact4?.value).toBe('Yes (HCP Confirmed)');
      const hcpField4 = briefCase4.sections.find(s => s.key === 'reporter')?.fields?.find(f => f.key === 'healthProfessional');
      expect(hcpField4?.value).toBe('Yes (HCP Confirmed)');
    });

    it('7. formatHealthProfessional helper unit tests for all edge cases', () => {
      expect(ReviewerBriefBuilder.formatHealthProfessional('No')).toBe('No');
      expect(ReviewerBriefBuilder.formatHealthProfessional('NO')).toBe('No');
      expect(ReviewerBriefBuilder.formatHealthProfessional('no')).toBe('No');
      expect(ReviewerBriefBuilder.formatHealthProfessional(false)).toBe('No');
      expect(ReviewerBriefBuilder.formatHealthProfessional('false')).toBe('No');

      expect(ReviewerBriefBuilder.formatHealthProfessional('Yes')).toBe('Yes (HCP Confirmed)');
      expect(ReviewerBriefBuilder.formatHealthProfessional('YES')).toBe('Yes (HCP Confirmed)');
      expect(ReviewerBriefBuilder.formatHealthProfessional('yes')).toBe('Yes (HCP Confirmed)');
      expect(ReviewerBriefBuilder.formatHealthProfessional(true)).toBe('Yes (HCP Confirmed)');
      expect(ReviewerBriefBuilder.formatHealthProfessional('true')).toBe('Yes (HCP Confirmed)');
      expect(ReviewerBriefBuilder.formatHealthProfessional('confirmed')).toBe('Yes (HCP Confirmed)');

      expect(ReviewerBriefBuilder.formatHealthProfessional(undefined)).toBeUndefined();
      expect(ReviewerBriefBuilder.formatHealthProfessional(null)).toBeUndefined();
      expect(ReviewerBriefBuilder.formatHealthProfessional('Not stated')).toBeUndefined();
      expect(ReviewerBriefBuilder.formatHealthProfessional('')).toBeUndefined();
    });
  });

  describe('Priority 2: Concomitant Medication Table mapping (medication_name & dose_and_route)', () => {
    it('1. Real API contract: medication_name + dose_and_route correctly rendered in table rows', () => {
      const msg: IntakeMessage = {
        ...baseMessage,
        icsrReport: {
          ...baseMessage.icsrReport!,
          sourceCitationsJson: JSON.stringify({
            concomitant_medications: [
              {
                medication_name: 'Lisinopril',
                dose_and_route: '10 mg PO Daily',
                indication: 'Renal Protection',
                dates: '2024-ongoing',
                citation: { source_type: 'pdf', verbatim_snippet: 'Lisinopril 10 mg PO Daily' }
              }
            ]
          })
        }
      };

      const brief = ReviewerBriefBuilder.buildFromMessage(msg);
      const concomSec = brief.sections.find(s => s.key === 'concomitant_medications');
      expect(concomSec).toBeDefined();
      expect(concomSec?.repeatedGroup?.rows.length).toBe(1);
      const row = concomSec?.repeatedGroup?.rows[0];
      expect(row?.cells['drug_name']).toBe('Lisinopril');
      expect(row?.cells['dose_frequency']).toBe('10 mg PO Daily');
      expect(row?.cells['indication']).toBe('Renal Protection');
      expect(row?.cells['dates_of_administration']).toBe('2024-ongoing');
      expect(row?.evidence?.snippet).toBe('Lisinopril 10 mg PO Daily');
    });

    it('2. CASE-01 equivalent data: Metformin HCl and Amlodipine besylate render with complete doses, indications, and therapy dates', () => {
      const msgCase1: IntakeMessage = {
        ...baseMessage,
        id: 1,
        icsrReport: {
          ...baseMessage.icsrReport!,
          sourceCitationsJson: JSON.stringify({
            concomitant_medications: [
              {
                medication_name: 'Metformin HCl',
                dose_and_route: '500 mg PO BID',
                indication: 'Type 2 Diabetes Mellitus',
                dates: 'Start: 12-JAN-2021, Ongoing',
                citation: { source_type: 'pdf', verbatim_snippet: '1. Metformin HCl 500 mg PO BID (Indication: Type 2 Diabetes Mellitus; Start: 12-JAN-2021, Ongoing).' }
              },
              {
                medication_name: 'Amlodipine besylate',
                dose_and_route: '5 mg PO QD',
                indication: 'Hypertension',
                dates: 'Start: 05-MAR-2023, Ongoing',
                citation: { source_type: 'pdf', verbatim_snippet: '2. Amlodipine besylate 5 mg PO QD (Indication: Hypertension; Start: 05-MAR-2023, Ongoing).' }
              }
            ]
          })
        }
      };

      const brief = ReviewerBriefBuilder.buildFromMessage(msgCase1);
      const concomSec = brief.sections.find(s => s.key === 'concomitant_medications');
      expect(concomSec).toBeDefined();
      const rows = concomSec!.repeatedGroup!.rows;
      expect(rows.length).toBe(2);

      // Row 1: Metformin HCl
      expect(rows[0].cells['drug_name']).toBe('Metformin HCl');
      expect(rows[0].cells['dose_frequency']).toBe('500 mg PO BID');
      expect(rows[0].cells['indication']).toBe('Type 2 Diabetes Mellitus');
      expect(rows[0].cells['dates_of_administration']).toBe('Start: 12-JAN-2021, Ongoing');
      expect(rows[0].evidence?.snippet).toContain('Metformin HCl 500 mg');

      // Row 2: Amlodipine besylate
      expect(rows[1].cells['drug_name']).toBe('Amlodipine besylate');
      expect(rows[1].cells['dose_frequency']).toBe('5 mg PO QD');
      expect(rows[1].cells['indication']).toBe('Hypertension');
      expect(rows[1].cells['dates_of_administration']).toBe('Start: 05-MAR-2023, Ongoing');
      expect(rows[1].evidence?.snippet).toContain('Amlodipine besylate 5 mg');
    });

    it('3. Legacy mock contract: drug_name + dose_frequency + name fallback continues to work', () => {
      const msgLegacy: IntakeMessage = {
        ...baseMessage,
        icsrReport: {
          ...baseMessage.icsrReport!,
          sourceCitationsJson: JSON.stringify({
            concomitant_medications: [
              {
                drug_name: 'Atorvastatin',
                dose_frequency: '20 mg QD',
                indication: 'Hyperlipidemia',
                dates_of_administration: '2021-2025'
              },
              {
                name: 'Aspirin',
                dose: '81 mg daily',
                indication: 'Cardioprotection',
                dates: '2020-ongoing'
              }
            ]
          })
        }
      };

      const brief = ReviewerBriefBuilder.buildFromMessage(msgLegacy);
      const rows = brief.sections.find(s => s.key === 'concomitant_medications')!.repeatedGroup!.rows;
      expect(rows[0].cells['drug_name']).toBe('Atorvastatin');
      expect(rows[0].cells['dose_frequency']).toBe('20 mg QD');
      expect(rows[1].cells['drug_name']).toBe('Aspirin');
      expect(rows[1].cells['dose_frequency']).toBe('81 mg daily');
    });

    it('4. Genuine missing medication name still renders "Not stated"', () => {
      const msgMissing: IntakeMessage = {
        ...baseMessage,
        icsrReport: {
          ...baseMessage.icsrReport!,
          sourceCitationsJson: JSON.stringify({
            concomitant_medications: [
              {
                indication: 'Hypertension',
                dates: 'Start: 2022'
              }
            ]
          })
        }
      };

      const brief = ReviewerBriefBuilder.buildFromMessage(msgMissing);
      const rows = brief.sections.find(s => s.key === 'concomitant_medications')!.repeatedGroup!.rows;
      expect(rows[0].cells['drug_name']).toBe('Not stated');
      expect(rows[0].cells['dose_frequency']).toBe('Not stated');
      expect(rows[0].cells['indication']).toBe('Hypertension');
      expect(rows[0].cells['dates_of_administration']).toBe('Start: 2022');
    });

    it('5. CASE-04 concomitant medication (Norepinephrine) renders properly without regression', () => {
      const msgCase4: IntakeMessage = {
        ...baseMessage,
        id: 4,
        primaryCategory: 'Safety Report (ICSR)',
        isMultiLabel: true,
        icsrReport: {
          ...baseMessage.icsrReport!,
          sourceCitationsJson: JSON.stringify({
            concomitant_medications: [
              {
                medication_name: 'Norepinephrine',
                dose_and_route: 'Titrated to 0.14 mcg/kg/min, IV infusion',
                indication: 'Vasopressor therapy / Septic shock hemodynamic support',
                dates: '14-NOV-2025',
                status: 'Active',
                citation: { source_type: 'pdf', verbatim_snippet: 'Vasopressor therapy (Norepinephrine infusion titrated to 0.14 mcg/kg/min)' }
              }
            ]
          })
        }
      };

      const brief = ReviewerBriefBuilder.buildFromMessage(msgCase4);
      const concomSec = brief.sections.find(s => s.key === 'concomitant_medications');
      expect(concomSec).toBeDefined();
      const row = concomSec!.repeatedGroup!.rows[0];
      expect(row.cells['drug_name']).toBe('Norepinephrine');
      expect(row.cells['dose_frequency']).toBe('Titrated to 0.14 mcg/kg/min, IV infusion');
      expect(row.cells['indication']).toBe('Vasopressor therapy / Septic shock hemodynamic support');
      expect(row.cells['dates_of_administration']).toBe('14-NOV-2025');
    });
  });

  describe('Priority 4: Reviewer-Facing Confidence Rework', () => {
    it('1. Case-level triage confidence passes through correctly from triage score', () => {
      const msgTriage: IntakeMessage = {
        ...baseMessage,
        confidence: 0.96
      };
      const brief = ReviewerBriefBuilder.buildFromMessage(msgTriage);
      expect(brief.confidence).toBe(0.96);
    });

    it('2. CONFIRMED fact retains HIGH confidence and high numeric score', () => {
      const brief = ReviewerBriefBuilder.buildFromMessage(baseMessage);
      const confirmedFact = brief.facts.find(f => f.field === 'productName');
      expect(confirmedFact).toBeDefined();
      expect(confirmedFact?.status).toBe('CONFIRMED');
      expect(confirmedFact?.confidence).toBe('HIGH');
      expect(confirmedFact?.confidenceScore).toBe(0.98);
    });

    it('3. UNCERTAIN fact retains LOW confidence and low numeric score', () => {
      const msgUncertain: IntakeMessage = {
        ...baseMessage,
        facts: [
          {
            field: 'patientAge',
            label: 'Patient Age',
            value: '74? years',
            status: 'UNCERTAIN',
            confidence: 'LOW',
            section: 'PATIENT'
          }
        ]
      };
      const brief = ReviewerBriefBuilder.buildFromMessage(msgUncertain);
      const uncertainFact = brief.facts.find(f => f.field === 'patientAge');
      expect(uncertainFact).toBeDefined();
      expect(uncertainFact?.status).toBe('UNCERTAIN');
      expect(uncertainFact?.confidence).toBe('LOW');
      expect(uncertainFact?.confidenceScore).toBe(0.65);
    });

    it('4. NOT_STATED fact has undefined confidence and undefined confidenceScore (never HIGH / 1.0)', () => {
      const msgMissing: IntakeMessage = {
        ...baseMessage,
        icsrReport: {
          ...baseMessage.icsrReport!,
          productDose: 'Not stated',
          patientWeight: 'null',
          productExpiry: '-'
        }
      };
      const brief = ReviewerBriefBuilder.buildFromMessage(msgMissing);
      const missingDose = brief.facts.find(f => f.field === 'productDose');
      const missingWeight = brief.facts.find(f => f.field === 'patientWeight');
      const missingExpiry = brief.facts.find(f => f.field === 'productExpiry');

      expect(missingDose?.status).toBe('NOT_STATED');
      expect(missingDose?.confidence).toBeUndefined();
      expect(missingDose?.confidenceScore).toBeUndefined();

      expect(missingWeight?.status).toBe('NOT_STATED');
      expect(missingWeight?.confidence).toBeUndefined();
      expect(missingWeight?.confidenceScore).toBeUndefined();

      expect(missingExpiry?.status).toBe('NOT_STATED');
      expect(missingExpiry?.confidence).toBeUndefined();
      expect(missingExpiry?.confidenceScore).toBeUndefined();
    });

    it('5. PQC and MI unstated facts have undefined confidence and undefined confidenceScore', () => {
      const msgPqcMissing: IntakeMessage = {
        ...baseMessage,
        primaryCategory: 'Quality Complaint (PQC)',
        pqcReport: {
          productName: 'Cardioril',
          lotNumber: 'Not stated',
          defectType: 'Cracked vial',
          defectDescription: 'Not stated',
          packagingBreached: false,
          photoDetected: false,
          requiresHumanReview: false
        }
      };
      const brief = ReviewerBriefBuilder.buildFromMessage(msgPqcMissing);
      const missingLot = brief.facts.find(f => f.field === 'pqcLot');
      const missingDesc = brief.facts.find(f => f.field === 'defectDescription');

      expect(missingLot?.status).toBe('NOT_STATED');
      expect(missingLot?.confidence).toBeUndefined();
      expect(missingLot?.confidenceScore).toBeUndefined();

      expect(missingDesc?.status).toBe('NOT_STATED');
      expect(missingDesc?.confidence).toBeUndefined();
      expect(missingDesc?.confidenceScore).toBeUndefined();
    });

    it('6. CONFLICT fact retains existing conflict status and behavior', () => {
      const msgConflict: IntakeMessage = {
        ...baseMessage,
        facts: [
          {
            field: 'eventOnset',
            label: 'Reaction Onset Date',
            value: '2026-08-10 vs 2026-08-15',
            status: 'CONFLICT',
            confidence: 'HIGH',
            section: 'EVENT'
          }
        ]
      };
      const brief = ReviewerBriefBuilder.buildFromMessage(msgConflict);
      const conflictFact = brief.facts.find(f => f.field === 'eventOnset');
      expect(conflictFact).toBeDefined();
      expect(conflictFact?.status).toBe('CONFLICT');
      expect(brief.factStats.conflictCount).toBe(1);
    });

    it('7. formatFactStats dynamically renders counts omitting zero categories', () => {
      const summary1 = ReviewerBriefBuilder.formatFactStats({
        totalFacts: 27,
        confirmedCount: 22,
        notStatedCount: 4,
        uncertainCount: 1,
        conflictCount: 0
      });
      expect(summary1).toBe('22 Confirmed · 4 Not Stated · 1 Uncertain');

      const summary2 = ReviewerBriefBuilder.formatFactStats({
        totalFacts: 15,
        confirmedCount: 12,
        notStatedCount: 3,
        uncertainCount: 0,
        conflictCount: 0
      });
      expect(summary2).toBe('12 Confirmed · 3 Not Stated');

      const summaryWithConflict = ReviewerBriefBuilder.formatFactStats({
        totalFacts: 20,
        confirmedCount: 15,
        notStatedCount: 3,
        uncertainCount: 1,
        conflictCount: 1
      });
      expect(summaryWithConflict).toBe('15 Confirmed · 3 Not Stated · 1 Uncertain · 1 Conflict');
    });

    it('8. formatFactStats returns empty string for empty or missing stats without hardcoding', () => {
      expect(ReviewerBriefBuilder.formatFactStats(undefined)).toBe('');
      expect(ReviewerBriefBuilder.formatFactStats({
        totalFacts: 0,
        confirmedCount: 0,
        notStatedCount: 0,
        uncertainCount: 0,
        conflictCount: 0
      })).toBe('');
    });

    it('9. Brief includes factStatsSummary on output object', () => {
      const brief = ReviewerBriefBuilder.buildFromMessage(baseMessage);
      expect(brief.factStatsSummary).toBeDefined();
      expect(brief.factStatsSummary).toContain('Confirmed');
      expect(brief.factStatsSummary).not.toContain('Conflict');
    });

    it('10. Header terminology is changed from "AI Confidence" to "Triage Confidence" in case workspace template', async () => {
      const fs = await import('fs');
      const path = await import('path');
      const htmlPath = path.resolve(__dirname, '../../features/case-workspace/case-workspace.component.html');
      const htmlContent = fs.readFileSync(htmlPath, 'utf-8');
      expect(htmlContent).toContain('Triage Confidence:');
      expect(htmlContent).not.toContain('AI Confidence:');
    });
  });

  describe('Priority 5: Reviewer-Facing Summary Quality & Deterministic Reviewer Attention', () => {
    it('1. Preserves the rich LLM executive summary on brief.executiveSummary without replacing with synthetic text', () => {
      const msgWithRichSummary: IntakeMessage = {
        ...baseMessage,
        executiveSummary: 'This expedited spontaneous pharmacovigilance transmission details acute angioedema in a 58-year-old male following Cardioril. Clinical dechallenge was positive upon discontinuation.'
      };
      const brief = ReviewerBriefBuilder.buildFromMessage(msgWithRichSummary);
      expect(brief.executiveSummary).toBe(msgWithRichSummary.executiveSummary);
    });

    it('2. ICSR case produces reviewer attention with assistive 15-day expedited reporting consideration', () => {
      const brief = ReviewerBriefBuilder.buildFromMessage(baseMessage);
      expect(brief.reviewerAttention).toBeDefined();
      expect(brief.reviewerAttention).toContain(
        'Potential 15-day expedited reporting consideration; subject to medical/regulatory review.'
      );
      // Ensure assistive language and absence of definitive AI conclusions
      const joined = brief.reviewerAttention!.join(' ');
      expect(joined).not.toContain('legally compliant');
      expect(joined).not.toContain('no further clarification required');
      expect(joined).not.toContain('must be submitted');
    });

    it('3. Reviewer attention dynamically surfaces missing critical fields (dose, lot, age)', () => {
      const msgMissingFields: IntakeMessage = {
        ...baseMessage,
        icsrReport: {
          ...baseMessage.icsrReport!,
          productDose: 'Not stated',
          productLot: 'Not stated',
          patientAge: 'Not stated'
        }
      };
      const brief = ReviewerBriefBuilder.buildFromMessage(msgMissingFields);
      expect(brief.reviewerAttention).toBeDefined();
      expect(brief.reviewerAttention).toContain('Administered dose is not stated — reviewer confirmation required.');
      expect(brief.reviewerAttention).toContain('Product lot/batch is not stated.');
      expect(brief.reviewerAttention).toContain('Patient age is not stated.');
    });

    it('4. Reviewer attention dynamically surfaces uncertain facts and handwritten source warnings', () => {
      const msgHandwritten: IntakeMessage = {
        ...baseMessage,
        attachments: [
          {
            id: 201,
            filename: 'yellow_card_handwritten.jpg',
            contentType: 'image/jpeg',
            flavor: 'handwritten'
          }
        ],
        icsrReport: {
          ...baseMessage.icsrReport!,
          productDose: '10 mg (?)'
        }
      };
      const brief = ReviewerBriefBuilder.buildFromMessage(msgHandwritten);
      expect(brief.reviewerAttention).toBeDefined();
      expect(brief.reviewerAttention).toContain('Handwritten source documentation requires reviewer manual verification.');
    });

    it('5. Reviewer attention dynamically surfaces conflicting evidence across sources', () => {
      const msgConflict: IntakeMessage = {
        ...baseMessage,
        icsrReport: {
          ...baseMessage.icsrReport!,
          eventOnset: '2026-03-01'
        }
      };
      const facts: any[] = [
        { field: 'eventOnset', label: 'Event Onset Date', value: '2026-03-01 / 2026-02-28', status: 'CONFLICT', section: 'EVENT' }
      ];
      const items = ReviewerBriefBuilder.buildReviewerAttention(
        facts,
        [],
        {
          hasIcsr: true,
          hasPqc: false,
          hasMi: false,
          isNotRelevant: false,
          isMultiLabel: false,
          allCategories: ['Safety Report (ICSR)'],
          urgency: 'EXPEDITED'
        }
      );
      expect(items).toContain("Discrepancy detected for Event Onset Date ('2026-03-01 / 2026-02-28') across source materials — resolve conflict.");
    });

    it('6. PQC case surfaces physical defect photo inspection requirement', () => {
      const pqcMsg: IntakeMessage = {
        id: 2,
        messageId: 'msg-002',
        sender: 'Pharmacist Linda Green',
        senderEmail: 'lgreen@pharmacy.com',
        subject: 'PQC: Broken tablets in sealed blister pack',
        receivedDate: '2026-03-02 11:00:00',
        rawBody: 'Discovered fragmented tablets inside unopened blister.',
        status: 'TRIAGED',
        primaryCategory: 'Quality Complaint (PQC)',
        confidence: 0.98,
        isMultiLabel: false,
        createdAt: '2026-03-02T11:00:00Z',
        updatedAt: '2026-03-02T11:05:00Z',
        attachments: [
          { id: 202, filename: 'defect_photo.jpg', contentType: 'image/jpeg', flavor: 'defect_photo' }
        ],
        pqcReport: {
          productName: 'Neurotranquil',
          lotNumber: 'B44912',
          defectType: 'Broken Tablet',
          defectDescription: 'Multiple fragmented tablets in intact blister',
          packagingBreached: false,
          photoDetected: true,
          photoDescription: 'Severe tablet fragmentation visible in blister',
          requiresHumanReview: true
        }
      };
      const brief = ReviewerBriefBuilder.buildFromMessage(pqcMsg);
      expect(brief.reviewerAttention).toBeDefined();
      expect(brief.reviewerAttention).toContain('Product defect image requires human visual inspection in viewer.');
    });

    it('7. Multi-label case surfaces dual regulatory domain guidance without collapsing narratives', () => {
      const multiMsg: IntakeMessage = {
        id: 4,
        messageId: 'msg-004',
        sender: 'Dr. Jane Smith',
        senderEmail: 'jsmith@clinic.org',
        subject: 'Particulate in inhaler with severe bronchospasm',
        receivedDate: '2026-03-04 14:00:00',
        rawBody: 'Patient experienced severe bronchospasm following administration from inhaler containing black specks.',
        status: 'TRIAGED',
        primaryCategory: 'Safety Report (ICSR)',
        confidence: 0.95,
        isMultiLabel: true,
        createdAt: '2026-03-04T14:00:00Z',
        updatedAt: '2026-03-04T14:05:00Z',
        attachments: [],
        icsrReport: {
          ...baseMessage.icsrReport!,
          productName: 'RespiraClear',
          adverseEvent: 'Severe Bronchospasm'
        },
        pqcReport: {
          productName: 'RespiraClear',
          lotNumber: 'RC-10492',
          defectType: 'Particulate Contamination',
          defectDescription: 'Foreign black particulates inside inhaler canister nozzle',
          packagingBreached: false,
          photoDetected: true,
          requiresHumanReview: true
        }
      };
      const brief = ReviewerBriefBuilder.buildFromMessage(multiMsg);
      expect(brief.reviewerAttention).toBeDefined();
      expect(brief.reviewerAttention).toContain(
        'Dual regulatory domain (Safety Report (ICSR) & Quality Complaint (PQC)); review across both safety and quality workflows.'
      );
      expect(brief.reviewerAttention).toContain('Product defect image requires human visual inspection in viewer.');
      expect(brief.reviewerAttention).toContain(
        'Critical priority intake; expedited medical assessment and containment evaluation required.'
      );
    });

    it('8. Non-English case surfaces verbatim grounding notice for source language', () => {
      const spanishMsg: IntakeMessage = {
        ...baseMessage,
        attachments: [
          {
            id: 301,
            filename: 'notificacion_farmacovigilancia.pdf',
            contentType: 'application/pdf',
            flavor: 'foreign_language',
            language: 'Spanish'
          }
        ]
      };
      const brief = ReviewerBriefBuilder.buildFromMessage(spanishMsg);
      expect(brief.reviewerAttention).toBeDefined();
      expect(brief.reviewerAttention).toContain(
        'Non-English source documentation (Spanish); verify verbatim original text against extraction.'
      );
    });

    it('9. Not Relevant case provides concise administrative disposition without clinical/expedited warnings', () => {
      const notRelMsg: IntakeMessage = {
        id: 6,
        messageId: 'msg-006',
        sender: 'Events Team',
        senderEmail: 'events@pharmanext.com',
        subject: 'Invitation to Annual Pharma Supply Chain Summit',
        receivedDate: '2026-03-06 08:00:00',
        rawBody: 'Join industry leaders at the upcoming Pharma Supply Chain Conference in Berlin.',
        status: 'TRIAGED',
        primaryCategory: 'Not Relevant',
        confidence: 0.99,
        isMultiLabel: false,
        createdAt: '2026-03-06T08:00:00Z',
        updatedAt: '2026-03-06T08:05:00Z',
        attachments: []
      };
      const brief = ReviewerBriefBuilder.buildFromMessage(notRelMsg);
      expect(brief.reviewerAttention).toBeDefined();
      expect(brief.reviewerAttention).toHaveLength(1);
      expect(brief.reviewerAttention![0]).toBe(
        'Submission does not meet adverse event or quality complaint reportability thresholds; candidate for administrative closure.'
      );
      expect(brief.reviewerAttention![0]).not.toContain('expedited');
      expect(brief.reviewerAttention![0]).not.toContain('dose');
    });

    it('10. Python triage instruction mandates 4-6 sentences and explicitly requires human-in-the-loop language', async () => {
      const fs = await import('fs');
      const path = await import('path');
      const triageServicePath = path.resolve(__dirname, '../../../../../ai-service-python/app/services/triage_service.py');
      const content = fs.readFileSync(triageServicePath, 'utf-8');

      // Mandate 4 to 6 sentences
      expect(content).toContain('approximately 4 to 6 sentences');
      expect(content).not.toContain('10 to 15 sentence');

      // Explicit human-in-the-loop rules
      expect(content).toContain('CRITICAL HUMAN-IN-THE-LOOP LANGUAGE MANDATE:');
      expect(content).toContain('The AI must NEVER state definitive legal or regulatory conclusions');
      expect(content).toContain('do NOT use "legally compliant"');
      expect(content).toContain('"must be submitted"');
      expect(content).toContain('"no further clarification required"');
      expect(content).toContain('subject to reviewer medical assessment and regulatory verification');
    });

    it('11. Case workspace template renders the Reviewer Attention box directly below executive summary', async () => {
      const fs = await import('fs');
      const path = await import('path');
      const htmlPath = path.resolve(__dirname, '../../features/case-workspace/case-workspace.component.html');
      const htmlContent = fs.readFileSync(htmlPath, 'utf-8');

      expect(htmlContent).toContain('class="reviewer-attention-box"');
      expect(htmlContent).toContain('Reviewer Attention');
      expect(htmlContent).toContain('*ngFor="let item of brief.reviewerAttention"');
    });
  });
});






