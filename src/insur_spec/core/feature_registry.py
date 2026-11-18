from __future__ import annotations

import ast
import re
import time
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field


class FeatureRecord(BaseModel):
    """Metadata for an individual feature specification & implementation slice."""

    slug: str
    title: str
    directive: str
    created_at: str = Field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    phase: str = "SPECIFIED"
    spec_path: str
    plan_path: str
    tasks_path: str


class FeatureRegistry:
    """Manages incremental feature specs under .insur-spec/features/ and the Living Master spec.md."""

    DELTA_HEADER = "## Feature Delta Log"

    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root.resolve()
        self.features_dir = self.workspace_root / ".insur-spec" / "features"

    @staticmethod
    def slugify(text: str, max_len: int = 36) -> str:
        cleaned = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
        if not cleaned:
            cleaned = "feature"
        return cleaned[:max_len].rstrip("-")

    def list_feature_dirs(self) -> list[Path]:
        if not self.features_dir.is_dir():
            return []
        return sorted(p for p in self.features_dir.iterdir() if p.is_dir())

    def next_slug(self, directive: str, custom_slug: Optional[str] = None) -> str:
        if custom_slug:
            return self.slugify(custom_slug, max_len=48)
        existing = self.list_feature_dirs()
        max_num = 0
        for d in existing:
            m = re.match(r"^(\d+)-", d.name)
            if m:
                max_num = max(max_num, int(m.group(1)))
        next_num = max_num + 1 if max_num > 0 else (2 if (self.workspace_root / "spec.md").is_file() else 1)
        return f"{next_num:03d}-{self.slugify(directive)}"

    def create_feature(self, directive: str, custom_slug: Optional[str] = None) -> FeatureRecord:
        slug = self.next_slug(directive, custom_slug=custom_slug)
        feat_dir = self.features_dir / slug
        feat_dir.mkdir(parents=True, exist_ok=True)

        rel_base = Path(".insur-spec") / "features" / slug
        return FeatureRecord(
            slug=slug,
            title=directive[:80],
            directive=directive,
            spec_path=(rel_base / "spec.md").as_posix(),
            plan_path=(rel_base / "plan.md").as_posix(),
            tasks_path=(rel_base / "tasks.md").as_posix(),
        )

    def resolve_paths(self, feature_slug: Optional[str] = None) -> tuple[Path, Path, Path]:
        """Returns (spec_path, plan_path, tasks_path) for a feature slug or falls back to root."""
        if feature_slug:
            feat_dir = self.features_dir / feature_slug
            if feat_dir.is_dir():
                return feat_dir / "spec.md", feat_dir / "plan.md", feat_dir / "tasks.md"
        return (
            self.workspace_root / "spec.md",
            self.workspace_root / "plan.md",
            self.workspace_root / "tasks.md",
        )

    def append_to_master_spec(self, record: FeatureRecord) -> Path:
        """Preserves root spec.md as Living Master Specification and appends a delta entry."""
        master_spec = self.workspace_root / "spec.md"
        if master_spec.is_file():
            existing = master_spec.read_text(encoding="utf-8").rstrip()
        else:
            existing = "# Master Service Specification\n\nLiving specification for this InsurSpec service."

        entry = (
            f"\n### [{record.slug}] {record.title}\n"
            f"- **Added (UTC):** {record.created_at}\n"
            f"- **Directive:** {record.directive}\n"
            f"- **Feature Spec:** [{record.spec_path}]({record.spec_path})\n"
        )

        if self.DELTA_HEADER in existing:
            updated = f"{existing}\n{entry}"
        else:
            updated = f"{existing}\n\n---\n\n{self.DELTA_HEADER}\n{entry}"

        master_spec.write_text(updated, encoding="utf-8")
        return master_spec

    def build_brownfield_context(self, active_slug: Optional[str] = None) -> str:
        """Assembles existing master spec and workspace file tree for brownfield LLM prompts."""
        sections: list[str] = []

        master_spec = self.workspace_root / "spec.md"
        if master_spec.is_file():
            spec_excerpt = master_spec.read_text(encoding="utf-8")[:4000]
            sections.append(f"### Existing Master Specification (spec.md)\n{spec_excerpt}")

        tracked_files: list[str] = []
        for folder_name in ("src", "tests", "app"):
            folder = self.workspace_root / folder_name
            if folder.is_dir():
                for path in sorted(folder.rglob("*")):
                    if path.is_file() and "__pycache__" not in path.parts:
                        tracked_files.append(path.relative_to(self.workspace_root).as_posix())
        if tracked_files:
            file_list = "\n".join(f"- {p}" for p in tracked_files[:60])
            sections.append(f"### Existing Repository Files\n{file_list}")

        symbol_lines = self._build_ast_symbol_map(tracked_files)
        if symbol_lines:
            sections.append("### Existing Python Symbol Map\n" + "\n".join(symbol_lines[:50]))

        if active_slug:
            sections.append(
                f"### Incremental Feature Constraint\n"
                f"You are adding incremental feature `{active_slug}` to an existing service. "
                f"Extend existing modules and preserve backward compatibility; do NOT delete or rewrite unrelated v1 functionality."
            )

        return "\n\n".join(sections)

    def _build_ast_symbol_map(self, rel_paths: list[str]) -> list[str]:
        """Extracts lightweight class/function signatures from Python files for brownfield context."""
        lines: list[str] = []
        for rel in rel_paths[:30]:
            if not rel.endswith(".py"):
                continue
            full_path = self.workspace_root / rel
            try:
                tree = ast.parse(full_path.read_text(encoding="utf-8"))
            except Exception:
                continue
            symbols: list[str] = []
            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    methods = [n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and not n.name.startswith("_")]
                    symbols.append(f"class {node.name}({', '.join(methods[:6])})")
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_"):
                    args = [a.arg for a in node.args.args if a.arg != "self"]
                    symbols.append(f"def {node.name}({', '.join(args[:5])})")
            if symbols:
                lines.append(f"- `{rel}`: " + "; ".join(symbols))
        return lines
