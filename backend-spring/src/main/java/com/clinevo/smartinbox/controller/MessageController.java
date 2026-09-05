package com.clinevo.smartinbox.controller;

import com.clinevo.smartinbox.dto.MessageSummaryDto;
import com.clinevo.smartinbox.dto.ReviewerAcceptRequest;
import com.clinevo.smartinbox.dto.ReviewerOverrideRequest;
import com.clinevo.smartinbox.model.*;
import com.clinevo.smartinbox.repository.AttachmentRepository;
import com.clinevo.smartinbox.repository.IntakeMessageRepository;
import com.clinevo.smartinbox.service.AuditService;
import com.clinevo.smartinbox.service.MailboxIngestionService;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.*;

@RestController
@RequestMapping("/api/messages")
public class MessageController {

    private final IntakeMessageRepository messageRepository;
    private final AttachmentRepository attachmentRepository;
    private final AuditService auditService;
    private final MailboxIngestionService ingestionService;

    public MessageController(IntakeMessageRepository messageRepository,
                             AttachmentRepository attachmentRepository,
                             AuditService auditService,
                             MailboxIngestionService ingestionService) {
        this.messageRepository = messageRepository;
        this.attachmentRepository = attachmentRepository;
        this.auditService = auditService;
        this.ingestionService = ingestionService;
    }

    @GetMapping
    public List<MessageSummaryDto> getAllMessages() {
        List<IntakeMessageEntity> messages = messageRepository.findAllByOrderByCreatedAtDesc();
        List<MessageSummaryDto> summaries = new ArrayList<>();

        for (IntakeMessageEntity m : messages) {
            MessageSummaryDto dto = new MessageSummaryDto();
            dto.setId(m.getId());
            dto.setMessageId(m.getMessageId());
            dto.setSender(m.getSender());
            dto.setSenderEmail(m.getSenderEmail());
            dto.setSubject(m.getSubject());
            dto.setReceivedDate(m.getReceivedDate());
            dto.setStatus(m.getStatus());
            dto.setPrimaryCategory(m.getPrimaryCategory() != null ? m.getPrimaryCategory() : "Pending Triage");
            dto.setConfidence(m.getConfidence() != null ? m.getConfidence() : 0.0);
            dto.setIsMultiLabel(m.getIsMultiLabel());
            dto.setExecutiveSummary(m.getExecutiveSummary());
            dto.setAttachmentCount(m.getAttachments().size());

            boolean photoReview = m.getPqcReport() != null && Boolean.TRUE.equals(m.getPqcReport().getRequiresHumanReview());
            dto.setRequiresHumanReview(photoReview);

            summaries.add(dto);
        }
        return summaries;
    }

    @GetMapping("/{id}")
    public ResponseEntity<IntakeMessageEntity> getMessageById(@PathVariable Long id) {
        return messageRepository.findById(id)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }

    @PostMapping("/{id}/accept")
    public ResponseEntity<IntakeMessageEntity> acceptMessage(@PathVariable Long id, @RequestBody(required = false) ReviewerAcceptRequest request) {
        Optional<IntakeMessageEntity> opt = messageRepository.findById(id);
        if (opt.isEmpty()) return ResponseEntity.notFound().build();

        IntakeMessageEntity message = opt.get();
        String oldStatus = message.getStatus();
        message.setStatus("REVIEWED");
        messageRepository.save(message);

        String username = request != null && request.getReviewerUsername() != null ? request.getReviewerUsername() : "safety.reviewer@clinevo.com";
        String comments = request != null ? request.getComments() : "Reviewer confirmed AI triage & extracted facts.";

        auditService.logEvent(
                id,
                username,
                "ACCEPT",
                "STATUS",
                oldStatus,
                "REVIEWED",
                comments
        );

        return ResponseEntity.ok(message);
    }

    @PostMapping("/{id}/override")
    public ResponseEntity<IntakeMessageEntity> overrideMessage(@PathVariable Long id, @RequestBody ReviewerOverrideRequest request) {
        Optional<IntakeMessageEntity> opt = messageRepository.findById(id);
        if (opt.isEmpty()) return ResponseEntity.notFound().build();

        IntakeMessageEntity message = opt.get();
        String username = request.getReviewerUsername() != null ? request.getReviewerUsername() : "safety.reviewer@clinevo.com";
        String justification = request.getJustification() != null ? request.getJustification() : "Manual reviewer override applied.";

        // Handle category override
        if (request.getNewCategory() != null && !request.getNewCategory().isBlank()) {
            String oldCat = message.getPrimaryCategory();
            message.setPrimaryCategory(request.getNewCategory());
            message.setStatus("OVERRIDDEN");

            auditService.logEvent(
                    id,
                    username,
                    "OVERRIDE_CATEGORY",
                    "PRIMARY_CATEGORY",
                    oldCat,
                    request.getNewCategory(),
                    justification
            );
        }

        // Handle field modifications on ICSR report
        if (request.getFieldEdits() != null && message.getIcsrReport() != null) {
            IcsrReportEntity icsr = message.getIcsrReport();
            for (Map.Entry<String, String> entry : request.getFieldEdits().entrySet()) {
                String field = entry.getKey();
                String newVal = entry.getValue();
                String oldVal = "";

                switch (field.toLowerCase()) {
                    case "patientage" -> { oldVal = icsr.getPatientAge(); icsr.setPatientAge(newVal); }
                    case "patientsex" -> { oldVal = icsr.getPatientSex(); icsr.setPatientSex(newVal); }
                    case "patientweight" -> { oldVal = icsr.getPatientWeight(); icsr.setPatientWeight(newVal); }
                    case "reportername" -> { oldVal = icsr.getReporterName(); icsr.setReporterName(newVal); }
                    case "productname" -> { oldVal = icsr.getProductName(); icsr.setProductName(newVal); }
                    case "productdose" -> { oldVal = icsr.getProductDose(); icsr.setProductDose(newVal); }
                    case "productlot" -> { oldVal = icsr.getProductLot(); icsr.setProductLot(newVal); }
                    case "adverseevent" -> { oldVal = icsr.getAdverseEvent(); icsr.setAdverseEvent(newVal); }
                }

                auditService.logEvent(
                        id,
                        username,
                        "EDIT_FIELD",
                        field.toUpperCase(),
                        oldVal,
                        newVal,
                        justification
                );
            }
        }

        messageRepository.save(message);
        return ResponseEntity.ok(message);
    }

    @PostMapping("/ingest")
    public ResponseEntity<Map<String, Object>> triggerIngestion() {
        try {
            int count = ingestionService.triggerIngestion();
            return ResponseEntity.ok(Map.of(
                    "status", "success",
                    "newMessagesIngested", count,
                    "message", "Ingestion triggered successfully."
            ));
        } catch (Exception e) {
            return ResponseEntity.internalServerError().body(Map.of(
                    "status", "error",
                    "message", e.getMessage()
            ));
        }
    }

    @PostMapping("/reset")
    public ResponseEntity<Map<String, Object>> resetAndReingest() {
        try {
            messageRepository.deleteAll();
            int count = ingestionService.triggerIngestion();
            return ResponseEntity.ok(Map.of(
                    "status", "success",
                    "reingestedCount", count,
                    "message", "Database reset and re-ingested successfully."
            ));
        } catch (Exception e) {
            return ResponseEntity.internalServerError().body(Map.of(
                    "status", "error",
                    "message", e.getMessage()
            ));
        }
    }

    @GetMapping("/attachments/{id}/download")
    public ResponseEntity<byte[]> downloadAttachment(@PathVariable Long id) {
        return attachmentRepository.findById(id)
                .map(att -> {
                    byte[] bytes = att.getContentBytes() != null ? att.getContentBytes() : new byte[0];
                    return ResponseEntity.ok()
                            .contentType(MediaType.parseMediaType(att.getContentType() != null ? att.getContentType() : "application/octet-stream"))
                            .header(HttpHeaders.CONTENT_DISPOSITION, "inline; filename=\"" + att.getFilename() + "\"")
                            .body(bytes);
                })
                .orElse(ResponseEntity.notFound().build());
    }
}
