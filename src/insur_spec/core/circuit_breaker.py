from __future__ import annotations

import hashlib
from typing import Optional
from pydantic import BaseModel, Field


class IncidentReport(BaseModel):
    tripped: bool = False
    strike_count: int = 0
    error_hash: str = ""
    last_error_sample: str = ""
    attempted_remedies: list[str] = Field(default_factory=list)
    suggested_human_actions: list[str] = Field(default_factory=list)


class CircuitBreaker:
    """Enforces Article VIII: 5-Strike Circuit Breaker & Token Economy."""

    MAX_STRIKES = 5
    DIAGNOSIS_SHIFT_STRIKE = 3
    MAX_LOG_LINES = 100

    def __init__(self, max_strikes: int = MAX_STRIKES):
        self.max_strikes = max_strikes
        self.strike_count = 0
        self.last_error_signature = ""
        self.history: list[str] = []

    def compute_signature(self, error_text: str) -> str:
        # Normalize whitespace and numbers to capture semantic error shape
        cleaned = " ".join(error_text.strip().split())[:500]
        return hashlib.sha256(cleaned.encode("utf-8")).hexdigest()[:12]

    def record_failure(self, error_message: str, remedy_attempted: str = "") -> IncidentReport:
        sig = self.compute_signature(error_message)
        truncated_error = self.truncate_log(error_message)

        if sig == self.last_error_signature:
            self.strike_count += 1
        else:
            self.strike_count = 1
            self.last_error_signature = sig

        self.history.append(remedy_attempted or f"Attempt {self.strike_count} on error {sig}")

        if self.strike_count >= self.max_strikes:
            return IncidentReport(
                tripped=True,
                strike_count=self.strike_count,
                error_hash=sig,
                last_error_sample=truncated_error,
                attempted_remedies=self.history[-self.max_strikes:],
                suggested_human_actions=[
                    "Check external dependency or network boundary (database connection, API gateway).",
                    "Verify compiler / typing mismatch that cannot be deduced autonomously.",
                    "Review git diff to roll back recent circular edits.",
                ],
            )

        return IncidentReport(
            tripped=False,
            strike_count=self.strike_count,
            error_hash=sig,
            last_error_sample=truncated_error,
            attempted_remedies=self.history[-3:],
            suggested_human_actions=[],
        )

    def record_success(self) -> None:
        self.strike_count = 0
        self.last_error_signature = ""
        self.history.clear()

    @classmethod
    def truncate_log(cls, raw_log: str, max_lines: int = MAX_LOG_LINES) -> str:
        """Enforces token budget by capping logs to max_lines lines."""
        lines = raw_log.strip().splitlines()
        if len(lines) <= max_lines:
            return raw_log
        
        half = max_lines // 2
        head = "\n".join(lines[:half])
        tail = "\n".join(lines[-half:])
        omitted = len(lines) - max_lines
        return f"{head}\n\n[... {omitted} lines truncated by InsurSpec Token Governor ...]\n\n{tail}"
