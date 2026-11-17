---
name: audit-trail-lineage
description: Injects tamper-evident, non-repudiable audit logging for policy modifications, underwriting overrides, and claim reserve changes.
---

# Audit Trail Lineage Skill

## 1. Mandatory Audit Event Fields
Every state-mutating endpoint **MUST** emit an immutable audit record containing:
- `event_id` (UUID), `timestamp_utc` (ISO-8601)
- `actor_id`, `actor_role`
- `entity_type`, `entity_id`
- `before_state` (PII-masked), `after_state` (PII-masked), `reason_code`

## 2. Invariant
- Audit writes **MUST** occur within the same transactional boundary or transactional outbox as the business mutation.
