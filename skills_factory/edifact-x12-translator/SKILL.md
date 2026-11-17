---
name: edifact-x12-translator
description: Builds parsers and generators for HIPAA X12 EDI transactions (834 Enrollment, 835 Remittance, 837 Claims) with 999/277 acknowledgments.
---

# HIPAA X12 EDI Translator Skill

## 1. Segment & Loop Parsing
- Validate ISA/GS/ST envelope control numbers and segment terminators (`~`, `*`, `:`).
- Mask all subscriber SSNs and member PHI in diagnostic logs via `phi-pii-token-masker`.

## 2. Acknowledgments
- Generate deterministic `999` Implementation Acknowledgment or `277CA` Claims Acknowledgment payloads for every ingested batch.
