---
name: expand-contract-db-migrator
description: Authors zero-downtime, non-destructive additive database migrations following the Expand-Contract pattern. Absolute prohibition on DROP TABLE/COLUMN.
---

# Expand-Contract Database Migrator Skill

This skill enforces Article IV of the Constitution: zero data destruction across multi-terabyte insurance databases.

---

## 1. The 4 Phases of Zero-Downtime Migration

```text
Phase 1 (Expand): Add new column/table as optional or with safe default.
Phase 2 (Dual Write): Application writes to BOTH old and new fields; reads fallback to old.
Phase 3 (Backfill): Run asynchronous batch job to populate new fields for historical records.
Phase 4 (Contract): Switch reads to new field; deprecate old field (do NOT drop immediately).
```

---

## 2. Hard Anti-Patterns (Prohibited)

- Never execute: `ALTER TABLE ... DROP COLUMN ...`
- Never execute: `DROP TABLE ...`
- Never execute: `TRUNCATE ...`
- Never execute: `db:reset` on shared/staging databases.
