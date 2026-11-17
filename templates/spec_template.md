# Feature Specification: {{ feature_title }}

## 1. Executive Context & Domain Mapping
- **Line of Business (LOB)**: {{ line_of_business }}
- **Domain**: {{ domain }}
- **Owning Domain Architecture Team**: {{ domain_architect_team }}
- **Backstage Component**: `{{ service_name }}`

## 2. Regulatory & Statutory Scope
- **State DOI Jurisdictions**: {{ state_jurisdictions | default("All Licensed States") }}
- **PII / PHI Classification**: {{ pii_classification | default("RESTRICTED - Tokenization Required") }}
- **Financial Ledger Impact**: {{ financial_impact | default("None") }}

## 3. Desired Business Outcomes & User Stories
{{ business_outcomes }}

## 4. Acceptance Criteria & Invariants
- [ ] Criterion 1: Happy path contract verification.
- [ ] Criterion 2: Key boundary value handling.
- [ ] Criterion 3: Deterministic error response structure.
- [ ] Criterion 4: Bi-temporal transaction logging.

## 5. Ambiguity Triage
*(If any requirements involve architectural forks or under-specified data models, invoke the Ambiguity Gate before proceeding to Plan.)*
