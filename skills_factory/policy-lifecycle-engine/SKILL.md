---
name: policy-lifecycle-engine
description: Generates deterministic state machines for policy administration (QUOTE -> BOUND -> ISSUED -> ENDORSED -> CANCELLED -> REINSTATED).
---

# Policy Lifecycle Engine Skill

This skill enforces valid, compliant state transitions for insurance policies.

---

## 1. The Canonical Policy State Machine

```mermaid
stateDiagram-v2
    [*] --> QUOTE
    QUOTE --> BOUND: Underwriting Approval & Premium Collected
    BOUND --> ISSUED: Policy Forms Generated
    ISSUED --> ENDORSED: Mid-Term Policy Change
    ENDORSED --> ISSUED: Endorsement Finalized
    ISSUED --> CANCELLED: Non-Payment / Insured Request
    CANCELLED --> REINSTATED: Arrears Paid & Underwriting Review
    REINSTATED --> ISSUED
    ISSUED --> [*]: Policy Term Expired
```

---

## 2. Invariant Rules

- Never transition from `QUOTE` directly to `ISSUED` without entering `BOUND`.
- Never endorse a `CANCELLED` policy without first completing formal reinstatement.
- Every state transition MUST emit a non-repudiable audit event to the enterprise event mesh.
