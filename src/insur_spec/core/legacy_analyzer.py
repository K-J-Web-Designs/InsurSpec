from __future__ import annotations

import ast
import re
from collections import Counter
from pathlib import Path
from typing import Any
from pydantic import BaseModel, Field

from .constitution_checker import ConstitutionGatekeeper
from .reviewer import DiffReviewer


class RepoAnalysisReport(BaseModel):
    """Structured inventory and health baseline of an existing production repository."""

    total_files: int = 0
    languages: dict[str, int] = Field(default_factory=dict)
    entry_points: list[str] = Field(default_factory=list)
    symbols: list[str] = Field(default_factory=list)
    detected_integrations: list[str] = Field(default_factory=list)
    pii_surface_files: list[str] = Field(default_factory=list)
    constitution_findings: list[dict[str, Any]] = Field(default_factory=list)


class LegacyRepoAnalyzer:
    """Performs deterministic deep-dive discovery and non-blocking compliance baselining on legacy repos."""

    SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache", "dist", "build"}
    EXT_LANG_MAP = {
        ".py": "Python",
        ".ts": "TypeScript",
        ".tsx": "TypeScript",
        ".js": "JavaScript",
        ".java": "Java",
        ".cs": "C#",
        ".go": "Go",
        ".sql": "SQL",
        ".cbl": "COBOL",
        ".cob": "COBOL",
        ".yaml": "YAML",
        ".yml": "YAML",
        ".json": "JSON",
    }
    INTEGRATION_HINTS = {
        "Kafka": r"\b(kafka|confluent_kafka|aiokafka)\b",
        "AWS / Bedrock / EventBridge": r"\b(boto3|botocore|eventbridge|bedrock)\b",
        "PostgreSQL / SQL": r"\b(psycopg|sqlalchemy|SELECT\s+.+\s+FROM|CREATE\s+TABLE)\b",
        "ACORD XML": r"\b(ACORD|RqUID|InsuranceSvcRq)\b",
        "HIPAA X12 EDI": r"\b(ISA\*|GS\*|ST\*83[457])\b",
        "Guidewire / PAS": r"\b(guidewire|policycenter|claimcenter|duckcreek)\b",
        "FastAPI / REST": r"\b(FastAPI|APIRouter|@app\.(get|post|put|delete)|flask)\b",
    }
    PII_HINTS = re.compile(r"\b(ssn|social_security|dob|date_of_birth|mrn|bank_account|routing_number|icd10)\b", re.I)

    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root.resolve()
        self.gatekeeper = ConstitutionGatekeeper(self.workspace_root)

    def _iter_source_files(self) -> list[Path]:
        files: list[Path] = []
        for path in sorted(self.workspace_root.rglob("*")):
            if not path.is_file():
                continue
            if any(part in self.SKIP_DIRS for part in path.parts):
                continue
            files.append(path)
        return files

    def analyze(self) -> RepoAnalysisReport:
        files = self._iter_source_files()
        lang_counts: Counter[str] = Counter()
        entry_points: list[str] = []
        symbols: list[str] = []
        integrations: set[str] = set()
        pii_files: list[str] = []
        findings: list[dict[str, Any]] = []

        for path in files:
            rel = path.relative_to(self.workspace_root).as_posix()
            lang = self.EXT_LANG_MAP.get(path.suffix.lower())
            if lang:
                lang_counts[lang] += 1

            if path.name in {"main.py", "app.py", "cli.py", "server.py", "index.ts", "Program.cs", "Dockerfile"}:
                entry_points.append(rel)

            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            for label, pattern in self.INTEGRATION_HINTS.items():
                if re.search(pattern, text, re.IGNORECASE):
                    integrations.add(label)

            if self.PII_HINTS.search(text):
                pii_files.append(rel)

            if path.suffix.lower() == ".py":
                symbols.extend(self._extract_python_symbols(rel, text))

            if path.suffix.lower() in {".py", ".ts", ".js", ".sql", ".java", ".cs", ".go"}:
                for v in self.gatekeeper.audit_text(text, source_name=rel):
                    findings.append(v._asdict())
                for pattern, desc in DiffReviewer.SECRET_PATTERNS:
                    for match in re.finditer(pattern, text, re.IGNORECASE):
                        findings.append({
                            "article": "Article VI: Security & Secrets",
                            "rule": "No Hardcoded Secrets",
                            "description": desc,
                            "severity": "BLOCKER",
                            "file_path": rel,
                            "line_number": text[:match.start()].count("\n") + 1,
                        })

        return RepoAnalysisReport(
            total_files=len(files),
            languages=dict(lang_counts.most_common()),
            entry_points=entry_points[:20],
            symbols=symbols[:60],
            detected_integrations=sorted(integrations),
            pii_surface_files=pii_files[:30],
            constitution_findings=findings[:100],
        )

    @staticmethod
    def _extract_python_symbols(rel_path: str, text: str) -> list[str]:
        try:
            tree = ast.parse(text)
        except Exception:
            return []
        out: list[str] = []
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                out.append(f"`{rel_path}`: class `{node.name}`")
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_"):
                out.append(f"`{rel_path}`: def `{node.name}()`")
        return out

    def format_markdown_summary(self, report: RepoAnalysisReport) -> str:
        langs = ", ".join(f"{k} ({v})" for k, v in report.languages.items()) or "Unknown"
        integrations = ", ".join(report.detected_integrations) or "None detected"
        entries = "\n".join(f"- `{e}`" for e in report.entry_points) or "- None detected"
        pii = "\n".join(f"- `{p}`" for p in report.pii_surface_files) or "- None detected"
        syms = "\n".join(f"- {s}" for s in report.symbols[:25]) or "- None parsed"
        return (
            f"# Repository Analysis Baseline\n\n"
            f"- **Total Files Scanned:** {report.total_files}\n"
            f"- **Languages:** {langs}\n"
            f"- **Detected Integrations:** {integrations}\n"
            f"- **Legacy Constitution/Secret Findings:** {len(report.constitution_findings)}\n\n"
            f"## Entry Points\n{entries}\n\n"
            f"## PII / PHI Surface Files\n{pii}\n\n"
            f"## Key Symbols\n{syms}\n"
        )
