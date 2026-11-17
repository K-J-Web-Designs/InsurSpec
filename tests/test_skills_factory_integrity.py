from __future__ import annotations

from pathlib import Path
from insur_spec.skills.manager import SkillsManager


def test_all_factory_skills_valid_and_compliant(tmp_path: Path):
    mgr = SkillsManager(workspace_root=tmp_path)
    skills = mgr.list_skills()

    # 25 original catalog skills + backstage-techdocs-cataloger = 26
    assert len(skills) == 26

    for meta in skills:
        assert meta.name
        assert meta.description
        res = mgr.get_skill(meta.name)
        assert res is not None
        _, content = res
        # Ensure none of the shipped factory skills violate the Constitution
        mgr.validate_content(content)
