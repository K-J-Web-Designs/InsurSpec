---
name: dead-letter-circuit-breaker
description: Routes poisoned claims or billing events to Dead Letter Queues (DLQ) with structured error metadata and safe replay tooling.
---

# Dead Letter Queue & Circuit Breaker Skill

## 1. Poison Message Isolation
- Never block a Kafka partition or queue on repeated deserialization/validation failures.
- After bounded retries with exponential backoff, route failed messages to `<topic>.dlq` enriched with `error_code`, `stack_summary`, and `original_timestamp`.
