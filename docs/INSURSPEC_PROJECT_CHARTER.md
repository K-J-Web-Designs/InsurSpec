# InsurSpec: Enterprise Project Charter & Discovery Questionnaire

> **Document Version:** 1.0.0  
> **Status:** Approved Baseline  
> **Classification:** Enterprise Strategic Proposal  
> **Target Enterprise:** Fortune 500 Insurance Enterprise (~10 Domain Architecture)  
> **Primary Technology Targets:** AWS Bedrock (VPC Production) | Google Cloud Vertex AI (Development/Sandbox)  

---

## 1. Project Overview

### 1.1 What is the primary goal of the InsurSpec project?
The primary goal of **InsurSpec** is to establish a **sovereign, spec-driven autonomous engineering platform** tailored for a Fortune 500 insurance enterprise. It replaces uncoordinated, hallucination-prone AI coding tools with a governed agent framework that translates business initiatives and architectural RFCs into production-grade software while mathematically preventing regulatory violations, data loss, architectural drift, and low-value "AI slop."

### 1.2 Who are the key stakeholders, and what are their expectations from the project?
*   **Domain Architects (~10 Line-of-Business Domains)**: Expect bounded contexts, clean C4 models, strict API versioning, and the ability to customize domain skills without breaking cross-domain integration.
*   **Chief Information Security Officer (CISO) & Head of Compliance**: Expect hard non-negotiable boundaries: zero unmasked PII/PHI token leakage, no hardcoded credentials, non-destructive additive database migrations, and cryptographically signed audit trails for state Department of Insurance (DOI) examiners.
*   **Enterprise Shared Services Architects**: Expect every newly created or modified API and microservice to automatically register in **Backstage.io** (`catalog-info.yaml`) with up-to-date TechDocs (`mkdocs.yml`).
*   **Domain Software Engineers**: Expect reduced cognitive overhead, automated boilerplate and test generation, elimination of brittle vanity tests, and clear, actionable feedback when requirements are ambiguous.
*   **Actuarial & Underwriting Leadership**: Expect high-throughput, deterministic rating code transpiled accurately from rate filings and loss models without calculation drift or rounding errors.

### 1.3 What are the key benefits of the InsurSpec project, and how will it impact the insurance industry?
*   **Accelerated Time-to-Market for New Insurance Products**: Reduces policy product filing-to-deployment timelines from 6–9 months down to weeks by automating spec, test, implementation, and cataloging workflows.
*   **Zero-Downtime Continuous Modernization**: Bridges 30-year-old mainframe/legacy Policy Administration Systems (PAS) with modern cloud services using non-destructive Expand-Contract migration patterns.
*   **Elimination of AI Technical Debt**: Enforces the **Essential Test Triad** and bars placeholder stubs (`// TODO`), preventing repository bloat.
*   **Industry Benchmark for Governed AI**: Proves that large regulated institutions do not have to ban generative AI or accept compliance risks; they can enforce statutory compliance directly through an **Immutable Machine-Readable Constitution**.

---

## 2. Scope and Requirements

### 2.1 What specific insurance products or lines of business will the InsurSpec platform support?
InsurSpec is built to support all major insurance lines across commercial and personal sectors:
*   **Property & Casualty (P&C)**: Commercial Auto, Personal Auto, Homeowners, Commercial Multi-Peril, Excess Liability.
*   **Life & Annuity**: Term Life, Whole Life, Indexed Universal Life, Fixed/Variable Annuities.
*   **Health & Benefits**: Commercial Health, Medicare Advantage, Supplemental Health, Group Disability.
*   **Specialty & Workers' Compensation**: Statutory Workers' Comp, Environmental Liability, Cyber Risk.

### 2.2 What are the key features and functionalities required for the platform?
*   **5-Phase Spec-Driven Lifecycle (`/specify`, `/plan`, `/tasks`, `/implement`, `/verify`)**: A deterministic finite state machine guiding development from user request to certified PR.
*   **Automated Constitution Gatekeeper**: Pre-implementation AST/regex engine that rejects plans containing destructive SQL (`DROP TABLE/COLUMN`, `TRUNCATE`), unmasked PII, empty catch blocks, or missing Backstage metadata.
*   **Skills Factory with CRUD Governance**: CLI-driven skills management allowing developers to customize domain playbooks while enforcing a strict constitutional ceiling.
*   **Automated Backstage.io Cataloging**: Automatic generation and synchronization of `catalog-info.yaml` and MkDocs TechDocs for zero-touch service discovery.
*   **5-Strike Circuit Breaker & Token Governor**: Intercepts failing retry loops on the 5th attempt, freezes workspace state, and truncates raw logs ($\le 100$ lines) to protect token budgets.
*   **Cryptographic Compliance Signer**: Produces HMAC-SHA256 signed `COMPLIANCE_RECEIPT.json` files sealing spec, plan, constitution, and test verification metrics.

### 2.3 Are there any regulatory or compliance requirements that the platform must adhere to?
*   **HIPAA / HITECH**: Mandatory field-level tokenization/redaction of all Protected Health Information (PHI) in claims and medical underwriting.
*   **Gramm-Leach-Bliley Act (GLBA)**: Protection of non-public personal financial information across policy and billing databases.
*   **NAIC Model Laws & State DOI Regulations**: State-specific rate and form filing rules, statutory accounting standards, and mandatory bi-temporal auditability.
*   **SOC 2 Type II & Sarbanes-Oxley (SOX)**: Non-repudiable audit logging, dual-approval controls for financial ledgers, and tamper-evident build receipts.
*   **PCI-DSS**: Strict tokenization of policyholder credit card and banking details for automated premium billing.

### 2.4 What are the non-functional requirements for the platform?
*   **Security & Privacy**: Zero prompt or telemetry egress outside the enterprise VPC; encryption in transit (TLS 1.3) and at rest (AES-256 via enterprise KMS).
*   **Resilience & Idempotency**: All generated endpoints, event consumers, and database migrations must be idempotent and resilient to partial network partitions.
*   **Performance & Latency**: Local CLI operations $< 200\text{ ms}$; spec generation $< 30\text{ s}$; task decomposition $< 15\text{ s}$; test verification $< 45\text{ s}$.
*   **Usability & Developer Ergonomics**: Seamless terminal UI via Rich/Typer with clear visual cues (green passes, red blocker alerts, structured trade-off prompts).

---

## 3. Technical Requirements

### 3.1 What is the preferred technology stack for the platform?
*   **Core Agent Engine**: Python 3.11+ / Typer / Rich / Pydantic v2 / Jinja2 / Pure-Python YAML (`ruamel.yaml`).
*   **Dual-LLM Runtime (Enterprise Provider Interface)**:
    *   *Production Target*: **AWS Bedrock** (Anthropic Claude 3.5 Sonnet / Llama 3.3 70B) via `boto3`.
    *   *Dev & Local Test Engine*: **Google Cloud Vertex AI / Gemini 3.8 Flash & Pro** via `google-genai`.
*   **Developer Portal & Documentation**: **Backstage.io** (YAML entity schemas) + **MkDocs** (`techdocs-core`).
*   **Data Persistence Standards**: PostgreSQL 16+ / Amazon Aurora / Snowflake (bi-temporal relational tables, pgvector for semantic search, zero destructive operations).
*   **Test Harness**: `pytest` / `pytest-asyncio` / parameterized table-driven suites enforcing the **Essential Test Triad**.

### 3.2 Are there any specific integration requirements with existing systems or third-party services?
*   **Policy Administration Systems (PAS)**: Read/write adapters for Guidewire PolicyCenter/ClaimCenter, Duck Creek, or mainframe core ledgers.
*   **Legacy Data Formats**: Parsers for **ACORD XML 2000**, **COBOL copybooks** (EBCDIC/COMP-3), and **HIPAA EDI X12** (834, 835, 837).
*   **Enterprise Service Backbone**: Event ingestion and publishing via **Apache Kafka** or **AWS EventBridge** using transactional outbox patterns.
*   **CI/CD & Security Scanners**: Automated integration with **GitHub Actions / GitLab CI**, **SonarQube** (quality gates), and **Snyk** (dependency/container vulnerability scanning).

### 3.3 What are the infrastructure and hosting requirements for the platform?
*   **Hybrid Cloud Architecture**:
    *   *Client Production*: Fully containerized deployment inside the client's **AWS VPC**, communicating with AWS Bedrock via **AWS PrivateLink** (zero public internet transit).
    *   *Developer Workstations*: Local CLI running in standard user space or VDI virtual desktops with local `.insur-spec/` workspace configuration.
    *   *Audit Vault*: Immutable **Amazon S3 WORM (Object Lock)** or Google Cloud Storage bucket holding non-repudiable compliance receipts.

---

## 4. Timeline and Milestones

### 4.1 What is the desired project timeline, including key milestones and deadlines?
A 12-week phased rollout spanning 4 sprints:
*   **Phase 1: Core Engine & Dual-LLM Foundations (Weeks 1–3)**
    *   *Milestone 1*: Functional `insur-spec` CLI with Bedrock/Gemini switchboard and state machine.
    *   *Milestone 2*: Active Constitution Gatekeeper and 5-strike circuit breaker.
*   **Phase 2: Skills Factory & Backstage Integration (Weeks 4–6)**
    *   *Milestone 3*: Skills CRUD engine with constitutional validation.
    *   *Milestone 4*: Backstage.io `catalog-info.yaml` and TechDocs automated provisioning.
    *   *Milestone 5*: Top 7 P0 skills delivered (`phi-pii-token-masker`, `expand-contract-db-migrator`, etc.).
*   **Phase 3: Domain Skills & Legacy Adapters (Weeks 7–9)**
    *   *Milestone 6*: Delivery of ACORD, COBOL copybook, and temporal rating skills.
    *   *Milestone 7*: Integration with staging Policy Administration System sandbox.
*   **Phase 4: Enterprise Pilot & Audit Certification (Weeks 10–12)**
    *   *Milestone 8*: Live pilot with a selected Line of Business team (e.g., Commercial Auto Underwriting or FNOL Claims).
    *   *Milestone 9*: Formal CISO and Enterprise Architecture Board security certification.

### 4.2 Are there any critical dependencies or prerequisites that must be completed before the project can begin?
*   **Enterprise VPC & IAM Role Provisioning**: AWS Bedrock access configured with VPC PrivateLink endpoints and cross-account IAM role assumption.
*   **Backstage.io Ingestion Permissions**: Service account credentials or GitHub App integration allowing InsurSpec repos to be auto-discovered by the central Backstage instance.
*   **Staging PAS / Sandbox Replicas**: Sanitized test databases or mock environments for Guidewire/Duck Creek/Mainframe systems containing synthetic policyholder data.
*   **Architecture & CISO Sign-off on Master Constitution**: Formal approval of the 10 constitutional articles by the client's Enterprise Architecture and Risk committees.

### 4.3 What are the key performance indicators (KPIs) for the project, and how will success be measured?
*   **Zero Production Downtime from Migrations**: 0 service interruptions or locked tables caused by AI-generated DDL (100% adherence to Expand-Contract).
*   **Zero PII/PHI Token Leaks**: 100% pass rate on pre-commit and CI/CD secret/PII AST scans.
*   **100% Backstage Catalog Coverage**: Zero uncataloged services or orphaned APIs deployed by pilot teams.
*   **Test Suite Efficiency (Anti-Bloat)**: $\ge 40\%$ reduction in total test lines with equal or higher boundary defect detection, verified by the Essential Triad.
*   **Developer Cycle Time Reduction**: $\ge 50\%$ reduction in lead time from approved Jira story to certified Pull Request.

---

## 5. Resources and Budget

### 5.1 What is the estimated budget for the project, and what are the key cost components?
*Estimated Pilot-to-Production Budget: $450,000 – $600,000 across 12–16 weeks.*
*   **Personnel (65%)**: Lead AI/Agent Architect, Enterprise Systems Integrator, Compliance/Security Engineer, QA/Test Engineer.
*   **Cloud & Model Compute (15%)**: AWS Bedrock token consumption, VPC PrivateLink endpoints, staging database replicas.
*   **Software & Tooling Licenses (10%)**: Backstage plugins, SonarQube Enterprise, enterprise container scanning.
*   **Contingency & Governance (10%)**: Independent third-party penetration testing and compliance audit review.

### 5.2 What resources will be required to complete the project?
*   **Core Engineering Team**:
    *   1 Lead Solutions / Agent Architect (InsurSpec orchestrator, skills factory).
    *   1 Cloud/DevSecOps Engineer (AWS VPC, Bedrock PrivateLink, IAM, CI/CD).
    *   1 Enterprise Insurance Data Specialist (ACORD, bi-temporal SQL, PAS integration).
*   **Client Stakeholder Commitments**:
    *   1 Domain Architect (part-time, 4 hrs/week for domain model reviews).
    *   1 CISO/Risk Liaison (part-time, 2 hrs/week for compliance gate validation).
    *   2 Pilot Software Developers (part-time during Phase 4 for user feedback).

### 5.3 Are there any specific resource constraints or limitations that must be considered?
*   **Availability of Legacy Mainframe SMEs**: Finding engineers who understand 20+ year-old COBOL copybooks and PAS batch scripts may require scheduling around release freezes.
*   **Corporate Security Clearance Cycles**: Provisioning AWS IAM roles and network access across corporate firewalls can introduce 1–2 week lead times if not initiated early.
*   **Model Rate Limits & Token Quotas**: Ensuring AWS Bedrock account quotas (tokens per minute) for Claude 3.5 Sonnet are sufficiently elevated for enterprise pilot loads.

---

## 6. Risks and Assumptions

### 6.1 What are the key risks associated with the project, and how will they be mitigated?
| Risk | Severity | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| **Model Hallucination of Core Logic** | High | Silent calculation or underwriting errors | Enforce the **Constitution Check** and **Essential Test Triad**; require deterministic tests to pass *before* code is accepted. |
| **Accidental PII/PHI Leakage** | Critical | Regulatory fines and breach disclosures | Pre-tokenization AST scanners (`phi-pii-token-masker`) sanitize inputs before LLM context ingestion. |
| **Developer Bypass of Guardrails** | High | Introduction of technical debt and uncataloged APIs | Hard-code constitutional invariants into `SkillsManager` and pre-commit hooks; block PR merges lacking signed receipts. |
| **Runaway Autonomous Retry Loops** | Medium | High token consumption and hung CI jobs | Enforce the **5-Strike Circuit Breaker** and cap ingested logs to $\le 100$ lines. |
| **AWS Account Access Delays** | Medium | Slippage in Phase 1 schedule | Leverage the **Dual-LLM Switchboard** to develop and test 100% of engine logic on Google Vertex AI / Gemini 3.8 locally. |

### 6.2 What assumptions have been made about the project, and how will they be validated?
*   **Assumption 1: Developers will adopt Spec-Driven Development**: Assumes developers are willing to write specifications before code.  
    *Validation*: Measure developer feedback and adoption friction during Phase 4 pilot using interactive CLI prompts.
*   **Assumption 2: Backstage is the enterprise source of truth**: Assumes the client’s architecture board requires Backstage.io for service discovery.  
    *Validation*: Confirm with the Shared Services Architect during Milestone 3.
*   **Assumption 3: Claude 3.5 Sonnet on Bedrock and Gemini 3.8 have prompt parity**: Assumes identical prompt templates produce compliant C4 and code outputs across both models.  
    *Validation*: Run the automated multi-LLM parity test suite included in `tests/test_llm_switchboard.py`.
*   **Assumption 4: Read-only staging replicas of PAS data are accessible**: Assumes synthetic or masked data can be provisioned for integration testing.  
    *Validation*: Review data governance agreements with the client's database administration team prior to Phase 3.
