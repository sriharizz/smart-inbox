package com.clinevo.smartinbox.service;

import com.clinevo.smartinbox.dto.ExtractionResultDto;
import com.clinevo.smartinbox.model.*;
import com.clinevo.smartinbox.repository.*;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.HashMap;
import java.util.Map;

@Service
public class AsyncDocumentProcessor {

    private static final Logger log = LoggerFactory.getLogger(AsyncDocumentProcessor.class);

    private final IntakeMessageRepository messageRepository;
    private final IcsrReportRepository icsrRepository;
    private final PqcReportRepository pqcRepository;
    private final MedicalInfoRepository medicalInfoRepository;
    private final AiGatewayClient aiGatewayClient;
    private final AuditService auditService;
    private final ObjectMapper objectMapper;

    public AsyncDocumentProcessor(IntakeMessageRepository messageRepository,
                                  IcsrReportRepository icsrRepository,
                                  PqcReportRepository pqcRepository,
                                  MedicalInfoRepository medicalInfoRepository,
                                  AiGatewayClient aiGatewayClient,
                                  AuditService auditService,
                                  ObjectMapper objectMapper) {
        this.messageRepository = messageRepository;
        this.icsrRepository = icsrRepository;
        this.pqcRepository = pqcRepository;
        this.medicalInfoRepository = medicalInfoRepository;
        this.aiGatewayClient = aiGatewayClient;
        this.auditService = auditService;
        this.objectMapper = objectMapper;
    }

    @Async("taskExecutor")
    @Transactional
    public void processMessageAsync(Long messageId, byte[] rawEmlBytes, String filename) {
        log.info("[ASYNC-WORKER] Starting AI triage & extraction for Message ID: {} ({})", messageId, filename);

        IntakeMessageEntity message = messageRepository.findById(messageId).orElse(null);
        if (message == null) {
            log.error("Message ID {} not found in database.", messageId);
            return;
        }

        message.setStatus("PROCESSING");
        messageRepository.save(message);

        try {
            ExtractionResultDto result = aiGatewayClient.processEml(filename, rawEmlBytes);
            if (result == null || result.getTriage() == null) {
                throw new IllegalStateException("Empty extraction result from AI service.");
            }

            // 1. Update Triage Metadata
            ExtractionResultDto.TriageResultDto triage = result.getTriage();
            message.setPrimaryCategory(triage.getPrimary_category());
            message.setIsMultiLabel(triage.isIs_multi_label());
            message.setExecutiveSummary(triage.getExecutive_summary());

            if (triage.getLabels() != null && !triage.getLabels().isEmpty()) {
                message.setConfidence(triage.getLabels().get(0).getConfidence());
                message.setLabelsJson(objectMapper.writeValueAsString(triage.getLabels()));
            } else {
                message.setConfidence(0.90);
            }

            // 2. Persist ICSR Report Entity
            IcsrReportEntity icsr = new IcsrReportEntity();
            icsr.setCaseIdentifier(result.getCase_id() != null ? result.getCase_id() : "CASE-" + messageId);

            if (result.getPatient() != null) {
                icsr.setPatientAge(result.getPatient().getAge());
                icsr.setPatientSex(result.getPatient().getSex());
                icsr.setPatientWeight(result.getPatient().getWeight());
                icsr.setPatientHistory(result.getPatient().getMedical_history());
            }

            if (result.getReporter() != null) {
                icsr.setReporterName(result.getReporter().getName());
                icsr.setReporterRole(result.getReporter().getRole());
                icsr.setReporterInstitution(result.getReporter().getInstitution());
                icsr.setReporterCountry(result.getReporter().getCountry());
                icsr.setReporterContact(result.getReporter().getEmail_or_phone());
            }

            if (result.getProduct() != null) {
                icsr.setProductName(result.getProduct().getProduct_name());
                icsr.setProductDose(result.getProduct().getDose());
                icsr.setProductFrequency(result.getProduct().getFrequency());
                icsr.setProductRoute(result.getProduct().getRoute());
                icsr.setProductLot(result.getProduct().getLot_number());
                icsr.setProductExpiry(result.getProduct().getExpiry_date());
                icsr.setProductIndication(result.getProduct().getIndication());
            }

            if (result.getReaction() != null) {
                icsr.setAdverseEvent(result.getReaction().getAdverse_event());
                icsr.setEventOnset(result.getReaction().getOnset_date());
                icsr.setEventOutcome(result.getReaction().getEventOutcome());
                icsr.setDechallenge(result.getReaction().getDechallenge());
                icsr.setRechallenge(result.getReaction().getRechallenge());
                if (result.getReaction().getSeriousness_criteria() != null) {
                    icsr.setSeriousnessCriteria(String.join(", ", result.getReaction().getSeriousness_criteria()));
                }
            }

            if (result.getLab_tests() != null && !result.getLab_tests().isEmpty()) {
                icsr.setLabTestsJson(objectMapper.writeValueAsString(result.getLab_tests()));
            }

            icsr.setClinicalNarrative(result.getNarrative() != null ? result.getNarrative() : "Not stated");

            Map<String, Object> citationsMap = new HashMap<>();
            if (result.getPatient() != null && result.getPatient().getCitation() != null) citationsMap.put("patient", result.getPatient().getCitation());
            if (result.getReporter() != null && result.getReporter().getCitation() != null) citationsMap.put("reporter", result.getReporter().getCitation());
            if (result.getProduct() != null && result.getProduct().getCitation() != null) citationsMap.put("product", result.getProduct().getCitation());
            if (result.getReaction() != null && result.getReaction().getCitation() != null) citationsMap.put("reaction", result.getReaction().getCitation());
            icsr.setSourceCitationsJson(objectMapper.writeValueAsString(citationsMap));

            message.setIcsrReport(icsr);

            // 3. Persist Quality Complaint (PQC) if detected
            if (result.getQuality_complaint() != null) {
                ExtractionResultDto.QualityComplaintDto qc = result.getQuality_complaint();
                PqcReportEntity pqc = new PqcReportEntity();
                pqc.setProductName(qc.getProduct_name());
                pqc.setLotNumber(qc.getLot_number());
                pqc.setDefectType(qc.getDefect_type());
                pqc.setDefectDescription(qc.getDefect_description());
                pqc.setPackagingBreached(qc.isPackaging_breached());
                pqc.setPhotoDetected(qc.isPhoto_detected());
                pqc.setPhotoDescription(qc.getPhoto_description());
                pqc.setRequiresHumanReview(qc.isRequires_human_review());
                if (qc.getCitation() != null) {
                    pqc.setSourceCitationsJson(objectMapper.writeValueAsString(qc.getCitation()));
                }
                message.setPqcReport(pqc);
            }

            // 4. Persist Medical Information (MI) if detected
            if (result.getMedical_info() != null) {
                ExtractionResultDto.MedicalInfoDto mi = result.getMedical_info();
                MedicalInfoEntity medInfo = new MedicalInfoEntity();
                medInfo.setProductOrTopic(mi.getProduct_or_topic());
                medInfo.setInquiryType(mi.getInquiry_type());
                medInfo.setQuestionText(mi.getQuestion_text());
                if (mi.getCitation() != null) {
                    medInfo.setSourceCitationsJson(objectMapper.writeValueAsString(mi.getCitation()));
                }
                message.setMedicalInfo(medInfo);
            }

            message.setStatus("TRIAGED");
            messageRepository.save(message);

            auditService.logEvent(
                    messageId,
                    "SYSTEM_AI_ENGINE",
                    "AI_TRIAGE_COMPLETED",
                    "STATUS",
                    "PROCESSING",
                    "TRIAGED",
                    "Classified as " + message.getPrimaryCategory() + " with confidence " + message.getConfidence()
            );

            log.info("[ASYNC-WORKER] Successfully completed AI triage for Message ID: {} -> {}", messageId, message.getPrimaryCategory());

        } catch (Exception e) {
            log.error("[ASYNC-WORKER] AI processing failed for Message ID {}: {}", messageId, e.getMessage(), e);
            message.setStatus("FAILED");
            messageRepository.save(message);
            auditService.logEvent(
                    messageId,
                    "SYSTEM_AI_ENGINE",
                    "AI_PROCESSING_FAILED",
                    "STATUS",
                    "PROCESSING",
                    "FAILED",
                    "Error: " + e.getMessage()
            );
        }
    }
}
