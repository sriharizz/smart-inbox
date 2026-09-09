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
        processMessageAsync(messageId, rawEmlBytes, filename, true);
    }

    @Async("taskExecutor")
    @Transactional
    public void processMessageAsync(Long messageId, byte[] rawEmlBytes, String filename, boolean freshProcessing) {
        log.info("[ASYNC-WORKER] Starting AI triage & extraction for Message ID: {} ({}) [fresh={}]", messageId, filename, freshProcessing);

        IntakeMessageEntity message = messageRepository.findById(messageId).orElse(null);
        if (message == null) {
            log.error("Message ID {} not found in database.", messageId);
            return;
        }

        message.setStatus("PROCESSING");
        messageRepository.save(message);

        try {
            Thread.sleep(1500); // Respect Google Gemini RPM quota
            ExtractionResultDto result = aiGatewayClient.processEml(filename, rawEmlBytes, freshProcessing);
            if (result == null || result.getTriage() == null) {
                throw new IllegalStateException("Empty extraction result from AI service.");
            }

            // Apply extraction result with category-aware conditional persistence
            applyExtractionResult(message, result);

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

    /**
     * Applies AI extraction results to an intake message with strict category-aware conditional persistence.
     * Persists IcsrReportEntity ONLY when the message is triaged as an ICSR / Safety Report (or has clinical data).
     * Prevents creation of empty dummy ICSR reports for pure PQC, pure MI, and Not Relevant cases.
     */
    public void applyExtractionResult(IntakeMessageEntity message, ExtractionResultDto result) throws Exception {
        ExtractionResultDto.TriageResultDto triage = result.getTriage();
        if (triage != null) {
            message.setPrimaryCategory(triage.getPrimary_category());
            message.setIsMultiLabel(triage.isIs_multi_label());
            message.setExecutiveSummary(triage.getExecutive_summary());

            if (triage.getLabels() != null && !triage.getLabels().isEmpty()) {
                message.setConfidence(triage.getLabels().get(0).getConfidence());
                message.setLabelsJson(objectMapper.writeValueAsString(triage.getLabels()));
            } else {
                message.setConfidence(0.90);
            }
        }

        // 1. Language and Document Metadata
        if (result.getLanguage_detected() != null && !result.getLanguage_detected().isBlank()) {
            message.setLanguage(result.getLanguage_detected());
        }

        if (result.getAttachment_metadata() != null && !result.getAttachment_metadata().isEmpty() && message.getAttachments() != null) {
            for (ExtractionResultDto.AttachmentMetadataDto meta : result.getAttachment_metadata()) {
                if (meta.getFilename() == null) continue;
                for (AttachmentEntity att : message.getAttachments()) {
                    if (meta.getFilename().equalsIgnoreCase(att.getFilename())) {
                        if (meta.getFlavor() != null && !meta.getFlavor().isBlank()) {
                            att.setFlavor(meta.getFlavor());
                        }
                        if (meta.getLanguage() != null && !meta.getLanguage().isBlank()) {
                            att.setLanguage(meta.getLanguage());
                        }
                        if (meta.getDocument_summary() != null && !meta.getDocument_summary().isBlank()) {
                            att.setDocumentSummary(meta.getDocument_summary());
                        }
                    }
                }
            }
        }

        // 2. Persist ICSR Report Entity (Only for ICSR / Safety Report categories)
        boolean shouldPersistIcsr = isIcsrCategory(triage);
        if (!shouldPersistIcsr && triage == null) {
            shouldPersistIcsr = hasAnyClinicalData(result);
        }

        if (shouldPersistIcsr) {
            IcsrReportEntity icsr = message.getIcsrReport() != null ? message.getIcsrReport() : new IcsrReportEntity();
            icsr.setMessage(message);
            icsr.setCaseIdentifier(result.getCase_id() != null ? result.getCase_id() : (message.getId() != null ? "CASE-" + message.getId() : "CASE-NEW"));

            if (result.getPatient() != null) {
                icsr.setPatientIdentifier(result.getPatient().getIdentifier());
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
            if (result.getCitations() != null && !result.getCitations().isEmpty()) {
                citationsMap.putAll(result.getCitations());
            }
            if (result.getPatient() != null) {
                if (result.getPatient().getCitation() != null) citationsMap.putIfAbsent("patient", result.getPatient().getCitation());
                if (result.getPatient().getDob() != null) citationsMap.put("patient_dob_val", result.getPatient().getDob());
                if (result.getPatient().getCountry() != null) citationsMap.put("patient_country_val", result.getPatient().getCountry());
            }
            if (result.getReporter() != null) {
                if (result.getReporter().getCitation() != null) citationsMap.putIfAbsent("reporter", result.getReporter().getCitation());
                if (result.getReporter().getSpecialty() != null) citationsMap.put("reporter_specialty_val", result.getReporter().getSpecialty());
                if (result.getReporter().getHealth_professional() != null) citationsMap.put("health_professional_val", result.getReporter().getHealth_professional());
            }
            if (result.getProduct() != null) {
                if (result.getProduct().getCitation() != null) citationsMap.putIfAbsent("product", result.getProduct().getCitation());
                if (result.getProduct().getFormulation() != null) citationsMap.put("product_formulation_val", result.getProduct().getFormulation());
                if (result.getProduct().getStart_date() != null) citationsMap.put("treatment_start_date_val", result.getProduct().getStart_date());
                if (result.getProduct().getStop_date() != null) citationsMap.put("treatment_stop_date_val", result.getProduct().getStop_date());
                if (result.getProduct().getDuration() != null) citationsMap.put("treatment_duration_val", result.getProduct().getDuration());
                if (result.getProduct().getAction_taken() != null) citationsMap.put("action_taken_val", result.getProduct().getAction_taken());
            }
            if (result.getReaction() != null) {
                if (result.getReaction().getCitation() != null) citationsMap.putIfAbsent("reaction", result.getReaction().getCitation());
                citationsMap.put("hospitalization_val", result.getReaction().isHospitalization());
                if (result.getReaction().getAdmission_date() != null) citationsMap.put("hospital_admission_date_val", result.getReaction().getAdmission_date());
                citationsMap.put("life_threatening_val", result.getReaction().isLife_threatening());
                citationsMap.put("death_val", result.getReaction().isDeath());
                citationsMap.put("medically_important_val", result.getReaction().isMedically_important());
            }
            if (result.getConcomitant_medications() != null && !result.getConcomitant_medications().isEmpty()) {
                citationsMap.put("concomitant_medications", result.getConcomitant_medications());
            }
            if (result.getRegulatory() != null && !result.getRegulatory().isEmpty()) {
                citationsMap.put("regulatory", result.getRegulatory());
            }
            icsr.setSourceCitationsJson(objectMapper.writeValueAsString(citationsMap));

            message.setIcsrReport(icsr);
        } else {
            message.setIcsrReport(null);
        }

        // 3. Persist Quality Complaint (PQC) if detected
        if (result.getQuality_complaint() != null) {
            ExtractionResultDto.QualityComplaintDto qc = result.getQuality_complaint();
            PqcReportEntity pqc = message.getPqcReport() != null ? message.getPqcReport() : new PqcReportEntity();
            pqc.setMessage(message);
            pqc.setProductName(qc.getProduct_name());
            pqc.setLotNumber(qc.getLot_number());
            String defect = qc.getDefect_type();
            pqc.setDefectType(defect != null && defect.length() > 950 ? defect.substring(0, 950) : defect);
            pqc.setDefectDescription(qc.getDefect_description());
            pqc.setPackagingBreached(qc.isPackaging_breached());
            pqc.setPhotoDetected(qc.isPhoto_detected());
            pqc.setPhotoDescription(qc.getPhoto_description());
            pqc.setRequiresHumanReview(qc.isRequires_human_review());
            Map<String, Object> pqcCitations = new HashMap<>();
            if (result.getCitations() != null) {
                pqcCitations.putAll(result.getCitations());
            }
            if (qc.getCitation() != null) {
                pqcCitations.put("quality_complaint", qc.getCitation());
            }
            pqc.setSourceCitationsJson(objectMapper.writeValueAsString(pqcCitations));
            message.setPqcReport(pqc);
        } else {
            message.setPqcReport(null);
        }

        // 4. Persist Medical Information (MI) if detected
        if (result.getMedical_info() != null) {
            ExtractionResultDto.MedicalInfoDto mi = result.getMedical_info();
            MedicalInfoEntity medInfo = message.getMedicalInfo() != null ? message.getMedicalInfo() : new MedicalInfoEntity();
            medInfo.setMessage(message);
            medInfo.setProductOrTopic(mi.getProduct_or_topic());
            medInfo.setInquiryType(mi.getInquiry_type());
            medInfo.setQuestionText(mi.getQuestion_text());
            Map<String, Object> miCitations = new HashMap<>();
            if (result.getCitations() != null) {
                miCitations.putAll(result.getCitations());
            }
            if (mi.getCitation() != null) {
                miCitations.put("medical_info", mi.getCitation());
                miCitations.put("mi", mi.getCitation());
            }
            medInfo.setSourceCitationsJson(objectMapper.writeValueAsString(miCitations));
            message.setMedicalInfo(medInfo);
        } else {
            message.setMedicalInfo(null);
        }
    }

    public boolean isIcsrCategory(ExtractionResultDto.TriageResultDto triage) {
        if (triage == null) return false;
        String primary = triage.getPrimary_category();
        if (primary != null) {
            String lower = primary.toLowerCase();
            if (lower.contains("not relevant") || lower.contains("not_relevant")) {
                return false;
            }
            if (lower.contains("icsr") || lower.contains("safety report") || lower.contains("adverse event")) {
                return true;
            }
        }
        if (triage.getLabels() != null) {
            for (ExtractionResultDto.TriageLabelDto label : triage.getLabels()) {
                if (label.getCategory() != null) {
                    String lLower = label.getCategory().toLowerCase();
                    if (!lLower.contains("not relevant") && 
                        (lLower.contains("icsr") || lLower.contains("safety report") || lLower.contains("adverse event"))) {
                        return true;
                    }
                }
            }
        }
        return false;
    }

    public boolean hasAnyClinicalData(ExtractionResultDto result) {
        if (result == null) return false;
        if (result.getPatient() != null && isStated(result.getPatient().getIdentifier())) return true;
        if (result.getProduct() != null && isStated(result.getProduct().getProduct_name())) return true;
        if (result.getReaction() != null && isStated(result.getReaction().getAdverse_event())) return true;
        if (isStated(result.getNarrative())) return true;
        return false;
    }

    private boolean isStated(String val) {
        if (val == null) return false;
        String clean = val.trim().toLowerCase();
        return !clean.isEmpty() && 
               !clean.equals("not stated") && 
               !clean.equals("unknown") && 
               !clean.equals("null") && 
               !clean.equals("n/a") &&
               !clean.equals("none");
    }
}
