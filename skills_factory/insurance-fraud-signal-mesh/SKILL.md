---
name: insurance-fraud-signal-mesh
description: Scaffolds event-driven SIU fraud indicator pipelines (rapid loss after bind, duplicate claims, entity-graph anomalies).
---

# Insurance Fraud Signal Mesh Skill

## 1. Signal Evaluation
- Compute non-blocking fraud risk scores asynchronously on FNOL and endorsement events.
- Never auto-deny a claim solely from an ML score; route flagged claims to the Special Investigation Unit (SIU) review queue with explainable indicator codes.
