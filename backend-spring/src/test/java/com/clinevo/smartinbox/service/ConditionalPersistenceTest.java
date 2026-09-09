package com.clinevo.smartinbox.service;

import com.clinevo.smartinbox.dto.ExtractionResultDto;
import com.clinevo.smartinbox.model.IcsrReportEntity;
import com.clinevo.smartinbox.model.IntakeMessageEntity;
import com.clinevo.smartinbox.repository.*;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class ConditionalPersistenceTest {

    private AsyncDocumentProcessor processor;
    private ObjectMapper objectMapper;

    @BeforeEach
    void setUp() {
        objectMapper = new ObjectMapper();
        processor = new AsyncDocumentProcessor(
                null, null, null, null, null, null, objectMapper
        );
    }

    @Test
    @DisplayName("1. ICSR Case -> IcsrReportEntity exists with extracted clinical data")
    void testIcsrReportPersistedWhenIcsrCategory() throws Exception {
        IntakeMessageEntity message = new IntakeMessageEntity();
        message.setId(101L);

        ExtractionResultDto result = new ExtractionResultDto();
        ExtractionResultDto.TriageResultDto triage = new ExtractionResultDto.TriageResultDto();
        triage.setPrimary_category("Safety Report (ICSR)");
        triage.setIs_multi_label(false);
        result.setTriage(triage);

        ExtractionResultDto.PatientDto patient = new ExtractionResultDto.PatientDto();
        patient.setIdentifier("Pt-01");
        patient.setAge("45 YRS");
        result.setPatient(patient);

        ExtractionResultDto.ProductDto product = new ExtractionResultDto.ProductDto();
        product.setProduct_name("Cardioril 10mg");
        result.setProduct(product);

        ExtractionResultDto.ReactionDto reaction = new ExtractionResultDto.ReactionDto();
        reaction.setAdverse_event("Hepatitis");
        result.setReaction(reaction);

        processor.applyExtractionResult(message, result);

        assertNotNull(message.getIcsrReport(), "ICSR report entity must be created for ICSR category");
        assertEquals("Pt-01", message.getIcsrReport().getPatientIdentifier());
        assertEquals("Cardioril 10mg", message.getIcsrReport().getProductName());
        assertEquals("Hepatitis", message.getIcsrReport().getAdverseEvent());
        assertNull(message.getPqcReport(), "PQC report must be null for pure ICSR");
        assertNull(message.getMedicalInfo(), "Medical Info must be null for pure ICSR");
    }

    @Test
    @DisplayName("2. PQC-only Case -> IcsrReportEntity is strictly null, PqcReportEntity exists")
    void testIcsrReportNullWhenPqcOnly() throws Exception {
        IntakeMessageEntity message = new IntakeMessageEntity();
        message.setId(102L);

        ExtractionResultDto result = new ExtractionResultDto();
        ExtractionResultDto.TriageResultDto triage = new ExtractionResultDto.TriageResultDto();
        triage.setPrimary_category("Quality Complaint (PQC)");
        triage.setIs_multi_label(false);
        result.setTriage(triage);

        // Dummy/empty ICSR fields that legacy adapter might output
        ExtractionResultDto.PatientDto emptyPatient = new ExtractionResultDto.PatientDto();
        emptyPatient.setIdentifier("Not stated");
        result.setPatient(emptyPatient);

        ExtractionResultDto.ProductDto emptyProduct = new ExtractionResultDto.ProductDto();
        emptyProduct.setProduct_name("Not stated");
        result.setProduct(emptyProduct);

        ExtractionResultDto.ReactionDto emptyReaction = new ExtractionResultDto.ReactionDto();
        emptyReaction.setAdverse_event("Not stated");
        result.setReaction(emptyReaction);

        // Actual PQC data
        ExtractionResultDto.QualityComplaintDto qc = new ExtractionResultDto.QualityComplaintDto();
        qc.setProduct_name("Cefatox IV 1g");
        qc.setLot_number("CFX-8092B");
        qc.setDefect_type("Compromised crimp seals");
        qc.setPackaging_breached(true);
        result.setQuality_complaint(qc);

        processor.applyExtractionResult(message, result);

        assertNull(message.getIcsrReport(), "IcsrReportEntity must be null for PQC-only case");
        assertNotNull(message.getPqcReport(), "PqcReportEntity must exist for PQC case");
        assertEquals("Cefatox IV 1g", message.getPqcReport().getProductName());
        assertEquals("CFX-8092B", message.getPqcReport().getLotNumber());
        assertTrue(message.getPqcReport().getPackagingBreached());
        assertNull(message.getMedicalInfo(), "Medical Info must be null for pure PQC");
    }

    @Test
    @DisplayName("3. MI-only Case -> IcsrReportEntity is strictly null, MedicalInfoEntity exists")
    void testIcsrReportNullWhenMiOnly() throws Exception {
        IntakeMessageEntity message = new IntakeMessageEntity();
        message.setId(103L);

        ExtractionResultDto result = new ExtractionResultDto();
        ExtractionResultDto.TriageResultDto triage = new ExtractionResultDto.TriageResultDto();
        triage.setPrimary_category("Medical Information (MI)");
        triage.setIs_multi_label(false);
        result.setTriage(triage);

        ExtractionResultDto.MedicalInfoDto mi = new ExtractionResultDto.MedicalInfoDto();
        mi.setProduct_or_topic("Cardioril");
        mi.setInquiry_type("Stability");
        mi.setQuestion_text("What is the room temperature stability of diluted Cardioril?");
        result.setMedical_info(mi);

        processor.applyExtractionResult(message, result);

        assertNull(message.getIcsrReport(), "IcsrReportEntity must be null for MI-only case");
        assertNull(message.getPqcReport(), "PqcReportEntity must be null for pure MI");
        assertNotNull(message.getMedicalInfo(), "MedicalInfoEntity must exist for MI case");
        assertEquals("Cardioril", message.getMedicalInfo().getProductOrTopic());
        assertEquals("Stability", message.getMedicalInfo().getInquiryType());
    }

    @Test
    @DisplayName("4. Not Relevant Case -> IcsrReportEntity, PQC, and MI are all strictly null")
    void testIcsrReportNullWhenNotRelevant() throws Exception {
        IntakeMessageEntity message = new IntakeMessageEntity();
        message.setId(104L);

        ExtractionResultDto result = new ExtractionResultDto();
        ExtractionResultDto.TriageResultDto triage = new ExtractionResultDto.TriageResultDto();
        triage.setPrimary_category("Not Relevant");
        triage.setIs_multi_label(false);
        result.setTriage(triage);

        processor.applyExtractionResult(message, result);

        assertNull(message.getIcsrReport(), "IcsrReportEntity must be null for Not Relevant communication");
        assertNull(message.getPqcReport(), "PqcReportEntity must be null for Not Relevant communication");
        assertNull(message.getMedicalInfo(), "MedicalInfoEntity must be null for Not Relevant communication");
    }

    @Test
    @DisplayName("5. Multi-label ICSR + PQC -> both IcsrReportEntity and PqcReportEntity coexist independently")
    void testMultiLabelCoexistenceIcsrAndPqc() throws Exception {
        IntakeMessageEntity message = new IntakeMessageEntity();
        message.setId(105L);

        ExtractionResultDto result = new ExtractionResultDto();
        ExtractionResultDto.TriageResultDto triage = new ExtractionResultDto.TriageResultDto();
        triage.setPrimary_category("Safety Report (ICSR) + Quality Complaint (PQC)");
        triage.setIs_multi_label(true);
        result.setTriage(triage);

        // ICSR data
        ExtractionResultDto.PatientDto patient = new ExtractionResultDto.PatientDto();
        patient.setIdentifier("Pt-99");
        result.setPatient(patient);

        ExtractionResultDto.ProductDto product = new ExtractionResultDto.ProductDto();
        product.setProduct_name("Cefatox IV 1g");
        result.setProduct(product);

        ExtractionResultDto.ReactionDto reaction = new ExtractionResultDto.ReactionDto();
        reaction.setAdverse_event("Septic shock");
        result.setReaction(reaction);

        // PQC data
        ExtractionResultDto.QualityComplaintDto qc = new ExtractionResultDto.QualityComplaintDto();
        qc.setProduct_name("Cefatox IV 1g");
        qc.setLot_number("LOT-SEPSIS-4");
        qc.setDefect_type("Particulate contamination");
        result.setQuality_complaint(qc);

        processor.applyExtractionResult(message, result);

        assertNotNull(message.getIcsrReport(), "IcsrReportEntity must exist for multi-label case");
        assertNotNull(message.getPqcReport(), "PqcReportEntity must exist for multi-label case");
        assertEquals("Pt-99", message.getIcsrReport().getPatientIdentifier());
        assertEquals("Septic shock", message.getIcsrReport().getAdverseEvent());
        assertEquals("Particulate contamination", message.getPqcReport().getDefectType());
        assertNull(message.getMedicalInfo(), "MedicalInfoEntity must remain null");
    }

    @Test
    @DisplayName("6. Existing ICSR Report is cleared when reprocessed as non-ICSR")
    void testExistingIcsrReportClearedWhenReprocessedAsPqc() throws Exception {
        IntakeMessageEntity message = new IntakeMessageEntity();
        message.setId(106L);

        // Pre-existing ICSR report (e.g., from old buggy run)
        IcsrReportEntity oldIcsr = new IcsrReportEntity();
        oldIcsr.setPatientIdentifier("Old Dummy Pt");
        message.setIcsrReport(oldIcsr);

        // Reprocessing with PQC-only
        ExtractionResultDto result = new ExtractionResultDto();
        ExtractionResultDto.TriageResultDto triage = new ExtractionResultDto.TriageResultDto();
        triage.setPrimary_category("Quality Complaint (PQC)");
        result.setTriage(triage);

        ExtractionResultDto.QualityComplaintDto qc = new ExtractionResultDto.QualityComplaintDto();
        qc.setProduct_name("Cefatox");
        result.setQuality_complaint(qc);

        processor.applyExtractionResult(message, result);

        assertNull(message.getIcsrReport(), "Stale ICSR report must be cleared to null on non-ICSR reprocessing");
        assertNotNull(message.getPqcReport(), "PQC report should be persisted");
    }

    @Test
    @DisplayName("7. Valid ICSR entity created even when some fields are Not stated (Preserves valid ICSRs)")
    void testIcsrReportPersistedWhenSomeFieldsAreNotStated() throws Exception {
        IntakeMessageEntity message = new IntakeMessageEntity();
        message.setId(107L);

        ExtractionResultDto result = new ExtractionResultDto();
        ExtractionResultDto.TriageResultDto triage = new ExtractionResultDto.TriageResultDto();
        triage.setPrimary_category("Safety Report (ICSR)");
        result.setTriage(triage);

        // Only reaction is known, patient demographics are Not stated
        ExtractionResultDto.PatientDto patient = new ExtractionResultDto.PatientDto();
        patient.setIdentifier("Not stated");
        patient.setAge("Not stated");
        result.setPatient(patient);

        ExtractionResultDto.ProductDto product = new ExtractionResultDto.ProductDto();
        product.setProduct_name("Cardioril");
        result.setProduct(product);

        ExtractionResultDto.ReactionDto reaction = new ExtractionResultDto.ReactionDto();
        reaction.setAdverse_event("Severe Nausea");
        result.setReaction(reaction);

        processor.applyExtractionResult(message, result);

        assertNotNull(message.getIcsrReport(), "ICSR report must not be suppressed when classified as ICSR even if some fields are Not stated");
        assertEquals("Cardioril", message.getIcsrReport().getProductName());
        assertEquals("Severe Nausea", message.getIcsrReport().getAdverseEvent());
        assertEquals("Not stated", message.getIcsrReport().getPatientIdentifier());
    }

    @Test
    @DisplayName("8. Non-English document metadata correctly updates attachment language and flavor")
    void testLanguageAndFlavorAppliedCorrectly() throws Exception {
        IntakeMessageEntity message = new IntakeMessageEntity();
        message.setId(108L);
        message.setLanguage("English"); // default

        com.clinevo.smartinbox.model.AttachmentEntity att = new com.clinevo.smartinbox.model.AttachmentEntity();
        att.setFilename("notificacion_ram_madrid.pdf");
        att.setFlavor("digital_form"); // default
        att.setLanguage("English"); // default
        message.addAttachment(att);

        ExtractionResultDto result = new ExtractionResultDto();
        result.setLanguage_detected("Spanish");
        
        ExtractionResultDto.AttachmentMetadataDto attMeta = new ExtractionResultDto.AttachmentMetadataDto();
        attMeta.setFilename("notificacion_ram_madrid.pdf");
        attMeta.setFlavor("non_english");
        attMeta.setLanguage("Spanish");
        result.setAttachment_metadata(java.util.List.of(attMeta));

        processor.applyExtractionResult(message, result);

        assertEquals("Spanish", message.getLanguage(), "Message language should update to detected Spanish");
        assertEquals("non_english", att.getFlavor(), "Attachment flavor should update to non_english");
        assertEquals("Spanish", att.getLanguage(), "Attachment language should update to Spanish");
    }

    @Test
    @DisplayName("9. Misleading English filename ('packaging_defect_report.pdf') remains English and digital_form")
    void testMisleadingEnglishAttachmentKeepsEnglishLanguageAndDigitalFlavor() throws Exception {
        IntakeMessageEntity message = new IntakeMessageEntity();
        message.setId(109L);
        message.setLanguage("English");

        com.clinevo.smartinbox.model.AttachmentEntity att = new com.clinevo.smartinbox.model.AttachmentEntity();
        att.setFilename("packaging_defect_report.pdf");
        att.setFlavor("digital_form");
        att.setLanguage("English");
        message.addAttachment(att);

        ExtractionResultDto result = new ExtractionResultDto();
        result.setLanguage_detected("English");
        
        ExtractionResultDto.AttachmentMetadataDto attMeta = new ExtractionResultDto.AttachmentMetadataDto();
        attMeta.setFilename("packaging_defect_report.pdf");
        attMeta.setFlavor("digital_form");
        attMeta.setLanguage("English");
        result.setAttachment_metadata(java.util.List.of(attMeta));

        processor.applyExtractionResult(message, result);

        assertEquals("English", message.getLanguage());
        assertEquals("digital_form", att.getFlavor());
        assertEquals("English", att.getLanguage());
    }

    @Test
    @DisplayName("10. English email + Spanish PDF: message language remains English, attachment language is Spanish")
    void testEnglishMessageWithSpanishAttachmentLanguageSeparation() throws Exception {
        IntakeMessageEntity message = new IntakeMessageEntity();
        message.setId(110L);
        message.setLanguage("English");

        com.clinevo.smartinbox.model.AttachmentEntity att = new com.clinevo.smartinbox.model.AttachmentEntity();
        att.setFilename("notificacion_ram_madrid.pdf");
        att.setFlavor("digital_form");
        att.setLanguage("English");
        message.addAttachment(att);

        ExtractionResultDto result = new ExtractionResultDto();
        result.setLanguage_detected("English"); // Email body is English!
        
        ExtractionResultDto.AttachmentMetadataDto attMeta = new ExtractionResultDto.AttachmentMetadataDto();
        attMeta.setFilename("notificacion_ram_madrid.pdf");
        attMeta.setFlavor("non_english");
        attMeta.setLanguage("Spanish"); // Attachment is Spanish!
        result.setAttachment_metadata(java.util.List.of(attMeta));

        processor.applyExtractionResult(message, result);

        assertEquals("English", message.getLanguage(), "Message language MUST remain English");
        assertEquals("non_english", att.getFlavor(), "Attachment flavor must be non_english");
        assertEquals("Spanish", att.getLanguage(), "Attachment language must be Spanish");
    }
}
