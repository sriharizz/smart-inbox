package com.clinevo.smartinbox.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import java.util.List;

@JsonIgnoreProperties(ignoreUnknown = true)
public class LiteratureScreenResultDto {

    private Long id;
    private String filename;
    private String article_title;
    private String authors;
    private String journal;
    private String publication_year;
    private boolean is_reportable;
    private String exclusion_reason;
    private String study_type;
    private int patient_cases_count;
    private List<ExtractionResultDto> individual_cases;
    private String screening_summary;
    private String review_status = "PENDING";
    private String reviewed_by;
    private String reviewed_at;
    private String reviewer_comments;

    public LiteratureScreenResultDto() {}

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public String getFilename() { return filename; }
    public void setFilename(String filename) { this.filename = filename; }

    public String getReview_status() { return review_status; }
    public void setReview_status(String review_status) { this.review_status = review_status; }

    public String getReviewed_by() { return reviewed_by; }
    public void setReviewed_by(String reviewed_by) { this.reviewed_by = reviewed_by; }

    public String getReviewed_at() { return reviewed_at; }
    public void setReviewed_at(String reviewed_at) { this.reviewed_at = reviewed_at; }

    public String getReviewer_comments() { return reviewer_comments; }
    public void setReviewer_comments(String reviewer_comments) { this.reviewer_comments = reviewer_comments; }

    public String getArticle_title() { return article_title; }
    public void setArticle_title(String article_title) { this.article_title = article_title; }

    public String getAuthors() { return authors; }
    public void setAuthors(String authors) { this.authors = authors; }

    public String getJournal() { return journal; }
    public void setJournal(String journal) { this.journal = journal; }

    public String getPublication_year() { return publication_year; }
    public void setPublication_year(String publication_year) { this.publication_year = publication_year; }

    public boolean isIs_reportable() { return is_reportable; }
    public void setIs_reportable(boolean is_reportable) { this.is_reportable = is_reportable; }

    public String getExclusion_reason() { return exclusion_reason; }
    public void setExclusion_reason(String exclusion_reason) { this.exclusion_reason = exclusion_reason; }

    public String getStudy_type() { return study_type; }
    public void setStudy_type(String study_type) { this.study_type = study_type; }

    public int getPatient_cases_count() { return patient_cases_count; }
    public void setPatient_cases_count(int patient_cases_count) { this.patient_cases_count = patient_cases_count; }

    public List<ExtractionResultDto> getIndividual_cases() { return individual_cases; }
    public void setIndividual_cases(List<ExtractionResultDto> individual_cases) { this.individual_cases = individual_cases; }

    public String getScreening_summary() { return screening_summary; }
    public void setScreening_summary(String screening_summary) { this.screening_summary = screening_summary; }
}
