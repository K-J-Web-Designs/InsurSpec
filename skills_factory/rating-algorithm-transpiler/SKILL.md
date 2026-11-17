---
name: rating-algorithm-transpiler
description: Transpiles actuarial rate tables and Excel/R/Python rating formulas into deterministic, typed production code with Banker's rounding.
---

# Rating Algorithm Transpiler Skill

## 1. Precision & Rounding Invariants
- All currency and premium calculations **MUST** use fixed-point `Decimal` arithmetic (`ROUND_HALF_EVEN`), never IEEE 754 `float`.
- Rating factors **MUST** be loaded with effective-date bounds via `temporal-data-versioning`.

## 2. Deterministic Verification
- Every transpiled rating rule **MUST** include a parameterized test table matching actuarial rate-book test vectors to the cent.
