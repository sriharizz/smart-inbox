package com.clinevo.smartinbox.dto;

public class ReviewerAcceptRequest {
    private String reviewerUsername = "safety.reviewer@clinevo.com";
    private String comments;

    public ReviewerAcceptRequest() {}

    public String getReviewerUsername() { return reviewerUsername; }
    public void setReviewerUsername(String reviewerUsername) { this.reviewerUsername = reviewerUsername; }

    public String getComments() { return comments; }
    public void setComments(String comments) { this.comments = comments; }
}
