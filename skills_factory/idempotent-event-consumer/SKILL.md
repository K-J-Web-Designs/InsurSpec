---
name: idempotent-event-consumer
description: Enforces idempotent consumption across Kafka/RabbitMQ/EventBridge using deduplication keys and transactional outbox tables.
---

# Idempotent Event Consumer Skill

## 1. Exactly-Once Business Semantics
- Every consumer **MUST** extract a deterministic `idempotency_key` (e.g., `event_id` or `claim_id + sequence_no`) and record it atomically within the database transaction.
- Duplicate deliveries **MUST** acknowledge cleanly without re-applying billing charges or claim disbursements.
