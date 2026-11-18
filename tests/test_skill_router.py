from pathlib import Path
from insur_spec.core.feature_registry import FeatureRegistry
from insur_spec.skills.manager import SkillsManager
from insur_spec.skills.router import SkillRouter


def test_skill_router_selects_domain_relevant_skills(tmp_path: Path):
    mgr = SkillsManager(tmp_path)
    skills = mgr.list_skills()

    selected = SkillRouter.select_skills(
        "Parse legacy COBOL copybook EBCDIC records and apply bi-temporal rating calculations",
        skills,
    )
    assert "mainframe-copybook-parser" in selected
    assert "temporal-data-versioning" in selected
    assert "phi-pii-token-masker" in selected


def test_brownfield_ast_symbol_map(tmp_path: Path):
    src_file = tmp_path / "src" / "claims.py"
    src_file.parent.mkdir(parents=True, exist_ok=True)
    src_file.write_text(
        "class ClaimService:\n"
        "    def submit_fnol(self, policy_id: str) -> dict:\n"
        "        return {'policy_id': policy_id}\n\n"
        "def validate_vin(vin: str) -> bool:\n"
        "    return len(vin) == 17\n",
        encoding="utf-8",
    )

    ctx = FeatureRegistry(tmp_path).build_brownfield_context()
    assert "Existing Python Symbol Map" in ctx
    assert "class ClaimService(submit_fnol)" in ctx
    assert "def validate_vin(vin)" in ctx
