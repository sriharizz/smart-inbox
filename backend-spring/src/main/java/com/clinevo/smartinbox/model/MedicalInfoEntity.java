package com.clinevo.smartinbox.model;

import com.fasterxml.jackson.annotation.JsonIgnore;
import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "MEDICAL_INFO_REPORTS")
public class MedicalInfoEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @JsonIgnore
    @OneToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "MESSAGE_ID", nullable = false)
    private IntakeMessageEntity message;

    @Column(name = "PRODUCT_OR_TOPIC", length = 255)
    private String productOrTopic = "Not stated";

    @Column(name = "INQUIRY_TYPE", length = 100)
    private String inquiryType = "Not stated";

    @Lob
    @Column(name = "QUESTION_TEXT")
    private String questionText = "Not stated";

    @Lob
    @Column(name = "SOURCE_CITATIONS_JSON")
    private String sourceCitationsJson;

    @Column(name = "CREATED_AT", nullable = false)
    private LocalDateTime createdAt = LocalDateTime.now();

    public MedicalInfoEntity() {}

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public IntakeMessageEntity getMessage() { return message; }
    public void setMessage(IntakeMessageEntity message) { this.message = message; }

    public String getProductOrTopic() { return productOrTopic; }
    public void setProductOrTopic(String productOrTopic) { this.productOrTopic = productOrTopic; }

    public String getInquiryType() { return inquiryType; }
    public void setInquiryType(String inquiryType) { this.inquiryType = inquiryType; }

    public String getQuestionText() { return questionText; }
    public void setQuestionText(String questionText) { this.questionText = questionText; }

    public String getSourceCitationsJson() { return sourceCitationsJson; }
    public void setSourceCitationsJson(String sourceCitationsJson) { this.sourceCitationsJson = sourceCitationsJson; }

    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
}
