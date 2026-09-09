package com.clinevo.smartinbox;

import com.clinevo.smartinbox.ingestion.FixtureIngestionSource;
import com.clinevo.smartinbox.ingestion.RawEmailPayload;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.TestPropertySource;

import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

@SpringBootTest
@TestPropertySource(properties = {
    "smartinbox.ingestion.auto-ingest-on-startup=false",
    "smartinbox.ingestion.fixture-dir=../test-data/emails"
})
class FixtureIngestionTest {

    @Autowired
    private FixtureIngestionSource fixtureIngestionSource;

    @Test
    void testFetchNewEmailsFromFixture() throws Exception {
        List<RawEmailPayload> emails = fixtureIngestionSource.fetchNewEmails();
        assertNotNull(emails);
        assertEquals(12, emails.size(), "Should load exactly 12 synthetic fixture emails");

        // Verify email 01
        RawEmailPayload email01 = emails.stream()
                .filter(e -> "email_01.eml".equals(e.filename()))
                .findFirst()
                .orElse(null);
        assertNotNull(email01);
        assertEquals("Dr. Sarah Jenkins, MD", email01.sender());
        assertEquals("sjenkins@metrohealth-chicago.org", email01.senderEmail());
        assertTrue(email01.subject().contains("Cardioril"));
        assertEquals(1, email01.attachments().size());
        assertEquals("cioms_form_MK_Cardioril.pdf", email01.attachments().get(0).filename());

        // Verify Case 04 (Multi-label with defect attachment)
        RawEmailPayload email04 = emails.stream()
                .filter(e -> "email_04.eml".equals(e.filename()))
                .findFirst()
                .orElse(null);
        assertNotNull(email04);
        assertEquals("Dr. Robert Lang, MD", email04.sender());
        assertTrue(email04.subject().contains("Cefatox"));
        assertEquals(1, email04.attachments().size());
        assertEquals("vial_contamination_sepsis.pdf", email04.attachments().get(0).filename());
    }
}
