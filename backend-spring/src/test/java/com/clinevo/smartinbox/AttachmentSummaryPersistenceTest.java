package com.clinevo.smartinbox;

import com.clinevo.smartinbox.dto.ExtractionResultDto;
import com.clinevo.smartinbox.model.AttachmentEntity;
import com.clinevo.smartinbox.model.IntakeMessageEntity;
import com.clinevo.smartinbox.service.AsyncDocumentProcessor;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

import java.util.ArrayList;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

@SpringBootTest
public class AttachmentSummaryPersistenceTest {

    @Autowired
    private AsyncDocumentProcessor asyncDocumentProcessor;

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    void testExtractionResultDtoDeserializesDocumentSummary() throws Exception {
        String json = """
            {
                "case_id": "TEST-01",
                "source_filename": "test.eml",
                "triage": {
                    "is_multi_label": false,
                    "primary_category": "Safety Report (ICSR)",
                    "executive_summary": "Message executive synthesis."
                },
                "attachment_metadata": [
                    {
                        "filename": "clinical_dili_report.pdf",
                        "flavor": "digital_form",
                        "language": "English",
                        "document_summary": "10 to 15 sentence clinical summary evaluating the attached PDF for DILI relevance."
                    }
                ]
            }
            """;

        ExtractionResultDto dto = objectMapper.readValue(json, ExtractionResultDto.class);
        assertNotNull(dto.getAttachment_metadata());
        assertEquals(1, dto.getAttachment_metadata().size());

        ExtractionResultDto.AttachmentMetadataDto attDto = dto.getAttachment_metadata().get(0);
        assertEquals("clinical_dili_report.pdf", attDto.getFilename());
        assertEquals("10 to 15 sentence clinical summary evaluating the attached PDF for DILI relevance.", attDto.getDocument_summary());
    }

    @Test
    void testAsyncDocumentProcessorAppliesDocumentSummaryToAttachment() throws Exception {
        IntakeMessageEntity message = new IntakeMessageEntity();
        message.setSubject("Test Subject");
        message.setSender("Dr. Tester");

        AttachmentEntity att = new AttachmentEntity();
        att.setFilename("cioms_form_MK_Cardioril.pdf");
        att.setContentType("application/pdf");
        att.setMessage(message);

        List<AttachmentEntity> attachments = new ArrayList<>();
        attachments.add(att);
        message.setAttachments(attachments);

        // Build ExtractionResultDto with 4-6 sentence executive summary AND 10-15 sentence PDF document_summary
        ExtractionResultDto result = new ExtractionResultDto();
        ExtractionResultDto.TriageResultDto triage = new ExtractionResultDto.TriageResultDto();
        triage.setPrimary_category("Safety Report (ICSR)");
        triage.setExecutive_summary("4-6 sentence message overview describing clinical event.");
        result.setTriage(triage);

        ExtractionResultDto.AttachmentMetadataDto attMeta = new ExtractionResultDto.AttachmentMetadataDto();
        attMeta.setFilename("cioms_form_MK_Cardioril.pdf");
        attMeta.setFlavor("digital_form");
        attMeta.setLanguage("English");
        attMeta.setDocument_summary("10-15 sentence comprehensive regulatory analysis of the CIOMS form confirming ICSR relevance.");

        result.setAttachment_metadata(List.of(attMeta));

        // Apply extraction result
        asyncDocumentProcessor.applyExtractionResult(message, result);

        // Verify Attachment received the document_summary
        assertEquals("10-15 sentence comprehensive regulatory analysis of the CIOMS form confirming ICSR relevance.", att.getDocumentSummary());
        assertEquals("digital_form", att.getFlavor());
        assertEquals("English", att.getLanguage());

        // Verify Executive Synthesis is strictly preserved on message and NOT overwritten by the PDF summary
        assertEquals("4-6 sentence message overview describing clinical event.", message.getExecutiveSummary());
        assertNotEquals(message.getExecutiveSummary(), att.getDocumentSummary());
    }
}
