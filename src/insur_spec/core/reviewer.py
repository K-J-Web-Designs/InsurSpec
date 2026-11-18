from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field

from .constitution_checker import ConstitutionGatekeeper


class ReviewFinding(BaseModel):
    severity: str
    category: str
    description: str
    file_path: str = ""
    line_number: int = 0


class ReviewReport(BaseModel):
    passed: bool = True
    files_reviewed: int = 0
    findings: list[ReviewFinding] = Field(default_factory=list)


class DiffReviewer:
    """Audits git diffs against the 10-Article Constitution and secret hygiene rules."""

    SECRET_PATTERNS = [
        (r"AKIA[0-9A-Z]{16}", "Potential AWS Access Key ID detected in diff"),
        (r"-----BEGIN\s+(?:RSA|EC|OPENSSH)?\s*PRIVATE\s+KEY-----", "Private key material detected in diff"),
        (r"(?:api_key|secret_key|password)\s*=\s*['\"][^'\"]{8,}['\"]", "Hardcoded secret/password literal detected"),
    ]

    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root.resolve()
        self.gatekeeper = ConstitutionGatekeeper(self.workspace_root)

    def get_git_diff(self, base_ref: str = "main", staged: bool = False) -> str:
        cmd = ["git", "diff", "--cached"] if staged else ["git", "diff", f"{base_ref}...HEAD"]
        try:
            proc = subprocess.run(cmd, cwd=str(self.workspace_root), capture_output=True, text=True, timeout=30)
            if proc.returncode != 0 and not staged:
                proc = subprocess.run(["git", "diff"], cwd=str(self.workspace_root), capture_output=True, text=True, timeout=30)
            return proc.stdout or ""
        except Exception:
            return ""

    def review_diff_text(self, diff_text: str) -> ReviewReport:
        findings: list[ReviewFinding] = []
        current_file = "diff"
        added_lines_by_file: dict[str, list[str]] = {}

        for line in diff_text.splitlines():
            if line.startswith("+++ b/"):
                current_file = line[6:].strip()
                added_lines_by_file.setdefault(current_file, [])
            elif line.startswith("+") and not line.startswith("+++"):
                added_lines_by_file.setdefault(current_file, []).append(line[1:])

        for file_path, lines in added_lines_by_file.items():
            joined = "\n".join(lines)
            for v in self.gatekeeper.audit_text(joined, source_name=file_path):
                findings.append(ReviewFinding(
                    severity=v.severity,
                    category=v.article,
                    description=v.description,
                    file_path=file_path,
                    line_number=v.line_number,
                ))
            for pattern, desc in self.SECRET_PATTERNS:
                for match in re.finditer(pattern, joined, re.IGNORECASE):
                    line_no = joined[:match.start()].count("\n") + 1
                    findings.append(ReviewFinding(
                        severity="BLOCKER",
                        category="Article VI: Security & Secrets",
                        description=desc,
                        file_path=file_path,
                        line_number=line_no,
                    ))

        passed = not any(f.severity == "BLOCKER" for f in findings)
        return ReviewReport(passed=passed, files_reviewed=len(added_lines_by_file), findings=findings)
