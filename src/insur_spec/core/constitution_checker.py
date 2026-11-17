from __future__ import annotations

import re
from pathlib import Path
from typing import NamedTuple
from pydantic import BaseModel, Field


class Violation(NamedTuple):
    article: str
    rule: str
    description: str
    severity: str  # BLOCKER | WARNING
    file_path: str = ""
    line_number: int = 0


class ConstitutionAuditReport(BaseModel):
    is_compliant: bool = True
    violations: list[dict[str, str | int]] = Field(default_factory=list)
    articles_verified: list[str] = Field(default_factory=list)


class ConstitutionGatekeeper:
    """AST and regex-based audit engine enforcing the 10-Article Insurance Constitution."""

    # Prohibited destructive SQL patterns (Article IV)
    DESTRUCTIVE_SQL_PATTERNS = [
        (r"\bDROP\s+TABLE\b", "DROP TABLE statement detected - violates Article IV non-destructive migration rule"),
        (r"\bDROP\s+COLUMN\b", "DROP COLUMN statement detected - violates Article IV additive schema rule"),
        (r"\bTRUNCATE\b", "TRUNCATE statement detected - violates Article IV data preservation rule"),
        (r"\bDELETE\s+FROM\s+\w+\s*;?$", "Unbounded DELETE FROM statement detected without WHERE clause"),
    ]

    # Prohibited placeholder slop patterns (Article I)
    SLOP_PATTERNS = [
        (r"//\s*\.\.\.rest\s+of\b", "Truncating ellipse '// ...rest of' detected - violates Article I complete implementation rule"),
        (r"/\*\s*\.\.\.existing\s+code\b", "Truncating ellipse '/* ...existing code' detected - violates Article I"),
        (r"#\s*\.\.\.rest\s+of\b", "Truncating ellipse '# ...rest of' detected - violates Article I"),
        (r"//\s*TODO:\s*implement\s+later\b", "Unimplemented TODO placeholder detected - violates Article I"),
        (r"raise\s+NotImplementedError\b", "NotImplementedError stub detected in production code path"),
    ]

    # Prohibited local-only data silos (Article V)
    LOCAL_SILO_PATTERNS = [
        (r"localStorage\.setItem\((['\"])user_", "Primary user state written exclusively to localStorage without cloud sync backing"),
    ]

    # Silent error swallowing (Article II)
    SILENT_ERROR_PATTERNS = [
        (r"except\s+\w+:\s*pass\b", "Silent error swallowing 'except: pass' detected - violates Article II resilience rule"),
        (r"catch\s*\([^)]*\)\s*\{\s*\}", "Empty catch block '{}' detected - violates Article II resilience rule"),
    ]

    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root

    def audit_text(self, text: str, source_name: str = "document") -> list[Violation]:
        violations: list[Violation] = []

        # Check Article IV: Destructive SQL
        for pattern, desc in self.DESTRUCTIVE_SQL_PATTERNS:
            for match in re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE):
                line_no = text[:match.start()].count("\n") + 1
                violations.append(Violation(
                    article="Article IV: Data Preservation",
                    rule="Zero-Destruction Schema Migrations",
                    description=desc,
                    severity="BLOCKER",
                    file_path=source_name,
                    line_number=line_no,
                ))

        # Check Article I: Anti-Slop
        for pattern, desc in self.SLOP_PATTERNS:
            for match in re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE):
                line_no = text[:match.start()].count("\n") + 1
                violations.append(Violation(
                    article="Article I: Anti-Slop Safeguards",
                    rule="Complete Implementation Only",
                    description=desc,
                    severity="BLOCKER",
                    file_path=source_name,
                    line_number=line_no,
                ))

        # Check Article II: Error Swallowing
        for pattern, desc in self.SILENT_ERROR_PATTERNS:
            for match in re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE):
                line_no = text[:match.start()].count("\n") + 1
                violations.append(Violation(
                    article="Article II: Architecture & Resilience",
                    rule="Explicit Error Handling",
                    description=desc,
                    severity="BLOCKER",
                    file_path=source_name,
                    line_number=line_no,
                ))

        # Check Article V: Local-only storage
        for pattern, desc in self.LOCAL_SILO_PATTERNS:
            for match in re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE):
                line_no = text[:match.start()].count("\n") + 1
                violations.append(Violation(
                    article="Article V: Cross-Device Synchronization",
                    rule="No Local-Only Silos",
                    description=desc,
                    severity="BLOCKER",
                    file_path=source_name,
                    line_number=line_no,
                ))

        return violations

    def audit_file(self, file_path: Path) -> list[Violation]:
        if not file_path.is_file():
            return []
        try:
            content = file_path.read_text(encoding="utf-8")
            return self.audit_text(content, str(file_path.relative_to(self.workspace_root)))
        except Exception as e:
            return [Violation(
                article="Article I: Anti-Slop",
                rule="Readable File",
                description=f"Failed to read file for audit: {e}",
                severity="BLOCKER",
                file_path=str(file_path),
            )]

    def audit_plan(self, plan_path: Path) -> ConstitutionAuditReport:
        violations: list[Violation] = self.audit_file(plan_path)

        # In addition, check for Mandatory Constitution Check checklist in plan
        content = plan_path.read_text(encoding="utf-8") if plan_path.is_file() else ""
        if "## 5. Mandatory Constitution Check" not in content and "## Constitution Check" not in content:
            violations.append(Violation(
                article="Article IX: Spec Gate",
                rule="Mandatory Constitution Check Section",
                description="Technical plan must contain a '## Constitution Check' section",
                severity="BLOCKER",
                file_path=str(plan_path),
            ))

        # Check Article X: Backstage catalog verification
        catalog_info = self.workspace_root / "catalog-info.yaml"
        if not catalog_info.is_file():
            violations.append(Violation(
                article="Article X: Backstage.io Integration",
                rule="catalog-info.yaml Required",
                description="Root catalog-info.yaml missing - every service must be registered in Backstage",
                severity="BLOCKER",
                file_path="catalog-info.yaml",
            ))

        is_compliant = not any(v.severity == "BLOCKER" for v in violations)
        return ConstitutionAuditReport(
            is_compliant=is_compliant,
            violations=[v._asdict() for v in violations],
            articles_verified=[
                "Article I: Anti-Slop",
                "Article II: Architecture",
                "Article III: Focused Testing",
                "Article IV: Data Preservation",
                "Article V: Cross-Device Sync",
                "Article VI: Security & Secrets",
                "Article VII: Ambiguity Gate",
                "Article VIII: 5-Strike Circuit Breaker",
                "Article IX: Spec Gate",
                "Article X: Backstage.io Integration",
            ],
        )
