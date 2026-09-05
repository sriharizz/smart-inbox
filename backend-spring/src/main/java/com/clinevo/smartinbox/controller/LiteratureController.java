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

@RestController
@RequestMapping("/api/literature")
public class LiteratureController {

    private final AiGatewayClient aiGatewayClient;
    private final LiteratureArticleRepository literatureRepository;
    private final ObjectMapper objectMapper;

    public LiteratureController(AiGatewayClient aiGatewayClient,
                                LiteratureArticleRepository literatureRepository,
                                ObjectMapper objectMapper) {
        this.aiGatewayClient = aiGatewayClient;
        this.literatureRepository = literatureRepository;
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

            if (result.getIndividual_cases() != null) {
                entity.setCasesJson(objectMapper.writeValueAsString(result.getIndividual_cases()));
            }

            entity.setCreatedAt(LocalDateTime.now());
            literatureRepository.save(entity);

            return ResponseEntity.ok(result);
        } catch (Exception e) {
            throw new RuntimeException("Literature screening failed: " + e.getMessage(), e);
        }
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
}
