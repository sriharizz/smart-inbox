package com.clinevo.smartinbox.model;

import com.fasterxml.jackson.annotation.JsonIgnore;
import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "PQC_REPORTS")
public class PqcReportEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @JsonIgnore
    @OneToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "MESSAGE_ID", nullable = false)
    private IntakeMessageEntity message;

    @Column(name = "PRODUCT_NAME", length = 255)
    private String productName = "Not stated";

    @Column(name = "LOT_NUMBER", length = 255)
    private String lotNumber = "Not stated";

    @Column(name = "DEFECT_TYPE", length = 1000)
    private String defectType = "Not stated";

    @Lob
    @Column(name = "DEFECT_DESCRIPTION")
    private String defectDescription = "Not stated";

    @Column(name = "PACKAGING_BREACHED")
    private Boolean packagingBreached = false;

    @Column(name = "PHOTO_DETECTED")
    private Boolean photoDetected = false;

    @Lob
    @Column(name = "PHOTO_DESCRIPTION")
    private String photoDescription = "Not stated";

    @Column(name = "REQUIRES_HUMAN_REVIEW")
    private Boolean requiresHumanReview = false;

    @Lob
    @Column(name = "SOURCE_CITATIONS_JSON")
    private String sourceCitationsJson;

    @Column(name = "CREATED_AT", nullable = false)
    private LocalDateTime createdAt = LocalDateTime.now();

    public PqcReportEntity() {}

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public IntakeMessageEntity getMessage() { return message; }
    public void setMessage(IntakeMessageEntity message) { this.message = message; }

    public String getProductName() { return productName; }
    public void setProductName(String productName) { this.productName = productName; }

    public String getLotNumber() { return lotNumber; }
    public void setLotNumber(String lotNumber) { this.lotNumber = lotNumber; }

    public String getDefectType() { return defectType; }
    public void setDefectType(String defectType) { this.defectType = defectType; }

    public String getDefectDescription() { return defectDescription; }
    public void setDefectDescription(String defectDescription) { this.defectDescription = defectDescription; }

    public Boolean getPackagingBreached() { return packagingBreached; }
    public void setPackagingBreached(Boolean packagingBreached) { this.packagingBreached = packagingBreached; }

    public Boolean getPhotoDetected() { return photoDetected; }
    public void setPhotoDetected(Boolean photoDetected) { this.photoDetected = photoDetected; }

    public String getPhotoDescription() { return photoDescription; }
    public void setPhotoDescription(String photoDescription) { this.photoDescription = photoDescription; }

    public Boolean getRequiresHumanReview() { return requiresHumanReview; }
    public void setRequiresHumanReview(Boolean requiresHumanReview) { this.requiresHumanReview = requiresHumanReview; }

    public String getSourceCitationsJson() { return sourceCitationsJson; }
    public void setSourceCitationsJson(String sourceCitationsJson) { this.sourceCitationsJson = sourceCitationsJson; }

    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
}
