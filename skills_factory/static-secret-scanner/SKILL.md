---
name: static-secret-scanner
description: Detects hardcoded credentials, API keys, mainframe passwords, and unencrypted tokens before code leaves the developer workspace.
---

# Static Secret Scanner Skill

## 1. Prohibited Patterns
- Never hardcode AWS keys (`AKIA...`), JWT signing secrets, database passwords, or TLS private keys in source or test files.
- Always bind secrets via environment variables or enterprise secret managers (AWS Secrets Manager / HashiCorp Vault).

## 2. Pre-Commit Verification
- Run secret and entropy checks on all staged diffs prior to `/verify`.
