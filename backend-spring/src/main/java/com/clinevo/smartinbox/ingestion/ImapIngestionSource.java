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

    private final java.time.Instant startupInstant = java.time.Instant.now();
    private final java.util.concurrent.atomic.AtomicLong baselineMaxUid = new java.util.concurrent.atomic.AtomicLong(-1L);
    private final java.util.concurrent.atomic.AtomicBoolean baselineInitialized = new java.util.concurrent.atomic.AtomicBoolean(false);
    private final java.util.Set<String> historicalMessageIds = java.util.concurrent.ConcurrentHashMap.newKeySet();

    @Override
    public String getSourceName() {
        return "LIVE_IMAP";
    }

    @Override
    public List<RawEmailPayload> fetchNewEmails() throws Exception {
        return fetchNewEmails(msgId -> false);
    }

    @Override
    public List<RawEmailPayload> fetchNewEmails(java.util.function.Predicate<String> isAlreadyIngested) throws Exception {
        List<RawEmailPayload> results = new ArrayList<>();

        Properties props = new Properties();
        props.put("mail.store.protocol", "imaps");
        props.put("mail.imaps.host", host);
        props.put("mail.imaps.port", String.valueOf(port));
        props.put("mail.imaps.ssl.enable", String.valueOf(ssl));
        props.put("mail.imaps.connectiontimeout", "15000");
        props.put("mail.imaps.timeout", "25000");
        props.put("mail.imaps.writetimeout", "15000");
        props.put("mail.imap.connectiontimeout", "15000");
        props.put("mail.imap.timeout", "25000");
        props.put("mail.imap.writetimeout", "15000");
        props.put("mail.imaps.partialfetch", "false");
        props.put("mail.imaps.fetchsize", "1048576");

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

            UIDFolder uidFolder = (folder instanceof UIDFolder u) ? u : null;

            if (messages.length == 0) {
                if (!baselineInitialized.get()) {
                    baselineMaxUid.set(0L);
                    baselineInitialized.set(true);
                    log.info("IMAP mailbox connected (empty). Baseline initialized at UID 0; ready for incoming emails.");
                }
                return results;
            }

            // 1. Batch header pre-fetch in a single lightweight IMAP command
            FetchProfile fp = new FetchProfile();
            fp.add(FetchProfile.Item.ENVELOPE);
            if (uidFolder != null) {
                fp.add(UIDFolder.FetchProfileItem.UID);
            }
            fp.add("Message-ID");
            folder.fetch(messages, fp);

            // Establish startup baseline: historical messages present at boot are strictly recorded and not re-ingested
            if (!baselineInitialized.get()) {
                long currentMaxUid = -1L;
                for (Message msg : messages) {
                    try {
                        if (uidFolder != null) {
                            long uid = uidFolder.getUID(msg);
                            if (uid > currentMaxUid) {
                                currentMaxUid = uid;
                            }
                        }
                        if (msg instanceof MimeMessage mimeMsg) {
                            String rawId = mimeMsg.getMessageID();
                            if ((rawId == null || rawId.isBlank()) && mimeMsg.getHeader("Message-ID") != null && mimeMsg.getHeader("Message-ID").length > 0) {
                                rawId = mimeMsg.getHeader("Message-ID")[0];
                            }
                            if (rawId != null && !rawId.isBlank()) {
                                historicalMessageIds.add(rawId.replaceAll("[<>]", "").trim());
                            }
                        }
                    } catch (Exception ignored) {}
                }
                baselineMaxUid.set(Math.max(currentMaxUid, 0L));
                baselineInitialized.set(true);
                log.info("IMAP mailbox baseline established at UID {}. {} historical messages in mailbox ({} IDs indexed) will NOT be re-ingested; waiting strictly for new incoming emails sent post-startup.",
                        baselineMaxUid.get(), messages.length, historicalMessageIds.size());
                return results;
            }

            for (Message msg : messages) {
                if (msg instanceof MimeMessage mimeMsg) {
                    long uid = msg.getMessageNumber();
                    if (uidFolder != null) {
                        try {
                            uid = uidFolder.getUID(msg);
                        } catch (Exception ignored) {}
                    }

                    // 1. Skip historical baseline messages by UID
                    if (baselineMaxUid.get() >= 0 && uid <= baselineMaxUid.get()) {
                        log.debug("Skipping baseline historical email [UID: {}]", uid);
                        continue;
                    }

                    String rawMessageId = mimeMsg.getMessageID();
                    if ((rawMessageId == null || rawMessageId.isBlank()) && mimeMsg.getHeader("Message-ID") != null && mimeMsg.getHeader("Message-ID").length > 0) {
                        rawMessageId = mimeMsg.getHeader("Message-ID")[0];
                    }

                    String messageId;
                    if (rawMessageId == null || rawMessageId.isBlank()) {
                        messageId = "IMAP-UID-" + uid;
                    } else {
                        messageId = rawMessageId.replaceAll("[<>]", "").trim();
                    }

                    // 2. Skip known historical Message-IDs
                    if (historicalMessageIds.contains(messageId)) {
                        log.debug("Skipping known historical email ID: {}", messageId);
                        continue;
                    }

                    // 3. Skip messages sent/received prior to application startup
                    try {
                        Date sentDate = mimeMsg.getSentDate();
                        Date receivedDate = mimeMsg.getReceivedDate();
                        Date relevantDate = sentDate != null ? sentDate : receivedDate;
                        if (relevantDate != null) {
                            if (relevantDate.toInstant().isBefore(startupInstant.minusSeconds(15))) {
                                log.debug("Skipping pre-startup email [Date: {}, MsgID: {}]", relevantDate, messageId);
                                historicalMessageIds.add(messageId);
                                continue;
                            }
                        }
                    } catch (Exception ignored) {}

                    // 4. Skip already ingested messages BEFORE downloading full MIME
                    if (isAlreadyIngested != null && isAlreadyIngested.test(messageId)) {
                        log.debug("Skipping already ingested email [UID: {}, MsgID: {}]", uid, messageId);
                        continue;
                    }

                    log.info("Discovered new live incoming email [UID: {}, MsgID: {}, Subject: {}]", uid, messageId, mimeMsg.getSubject());

                    // 3. Download raw bytes once
                    ByteArrayOutputStream baos = new ByteArrayOutputStream();
                    mimeMsg.writeTo(baos);
                    byte[] rawBytes = baos.toByteArray();

                    // 4. Parse in-memory to prevent secondary IMAP network round-trips during attachment extraction
                    MimeMessage parsedInMemoryMsg;
                    try (InputStream bais = new java.io.ByteArrayInputStream(rawBytes)) {
                        parsedInMemoryMsg = new MimeMessage(session, bais);
                    }

                    String subject = "No Subject";
                    try {
                        if (parsedInMemoryMsg.getSubject() != null) {
                            subject = jakarta.mail.internet.MimeUtility.decodeText(parsedInMemoryMsg.getSubject());
                        }
                    } catch (Exception ignored) {
                        subject = parsedInMemoryMsg.getSubject() != null ? parsedInMemoryMsg.getSubject() : "No Subject";
                    }

                    String date = parsedInMemoryMsg.getSentDate() != null ? parsedInMemoryMsg.getSentDate().toString() : "";

                    String senderName = "";
                    String senderEmail = "";
                    if (parsedInMemoryMsg.getFrom() != null && parsedInMemoryMsg.getFrom().length > 0) {
                        InternetAddress address = (InternetAddress) parsedInMemoryMsg.getFrom()[0];
                        senderName = address.getPersonal() != null ? address.getPersonal() : address.getAddress();
                        senderEmail = address.getAddress();
                    }

                    String recipient = "";
                    if (parsedInMemoryMsg.getAllRecipients() != null && parsedInMemoryMsg.getAllRecipients().length > 0) {
                        recipient = parsedInMemoryMsg.getAllRecipients()[0].toString();
                    }

                    StringBuilder bodyText = new StringBuilder();
                    List<RawAttachmentPayload> attachments = new ArrayList<>();
                    extractParts(parsedInMemoryMsg, bodyText, attachments);

                    results.add(new RawEmailPayload(
                            "imap_" + uid + ".eml",
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
                    if (uidFolder != null && uid > baselineMaxUid.get()) {
                        baselineMaxUid.set(uid);
                    }
                    log.info("Successfully fetched new email [UID: {}, MsgID: {}] with {} attachments", uid, messageId, attachments.size());
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
                try {
                    fileName = jakarta.mail.internet.MimeUtility.decodeText(fileName);
                } catch (Exception ignored) {}
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
