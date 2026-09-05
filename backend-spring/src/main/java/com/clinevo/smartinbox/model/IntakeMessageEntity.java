package com.clinevo.smartinbox.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

@Entity
@Table(name = "INTAKE_MESSAGES")
public class IntakeMessageEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "MESSAGE_ID", length = 255)
    private String messageId;

    @Column(name = "SENDER", length = 255)
    private String sender;

    @Column(name = "SENDER_EMAIL", length = 255)
    private String senderEmail;

    @Column(name = "RECIPIENT", length = 255)
    private String recipient;

    @Column(name = "SUBJECT", length = 500)
    private String subject;

    @Column(name = "RECEIVED_DATE", length = 100)
    private String receivedDate;

    @Lob
    @Column(name = "RAW_BODY")
    private String rawBody;

    @Column(name = "STATUS", length = 50, nullable = false)
    private String status = "RECEIVED"; // RECEIVED, PROCESSING, TRIAGED, REVIEWED, OVERRIDDEN, FAILED

    @Column(name = "PRIMARY_CATEGORY", length = 100)
    private String primaryCategory;

    @Column(name = "CONFIDENCE")
    private Double confidence;

    @Column(name = "IS_MULTI_LABEL")
    private Boolean isMultiLabel = false;

    @Lob
    @Column(name = "LABELS_JSON")
    private String labelsJson;

    @Lob
    @Column(name = "EXECUTIVE_SUMMARY")
    private String executiveSummary;

    @Column(name = "CREATED_AT", nullable = false)
    private LocalDateTime createdAt = LocalDateTime.now();

    @Column(name = "UPDATED_AT", nullable = false)
    private LocalDateTime updatedAt = LocalDateTime.now();

    @OneToMany(mappedBy = "message", cascade = CascadeType.ALL, orphanRemoval = true, fetch = FetchType.EAGER)
    private List<AttachmentEntity> attachments = new ArrayList<>();

    @OneToOne(mappedBy = "message", cascade = CascadeType.ALL, orphanRemoval = true, fetch = FetchType.EAGER)
    private IcsrReportEntity icsrReport;

    @OneToOne(mappedBy = "message", cascade = CascadeType.ALL, orphanRemoval = true, fetch = FetchType.EAGER)
    private PqcReportEntity pqcReport;

    @OneToOne(mappedBy = "message", cascade = CascadeType.ALL, orphanRemoval = true, fetch = FetchType.EAGER)
    private MedicalInfoEntity medicalInfo;

    public IntakeMessageEntity() {}

    // Getters and Setters
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getMessageId() { return messageId; }
    public void setMessageId(String messageId) { this.messageId = messageId; }

    public String getSender() { return sender; }
    public void setSender(String sender) { this.sender = sender; }

    public String getSenderEmail() { return senderEmail; }
    public void setSenderEmail(String senderEmail) { this.senderEmail = senderEmail; }

    public String getRecipient() { return recipient; }
    public void setRecipient(String recipient) { this.recipient = recipient; }

    public String getSubject() { return subject; }
    public void setSubject(String subject) { this.subject = subject; }

    public String getReceivedDate() { return receivedDate; }
    public void setReceivedDate(String receivedDate) { this.receivedDate = receivedDate; }

    public String getRawBody() { return rawBody; }
    public void setRawBody(String rawBody) { this.rawBody = rawBody; }

    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }

    public String getPrimaryCategory() { return primaryCategory; }
    public void setPrimaryCategory(String primaryCategory) { this.primaryCategory = primaryCategory; }

    public Double getConfidence() { return confidence; }
    public void setConfidence(Double confidence) { this.confidence = confidence; }

    public Boolean getIsMultiLabel() { return isMultiLabel; }
    public void setIsMultiLabel(Boolean multiLabel) { isMultiLabel = multiLabel; }

    public String getLabelsJson() { return labelsJson; }
    public void setLabelsJson(String labelsJson) { this.labelsJson = labelsJson; }

    public String getExecutiveSummary() { return executiveSummary; }
    public void setExecutiveSummary(String executiveSummary) { this.executiveSummary = executiveSummary; }

    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }

    public LocalDateTime getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(LocalDateTime updatedAt) { this.updatedAt = updatedAt; }

    public List<AttachmentEntity> getAttachments() { return attachments; }
    public void setAttachments(List<AttachmentEntity> attachments) { this.attachments = attachments; }

    public IcsrReportEntity getIcsrReport() { return icsrReport; }
    public void setIcsrReport(IcsrReportEntity icsrReport) {
        this.icsrReport = icsrReport;
        if (icsrReport != null) icsrReport.setMessage(this);
    }

    public PqcReportEntity getPqcReport() { return pqcReport; }
    public void setPqcReport(PqcReportEntity pqcReport) {
        this.pqcReport = pqcReport;
        if (pqcReport != null) pqcReport.setMessage(this);
    }

    public MedicalInfoEntity getMedicalInfo() { return medicalInfo; }
    public void setMedicalInfo(MedicalInfoEntity medicalInfo) {
        this.medicalInfo = medicalInfo;
        if (medicalInfo != null) medicalInfo.setMessage(this);
    }

    public void addAttachment(AttachmentEntity attachment) {
        attachments.add(attachment);
        attachment.setMessage(this);
    }

    @PreUpdate
    public void onUpdate() {
        this.updatedAt = LocalDateTime.now();
    }
}
