package com.clinevo.smartinbox.ingestion;

import jakarta.mail.*;
import jakarta.mail.internet.InternetAddress;
import jakarta.mail.internet.MimeMessage;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.util.*;

@Component("imapIngestionSource")
public class ImapIngestionSource implements IngestionSource {

    private static final Logger log = LoggerFactory.getLogger(ImapIngestionSource.class);

    @Value("${smartinbox.ingestion.imap.host:imap.gmail.com}")
    private String host;

    @Value("${smartinbox.ingestion.imap.port:993}")
    private int port;

    @Value("${smartinbox.ingestion.imap.username:safety.intake.test@example.com}")
    private String username;

    @Value("${smartinbox.ingestion.imap.password:secret}")
    private String password;

    @Value("${smartinbox.ingestion.imap.ssl:true}")
    private boolean ssl;

    @Value("${smartinbox.ingestion.imap.folder:INBOX}")
    private String folderName;

    @Override
    public String getSourceName() {
        return "LIVE_IMAP";
    }

    @Override
    public List<RawEmailPayload> fetchNewEmails() throws Exception {
        List<RawEmailPayload> results = new ArrayList<>();

        Properties props = new Properties();
        props.put("mail.store.protocol", "imaps");
        props.put("mail.imaps.host", host);
        props.put("mail.imaps.port", String.valueOf(port));
        props.put("mail.imaps.ssl.enable", String.valueOf(ssl));
        props.put("mail.imaps.timeout", "10000");
        props.put("mail.imaps.connectiontimeout", "10000");

        Session session = Session.getInstance(props);
        Store store = null;
        Folder folder = null;

        try {
            store = session.getStore("imaps");
            store.connect(host, username, password);

            folder = store.getFolder(folderName);
            folder.open(Folder.READ_ONLY);

            Message[] messages = folder.getMessages();
            log.info("IMAP mailbox connected: {} messages found in {}", messages.length, folderName);

            for (Message msg : messages) {
                if (msg instanceof MimeMessage mimeMsg) {
                    ByteArrayOutputStream baos = new ByteArrayOutputStream();
                    mimeMsg.writeTo(baos);
                    byte[] rawBytes = baos.toByteArray();

                    String messageId = mimeMsg.getMessageID();
                    if (messageId == null || messageId.isBlank()) {
                        messageId = "IMAP-MSG-" + msg.getMessageNumber();
                    } else {
                        messageId = messageId.replaceAll("[<>]", "").trim();
                    }

                    String subject = mimeMsg.getSubject() != null ? mimeMsg.getSubject() : "No Subject";
                    String date = mimeMsg.getSentDate() != null ? mimeMsg.getSentDate().toString() : "";

                    String senderName = "";
                    String senderEmail = "";
                    if (mimeMsg.getFrom() != null && mimeMsg.getFrom().length > 0) {
                        InternetAddress address = (InternetAddress) mimeMsg.getFrom()[0];
                        senderName = address.getPersonal() != null ? address.getPersonal() : address.getAddress();
                        senderEmail = address.getAddress();
                    }

                    String recipient = "";
                    if (mimeMsg.getAllRecipients() != null && mimeMsg.getAllRecipients().length > 0) {
                        recipient = mimeMsg.getAllRecipients()[0].toString();
                    }

                    StringBuilder bodyText = new StringBuilder();
                    List<RawAttachmentPayload> attachments = new ArrayList<>();
                    extractParts(mimeMsg, bodyText, attachments);

                    results.add(new RawEmailPayload(
                            "imap_" + msg.getMessageNumber() + ".eml",
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
            }
        } catch (AuthenticationFailedException e) {
            log.error("IMAP Authentication failed for {}: {}", username, e.getMessage());
        } catch (Exception e) {
            log.error("Error reading from IMAP mailbox: {}", e.getMessage());
        } finally {
            if (folder != null && folder.isOpen()) {
                try { folder.close(false); } catch (Exception ignored) {}
            }
            if (store != null && store.isConnected()) {
                try { store.close(); } catch (Exception ignored) {}
            }
        }

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
