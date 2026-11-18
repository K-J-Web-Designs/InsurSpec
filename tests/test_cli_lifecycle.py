from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typer.testing import CliRunner
from insur_spec.cli import app


def test_full_lifecycle_e2e():
    runner = CliRunner()
    orig = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            os.chdir(tmpdir)
            
            # 1. init
            res_init = runner.invoke(app, ["init", "--name", "test-fnol-api", "--lob", "pnc", "--domain", "claims"])
            assert res_init.exit_code == 0, res_init.output
            assert (Path(tmpdir) / "catalog-info.yaml").is_file()
            assert (Path(tmpdir) / "mkdocs.yml").is_file()
            assert (Path(tmpdir) / ".insur-spec" / "memory" / "constitution.md").is_file()
            assert (Path(tmpdir) / "AGENTS.md").is_file()
            assert (Path(tmpdir) / ".github" / "copilot-instructions.md").is_file()

            prompts_dir = Path(tmpdir) / ".github" / "prompts"
            for prompt_name in (
                "insur-specify",
                "insur-feature-add",
                "insur-grill",
                "insur-plan",
                "insur-tasks",
                "insur-implement",
                "insur-qa",
                "insur-document",
                "insur-readme",
                "insur-review",
                "insur-quick",
                "insur-verify",
            ):
                p_file = prompts_dir / f"{prompt_name}.prompt.md"
                assert p_file.is_file()
                assert "description:" in p_file.read_text(encoding="utf-8")
                assert (Path(tmpdir) / ".claude" / "commands" / f"{prompt_name}.md").is_file()

            assert (Path(tmpdir) / "CLAUDE.md").is_file()
            assert (Path(tmpdir) / ".claude" / "settings.json").is_file()

            tasks_json = Path(tmpdir) / ".vscode" / "tasks.json"
            assert tasks_json.is_file()
            parsed_tasks = json.loads(tasks_json.read_text(encoding="utf-8"))
            assert parsed_tasks["version"] == "2.0.0"
            assert len(parsed_tasks["tasks"]) >= 5

            mcp_json = Path(tmpdir) / ".vscode" / "mcp.json"
            assert mcp_json.is_file()
            parsed_mcp = json.loads(mcp_json.read_text(encoding="utf-8"))
            assert "insur-spec" in parsed_mcp["servers"]

            # 2. specify
            res_spec = runner.invoke(app, ["specify", "Implement FNOL claim webhook with policy validation"])
            assert res_spec.exit_code == 0, res_spec.output
            assert (Path(tmpdir) / "spec.md").is_file()

            # 3. plan (triggers Constitution Gatekeeper)
            res_plan = runner.invoke(app, ["plan"])
            assert res_plan.exit_code == 0, res_plan.output
            assert (Path(tmpdir) / "plan.md").is_file()

            # 4. tasks
            res_tasks = runner.invoke(app, ["tasks"])
            assert res_tasks.exit_code == 0, res_tasks.output
            assert (Path(tmpdir) / "tasks.md").is_file()

            # 5. implement, qa, document, readme
            res_imp = runner.invoke(app, ["implement"])
            assert res_imp.exit_code == 0, res_imp.output

            res_qa = runner.invoke(app, ["qa"])
            assert res_qa.exit_code == 0, res_qa.output

            res_doc = runner.invoke(app, ["document"])
            assert res_doc.exit_code == 0, res_doc.output

            res_readme = runner.invoke(app, ["readme"])
            assert res_readme.exit_code == 0, res_readme.output

            res_quick = runner.invoke(app, ["quick", "Validate policy effective date", "--dry-run"])
            assert res_quick.exit_code == 0, res_quick.output

            res_grill = runner.invoke(app, ["grill"])
            assert res_grill.exit_code == 0, res_grill.output

            # 6. verify (generates signed receipt)
            res_ver = runner.invoke(app, ["verify"])
            assert res_ver.exit_code == 0, res_ver.output
            assert (Path(tmpdir) / "COMPLIANCE_RECEIPT.json").is_file()

        finally:
            os.chdir(orig)
