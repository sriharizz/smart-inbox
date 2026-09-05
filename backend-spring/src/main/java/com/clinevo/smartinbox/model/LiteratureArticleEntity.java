package com.clinevo.smartinbox.model;

import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "LITERATURE_ARTICLES")
public class LiteratureArticleEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "FILENAME", length = 255, nullable = false)
    private String filename;

    @Column(name = "ARTICLE_TITLE", length = 500)
    private String articleTitle;

    @Column(name = "AUTHORS", length = 500)
    private String authors;

    @Column(name = "JOURNAL", length = 255)
    private String journal;

    @Column(name = "PUBLICATION_YEAR", length = 50)
    private String publicationYear;

    @Column(name = "IS_REPORTABLE")
    private Boolean isReportable;

    @Column(name = "EXCLUSION_REASON", length = 500)
    private String exclusionReason;

    @Column(name = "STUDY_TYPE", length = 100)
    private String studyType;

    @Column(name = "PATIENT_CASES_COUNT")
    private Integer patientCasesCount = 0;

    @Lob
    @Column(name = "SCREENING_SUMMARY")
    private String screeningSummary;

    @Lob
    @Column(name = "CASES_JSON")
    private String casesJson;

    @Column(name = "CREATED_AT", nullable = false)
    private LocalDateTime createdAt = LocalDateTime.now();

    public LiteratureArticleEntity() {}

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getFilename() { return filename; }
    public void setFilename(String filename) { this.filename = filename; }

    public String getArticleTitle() { return articleTitle; }
    public void setArticleTitle(String articleTitle) { this.articleTitle = articleTitle; }

    public String getAuthors() { return authors; }
    public void setAuthors(String authors) { this.authors = authors; }

    public String getJournal() { return journal; }
    public void setJournal(String journal) { this.journal = journal; }

    public String getPublicationYear() { return publicationYear; }
    public void setPublicationYear(String publicationYear) { this.publicationYear = publicationYear; }

    public Boolean getIsReportable() { return isReportable; }
    public void setIsReportable(Boolean isReportable) { this.isReportable = isReportable; }

    public String getExclusionReason() { return exclusionReason; }
    public void setExclusionReason(String exclusionReason) { this.exclusionReason = exclusionReason; }

    public String getStudyType() { return studyType; }
    public void setStudyType(String studyType) { this.studyType = studyType; }

    public Integer getPatientCasesCount() { return patientCasesCount; }
    public void setPatientCasesCount(Integer patientCasesCount) { this.patientCasesCount = patientCasesCount; }

    public String getScreeningSummary() { return screeningSummary; }
    public void setScreeningSummary(String screeningSummary) { this.screeningSummary = screeningSummary; }

    public String getCasesJson() { return casesJson; }
    public void setCasesJson(String casesJson) { this.casesJson = casesJson; }

    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
}
