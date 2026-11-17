---
name: reinsurance-treaty-allocator
description: Implements proportional (Quota Share) and non-proportional (Excess of Loss, Stop Loss) reinsurance treaty allocation and bordereau schemas.
---

# Reinsurance Treaty Allocator Skill

## 1. Allocation Rules
- Enforce attachment point, limit, and retention ceiling checks before ceding premium or loss.
- Preserve exact penny reconciliation so `retained_amount + sum(ceded_amounts) == gross_amount`.

## 2. Bordereau Output
- Emit standardized bordereau records tagged with treaty ID, effective term, and currency ISO code.
