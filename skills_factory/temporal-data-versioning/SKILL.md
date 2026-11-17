---
name: temporal-data-versioning
description: Implements bi-temporal data modeling (valid_from/valid_to and system_from/system_to) to support historical rate recalculation and statutory insurance audits.
---

# Temporal Data Versioning Skill

This skill enforces bi-temporal table design across insurance rating, policy terms, and claims reserve history.

---

## 1. Dual Time Dimensions

Every temporal entity MUST track two distinct timelines:
1. **Valid Time (Business Time)**: When the rate or policy term was actually in effect in the real world (`effective_from`, `effective_to`).
2. **System Time (Transaction Time)**: When the record was inserted or superseded in the database (`created_at`, `superseded_at`).

---

## 2. Temporal Query Invariant

Adjusters and actuaries must be able to query the exact system state as of any past timestamp:
```sql
SELECT premium_rate 
FROM rate_table
WHERE coverage_type = 'AUTO_COMPREHENSIVE'
  AND '2024-05-10' BETWEEN effective_from AND effective_to  -- Real-world accident date
  AND '2024-05-15 14:00:00' BETWEEN created_at AND COALESCE(superseded_at, '9999-12-31'); -- System state when claim was filed
```
