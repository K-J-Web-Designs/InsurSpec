---
name: acord-standard-parser
description: Translates and validates ACORD XML and ACORD 2000 message formats into typed Pydantic/TypeScript schemas.
---

# ACORD Standard Parser Skill

## 1. Schema & XML Safety
- Validate incoming ACORD XML payloads against canonical XSD definitions before business mapping.
- Disable external entity expansion (`XXE`) on all XML parsers (`defusedxml` in Python).

## 2. Mapping Discipline
- Preserve ACORD `RqUID` / `TransactionResponseDt` correlation IDs end-to-end across downstream services.
