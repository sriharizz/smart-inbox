package com.clinevo.smartinbox.model;

import com.fasterxml.jackson.annotation.JsonIgnore;
import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "ATTACHMENTS")
public class AttachmentEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @JsonIgnore
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "MESSAGE_ID", nullable = false)
    private IntakeMessageEntity message;

    @Column(name = "FILENAME", length = 255, nullable = false)
    private String filename;

    @Column(name = "CONTENT_TYPE", length = 100)
    private String contentType;

    @Column(name = "SIZE_BYTES")
    private Long sizeBytes;

    @Column(name = "FLAVOR", length = 50)
    private String flavor; // digital_form, scanned_handwritten, literature_article, non_english

    @Column(name = "LANGUAGE", length = 50)
    private String language = "English";

    @Lob
    @Column(name = "DOCUMENT_SUMMARY")
    private String documentSummary;

    @Lob
    @Column(name = "CONTENT_BYTES")
    private byte[] contentBytes;

    @Column(name = "CREATED_AT", nullable = false)
    private LocalDateTime createdAt = LocalDateTime.now();

    public AttachmentEntity() {}

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public IntakeMessageEntity getMessage() { return message; }
    public void setMessage(IntakeMessageEntity message) { this.message = message; }

    public String getFilename() { return filename; }
    public void setFilename(String filename) { this.filename = filename; }

    public String getContentType() { return contentType; }
    public void setContentType(String contentType) { this.contentType = contentType; }

    public Long getSizeBytes() { return sizeBytes; }
    public void setSizeBytes(Long sizeBytes) { this.sizeBytes = sizeBytes; }

    public String getFlavor() { return flavor; }
    public void setFlavor(String flavor) { this.flavor = flavor; }

    public String getLanguage() { return language; }
    public void setLanguage(String language) { this.language = language; }

    public String getDocumentSummary() { return documentSummary; }
    public void setDocumentSummary(String documentSummary) { this.documentSummary = documentSummary; }

    public byte[] getContentBytes() { return contentBytes; }
    public void setContentBytes(byte[] contentBytes) { this.contentBytes = contentBytes; }

    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
}

