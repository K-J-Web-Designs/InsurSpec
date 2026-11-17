---
name: actuarial-model-wrapper
description: Packages predictive loss models (GLMs, catastrophe models, mortality tables) into low-latency, schema-validated REST or gRPC services.
---

# Actuarial Model Wrapper Skill

## 1. Model Serving Contracts
- Enforce strict Pydantic/Protobuf input bounds (age, territory, exposure) and return model version metadata (`model_id`, `effective_date`) on every prediction.
- Log anonymized feature vectors for drift monitoring without exposing policyholder PII.
