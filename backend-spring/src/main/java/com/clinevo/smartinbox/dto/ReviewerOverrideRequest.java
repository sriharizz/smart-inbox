package com.clinevo.smartinbox.dto;

import java.util.Map;

public class ReviewerOverrideRequest {
    private String reviewerUsername = "safety.reviewer@clinevo.com";
    private String newCategory;
    private String justification;
    private Map<String, String> fieldEdits;

    public ReviewerOverrideRequest() {}

    public String getReviewerUsername() { return reviewerUsername; }
    public void setReviewerUsername(String reviewerUsername) { this.reviewerUsername = reviewerUsername; }

    public String getNewCategory() { return newCategory; }
    public void setNewCategory(String newCategory) { this.newCategory = newCategory; }

    public String getJustification() { return justification; }
    public void setJustification(String justification) { this.justification = justification; }

    public Map<String, String> getFieldEdits() { return fieldEdits; }
    public void setFieldEdits(Map<String, String> fieldEdits) { this.fieldEdits = fieldEdits; }
}
