from __future__ import annotations

from pathlib import Path
import pytest
from insur_spec.core.constitution_checker import ConstitutionGatekeeper


def test_destructive_sql_rejection(tmp_path: Path):
    gatekeeper = ConstitutionGatekeeper(tmp_path)
    bad_plan = """
    # Plan
    ## 1. Database
    DROP TABLE policy_records;
    """
    violations = gatekeeper.audit_text(bad_plan)
    assert any(v.rule == "Zero-Destruction Schema Migrations" for v in violations)
    assert any("DROP TABLE" in v.description for v in violations)


def test_placeholder_slop_rejection(tmp_path: Path):
    gatekeeper = ConstitutionGatekeeper(tmp_path)
    slop_code = """
    def handle_claim():
        // ...rest of implementation...
        pass
    """
    violations = gatekeeper.audit_text(slop_code)
    assert any(v.rule == "Complete Implementation Only" for v in violations)


def test_silent_error_rejection(tmp_path: Path):
    gatekeeper = ConstitutionGatekeeper(tmp_path)
    silent_swallow = """
    try:
        calculate_rating()
    except Exception:
        pass
    """
    violations = gatekeeper.audit_text(silent_swallow)
    assert any(v.rule == "Explicit Error Handling" for v in violations)


def test_clean_plan_passes_audit(tmp_path: Path):
    # Setup Backstage catalog-info.yaml
    (tmp_path / "catalog-info.yaml").write_text("apiVersion: backstage.io/v1alpha1\nkind: Component\n")
    plan_file = tmp_path / "plan.md"
    plan_file.write_text("""
    # Plan
    ## 1. System
    Clean additive architecture.
    ## 5. Mandatory Constitution Check
    - [x] All passed.
    """)

    gatekeeper = ConstitutionGatekeeper(tmp_path)
    report = gatekeeper.audit_plan(plan_file)
    assert report.is_compliant is True
    assert len(report.violations) == 0
