---
name: test-triad-generator
description: Generates high-value, focused unit and integration tests enforcing the Essential Triad (Happy path, Key boundary, Expected failure) while prohibiting vanity test bloat.
---

# Focused Test Triad Generator Skill

This skill enforces Article III of the Constitution: eliminate AI test slop and maintain fast, deterministic test suites.

---

## 1. The Essential Triad Rule

For every business unit, function, or endpoint, the test suite MUST be capped at the **Essential Triad**:
1. **The Happy Path**: Canonical input yielding verified expected output.
2. **The Key Boundary**: High-risk edge conditions (empty collection, off-by-one limit, maximum coverage limit).
3. **The Expected Failure**: Deterministic error response upon invalid input or downstream failure.

---

## 2. Table-Driven / Parameterized Testing

- Never write 10 copy-pasted `def test_...` functions differing only by input value.
- Consolidate inputs using `@pytest.mark.parametrize` or `test.each`.

---

## 3. Strict Prohibitions

- Do not test trivial getters, setters, or Pydantic models with no custom validators.
- Do not test third-party framework internals.
- Do not mock the internal business logic under test.
