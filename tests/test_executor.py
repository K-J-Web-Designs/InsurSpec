from __future__ import annotations

from pathlib import Path
from typing import AsyncIterator
from insur_spec.core.executor import ImplementExecutor
from insur_spec.llm.base import EnterpriseProviderInterface


class _MockProvider(EnterpriseProviderInterface):
    def __init__(self, outputs: list[str]):
        self.outputs = outputs
        self.idx = 0

    def generate(self, prompt: str, system_instructions: str = "", temperature: float = 0.2, max_output_tokens: int = 4096) -> str:
        out = self.outputs[min(self.idx, len(self.outputs) - 1)]
        self.idx += 1
        return out

    async def stream_generate(self, prompt: str, system_instructions: str = "", temperature: float = 0.2, max_output_tokens: int = 4096) -> AsyncIterator[str]:
        yield self.generate(prompt)


def test_executor_writes_clean_files_and_passes(tmp_path: Path):
    provider = _MockProvider([
        "<<<FILE: src/handler.py>>>\ndef handle_claim(claim_id: str) -> dict:\n    return {'claim_id': claim_id, 'status': 'RECEIVED'}\n<<<END FILE>>>"
    ])
    executor = ImplementExecutor(workspace_root=tmp_path, provider=provider)
    result = executor.run_loop(
        tasks_markdown="- Implement claim handler",
        system_instructions="Follow Constitution",
        verify_fn=lambda: (True, "All tests passed"),
    )
    assert result.success is True
    assert result.attempts == 1
    assert "src/handler.py" in result.files_written
    assert (tmp_path / "src" / "handler.py").is_file()


def test_executor_trips_circuit_breaker_on_5_constitutional_violations(tmp_path: Path):
    provider = _MockProvider([
        "<<<FILE: migrations/001.sql>>>\nDROP TABLE legacy_policies;\n<<<END FILE>>>"
    ])
    executor = ImplementExecutor(workspace_root=tmp_path, provider=provider, max_strikes=5)
    result = executor.run_loop(
        tasks_markdown="- Migrate policies",
        system_instructions="Follow Constitution",
    )
    assert result.success is False
    assert result.attempts == 5
    assert result.incident is not None
    assert result.incident.tripped is True
    assert not (tmp_path / "migrations" / "001.sql").exists()
