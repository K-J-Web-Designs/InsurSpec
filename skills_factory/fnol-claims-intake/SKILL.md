---
name: fnol-claims-intake
description: Scaffolds First Notice of Loss (FNOL) event handlers with dynamic loss triage, policy coverage validation, and fraud anomaly detection.
---

# First Notice of Loss (FNOL) Claims Intake Skill

This skill scaffolds high-throughput, multi-channel claims intake pipelines across web, mobile, and telematics.

---

## 1. Intake Workflow

```text
1. Ingest FNOL Payload (Insured ID, Loss Date/Time, Location, Loss Description, Severity)
2. Verify Policy Coverage at Loss Date (Temporal lookup via policy-lifecycle-engine)
3. Check SIU Fraud Signals (Rapid claim after binding, suspicious loss history)
4. Assign Initial Loss Reserve based on actuarial severity tables
5. Route Claim to Adjuster Queue / Auto-Adjudication Pipeline
```

---

## 2. Invariant Guardrails

- Loss Date MUST be within the policy's effective coverage dates.
- Initial loss reserve cannot be null or zero.
- All driver/claimant PII must be encrypted using `phi-pii-token-masker`.
