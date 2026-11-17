from __future__ import annotations

from pathlib import Path
from typing import Optional
from .manager import SkillsManager


class SkillsLoader:
    """Assembles prompt contexts by surgically injecting active skills."""

    def __init__(self, manager: SkillsManager):
        self.manager = manager

    def assemble_skills_context(self, active_skill_names: list[str]) -> str:
        sections: list[str] = []
        for name in active_skill_names:
            skill_tuple = self.manager.get_skill(name)
            if skill_tuple:
                meta, doc = skill_tuple
                sections.append(
                    f"### Skill: {meta.name}\n"
                    f"**Description**: {meta.description}\n\n"
                    f"{doc}\n"
                )

        if not sections:
            return ""

        return (
            "\n\n---\n\n"
            "# ACTIVE DOMAIN SKILLS (INJECTED BY INSURSPEC SKILLS FACTORY)\n"
            "Use the following domain runbooks, schemas, and instructions for your execution turns:\n\n"
            + "\n---\n".join(sections)
        )
