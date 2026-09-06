package com.clinevo.smartinbox.model;

import com.fasterxml.jackson.annotation.JsonIgnore;
import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "ICSR_REPORTS")
public class IcsrReportEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @JsonIgnore
    @OneToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "MESSAGE_ID", nullable = false)
    private IntakeMessageEntity message;

    @Column(name = "CASE_IDENTIFIER", length = 255)
    private String caseIdentifier;

    // Patient Information
    @Column(name = "PATIENT_IDENTIFIER", length = 255)
    private String patientIdentifier = "Not stated";

    @Column(name = "PATIENT_AGE", length = 100)
    private String patientAge = "Not stated";

    @Column(name = "PATIENT_SEX", length = 100)
    private String patientSex = "Not stated";

    @Column(name = "PATIENT_WEIGHT", length = 100)
    private String patientWeight = "Not stated";

    @Lob
    @Column(name = "PATIENT_HISTORY")
    private String patientHistory = "Not stated";

    // Reporter Information
    @Column(name = "REPORTER_NAME", length = 255)
    private String reporterName = "Not stated";

    @Column(name = "REPORTER_ROLE", length = 255)
    private String reporterRole = "Not stated";

    @Column(name = "REPORTER_INSTITUTION", length = 255)
    private String reporterInstitution = "Not stated";

    @Column(name = "REPORTER_COUNTRY", length = 255)
    private String reporterCountry = "Not stated";

    @Column(name = "REPORTER_CONTACT", length = 255)
    private String reporterContact = "Not stated";

    // Product Information
    @Column(name = "PRODUCT_NAME", length = 255)
    private String productName = "Not stated";

    @Column(name = "PRODUCT_DOSE", length = 255)
    private String productDose = "Not stated";

    @Column(name = "PRODUCT_FREQUENCY", length = 255)
    private String productFrequency = "Not stated";

    @Column(name = "PRODUCT_ROUTE", length = 255)
    private String productRoute = "Not stated";

    @Column(name = "PRODUCT_LOT", length = 255)
    private String productLot = "Not stated";

    @Column(name = "PRODUCT_EXPIRY", length = 255)
    private String productExpiry = "Not stated";

    @Column(name = "PRODUCT_INDICATION", length = 500)
    private String productIndication = "Not stated";

    // Adverse Reaction Information
    @Column(name = "ADVERSE_EVENT", length = 500)
    private String adverseEvent = "Not stated";

    @Column(name = "EVENT_ONSET", length = 255)
    private String eventOnset = "Not stated";

    @Column(name = "EVENT_OUTCOME", length = 255)
    private String eventOutcome = "Not stated";

    @Column(name = "SERIOUSNESS_CRITERIA", length = 500)
    private String seriousnessCriteria;

    @Column(name = "DECHALLENGE", length = 500)
    private String dechallenge = "Not stated";

    @Column(name = "RECHALLENGE", length = 500)
    private String rechallenge = "Not stated";

    @Lob
    @Column(name = "LAB_TESTS_JSON")
    private String labTestsJson;

    @Lob
    @Column(name = "CLINICAL_NARRATIVE")
    private String clinicalNarrative = "Not stated";

    @Lob
    @Column(name = "SOURCE_CITATIONS_JSON")
    private String sourceCitationsJson;

    @Column(name = "CREATED_AT", nullable = false)
    private LocalDateTime createdAt = LocalDateTime.now();

    public IcsrReportEntity() {}

    // Getters and Setters
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }

    public IntakeMessageEntity getMessage() { return message; }
    public void setMessage(IntakeMessageEntity message) { this.message = message; }

    public String getCaseIdentifier() { return caseIdentifier; }
    public void setCaseIdentifier(String caseIdentifier) { this.caseIdentifier = caseIdentifier; }

    public String getPatientIdentifier() { return patientIdentifier; }
    public void setPatientIdentifier(String patientIdentifier) { this.patientIdentifier = patientIdentifier; }

    public String getPatientAge() { return patientAge; }
    public void setPatientAge(String patientAge) { this.patientAge = patientAge; }

    public String getPatientSex() { return patientSex; }
    public void setPatientSex(String patientSex) { this.patientSex = patientSex; }

    public String getPatientWeight() { return patientWeight; }
    public void setPatientWeight(String patientWeight) { this.patientWeight = patientWeight; }

    public String getPatientHistory() { return patientHistory; }
    public void setPatientHistory(String patientHistory) { this.patientHistory = patientHistory; }

    public String getReporterName() { return reporterName; }
    public void setReporterName(String reporterName) { this.reporterName = reporterName; }

    public String getReporterRole() { return reporterRole; }
    public void setReporterRole(String reporterRole) { this.reporterRole = reporterRole; }

    public String getReporterInstitution() { return reporterInstitution; }
    public void setReporterInstitution(String reporterInstitution) { this.reporterInstitution = reporterInstitution; }

    public String getReporterCountry() { return reporterCountry; }
    public void setReporterCountry(String reporterCountry) { this.reporterCountry = reporterCountry; }

    public String getReporterContact() { return reporterContact; }
    public void setReporterContact(String reporterContact) { this.reporterContact = reporterContact; }

    public String getProductName() { return productName; }
    public void setProductName(String productName) { this.productName = productName; }

    public String getProductDose() { return productDose; }
    public void setProductDose(String productDose) { this.productDose = productDose; }

    public String getProductFrequency() { return productFrequency; }
    public void setProductFrequency(String productFrequency) { this.productFrequency = productFrequency; }

    public String getProductRoute() { return productRoute; }
    public void setProductRoute(String productRoute) { this.productRoute = productRoute; }

    public String getProductLot() { return productLot; }
    public void setProductLot(String productLot) { this.productLot = productLot; }

    public String getProductExpiry() { return productExpiry; }
    public void setProductExpiry(String productExpiry) { this.productExpiry = productExpiry; }

    public String getProductIndication() { return productIndication; }
    public void setProductIndication(String productIndication) { this.productIndication = productIndication; }

    public String getAdverseEvent() { return adverseEvent; }
    public void setAdverseEvent(String adverseEvent) { this.adverseEvent = adverseEvent; }

    public String getEventOnset() { return eventOnset; }
    public void setEventOnset(String eventOnset) { this.eventOnset = eventOnset; }

    public String getEventOutcome() { return eventOutcome; }
    public void setEventOutcome(String eventOutcome) { this.eventOutcome = eventOutcome; }

    public String getSeriousnessCriteria() { return seriousnessCriteria; }
    public void setSeriousnessCriteria(String seriousnessCriteria) { this.seriousnessCriteria = seriousnessCriteria; }

    public String getDechallenge() { return dechallenge; }
    public void setDechallenge(String dechallenge) { this.dechallenge = dechallenge; }

    public String getRechallenge() { return rechallenge; }
    public void setRechallenge(String rechallenge) { this.rechallenge = rechallenge; }

    public String getLabTestsJson() { return labTestsJson; }
    public void setLabTestsJson(String labTestsJson) { this.labTestsJson = labTestsJson; }

    public String getClinicalNarrative() { return clinicalNarrative; }
    public void setClinicalNarrative(String clinicalNarrative) { this.clinicalNarrative = clinicalNarrative; }

    public String getSourceCitationsJson() { return sourceCitationsJson; }
    public void setSourceCitationsJson(String sourceCitationsJson) { this.sourceCitationsJson = sourceCitationsJson; }

    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
}
