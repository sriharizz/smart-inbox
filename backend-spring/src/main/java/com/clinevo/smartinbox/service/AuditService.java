package com.clinevo.smartinbox.service;

import com.clinevo.smartinbox.model.AuditEventEntity;
import com.clinevo.smartinbox.repository.AuditEventRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;

@Service
public class AuditService {

    private static final Logger log = LoggerFactory.getLogger(AuditService.class);

    private final AuditEventRepository auditEventRepository;

    public AuditService(AuditEventRepository auditEventRepository) {
        this.auditEventRepository = auditEventRepository;
    }

    @Transactional
    public AuditEventEntity logEvent(Long messageId, String reviewerUsername, String action,
                                     String targetField, String originalValue, String newValue,
                                     String reviewerComments) {
        AuditEventEntity event = new AuditEventEntity();
        event.setMessageId(messageId);
        event.setReviewerUsername(reviewerUsername != null ? reviewerUsername : "safety.reviewer@clinevo.com");
        event.setAction(action);
        event.setTargetField(targetField);
        event.setOriginalValue(originalValue);
        event.setNewValue(newValue);
        event.setReviewerComments(reviewerComments);
        event.setTimestamp(LocalDateTime.now());
        event.setIsImmutable(true);

        AuditEventEntity saved = auditEventRepository.save(event);
        log.info("[AUDIT] Action: {} on Message ID: {} by User: {} - Field: {}", action, messageId, reviewerUsername, targetField);
        return saved;
    }

    @Transactional(readOnly = true)
    public List<AuditEventEntity> getAuditTrail(Long messageId) {
        return auditEventRepository.findByMessageIdOrderByTimestampDesc(messageId);
    }

    @Transactional(readOnly = true)
    public List<AuditEventEntity> getAllAuditEvents() {
        return auditEventRepository.findAllByOrderByTimestampDesc();
    }
}
