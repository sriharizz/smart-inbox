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
        if (autoIngestOnStartup) {
            log.info("Auto-ingestion enabled on startup. Ingestion mode: {}", ingestionMode);
            try {
                triggerIngestion();
            } catch (Exception e) {
                log.error("Error during startup ingestion: {}", e.getMessage(), e);
            }
        }
    }

    public synchronized int triggerIngestion() throws Exception {
        IngestionSource source = "IMAP".equalsIgnoreCase(ingestionMode) ? imapIngestionSource : fixtureIngestionSource;
        log.info("Triggering mailbox ingestion from source: {}", source.getSourceName());

        List<RawEmailPayload> emails = source.fetchNewEmails();
        int newMessagesCount = 0;

        for (RawEmailPayload email : emails) {
            if (messageRepository.existsByMessageId(email.messageId())) {
                log.debug("Skipping already ingested message: {}", email.messageId());
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
                    } else if (lowerName.contains("es") || lowerName.contains("de") || lowerName.contains("notificacion") || lowerName.contains("bericht")) {
                        attEntity.setFlavor("non_english");
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
            asyncDocumentProcessor.processMessageAsync(saved.getId(), email.rawBytes(), email.filename());
        }

        log.info("Ingestion run complete. Ingested {} new messages.", newMessagesCount);
        return newMessagesCount;
    }
}
