from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Callable, Optional
from pydantic import BaseModel, Field

from ..llm.base import EnterpriseProviderInterface
from .circuit_breaker import CircuitBreaker, IncidentReport
from .constitution_checker import ConstitutionGatekeeper


FILE_BLOCK_PATTERN = re.compile(
    r"<<<FILE:\s*(?P<path>[^\n>]+?)>>>\n(?P<content>.*?)\n<<<END FILE>>>",
    re.DOTALL,
)


class ExecutionResult(BaseModel):
    success: bool
    files_written: list[str] = Field(default_factory=list)
    attempts: int = 0
    incident: Optional[IncidentReport] = None
    message: str = ""


class ImplementExecutor:
    """Executes spec-driven implementation turns guarded by the Constitution and 5-Strike Circuit Breaker."""

    def __init__(
        self,
        workspace_root: Path,
        provider: EnterpriseProviderInterface,
        max_strikes: int = CircuitBreaker.MAX_STRIKES,
    ):
        self.workspace_root = workspace_root.resolve()
        self.provider = provider
        self.gatekeeper = ConstitutionGatekeeper(self.workspace_root)
        self.breaker = CircuitBreaker(max_strikes=max_strikes)

    def _safe_resolve(self, rel_path: str) -> Optional[Path]:
        cleaned = rel_path.strip().lstrip("/\\")
        target = (self.workspace_root / cleaned).resolve()
        try:
            target.relative_to(self.workspace_root)
            return target
        except ValueError:
            return None

    def apply_file_blocks(self, llm_output: str) -> tuple[list[str], list[str]]:
        """Parses <<<FILE: path>>> blocks, audits against Constitution, and writes within workspace."""
        written: list[str] = []
        errors: list[str] = []

        for match in FILE_BLOCK_PATTERN.finditer(llm_output):
            rel_path = match.group("path").strip()
            content = match.group("content")
            target = self._safe_resolve(rel_path)
            if target is None:
                errors.append(f"Blocked unsafe path outside workspace: {rel_path}")
                continue

            violations = self.gatekeeper.audit_text(content, source_name=rel_path)
            blockers = [v for v in violations if v.severity == "BLOCKER"]
            if blockers:
                msgs = "; ".join(f"{b.article}: {b.description}" for b in blockers)
                errors.append(f"Constitution blocked write to {rel_path}: {msgs}")
                continue

            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            written.append(rel_path)

        return written, errors

    def run_loop(
        self,
        tasks_markdown: str,
        system_instructions: str,
        verify_fn: Optional[Callable[[], tuple[bool, str]]] = None,
    ) -> ExecutionResult:
        """Runs up to max_strikes implementation + verification turns."""
        files_written: list[str] = []
        feedback = ""

        for attempt in range(1, self.breaker.max_strikes + 1):
            prompt = (
                "Implement the following tasks strictly according to the Governing Constitution and active skills.\n"
                "Output any file creations or updates using:\n"
                "<<<FILE: relative/path/to/file.py>>>\n<complete file content>\n<<<END FILE>>>\n\n"
                f"## Tasks\n{tasks_markdown}\n"
            )
            if feedback:
                prompt += f"\n## Previous Attempt Failure (Fix Required)\n{feedback}\n"

            llm_response = self.provider.generate(
                prompt=prompt,
                system_instructions=system_instructions,
            )

            written, write_errors = self.apply_file_blocks(llm_response)
            files_written.extend(w for w in written if w not in files_written)

            if write_errors:
                err_msg = "\n".join(write_errors)
                incident = self.breaker.record_failure(err_msg, remedy_attempted=f"LLM synthesis attempt {attempt}")
                if incident.tripped:
                    return ExecutionResult(
                        success=False,
                        files_written=files_written,
                        attempts=attempt,
                        incident=incident,
                        message="5-Strike Circuit Breaker tripped due to repeated Constitutional/write violations.",
                    )
                feedback = incident.last_error_sample
                continue

            if verify_fn is not None:
                ok, verify_output = verify_fn()
                if not ok:
                    incident = self.breaker.record_failure(verify_output, remedy_attempted=f"Verification attempt {attempt}")
                    if incident.tripped:
                        return ExecutionResult(
                            success=False,
                            files_written=files_written,
                            attempts=attempt,
                            incident=incident,
                            message="5-Strike Circuit Breaker tripped during verification.",
                        )
                    feedback = incident.last_error_sample
                    continue

            self.breaker.record_success()
            return ExecutionResult(
                success=True,
                files_written=files_written,
                attempts=attempt,
                message=f"Implementation verified in {attempt} attempt(s).",
            )

        return ExecutionResult(
            success=False,
            files_written=files_written,
            attempts=self.breaker.max_strikes,
            message="Max attempts exhausted.",
        )

    @staticmethod
    def run_shell_check(command: list[str], cwd: Path) -> tuple[bool, str]:
        """Executes a verification command (e.g. pytest) and returns (passed, output)."""
        try:
            proc = subprocess.run(
                command,
                cwd=str(cwd),
                capture_output=True,
                text=True,
                timeout=120,
            )
            combined = (proc.stdout or "") + "\n" + (proc.stderr or "")
            return proc.returncode == 0, combined.strip()
        except Exception as e:
            return False, str(e)
