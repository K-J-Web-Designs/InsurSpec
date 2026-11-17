---
name: backward-compat-api-guard
description: Audits OpenAPI and Protobuf schemas to block breaking API changes (removed fields, narrowed types, new required fields) before merge.
---

# Backward-Compatible API Guard Skill

## 1. Additive Evolution Only
- Never remove or rename existing response fields or add new mandatory request fields on an active major API version.
- Publish breaking contract evolutions under a new explicit version path (`/v2/...`) and update `catalog-info.yaml` API entities.
