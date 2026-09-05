package com.clinevo.smartinbox.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "AUDIT_LOG")
public class AuditEventEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "MESSAGE_ID")
    private Long messageId;

    @Column(name = "TIMESTAMP", nullable = false)
    private LocalDateTime timestamp = LocalDateTime.now();

    @Column(name = "REVIEWER_USERNAME", length = 100, nullable = false)
    private String reviewerUsername = "safety.reviewer@clinevo.com";

    @Column(name = "ACTION", length = 50, nullable = false)
    private String action; // ACCEPT, OVERRIDE_CATEGORY, EDIT_FIELD, ADD_COMMENT, INGESTION

    @Column(name = "TARGET_FIELD", length = 100)
    private String targetField;

    @Lob
    @Column(name = "ORIGINAL_VALUE")
    private String originalValue;

    @Lob
    @Column(name = "NEW_VALUE")
    private String newValue;

    @Lob
    @Column(name = "REVIEWER_COMMENTS")
    private String reviewerComments;

    @Column(name = "IS_IMMUTABLE", nullable = false)
    private Boolean isImmutable = true;

    public AuditEventEntity() {}

    public AuditEventEntity(Long messageId, String reviewerUsername, String action, String targetField, String originalValue, String newValue, String reviewerComments) {
        this.messageId = messageId;
        this.reviewerUsername = reviewerUsername;
        this.action = action;
        this.targetField = targetField;
        this.originalValue = originalValue;
        this.newValue = newValue;
        this.reviewerComments = reviewerComments;
        this.timestamp = LocalDateTime.now();
        this.isImmutable = true;
    }

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public Long getMessageId() { return messageId; }
    public void setMessageId(Long messageId) { this.messageId = messageId; }

    public LocalDateTime getTimestamp() { return timestamp; }
    public void setTimestamp(LocalDateTime timestamp) { this.timestamp = timestamp; }

    public String getReviewerUsername() { return reviewerUsername; }
    public void setReviewerUsername(String reviewerUsername) { this.reviewerUsername = reviewerUsername; }

    public String getAction() { return action; }
    public void setAction(String action) { this.action = action; }

    public String getTargetField() { return targetField; }
    public void setTargetField(String targetField) { this.targetField = targetField; }

    public String getOriginalValue() { return originalValue; }
    public void setOriginalValue(String originalValue) { this.originalValue = originalValue; }

    public String getNewValue() { return newValue; }
    public void setNewValue(String newValue) { this.newValue = newValue; }

    public String getReviewerComments() { return reviewerComments; }
    public void setReviewerComments(String reviewerComments) { this.reviewerComments = reviewerComments; }

    public Boolean getIsImmutable() { return isImmutable; }
    public void setIsImmutable(Boolean isImmutable) { this.isImmutable = isImmutable; }
}
