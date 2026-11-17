---
name: adr-architectural-decision
description: Generates Markdown Architectural Decision Records (MADR) in docs/adr/ whenever technology choices or cross-domain patterns change.
---

# Architectural Decision Record (ADR) Skill

## 1. MADR Standard
When introducing a new datastore, messaging pattern, or cross-domain dependency, author `docs/adr/ADR-XXXX-<slug>.md` containing:
- **Context & Problem Statement**
- **Considered Options** (with trade-offs)
- **Decision Outcome** & **Consequences**
- Link the ADR in `mkdocs.yml` for Backstage TechDocs visibility.
