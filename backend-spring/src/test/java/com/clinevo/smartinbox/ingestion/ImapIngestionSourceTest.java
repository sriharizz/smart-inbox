package com.clinevo.smartinbox.ingestion;

import jakarta.mail.Session;
import jakarta.mail.internet.InternetAddress;
import jakarta.mail.internet.MimeBodyPart;
import jakarta.mail.internet.MimeMessage;
import jakarta.mail.internet.MimeMultipart;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.test.util.ReflectionTestUtils;

import java.io.ByteArrayOutputStream;
import java.util.List;
import java.util.Properties;

import static org.junit.jupiter.api.Assertions.*;

class ImapIngestionSourceTest {

    private ImapIngestionSource imapSource;

    @BeforeEach
    void setUp() {
        imapSource = new ImapIngestionSource();
        ReflectionTestUtils.setField(imapSource, "host", "imap.gmail.com");
        ReflectionTestUtils.setField(imapSource, "port", 993);
        ReflectionTestUtils.setField(imapSource, "username", "test.user@example.com");
        ReflectionTestUtils.setField(imapSource, "password", "testpassword");
        ReflectionTestUtils.setField(imapSource, "ssl", true);
        ReflectionTestUtils.setField(imapSource, "folderName", "INBOX");
    }

    @Test
    void testGetSourceName() {
        assertEquals("LIVE_IMAP", imapSource.getSourceName());
    }

    @Test
    void testConfigurationFields() {
        assertEquals("imap.gmail.com", ReflectionTestUtils.getField(imapSource, "host"));
        assertEquals(993, ReflectionTestUtils.getField(imapSource, "port"));
        assertEquals("test.user@example.com", ReflectionTestUtils.getField(imapSource, "username"));
        assertEquals(true, ReflectionTestUtils.getField(imapSource, "ssl"));
        assertEquals("INBOX", ReflectionTestUtils.getField(imapSource, "folderName"));
    }

    @Test
    void testMimeMessageExtractionLogic() throws Exception {
        Session session = Session.getInstance(new Properties());
        MimeMessage msg = new MimeMessage(session);
        msg.setFrom(new InternetAddress("dr.smith@hospital.org", "Dr. John Smith"));
        msg.setRecipients(jakarta.mail.Message.RecipientType.TO, "safety@pharma.com");
        msg.setSubject("Adverse Event Report: Drug X - Severe Rash");
        msg.setHeader("Message-ID", "<custom-msg-id-12345@hospital.org>");

        MimeMultipart multipart = new MimeMultipart();

        // Body text
        MimeBodyPart textPart = new MimeBodyPart();
        textPart.setText("Patient experienced severe urticaria and rash after 50mg dose.");
        multipart.addBodyPart(textPart);

        // Attachment
        MimeBodyPart attachPart = new MimeBodyPart();
        attachPart.setFileName("medwatch_form.pdf");
        attachPart.setContent("Mock PDF Content".getBytes(), "application/pdf");
        multipart.addBodyPart(attachPart);

        msg.setContent(multipart);
        msg.saveChanges();
        msg.setHeader("Message-ID", "<custom-msg-id-12345@hospital.org>");

        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        msg.writeTo(baos);
        byte[] rawBytes = baos.toByteArray();

        assertNotNull(rawBytes);
        assertTrue(rawBytes.length > 0);
        assertEquals("custom-msg-id-12345@hospital.org", msg.getMessageID().replaceAll("[<>]", "").trim());
    }

    @Test
    void testInvalidHostReturnsEmptyListGracefully() throws Exception {
        ReflectionTestUtils.setField(imapSource, "host", "nonexistent.invalid.host.local");
        List<RawEmailPayload> emails = imapSource.fetchNewEmails();
        assertNotNull(emails);
        assertTrue(emails.isEmpty(), "Connection failure should be logged and return empty list rather than crashing");
    }

    @Test
    void testBenchmarkIdentification() {
        com.clinevo.smartinbox.model.IntakeMessageEntity benchmark = new com.clinevo.smartinbox.model.IntakeMessageEntity();
        benchmark.setMessageId("case-01-final-1788957014@metrohealth-chicago.org");
        assertTrue(com.clinevo.smartinbox.service.MailboxIngestionService.isBenchmarkMessage(benchmark));

        com.clinevo.smartinbox.model.IntakeMessageEntity liveEmail = new com.clinevo.smartinbox.model.IntakeMessageEntity();
        liveEmail.setMessageId("CAGvH-3uU5X8g=abc@mail.gmail.com");
        assertFalse(com.clinevo.smartinbox.service.MailboxIngestionService.isBenchmarkMessage(liveEmail));

        com.clinevo.smartinbox.model.IntakeMessageEntity nullMsg = new com.clinevo.smartinbox.model.IntakeMessageEntity();
        assertFalse(com.clinevo.smartinbox.service.MailboxIngestionService.isBenchmarkMessage(nullMsg));
    }
}
