---
name: pas-adapter-generator
description: Generates resilient Anti-Corruption Layer (ACL) API adapters for Policy Administration Systems (Guidewire, Duck Creek, Majesco).
---

# Policy Administration System (PAS) Adapter Generator Skill

## 1. Anti-Corruption Layer (ACL)
- Isolate legacy PAS SOAP/REST DTOs behind clean domain interfaces; never leak vendor-specific field names into core microservices.
- Wrap all outbound PAS calls with timeouts, exponential backoff retries, and circuit breakers.
