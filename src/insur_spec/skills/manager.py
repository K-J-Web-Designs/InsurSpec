from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Optional
from ..yaml_utils import yaml
from pydantic import BaseModel, Field


class ConstitutionalViolationError(Exception):
    """Raised when a custom skill attempts to circumvent the established Constitution."""
    pass


class SkillMetadata(BaseModel):
    name: str
    description: str = ""
    is_local_override: bool = False
    path: str
    author: str = "Enterprise Insurance Architecture"


class SkillsManager:
    """Manages full CRUD operations for skills with strict constitutional enforcement."""

    # Explicit prohibitions: no skill can instruct the agent to relax these rules
    FORBIDDEN_SKILL_PATTERNS = [
        (r"\b(bypass|skip|ignore|disable)\b.*\bconstitution\b", "Cannot instruct agent to bypass or ignore Constitution"),
        (r"\b(allow|enable)\b.*\b(drop\s+table|drop\s+column|truncate)\b", "Cannot authorize destructive database operations"),
        (r"\b(skip|ignore)\b.*\b(pii|phi|hipaa)\b", "Cannot instruct agent to skip PII/PHI redaction"),
        (r"\b(skip|ignore|omit)\b.*\b(backstage|catalog-info)\b", "Cannot omit Backstage.io registration"),
    ]

    def __init__(self, workspace_root: Path, factory_root: Optional[Path] = None):
        self.workspace_root = workspace_root
        self.local_skills_dir = workspace_root / ".insur-spec" / "skills"
        self.factory_root = factory_root or (Path(__file__).resolve().parent.parent.parent.parent / "skills_factory")

    def validate_content(self, skill_content: str) -> None:
        """Enforces that custom skills cannot circumvent the established Constitution."""
        for pattern, reason in self.FORBIDDEN_SKILL_PATTERNS:
            if re.search(pattern, skill_content, re.IGNORECASE):
                raise ConstitutionalViolationError(
                    f"Constitutional Violation in skill definition: {reason} (matched pattern: {pattern})"
                )

    def list_skills(self) -> list[SkillMetadata]:
        results: dict[str, SkillMetadata] = {}

        # 1. Discover factory skills
        if self.factory_root.is_dir():
            for skill_dir in self.factory_root.iterdir():
                if skill_dir.is_dir() and (skill_dir / "SKILL.md").is_file():
                    meta = self._parse_skill_md(skill_dir / "SKILL.md", is_local=False)
                    if meta:
                        results[meta.name] = meta

        # 2. Discover local project skills (can override factory skills)
        if self.local_skills_dir.is_dir():
            for skill_dir in self.local_skills_dir.iterdir():
                if skill_dir.is_dir() and (skill_dir / "SKILL.md").is_file():
                    meta = self._parse_skill_md(skill_dir / "SKILL.md", is_local=True)
                    if meta:
                        results[meta.name] = meta

        return sorted(results.values(), key=lambda s: s.name)

    def get_skill(self, name: str) -> Optional[tuple[SkillMetadata, str]]:
        # Check local override first
        local_file = self.local_skills_dir / name / "SKILL.md"
        if local_file.is_file():
            meta = self._parse_skill_md(local_file, is_local=True)
            if meta:
                return meta, local_file.read_text(encoding="utf-8")

        # Check factory
        factory_file = self.factory_root / name / "SKILL.md"
        if factory_file.is_file():
            meta = self._parse_skill_md(factory_file, is_local=False)
            if meta:
                return meta, factory_file.read_text(encoding="utf-8")

        return None

    def add_skill(self, name: str, description: str, markdown_content: str) -> SkillMetadata:
        slug = re.sub(r"[^a-z0-9_-]", "-", name.lower()).strip("-")
        full_doc = f"---\nname: {slug}\ndescription: {description}\n---\n\n{markdown_content}\n"
        
        self.validate_content(full_doc)

        target_dir = self.local_skills_dir / slug
        target_dir.mkdir(parents=True, exist_ok=True)
        target_file = target_dir / "SKILL.md"
        target_file.write_text(full_doc, encoding="utf-8")

        return SkillMetadata(
            name=slug,
            description=description,
            is_local_override=True,
            path=str(target_file.relative_to(self.workspace_root)),
        )

    def edit_skill(self, name: str, new_content: str) -> SkillMetadata:
        self.validate_content(new_content)

        target_dir = self.local_skills_dir / name
        target_dir.mkdir(parents=True, exist_ok=True)
        target_file = target_dir / "SKILL.md"
        target_file.write_text(new_content, encoding="utf-8")

        meta = self._parse_skill_md(target_file, is_local=True)
        if not meta:
            raise ValueError(f"Invalid SKILL.md frontmatter in {name}")
        return meta

    def delete_skill(self, name: str) -> bool:
        local_dir = self.local_skills_dir / name
        if local_dir.is_dir():
            shutil.rmtree(local_dir)
            return True
        return False

    def _parse_skill_md(self, skill_file: Path, is_local: bool) -> Optional[SkillMetadata]:
        try:
            content = skill_file.read_text(encoding="utf-8")
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    frontmatter = yaml.safe_load(parts[1])
                    if isinstance(frontmatter, dict):
                        return SkillMetadata(
                            name=frontmatter.get("name", skill_file.parent.name),
                            description=frontmatter.get("description", ""),
                            is_local_override=is_local,
                            path=str(skill_file.relative_to(self.workspace_root if is_local else self.factory_root.parent)),
                        )
        except Exception:
            pass
        return None
