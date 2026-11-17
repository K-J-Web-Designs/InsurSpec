---
name: sox-glba-control-enforcer
description: Audits financial transaction code (premiums, reserves, claim payouts) against SOX separation-of-duties and GLBA safeguard controls.
---

# SOX & GLBA Control Enforcer Skill

## 1. Separation of Duties
- Disbursements or reserve overrides exceeding authority thresholds **MUST** enforce dual-actor approval (`creator_id != approver_id`).
- Ledger entries **MUST** be append-only; reversals use offsetting credit/debit entries rather than row updates.

## 2. GLBA Safeguards
- Non-public personal financial data **MUST** be encrypted in transit (TLS 1.3) and at rest, with least-privilege RBAC checks on every query.
