package com.clinevo.smartinbox.controller;

import com.clinevo.smartinbox.dto.LiteratureScreenResultDto;
import com.clinevo.smartinbox.model.LiteratureArticleEntity;
import com.clinevo.smartinbox.repository.LiteratureArticleRepository;
import com.clinevo.smartinbox.service.AiGatewayClient;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.time.LocalDateTime;
import java.util.List;

import com.clinevo.smartinbox.model.AuditEventEntity;
import com.clinevo.smartinbox.service.AuditService;

@RestController
@RequestMapping("/api/literature")
public class LiteratureController {

    private final AiGatewayClient aiGatewayClient;
    private final LiteratureArticleRepository literatureRepository;
    private final AuditService auditService;
    private final ObjectMapper objectMapper;

    public LiteratureController(AiGatewayClient aiGatewayClient,
                                LiteratureArticleRepository literatureRepository,
                                AuditService auditService,
                                ObjectMapper objectMapper) {
        this.aiGatewayClient = aiGatewayClient;
        this.literatureRepository = literatureRepository;
        this.auditService = auditService;
        this.objectMapper = objectMapper;
    }

    @GetMapping
    public List<LiteratureArticleEntity> getAllArticles() {
        return literatureRepository.findAllByOrderByCreatedAtDesc();
    }

    @PostMapping("/upload")
    public ResponseEntity<LiteratureScreenResultDto> uploadAndScreenLiterature(@RequestParam("file") MultipartFile file) {
        try {
            byte[] bytes = file.getBytes();
            String filename = file.getOriginalFilename() != null ? file.getOriginalFilename() : "article.pdf";

            LiteratureScreenResultDto result = aiGatewayClient.screenLiteraturePdf(filename, bytes);

            LiteratureArticleEntity entity = new LiteratureArticleEntity();
            entity.setFilename(filename);
            entity.setArticleTitle(result.getArticle_title());
            entity.setAuthors(result.getAuthors());
            entity.setJournal(result.getJournal());
            entity.setPublicationYear(result.getPublication_year());
            entity.setIsReportable(result.isIs_reportable());
            entity.setExclusionReason(result.getExclusion_reason());
            entity.setStudyType(result.getStudy_type());
            entity.setPatientCasesCount(result.getPatient_cases_count());
            entity.setScreeningSummary(result.getScreening_summary());
            entity.setReviewStatus("PENDING");
            entity.setPdfData(bytes);

            if (result.getIndividual_cases() != null) {
                entity.setCasesJson(objectMapper.writeValueAsString(result.getIndividual_cases()));
            }

            entity.setCreatedAt(LocalDateTime.now());
            literatureRepository.save(entity);

            result.setId(entity.getId());
            result.setFilename(filename);
            result.setReview_status(entity.getReviewStatus());

            return ResponseEntity.ok(result);
        } catch (Exception e) {
            throw new RuntimeException("Literature screening failed: " + e.getMessage(), e);
        }
    }

    @GetMapping("/{id}")
    public ResponseEntity<LiteratureArticleEntity> getArticleById(@PathVariable Long id) {
        return literatureRepository.findById(id)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }

    @GetMapping("/{id}/pdf")
    public ResponseEntity<byte[]> getArticlePdf(@PathVariable Long id) {
        return literatureRepository.findById(id).map(entity -> {
            byte[] bytes = entity.getPdfData();
            if (bytes != null && bytes.length > 0) {
                return ResponseEntity.ok()
                        .contentType(org.springframework.http.MediaType.APPLICATION_PDF)
                        .header(org.springframework.http.HttpHeaders.CONTENT_DISPOSITION, "inline; filename=\"" + entity.getFilename() + "\"")
                        .body(bytes);
            }
            try {
                java.nio.file.Path p = java.nio.file.Paths.get("../test-data/pdfs/literature_articles", entity.getFilename());
                if (!java.nio.file.Files.exists(p)) {
                    p = java.nio.file.Paths.get("test-data/pdfs/literature_articles", entity.getFilename());
                }
                if (java.nio.file.Files.exists(p)) {
                    byte[] diskBytes = java.nio.file.Files.readAllBytes(p);
                    return ResponseEntity.ok()
                            .contentType(org.springframework.http.MediaType.APPLICATION_PDF)
                            .header(org.springframework.http.HttpHeaders.CONTENT_DISPOSITION, "inline; filename=\"" + entity.getFilename() + "\"")
                            .body(diskBytes);
                }
            } catch (Exception ignored) {}
            return ResponseEntity.notFound().<byte[]>build();
        }).orElse(ResponseEntity.notFound().build());
    }

    @PostMapping("/{id}/review")
    public ResponseEntity<LiteratureArticleEntity> reviewArticle(
            @PathVariable Long id,
            @RequestBody ReviewActionRequestDto req) {
        return literatureRepository.findById(id).map(entity -> {
            String prevDecision = "Reportable=" + entity.getIsReportable() + ", Cases=" + entity.getPatientCasesCount();
            boolean isAccept = "ACCEPT".equalsIgnoreCase(req.getAction()) || "CONFIRM".equalsIgnoreCase(req.getAction());
            entity.setReviewStatus(isAccept ? "ACCEPTED" : "OVERRIDDEN");
            entity.setReviewedBy(req.getReviewerUsername() != null && !req.getReviewerUsername().isBlank()
                    ? req.getReviewerUsername()
                    : "safety.reviewer@clinevo.com");
            entity.setReviewedAt(LocalDateTime.now());
            entity.setReviewerComments(req.getComments());

            if (!isAccept) {
                if (req.getOverrideIsReportable() != null) {
                    entity.setIsReportable(req.getOverrideIsReportable());
                }
                if (req.getOverrideCasesCount() != null) {
                    entity.setPatientCasesCount(req.getOverrideCasesCount());
                }
            }
            literatureRepository.save(entity);

            String newDecision = "ReviewStatus=" + entity.getReviewStatus() + ", Reportable=" + entity.getIsReportable() + ", Cases=" + entity.getPatientCasesCount();
            auditService.logEvent(
                    entity.getId(),
                    entity.getReviewedBy(),
                    isAccept ? "LITERATURE_REVIEW_ACCEPT" : "LITERATURE_REVIEW_OVERRIDE",
                    "LITERATURE_SCREENING_ASSESSMENT",
                    prevDecision,
                    newDecision,
                    req.getComments()
            );

            return ResponseEntity.ok(entity);
        }).orElse(ResponseEntity.notFound().build());
    }

    @GetMapping("/{id}/audit")
    public ResponseEntity<List<AuditEventEntity>> getArticleAuditTrail(@PathVariable Long id) {
        return ResponseEntity.ok(auditService.getAuditTrail(id));
    }

    @GetMapping("/sample-pdf")
    public ResponseEntity<byte[]> getSamplePdf(@RequestParam String filename) {
        try {
            java.nio.file.Path p = java.nio.file.Paths.get("../test-data/pdfs/literature_articles", filename);
            if (!java.nio.file.Files.exists(p)) {
                p = java.nio.file.Paths.get("test-data/pdfs/literature_articles", filename);
            }
            if (java.nio.file.Files.exists(p)) {
                byte[] bytes = java.nio.file.Files.readAllBytes(p);
                return ResponseEntity.ok()
                        .contentType(org.springframework.http.MediaType.APPLICATION_PDF)
                        .header(org.springframework.http.HttpHeaders.CONTENT_DISPOSITION, "inline; filename=\"" + filename + "\"")
                        .body(bytes);
            }
            return ResponseEntity.notFound().build();
        } catch (Exception e) {
            return ResponseEntity.internalServerError().build();
        }
    }

    public static class ReviewActionRequestDto {
        private String action;
        private String reviewerUsername;
        private String comments;
        private Boolean overrideIsReportable;
        private Integer overrideCasesCount;

        public String getAction() { return action; }
        public void setAction(String action) { this.action = action; }
        public String getReviewerUsername() { return reviewerUsername; }
        public void setReviewerUsername(String reviewerUsername) { this.reviewerUsername = reviewerUsername; }
        public String getComments() { return comments; }
        public void setComments(String comments) { this.comments = comments; }
        public Boolean getOverrideIsReportable() { return overrideIsReportable; }
        public void setOverrideIsReportable(Boolean overrideIsReportable) { this.overrideIsReportable = overrideIsReportable; }
        public Integer getOverrideCasesCount() { return overrideCasesCount; }
        public void setOverrideCasesCount(Integer overrideCasesCount) { this.overrideCasesCount = overrideCasesCount; }
    }
}
