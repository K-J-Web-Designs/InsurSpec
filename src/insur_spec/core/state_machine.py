from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Optional, Any
from pydantic import BaseModel, Field


class LifecyclePhase(str, Enum):
    UNINITIALIZED = "UNINITIALIZED"
    INITIALIZED = "INITIALIZED"
    SPECIFIED = "SPECIFIED"
    PLANNED = "PLANNED"
    TASKS_READY = "TASKS_READY"
    IMPLEMENTED = "IMPLEMENTED"
    VERIFIED = "VERIFIED"


class ProjectState(BaseModel):
    current_phase: LifecyclePhase = Field(default=LifecyclePhase.UNINITIALIZED)
    service_name: str = Field(default="")
    constitution_hash: str = Field(default="")
    last_spec_path: Optional[str] = None
    last_plan_path: Optional[str] = None
    last_tasks_path: Optional[str] = None
    last_receipt_path: Optional[str] = None
    active_feature: Optional[str] = None
    features: dict[str, dict[str, Any]] = Field(default_factory=dict)
    consecutive_failures: int = 0
    phase_history: list[dict[str, Any]] = Field(default_factory=list)


class PhaseStateMachine:
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.state_file = workspace_root / ".insur-spec" / "state.json"
        self._state = self._load()

    @property
    def current_phase(self) -> LifecyclePhase:
        return self._state.current_phase

    @property
    def state(self) -> ProjectState:
        return self._state

    def _load(self) -> ProjectState:
        if self.state_file.is_file():
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    return ProjectState(**json.load(f))
            except Exception:
                pass
        return ProjectState()

    def save(self) -> None:
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(self._state.model_dump(), f, indent=2)

    def transition(self, next_phase: LifecyclePhase, details: Optional[dict[str, Any]] = None) -> None:
        self._state.phase_history.append({
            "from_phase": self._state.current_phase.value,
            "to_phase": next_phase.value,
            "details": details or {},
        })
        self._state.current_phase = next_phase
        self.save()
