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


def test_executor_targeted_edit_and_dry_run(tmp_path: Path):
    target = tmp_path / "src" / "rating.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("def calc(x: int) -> int:\n    return x * 2\n", encoding="utf-8")

    edit_block = (
        "<<<EDIT: src/rating.py>>>\n"
        "<<<SEARCH>>>\n"
        "    return x * 2\n"
        "<<<REPLACE>>>\n"
        "    return x * 3\n"
        "<<<END EDIT>>>"
    )
    provider = _MockProvider([edit_block])
    executor = ImplementExecutor(workspace_root=tmp_path, provider=provider)

    # Dry-run should return diff without modifying file
    dry_res = executor.run_loop(tasks_markdown="Update multiplier", system_instructions="Const", dry_run=True)
    assert dry_res.success is True
    assert len(dry_res.diffs) == 1
    assert "+    return x * 3" in dry_res.diffs[0]
    assert "return x * 2" in target.read_text(encoding="utf-8")

    # Real run applies the targeted edit
    real_res = executor.run_loop(tasks_markdown="Update multiplier", system_instructions="Const", dry_run=False)
    assert real_res.success is True
    assert "return x * 3" in target.read_text(encoding="utf-8")
