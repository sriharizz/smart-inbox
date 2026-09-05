package com.clinevo.smartinbox.ingestion;

import jakarta.mail.BodyPart;
import jakarta.mail.Multipart;
import jakarta.mail.Session;
import jakarta.mail.internet.InternetAddress;
import jakarta.mail.internet.MimeMessage;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.io.ByteArrayInputStream;
import java.io.File;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.*;

@Component("fixtureIngestionSource")
public class FixtureIngestionSource implements IngestionSource {

    private static final Logger log = LoggerFactory.getLogger(FixtureIngestionSource.class);

    @Value("${smartinbox.ingestion.fixture-dir:../test-data/emails}")
    private String fixtureDir;

    @Override
    public String getSourceName() {
        return "LOCAL_FIXTURE";
    }

    @Override
    public List<RawEmailPayload> fetchNewEmails() throws Exception {
        List<RawEmailPayload> results = new ArrayList<>();
        Path path = Paths.get(fixtureDir).toAbsolutePath().normalize();
        
        // Check fallback paths if relative directory differs
        if (!Files.exists(path)) {
            Path alternativePath = Paths.get("test-data", "emails").toAbsolutePath().normalize();
            if (Files.exists(alternativePath)) {
                path = alternativePath;
            } else {
                alternativePath = Paths.get("..", "test-data", "emails").toAbsolutePath().normalize();
                if (Files.exists(alternativePath)) {
                    path = alternativePath;
                }
            }
        }

        if (!Files.exists(path) || !Files.isDirectory(path)) {
            log.warn("Fixture email directory not found at: {}", path);
            return results;
        }

        File[] emlFiles = path.toFile().listFiles((dir, name) -> name.toLowerCase().endsWith(".eml"));
        if (emlFiles == null || emlFiles.length == 0) {
            log.info("No .eml files found in fixture directory: {}", path);
            return results;
        }

        Arrays.sort(emlFiles, Comparator.comparing(File::getName));
        Session session = Session.getDefaultInstance(new Properties());

        for (File file : emlFiles) {
            try {
                byte[] rawBytes = Files.readAllBytes(file.toPath());
                try (InputStream is = new ByteArrayInputStream(rawBytes)) {
                    MimeMessage message = new MimeMessage(session, is);
                    
                    String messageId = message.getMessageID();
                    if (messageId == null || messageId.isBlank()) {
                        messageId = file.getName();
                    } else {
                        messageId = messageId.replaceAll("[<>]", "").trim();
                    }

                    String subject = message.getSubject() != null ? message.getSubject() : "No Subject";
                    String date = message.getSentDate() != null ? message.getSentDate().toString() : "";
                    
                    String senderName = "";
                    String senderEmail = "";
                    if (message.getFrom() != null && message.getFrom().length > 0) {
                        InternetAddress address = (InternetAddress) message.getFrom()[0];
                        senderName = address.getPersonal() != null ? address.getPersonal() : address.getAddress();
                        senderEmail = address.getAddress();
                    }

                    String recipient = "";
                    if (message.getAllRecipients() != null && message.getAllRecipients().length > 0) {
                        recipient = message.getAllRecipients()[0].toString();
                    }

                    StringBuilder bodyText = new StringBuilder();
                    List<RawAttachmentPayload> attachments = new ArrayList<>();

                    extractParts(message, bodyText, attachments);

                    results.add(new RawEmailPayload(
                            file.getName(),
                            messageId,
                            date,
                            senderName,
                            senderEmail,
                            recipient,
                            subject,
                            bodyText.toString().trim(),
                            attachments,
                            rawBytes
                    ));
                }
            } catch (Exception e) {
                log.error("Error parsing fixture email file {}: {}", file.getName(), e.getMessage());
            }
        }

        log.info("Loaded {} synthetic fixture emails from {}", results.size(), path);
        return results;
    }

    private void extractParts(jakarta.mail.Part part, StringBuilder bodyText, List<RawAttachmentPayload> attachments) throws Exception {
        if (part.isMimeType("text/plain") && part.getFileName() == null) {
            bodyText.append(part.getContent().toString()).append("\n");
        } else if (part.isMimeType("text/html") && bodyText.isEmpty() && part.getFileName() == null) {
            String html = part.getContent().toString();
            bodyText.append(html.replaceAll("<[^>]*>", " ")).append("\n");
        } else if (part.isMimeType("multipart/*")) {
            Multipart mp = (Multipart) part.getContent();
            for (int i = 0; i < mp.getCount(); i++) {
                BodyPart bodyPart = mp.getBodyPart(i);
                extractParts(bodyPart, bodyText, attachments);
            }
        } else {
            String fileName = part.getFileName();
            if (fileName != null && !fileName.isBlank()) {
                InputStream is = part.getInputStream();
                byte[] bytes = is.readAllBytes();
                attachments.add(new RawAttachmentPayload(
                        fileName,
                        part.getContentType(),
                        bytes.length,
                        bytes
                ));
            }
        }
    }
}
