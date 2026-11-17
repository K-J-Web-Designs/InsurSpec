---
name: saga-orchestration-builder
description: Constructs distributed Saga orchestrators for multi-step insurance workflows (Bind -> Reserve -> Bill -> Issue Forms) with compensating transactions.
---

# Saga Orchestration Builder Skill

## 1. Compensating Transactions
- Every forward step in a distributed workflow **MUST** define an explicit idempotent compensating action (e.g., `void_invoice`, `release_reserve`, `revert_bind_state`).
- Persist saga execution state in a durable store so interrupted workflows resume deterministically.
