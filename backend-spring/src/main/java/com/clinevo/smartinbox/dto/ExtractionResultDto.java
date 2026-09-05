package com.clinevo.smartinbox.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import java.util.List;
import java.util.Map;

@JsonIgnoreProperties(ignoreUnknown = true)
public class ExtractionResultDto {

    private String case_id;
    private String source_filename;
    private String language_detected;
    private TriageResultDto triage;
    private PatientDto patient;
    private ReporterDto reporter;
    private ProductDto product;
    private ReactionDto reaction;
    private List<Map<String, Object>> lab_tests;
    private QualityComplaintDto quality_complaint;
    private MedicalInfoDto medical_info;
    private String narrative;
    private int processing_time_ms;

    public ExtractionResultDto() {}

    // Nested DTOs
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class TriageResultDto {
        private boolean is_multi_label;
        private String primary_category;
        private List<TriageLabelDto> labels;
        private String executive_summary;

        public boolean isIs_multi_label() { return is_multi_label; }
        public void setIs_multi_label(boolean is_multi_label) { this.is_multi_label = is_multi_label; }
        public String getPrimary_category() { return primary_category; }
        public void setPrimary_category(String primary_category) { this.primary_category = primary_category; }
        public List<TriageLabelDto> getLabels() { return labels; }
        public void setLabels(List<TriageLabelDto> labels) { this.labels = labels; }
        public String getExecutive_summary() { return executive_summary; }
        public void setExecutive_summary(String executive_summary) { this.executive_summary = executive_summary; }
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class TriageLabelDto {
        private String category;
        private double confidence;
        private String reason;

        public String getCategory() { return category; }
        public void setCategory(String category) { this.category = category; }
        public double getConfidence() { return confidence; }
        public void setConfidence(double confidence) { this.confidence = confidence; }
        public String getReason() { return reason; }
        public void setReason(String reason) { this.reason = reason; }
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class SourceCitationDto {
        private String source_type = "email";
        private String page_or_location = "body";
        private String verbatim_snippet = "Not stated";

        public String getSource_type() { return source_type; }
        public void setSource_type(String source_type) { this.source_type = source_type; }
        public String getPage_or_location() { return page_or_location; }
        public void setPage_or_location(String page_or_location) { this.page_or_location = page_or_location; }
        public String getVerbatim_snippet() { return verbatim_snippet; }
        public void setVerbatim_snippet(String verbatim_snippet) { this.verbatim_snippet = verbatim_snippet; }
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class PatientDto {
        private String age = "Not stated";
        private String sex = "Not stated";
        private String weight = "Not stated";
        private String medical_history = "Not stated";
        private SourceCitationDto citation;

        public String getAge() { return age; }
        public void setAge(String age) { this.age = age; }
        public String getSex() { return sex; }
        public void setSex(String sex) { this.sex = sex; }
        public String getWeight() { return weight; }
        public void setWeight(String weight) { this.weight = weight; }
        public String getMedical_history() { return medical_history; }
        public void setMedical_history(String medical_history) { this.medical_history = medical_history; }
        public SourceCitationDto getCitation() { return citation; }
        public void setCitation(SourceCitationDto citation) { this.citation = citation; }
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class ReporterDto {
        private String name = "Not stated";
        private String role = "Not stated";
        private String institution = "Not stated";
        private String country = "Not stated";
        private String email_or_phone = "Not stated";
        private SourceCitationDto citation;

        public String getName() { return name; }
        public void setName(String name) { this.name = name; }
        public String getRole() { return role; }
        public void setRole(String role) { this.role = role; }
        public String getInstitution() { return institution; }
        public void setInstitution(String institution) { this.institution = institution; }
        public String getCountry() { return country; }
        public void setCountry(String country) { this.country = country; }
        public String getEmail_or_phone() { return email_or_phone; }
        public void setEmail_or_phone(String email_or_phone) { this.email_or_phone = email_or_phone; }
        public SourceCitationDto getCitation() { return citation; }
        public void setCitation(SourceCitationDto citation) { this.citation = citation; }
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class ProductDto {
        private String product_name = "Not stated";
        private String dose = "Not stated";
        private String frequency = "Not stated";
        private String route = "Not stated";
        private String lot_number = "Not stated";
        private String expiry_date = "Not stated";
        private String indication = "Not stated";
        private SourceCitationDto citation;

        public String getProduct_name() { return product_name; }
        public void setProduct_name(String product_name) { this.product_name = product_name; }
        public String getDose() { return dose; }
        public void setDose(String dose) { this.dose = dose; }
        public String getFrequency() { return frequency; }
        public void setFrequency(String frequency) { this.frequency = frequency; }
        public String getRoute() { return route; }
        public void setRoute(String route) { this.route = route; }
        public String getLot_number() { return lot_number; }
        public void setLot_number(String lot_number) { this.lot_number = lot_number; }
        public String getExpiry_date() { return expiry_date; }
        public void setExpiry_date(String expiry_date) { this.expiry_date = expiry_date; }
        public String getIndication() { return indication; }
        public void setIndication(String indication) { this.indication = indication; }
        public SourceCitationDto getCitation() { return citation; }
        public void setCitation(SourceCitationDto citation) { this.citation = citation; }
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class ReactionDto {
        private String adverse_event = "Not stated";
        private String onset_date = "Not stated";
        private String outcome = "Not stated";
        private List<String> seriousness_criteria;
        private String dechallenge = "Not stated";
        private String rechallenge = "Not stated";
        private SourceCitationDto citation;

        public String getAdverse_event() { return adverse_event; }
        public void setAdverse_event(String adverse_event) { this.adverse_event = adverse_event; }
        public String getOnset_date() { return onset_date; }
        public void setOnset_date(String onset_date) { this.onset_date = onset_date; }
        public String getEventOutcome() { return outcome; }
        public void setOutcome(String outcome) { this.outcome = outcome; }
        public String getOutcome() { return outcome; }
        public List<String> getSeriousness_criteria() { return seriousness_criteria; }
        public void setSeriousness_criteria(List<String> seriousness_criteria) { this.seriousness_criteria = seriousness_criteria; }
        public String getDechallenge() { return dechallenge; }
        public void setDechallenge(String dechallenge) { this.dechallenge = dechallenge; }
        public String getRechallenge() { return rechallenge; }
        public void setRechallenge(String rechallenge) { this.rechallenge = rechallenge; }
        public SourceCitationDto getCitation() { return citation; }
        public void setCitation(SourceCitationDto citation) { this.citation = citation; }
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class QualityComplaintDto {
        private String product_name = "Not stated";
        private String lot_number = "Not stated";
        private String defect_type = "Not stated";
        private String defect_description = "Not stated";
        private boolean packaging_breached;
        private boolean photo_detected;
        private String photo_description = "Not stated";
        private boolean requires_human_review;
        private SourceCitationDto citation;

        public String getProduct_name() { return product_name; }
        public void setProduct_name(String product_name) { this.product_name = product_name; }
        public String getLot_number() { return lot_number; }
        public void setLot_number(String lot_number) { this.lot_number = lot_number; }
        public String getDefect_type() { return defect_type; }
        public void setDefect_type(String defect_type) { this.defect_type = defect_type; }
        public String getDefect_description() { return defect_description; }
        public void setDefect_description(String defect_description) { this.defect_description = defect_description; }
        public boolean isPackaging_breached() { return packaging_breached; }
        public void setPackaging_breached(boolean packaging_breached) { this.packaging_breached = packaging_breached; }
        public boolean isPhoto_detected() { return photo_detected; }
        public void setPhoto_detected(boolean photo_detected) { this.photo_detected = photo_detected; }
        public String getPhoto_description() { return photo_description; }
        public void setPhoto_description(String photo_description) { this.photo_description = photo_description; }
        public boolean isRequires_human_review() { return requires_human_review; }
        public void setRequires_human_review(boolean requires_human_review) { this.requires_human_review = requires_human_review; }
        public SourceCitationDto getCitation() { return citation; }
        public void setCitation(SourceCitationDto citation) { this.citation = citation; }
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class MedicalInfoDto {
        private String product_or_topic = "Not stated";
        private String inquiry_type = "Not stated";
        private String question_text = "Not stated";
        private SourceCitationDto citation;

        public String getProduct_or_topic() { return product_or_topic; }
        public void setProduct_or_topic(String product_or_topic) { this.product_or_topic = product_or_topic; }
        public String getInquiry_type() { return inquiry_type; }
        public void setInquiry_type(String inquiry_type) { this.inquiry_type = inquiry_type; }
        public String getQuestion_text() { return question_text; }
        public void setQuestion_text(String question_text) { this.question_text = question_text; }
        public SourceCitationDto getCitation() { return citation; }
        public void setCitation(SourceCitationDto citation) { this.citation = citation; }
    }

    // Getters and Setters for top-level DTO
    public String getCase_id() { return case_id; }
    public void setCase_id(String case_id) { this.case_id = case_id; }
    public String getSource_filename() { return source_filename; }
    public void setSource_filename(String source_filename) { this.source_filename = source_filename; }
    public String getLanguage_detected() { return language_detected; }
    public void setLanguage_detected(String language_detected) { this.language_detected = language_detected; }
    public TriageResultDto getTriage() { return triage; }
    public void setTriage(TriageResultDto triage) { this.triage = triage; }
    public PatientDto getPatient() { return patient; }
    public void setPatient(PatientDto patient) { this.patient = patient; }
    public ReporterDto getReporter() { return reporter; }
    public void setReporter(ReporterDto reporter) { this.reporter = reporter; }
    public ProductDto getProduct() { return product; }
    public void setProduct(ProductDto product) { this.product = product; }
    public ReactionDto getReaction() { return reaction; }
    public void setReaction(ReactionDto reaction) { this.reaction = reaction; }
    public List<Map<String, Object>> getLab_tests() { return lab_tests; }
    public void setLab_tests(List<Map<String, Object>> lab_tests) { this.lab_tests = lab_tests; }
    public QualityComplaintDto getQuality_complaint() { return quality_complaint; }
    public void setQuality_complaint(QualityComplaintDto quality_complaint) { this.quality_complaint = quality_complaint; }
    public MedicalInfoDto getMedical_info() { return medical_info; }
    public void setMedical_info(MedicalInfoDto medical_info) { this.medical_info = medical_info; }
    public String getNarrative() { return narrative; }
    public void setNarrative(String narrative) { this.narrative = narrative; }
    public int getProcessing_time_ms() { return processing_time_ms; }
    public void setProcessing_time_ms(int processing_time_ms) { this.processing_time_ms = processing_time_ms; }
}
