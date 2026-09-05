# LIMITATIONS & PRODUCTION ROADMAP — CLINEVO SMART INBOX ASSISTANT

## 1. Prototype Scope Statement

The current implementation of the Clinevo Smart Inbox Assistant is an advanced engineering prototype and proof-of-concept designed to satisfy the official Clinevo Technologies assignment specifications. It demonstrates the technical feasibility of end-to-end automated intake, multimodal document triage, ICH E2B fact extraction, literature case series disaggregation, and human-in-the-loop review.

**The prototype is NOT currently certified as a validated GxP or 21 CFR Part 11 production medical software system.** Before deploying this architecture in a commercial pharmaceutical safety environment, significant enterprise hardening, compliance validation, and infrastructure scaling must be enacted.

---

## 2. Current Prototype Limitations

### 2.1 Synthetic Test Data Scope
- All documents, patient records, adverse reaction narratives, and product lots in `test-data/` are synthetic. Real-world pharmacovigilance intake involves highly unpredictable clinical correspondence, including poor-quality faxes, multi-generation photocopies, illegible physician handwriting, and unstructured email chains with multiple nested forwards.

### 2.2 Explicitly Deferred 2nd Handwritten PDF
- In accordance with the assignment plan, the second scanned/handwritten PDF requirement is explicitly **DEFERRED** and reserved for physical paper form testing. The current system validates one authentic handwritten clinic note (`clinic_handwritten_note.pdf`).

### 2.3 Single LLM Provider Dependency
- The current AI microservice relies exclusively on the Google GenAI SDK (Gemini Flash). While `tenacity` exponential retries and fallback to `gemini-flash-latest` are implemented, a regional Google Cloud outage would halt live inference without an alternative cloud vendor failover (e.g. Azure OpenAI or AWS Bedrock).

### 2.4 Lack of Standardized Medical Dictionary Auto-Coding
- Extracted adverse event terms (e.g. "liver injury", "tachycardia") and drug names (e.g. "Cardioril") are extracted as plain text. The prototype does not perform automated algorithmic MedDRA (Medical Dictionary for Regulatory Activities) Lowest Level Term (LLT) / Preferred Term (PT) coding or WHO Drug Global Dictionary coding.

### 2.5 Local Embedded Persistence (Demo Profile)
- For ease of evaluation, Spring Boot defaults to an embedded H2 database in Oracle mode. While an authentic Oracle PL/SQL DDL schema is provided in `database/oracle/schema.sql`, enterprise-scale transactional concurrency, tablespace management, and database-level high availability are not demonstrated in H2 mode.

---

## 3. Production Readiness Roadmap (What Would Change for Production)

To transition this prototype into an enterprise-ready, regulatory-compliant pharmacovigilance platform, the following architectural additions are required:

### 3.1 Regulatory Validation (CSV & 21 CFR Part 11 / Annex 11)
- **Computer System Validation (CSV)**: Execute Formal Installation Qualification (IQ), Operational Qualification (OQ), and Performance Qualification (PQ) testing in compliance with GAMP 5 guidelines.
- **Electronic Signatures**: Integrate 21 CFR Part 11 compliant dual-factor electronic signatures for reviewer approval workflows (meaning of signature, date/time, and authenticated user ID).
- **Audit Trail Archival**: Maintain write-once-read-many (WORM) audit trail retention for a minimum of 25 years in accordance with ICH GVP Module I.

### 3.2 Security, Privacy & PHI/PII De-Identification
- **Client-Side PHI Scrubbing**: Implement an on-premise Named Entity Recognition (NER) pipeline (e.g. Microsoft Presidio or specialized clinical de-identification model) to redact direct identifiers (patient Social Security Numbers, phone numbers, exact residential addresses) *before* payloads are transmitted to external cloud LLMs.
- **Enterprise IAM & RBAC**: Replace basic authentication with OAuth2.0 / OpenID Connect integrated with corporate identity providers (Azure AD / Okta), enforcing role-based access control (Triage Specialist, Safety Physician, Quality Manager, System Auditor).
- **Data Encryption**: Enforce TLS 1.3 in transit and AES-256 with Customer-Managed Encryption Keys (CMEK) at rest for all database tables and blob attachments.

### 3.3 Multi-Model & Multi-Cloud Redundancy
- **Active-Active Model Fallback**: Deploy an abstract LLM gateway routing requests dynamically across:
  - Primary: Google Cloud Vertex AI (Gemini 2.5 Flash / Pro)
  - Secondary: AWS Bedrock (Claude 3.5 Sonnet)
  - Tertiary: Azure OpenAI (GPT-4o)
- **Automatic Health Probing**: Dynamic circuit breakers (e.g. Resilience4j) automatically route inference to secondary providers during latency spikes or API throttling.

### 3.4 Regulatory Dictionary Integration (MedDRA & WHO Drug)
- **MedDRA Coding Engine**: Implement semantic vector search against official MSSO MedDRA dictionary files to automatically map extracted verbatim terms to coded SOC (System Organ Class) and PT (Preferred Term) codes with human reviewer confirmation.
- **WHO Drug Dictionary**: Map reported trade names to standard Medicinal Product Identifiers (MPIDs) and active substance names.

### 3.5 Scalable Enterprise Infrastructure
- **Distributed Event Broker**: Replace Spring Boot's internal `ThreadPoolTaskExecutor` with Apache Kafka or AWS SQS, enabling guaranteed message delivery, partitioned mailbox queues, and dead-letter queues (DLQ).
- **Container Orchestration**: Deploy services on Kubernetes (EKS / GKE / OpenShift) with Horizontal Pod Autoscaling (HPA) driven by queue depth.
- **Production Oracle RAC**: Deploy on Oracle Database 19c/21c Real Application Clusters (RAC) with Active Data Guard for disaster recovery and automated failover.

### 3.6 Observability & Model Drift Monitoring
- **Prometheus & Grafana**: Export real-time metrics on email ingestion rate, AI inference latency, confidence distributions, and human override frequency.
- **AI Performance Drift Detection**: Track reviewer override rates across categories and fields. A rising override rate triggers automated prompt evaluation alerts and model fine-tuning cycles.
