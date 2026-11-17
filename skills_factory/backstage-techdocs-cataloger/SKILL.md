---
name: backstage-techdocs-cataloger
description: Automatically generates and maintains Backstage.io catalog-info.yaml and MkDocs TechDocs for enterprise API cataloging and service discovery.
---

# Backstage.io TechDocs & Cataloger Skill

This skill enforces enterprise discovery and automated registration for all APIs, microservices, and event streams in **Backstage.io**.

---

## 1. Mandatory File Assets

Every repository managed by InsurSpec MUST contain:
1. `catalog-info.yaml`: Backstage Component and API descriptors.
2. `mkdocs.yml`: TechDocs core configuration.
3. `/docs/index.md`: Service overview, architecture diagrams, and ownership matrix.

---

## 2. Generating Backstage `catalog-info.yaml`

When scaffolding or modifying an API or microservice:
1. **Declare Component**:
   - `metadata.name`: kebab-case service name.
   - `metadata.annotations`:
     - `backstage.io/techdocs-ref: dir:.`
     - `github.com/project-slug: <org>/<repo>`
   - `spec.type`: `service` or `library`.
   - `spec.lifecycle`: `experimental`, `production`, or `deprecated`.
   - `spec.owner`: The domain architecture team (e.g., `group:claims-architecture-team`).
   - `spec.system`: The enterprise parent system (e.g., `claims-core-system`).
2. **Declare Provided APIs**:
   - If the service exposes REST, gRPC, or GraphQL endpoints, define an accompanying `kind: API` descriptor pointing to `./docs/api/openapi.yaml`.

---

## 3. TechDocs Structure (`/docs`)

```
docs/
├── index.md                 # Executive summary & domain context
├── architecture.md          # C4 Component diagram & data flow
├── api_reference.md         # OpenAPI / gRPC reference
├── data_model.md            # Bi-temporal schema & state machines
└── compliance.md            # Constitution Check & COMPLIANCE_RECEIPT.json log
```

Whenever an API route or schema is updated, the agent MUST update `/docs` in the same turn.
