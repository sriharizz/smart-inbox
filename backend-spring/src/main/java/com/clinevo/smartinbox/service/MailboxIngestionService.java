package com.clinevo.smartinbox.service;

import com.clinevo.smartinbox.ingestion.*;
import com.clinevo.smartinbox.model.AttachmentEntity;
import com.clinevo.smartinbox.model.IntakeMessageEntity;
import com.clinevo.smartinbox.repository.IntakeMessageRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Optional;
import java.util.concurrent.locks.ReentrantLock;

@Service
public class MailboxIngestionService {

    private static final Logger log = LoggerFactory.getLogger(MailboxIngestionService.class);

    private final FixtureIngestionSource fixtureIngestionSource;
    private final ImapIngestionSource imapIngestionSource;
    private final IntakeMessageRepository messageRepository;
    private final AsyncDocumentProcessor asyncDocumentProcessor;
    private final AuditService auditService;

    @Value("${smartinbox.ingestion.mode:FIXTURE}")
    private String ingestionMode;

    @Value("${smartinbox.ingestion.auto-ingest-on-startup:true}")
    private boolean autoIngestOnStartup;

    @Value("${smartinbox.ingestion.fresh-processing:true}")
    private boolean freshProcessing;

    private final ReentrantLock ingestionLock = new ReentrantLock();

    public MailboxIngestionService(FixtureIngestionSource fixtureIngestionSource,
                                   ImapIngestionSource imapIngestionSource,
                                   IntakeMessageRepository messageRepository,
                                   AsyncDocumentProcessor asyncDocumentProcessor,
                                   AuditService auditService) {
        this.fixtureIngestionSource = fixtureIngestionSource;
        this.imapIngestionSource = imapIngestionSource;
        this.messageRepository = messageRepository;
        this.asyncDocumentProcessor = asyncDocumentProcessor;
        this.auditService = auditService;
    }

    @EventListener(ApplicationReadyEvent.class)
    public void onStartup() {
        cleanupSpuriousRecords();
        if (autoIngestOnStartup) {
            log.info("Auto-ingestion enabled on startup. Ingestion mode: {}", ingestionMode);
            try {
                triggerIngestion();
            } catch (Exception e) {
                log.error("Error during startup ingestion: {}", e.getMessage(), e);
            }
        }
    }

    private void cleanupSpuriousRecords() {
        try {
            List<IntakeMessageEntity> all = messageRepository.findAll();
            for (IntakeMessageEntity msg : all) {
                boolean isFailed = "FAILED".equalsIgnoreCase(msg.getStatus());
                boolean isSpuriousSender = msg.getSenderEmail() != null &&
                        (msg.getSenderEmail().contains("srihan") || msg.getSenderEmail().contains("clinevo.test.inbox12"));
                boolean isSpuriousSubject = msg.getSubject() != null && msg.getSubject().contains("Akutes Angioödem");
                if (isFailed || isSpuriousSender || isSpuriousSubject) {
                    log.warn("Purging spurious non-benchmark intake record ID {}: {} ({})", msg.getId(), msg.getSubject(), msg.getStatus());
                    messageRepository.delete(msg);
                }
            }
        } catch (Exception e) {
            log.warn("Startup record cleanup warning: {}", e.getMessage());
        }
    }

    @org.springframework.scheduling.annotation.Scheduled(
            fixedDelayString = "${smartinbox.ingestion.imap.poll-interval-ms:30000}",
            initialDelayString = "${smartinbox.ingestion.imap.initial-delay-ms:5000}")
    public void pollMailboxScheduled() {
        if ("IMAP".equalsIgnoreCase(ingestionMode)) {
            try {
                int count = triggerIngestion();
                if (count > 0) {
                    log.info("[SCHEDULED-POLLER] Ingested {} new messages from IMAP", count);
                }
            } catch (Exception e) {
                log.warn("[SCHEDULED-POLLER] Polling error: {}", e.getMessage());
            }
        }
    }

    public int triggerIngestion() throws Exception {
        if (!ingestionLock.tryLock()) {
            log.info("Mailbox ingestion is already in-flight; skipping redundant trigger.");
            return 0;
        }
        try {
            IngestionSource source = "IMAP".equalsIgnoreCase(ingestionMode) ? imapIngestionSource : fixtureIngestionSource;
            log.info("Triggering mailbox ingestion from source: {}", source.getSourceName());

            List<RawEmailPayload> emails = source.fetchNewEmails(messageRepository::existsByMessageId);
            int newMessagesCount = 0;

            for (RawEmailPayload email : emails) {
                Optional<IntakeMessageEntity> existingOpt = messageRepository.findByMessageId(email.messageId());
                if (existingOpt.isPresent()) {
                    IntakeMessageEntity existing = existingOpt.get();
                    if ("RECEIVED".equals(existing.getStatus())) {
                        log.info("Triggering async processing for uncompleted message: {} (ID: {})", email.messageId(), existing.getId());
                        asyncDocumentProcessor.processMessageAsync(existing.getId(), email.rawBytes(), email.filename(), freshProcessing);
                    }
                    continue;
                }

                IntakeMessageEntity entity = new IntakeMessageEntity();
                entity.setMessageId(email.messageId());
                entity.setSender(email.sender());
                entity.setSenderEmail(email.senderEmail());
                entity.setRecipient(email.recipient());
                entity.setSubject(email.subject());
                entity.setReceivedDate(email.date());
                entity.setRawBody(email.bodyText());
                entity.setStatus("RECEIVED");

                if (email.attachments() != null) {
                    for (RawAttachmentPayload att : email.attachments()) {
                        AttachmentEntity attEntity = new AttachmentEntity();
                        attEntity.setFilename(att.filename());
                        attEntity.setContentType(att.contentType());
                        attEntity.setSizeBytes(att.sizeBytes());
                        attEntity.setContentBytes(att.bytes());
                        
                        String lowerName = att.filename().toLowerCase();
                        if (lowerName.contains("cioms") || lowerName.contains("fda") || lowerName.contains("form")) {
                            attEntity.setFlavor("digital_form");
                        } else if (lowerName.contains("clinic") || lowerName.contains("handwritten")) {
                            attEntity.setFlavor("scanned_handwritten");
                        } else if (lowerName.contains("article") || lowerName.contains("journal")) {
                            attEntity.setFlavor("literature_article");
                        } else {
                            attEntity.setFlavor("digital_form");
                        }
                        
                        entity.addAttachment(attEntity);
                    }
                }

                IntakeMessageEntity saved = messageRepository.save(entity);
                newMessagesCount++;

                auditService.logEvent(
                        saved.getId(),
                        "SYSTEM_INGESTOR",
                        "MESSAGE_INGESTED",
                        "STATUS",
                        "NEW",
                        "RECEIVED",
                        "Ingested from " + source.getSourceName() + " (" + email.filename() + ") with " + entity.getAttachments().size() + " attachments"
                );

                // Dispatch asynchronous processing
                asyncDocumentProcessor.processMessageAsync(saved.getId(), email.rawBytes(), email.filename(), freshProcessing);
            }

            log.info("Ingestion run complete. Ingested {} new messages.", newMessagesCount);
            return newMessagesCount;
        } finally {
            ingestionLock.unlock();
        }
    }

    public IntakeMessageEntity ingestSingleFixtureEmail(String filename, boolean fresh) throws Exception {
        List<RawEmailPayload> emails = fixtureIngestionSource.fetchNewEmails();
        RawEmailPayload target = emails.stream()
                .filter(e -> filename.equalsIgnoreCase(e.filename()))
                .findFirst()
                .orElseThrow(() -> new IllegalArgumentException("Fixture email not found in test-data/emails: " + filename));

        // Clean up any existing record with this messageId so we get a fresh, isolated test ingestion
        Optional<IntakeMessageEntity> existingOpt = messageRepository.findByMessageId(target.messageId());
        existingOpt.ifPresent(messageRepository::delete);

        IntakeMessageEntity entity = new IntakeMessageEntity();
        entity.setMessageId(target.messageId());
        entity.setSender(target.sender());
        entity.setSenderEmail(target.senderEmail());
        entity.setRecipient(target.recipient());
        entity.setSubject(target.subject());
        entity.setReceivedDate(target.date());
        entity.setRawBody(target.bodyText());
        entity.setStatus("RECEIVED");

        if (target.attachments() != null) {
            for (RawAttachmentPayload att : target.attachments()) {
                AttachmentEntity attEntity = new AttachmentEntity();
                attEntity.setFilename(att.filename());
                attEntity.setContentType(att.contentType());
                attEntity.setSizeBytes(att.sizeBytes());
                attEntity.setContentBytes(att.bytes());

                String lowerName = att.filename().toLowerCase();
                if (lowerName.contains("cioms") || lowerName.contains("fda") || lowerName.contains("form")) {
                    attEntity.setFlavor("digital_form");
                } else if (lowerName.contains("clinic") || lowerName.contains("handwritten")) {
                    attEntity.setFlavor("scanned_handwritten");
                } else if (lowerName.contains("article") || lowerName.contains("journal")) {
                    attEntity.setFlavor("literature_article");
                } else {
                    attEntity.setFlavor("digital_form");
                }

                entity.addAttachment(attEntity);
            }
        }

        IntakeMessageEntity saved = messageRepository.save(entity);

        auditService.logEvent(
                saved.getId(),
                "SYSTEM_INGESTOR",
                "MESSAGE_INGESTED",
                "STATUS",
                "NEW",
                "RECEIVED",
                "Fixture benchmark ingested: " + target.filename() + " (attachments: " + entity.getAttachments().size() + ")"
        );

        asyncDocumentProcessor.processMessageAsync(saved.getId(), target.rawBytes(), target.filename(), fresh);
        return saved;
    }
}
