from __future__ import annotations

import os
from pathlib import Path
import pytest
from insur_spec.llm.switchboard import LLMSwitchboard
from insur_spec.llm.gemini_provider import GeminiProvider
from insur_spec.llm.bedrock_provider import BedrockProvider
from insur_spec.core.state_machine import PhaseStateMachine, LifecyclePhase


def test_switchboard_provider_selection():
    # Explicit gemini
    p_gemini = LLMSwitchboard.get_provider("gemini")
    assert isinstance(p_gemini, GeminiProvider)

    # Explicit bedrock
    p_bedrock = LLMSwitchboard.get_provider("bedrock")
    assert isinstance(p_bedrock, BedrockProvider)

    # Auto fallback with no keys defaults to Gemini for developer ergonomics
    p_auto = LLMSwitchboard.get_provider("auto")
    assert isinstance(p_auto, GeminiProvider)


def test_mock_generation_without_keys():
    gemini = GeminiProvider()
    response = gemini.generate("Draft C4 model for FNOL")
    assert "Gemini Mock" in response or len(response) > 0

    bedrock = BedrockProvider()
    response = bedrock.generate("Draft C4 model for FNOL")
    assert "AWS Bedrock Mock" in response or len(response) > 0


def test_state_machine_transitions(tmp_path: Path):
    fsm = PhaseStateMachine(tmp_path)
    assert fsm.current_phase == LifecyclePhase.UNINITIALIZED

    fsm.transition(LifecyclePhase.INITIALIZED)
    assert fsm.current_phase == LifecyclePhase.INITIALIZED

    fsm.transition(LifecyclePhase.SPECIFIED)
    assert fsm.current_phase == LifecyclePhase.SPECIFIED

    # Verify state saved to disk
    fsm2 = PhaseStateMachine(tmp_path)
    assert fsm2.current_phase == LifecyclePhase.SPECIFIED
    assert len(fsm2.state.phase_history) == 2
