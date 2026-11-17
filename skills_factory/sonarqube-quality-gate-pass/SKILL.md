---
name: sonarqube-quality-gate-pass
description: Refactors high cognitive complexity functions, code smells, and duplication to pass enterprise SonarQube and Snyk quality gates.
---

# SonarQube Quality Gate Pass Skill

## 1. Complexity & Maintainability Standards
- Keep cyclomatic/cognitive complexity low by extracting single-purpose helper functions with early returns.
- Eliminate duplicated logic blocks across handlers and ensure zero critical/blocker code smells or Snyk CVEs.
