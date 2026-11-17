---
name: phi-pii-token-masker
description: Identifies, tokenizes, and redacts Protected Health Information (PHI) and Personally Identifiable Information (PII) to comply with HIPAA and GLBA.
---

# PHI/PII Token Masker Skill

This skill enforces zero-leakage policies across logging, database queries, and API response payloads.

---

## 1. Regulated Entities

The following fields MUST never appear in plaintext in loggers, error traces, or unauthenticated API responses:
- Social Security Number (SSN) / Tax ID: `\d{3}-\d{2}-\d{4}`
- Driver's License Number
- Date of Birth (DOB)
- Medical Record Numbers (MRN) / Diagnostic codes (ICD-10)
- Policyholder Financial / Bank Account numbers

---

## 2. Tokenization & Masking Protocol

1. **Logging**:
   - Always apply redaction filters: `mask_pii(record)` $\to$ `***-**-1234`.
2. **DTOs & Schemas**:
   - Annotate sensitive fields with `@field_serializer` or custom Pydantic types that prevent inadvertent serialization.
3. **Database Storage**:
   - Sensitive fields must be encrypted at rest using AES-256 or envelope encryption with AWS KMS / Google Cloud KMS.
