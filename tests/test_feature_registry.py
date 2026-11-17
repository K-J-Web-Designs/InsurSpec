import json
from pathlib import Path
from typer.testing import CliRunner

from insur_spec.cli import app
from insur_spec.core.feature_registry import FeatureRegistry

runner = CliRunner()


def test_feature_registry_preserves_master_spec_and_appends_delta(tmp_path: Path):
    master = tmp_path / "spec.md"
    master.write_text("# V1 Claims Intake Spec\n\nInitial FNOL ingestion.", encoding="utf-8")

    registry = FeatureRegistry(tmp_path)
    rec = registry.create_feature("Add subrogation recovery workflow")
    assert rec.slug.startswith("002-")

    (tmp_path / rec.spec_path).write_text("# Subrogation Spec", encoding="utf-8")
    registry.append_to_master_spec(rec)

    updated_master = master.read_text(encoding="utf-8")
    assert "# V1 Claims Intake Spec" in updated_master
    assert "## Feature Delta Log" in updated_master
    assert rec.slug in updated_master
    assert rec.spec_path in updated_master


def test_brownfield_context_includes_existing_files_and_spec(tmp_path: Path):
    (tmp_path / "spec.md").write_text("# V1 Spec", encoding="utf-8")
    src_file = tmp_path / "src" / "claims_api.py"
    src_file.parent.mkdir(parents=True, exist_ok=True)
    src_file.write_text("def ingest():\n    return True\n", encoding="utf-8")

    registry = FeatureRegistry(tmp_path)
    ctx = registry.build_brownfield_context(active_slug="002-subrogation")
    assert "V1 Spec" in ctx
    assert "src/claims_api.py" in ctx
    assert "002-subrogation" in ctx


def test_cli_incremental_feature_lifecycle(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("INSURSPEC_LLM_PROVIDER", "gemini")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    assert runner.invoke(app, ["init", "--name", "claims-svc", "--lob", "pnc", "--domain", "claims"]).exit_code == 0

    # V1 specification
    res_v1 = runner.invoke(app, ["specify", "Initial FNOL claims intake"])
    assert res_v1.exit_code == 0
    v1_spec = (tmp_path / "spec.md").read_text(encoding="utf-8")
    assert "Initial FNOL claims intake" in v1_spec

    # Add incremental feature (V2)
    res_v2 = runner.invoke(app, ["specify", "--add", "Subrogation recovery tracking"])
    assert res_v2.exit_code == 0

    master_after = (tmp_path / "spec.md").read_text(encoding="utf-8")
    assert "Initial FNOL claims intake" in master_after
    assert "## Feature Delta Log" in master_after
    assert "Subrogation recovery tracking" in master_after

    # Plan, tasks, verify should target the active incremental feature
    assert runner.invoke(app, ["plan"]).exit_code == 0
    assert runner.invoke(app, ["tasks"]).exit_code == 0
    assert runner.invoke(app, ["verify"]).exit_code == 0

    receipt = json.loads((tmp_path / "COMPLIANCE_RECEIPT.json").read_text(encoding="utf-8"))
    assert receipt["feature_id"] is not None
    assert receipt["feature_id"].startswith("002-")

    feat_dir = tmp_path / ".insur-spec" / "features" / receipt["feature_id"]
    assert (feat_dir / "spec.md").is_file()
    assert (feat_dir / "plan.md").is_file()
    assert (feat_dir / "tasks.md").is_file()

    # Feature list & use commands
    res_list = runner.invoke(app, ["feature", "list"])
    assert res_list.exit_code == 0
    assert receipt["feature_id"] in res_list.output
